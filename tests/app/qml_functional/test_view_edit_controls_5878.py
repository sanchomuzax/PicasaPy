"""A Show Edit Controls csak szerkesztőnézetben aktív (#5878)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from tests.app.qml_functional._racs_helyimenuk_5150_helpers import vizualis_bejaras
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def qml_app_kepekkel(qt_app, tmp_path):
    """Két valódi JPEG a valódi bélyegkép-szolgáltatóval (a kiadásképhez)."""

    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "tengerpart.jpg", size=(640, 480), seed=7)
        make_minta_jpeg(lib / "hegyek.jpg", size=(320, 240), seed=8)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _valodi_belyegkep_kesz(window) -> bool:
    for elem in vizualis_bejaras(window.contentItem()):
        if elem.objectName() != "thumbImage" or not elem.property("source"):
            continue
        kifejezes = QQmlExpression(qmlContext(elem), elem, "status === Image.Ready")
        ertek, hiba = kifejezes.evaluate()
        if not hiba and ertek:
            return True
    return False


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a főablakban nincs {nev}"
    return elem


def _nyisd_nezet_menu(window, qt_app):
    menu = _elem(window, "menuView")
    QMetaObject.invokeMethod(menu, "open", Qt.ConnectionType.DirectConnection)
    _varj(qt_app, lambda: menu.property("visible"), "a Nézet menü nem nyílt meg")
    return menu


def _valodi_menu_kattintas(elem, qt_app) -> None:
    """A menütétel kirajzoló ablakában, a tényleges közepére kattint."""
    ablak = elem.window()
    assert ablak is not None, "a menütételnek nincs kirajzoló ablaka"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def test_konyvtarnezetben_szurke_pipa_nelkuli_es_kiadaskepe(qml_app_kepekkel, qt_app):
    window, controller, _engine = qml_app_kepekkel
    controller.setEditorControlsVisible(True)
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    _varj(qt_app, lambda: _valodi_belyegkep_kesz(window),
          "nem töltődött be valódi bélyegkép", 20.0)

    menu = _nyisd_nezet_menu(window, qt_app)
    tetel = _elem(window, "menuViewEditControls")
    assert tetel.property("enabled") is False, (
        "a Show Edit Controls könyvtárnézetben kattintható"
    )
    assert tetel.property("checked") is False, (
        "a Show Edit Controls könyvtárnézetben pipát mutat"
    )

    kepmappa = os.environ.get("PICASAPY_KIADASKEP_MAPPA")
    if kepmappa:
        kep = window.grabWindow()
        assert not kep.isNull(), "a megnyitott Nézet menüről nem készült kép"
        cel = Path(kepmappa) / "kep-5878.png"
        assert kep.save(str(cel), "PNG"), f"a kiadáskép mentése nem sikerült: {cel}"

    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_nezoben_valodi_kattintas_elrejti_a_bal_fiokot(
    qml_app, qt_app, magassag_elteres
):
    window, controller, _engine = qml_app
    celmagassag = window.height() + magassag_elteres
    window.setHeight(celmagassag)
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    assert window.height() == celmagassag, (
        f"a főablak nem vette fel a kért {celmagassag} px magasságot: "
        f"{window.height()} px"
    )

    window.setProperty("selectedIndex", 0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("viewerOpen", True)
    viewer = _elem(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    controller.setEditorControlsVisible(True)
    _varj(qt_app, viewer.isVisible, "a szerkesztőnézet nem nyílt meg")

    drawer = _elem(window, "viewerLeftDrawer")
    nyitott_szelesseg = drawer.width()
    assert nyitott_szelesseg > 0, "a bal fiók nem látható a szerkesztőnézetben"

    menu = _nyisd_nezet_menu(window, qt_app)
    tetel = _elem(window, "menuViewEditControls")
    assert tetel.property("enabled") is True, (
        "a Show Edit Controls nincs engedélyezve a szerkesztőnézetben"
    )
    assert tetel.property("checked") is True, (
        "a Show Edit Controls pipája nem követi a bal fiók állapotát"
    )

    _valodi_menu_kattintas(tetel, qt_app)
    _varj(
        qt_app,
        lambda: controller.editorControlsVisible is False
        and drawer.width() < nyitott_szelesseg / 2,
        "a menü valódi kattintása nem rejtette el a bal fiókot",
    )
    _varj(qt_app, lambda: not menu.property("visible"), "a Nézet menü nem zárult be")
