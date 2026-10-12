"""#4548: szabad színválasztás a szöveg- és effekt-színparaméterekhez."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import (
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QSettings,
    QStandardPaths,
    Qt,
)
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest


def _item(root, name):
    if root is None:
        return None
    if root.objectName() == name:
        return root
    for child in root.childItems():
        found = _item(child, name)
        if found is not None:
            return found
    return None


def _wait_for(qt_app, predicate, description, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return
        time.sleep(0.05)
    assert predicate(), f"határidőn belül nem teljesült: {description}"


def _click_item(window, item, qt_app, x_ratio=0.5, y_ratio=0.5):
    local = QPointF(item.width() * x_ratio, item.height() * y_ratio)
    scene = item.mapToScene(local)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(scene.x()), round(scene.y())),
    )
    qt_app.processEvents()


def _click_point(window, qt_app, x, y):
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(x), round(y)),
    )
    qt_app.processEvents()


def _pick_from_spectrum(window, swatches, qt_app, image_path):
    button = _item(swatches, swatches.objectName() + "SpectrumButton")
    assert button is not None, f"hiányzik a spektrumgomb: {swatches.objectName()}"
    _click_item(window, button, qt_app)

    _wait_for(
        qt_app,
        lambda: swatches.property("spectrumPickerVisible"),
        "a színválasztó megnyílt",
    )
    assert abs(swatches.property("spectrumPickerWidth") - 225) <= 3
    assert abs(swatches.property("spectrumPickerHeight") - 225) <= 3
    window.grabWindow().save(str(image_path.with_name(image_path.stem + "-open.png")))

    _click_point(
        window,
        qt_app,
        swatches.property("hueSceneX") + swatches.property("hueWidth") * 0.72,
        swatches.property("hueSceneY") + 5,
    )
    assert swatches.property("spectrumPickerVisible"), (
        "a spektrumsávra számolt kattintás kívülre esett: "
        f"x={swatches.property('hueSceneX')}, "
        f"y={swatches.property('hueSceneY')}, "
        f"width={swatches.property('hueWidth')}"
    )
    _click_point(
        window,
        qt_app,
        swatches.property("spectrumSceneX") + swatches.property("spectrumWidth") * 0.72,
        swatches.property("spectrumSceneY") + swatches.property("spectrumHeight") * 0.28,
    )

    rendered = window.grabWindow()
    assert not rendered.isNull(), "a színválasztó renderelt képe üres"
    assert rendered.save(str(image_path)), f"nem menthető a render: {image_path}"
    dpr = rendered.devicePixelRatio()
    pixel = rendered.pixelColor(
        round((swatches.property("spectrumSceneX")
               + swatches.property("spectrumWidth") * 0.72) * dpr),
        round((swatches.property("spectrumSceneY")
               + swatches.property("spectrumHeight") * 0.28) * dpr),
    )
    return pixel


@pytest.fixture(autouse=True)
def picasapy_settings_identity(qt_app, tmp_path):
    previous_format = QSettings.defaultFormat()
    default_ini_path = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.GenericConfigLocation
    )
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path)
    )
    qt_app.setOrganizationName("PicasaPy")
    qt_app.setApplicationName("PicasaPy")
    QSettings("PicasaPy", "PicasaPy").clear()
    try:
        yield
    finally:
        settings = QSettings("PicasaPy", "PicasaPy")
        settings.clear()
        settings.sync()
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            default_ini_path,
        )
        QSettings.setDefaultFormat(previous_format)


def test_text_and_effect_colors_are_picked_and_rendered_from_spectrum(
    qml_app, qt_app, tmp_path
):
    window, _controller, _engine = qml_app
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()

    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    panel.setProperty("textActive", True)
    qt_app.processEvents()

    fill = _item(panel, "textFillColorSwatches")
    outline = _item(panel, "textOutlineColorSwatches")
    assert fill is not None and outline is not None
    assert fill.property("showRecentColors") is True
    assert outline.property("showRecentColors") is True

    original_height = window.height()
    for delta, swatches, property_name in (
        (0, fill, "textFillColor"),
        (5, outline, "textOutlineColor"),
    ):
        window.setHeight(original_height + delta)
        qt_app.processEvents()
        pixel = _pick_from_spectrum(
            window, swatches, qt_app, tmp_path / f"{property_name}.png"
        )
        color = QColor(panel.property(property_name))
        assert color != QColor("#ffffff")
        assert max(
            abs(pixel.red() - color.red()),
            abs(pixel.green() - color.green()),
            abs(pixel.blue() - color.blue()),
        ) <= 3, "a renderelt szín eltér a kiválasztott RGB-csatornáktól több mint 3-mal"
        recent = _item(swatches, swatches.objectName() + "Recent0")
        assert recent is not None
        assert recent.property("recentColor") == color.name()
        QMetaObject.invokeMethod(
            swatches, "closeSpectrumPicker", Qt.ConnectionType.DirectConnection
        )

    panel.setProperty("textActive", False)
    panel.setProperty("paramEffectName", "test")
    panel.setProperty("paramEffectParams", [{
        "key": "color",
        "label": "Color",
        "kind": "color",
        "minimum": 0,
        "maximum": 0,
        "step": 1,
        "default": 0,
        "color": "#000000",
    }])
    panel.setProperty("paramEffectValues", ["#000000"])
    panel.setProperty("paramPanelActive", True)
    window.setHeight(original_height - 5)
    qt_app.processEvents()

    effect = _item(panel, "effectParamColor0")
    assert effect is not None
    pixel = _pick_from_spectrum(
        window, effect, qt_app, tmp_path / "effect-color.png"
    )
    values = panel.property("paramEffectValues")
    values = values.toVariant() if hasattr(values, "toVariant") else values
    color = QColor(values[0])
    assert color != QColor("#000000")
    assert max(
        abs(pixel.red() - color.red()),
        abs(pixel.green() - color.green()),
        abs(pixel.blue() - color.blue()),
    ) <= 3
    assert effect.property("showRecentColors") is True
    QMetaObject.invokeMethod(
        effect, "closeSpectrumPicker", Qt.ConnectionType.DirectConnection
    )
    window.setHeight(original_height)
