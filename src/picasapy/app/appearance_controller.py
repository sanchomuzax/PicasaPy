"""Megjelenés-kapcsoló: sötét téma (#28) — az AppController vezérlő-szelete.

A felhasználó döntése szerint az app **alapból világos** (a dizájn-igazság-
forrás a `docs/specs/design-guide.md`), a sötét mód opcionális, V3-as extra.
A kapcsoló QSettings-be íródik, így a következő induláskor visszaáll; a
Theme.qml `dark` tokenje ehhez a property-hez van kötve (Main.qml), és
minden szín-token kötése automatikusan követi.

Hibás vagy kézzel átírt beállításból SOSEM lesz sötét téma: az ismeretlen
érték világosra esik vissza (a window_geometry.py „értelmetlen mentés =
alapértelmezés" elvének mintájára).
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Property, Qt, Signal, Slot

from .folder_photo_sort_controller import FolderPhotoSortMixin

# A QSettings-kulcs — a `view/` névtér a többi nézet-beállításé is
# (folderSort, thumbCaption, showHidden).
DARK_THEME_KEY = "view/darkTheme"
UI_TRANSITIONS_KEY = "view/uiTransitions"
SHOW_TOOLTIPS_KEY = "view/showTooltips"
SINGLE_CLICK_EXIT_KEY = "view/singleClickExit"
# #4570: az eredeti `Preferences/AutoPlayMovies` kapcsolója — megnyitáskor
# magától lejátssza-e a videót. Alapállapot: igen (a Picasa így működött).
AUTO_PLAY_MOVIES_KEY = "view/autoPlayMovies"
# #4949: a Ctrl+Alt felugró előnézet saját kapcsolója (az eredeti
# `Preferences\EnableHover`). Független a buboréksúgótól. Alapállapot: igen,
# mert a mai viselkedés is alapból mutatja az előnézetet.
ENABLE_HOVER_KEY = "view/enableHover"

# Igaznak számító mentett értékek (a QSettings platformonként bool-t vagy
# szöveget ad vissza ugyanarra az írásra).
_TRUE_VALUES = ("true", "1")
_FALSE_VALUES = ("false", "0")


def coerce_dark_flag(value) -> bool:
    """A mentett beállítás bool-lá alakítása; minden ismeretlen érték = világos."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return False


