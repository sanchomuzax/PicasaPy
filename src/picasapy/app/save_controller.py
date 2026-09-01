"""Mentés a lemezre / Visszaállítás / Utolsó mentés visszavonása (#444).

A nem-destruktív modell magja (`picasapy.edit.save`) régóta megvan és
tesztelt — de a felületen **nem volt elérhető**: a Fájl menü „Mentés",
„Visszaállítás" pontjai helyfoglalók voltak. Ez a szelet köti be őket.

A Picasa NÉGY külön műveletet ismer (a jegy szerint, a bináris
sztringjeiből):

| művelet | mire hat |
|---|---|
| **Mentés** | a lemezen lévő fájlra — előtte biztonsági másolat készül |
| **Visszaállítás** | a lemezen lévő fájlra — az eredeti jön vissza, a szerkesztések ELVESZNEK |
| **Utolsó mentés visszavonása** | csak az utolsó lemezre írásra — a szerkesztések MEGMARADNAK |
| **Összes szerkesztés visszavonása** | csak a `filters=` láncra (ez a #465-ben már megvan) |

**A #484-es rangsor kiemelt pontja:** a mentés **véglegesen eldobja** azt a
láncelemet, amit nem tudunk renderelni — a beégetett képbe az nem kerül
bele, a `redo=` viszont felülíródik. Ezért a mentés előtt a hívó a
`unrenderableFiltersIn()`-nel megkérdezheti, van-e ilyen, és
figyelmeztetheti a felhasználót. Ez NEM elméleti kockázat: a „Régi
effektek" fülön (#571) ma is látszanak olyan nevek, amikhez nincs
renderelőnk, és egy régi `.picasa.ini` bármikor hozhat ilyet.
"""

from __future__ import annotations

import logging
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np
from PySide6.QtCore import Property, Signal, Slot, QUrl

from picasapy.cvimage import read_image_bytes
from picasapy.edit.save import SaveError, revert, save_edited, undo_save
from picasapy.edit.save_copy import (
    FileNameCollisionError,
    next_copy_path,
    save_copy,
)
from picasapy.edit.session import EditSession
from picasapy.ini import IniConflictError, IniSaveError
from picasapy.render.chain import apply_filters, can_render_filter

from .save_error_kind import save_error_code, save_error_kind
from .worker_thread import BackgroundWorkerMixin

def _konyvtar_tartalma(konyvtar: Path) -> list[Path]:
    """Az eredeti-mappa egyszeri listázása — külön függvény, hogy a teszt
    MEGSZÁMOLHASSA (#1146), a globális `Path.glob` átírása nélkül (#1375).

    A `monkeypatch.setattr(Path, "glob", figyelo)` alak a `pathlib.Path`
    OSZTÁLYT írja át: a számláló a teszt idejére a folyamat MINDEN
    mappalistázását felvenné, tehát a „100 képre egy listázás" állítás nem
    is csak erről a vezérlőről szólna."""
    return list(konyvtar.glob("*"))

#: A mentés kezelt hibái: a fájlrendszeré, a kódolásé, a párhuzamos
#: ini-íróé és a magé — egyik sem szökhet ki a QML felé kivételként.
_SAVE_ERRORS = (OSError, ValueError, SaveError, IniSaveError, IniConflictError)

#: Ennyi hibás fájl nevét/okát mutatjuk az összegzésben (az export
#: `_EXPORT_FAILED_DETAILS_LIMIT` mintája) — tömeges hibánál a teljes lista
#: inkább zavaró, mint hasznos.
_FAILED_DETAILS_LIMIT = 5


def _render_for_save(path: Path, rotate_steps: int, filters: str) -> np.ndarray:
    """A képfájl a szerkesztésekkel BEÉGETVE, OpenCV BGR-ben.

    A forgatás és a `filters=` lánc ugyanazon a renderelő-úton megy, mint
    az exportnál — a mentett fájl és a rácsban látott kép így egyezik.
    """
    payload = read_image_bytes(path)
    if payload is None:
        raise ValueError(f"Üres vagy nem olvasható fájl: {path}")
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Nem dekódolható kép: {path}")
    steps = int(rotate_steps or 0) % 4
    for _ in range(steps):
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    ops = EditSession.from_value(filters).ops
    if not ops:
        return image
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rendered, _skipped = apply_filters(rgb, ops)
    return cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR)


