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

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Signal, Slot

from picasapy.cvimage import read_image_bytes
from picasapy.edit.save import SaveError, revert, save_edited, undo_save
from picasapy.edit.session import EditSession
from picasapy.ini import IniConflictError, IniSaveError
from picasapy.render.chain import apply_filters, can_render_filter

from .worker_thread import BackgroundWorkerMixin

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
        visszaállítani) — a menü ezzel tiltja a pontjait.
        """
        from picasapy.edit.save import ORIGINALS_DIR_NAME

        for record in self._selected_records(rows):
            folder = Path(record.folder_path) / ORIGINALS_DIR_NAME
            if folder.is_dir() and any(folder.glob(f"{Path(record.name).stem}*")):
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

        def worker():
            done, failed, details = 0, 0, []
            naplo: list[tuple[str, str]] = []
            for path, rotate_steps, filters in records:
                try:
                    rendered = _render_for_save(path, rotate_steps, filters)
                    save_edited(path, rendered, EditSession.from_value(filters))
                except _SAVE_ERRORS as error:
                    failed += 1
                    if len(details) < _FAILED_DETAILS_LIMIT:
                        details.append(f"{path.name}: {error}")
                else:
                    done += 1
                    # #750: a sikeres mentés ÜRES lánccal jelent a naplónak,
                    # ami ott a bejegyzés TÖRLÉSÉT jelenti. Ld. a `redo=`
                    # döntést a `_record_saved_state` docstringjében.
                    naplo.append((str(path), ""))
            self._record_saved_state(naplo)
            if details:
                self.saveFailedDetails.emit(details)
            self.saveFinished.emit(done, failed)

        self._start_background(worker, name="picasapy-save")

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
