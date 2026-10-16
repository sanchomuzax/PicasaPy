"""#4555: a Ceruzarajz kattintása a specifikáció szerinti csúszkákat nyitja."""

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlEngine

import picasapy.app.application as app_module

from test_effect_sliders import (
    _FakeEditController,
    _as_list,
    _click,
    _make_panel,
)


@pytest.fixture
def pencil_qml_engine(qt_app):
    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


@pytest.mark.parametrize("panel_height", [595, 600, 605])
def test_pencil_sketch_click_opens_the_spec_controls(
    pencil_qml_engine, qt_app, panel_height
):
    panel = _make_panel(pencil_qml_engine, _FakeEditController(), active_tab=4)
    panel.setProperty("height", panel_height)
    qt_app.processEvents()

    button = panel.findChild(QObject, "effectPencilSketch")
    assert button is not None
    assert button.property("visible") is True

    _click(button)
    qt_app.processEvents()

    assert panel.property("paramPanelActive") is True
    assert panel.property("paramEffectName") == "pencilsketch"
    params = _as_list(panel.property("paramEffectParams"))
    assert [param["label"] for param in params] == ["Radius", "Strength", "Fade"]
    assert [
        (param["minimum"], param["maximum"], param["default"])
        for param in params
    ] == [(1.3, 5.0, 2.0), (0.0, 200.0, 100.0), (0.0, 100.0, 0.0)]
    assert _as_list(panel.property("paramEffectValues")) == [2.0, 100.0, 0.0]

    # A feliratok a panel tényleges qsTr-segédjén mennek át, ahogy a
    # kirajzolt feliratok is; a forrásnyelvű tesztben ugyanazt adják vissza.
    for param in params:
        label = param["label"]
        translated = QMetaObject.invokeMethod(
            panel,
            "paramLabel",
            Qt.ConnectionType.DirectConnection,
            Q_RETURN_ARG("QVariant"),
            Q_ARG("QVariant", label),
        )
        assert translated == label
