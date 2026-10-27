"""A diavetítés QML-beállításai és segédei."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Property, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from . import formatting
from .controller_signals import AppControllerSignalsMixin as _Signals
from .slideshow_pan_zoom import qml_pan_zoom_rectangles

# #4856: az eredeti diavetítés hét átmenete; a filmkészítő listája külön él.
_SLIDESHOW_TRANSITIONS = (
    "cut", "kenburns", "dissolve", "wiperight",
    "circleout", "pushright", "rect",
)

class SlideshowSettingsMixin:
    """A diavetítés QML-beállításai és segédei."""

    @Property(bool, notify=_Signals.statusChanged)
    def bigSlideshow2(self):  # noqa: N802 - QML-property-konvenció
        value = self._get_settings().value("Preferences/BigSlideshow2", 1)
        if value in (False, "false", "False", "0", 0):
            return False
        return True

    #: #5653: a `GetDeviceCaps(BITSPIXEL)` Qt-megfelelője; a vetítő QML-je
    #: ezt a megnevezett értéket ellenőrzi (16 vagy 32 bit).
    @Property(int, notify=_Signals.statusChanged)
    def slideshowScreenDepth(self):  # noqa: N802 - QML-property-konvenció
        screen = QGuiApplication.primaryScreen()
        return screen.depth() if screen is not None else 0

    #: #433: a diavetítés MEGŐRZÖTT beállításai. Az eredeti a `Preferences`
    #: alá teszi őket (`SlideshowEffectTime`, `captionmode`); nálunk a saját
    #: beállítás-tárolóba mennek, a `view/…` kulcsok mintájára — a
    #: registry-kulcsok egy-az-egyben átvétele nem cél (más a platform).
    @Property(str, notify=_Signals.statusChanged)
    def slideshowTransition(self):  # noqa: N802 - QML-property-konvenció
        """A mentett átmenet. A hét elemen kívüli (régebbi) mentett értéket
        betöltéskor Dissolve-ra cseréli (#4856)."""
        mentett = self._get_settings().value("view/slideshowTransition", "dissolve")
        return mentett if mentett in _SLIDESHOW_TRANSITIONS else "dissolve"

    @Slot(str)
    def setSlideshowTransition(self, value: str) -> None:  # noqa: N802
        """A vetítés-átmenet megőrzése (#433).

        Ismeretlen kulcsot NEM tárolunk; a készlet az eredeti diavetítés hét
        átmenete (`picasa-create-features.md` 4.3, #4856)."""
        if value not in _SLIDESHOW_TRANSITIONS:
            return
        self._get_settings().setValue("view/slideshowTransition", value)
        self.statusChanged.emit()

    @Slot(int, int, int, int, result="QVariantList")
    def slideshowPanZoomRectangles(  # noqa: N802 - QML metódusnév
        self,
        forras_szelesseg: int,
        forras_magassag: int,
        nezet_szelesseg: int,
        nezet_magassag: int,
    ) -> list[dict[str, float]]:
        """A vetítő Pan and Zoom kivágásai, a QML-nek átadható alakban."""
        if min(
            forras_szelesseg,
            forras_magassag,
            nezet_szelesseg,
            nezet_magassag,
        ) <= 0:
            return []
        return qml_pan_zoom_rectangles(
            forras_szelesseg,
            forras_magassag,
            nezet_szelesseg,
            nezet_magassag,
        )

    @Property(int, notify=_Signals.statusChanged)
    def slideshowTransitionMs(self):  # noqa: N802
        """Az átmenet hossza milliszekundumban (`SlideshowEffectTime`)."""
        try:
            value = int(self._get_settings().value("view/slideshowTransitionMs", 700))
        except (TypeError, ValueError):
            return 700
        #: a dia-idő alatt kell maradnia, különben az átmenet sosem fejeződik
        #: be; a felső korlát a legrövidebb dia-idő (1 s) fele
        return max(0, min(value, 500))

    #: #2992, #5544: a diaidő alsó/felső korlátja, mérve. Az eredeti `+`/`-`
    #: gombjai után az érték 1 és 20 közé szorul: az alsó határ
    #: `0x00802b6d` (`fld1`), a felső `0x00802b7e` (a `0x00cf4974` konstans,
    #: f32 = 20,0).
    SLIDESHOW_SECONDS_MIN = 1
    SLIDESHOW_SECONDS_MAX = 20

    @Property(int, notify=_Signals.statusChanged)
    def slideshowSeconds(self):  # noqa: N802 — QML-property-konvenció
        """Egy dia ideje másodpercben (`SlideshowEffectTime`, alapérték 3).

        Mérve: `0x007facd3` (`mov dword ptr [esp+0x3c], 3`). A sérült vagy
        tartományon kívüli tárolt érték az alapértékre esik vissza — egy
        elgépelt beállítás ne fagyassza meg a vetítést egy képen."""
        try:
            ertek = int(self._get_settings().value("view/slideshowSeconds", 3))
        except (TypeError, ValueError):
            return 3
        if not (self.SLIDESHOW_SECONDS_MIN <= ertek <= self.SLIDESHOW_SECONDS_MAX):
            return 3
        return ertek

    @Slot(int)
    def setSlideshowSeconds(self, value: int) -> None:  # noqa: N802
        """A diaidő megőrzése; a tartományon kívüli érték NEM megy be."""
        try:
            ertek = int(value)
        except (TypeError, ValueError):
            return
        if not (self.SLIDESHOW_SECONDS_MIN <= ertek <= self.SLIDESHOW_SECONDS_MAX):
            return
        self._get_settings().setValue("view/slideshowSeconds", ertek)
        self.statusChanged.emit()

    @Property(bool, notify=_Signals.statusChanged)
    def slideshowLoop(self):  # noqa: N802
        """A diavetítés ismétlése; az eredeti alapértéke ki."""
        value = self._get_settings().value("view/slideshowLoop", False)
        if value in (True, "true", "1"):
            return True
        if value in (False, "false", "0"):
            return False
        return False

    @Slot(bool)
    def setSlideshowLoop(self, value: bool) -> None:  # noqa: N802
        self._get_settings().setValue("view/slideshowLoop", bool(value))
        self.statusChanged.emit()

    @Property(bool, notify=_Signals.statusChanged)
    def slideshowMusicEnabled(self):  # noqa: N802
        value = self._get_settings().value("view/slideshowMusicEnabled", True)
        return value in (True, "true", "1")

    @Slot(bool)
    def setSlideshowMusicEnabled(self, value: bool) -> None:  # noqa: N802
        self._get_settings().setValue("view/slideshowMusicEnabled", bool(value))
        self.statusChanged.emit()

    @Property(str, notify=_Signals.statusChanged)
    def slideshowMusicFolder(self):  # noqa: N802
        return str(self._get_settings().value("view/slideshowMusicFolder", "") or "")

    @Property(QUrl, notify=_Signals.statusChanged)
    def slideshowMusicFolderUrl(self):  # noqa: N802
        """A mappaválasztó URL-je a közös útvonal-konverteren keresztül."""
        return formatting.to_file_url(self.slideshowMusicFolder)

    @Slot(str)
    def setSlideshowMusicFolder(self, value: str) -> None:  # noqa: N802
        """Megőrzi a kiválasztott, létező mappát; az üres érték törli."""
        local_path = formatting.to_local_path(value)
        if not local_path:
            self._get_settings().setValue("view/slideshowMusicFolder", "")
            self.statusChanged.emit()
            return
        folder = Path(local_path).expanduser()
        try:
            if not folder.is_dir():
                return
            local_path = str(folder.resolve())
        except OSError:
            return
        self._get_settings().setValue("view/slideshowMusicFolder", local_path)
        self.statusChanged.emit()

    @Property(list, notify=_Signals.statusChanged)
    def slideshowMusicTrackUrls(self):  # noqa: N802
        """Az album-, mappa- vagy közös diavetítési zeneforrás."""
        mode, token = self._view_mode
        if mode == "album":
            tracks = self.albumMusicTrackUrls(token)
            if tracks:
                return tracks
        if self._current_folder and self.folderMusicEnabled(self._current_folder):
            return self.folderMusicTrackUrls(self._current_folder)
        folder = Path(self.slideshowMusicFolder).expanduser()
        try:
            if not folder.is_dir():
                return []
            tracks = sorted(
                (
                    path for path in folder.iterdir()
                    if path.is_file() and path.suffix.casefold() == ".mp3"
                ),
                key=lambda path: path.name.casefold(),
            )
        except OSError:
            return []
        return [formatting.to_file_url(str(path)) for path in tracks]

    @Property(str, notify=_Signals.statusChanged)
    def slideshowCaptionMode(self):  # noqa: N802
        return self._get_settings().value("view/slideshowCaptionMode", "caption")

    @Slot(str)
    def setSlideshowCaptionMode(self, value: str) -> None:  # noqa: N802
        """A vetítés feliratmódja (#433): felirat / fájlnév / semmi."""
        if value not in ("caption", "filename", "none"):
            return
        self._get_settings().setValue("view/slideshowCaptionMode", value)
        self.statusChanged.emit()
