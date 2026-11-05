"""A vetítés vezérlősávjának biztos előhozása valódi egérmozgatással (#6591).

A sáv az eredeti szabálya szerint (`0x005c4a10`, spec 12.8, #6580) csak akkor
jelenik meg, ha a mutató 50 képpontnál többet mozdul a vonatkoztatási ponttól,
és ez a pont csak 0,5 mp nyugalom után áll be újra. Két gyors, közeli
mozdulat ezért lassú gépen nem hozza elő a sávot; a rejtett sáv átlátszósága
1/256, tehát az `opacity > 0` várakozás sem jelez semmit.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre

_NYUGALOM_MS = 600
_TAVOLSAG_PX = 120


def sav_elohozasa(window, qt_app, controls, cel: QPoint) -> None:
    """Nyugalom, távoli vonatkoztatási pont, majd küszöb feletti mozdulat a célra."""
    QTest.qWait(_NYUGALOM_MS)
    tavoli_y = cel.y() - _TAVOLSAG_PX if cel.y() > _TAVOLSAG_PX else cel.y() + _TAVOLSAG_PX
    QTest.mouseMove(window, QPoint(cel.x(), tavoli_y))
    qt_app.processEvents()
    QTest.mouseMove(window, cel)
    assert varj_feltetelre(
        qt_app, lambda: controls.property("shown") is True, masodperc=10.0
    ), "a küszöb feletti egérmozdulat nem hozta elő a vezérlősávot"
    # a 250 ms-os beúszás végéig a sáv elemei még mozoghatnak
    assert varj_feltetelre(
        qt_app, lambda: controls.property("opacity") >= 0.99, masodperc=10.0
    ), "a vezérlősáv nem jelent meg teljesen"
