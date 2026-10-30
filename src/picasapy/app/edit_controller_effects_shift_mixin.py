"""A Shift-állapot követése az effekt-fülön (#798, #2146, #6267)."""

from __future__ import annotations

from .edit_controller_shared import (
    Property,
    QGuiApplication,
    Slot,
)
from .edit_controller_signals import EditControllerSignalsMixin as _Signals


class EditControllerEffectsShiftMixin:
    """A Shift-állapot követése az effekt-fülön (#6267)."""

    @Slot(bool)
    def figyeldAShiftet(self, kell: bool) -> None:  # noqa: N802 — QML-slot
        """A Shift követésének be-/kikapcsolása (#798).

        ⚠️ **MÉRVE, miért nem állandó.** Az első változat az
        alkalmazás-szintű szűrőt a vezérlő születésekor tette fel, és ott
        is hagyta. Az eseményszűrő MINDEN eseményre átlép Pythonba: a
        `tests/app/qml_functional/test_people_panel_26.py` futásideje
        13 s-ról **25 s-ra** nőtt tőle, és két időzítésre épülő próba el is
        bukott. A felhasználó ugyanezt a lassulást kapná az egész
        felületen, egy olyan funkcióért, ami CSAK az effekt-fülön él.

        Ezért a szűrő addig van fent, amíg az effekt-fül látszik — a panel
        kapcsolja. Felrakáskor a pillanatnyi állapotot is beolvassuk, mert
        a felhasználó már a fül megnyitása előtt is nyomhatja a Shiftet.
        """
        kell = bool(kell)
        if kell == self._shift_figyeles:
            return
        alkalmazas = QGuiApplication.instance()
        if alkalmazas is None:
            return
        self._shift_figyeles = kell
        if kell:
            alkalmazas.installEventFilter(self)
            self._allitsd_a_shiftet(self.shiftLenyomva())
        else:
            alkalmazas.removeEventFilter(self)
            self._allitsd_a_shiftet(False)


    def _allitsd_a_shiftet(self, aktiv: bool) -> None:
        if aktiv == self._shift_aktiv:
            return
        self._shift_aktiv = aktiv
        self.shiftAktivChanged.emit()


    @Property(bool, notify=_Signals.shiftAktivChanged)
    def shiftAktiv(self) -> bool:
        """Le van-e nyomva ÉPPEN MOST a Shift (#798).

        Ez a kötés-barát alak: a QML rá köt, és a lenyomás pillanatában
        újraértékelődik. A `shiftLenyomva()` lekérdezés megmarad — a panel
        FELÉPÜLÉSEKOR arra van szükség, mert akkor még nem volt olyan
        billentyű-esemény, amiből a szűrő tudhatna (a felhasználó már a
        fül megnyitása előtt is nyomva tarthatja).
        """
        return self._shift_aktiv


    @Slot(result=bool)
    def shiftLenyomva(self) -> bool:  # noqa: N802 — QML-stílusú név
        """Le van-e nyomva a Shift ÉPPEN MOST (#2146)?

        Az eredeti az effekt-fül felépülésekor **egyszer** kérdezi le
        (`GetAsyncKeyState(VK_SHIFT)`, `0x005d7c91`), és a bitet eltárolja
        (`[ecx+0x33a8]`); a kilenc érintett csempe ezután ezt a tárolt
        értéket nézi, nem a pillanatnyi billentyűállapotot. A QML-ben
        nincs erre API — a `Qt.ShiftModifier` csak eseményből érhető el,
        a fül felépülése viszont nem billentyűesemény.

        ⚠️ A hívó felelőssége, hogy **egyszer** hívja (a fül láthatóvá
        válásakor), és az eredményt eltárolja. Ha képkockánként kérdezné,
        a csempék a Shift minden le-fel nyomására átbillennének — az
        eredeti pontosan ezt NEM teszi.
        """
        from PySide6.QtCore import Qt as QtNs
        from PySide6.QtGui import QGuiApplication

        return bool(
            QGuiApplication.queryKeyboardModifiers()
            & QtNs.KeyboardModifier.ShiftModifier
        )
