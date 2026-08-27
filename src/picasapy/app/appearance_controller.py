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
from .text_input_controller import TextInputMixin

# A QSettings-kulcs — a `view/` névtér a többi nézet-beállításé is
# (folderSort, thumbCaption, showHidden).
DARK_THEME_KEY = "view/darkTheme"

# Igaznak számító mentett értékek (a QSettings platformonként bool-t vagy
# szöveget ad vissza ugyanarra az írásra).
_TRUE_VALUES = ("true", "1")


def coerce_dark_flag(value) -> bool:
    """A mentett beállítás bool-lá alakítása; minden ismeretlen érték = világos."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return False


class AppearanceMixin(FolderPhotoSortMixin, TextInputMixin):
    """`darkTheme` kapcsoló — perzisztens, jelzéssel a QML-kötéseknek.

    #1436: a mappán belüli képsorrend szelete (`FolderPhotoSortMixin`) is
    innen kapcsolódik az `AppController`-hez — mindkettő `view/` névtérbeli,
    perzisztens nézet-beállítás, és az `AppController` bázislistája a forró
    `controller.py`-ban él (a `CollageMixin` ugyanígy hozza a szeleteit).

    #1526: ugyanezen az úton jön az „Automatikus kitöltés" kapcsoló
    (`TextInputMixin`) — szintén `view/` névtérbeli, perzisztens beállítás.
    """

    darkThemeChanged = Signal()

    def _init_appearance(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        __init__-et — ez a repó konvenciója, ld. PerfMonitorMixin)."""
        self._dark_theme = coerce_dark_flag(self._get_settings().value(DARK_THEME_KEY))
        self._init_folder_photo_sort()  # #1436
        self._init_text_input()  # #1526

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
