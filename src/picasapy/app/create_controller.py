"""Létrehozás menü: kollázs és mozgófilm (#29) — az AppController szelete.

Mindkét művelet háttérszálon fut (nagy képeknél, NAS-on percekig tarthat),
és ugyanazt a jelzés-mintát követi, mint az export (#16/#136):

- `...Finished(útvonal, felhasznált, kihagyott)` — sikeres futás,
- `...Failed(üzenet)` — emberi nyelvű hibaüzenet (a hívó dialógusa mutatja),
- a mozgófilm közben `movieProgress(kész, összes)` képenként.

A dialógusok a célfájlt `file://` URL-ként adják át (a QML FileDialog
alakja) — a `to_local_path` fordítja vissza helyi útvonallá.

## A kollázs-piszkozat (#960)

A Picasa szerkesztés közben külön szálon írta az **`autosave.cxf`**
piszkozatot, és a következő indításkor felajánlotta a visszaállítást (spec
1.5). Nálunk a piszkozat ott keletkezik, ahol a vászon geometriája
egyáltalán létezik: az élő előnézet és a mentés `CollageReport.nodes`-
csomópontjaiból (#942). Két szabály tartja értelmesnek:

1. **Sosem találunk ki geometriát.** Ha a rajzoló nem ad csomópontot (a
   Többszörös exponálás nem helyez el képeket), piszkozat sem születik — a
   formátum épp azt ígéri, hogy pontosan visszaáll.
2. **A piszkozat hibája sosem viheti el a kollázst.** Írása és eldobása
   naplózott, de nyelt hiba: a felhasználó munkája fontosabb, mint a
   biztonsági másolata.

Sikeres mentés után a piszkozat betöltötte a szerepét, ezért eldobjuk.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.collage import write_collage
from picasapy.collage.autosave import (
    discard_autosave,
    has_recoverable_draft,
    write_autosave,
)
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.picasa_render import PicasaCollageSettings, make_picasa_collage
from picasapy.app.collage_preview import CollagePreviewProvider
from picasapy.collage.themes import BORDER_THEMES, COLLAGE_THEMES, NOBORDER
from picasapy.movie import MovieSettings, export_movie

from . import collage_output, collage_prefs
from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

logger = logging.getLogger(__name__)

# A kollázs alapértelmezett vászonmérete — nyomtatható, de nem irreális.
_COLLAGE_SIZE = (1600, 1200)
# Egy kollázsba/filmbe ennél több képet nincs értelme tenni: a cellák
# olvashatatlanul kicsik lennének, a videó pedig órákig tartana.
_MAX_ITEMS = 200
# A képek közti áttűnés felső korlátja (mp) — ennél hosszabb áttűnés
# elmossa a diavetítés ritmusát.
_MAX_TRANSITION_S = 0.5
# #920: az élő előnézet mérete. Kicsi, mert a Képkupac pakolója
# időkorlátos keresést futtat — teljes felbontáson a felület beragadna.
_PREVIEW_SIZE = (640, 480)


class CreateMixin(BackgroundWorkerMixin):
    """Kollázs- és mozgófilm-készítés a kijelölésből, háttérszálon."""

    # (célfájl, felhasznált, kihagyott, ebből NEM TALÁLHATÓ) — #459/3: a
    # hiányzó fájl más eset, mint az olvashatatlan, külön mondatot kap
    collageFinished = Signal(str, int, int, int)
    collageFailed = Signal(str)
    movieProgress = Signal(int, int)
    movieFinished = Signal(str, int, int, int)
    movieFailed = Signal(str)
    #: #920: az élő előnézet elkészült — a paraméter a revízió, amivel a
    #: QML törni tudja a Qt kép-gyorsítótárát (`?rev=<n>`).
    collagePreviewReady = Signal(int)
    collagePreviewFailed = Signal(str)
    collageSeedChanged = Signal()
    #: #960: a `collageDraftAvailable` property jelzése — erre köt rá a
    #: visszaállítást felajánló párbeszéd (a párbeszédet a kollázs-panel
    #: sorozata építi, ez itt a vezérlő-oldali horog).
    collageDraftAvailableChanged = Signal()

    def _ensure_collage_wired(self) -> None:
        """Lusta, egyszeri állapot-inicializálás (a `TrayMixin.
        _ensure_tray_wired` mintája) — a `controller.py` FORRÓ FÁJL, ezért a
        szelet a saját állapotát maga hozza létre, nem az `__init__`-ben.
        """
        if getattr(self, "_collage_wired", False):
            return
        self._collage_wired = True
        self._collage_preview = CollagePreviewProvider()
        self._collage_preview_revision = 0
        self._collage_seed = 0

    @property
    def collage_preview_provider(self) -> CollagePreviewProvider:
        """A képszolgáltató, amit az `application.py` regisztrál."""
        self._ensure_collage_wired()
        return self._collage_preview

    # --- A kollázs-piszkozat (#960) ---------------------------------------

    def _collage_draft_dir(self) -> Path:
        """A piszkozat mappája: a „Kollázsok" album (spec 1.5).

        A piszkozatnak RÖGZÍTETT helye kell legyen: az összeomlás utáni
        felajánlás akkor is meg kell találja, ha a felhasználó a célfájlt
        még ki sem választotta."""
        return collage_output.output_dir(
            self._get_settings().value(collage_prefs.OUTPUT_DIR_KEY)
        )

    def _save_collage_draft(self, nodes, settings: PicasaCollageSettings) -> None:
        """A vászon csomópontjaiból piszkozat a lemezre, atomi írással.

        Csomópont nélkül (Többszörös exponálás) NEM ír: kitalált geometria
        rosszabb volna a semminél. A hiba nyelt — a piszkozat baja sosem
        viheti el a felhasználó kollázsát."""
        if not nodes:
            return
        try:
            write_autosave(
                self._collage_draft_dir(), project_from_nodes(nodes, settings)
            )
        except (OSError, ValueError) as hiba:
            logger.warning("A kollázs-piszkozat nem írható: %s", hiba)
            return
        self.collageDraftAvailableChanged.emit()

    def _drop_collage_draft(self) -> None:
        """A piszkozat eldobása — sikeres mentés után, vagy ha a felhasználó
        nemet mond a visszaállításra."""
        if discard_autosave(self._collage_draft_dir()):
            self.collageDraftAvailableChanged.emit()

    @Property(bool, notify=collageDraftAvailableChanged)
    def collageDraftAvailable(self) -> bool:  # noqa: N802 (QML-stílusú név)
        """Van-e ÉP, visszaállítható kollázs-piszkozat.

        A QML ezen a property-n át tudja felajánlani a visszaállítást
        induláskor (spec 1.5, `collage::recoveredautosave`). Szándékosan a
        tényleges beolvasással válaszol: sérült piszkozatot felajánlani
        rosszabb, mint nem felajánlani semmit."""
        return has_recoverable_draft(self._collage_draft_dir())

    @Slot()
    def refreshCollageDraft(self) -> None:  # noqa: N802 (QML-stílusú név)
        """A felajánlás újraértékelése (pl. induláskor, a felület
        felépülése után)."""
        self.collageDraftAvailableChanged.emit()

    @Slot()
    def discardCollageDraft(self) -> None:  # noqa: N802 (QML-stílusú név)
        """A piszkozat eldobása a felhasználó kérésére („nem állítom
        vissza")."""
        self._drop_collage_draft()

    def _selected_sources(self, rows) -> tuple[Path, ...]:
        """A kijelölt sorokból forrás-útvonalak, a rács sorrendjében."""
        photos = self._photos.photos
        return tuple(
            Path(photos[int(r)].folder_path) / photos[int(r)].name
            for r in rows
            if 0 <= int(r) < len(photos)
        )

    def _tray_sources(self) -> tuple[Path, ...]:
        """A KÉPTÁLCA tartalma forrás-útvonalként, beszúrási sorrendben
        (#455, 3. teendő).

        Az eredetiben a tálca alatti műveletsor a tálca tartalmán futott,
        nem a pillanatnyi kijelölésen. A tálca mappákon átnyúlik, ezért itt
        nem rács-sorokból, hanem a `heldPaths`-ből dolgozunk — az a globális
        indexből olvas, és az időközben eltűnt képeket kihagyja.
        """
        return tuple(Path(path) for path in (self.heldPaths or ()))

    def _sources_for(self, rows) -> tuple[Path, ...]:
        """A művelet forrása: a TÁLCA, ha van benne kép; egyébként a
        kijelölés (így az üres tálcás, mai viselkedés nem romlik el)."""
        tray = self._tray_sources()
        return tray if tray else self._selected_sources(rows)

    @Slot(list, str, str)
    def requestCollagePreview(self, rows, kind: str, border: str = NOBORDER) -> None:
        """#920: élő előnézet a jelenlegi beállításokkal, háttérszálon.

        A Kollázs eddig VAKON dolgozott: a felhasználó választott, a program
        fájlba renderelt, és csak utána derült ki, mit kapott. Az eredetiben
        a panel jobb oldalán élő vászon áll.

        Az előnézet szándékosan KICSI (`_PREVIEW_SIZE`): a Képkupac pakolója
        időkorlátos keresést futtat, és a teljes felbontású renderelés minden
        csúszka-mozdulatnál használhatatlanná tenné a felületet.
        """
        self._ensure_collage_wired()
        sources = self._sources_for(rows)[:_MAX_ITEMS]
        if not sources:
            self._collage_preview.clear()
            self._collage_preview_revision += 1
            self.collagePreviewReady.emit(self._collage_preview_revision)
            return
        if kind not in COLLAGE_THEMES or border not in BORDER_THEMES:
            self.collagePreviewFailed.emit(self.tr("Unknown collage type."))
            return

        settings = PicasaCollageSettings(
            theme=kind,
            border=border,
            width=_PREVIEW_SIZE[0],
            height=_PREVIEW_SIZE[1],
            seed=self._collage_seed,
        )

        def worker():
            try:
                report = make_picasa_collage(sources, settings)
            except (ValueError, OSError) as error:
                self.collagePreviewFailed.emit(str(error))
                return
            self._collage_preview.set_image(report.image)
            # #960: az élő előnézet a SZERKESZTÉS állapota — a piszkozat
            # innen kapja a vászon valódi geometriáját
            self._save_collage_draft(report.nodes, settings)
            self._collage_preview_revision += 1
            self.collagePreviewReady.emit(self._collage_preview_revision)

        self._start_background(worker, name="picasapy-collage-preview")

    @Slot()
    def shuffleCollage(self) -> None:
        """#920: a két véletlenszerűsítő gomb magja — új elrendezés ugyanazokból
        a képekből. A Képkupac szórása és a Mozaik pakolója is a magból dolgozik.
        """
        self._ensure_collage_wired()
        self._collage_seed += 1
        self.collageSeedChanged.emit()

    @Property(int, notify=collageSeedChanged)
    def collageSeed(self) -> int:
        self._ensure_collage_wired()
        return self._collage_seed

    @Slot(list, str, str)
    @Slot(list, str, str, str)
    def makeCollage(self, rows, kind: str, target_url: str, border: str = NOBORDER) -> None:
        """Kollázs a kijelölt képekből a megadott célfájlba (JPEG).

        `kind`: a `picasapy.collage.themes.COLLAGE_THEMES` egyike — a HAT
        Picasa-elrendezés. `border`: a `BORDER_THEMES` egyike.

        **#431: ez a slot a #29-es, saját tervezésű négy elrendezésről a
        Picasa-hű hatra állt át.** A mag (`picasa_render`) 2026-08-16 óta
        készen állt, de senki nem hívta — a felület a régi rajzolót
        használta, tehát a kollázs működött, csak nem a Picasa
        elrendezéseivel.
        """
        self._ensure_collage_wired()
        sources = self._sources_for(rows)[:_MAX_ITEMS]
        target = to_local_path(target_url)
        if not sources:
            self.collageFailed.emit(self.tr("No pictures are selected."))
            return
        if not target:
            self.collageFailed.emit(self.tr("No target file was chosen."))
            return
        if kind not in COLLAGE_THEMES:
            self.collageFailed.emit(self.tr("Unknown collage type."))
            return
        if border not in BORDER_THEMES:
            self.collageFailed.emit(self.tr("Unknown picture frame."))
            return

        settings = PicasaCollageSettings(
            theme=kind,
            border=border,
            width=_COLLAGE_SIZE[0],
            height=_COLLAGE_SIZE[1],
            # #920: amit az előnézeten LÁT, azt kapja mentéskor is
            seed=self._collage_seed,
        )

        def worker():
            try:
                report = make_picasa_collage(sources, settings)
                if not report.used:
                    self.collageFailed.emit(
                        self.tr("None of the selected pictures could be read.")
                    )
                    return
                # #960: a piszkozat a mentés ELŐTT készül el — épp az az
                # eset a lényeg, amikor a hosszú írás közben vész el minden
                self._save_collage_draft(report.nodes, settings)
                path = write_collage(Path(target), report.image)
            except (ValueError, OSError) as error:
                self.collageFailed.emit(str(error))
                return
            # a mentés sikerült: a piszkozat betöltötte a szerepét
            self._drop_collage_draft()
            self.collageFinished.emit(
                str(path),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-collage")

    @Slot(list, str, int, float)
    def exportMovie(
        self, rows, target_url: str, height: int, seconds_per_photo: float
    ) -> None:
        """Diavetítés-videó a kijelölt képekből (MP4).

        `height`: a videó magassága (720/1080); a szélesség 16:9-ből jön."""
        sources = self._sources_for(rows)[:_MAX_ITEMS]
        target = to_local_path(target_url)
        if not sources:
            self.movieFailed.emit(self.tr("No pictures are selected."))
            return
        if not target:
            self.movieFailed.emit(self.tr("No target file was chosen."))
            return
        try:
            settings = MovieSettings(
                width=(height * 16 // 9) // 2 * 2,
                height=height,
                seconds_per_photo=seconds_per_photo,
                # az áttűnés a képenkénti idő harmada, de legfeljebb 0,5 mp:
                # rövid diáknál (1 mp) a fix 0,5 mp-es áttűnés hosszabb
                # lenne, mint amennyi ideig a kép áll — az érvénytelen
                transition_seconds=min(_MAX_TRANSITION_S, seconds_per_photo / 3),
            )
        except ValueError as error:
            self.movieFailed.emit(str(error))
            return

        def worker():
            try:
                report = export_movie(
                    sources,
                    Path(target),
                    settings,
                    progress=lambda done, total: self.movieProgress.emit(done, total),
                )
            except (ValueError, OSError, RuntimeError) as error:
                self.movieFailed.emit(str(error))
                return
            if not report.used:
                self.movieFailed.emit(
                    self.tr("None of the selected pictures could be read.")
                )
                return
            self.movieFinished.emit(
                str(report.target),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-movie")
