"""Szövegbeviteli beállítás: **automatikus kitöltés** ki/be (#1526).

## Honnan tudjuk, hogy ez létezik

A Picasa szövegmező-helyimenüje (`Address` menüosztály, `0x007331e0`) hét
tételes, és a hetedik az **`ID_AUTOCOMPLETE`** — „&Automatikus kitöltés".
Vagyis a mezők kiegészítése a felhasználó által **kikapcsolható**, méghozzá
onnan, ahol a zavarja: a mező helyi menüjéből.

## Mit kapcsol nálunk

Két ÉLŐ javaslat-felület van a felületen, és a kapcsoló mindkettőre hat:

* a **keresőmező** javaslat-buborékja (`SearchSuggestions`, #7),
* az **arcnév-mező** ismert-név listája (`FacesOverlay`, #147).

Ez tehát nem jelölőnégyzet-a-semmibe: kikapcsolva egyik legördülő sem jelenik
meg. Ha később új kiegészítő mező születik, azt is ehhez a tulajdonsághoz kell
kötni.

## Alapból BE

Az eredetiben a kiegészítés működik, és a menütétel a kikapcsolására való —
tehát a hiányzó vagy értelmezhetetlen beállítás **bekapcsolt** állapotot
jelent (az `appearance_controller.coerce_dark_flag` ellentéte, ahol az
alapértelmezés a „nem").
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

#: QSettings-kulcs — a `view/` névtér a többi nézet-beállításé is.
AUTO_COMPLETE_KEY = "view/autoComplete"

_FALSE_VALUES = ("false", "0")


def coerce_auto_complete_flag(value) -> bool:
    """A mentett beállítás bool-lá alakítása; **ismeretlen érték = BE**.

    Kézzel átírt vagy hiányzó beállításból soha nem lesz néma kikapcsolás: a
    felhasználó azt látná, hogy a javaslatok minden ok nélkül eltűntek.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in _FALSE_VALUES
    return value is None or bool(value)


class TextInputMixin:
    """`autoComplete` kapcsoló — perzisztens, jelzéssel a QML-kötéseknek."""

    autoCompleteChanged = Signal()

    def _init_text_input(self) -> None:
        """Az `AppearanceMixin._init_appearance` hívja (a mixinek nem
        definiálnak saját `__init__`-et — a repó konvenciója)."""
        self._auto_complete = coerce_auto_complete_flag(
            self._get_settings().value(AUTO_COMPLETE_KEY)
        )

    @Property(bool, notify=autoCompleteChanged)
    def autoComplete(self) -> bool:
        """Megjelenjenek-e a beírás közbeni javaslat-listák."""
        return self._auto_complete

    @Slot(bool)
    def setAutoComplete(self, enabled: bool) -> None:
        """A szövegmező helyi menüjének „Automatikus kitöltés" tétele."""
        enabled = bool(enabled)
        if enabled == self._auto_complete:
            return
        self._auto_complete = enabled
        self._get_settings().setValue(AUTO_COMPLETE_KEY, enabled)
        self.autoCompleteChanged.emit()


__all__ = ["AUTO_COMPLETE_KEY", "TextInputMixin", "coerce_auto_complete_flag"]
