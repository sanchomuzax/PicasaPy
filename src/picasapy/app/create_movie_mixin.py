"""A Létrehozás filmhez tartozó QML-felülete (#6252)."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot
from picasapy.app.movie_preview import MovieTransitionPreviewProvider
from picasapy.movie import MovieSettings
from picasapy.movie.mxf import MxfProjekt

class _LegacyMovieCall:
    """A régi modul patchpontjának futásidejű továbbítása."""

    def __call__(self, *args, **kwargs):
        legacy = import_module("picasapy.app.create_controller")
        return legacy._movie_call(*args, **kwargs)


_movie_call = _LegacyMovieCall()


class _CreateMovieMixin:
    """A CreateMixin filmbeállításai, előnézetei és műveletei."""

    movieProgress = Signal(int, int)

    movieFinished = Signal(str, int, int, int)

    movieFailed = Signal(str)

    movieTransitionPreviewReady = Signal(str, int)

    moviePreferencesChanged = Signal()

    @Property(int, notify=moviePreferencesChanged)
    def movieResolutionIndex(self) -> int:  # noqa: N802
        """A normál film méretindexe (`Preferences\\makemovieres`)."""
        return _movie_call("movieResolutionIndex", self)

    @Property(int, notify=moviePreferencesChanged)
    def faceMovieResolutionIndex(self) -> int:  # noqa: N802
        """Az arc-film méretindexe (`facemakemovieres`), alapból 3 (#4391).

        A Picasa ezt a kulcsot olvassa, de a beállított új értéket nem írja
        vissza; a QML-ben is megmarad ez a nem mentő viselkedés.
        """
        return _movie_call("faceMovieResolutionIndex", self)

    @Slot(int)
    def setMovieResolutionIndex(self, index: int) -> None:  # noqa: N802
        """A hét eredeti méret közül a választott index megőrzése."""
        return _movie_call("setMovieResolutionIndex", self, index)

    @Property(float, notify=moviePreferencesChanged)
    def movieSlideDuration(self) -> float:  # noqa: N802
        """A filmkészítő diaideje másodpercben (`Preferences\\slideduration`)."""
        return _movie_call("movieSlideDuration", self)

    @Slot(float)
    def setMovieSlideDuration(self, seconds: float) -> None:  # noqa: N802
        """A diaidő mentése az eredeti 1–300 másodperces tartományban."""
        return _movie_call("setMovieSlideDuration", self, seconds)

    @Property(str, notify=moviePreferencesChanged)
    def movieTransition(self) -> str:  # noqa: N802
        """A filmkészítő átmenetkulcsa, alapból a jelenlegi `dissolve`."""
        return _movie_call("movieTransition", self)

    @Slot(str)
    def setMovieTransition(self, transition: str) -> None:  # noqa: N802
        """Az ismert átmenetkulcs mentése a `Preferences` tárba."""
        return _movie_call("setMovieTransition", self, transition)

    @Property(int, notify=moviePreferencesChanged)
    def movieVolume(self) -> int:  # noqa: N802
        """A videó hangerőcsúszkájának Preferences/movievolume értéke."""
        return _movie_call("movieVolume", self)

    @Slot(int)
    def setMovieVolume(self, volume: int) -> None:  # noqa: N802
        """A hangerő elmentése az eredeti 0..1000-es tartományban."""
        return _movie_call("setMovieVolume", self, volume)

    @Slot(str, result=bool)
    def moviePreference(self, name: str) -> bool:  # noqa: N802
        """A filmkészítő hivatalos Preferences-kulcsának beolvasása."""
        return _movie_call("moviePreference", self, name)

    @Slot(str, bool)
    def setMoviePreference(self, name: str, value: bool) -> None:  # noqa: N802
        """Csak a specifikációban szereplő filmkészítő-kulcsokat írja."""
        return _movie_call("setMoviePreference", self, name, value)

    @Slot(list, result=list)
    def movieSourceUrls(self, rows) -> list[str]:  # noqa: N802
        """A film forrásképeinek `file:` URL-je, a dia-előnézethez."""
        return _movie_call("movieSourceUrls", self, rows)

    @Slot(list, result=list)
    def movieClipNames(self, rows) -> list[str]:  # noqa: N802
        """A film kliptálcáján megjelenő képfájlnevek."""
        return _movie_call("movieClipNames", self, rows)

    @Slot(list, result=list)
    def selectedMovieSourceUrls(self, rows) -> list[str]:  # noqa: N802
        """Új klipek a könyvtár aktuális kijelöléséből, a tálcától függetlenül."""
        return _movie_call("selectedMovieSourceUrls", self, rows)

    @property
    def movie_transition_preview_provider(self) -> MovieTransitionPreviewProvider:
        """A slideshow azonos átmenetfüggvényét használó QML-képszolgáltató."""
        return _movie_call("movie_transition_preview_provider", self)

    @Slot(
        str,
        str,
        str,
        float,
        int,
        int,
        bool,
        bool,
        bool,
        str,
        str,
        bool,
        int,
        int,
        float,
        result=int,
    )
    def requestMovieTransitionPreview(  # noqa: N802
        self,
        outgoing_source: str,
        incoming_source: str,
        transition: str,
        progress: float,
        width: int,
        height: int,
        cropfit: bool,
        show_captions: bool,
        show_dates: bool,
        outgoing_slide_json: str,
        incoming_slide_json: str,
        actual_size: bool,
        viewport_width: int,
        viewport_height: int,
        device_pixel_ratio: float,
    ) -> int:
        """Elindítja a nézőképkocka háttérbeli renderelését."""
        return _movie_call(
            "requestMovieTransitionPreview",
            self,
            outgoing_source,
            incoming_source,
            transition,
            progress,
            width,
            height,
            cropfit,
            show_captions,
            show_dates,
            outgoing_slide_json,
            incoming_slide_json,
            actual_size,
            viewport_width,
            viewport_height,
            device_pixel_ratio,
        )

    @Slot(str, str, int, int, bool, bool, bool, bool, int, int, float)
    def prefetchMovieTransitionPreview(  # noqa: N802
        self,
        source: str,
        slide_json: str,
        width: int,
        height: int,
        cropfit: bool,
        show_captions: bool,
        show_dates: bool,
        actual_size: bool,
        viewport_width: int,
        viewport_height: int,
        device_pixel_ratio: float,
    ) -> None:
        """Kéri a film-előnézet következő dia-alapkockájának előtöltését."""
        return _movie_call(
            "prefetchMovieTransitionPreview",
            self,
            source,
            slide_json,
            width,
            height,
            cropfit,
            show_captions,
            show_dates,
            actual_size,
            viewport_width,
            viewport_height,
            device_pixel_ratio,
        )

    @Slot(str, result=list)
    def moviePreviewImageSize(self, source: str) -> list[int]:  # noqa: N802
        """A forrásméretet fejlécekből olvassa, képtartalom-dekódolás nélkül."""
        return _movie_call("moviePreviewImageSize", self, source)

    def _alapertelmezett_film_cel(self) -> Path:
        """A film célfájlja, ha a felhasználó nem adott meg egyet (#1977).

        A mappa a `Picasa` alatti (meglévő vagy honosított) Filmek-mappa,
        és **projekt-mappaként be is jelöljük** — enélkül a bal hasáb
        Projektek gyűjteménye nem tudja hova sorolni (ugyanaz a hiba,
        amit a kollázsnál a `write_album_ini` javított).

        A név (#5676): ha a munkamenetben már készült kimenet, annak a neve
        ÉS mappája (`0x00620998`); különben a felület nyelvének honosított
        alapneve (`CMakeMoviePanel::deffilename`). A forrásmappa neve nem
        számít, az eredeti sem abból nevez el.
        """
        return _movie_call("_alapertelmezett_film_cel", self)

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
        return _movie_call(
            "_film_beallitas",
            width,
            height,
            seconds_per_photo,
            transition_seconds,
            transition_type,
            audio_path,
            audio_option,
            text_slides,
            options,
        )

    @staticmethod
    def _film_projekt(
        sources,
        settings,
        used_face_rects=(),
    ) -> MxfProjekt:
        """A film állapota `.mxf`-projektként (#3191).

        A felület által állítható méret, hangsáv, opciók, rendezés,
        szöveges diák és áttűnés kerül a projektbe. A formátum megengedi,
        hogy a diánkénti `trans` felülírja az album-szintű `defaulttrans`-ot.
        """
        return _movie_call("_film_projekt", sources, settings, used_face_rects)

    @staticmethod
    def _film_projekt_utja(video_path: str) -> Path | None:
        """A kimenet melletti `.mxf`, ha létezik (#2114).

        A KERESÉST a `movie.mxf.projekt_utvonal` végzi (#3191 óta megvan,
        a `collage_save_open._collage_project_path` párja); itt csak az
        URL-alakot bontjuk vissza, mert a QML `file://`-ként adja tovább a
        néző útvonalát — enélkül a gomb SOSEM jelenne meg."""
        return _movie_call("_film_projekt_utja", video_path)

    @Slot(str, result=bool)
    def hasMovieProject(self, video_path: str) -> bool:  # noqa: N802
        """Van-e a filmnek `.mxf` párja — vagyis szerkeszthető-e (#2114).

        A `hasCollageProject` ikerpárja: nem a létrehozás emléke kapcsolja
        be a gombot, hanem a fájl mellett álló projektfájl."""
        return _movie_call("hasMovieProject", self, video_path)

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
        return _movie_call("movieProject", self, video_path)

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
        return _movie_call(
            "exportMovie",
            self,
            rows,
            target_url,
            height,
            seconds_per_photo,
            width,
            transition_type,
            overlap_seconds,
            audio_url,
            audio_option,
            text_slides,
            movie_options,
        )
