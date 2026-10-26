"""#5909: HTML-export a Picasa sablonlistájával, leírásával és előnézetével.

A főablak valódi QML-vezérlőin kattintunk, az exportot pedig a tényleges
webexport-motor készíti el. Az elrendezési kattintásokat három ablakmagasságon
futtatjuk a platformfüggetlen geometria ellenőrzésére.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtTest import QTest
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg


@pytest.fixture
def qml_app(qt_app, tmp_path, request):
    # valódi bélyegképek: a kiadásképen ne egyszínű csempe látsszon
    def kepeket_keszit(folder):
        make_minta_jpeg(folder / "a.jpg", size=(320, 240), seed=71)
        make_minta_jpeg(folder / "b.jpg", size=(320, 240), seed=72)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket_keszit,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


SABLONNEVEK = [
    "Template 1, 2-page grey background",
    "Template 2, 2-page black background",
    "Template 3, 2-page white background",
    "Template 4, 1-page grey background",
    "Template 5, 1-page black background",
    "Template 6, 1-page white background",
    "XML Code",
]


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _listava(ertek):
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return list(ertek)


def _kep_proba(engine, image):
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent

    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
Item {
    property var imageItem
    readonly property bool previewReady:
        imageItem ? imageItem.status === Image.Ready : false
    readonly property bool previewFailed:
        imageItem ? imageItem.status === Image.Error : false
}""",
        QUrl(),
    )
    assert component.isReady(), component.errors()
    probe = component.createWithInitialProperties({"imageItem": image})
    assert probe is not None, component.errors()
    return component, probe


def _kattint(elem) -> None:
    pont = elem.mapToScene(
        QPointF(float(elem.width()) / 2, float(elem.height()) / 2)
    ).toPoint()
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )


def _webexport_vezerlo(engine, controller):
    from picasapy.app.webexport_controller import WebExportController

    vezerlo = WebExportController(photo_source=lambda: controller.photos.photos)
    engine.rootContext().setContextProperty("webExportController", vezerlo)
    return vezerlo


