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

from PySide6.QtCore import Property, Signal, Slot

from .folder_photo_sort_controller import FolderPhotoSortMixin

# A QSettings-kulcs — a `view/` névtér a többi nézet-beállításé is
# (folderSort, thumbCaption, showHidden).
DARK_THEME_KEY = "view/darkTheme"
UI_TRANSITIONS_KEY = "view/uiTransitions"
SHOW_TOOLTIPS_KEY = "view/showTooltips"
SINGLE_CLICK_EXIT_KEY = "view/singleClickExit"

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

    #1436: a mappán belüli képsorrend szelete (`FolderPhotoSortMixin`) is
    innen kapcsolódik az `AppController`-hez — mindkettő `view/` névtérbeli,
    perzisztens nézet-beállítás, és az `AppController` bázislistája a forró
    `controller.py`-ban él (a `CollageMixin` ugyanígy hozza a szeleteit).
    """

    darkThemeChanged = Signal()
    uiTransitionsEnabledChanged = Signal()
    showTooltipsEnabledChanged = Signal()
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
        self._single_click_exit_enabled = coerce_ui_preference_flag(
            settings.value(SINGLE_CLICK_EXIT_KEY, False), default=False
        )
        self._init_folder_photo_sort()  # #1436

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
