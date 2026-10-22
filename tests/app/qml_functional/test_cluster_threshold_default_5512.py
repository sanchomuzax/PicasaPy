"""#5512: a Névcímkék csoportküszöb-csúszkája kirajzolva 85-ön áll."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Slot, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

_KEEPALIVE: list[object] = []


class _FaceControllerStub(QObject):
    @Slot(result=bool)
    def automaticDetectionEnabled(self):
        return True

    @Slot(result=bool)
    def suggestionsEnabled(self):
        return True

    @Slot(result=int)
    def suggestionThreshold(self):
        return 85

    @Slot(result=int)
    def clusterThreshold(self):
        return 85

    @Slot(result=bool)
    def persistFaceToFile(self):
        return True


def _child(root, name: str):
    result = root.findChild(QObject, name)
    assert result is not None, f"{name} nem található a Névcímkék fülön"
    return result


def _render_until_ready(view: QQuickView, qt_app):
    deadline = time.monotonic() + 3.0
    previous = None
    while time.monotonic() < deadline:
        qt_app.processEvents()
        image = view.grabWindow()
        if not image.isNull() and previous is not None and image == previous:
            return image
        previous = image
        QTest.qWait(50)
    pytest.fail("A Névcímkék fül nem rajzolódott ki 3 másodpercen belül")


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
@pytest.mark.parametrize("has_controller", [False, True])
def test_cluster_threshold_default_is_rendered_at_85(
    qt_app, height_offset, has_controller
):
    import picasapy.app.application as app_module

    app_module.allitsd_be_a_stilust()
    app_module._install_ui_font(qt_app)

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    controller = _FaceControllerStub() if has_controller else None
    if controller is not None:
        view.engine().rootContext().setContextProperty("faceScanController", controller)
    view.setColor(QColor("white"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    source = app_module._APP_DIR / "qml" / "PicasaPy" / "OptionsTabNameTags.qml"
    view.setSource(QUrl.fromLocalFile(str(source)))
    assert view.status() == QQuickView.Status.Ready, [
        error.toString() for error in view.errors()
    ]
    root = view.rootObject()
    assert root is not None
    view.resize(500, 240 + height_offset)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    image = _render_until_ready(view, qt_app)

    slider = _child(root, "optionsFaceClusterThresholdSlider")
    assert slider.property("value") == 85
    assert bool(slider.property("enabled")) is has_controller
    handle = slider.property("handle")
    assert handle is not None
    assert abs(slider.property("visualPosition") - 35 / 45) <= 0.01

    handle_x = handle.mapToScene(QPointF(0, 0)).x()
    slider_x = slider.mapToScene(QPointF(0, 0)).x()
    expected_x = (
        slider_x
        + slider.property("leftPadding")
        + slider.property("visualPosition")
        * (slider.property("availableWidth") - handle.width())
    )
    assert abs(handle_x - expected_x) <= 2

    if height_offset == 0 and has_controller:
        output = Path(".bt/kep5512.png")
        output.parent.mkdir(parents=True, exist_ok=True)
        assert image.save(str(output)), f"Nem sikerült elmenteni: {output}"
    _KEEPALIVE.extend((view, root, handle, controller))
