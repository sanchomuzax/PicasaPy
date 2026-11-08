"""#6531 - a bizonyított billentyűutak nézeti mátrixának hiányzó próbái.

Már meglévő, valódi billentyűleütéses bizonyítékra hivatkozunk, nem
ismételjük meg: könyvtár Ctrl+N/M/O/3/K és F2 (#1616, #1615, #1633,
#5150, #2163, #6530); menüsáv Ctrl+P/Shift+P/Enter/Delete/1/2
(#5150_l); Ctrl+T és Alt+Enter (#6301); néző Esc és nyilak
(#4462, #3877, #4525); szerkesztő +/=/-/_ (#4398).

Ez a fájl a hiányzó könyvtári Ctrl+4 és az állóképes néző Space útját
próbálja valódi Qt-billentyűeseménnyel, látható nézetváltással. A §3.3
korábbi billentyűpróbáiból kimaradt Ctrl+A/D, Ctrl+R/Shift+R, Ctrl+S és
Ctrl+Shift+S látható műveleteit is itt ellenőrizzük. A #6531 kiegészítések
a könyvtári Ctrl+F-et is valódi leütéssel mérik. Más fájlokban már megvan
a Ctrl+Enter (#4631), Ctrl+1/2 (#5150_l), Ctrl+5 (#5377), Ctrl+9 negatív
könyvtárnézeti próbája (#4696), a Ctrl+F6/7/8 és a tükrözés (#5150_n),
valamint a projektlap Ctrl+←/→ próbája (#2170); ezeket nem ismételjük.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, timeout: float = 10.0) -> bool:
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


def test_konyvtar_ctrl_f_a_keresomezore_viszi_a_fokuszt(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _aktiv_ablak(window, qt_app, 0)
    racs = _objektum(window, "folderListView")
    keresomezo = _objektum(window, "searchField")
    racs.forceActiveFocus()
    assert _varj(qt_app, lambda: racs.property("activeFocus") is True)
    assert keresomezo.property("activeFocus") is False

    QTest.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)

    assert _varj(
        qt_app, lambda: keresomezo.property("activeFocus") is True
    ), "a könyvtári Ctrl+F nem vitte a fókuszt a keresőmezőre"


def test_szerkeszto_f8_f9_modosito_nelkul_nem_valtoztat_az_allapoton(
    qml_app, qt_app
):
    """A szerkesztő F8/F9 leütése nem írhatja át a nézet vagy a kép állapotát."""
    window, _controller, engine = qml_app
    _aktiv_ablak(window, qt_app, 0)
    window.setProperty("viewerOpen", True)
    viewer = _objektum(window, "photoViewer")
    panel = _objektum(window, "viewerEditorPanel")
    edit_controller = engine.rootContext().contextProperty("editController")
    viewer.setProperty("currentIndex", 0)
    assert _varj(
        qt_app,
        lambda: viewer.isVisible()
        and viewer.property("controllerReady")
        and bool(edit_controller.property("previewSource")),
    ), "a szerkesztő nézője és képmunkamenete nem nyílt meg"
    panel.setProperty("activeTab", 2)
    edit_controller.applyEffect("warm")
    assert _varj(
        qt_app,
        lambda: edit_controller.property("effectChainCounts").get("warm", 0)
        == 1
        and edit_controller.property("canUndo") is True,
    ), "az effekt vagy a visszavonási bejegyzés nem készült el"
    assert _varj(
        qt_app,
        lambda: (effekt := window.findChild(QObject, "effectWarm")) is not None
        and effekt.property("visible") is True,
    ), "az effektlista nem épült fel"
    viewer.forceActiveFocus()
    assert _varj(qt_app, lambda: viewer.property("activeFocus")), (
        "a néző nem kapott fókuszt"
    )

    def szerkeszto_allapot() -> tuple:
        racs = _objektum(window, "effectsGrid")
        effektlista = tuple(
            elem.objectName()
            for elem in racs.findChildren(QObject)
            if elem.objectName().startswith("effect")
        )
        kep = _objektum(window, "viewerImage")
        kepforras = kep.property("source")
        kepforras = (
            kepforras.toString()
            if hasattr(kepforras, "toString")
            else str(kepforras)
        )
        return (
            panel.property("activeTab"),
            viewer.property("currentIndex"),
            str(viewer.property("currentFilePath")),
            kepforras,
            effektlista,
            dict(edit_controller.property("effectChainCounts")),
            tuple(edit_controller._undo_stack),
            tuple(edit_controller._redo_stack),
        )

    elteresek = []
    for billentyu in (Qt.Key.Key_F8, Qt.Key.Key_F9):
        elotte = szerkeszto_allapot()
        QTest.keyClick(window, billentyu, Qt.KeyboardModifier.NoModifier)
        qt_app.processEvents()
        utana = szerkeszto_allapot()
        if utana != elotte:
            elteresek.append((billentyu.name, elotte, utana))

    assert not elteresek, (
        "a módosító nélküli szerkesztőbillentyű megváltoztatta az állapotot: "
        f"{elteresek!r}"
    )


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
