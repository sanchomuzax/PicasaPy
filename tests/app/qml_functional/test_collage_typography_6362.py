"""A kollázs feliratának eredeti betűfokozata és alsó gombsora, kirajzolva."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QCoreApplication

from test_collage_settings_tab_946 import _CollageStub, _betolt, _child

_REPO = Path(__file__).resolve().parents[3]
_QML = _REPO / "src/picasapy/app/qml/PicasaPy/CollageSettingsTab.qml"
_THEME = _REPO / "src/picasapy/app/qml/PicasaPy/Theme.qml"
_TS = _REPO / "src/picasapy/app/i18n/picasapy_hu.ts"


def _hivatalos_magyar_felirat() -> str:
    gyoker = ET.parse(_TS).getroot()
    for uzenet in gyoker.iter("message"):
        forras = uzenet.findtext("source")
        if forras == "Show Captions":
            magyar = uzenet.findtext("translation")
            if magyar:
                return magyar
    raise AssertionError("A hivatalos Show Captions fordítás hiányzik a picasapy_hu.ts-ből")


def _kollazs_panel(qt_app, magassag: int, tema: str = "picturepile"):
    from picasapy.app.application_platform import _install_ui_font

    _install_ui_font(qt_app)
    panel = _betolt(
        qt_app,
        b"import QtQuick\nimport PicasaPy 1.0\nCollagePanel { objectName: 'collagePanel' }",
        300,
        magassag,
        _CollageStub(theme=tema),
    )
    felirat = _child(panel, "collageCaptionLabel")
    felirat.setProperty("text", _hivatalos_magyar_felirat())
    QCoreApplication.processEvents()
    kep = panel.property("_view").grabWindow()
    assert not kep.isNull(), "A kollázs-panel nem rajzolódott ki"
    return panel, felirat


def _doboz(item, vonatkoztatasi_elem):
    pont = item.mapToItem(vonatkoztatasi_elem, QPointF(0, 0))
    return (pont.x(), pont.y(), item.width(), item.height())


def test_a_kollazs_felirata_a_megmeretett_betuformatumot_hasznalja():
    qml = _QML.read_text(encoding="utf-8")
    tema = _THEME.read_text(encoding="utf-8")
    cimke = re.search(r"component CheckLabel: Text \{(?P<body>.*?)\n    \}", qml, re.S)
    assert cimke is not None
    for beallitas in (
        "font.family: Theme.uiFamily",
        "font.pixelSize: 12",
        "font.weight: Theme.fontWeightNormal",
    ):
        assert beallitas in cimke.group("body")
    assert re.search(r"readonly property int fontSize: 12\b", tema)
    assert 'readonly property string uiFamily: "Open Sans"' in tema


@pytest.mark.parametrize("magassag", (529, 534, 539))
def test_a_magyar_kepfelirat_egysoros_es_az_also_gombok_felett_marad(
    qt_app, magassag: int
):
    panel, felirat = _kollazs_panel(qt_app, magassag)
    assert felirat.property("lineCount") == 1
    felirat_doboz = _doboz(felirat, panel)
    also_gomb = _child(panel, "collageMakeDesktopButton")
    gomb_doboz = _doboz(also_gomb, panel)
    assert felirat_doboz[1] + felirat_doboz[3] <= gomb_doboz[1]


def test_a_kepfelirat_a_framegrid_gombjaval_sem_fedi_egymast(qt_app):
    panel, felirat = _kollazs_panel(qt_app, 534, tema="framegrid")
    assert felirat.property("lineCount") == 1
    felirat_doboz = _doboz(felirat, panel)
    frame_gomb = _child(panel, "collageSetFrameCenter")
    assert frame_gomb.isVisible()
    frame_doboz = _doboz(frame_gomb, panel)
    assert felirat_doboz[1] >= frame_doboz[1] + frame_doboz[3]
    also_gomb = _child(panel, "collageMakeDesktopButton")
    gomb_doboz = _doboz(also_gomb, panel)
    assert felirat_doboz[1] + felirat_doboz[3] <= gomb_doboz[1]
