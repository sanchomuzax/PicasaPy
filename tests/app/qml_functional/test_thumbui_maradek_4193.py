"""A #4193 megmaradt, máshol élő és párosítandó thumbui-elemei."""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest


def _elem(ablak, nev: str):
    talalat = ablak.findChild(QObject, nev)
    assert talalat is not None, f"{nev} nem található a főablakban"
    return talalat


def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return feltetel()


def _kattint(ablak, elem, qt_app) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("magassag", (795, 800, 805))
def test_a_keresocsoport_az_eredeti_neven_kapcsolja_a_csillagszurot(
    qml_app_email, qt_app, magassag
):
    """Valódi főablak, kattintás, üres eszköztár-rész mint negatív kontroll."""
    ablak, controller, _engine = qml_app_email
    ablak.resize(1280, magassag)
    ablak.show()
    qt_app.processEvents()

    csoport = _elem(ablak, "searchgroup")
    eszkoztar = _elem(ablak, "mainToolbar")
    csillag = _elem(ablak, "starFilterButton")
    assert csoport.property("visible") is True
    csoport_pont = csoport.mapToItem(eszkoztar, QPointF(0, 0))
    assert -3 <= csoport_pont.y() <= eszkoztar.height() + 3
    assert controller.filterActive is False

    _kattint(ablak, csillag, qt_app)
    assert _var(qt_app, lambda: controller.filterActive is True)

    kep = ablak.grabWindow()
    dpr = kep.devicePixelRatio()
    ures_pont = csillag.mapToScene(QPointF(3, csillag.height() / 2))
    kirajzolt = kep.pixelColor(
        round(ures_pont.x() * dpr), round(ures_pont.y() * dpr)
    )
    assert kirajzolt == QColor(csillag.property("color"))

    # A gombsor alsó üres sarka nem válthatja át a szűrőt.
    ures_toolbar_pont = eszkoztar.mapToScene(
        QPointF(2, eszkoztar.height() - 2)
    )
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(ures_toolbar_pont.x()), round(ures_toolbar_pont.y())),
    )
    qt_app.processEvents()
    assert controller.filterActive is True


@pytest.mark.parametrize("magassag", (795, 800, 805))
def test_a_fiokvalto_eredeti_nevu_lathatatlan_kattinthato_terulet(
    qml_app_email, qt_app, magassag
):
    """A fiók valódi kattintással nyílik; a mellette kattintás nem nyitja ki."""
    ablak, _controller, _engine = qml_app_email
    ablak.resize(1280, magassag)
    ablak.show()
    qt_app.processEvents()

    fogo = _elem(ablak, "toggle_right_drawer")
    fiok = _elem(ablak, "rightDrawer")
    assert fogo.property("opacity") == 0
    assert fiok.width() == 0
    nyitott_szelesseg = fiok.property("alapSzelesseg")

    kozeppont = fogo.mapToScene(QPointF(-5, fogo.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozeppont.x()), round(kozeppont.y())),
    )
    qt_app.processEvents()
    assert fiok.width() == 0
    assert ablak.property("activeDrawerTab") == ""

    _kattint(ablak, fogo, qt_app)
    assert _var(qt_app, lambda: fiok.width() >= 1)
    assert _var(
        qt_app, lambda: abs(fiok.width() - nyitott_szelesseg) <= 3
    )
    assert ablak.property("activeDrawerTab") != ""


def test_klipgyujto_uzenet_qstr_je_az_eredeti_angol_forrasszoveg():
    qml = (
        Path(picasapy.app.__file__).parent
        / "qml"
        / "PicasaPy"
        / "TrayBar.qml"
    ).read_text(encoding="utf-8")
    eredeti = (
        'Select items to add to your project\'s clips tray, then press the '
        '"Back" button to return to your project'
    )
    qml_literal = eredeti.replace('"', '\\"')
    assert f'text: qsTr("{qml_literal}")' in qml


@pytest.mark.parametrize("magassag", (795, 800, 805))
def test_klipgyujto_uzenet_lathato_magyarul_es_a_vissza_gomb_mukodik(
    qml_app_email, qt_app, magassag
):
    """A renderelt főablak üzenetét valódi gombkattintás viszi a projektre."""
    ablak, _controller, _engine = qml_app_email
    ablak.resize(1280, magassag)
    ablak.show()
    qt_app.processEvents()
    ablak.setProperty("backToCollagePrompted", True)
    qt_app.processEvents()

    sav = _elem(ablak, "traySingleActionBar")
    uzenet = _elem(ablak, "traySingleActionMessage")
    csoport = _elem(ablak, "traySingleActionGroup")
    vissza = _elem(ablak, "traySingleActionReturn")
    tabsav = _elem(ablak, "documentTabStrip")
    assert _var(qt_app, lambda: sav.isVisible())
    assert uzenet.property("text") == (
        'Jelölje ki azokat az elemeket, amelyeket a projekt kliptálcájára '
        'fel szeretne venni, majd a "Vissza" gombra kattintva térjen '
        'vissza a projekthez'
    )

    csoport_eredete = csoport.mapToItem(sav, QPointF(0, 0))
    assert abs(
        csoport_eredete.x() + csoport.width() / 2 - sav.width() / 2
    ) <= 3

    # A háttér képpontját mérjük, nem a gépenként eltérő betűket.
    kep = ablak.grabWindow()
    dpr = kep.devicePixelRatio()
    ures_pont = sav.mapToScene(QPointF(10, sav.height() / 2))
    kirajzolt = kep.pixelColor(
        round(ures_pont.x() * dpr), round(ures_pont.y() * dpr)
    )
    assert kirajzolt == QColor(sav.property("color"))

    lap_elotte = tabsav.property("activeTabId")
    assert lap_elotte != ablak.property("collageTabId")
    _kattint(ablak, uzenet, qt_app)
    assert tabsav.property("activeTabId") == lap_elotte
    assert ablak.property("backToCollagePrompted") is True

    _kattint(ablak, vissza, qt_app)
    assert _var(
        qt_app,
        lambda: tabsav.property("activeTabId")
        == ablak.property("collageTabId"),
    )
    assert ablak.property("backToCollagePrompted") is False