def _html_parbeszed(engine, window, controller, qt_app, monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    vezerlo = _webexport_vezerlo(engine, controller)
    QMetaObject.invokeMethod(window, "openWebExport", Qt.ConnectionType.DirectConnection)
    assert _varj(
        qt_app,
        lambda: window.findChild(QObject, "webExportDialog") is not None,
    ), "a webexport-párbeszéd nem épült fel"
    return window.findChild(QObject, "webExportDialog"), vezerlo


def test_a_html_parbeszed_eredeti_feliratai_es_sablonmodellje(
    qml_app, qt_app, monkeypatch, tmp_path
):
    window, controller, engine = qml_app
    dialog, _ = _html_parbeszed(
        engine, window, controller, qt_app, monkeypatch, tmp_path
    )

    assert dialog.property("templateId") == "szurke"
    assert _gyerek(dialog, "webExportTitleLabel").property("text") == "Web page title:"
    assert _gyerek(dialog, "webExportTargetLabel").property("text") == "Folder:"
    assert _gyerek(dialog, "webExportTitleField").property("text") == Path(
        str(controller.currentFolder)
    ).name
    assert _gyerek(dialog, "webExportInstruction").property("text") == (
        "Click a Template Name to view an example.  When you have made your "
        "selection, click Export."
    )
    assert _gyerek(dialog, "webExportGenerateButton").property("text") == "Export"
    assert _gyerek(dialog, "webExportCloseButton").property("text") == "Cancel"

    assert _listava(dialog.property("templateDisplayNames")) == SABLONNEVEK
    assert _gyerek(dialog, "webExportTemplateList").property("count") == 7

    kep_path = os.environ.get("PICASAPY_5909_SCREENSHOT")
    if kep_path:
        assert controller.photos.photos, "a főablak háttérkönyvtárában nincs kép"
        component, probe = _kep_proba(
            engine, _gyerek(dialog, "webExportTemplatePreview")
        )
        assert _varj(
            qt_app,
            lambda: probe.property("previewReady")
            or probe.property("previewFailed"),
        ), f"az előnézet nem töltött be: {component.errors()}"
        assert probe.property("previewReady")
        window.setWidth(max(1800, int(window.width())))
        window.setHeight(max(960, int(window.height())))
        assert _varj(
            qt_app,
            lambda: window.width() >= 1800 and window.height() >= 960,
        ), "a kiadáskép ablakmérete nem állt be"
        foablak_kep = window.grabWindow()
        parbeszed_kep = dialog.grabWindow()
        assert not foablak_kep.isNull() and not parbeszed_kep.isNull()
        painter = QPainter(foablak_kep)
        painter.drawImage(
            QPoint(
                foablak_kep.width() - parbeszed_kep.width() - 24,
                (foablak_kep.height() - parbeszed_kep.height()) // 2,
            ),
            parbeszed_kep,
        )
        painter.end()
        kep_fajl = Path(kep_path)
        kep_fajl.parent.mkdir(parents=True, exist_ok=True)
        assert foablak_kep.save(str(kep_fajl), "PNG")


@pytest.mark.parametrize("delta", [-5, 0, 5], ids=["-5px", "0px", "+5px"])
def test_kattintott_sablon_frissiti_a_leirast_elonezetet_es_exportot(
    qml_app, qt_app, monkeypatch, tmp_path, delta
):
    window, controller, engine = qml_app
    dialog, vezerlo = _html_parbeszed(
        engine, window, controller, qt_app, monkeypatch, tmp_path
    )
    cel = tmp_path / "html-export"
    dialog.setProperty("targetFolder", str(cel))

    leiras = _gyerek(dialog, "webExportTemplateDescription")
    kep = _gyerek(dialog, "webExportTemplatePreview")
    elso_leiras = leiras.property("text")
    elso_kep = kep.property("source").toString()

    lista = _gyerek(dialog, "webExportTemplateList")
    sor = 3
    sor_magassag = float(lista.property("rowHeight"))
    celpont = lista.mapToScene(
        QPointF(float(lista.width()) / 2, sor_magassag * (sor + 0.5))
    ).toPoint()
    QTest.mouseClick(
        lista.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        celpont,
    )
    assert _varj(qt_app, lambda: int(lista.property("currentIndex")) == sor)

    assert dialog.property("templateId") == "szurke-keret"
    assert leiras.property("text") == (
        "Scrollable thumbnail index on left with full view picture on right."
    )
    assert leiras.property("text") != elso_leiras
    assert kep.property("source").toString() != elso_kep
    component, probe = _kep_proba(engine, kep)
    assert _varj(
        qt_app,
        lambda: probe.property("previewReady") or probe.property("previewFailed"),
    ), f"az előnézet nem töltött be: {component.errors()}"
    assert probe.property("previewReady")

    # A tényleges listavezérlő és a gomb elhelyezéséből számolunk; az ablak
    # magassága ±5 px-re változik, a gombnak továbbra is az ablakban kell lennie.
    dialog.setProperty("height", float(dialog.property("fitHeight")) + delta)
    qt_app.processEvents()
    export_gomb = _gyerek(dialog, "webExportGenerateButton")
    gomb_teteje = export_gomb.mapToScene(QPointF(0, 0)).y()
    assert gomb_teteje + float(export_gomb.height()) <= float(dialog.height())

    _kattint(export_gomb)
    assert _varj(qt_app, lambda: (cel / "index.html").is_file(), 30.0)
    assert vezerlo.waitForExport(30.0)
    from picasapy.webexport.catalog import list_bundled_templates

    selected_template = next(
        template
        for template in list_bundled_templates()
        if template.id == "szurke-keret"
    )
    assert (cel / "style.css").read_bytes() == (
        selected_template.path / "style.css"
    ).read_bytes()
