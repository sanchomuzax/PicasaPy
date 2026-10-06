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

1. **Sosem találunk ki geometriát.** Ha a rajzoló nem ad csomópontot,
   piszkozat sem születik — a formátum épp azt ígéri, hogy pontosan
   visszaáll.

   ⚠️ A Többszörös exponálás **nem** ilyen eset (#1248). Geometriát tényleg
   nem helyez el, de a `.cxf`-nek tudnia kell, MELYIK képekből készült; az
   eredeti is képenként egy, teljes lapos csomópontot ír (mérve:
   `referencia/kollazs-golden/AI7.cxf`). Amíg nálunk üres maradt, az
   újraszerkesztés fekete lapot adott, a mentés pedig azt jelentette, hogy
   „az összes képet eltávolították".
2. **A piszkozat hibája sosem viheti el a kollázst.** Írása és eldobása
   naplózott, de nyelt hiba: a felhasználó munkája fontosabb, mint a
   biztonsági másolata.

Sikeres mentés után a piszkozat betöltötte a szerepét, ezért eldobjuk.
"""

from __future__ import annotations

import logging
from pathlib import Path
from xml.etree import ElementTree

from PySide6.QtCore import Property, QUrl, Signal, Slot

from picasapy.collage import write_collage
from picasapy.collage.autosave import (
    discard_autosave,
    has_recoverable_draft,
    recover_orphan_draft,
    write_autosave,
)
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.picasa_render import PicasaCollageSettings, make_picasa_collage
from picasapy.app.collage_preview import CollagePreviewProvider
from picasapy.collage.themes import BORDER_THEMES, COLLAGE_THEMES, NOBORDER
from picasapy.movie import MovieSettings, export_movie
from picasapy.movie.mxf import (
    MxfAtmenet,
    MxfForras,
    MxfSzovegParam,
    MxfProjekt,
    projekt_utvonal,
    read_mxf,
    write_mxf,
)

from . import collage_output, collage_prefs
from .formatting import to_local_path
from .poster_controller import PosterMixin

logger = logging.getLogger(__name__)

# A kollázs alapértelmezett vászonmérete — nyomtatható, de nem irreális.
_COLLAGE_SIZE = (1600, 1200)
# Egy kollázsba/filmbe ennél több képet nincs értelme tenni: a cellák
# olvashatatlanul kicsik lennének, a videó pedig órákig tartana.
_MAX_ITEMS = 200
# A képek közti áttűnés felső korlátja (mp) — ennél hosszabb áttűnés
# elmossa a diavetítés ritmusát.
_MAX_TRANSITION_S = 0.5
_MOVIE_SIZES = (
    (320, 240), (640, 480), (800, 600), (1024, 768), (1600, 1200),
    (1280, 720), (1920, 1080),
)
_MOVIE_TRANSITIONS = (
    "cut", "dissolve", "dissolveblack", "dissolvewhite", "wipeleft",
    "wiperight", "wipeup", "wipedown", "diagwipeul", "diagwipeur",
    "diagwipedl", "diagwipedr", "pushleft", "pushright", "pushtop",
    "pushdown", "circlein", "circleout", "kenburns", "kenburnsaoi",
    "timelapse", "rect",
)
_MOVIE_PREFERENCES = {
    "captions": ("CMakeMoviePanel::showcaptions", False),
    "cropfit": ("CMakeMoviePanel::cropfit", False),
    "removeLowResFaces": ("makemoviepanel/remove_low_res_faces", False),
}
# #920: az élő előnézet mérete. Kicsi, mert a Képkupac pakolója
# időkorlátos keresést futtat — teljes felbontáson a felület beragadna.
_PREVIEW_SIZE = (640, 480)


class CreateMixin(PosterMixin):
    """Poszter-, kollázs- és mozgófilm-készítés a kijelölésből."""

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
    moviePreferencesChanged = Signal()
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

    @Property(int, notify=moviePreferencesChanged)
    def movieResolutionIndex(self) -> int:  # noqa: N802
        """A normál film méretindexe (`Preferences\\makemovieres`)."""
        try:
            return max(0, min(6, int(self._get_settings().value("makemovieres", 1))))
        except (TypeError, ValueError):
            return 1

    @Property(int, notify=moviePreferencesChanged)
    def faceMovieResolutionIndex(self) -> int:  # noqa: N802
        """Az arc-film méretindexe (`facemakemovieres`), alapból 3 (#4391).

        A Picasa ezt a kulcsot olvassa, de a beállított új értéket nem írja
        vissza; a QML-ben is megmarad ez a nem mentő viselkedés.
        """
        try:
            return max(
                0,
                min(6, int(self._get_settings().value("facemakemovieres", 3))),
            )
        except (TypeError, ValueError):
            return 3

    @Slot(int)
    def setMovieResolutionIndex(self, index: int) -> None:  # noqa: N802
        """A hét eredeti méret közül a választott index megőrzése."""
        index = max(0, min(6, int(index)))
        self._get_settings().setValue("makemovieres", index)
        self.moviePreferencesChanged.emit()

    @Property(int, notify=moviePreferencesChanged)
    def movieVolume(self) -> int:  # noqa: N802
        """A videó hangerőcsúszkájának Preferences/movievolume értéke."""
        try:
            return max(0, min(1000, int(self._get_settings().value("movievolume", 500))))
        except (TypeError, ValueError):
            return 500

    @Slot(int)
    def setMovieVolume(self, volume: int) -> None:  # noqa: N802
        """A hangerő elmentése az eredeti 0..1000-es tartományban."""
        volume = max(0, min(1000, int(volume)))
        self._get_settings().setValue("movievolume", volume)
        self.moviePreferencesChanged.emit()

    @Slot(str, result=bool)
    def moviePreference(self, name: str) -> bool:  # noqa: N802
        """A filmkészítő hivatalos Preferences-kulcsának beolvasása."""
        if name not in _MOVIE_PREFERENCES:
            return False
        key, default = _MOVIE_PREFERENCES[name]
        return bool(self._get_settings().value(key, default))

    @Slot(str, bool)
    def setMoviePreference(self, name: str, value: bool) -> None:  # noqa: N802
        """Csak a specifikációban szereplő filmkészítő-kulcsokat írja."""
        if name not in _MOVIE_PREFERENCES:
            return
        key, _default = _MOVIE_PREFERENCES[name]
        self._get_settings().setValue(key, bool(value))
        self.moviePreferencesChanged.emit()

    @Slot(list, result=list)
    def movieSourceUrls(self, rows) -> list[str]:  # noqa: N802
        """A film forrásképeinek `file:` URL-je, a dia-előnézethez."""
        if rows and isinstance(rows[0], str):
            paths = (Path(to_local_path(str(row))) for row in rows)
        else:
            paths = self._sources_for(rows)
        return [
            QUrl.fromLocalFile(str(path)).toString()
            for path in paths
        ]

    @Slot(list, result=list)
    def movieClipNames(self, rows) -> list[str]:  # noqa: N802
        """A film kliptálcáján megjelenő képfájlnevek."""
        paths = (
            (Path(to_local_path(str(row))) for row in rows)
            if rows and isinstance(rows[0], str)
            else self._sources_for(rows)
        )
        return [Path(path).name for path in paths]

    @Slot(list, result=list)
    def selectedMovieSourceUrls(self, rows) -> list[str]:  # noqa: N802
        """Új klipek a könyvtár aktuális kijelöléséből, a tálcától függetlenül."""
        return [
            QUrl.fromLocalFile(str(path)).toString()
            for path in self._selected_sources(rows)
        ]

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
        """A felhasználó nemet mond a visszaállításra (#979).

        ⚠️ **Ez NEM törlés.** Az eredeti Picasa az elárvult automentést
        nem dobja el, hanem ÁTNEVEZI („Helyreállított automatikus
        másolat") és indexeli, hogy a felhasználó megtalálja a Kollázsok
        albumban (spec 9.2/b, `0x008419e0`). A munkája így akkor sem
        vész el, ha a felajánlásra nemet mondott — meggondolhatja magát.

        A mentés utáni eldobás (`_drop_collage_draft`) továbbra is
        TÖRLÉS: ott a piszkozat betöltötte a szerepét, és a megőrzése
        csak szemetelne.

        ⚠️ Az eredeti mindezt INDULÁSKOR, kérdés nélkül teszi. Nálunk van
        egy felajánlás-lépés (#1064), ami az eredetiben nincs; ha
        induláskor neveznénk át, a felajánlásnak nem maradna mit
        felajánlania. Ezért a „nem" ágra kötjük — a végeredmény ugyanaz:
        a piszkozat megmarad, néven nevezve.
        """
        uj_ut = recover_orphan_draft(self._collage_draft_dir())
        if uj_ut is not None:
            self.collageDraftAvailableChanged.emit()

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

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a magot a `shuffleCollage`
    # lépteti, az eredmény a vásznon látszik — a szám maga nem való a felületre.
    @property
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
        # #1539: a bekötés a GUI-szálon, a háttérszál indítása ELŐTT
        self._ensure_output_resync_wired()
        if rows and isinstance(rows[0], str):
            sources = tuple(Path(to_local_path(str(row))) for row in rows)[:_MAX_ITEMS]
        else:
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
            # #1539: a kollázs a figyelt gyökér alatti, MÉG NEM INDEXELT
            # mappába is mehet (a fájlválasztó nincs korlátozva). Mérve: a
            # figyelő nélkül 25 s alatt sem jelent meg — a #1275 lekérdezés
            # a LÁTOTT mappát nézi, a kollázs viszont egy másikba került.
            self.noteOutputWritten(str(path))
            self.collageFinished.emit(
                str(path),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-collage")

    def _alapertelmezett_film_cel(self, sources) -> Path:
        """A film célfájlja, ha a felhasználó nem adott meg egyet (#1977).

        A mappa a `Picasa` alatti (meglévő vagy honosított) Filmek-mappa,
        és **projekt-mappaként be is jelöljük** — enélkül a bal hasáb
        Projektek gyűjteménye nem tudja hova sorolni (ugyanaz a hiba,
        amit a kollázsnál a `write_album_ini` javított).

        A fájlnév töve a KÖZÖS forrásmappa neve; ha a képek több mappából
        jönnek, a mért alapnév (`diavetites_jellegu_film`).
        """
        from . import movie_output

        # A `_get_settings()` a többi ág mintája (ld. a piszkozat-mappát
        # a 124. sorban) — enélkül a próbák a VALÓDI `~/Képek`-be írnának.
        beallitott = self._get_settings().value(movie_output.OUTPUT_DIR_KEY)
        mappa = movie_output.tartalek_mappa(movie_output.output_dir(beallitott))
        movie_output.write_album_ini(mappa, mappa.name)
        szulok = {Path(s).parent for s in sources}
        cim = next(iter(szulok)).name if len(szulok) == 1 else ""
        return movie_output.output_path(mappa, cim)

    #: #1977 REGRESSZIÓ (#2185): ez a dekorátor korábban ITT állt, de a
    #: `_alapertelmezett_film_cel` beszúrása ALÁJA került, és így a
    #: PRIVÁT segítő kapta meg a slotot — az `exportMovie` pedig
    #: kiesett a meta-objektumból, tehát a QML `controller.exportMovie(…)`
    #: hívása nem érte el. A Mozgófilm-párbeszéd OK gombja így
    #: NÉMÁN nem csinált semmit. Mérve: `staticMetaObject`-ben
    #: `_alapertelmezett_film_cel(QVariantList,QString,int,double)`
    #: szerepelt, `exportMovie` nem.
    @staticmethod
    def _film_beallitas(
        width: int,
        height: int,
        seconds_per_photo: float,
        transition_seconds: float | None = None,
        transition_type: str = "dissolve",
        audio_path: Path | None = None,
        audio_option: int = 0,
        text_slides: list[dict] | None = None,
        options: dict | None = None,
    ) -> MovieSettings:
        """A `MovieSettings` összeállítása — külön metódus, hogy mérhető legyen.

        #1977 (7. pont): a szélesség KAPOTT érték, nem 16:9-ből
        származtatott. Az eredeti hét mérete közül **öt 4:3-as**
        (320×240, 640×480, 800×600, 1024×768, 1600×1200); azokra a
        származtatás torzítana — 1024-es magasságból 1820 jönne ki 768
        helyett.

        `width=0` a RÉGI, négyargumentumos hívási alak: ilyenkor 16:9-ből
        számolunk, tehát a meglévő 720p/1080p hívások változatlanok.
        """
        if not width:
            width = (height * 16 // 9) // 2 * 2
        if transition_seconds is None:
            transition_seconds = min(_MAX_TRANSITION_S, seconds_per_photo / 3)
        return MovieSettings(
            width=max(2, int(width)) // 2 * 2,
            height=height,
            seconds_per_photo=seconds_per_photo,
            # az áttűnés a képenkénti idő harmada, de legfeljebb 0,5 mp:
            # rövid diáknál (1 mp) a fix 0,5 mp-es áttűnés hosszabb
            # lenne, mint amennyi ideig a kép áll — az érvénytelen
            transition_seconds=min(
                max(0.0, transition_seconds), seconds_per_photo * 0.9
            ),
            transition_type=transition_type,
            audio_path=audio_path,
            audio_option=audio_option,
            text_slides=tuple(text_slides or ()),
            show_captions=bool((options or {}).get("showcaptions", False)),
            show_dates=bool((options or {}).get("showdates", False)),
            cropfit=bool((options or {}).get("cropfit", False)),
            remove_low_res_faces=bool((options or {}).get("removelowresfaces", False)),
            ordering=max(0, min(2, int((options or {}).get("ordering", 1)))),
            burstmodethresh=max(
                0, min(86400, int((options or {}).get("burstmodethresh", 0)))
            ),
        )

    @staticmethod
    def _film_projekt(sources, settings) -> MxfProjekt:
        """A film állapota `.mxf`-projektként (#3191).

        A felület által állítható méret, hangsáv, opciók, rendezés,
        szöveges diák és áttűnés kerül a projektbe. A formátum megengedi,
        hogy a diánkénti `trans` felülírja az album-szintű `defaulttrans`-ot.
        """
        try:
            felbontas = _MOVIE_SIZES.index((settings.width, settings.height))
        except ValueError:
            felbontas = 1
        atmenet_tipus = _MOVIE_TRANSITIONS.index(settings.transition_type)
        alap = MxfAtmenet(
            transition=atmenet_tipus,
            advanceinterval=float(settings.seconds_per_photo),
            transitiontime=float(settings.transition_seconds),
        )
        atmenetek = [
            MxfAtmenet(
                transition=atmenet_tipus,
                advanceinterval=alap.advanceinterval,
                transitiontime=alap.transitiontime,
                forras=MxfForras(index=i, filename=str(ut)),
            )
            for i, ut in enumerate(sources)
        ]
        for index, slide in enumerate(settings.text_slides):
            text_color = str(slide.get("textColor", "#ffffff")).lstrip("#")[-6:]
            try:
                packed_color = int(text_color, 16)
            except ValueError:
                packed_color = 0xFFFFFF
            background_color = str(slide.get("backgroundColor", "#000000")).lstrip("#")[-6:]
            try:
                packed_background = int(background_color, 16)
            except ValueError:
                packed_background = 0
            font = str(slide.get("font", ""))
            size = int(slide.get("size", 16))
            style = max(0, min(11, int(slide.get("style", 0))))
            weight = 700 if slide.get("bold") else 400
            forras = MxfForras(
                tipus=2,
                bkcolor=packed_background,
                index=len(sources) + index,
                text=str(slide.get("text", "")),
                szovegparam=MxfSzovegParam(
                    fontname=font,
                    size=size,
                    color=packed_color,
                    weight=weight,
                    italic=bool(slide.get("italic")),
                    outline=bool(slide.get("outline")),
                    styleid=style,
                ),
            )
            atmenetek.append(
                MxfAtmenet(
                    transition=atmenet_tipus,
                    advanceinterval=alap.advanceinterval,
                    transitiontime=alap.transitiontime,
                    forras=forras,
                )
            )
        return MxfProjekt(
            curresolution=felbontas,
            musicfile=str(settings.audio_path or ""),
            audiooption=settings.audio_option,
            showcaption=settings.show_captions,
            showdates=settings.show_dates,
            cropfit=int(settings.cropfit),
            removelowresfaces=settings.remove_low_res_faces,
            ordering=settings.ordering,
            burstmodethresh=settings.burstmodethresh,
            defaulttrans=alap,
            atmenetek=tuple(atmenetek),
        )

    # -- #2114: a film KIMENETÉTŐL vissza a projekthez ---------------------
    #
    # Az eredetiben a szerkesztő két ikergombot ismer — `editpanel/editcollage`
    # („Kollázs szerkesztése") és `editpanel/editslideshow` („Mozgófilm
    # szerkesztése") —, ugyanabban a kezelőben (`0x00567a00`), mindkettő
    # `m_hidden`: csak akkor jön elő, ha a megnyitott fájl egy PROJEKT
    # kimenete. A kollázs-ág nálunk a `.cxf`-en áll (`hasCollageProject`);
    # a film-ág feltétele a #3191 óta adott, mert a kimenet mellé kiírjuk a
    # `.mxf`-et.

    @staticmethod
    def _film_projekt_utja(video_path: str) -> Path | None:
        """A kimenet melletti `.mxf`, ha létezik (#2114).

        A KERESÉST a `movie.mxf.projekt_utvonal` végzi (#3191 óta megvan,
        a `collage_save._collage_project_path` párja); itt csak az
        URL-alakot bontjuk vissza, mert a QML `file://`-ként adja tovább a
        néző útvonalát — enélkül a gomb SOSEM jelenne meg."""
        nyers = str(video_path or "")
        if not nyers:
            return None
        if nyers.startswith("file://"):
            nyers = QUrl(nyers).toLocalFile()
        return projekt_utvonal(nyers)

    @Slot(str, result=bool)
    def hasMovieProject(self, video_path: str) -> bool:  # noqa: N802
        """Van-e a filmnek `.mxf` párja — vagyis szerkeszthető-e (#2114).

        A `hasCollageProject` ikerpárja: nem a létrehozás emléke kapcsolja
        be a gombot, hanem a fájl mellett álló projektfájl."""
        return CreateMixin._film_projekt_utja(video_path) is not None

    @Slot(str, result="QVariantMap")
    def movieProject(self, video_path: str):  # noqa: N802
        """A film projektje a felületnek: forrásképek + diaidő (#2114).

        Üres szótár, ha nincs (vagy nem olvasható) projektfájl — a visszaút
        nem boríthatja a felületet.

        ⛔ A **felbontás nincs benne**: a `_film_projekt` a `curresolution`
        mezőt nem tölti ki (a jelentése a mi modellünkben nincs mérve),
        ezért az újranyitás a felbontás alapértelmezését hozza. Ezt a hívó
        felület mondja ki a felhasználónak — találgatott érték nem megy a
        projektbe."""
        ut = CreateMixin._film_projekt_utja(video_path)
        if ut is None:
            return {}
        try:
            projekt = read_mxf(ut)
        except (OSError, ValueError, ElementTree.ParseError) as hiba:
            logger.warning("a film projektfájlja nem olvasható: %s", hiba)
            return {}
        return {
            "sources": [
                atmenet.forras.filename
                for atmenet in projekt.atmenetek
                if atmenet.forras.filename
            ],
            "seconds": float(projekt.defaulttrans.advanceinterval),
            "burstmodethresh": int(projekt.burstmodethresh),
        }

    @Slot(list, str, int, float)
    @Slot(list, str, int, float, int)
    @Slot(list, str, int, float, int, str, float, str, int)
    @Slot(list, str, int, float, int, str, float, str, int, list)
    @Slot(list, str, int, float, int, str, float, str, int, list, dict)
    def exportMovie(
        self,
        rows,
        target_url: str,
        height: int,
        seconds_per_photo: float,
        width: int = 0,
        transition_type: str = "dissolve",
        overlap_seconds: float = 0.5,
        audio_url: str = "",
        audio_option: int = 0,
        text_slides: list | None = None,
        movie_options: dict | None = None,
    ) -> None:
        """Diavetítés-videó a kijelölt képekből (MP4).

        `height` a videó magassága, `width` a szélessége. #1977: a
        szélesség KÜLÖN paraméter, mert az eredeti hét mérete közül öt
        4:3-as. `width=0` ⇒ 16:9-ből (a régi hívási alak).

        ⚠️ **A kimenet MP4 (`mp4v`), az eredeti `.wmv`-jével szemben** — és
        ez SZÁNDÉKOS, nem elmaradás. A `.wmv` írásához Windows-specifikus
        kodek kellene; az OpenCV `mp4v`-je minden platformon megy, külön
        telepítés nélkül (`movie/slideshow.py:27-28`). Egy későbbi kör ne
        „javítsa vissza": a konténer eltérése a hordozhatóság ára.
        """
        # #1539: a bekötés a GUI-szálon, a háttérszál indítása ELŐTT
        self._ensure_output_resync_wired()
        # A filmprojektum saját kliptálcát ad át `file:` URL-ekkel; ne
        # olvassuk újra helyette a főablak kijelölését vagy képtálcáját.
        # A régi, sorindexeket váró hívási alak változatlan marad.
        if rows and isinstance(rows[0], str):
            sources = tuple(
                Path(to_local_path(str(row))) for row in rows if str(row)
            )
        else:
            sources = self._sources_for(rows)
        sources = sources[:_MAX_ITEMS]
        target = to_local_path(target_url)
        if not sources:
            self.movieFailed.emit(self.tr("No pictures are selected."))
            return
        if not target:
            # #1977: cél nélkül NEM hibázunk — az eredeti sem kér célfájlt.
            # A mappát a program adja (`Picasa`/honosított Filmek), a nevet
            # a forrásmappa címéből képezzük, ütközésnél sorszámozva. Ha a
            # mappa nem hozható létre, a rendszer Videók mappája a tartalék
            # (`0x00620af9`–`0x00620b1d`), és ez SEM hibaüzenet.
            try:
                target = str(self._alapertelmezett_film_cel(sources))
            except OSError as hiba:
                # A részletet NAPLÓZZUK, nem a felhasználónak mondjuk: az
                # `OSError` szövege fejlesztői (errno, útvonal), és a
                # honosítása is külön csapda volna (%1-helyettesítő).
                logger.warning("a film mappája nem hozható létre: %s", hiba)
                self.movieFailed.emit(
                    self.tr("The movie folder could not be created.")
                )
                return
        try:
            audio_path = Path(to_local_path(audio_url)) if audio_url else None
            settings = self._film_beallitas(
                width,
                height,
                seconds_per_photo,
                overlap_seconds,
                transition_type,
                audio_path,
                audio_option,
                text_slides,
                movie_options,
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
            # #3191: a PROJEKTFÁJL a kimenet mellé. A kollázs ugyanezt
            # teszi a `.cxf`-fel: enélkül a kirenderelt film mellől
            # hiányzik a szerkeszthető állapot, és a szerkesztőben nem
            # jelenhet meg a „Mozgófilm szerkesztése" gomb (#2114).
            # Sosem dob: a projektfájl kudarca nem boríthatja a KÉSZ
            # videót (ugyanaz az elv, mint az ini-érintésnél, #643).
            try:
                write_mxf(
                    Path(report.target).with_suffix(".mxf"),
                    self._film_projekt(report.used, settings),
                )
            except OSError as hiba:  # pragma: no cover - írásvédett cél
                logger.warning("a film projektfájlja nem írható: %s", hiba)
            # #1539: az `.mp4` INDEXELT médiatípus (scanner/filetypes.py),
            # tehát a rácsra való — ugyanaz a helyzet, mint a kollázsnál.
            self.noteOutputWritten(str(report.target))
            self.movieFinished.emit(
                str(report.target),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-movie")