class SaveMixin(BackgroundWorkerMixin):
    """A Fájl menü mentés-műveletei a kijelölt képekre."""

    #: (sikeres, sikertelen) — a művelet végén EGY összegzés
    saveFinished = Signal(int, int)
    revertFinished = Signal(int, int)
    undoSaveFinished = Signal(int, int)
    #: az első néhány sikertelen fájl "név: ok" alakban
    saveFailedDetails = Signal(list)

    # ── #1527 ─────────────────────────────────────────────────────────
    #: „Másolat mentése" / „Mentés másként…" vége: (sikeres, sikertelen)
    saveCopyFinished = Signal(int, int)

    # ── #1566 ─────────────────────────────────────────────────────────
    #: A másolat-mentés FELÜLETI visszajelzése: (hány sikerült, az utolsó
    #: célfájl útja). A lebegő értesítősáv (#1129) fogadja.
    #:
    #: Miért KÜLÖN jelzés, és nem a `saveCopyFinished` bővítése:
    #:
    #: 1. A `saveCopyFinished(int, int)` szignatúráját két beolvadt jegy
    #:    kötései és tesztjei rögzítik (#1527 menüpont-tesztjei, #1539
    #:    újraolvasás-kötése) — a bővítése azokat törné.
    #: 2. A sávnak a darabszámon felül a CÉLÚTVONAL is kell, különben a
    #:    cella kattintása néma no-op: a `NotifierCell` a hasznos adat
    #:    MAPPÁJÁRA navigál. Épp ez a jegy tétje — a „Mentés másként…"
    #:    bárhova írhat, és ott a fájlnak a rácsban sem marad nyoma.
    #:
    #: Ugyanaz az alak, mint a kollázsnál: a gépies befejezés-jelzés és a
    #: felhasználónak szóló, ÚTVONALAT vivő jelzés
    #: (`collageDesktopBackgroundReady`) ott is két külön jelzés.
    saveCopyReady = Signal(int, str)

    #: a HÁROM hivatalos hibaág: (ág, fájlnév, hibakód). Az ág-azonosítók
    #: a `save_error_kind.py`-ban; a SZÖVEGET a `SaveDialogs.qml` adja,
    #: mert a hivatalos feliratok fordítható erőforrások.
    saveErrorOccurred = Signal(str, str, int)
    #: a lebegő folyamat-panel állapota változott
    saveProgressChanged = Signal()
    #: háttérszálból jövő haladás — Qt sorolja a GUI-szálra
    _saveProgressTick = Signal(int, int, int)  # (kész, összes, aktív?)

    def _ensure_save_progress(self) -> None:
        """Lusta állapot-inicializálás (a `BatchEffectMixin` mintája)."""
        if getattr(self, "_save_progress_wired", False):
            return
        self._save_progress_wired = True
        self._save_progress_done = 0
        self._save_progress_total = 0
        self._save_progress_active = False
        self._saveProgressTick.connect(self._on_save_progress_tick)
        # ⚠️ A fájl kiírása MÉG NEM láthatóság: a másolat addig nem jelenik
        # meg a rácsban, amíg az index nem tud róla, a `selectFolder` pedig
        # kizárólag az indexből olvas.
        #
        # #1539: az INDEX helyessége innentől NEM ezen a kötésen múlik. A
        # célmappát a `_save_copies` workere jelenti be fájlonként
        # (`noteOutputWritten`), a TÉNYLEGES célútvonallal.
        #
        # Miért kellett ez: a lenti kötés a LÁTOTT mappát olvassa újra. A
        # „Másolat mentése" mellett az történetesen a célmappa is, tehát
        # véletlenül jó volt — a #1527-tel érkezett „Mentés másként…"
        # viszont a fájlválasztóból BÁRHOVA mutathat, és ott a program a
        # rossz mappát frissítette. Mérve (figyelő nélkül): a más mappába
        # mentett másolat 25 s alatt sem jelent meg.
        #
        # A kötés mégis MEGMARAD, két okból: ez frissíti a felhasználó által
        # ÉPP NÉZETT mappa nézetét a művelet végén (a #1527 szándéka), és ez
        # a `saveCopyFinished` egyetlen fogyasztója — QML-oldali kezelője
        # NINCS, tehát elhagyva néma jelzés lenne belőle (#1003). Hogy a
        # befejezésnek van-e FELÜLETI visszajelzése, az önálló kérdés.
        self._ensure_output_resync_wired()
        poll = getattr(self, "_poll_current_folder", None)
        if poll is not None:
            self.saveCopyFinished.connect(lambda _done, _failed: poll())

    def _on_save_progress_tick(self, done: int, total: int, active: int) -> None:
        self._save_progress_done = done
        self._save_progress_total = total
        self._save_progress_active = bool(active)
        self.saveProgressChanged.emit()

    @Property(bool, notify=saveProgressChanged)
    def saveProgressActive(self) -> bool:  # noqa: N802 — QML-stílus
        """Látszódjon-e a mentés folyamat-panelje."""
        self._ensure_save_progress()
        return self._save_progress_active

    @Property(int, notify=saveProgressChanged)
    def saveProgressFileCount(self) -> int:  # noqa: N802 — QML-stílus
        """Hány fájlt ment a futó művelet — ettől függ, hogy a felület az
        egyes vagy a többes számú hivatalos mondatot mutatja
        (`progfile` / `progfiles`)."""
        self._ensure_save_progress()
        return self._save_progress_total

    @Property(float, notify=saveProgressChanged)
    def saveProgressPercent(self) -> float:  # noqa: N802 — QML-stílus
        """A készültség százalékban.

        ⚠️ A hivatalos formátum `%.1f%%` — EGY tizedesjegy (a #1527 jegy
        „századpontos" megfogalmazása a `%.1f`-fel nem egyezik; a
        formátumsztring az erősebb bizonyíték, azt követjük). A
        kerekítést a felület végzi, itt a nyers arány áll."""
        self._ensure_save_progress()
        if self._save_progress_total <= 0:
            return 0.0
        return 100.0 * self._save_progress_done / self._save_progress_total

    def _report_save_error(self, error: BaseException, path: Path) -> None:
        """Egy mentés-hiba besorolása és felküldése a felületnek."""
        self.saveErrorOccurred.emit(
            save_error_kind(error), path.name, save_error_code(error)
        )

    def _selected_records(self, rows):
        photos = self._photos.photos
        return [
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        ]

    @Slot(list, result=list)
    def unrenderableFiltersIn(self, rows) -> list:  # noqa: N802 — QML-stílus
        """A kijelölésben szereplő, ÁLTALUNK NEM RENDERELHETŐ szűrőnevek.

        A mentés beégeti a láncot a fájlba: amit nem tudunk renderelni, az a
        beégetett képből kimarad, a `redo=` viszont felülíródik — vagyis a
        beállítás **véglegesen elvész**. A felület ezért a mentés előtt
        rákérdezhet (#444/#484).

        Ábécésorrendben, ismétlés nélkül; üres lista = nincs miért kérdezni.
        """
        names = set()
        for record in self._selected_records(rows):
            for op in EditSession.from_value(record.filters).ops:
                if not can_render_filter(op.name):
                    names.add(op.name.casefold())
        return sorted(names)

    @Slot(list, result=bool)
    def hasSavedBackup(self, rows) -> bool:  # noqa: N802 — QML-stílus
        """Van-e a kijelölésben olyan kép, amit MÁR mentettünk egyszer.

        Ettől függ, hogy a „Visszaállítás" és az „Utolsó mentés
        visszavonása" egyáltalán értelmes-e (mentetlen képnél nincs mit
        visszaállítani) — a menü ezzel tiltja a pontjait. A mentés-előtti
        másolat KÉT mappanév alatt lehet (`.picasaoriginals`, `Originals`);
        ld. `picasapy.edit.save` „Két mappanév" szakaszát (#1425).
        """
        from picasapy.edit.save import ORIGINALS_DIR_NAMES

        # ⚠️ #1146: MAPPÁNKÉNT nézünk a lemezre, nem képenként. A régi ág
        # soronként hívott `is_dir()`-t ÉS `glob()`-ot — 2 002 soros
        # kijelölésnél 10 010 `stat()` EGYETLEN billentyűleütésre. A
        # tulajdonos gyűjteménye hálózati megosztáson van, ahol minden
        # `stat()` egy hálózati kör: ott ez nem lassulás, hanem fagyás.
        #
        # Egy mappa eredeti-mappáit elég EGYSZER kilistázni; a tőnevek
        # halmazából utána memóriából válaszolunk.
        #
        # #1425: MINDKÉT mappanevet nézzük — a mai `.picasaoriginals`-t és a
        # 2009 előtti, látható `Originals`-t. A régi név a tulajdonos
        # gyűjteményében 127 mappában előfordul; enélkül a „Visszaállítás"
        # menütétel ott szürke maradna, magyarázat nélkül.
        tovek: dict[str, set[str]] = {}
        for record in self._selected_records(rows):
            mappa = str(record.folder_path)
            if mappa not in tovek:
                nevek: set[str] = set()
                for dir_name in ORIGINALS_DIR_NAMES:
                    konyvtar = Path(mappa) / dir_name
                    if konyvtar.is_dir():
                        nevek.update(
                            utvonal.name
                            for utvonal in _konyvtar_tartalma(konyvtar)
                        )
                tovek[mappa] = nevek
            to = Path(record.name).stem
            if any(nev.startswith(to) for nev in tovek[mappa]):
                return True
        return False

    @Slot(list)
    def saveRowsToDisk(self, rows) -> None:  # noqa: N802 — QML-stílus
        """„Mentés" (Ctrl+S): a szerkesztések BEÉGETÉSE a fájlokba.

        Minden mentés előtt biztonsági másolat készül (az eredeti a
        `.picasaoriginals`-ba, plusz mentésenként egy sorszámozott
        pillanatkép az „Utolsó mentés visszavonása" számára).
        """
        records = [
            (Path(r.folder_path) / r.name, int(r.rotate_steps or 0), r.filters or "")
            for r in self._selected_records(rows)
        ]
        if not records:
            self.saveFinished.emit(0, 0)
            return
        self._ensure_save_progress()
        self._saveProgressTick.emit(0, len(records), 1)

        def worker():
            done, failed, details = 0, 0, []
            naplo: list[tuple[str, str]] = []
            # #1527: ágonként EGY üzenet. Az eredeti sem sorolja fel a
            # fájlokat: három külön mondata van, és a lemezhiba-ágon az
            # ELSŐ érintett fájl neve + a hibakód jelenik meg.
            jelentett_agak: set[str] = set()
            for index, (path, rotate_steps, filters) in enumerate(records):
                try:
                    rendered = _render_for_save(path, rotate_steps, filters)
                    save_edited(path, rendered, EditSession.from_value(filters))
                except _SAVE_ERRORS as error:
                    failed += 1
                    if len(details) < _FAILED_DETAILS_LIMIT:
                        details.append(f"{path.name}: {error}")
                    ag = save_error_kind(error)
                    if ag not in jelentett_agak:
                        jelentett_agak.add(ag)
                        self._report_save_error(error, path)
                else:
                    done += 1
                    # #750: a sikeres mentés ÜRES lánccal jelent a naplónak,
                    # ami ott a bejegyzés TÖRLÉSÉT jelenti. Ld. a `redo=`
                    # döntést a `_record_saved_state` docstringjében.
                    naplo.append((str(path), ""))
                self._saveProgressTick.emit(index + 1, len(records), 1)
            self._record_saved_state(naplo)
            self._saveProgressTick.emit(len(records), len(records), 0)
            # #1527: a MENTÉS ága innentől a besorolt, hivatalos üzenetet
            # adja (`saveErrorOccurred`), nem a nyers „név: ok" listát —
            # az eredetiben is három konkrét mondat áll, nem felsorolás.
            # A `details` a naplónak marad, hogy a bukás oka ne vesszen el.
            if details:
                logging.getLogger(__name__).warning(
                    "mentés-hibák (#1527): %s", "; ".join(details)
                )
            self.saveFinished.emit(done, failed)

        self._start_background(worker, name="picasapy-save")

    # ── #1527: „Másolat mentése" és „Mentés másként…" ────────────────
    #
    # A két parancs a MÉRÉS szerint ugyanaz a művelet, egyetlen
    # kapcsolóval (a bináris `0x005e6a20` bájt-paramétere) — ld.
    # `picasapy.edit.save_copy` modul-docstringjét. Nálunk ez a kapcsoló
    # az, hogy a hívó ad-e célútvonalat:
    #
    #   * `saveCopyRows(rows)`  — nem ad ⇒ a mért `-001` minta,
    #     kérdés nélkül, TÖBB képre is (a menüpont felirata ellipszis
    #     nélküli: `Save a Cop&y`).
    #   * `saveRowAs(row, url)` — ad ⇒ a fájlválasztóból jött út, EGY
    #     képre (`Save &As...`, ellipszissel).

    @Slot(int, result=str)
    def suggestedCopyUrl(self, row) -> str:  # noqa: N802 — QML-stílus
        """A „Mentés másként…" fájlválasztójának alapértelmezett célja.

        A mért `-001` mintát ajánljuk fel: a felhasználó átírhatja, de a
        felkínált név sosem a forrásé — az eredeti is elutasítaná
        (`IDS_CANT_SAVE_TO_SAME`)."""
        records = self._selected_records([row])
        if not records:
            return ""
        record = records[0]
        return QUrl.fromLocalFile(
            str(next_copy_path(Path(record.folder_path) / record.name))
        ).toString()

    @Slot(list)
    def saveCopyRows(self, rows) -> None:  # noqa: N802 — QML-stílus
        """„Másolat mentése": a szerkesztések beégetve ÚJ fájlba.

        A forrás — se a képe, se az ini-bejegyzése — nem változik."""
        self._save_copies(self._selected_records(rows), target=None)

    @Slot(int, str)
    def saveRowAs(self, row, target_url: str) -> None:  # noqa: N802 — QML-stílus
        """„Mentés másként…": a felhasználó választotta célútvonalra."""
        cel = QUrl(target_url).toLocalFile() if target_url else ""
        if not cel:
            # A fájlválasztó megszakítása NEM hiba — de a hívó (és a
            # teszt) a befejezés-jelzésre vár, némán nem térhetünk vissza.
            self.saveCopyFinished.emit(0, 0)
            return
        self._save_copies(self._selected_records([row]), target=Path(cel))

    def _save_copies(self, records, *, target: Path | None) -> None:
        """A másolat-mentés közös háttérszálas útja."""
        items = [
            (Path(r.folder_path) / r.name, int(r.rotate_steps or 0), r.filters or "")
            for r in records
        ]
        if not items:
            self.saveCopyFinished.emit(0, 0)
            return
        self._ensure_save_progress()
        self._saveProgressTick.emit(0, len(items), 1)

        def worker():
            done, failed = 0, 0
            # #1566: az UTOLSÓ ténylegesen kiírt célfájl — ez lesz az
            # értesítés kattintási célja. Több képnél a mappájuk közös (a
            # `-001` minta a forrás mellé ír), a „Mentés másként…" pedig
            # eleve EGY képre hat, tehát az utolsó út mindig jó mappára
            # mutat.
            utolso_cel = ""
            jelentett_agak: set[str] = set()
            for index, (path, rotate_steps, filters) in enumerate(items):
                try:
                    rendered = _render_for_save(path, rotate_steps, filters)
                    eredmeny = save_copy(
                        path,
                        rendered,
                        EditSession.from_value(filters),
                        target_path=target,
                    )
                except (*_SAVE_ERRORS, FileNameCollisionError) as error:
                    failed += 1
                    ag = save_error_kind(error)
                    if ag not in jelentett_agak:
                        jelentett_agak.add(ag)
                        self._report_save_error(error, target or path)
                else:
                    done += 1
                    utolso_cel = str(eredmeny.target_path)
                    # #1539: a TÉNYLEGES célút megy be, nem a látott mappa
                    self.noteOutputWritten(utolso_cel)
                self._saveProgressTick.emit(index + 1, len(items), 1)
            self._saveProgressTick.emit(len(items), len(items), 0)
            # #1566: a FELÜLETI visszajelzés ELŐBB megy ki, mint a gépies
            # befejezés-jelzés. Mindkettő a GUI-szálra sorolódik, sorrendben
            # — így a `saveCopyFinished`-re váró hívó (és teszt) számára az
            # értesítés már kézbesítve van, nem versenyeznek.
            self.saveCopyReady.emit(done, utolso_cel)
            self.saveCopyFinished.emit(done, failed)

        self._start_background(worker, name="picasapy-save-copy")

    @Slot(list)
    def revertRowsToOriginal(self, rows) -> None:  # noqa: N802 — QML-stílus
        """„Visszaállítás": az eredeti visszamásolása a biztonsági
        mentésből — a szerkesztések ELVESZNEK (a felület ezért kérdez rá az
        eredeti szövegével)."""
        self._run_restore(rows, revert, self.revertFinished)

    @Slot(list)
    def undoLastSave(self, rows) -> None:  # noqa: N802 — QML-stílus
        """„Utolsó mentés visszavonása": a legutóbbi lemezre írás előtti
        állapot jön vissza, de a **szerkesztések megmaradnak** — ez a Picasa
        köztes fokozata a Mentés és a Visszaállítás között."""
        self._run_restore(rows, undo_save, self.undoSaveFinished)

    def _record_saved_state(self, items) -> None:
        """A mentés-műveletek utáni ini-állapot átvezetése a #644-es naplóra.

        ## Miért kell (a hamis riasztás ugyanolyan kár, mint a néma veszteség)

        A napló azt őrzi, MI milyen `filters=` láncot írtunk ki utoljára, és
        a nézet feltöltésekor riaszt, ha az eltűnt. A mentés viszont MAGA
        veszi el a `filters=`-t: a láncot a pixelekbe égeti, a kulcsot törli,
        a tartalmát a `redo=`-ba forgatja át (`edit/save.py`). Ha a naplót nem
        vezetnénk át, a mentés utáni ELSŐ nézetfrissítés minden mentett képre
        azt állítaná, hogy „a szerkesztésed eltűnt" — a felhasználó pedig egy
        kattintással vissza is írhatná a láncot `filters=`-be, ami a már
        beégetett effektet MÁSODSZOR is ráfuttatná. Az átvezetés tehát nem
        kényelmi kérdés, hanem adatvédelem.

        ## A `redo=` NEM kerül a naplóba láncként (#750 döntés)

        Kézenfekvő lenne a `redo=` értékét is védeni — mégsem tesszük, két
        okból, és mindkettő a kár irányáról szól:

        1. **A detektor a `filters=`-t nézi.** A `detect_lost_edits` az index
           `filters=` mezőihez hasonlít; mentés után az minden mentett képnél
           üres. Egy `redo=`-t őrző bejegyzés így ÖRÖKKÉ veszteséget jelezne
           — a védelem zajjá válna, és a felhasználó megtanulná elhessegetni.
        2. **A helyreállítás célkulcsa rossz volna.** A
           `restoreOverwrittenEdit` a `filters=`-be ír vissza. Egy beégetett
           láncot oda visszatéve dupla-szerkesztés keletkezne (#297) — az
           eredménye ROSSZABB, mint a `redo=` elvesztése, amiből legfeljebb
           az „Utolsó mentés visszavonása" kényelme vész el, a pixelek nem: a
           mentés előtti bájtok a `.picasaoriginals` sorszámozott
           pillanatképében megvannak.

        A `redo=` valódi védelme külön alakú mechanizmust kívánna (saját
        bejegyzés-fajta, saját visszaírási cél és saját felületi üzenet) —
        önálló jegyre való, nem erre.

        Az „Utolsó mentés visszavonása" ellenben VISSZAÍRJA a láncot
        `filters=`-be: onnantól megint van mit védeni, ezért ott a
        visszakapott láncot naplózzuk.
        """
        if items:
            self.recordSavedChains(items)

    def _run_restore(self, rows, operation, finished_signal) -> None:
        paths = [
            Path(r.folder_path) / r.name for r in self._selected_records(rows)
        ]
        if not paths:
            finished_signal.emit(0, 0)
            return

        def worker():
            done, failed, details = 0, 0, []
            naplo: list[tuple[str, str]] = []
            for path in paths:
                try:
                    result = operation(path)
                except _SAVE_ERRORS as error:
                    failed += 1
                    if len(details) < _FAILED_DETAILS_LIMIT:
                        details.append(f"{path.name}: {error}")
                else:
                    done += 1
                    # #750: az „Utolsó mentés visszavonása" a `redo=`-ból
                    # VISSZAÍRJA a láncot `filters=`-be (`restored_filters`)
                    # — onnantól megint van mit védeni. A „Visszaállítás"
                    # minden szerkesztés-könyvelést töröl, ott az üres lánc
                    # (a `getattr` alapértéke) törli a bejegyzést.
                    naplo.append((str(path), getattr(result, "restored_filters", "")))
            self._record_saved_state(naplo)
            if details:
                self.saveFailedDetails.emit(details)
            finished_signal.emit(done, failed)

        self._start_background(worker, name="picasapy-save-restore")
