"""#7209 (D6): ismétlés nélkül a vetítő a lista végén nyitva marad.

A mérce a docs/specs/paritas-ellenorzes.md #7060/D6 része és a #7197 mérése
(`picasa-colab-jobs` #700, `video__09`): az eredeti ismétlés nélkül az utolsó
dia után nem lép ki és nem fordul vissza, az utolsó képen marad (legalább 47
másodpercig); a kilépés Esc-re vagy az Exit gombra történik, a kézi Right
innen az első képre fordít (#7190).

A teszt a teljes alkalmazásban, valódi időzítővel és valódi billentyűkkel
fut (az alap `qml_app` két képet tartalmaz).

# rontás-kontroll: a régi `advance()` a lista végén `stop()`-ot hív → a
# `maradjon nyitva` próbák javítás nélkül pirosak (FF)
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre

#: a legkisebb diaidő (másodperc): egy léptetés ~1 s, a vizsgálati ablak 3 s
_DIAIDO_S = 1
_TOBB_DIAIDO_MS = 3200


def _show(window) -> QQuickItem:
    show = window.findChild(QQuickItem, "slideshowView")
    assert show is not None, "a slideshowView nem található"
    return show


def _inditas(window, qt_app, controller, *, loop_enabled: bool) -> QQuickItem:
    window.show()
    window.requestActivate()
    window.setVisibility(QWindow.Visibility.Windowed)
    controller.setSlideshowLoop(loop_enabled)
    controller.setSlideshowSeconds(_DIAIDO_S)
    window.startSlideshow(0, False)
    show = _show(window)
    assert varj_feltetelre(
        qt_app,
        lambda: show.property("visible") is True
        and show.property("playing") is True
        and show.property("currentIndex") == 0,
        3.0,
    ), "a vetítés nem indult el az első képről"
    assert show.property("loop") is loop_enabled
    return show


def _varakozik(qt_app, ms: int) -> None:
    """Valódi időt vár az eseményhurok pörgetése mellett."""
    veg = time.monotonic() + ms / 1000.0
    while time.monotonic() < veg:
        qt_app.processEvents()
        QTest.qWait(20)


def test_ismetles_nelkul_az_utolso_kepen_nyitva_marad(qml_app, qt_app):
    window, controller, _engine = qml_app
    show = _inditas(window, qt_app, controller, loop_enabled=False)
    try:
        assert varj_feltetelre(
            qt_app, lambda: show.property("currentIndex") == 1, 4.0
        ), "az automatikus léptetés nem érte el az utolsó képet"
        # Több diaidőn át sem léphet ki, és nem fordulhat vissza.
        _varakozik(qt_app, _TOBB_DIAIDO_MS)
        assert show.property("visible") is True, (
            "az utolsó dia után a vetítés bezárult, pedig nyitva kell maradnia"
        )
        assert show.property("currentIndex") == 1, (
            "az automatikus léptetés visszafordult az első képre"
        )
    finally:
        if show.property("visible"):
            show.stop()


def test_ismetles_nelkul_escre_a_racs_ter_vissza_az_utolso_kep_kijelolve(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    show = _inditas(window, qt_app, controller, loop_enabled=False)
    try:
        assert varj_feltetelre(
            qt_app, lambda: show.property("currentIndex") == 1, 4.0
        ), "az automatikus léptetés nem érte el az utolsó képet"
        _varakozik(qt_app, _TOBB_DIAIDO_MS)
        assert show.property("visible") is True

        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert varj_feltetelre(
            qt_app, lambda: show.property("visible") is False, 3.0
        ), "az Esc nem zárta be a vetítést"
        assert window.property("viewerOpen") is False
        assert window.property("selectedIndex") == 1, (
            "Esc után nem az utoljára látott kép a kijelölt"
        )
    finally:
        if show.property("visible"):
            show.stop()


def test_ismetles_nelkul_a_lista_veg_utan_a_kezi_jobb_az_elsore_fordit(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    show = _inditas(window, qt_app, controller, loop_enabled=False)
    try:
        assert varj_feltetelre(
            qt_app, lambda: show.property("currentIndex") == 1, 4.0
        ), "az automatikus léptetés nem érte el az utolsó képet"
        _varakozik(qt_app, _TOBB_DIAIDO_MS)
        assert show.property("visible") is True

        QTest.keyClick(window, Qt.Key.Key_Right)
        assert varj_feltetelre(
            qt_app, lambda: show.property("currentIndex") == 0, 3.0
        ), "a kézi Right nem fordított az első képre a lista végéről"
        assert show.property("visible") is True
    finally:
        if show.property("visible"):
            show.stop()


def test_ismetles_bekapcsolva_a_lista_vegerol_az_elso_kepre_lep(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    show = _inditas(window, qt_app, controller, loop_enabled=True)
    try:
        assert varj_feltetelre(
            qt_app, lambda: show.property("currentIndex") == 1, 4.0
        ), "az automatikus léptetés nem érte el az utolsó képet"
        assert varj_feltetelre(
            qt_app, lambda: show.property("currentIndex") == 0, 4.0
        ), "ismétléssel az utolsó képről nem lépett az elsőre"
        assert show.property("visible") is True
    finally:
        if show.property("visible"):
            show.stop()

