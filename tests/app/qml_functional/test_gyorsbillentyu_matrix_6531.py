"""#6531 - a bizonyított billentyűutak nézeti mátrixának hiányzó próbái.

Már meglévő, valódi billentyűleütéses bizonyítékra hivatkozunk, nem
ismételjük meg: könyvtár Ctrl+N/M/O/3/K és F2 (#1616, #1615, #1633,
#5150, #2163, #6530); menüsáv Ctrl+P/Shift+P/Enter/Delete/1/2
(#5150_l); Ctrl+T és Alt+Enter (#6301); néző Esc és nyilak
(#4462, #3877, #4525); szerkesztő +/=/-/_ (#4398).

Ez a fájl a hiányzó könyvtári Ctrl+4 és az állóképes néző Space útját
próbálja valódi Qt-billentyűeseménnyel, látható nézetváltással. A §3.3
korábbi billentyűpróbáiból kimaradt Ctrl+A/D, Ctrl+R/Shift+R, Ctrl+S és
Ctrl+Shift+S látható műveleteit is itt ellenőrizzük.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, timeout: float = 3.0) -> bool:
    return var_feltetelre(qt_app, feltetel, timeout)


def _objektum(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _aktiv_ablak(window, qt_app, magassag_eltolas: int) -> None:
    window.setHeight(window.height() + magassag_eltolas)
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: window.isActive()), "a főablak nem aktiválódott"


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_konyvtar_ctrl4_elinditja_a_diavetitest(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    _aktiv_ablak(window, qt_app, magassag_eltolas)
    vetito = _objektum(window, "slideshowView")
    assert not vetito.property("visible"), "a vetítés már nyitva van"

    QTest.keyClick(window, Qt.Key.Key_4, Qt.KeyboardModifier.ControlModifier)

    assert _varj(qt_app, lambda: vetito.property("visible") is True), (
        "a könyvtári Ctrl+4 nem nyitotta meg a diavetítést"
    )


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_nezo_space_allokepeknel_elinditja_a_diavetitest(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    _aktiv_ablak(window, qt_app, magassag_eltolas)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setProperty("viewerOpen", True)
    nezo = _objektum(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    vetito = _objektum(window, "slideshowView")
    assert _varj(
        qt_app,
        lambda: nezo.isVisible() and nezo.property("activeFocus") is True,
    ), "a nyitott néző nem épült fel vagy nem kapott fókuszt"
    assert vetito.property("visible") is False, "a vetítés már nyitva van"

    QTest.keyClick(window, Qt.Key.Key_Space)

    assert _varj(qt_app, lambda: vetito.property("visible") is True), (
        "a néző Space billentyűje állóképnél nem indította el az automatikus vetítést"
    )


def test_konyvtar_ctrl_a_es_ctrl_d_valtoztatja_a_kijelolest(qml_app, qt_app):
    window, controller, _engine = qml_app
    _aktiv_ablak(window, qt_app, 0)
    _varj(qt_app, lambda: controller.photos.rowCount() > 0)
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)

    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)

    assert _varj(
        qt_app,
        lambda: len(window.property("selectedIndexes").toVariant())
        == controller.photos.rowCount(),
    ), "a könyvtári Ctrl+A nem jelölte ki a képeket"
    QTest.keyClick(window, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
    assert _varj(
        qt_app,
        lambda: window.property("selectedIndexes").toVariant() == [],
    ), "a könyvtári Ctrl+D nem törölte a kijelölést"


def test_konyvtar_ctrl_r_es_ctrl_shift_r_forgatja_a_kijelolt_kepet(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    _aktiv_ablak(window, qt_app, 0)
    _varj(qt_app, lambda: controller.photos.rowCount() > 0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    kezdeti_forgatas = controller.photos.photos[0].rotate_steps
    tray = _objektum(window, "trayTopRow")
    assert tray.property("starTargetRow") == 0
    assert window.property("_szovegmezoneVanFokusz") is False

    QTest.keyClick(window, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier)

    assert _varj(
        qt_app,
        lambda: controller.photos.photos[0].rotate_steps
        == (kezdeti_forgatas + 1) % 4,
        10.0,
    ), (
        "a könyvtári Ctrl+R nem forgatta jobbra a kijelölt képet"
    )
    QTest.keyClick(
        window,
        Qt.Key.Key_R,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
    )
    assert _varj(
        qt_app,
        lambda: controller.photos.photos[0].rotate_steps == kezdeti_forgatas,
        10.0,
    ), (
        "a könyvtári Ctrl+Shift+R nem forgatta vissza a kijelölt képet"
    )


def test_konyvtar_ctrl_shift_s_megnyitja_a_mappa_exportot(qml_app, qt_app):
    window, controller, _engine = qml_app
    _aktiv_ablak(window, qt_app, 0)
    _varj(qt_app, lambda: controller.photos.rowCount() > 0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)

    QTest.keyClick(
        window,
        Qt.Key.Key_S,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
    )

    assert _varj(
        qt_app,
        lambda: (dialog := window.findChild(QObject, "exportDialog")) is not None
        and dialog.property("opened") is True,
    ), "a könyvtári Ctrl+Shift+S nem nyitotta meg az exportálási párbeszédet"


def test_konyvtar_ctrl_s_megerositi_a_szerkesztett_kep_menteset(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    _aktiv_ablak(window, qt_app, 0)
    _varj(qt_app, lambda: controller.photos.rowCount() > 0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    controller.applyEffectMany([0], "enhance")
    assert _varj(
        qt_app,
        lambda: controller.photos.itemAt(0)["hasEdits"] is True,
        10.0,
    ), "a mentési előfeltételként indított képjavítás nem fejeződött be"

    QTest.keyClick(window, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert _varj(
        qt_app,
        lambda: (dialog := window.findChild(QObject, "saveConfirmDialog"))
        is not None and dialog.property("opened") is True,
    ), "a könyvtári Ctrl+S nem nyitotta meg a mentési megerősítést"
