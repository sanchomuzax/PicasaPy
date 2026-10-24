"""A színválasztó az eredeti palettát és az üres MRU-színeket rajzolja (#5730)."""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest

from support.varakozas import var_feltetelre

_MINTAK = (
    "#63001e", "#b10039", "#895227", "#c47338", "#d39815", "#e9a518",
    "#ffbd00", "#ffd154", "#c8c866", "#e3e274", "#629c33", "#85cd44",
    "#8ab28d", "#a8d8ab", "#00727c", "#00b2bd", "#87a2b0", "#a6c7d7",
    "#a9d1e7", "#cde7f6", "#007bc4", "#0091e1", "#002455", "#004baa",
    "#586695", "#778cca", "#38175a", "#692dac", "#c88dac", "#e3a1c4",
)
_MRU_ALAPSZINEK = (
    "#00b2bd", "#87a2b0", "#007bc4", "#00727c", "#692dac",
)
_HSL_PONTOK = {
    0: {
        (90, 100): "#2fd27c",
        (45, 100): "#b4d22f",
        (135, 100): "#2f53d2",
        (90, 56): "#eafaf1",
        (90, 144): "#092c1a",
    },
    1: {
        (90, 100): "#50b17d",
        (45, 100): "#9fb150",
        (135, 100): "#5065b1",
        (90, 56): "#edf6f1",
        (90, 144): "#10251a",
    },
}


def _item(root, name):
    if root is None:
        return None
    if root.objectName() == name:
        return root
    for child in root.childItems() if hasattr(root, "childItems") else ():
        found = _item(child, name)
        if found is not None:
            return found
    if hasattr(root, "findChild"):
        return root.findChild(QObject, name)
    return None


def _pixel(image, x, y):
    dpr = image.devicePixelRatio()
    return image.pixelColor(math.floor(x * dpr), math.floor(y * dpr))


def _assert_pixel(image, x, y, expected):
    actual = _pixel(image, x, y)
    wanted = QColor(expected)
    error = max(
        abs(actual.red() - wanted.red()),
        abs(actual.green() - wanted.green()),
        abs(actual.blue() - wanted.blue()),
    )
    assert error <= 3, (
        f"a ({x:.1f}, {y:.1f}) helyen {expected} helyett {actual.name()} "
        f"jelent meg ({error} szint eltérés)"
    )


def _set_effect_color_panel(window, qt_app):
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
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
    qt_app.processEvents()
    return panel, _item(panel, "effectParamColor0")


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_a_paletta_es_az_ures_mru_helye_es_szine_renderelve_megegyezik(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    ablakmagassag = window.height()
    window.setHeight(ablakmagassag + height_delta)
    assert var_feltetelre(
        qt_app,
        lambda: window.height() == ablakmagassag + height_delta,
        3.0,
    ), "az ablak nem vette fel a tesztmagasságot határidőn belül"
    _panel, swatches = _set_effect_color_panel(window, qt_app)
    assert swatches is not None

    button = _item(swatches, "effectParamColor0SpectrumButton")
    assert button is not None
    scene = button.mapToScene(button.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(scene.x()), round(scene.y())),
    )
    assert var_feltetelre(
        qt_app, lambda: swatches.property("spectrumPickerVisible"), 3.0
    ), "a színválasztó nem nyílt meg határidőn belül"

    assert swatches.property("paletteMode") == 0
    assert abs(swatches.property("spectrumWidth") - 181) <= 3
    assert abs(swatches.property("spectrumHeight") - 147) <= 3
    palette_x = swatches.property("spectrumSceneX")
    palette_y = swatches.property("spectrumSceneY")
    picker = swatches.findChild(QObject, "effectParamColor0Picker")
    assert picker is not None
    field = _item(picker, "effectParamColor0PickerSpectrum")
    assert field is not None
    assert abs(field.property("x") - 20) <= 3
    assert abs(field.property("y") - 15) <= 3

    content = picker.property("contentItem")
    recent = [
        _item(content, f"effectParamColor0PickerRecent{index}")
        for index in range(5)
    ]
    assert all(slot is not None for slot in recent)
    for index, slot in enumerate(recent):
        assert abs(slot.property("x") - (51 + index * 31)) <= 3
        assert abs(slot.property("y") - 15) <= 3
        assert abs(slot.width() - 26) <= 3
        assert abs(slot.height() - 26) <= 3
        assert slot.property("recentColor") == ""

    qt_app.processEvents()
    image = window.grabWindow()
    assert not image.isNull()
    popup_x = palette_x - field.property("x")
    popup_y = palette_y - field.property("y")
    # A kitöltéseket szöveg nélküli, belső képpontban mérjük.
    for index, expected in enumerate(_MINTAK):
        _assert_pixel(
            image,
            palette_x + 1 + index * 6 + 3,
            palette_y + 28 + 6,
            expected,
        )
    for index, expected in enumerate(_MRU_ALAPSZINEK):
        _assert_pixel(
            image,
            popup_x + 51 + index * 31 + 13,
            popup_y + 15 + 13,
            expected,
        )
    for (x, y), expected in _HSL_PONTOK[0].items():
        _assert_pixel(image, palette_x + x + 0.5, palette_y + y + 0.5, expected)

    swatches.setProperty("paletteMode", 1)
    assert var_feltetelre(
        qt_app,
        lambda: picker.property("paletteMode") == 1,
        3.0,
    ), "az 1-es palettamód nem jutott el a panelhez"
    qt_app.processEvents()
    image = window.grabWindow()
    assert not image.isNull()
    for (x, y), expected in _HSL_PONTOK[1].items():
        _assert_pixel(image, palette_x + x + 0.5, palette_y + y + 0.5, expected)