def coerce_ui_preference_flag(value, default: bool) -> bool:
    """A felületi kapcsolók bool/string értékét értelmezi; hibás érték = alap."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
    return default


class AppearanceMixin(FolderPhotoSortMixin):
    """`darkTheme` kapcsoló — perzisztens, jelzéssel a QML-kötéseknek.

    #1436/#4890: a mappánkénti kézi sorrend szelete
    (`FolderPhotoSortMixin`) is innen kapcsolódik az `AppController`-hez;
    a sorrend a mappa `.picasa.ini`-jében él, nem a `view/` beállításban.
    """

    darkThemeChanged = Signal()
    uiTransitionsEnabledChanged = Signal()
    showTooltipsEnabledChanged = Signal()
    ctrlAltHeldChanged = Signal()
    autoPlayMoviesChanged = Signal()
    enableHoverChanged = Signal()
    singleClickExitEnabledChanged = Signal()

    def _init_appearance(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        __init__-et — ez a repó konvenciója, ld. PerfMonitorMixin)."""
        self._dark_theme = coerce_dark_flag(self._get_settings().value(DARK_THEME_KEY))
        settings = self._get_settings()
        self._ui_transitions_enabled = coerce_ui_preference_flag(
            settings.value(UI_TRANSITIONS_KEY, True), default=True
        )
        self._show_tooltips_enabled = coerce_ui_preference_flag(
            settings.value(SHOW_TOOLTIPS_KEY, True), default=True
        )
        self._enable_hover = coerce_ui_preference_flag(
            settings.value(ENABLE_HOVER_KEY, True), default=True
        )
        self._single_click_exit_enabled = coerce_ui_preference_flag(
            settings.value(SINGLE_CLICK_EXIT_KEY, False), default=False
        )
        self._auto_play_movies = coerce_ui_preference_flag(
            settings.value(AUTO_PLAY_MOVIES_KEY, True), default=True
        )
        self._hover_preview_pressed: set[int] = set()
        self._ctrl_alt_held = False
        self._init_folder_photo_sort()  # #1436

    @Property(bool, notify=ctrlAltHeldChanged)
    def ctrlAltHeld(self) -> bool:  # noqa: N802 — QML-property
        return self._ctrl_alt_held

    @Slot(QObject)
    def attachHoverPreviewKeyState(self, target: QObject) -> None:  # noqa: N802
        """A főablak valódi Ctrl/Alt eseményeit figyelje, de ne nyelje el."""
        target.installEventFilter(self)

    def eventFilter(self, watched: QObject, event) -> bool:  # noqa: N802
        event_type = event.type()
        if event_type in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            key = event.key()
            if (
                key in (Qt.Key.Key_Control, Qt.Key.Key_Alt)
                and not event.isAutoRepeat()
            ):
                if event_type == QEvent.Type.KeyPress:
                    self._hover_preview_pressed.add(key)
                else:
                    self._hover_preview_pressed.discard(key)
                self._set_ctrl_alt_held(
                    Qt.Key.Key_Control in self._hover_preview_pressed
                    and Qt.Key.Key_Alt in self._hover_preview_pressed
                )
        elif event_type == QEvent.Type.WindowDeactivate:
            self._hover_preview_pressed.clear()
            self._set_ctrl_alt_held(False)
        return False

    def _set_ctrl_alt_held(self, held: bool) -> None:
        if held == self._ctrl_alt_held:
            return
        self._ctrl_alt_held = held
        self.ctrlAltHeldChanged.emit()

    @Property(bool, notify=darkThemeChanged)
    def darkTheme(self) -> bool:
        """Nézet → Sötét téma: sötét tokenkészletet használ-e a felület."""
        return self._dark_theme

    @Slot(bool)
    def setDarkTheme(self, dark: bool) -> None:
        """Téma beállítása; azonos értéknél nincs írás és nincs jelzés sem
        (a felesleges jelzés az egész felület kötéseit újraszámoltatná)."""
        dark = bool(dark)
        if dark == self._dark_theme:
            return
        self._dark_theme = dark
        self._get_settings().setValue(DARK_THEME_KEY, "true" if dark else "false")
        self.darkThemeChanged.emit()

    @Slot()
    def toggleDarkTheme(self) -> None:
        self.setDarkTheme(not self._dark_theme)

    @Property(bool, notify=uiTransitionsEnabledChanged)
    def uiTransitionsEnabled(self) -> bool:
        """Az Általános fül felületi átmenetei aktívak-e (#4449)."""
        return self._ui_transitions_enabled

    @Slot(bool)
    def setUITransitionsEnabled(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if enabled == self._ui_transitions_enabled:
            return
        self._ui_transitions_enabled = enabled
        self._get_settings().setValue(
            UI_TRANSITIONS_KEY, "true" if enabled else "false"
        )
        self.uiTransitionsEnabledChanged.emit()

    @Property(bool, notify=autoPlayMoviesChanged)
    def autoPlayMovies(self) -> bool:
        """Megnyitáskor magától induljon-e a videó (#4570, `AutoPlayMovies`)."""
        return self._auto_play_movies

    # Nem `@Slot`: az eredetiben rejtett kulcs, a felületről nem állítható (#4570)
    def setAutoPlayMovies(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if enabled == self._auto_play_movies:
            return
        self._auto_play_movies = enabled
        self._get_settings().setValue(
            AUTO_PLAY_MOVIES_KEY, "true" if enabled else "false"
        )
        self.autoPlayMoviesChanged.emit()

    @Property(bool, notify=enableHoverChanged)
    def enableHover(self) -> bool:
        """A Ctrl+Alt felugró előnézet kapcsolója (#4949, `EnableHover`)."""
        return self._enable_hover

    # Nem `@Slot`: az eredetiben rejtett kulcs, a felületről nem állítható (#4949)
    def setEnableHover(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if enabled == self._enable_hover:
            return
        self._enable_hover = enabled
        self._get_settings().setValue(
            ENABLE_HOVER_KEY, "true" if enabled else "false"
        )
        self.enableHoverChanged.emit()

    @Property(bool, notify=showTooltipsEnabledChanged)
    def showTooltipsEnabled(self) -> bool:
        """Az Általános fül buboréksúgó-kapcsolója (#4449)."""
        return self._show_tooltips_enabled

    @Slot(bool)
    def setShowTooltipsEnabled(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if enabled == self._show_tooltips_enabled:
            return
        self._show_tooltips_enabled = enabled
        self._get_settings().setValue(
            SHOW_TOOLTIPS_KEY, "true" if enabled else "false"
        )
        self.showTooltipsEnabledChanged.emit()

    @Property(bool, notify=singleClickExitEnabledChanged)
    def singleClickExitEnabled(self) -> bool:
        """A videó-előnézet egykattintásos visszalépési módja (#4449)."""
        return self._single_click_exit_enabled

    @Slot(bool)
    def setSingleClickExitEnabled(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if enabled == self._single_click_exit_enabled:
            return
        self._single_click_exit_enabled = enabled
        self._get_settings().setValue(
            SINGLE_CLICK_EXIT_KEY, "true" if enabled else "false"
        )
        self.singleClickExitEnabledChanged.emit()
