"""#4449/#4499: a beállítás kikapcsolva megőrzi a nagyítást, bekapcsolva kilép."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(qt_app, ablak, elem, dupla=False):
    assert _varj(qt_app, lambda: elem.width() > 0 and elem.height() > 0)
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    if dupla:
        QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, pos=pont)
    else:
        QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=pont)


def _nyitott_nezo(
    qml_app, qt_app, magassageltolas, egykattintas, nagyitas=1.0
):
    ablak, controller, _engine = qml_app
    alapmagassag = ablak.height()
    ablak.setHeight(alapmagassag + magassageltolas)
    assert _varj(qt_app, lambda: ablak.height() == alapmagassag + magassageltolas)

    ablak.setProperty("viewerOpen", True)
    viewer = ablak.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    assert _varj(qt_app, lambda: ablak.findChild(QObject, "viewerImage") is not None)
    kep = ablak.findChild(QObject, "viewerImage")
    assert _varj(qt_app, lambda: kep.property("visible"))

    controller.setSingleClickExitEnabled(egykattintas)
    viewer.setProperty("zoomValue", nagyitas)
    pan_area = ablak.findChild(QObject, "viewerPanArea")
    assert pan_area is not None
    assert _varj(qt_app, lambda: pan_area.property("enabled"))
    return ablak, controller, viewer, pan_area


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_kikapcsolva_az_allokepes_dupla_kattintas_nagyitasillesztes_marad(
    qml_app, qt_app, magassageltolas
):
    ablak, _controller, viewer, pan_area = _nyitott_nezo(
        qml_app, qt_app, magassageltolas, egykattintas=False
    )

    _kattints(qt_app, ablak, pan_area)
    assert ablak.property("viewerOpen") is True, (
        "az állóképes egyszeres kattintás bezárta a szerkesztőnézetet"
    )
    _kattints(qt_app, ablak, pan_area, dupla=True)
    assert _varj(qt_app, lambda: abs(viewer.property("zoomFactor") - 1.0) < 0.01), (
        "az állóképes dupla kattintásnak továbbra is nagyítás-illesztést kell adnia"
    )
    ablak.setProperty("viewerOpen", False)


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_bekapcsolva_kattintas_kilep_de_huzas_es_aktiv_atfedok_nem(
    qml_app, qt_app, magassageltolas
):
    # Rontás-kontroll: a bekapcsolt állóképes kattintás bekötése nélkül ez
    # a viselkedési próba piros; a későbbi esetek a kapuk megőrzését mérik.
    ablak, _controller, viewer, pan_area = _nyitott_nezo(
        qml_app, qt_app, magassageltolas, egykattintas=True, nagyitas=0.0
    )
    vissza_gomb = ablak.findChild(QObject, "viewerBackButton")
    assert vissza_gomb is not None

    _kattints(qt_app, ablak, pan_area)
    assert _varj(qt_app, lambda: ablak.property("viewerOpen") is False), (
        "bekapcsolt SingleClickExit mellett a bal kattintás nem lépett ki"
    )

    ablak.setProperty("viewerOpen", True)
    assert _varj(qt_app, lambda: ablak.property("viewerOpen") is True)
    kep = ablak.findChild(QObject, "viewerImage")
    assert kep is not None and _varj(qt_app, lambda: kep.property("visible"))
    viewer.setProperty("zoomValue", 1.0)
    assert _varj(qt_app, lambda: pan_area.property("enabled"))

    kezdo = pan_area.mapToScene(
        QPointF(pan_area.width() / 2, pan_area.height() / 2)
    ).toPoint()
    veg = kezdo + QPoint(24, 12)
    QTest.mousePress(ablak, Qt.MouseButton.LeftButton, pos=kezdo)
    QTest.mouseMove(ablak, veg)
    QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, pos=veg)
    qt_app.processEvents()
    assert ablak.property("viewerOpen") is True, "a pásztázó húzás kiléptetett"

    editor_panel = ablak.findChild(QObject, "viewerEditorPanel")
    assert editor_panel is not None
    editor_panel.setProperty("cropActive", True)
    crop = ablak.findChild(QObject, "cropOverlay")
    assert crop is not None and _varj(qt_app, lambda: crop.property("visible"))
    _kattints(qt_app, ablak, crop)
    assert ablak.property("viewerOpen") is True, "az aktív vágóeszköz kattintása kiléptetett"

    editor_panel.setProperty("cropActive", False)
    editor_panel.setProperty("redeyeActive", True)
    redeye = ablak.findChild(QObject, "redeyeDragArea")
    assert redeye is not None and _varj(qt_app, lambda: redeye.property("visible"))
    _kattints(qt_app, ablak, redeye)
    assert ablak.property("viewerOpen") is True, "az aktív vörösszem-átfedő kattintása kiléptetett"

    editor_panel.setProperty("redeyeActive", False)
    viewer.setProperty("facesVisible", True)
    viewer.setProperty("facesEditMode", True)
    arc_terulet = ablak.findChild(QObject, "facesCreateArea")
    assert arc_terulet is not None
    assert _varj(qt_app, lambda: arc_terulet.property("visible"))
    _kattints(qt_app, ablak, arc_terulet)
    assert ablak.property("viewerOpen") is True, "a képi átfedés alatti kattintás kiléptetett"

    editor_panel.setProperty("retouchActive", True)
    retus = ablak.findChild(QObject, "retouchClickArea")
    assert retus is not None and _varj(qt_app, lambda: retus.property("visible"))
    _kattints(qt_app, ablak, retus)
    assert ablak.property("viewerOpen") is True, "a retusálás alatti kattintás kiléptetett"

    editor_panel.setProperty("retouchActive", False)
    editor_panel.setProperty("textActive", True)
    szoveg = ablak.findChild(QObject, "textClickArea")
    assert szoveg is not None and _varj(qt_app, lambda: szoveg.property("visible"))
    _kattints(qt_app, ablak, szoveg)
    assert ablak.property("viewerOpen") is True, "a szöveg-elhelyezés alatti kattintás kiléptetett"

    editor_panel.setProperty("textActive", False)
    editor_panel.setProperty("neutralPickerActive", True)
    pipetta = ablak.findChild(QObject, "neutralPickArea")
    assert pipetta is not None and _varj(qt_app, lambda: pipetta.property("visible"))
    _kattints(qt_app, ablak, pipetta)
    assert ablak.property("viewerOpen") is True, "a semleges pipetta alatti kattintás kiléptetett"
    ablak.setProperty("viewerOpen", False)


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_kettos_nezetben_a_masik_fel_kattintasa_fokuszt_valt_es_nem_lep_ki(
    qml_app, qt_app, magassageltolas
):
    ablak, _controller, viewer, _pan_area = _nyitott_nezo(
        qml_app, qt_app, magassageltolas, egykattintas=True, nagyitas=0.0
    )
    viewer.setProperty("layoutMode", "ab")
    viewer.setProperty("aktivOldal", "jobb")
    masik_fel = ablak.findChild(QObject, "viewerImageElotte")
    assert masik_fel is not None
    assert _varj(qt_app, lambda: masik_fel.width() > 0 and masik_fel.height() > 0)

    _kattints(qt_app, ablak, masik_fel)

    assert ablak.property("viewerOpen") is True, "a kettős nézetből kilépett a kattintás"
    assert viewer.property("aktivOldal") == "bal", (
        "a másik félre kattintásnak a meglévő fokuszKattintas/TapHandler útján "
        "fókuszt kell váltania"
    )


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_aktiv_kiegyenesitesnel_a_kepkattintas_nem_lep_ki(
    qml_app, qt_app, magassageltolas
):
    ablak, _controller, viewer, pan_area = _nyitott_nezo(
        qml_app, qt_app, magassageltolas, egykattintas=True
    )
    editor_panel = ablak.findChild(QObject, "viewerEditorPanel")
    assert editor_panel is not None
    editor_panel.setProperty("tiltActive", True)
    assert _varj(qt_app, lambda: editor_panel.property("tiltActive"))
    # A Kiegyenesítés illesztésbe teszi a képet. A nagyítás újbóli
    # beállításával külön ellenőrizzük, hogy a pásztázás megmarad.
    viewer.setProperty("zoomValue", 1.0)
    assert _varj(qt_app, lambda: pan_area.property("enabled"))

    _kattints(qt_app, ablak, pan_area)

    assert ablak.property("viewerOpen") is True, "az aktív Kiegyenesítés kattintásra kilépett"
    assert editor_panel.property("tiltActive") is True, "a kattintás lezárta a Kiegyenesítést"


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_bekapcsolt_dupla_kattintas_bezarja_de_nem_nyitja_ujra_a_nezot(
    qml_app, qt_app, magassageltolas
):
    ablak, _controller, _viewer, pan_area = _nyitott_nezo(
        qml_app, qt_app, magassageltolas, egykattintas=True
    )
    pont = pan_area.mapToScene(
        QPointF(pan_area.width() / 2, pan_area.height() / 2)
    ).toPoint()
    kattintas_vege = time.monotonic() + (
        qt_app.styleHints().mouseDoubleClickInterval() / 1000.0
    ) + 0.2

    QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, pos=pont)

    assert _varj(qt_app, lambda: time.monotonic() >= kattintas_vege, 3.0)
    assert ablak.property("viewerOpen") is False, (
        "bekapcsolt SingleClickExit mellett a dupla kattintás után zárva kell "
        "maradnia a nézőnek"
    )
