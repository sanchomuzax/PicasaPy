"""#4068: a hat csúszkás effektpanel zárolja a bal panel tartalmát."""

from pathlib import Path
from time import monotonic

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPointF, QRect, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest


_TOOLS = (
    ("Soft Focus", "radblur", 2, "effectRadblur", "editTabEffects", "soft-focus"),
    ("Focal B&W", "radsat", 2, "effectRadsat", "editTabEffects", "focal-bw"),
    ("Graduated Tint", "dir_tint", 2, "effectDirTint", "editTabEffects", "graduated-tint"),
    ("Glow", "glow2", 2, "effectGlow2", "editTabEffects", "glow"),
    ("Vignette", "vignette", 4, "effectVignette", "editTabEffects3", "vignette"),
    ("Focal Zoom", "focalzoom", 4, "effectFocalZoom", "editTabEffects3", "focal-zoom"),
)


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található a főablakban"
    return item


def _wait_until(qt_app, condition, description: str, timeout_s: float = 3.0):
    deadline = monotonic() + timeout_s
    while not condition() and monotonic() < deadline:
        qt_app.processEvents()
        QTest.qWait(10)
    qt_app.processEvents()
    assert condition(), description


def _click(window, item, qt_app):
    assert item.property("visible") is True, f"{item.objectName()} nem látható"
    point = item.mapToScene(
        QPointF(float(item.property("width")) / 2,
                float(item.property("height")) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point.toPoint(),
    )
    qt_app.processEvents()


def _capture_item(window, item) -> QImage:
    """Az elem tényleges, kirajzolt területét vágja ki az ablak képéből."""
    screenshot = window.grabWindow()
    assert not screenshot.isNull(), "üres szerkesztő-képernyőkép"
    dpr = screenshot.devicePixelRatio()
    origin = item.mapToScene(QPointF(0, 0))
    rect = QRect(
        round(origin.x() * dpr),
        round(origin.y() * dpr),
        round(float(item.property("width")) * dpr),
        round(float(item.property("height")) * dpr),
    )
    return screenshot.copy(rect).convertToFormat(QImage.Format.Format_RGB32)


def _pixels(image: QImage) -> np.ndarray:
    return np.array(
        [
            [
                (color.red(), color.green(), color.blue())
                for color in (image.pixelColor(x, y) for x in range(image.width()))
            ]
            for y in range(image.height())
        ],
        dtype=np.float64,
    )


def _normalized_laplacian_variance(image: QImage) -> float:
    """Kontraszttól független élélesség: halványítás önmagában nem elég."""
    pixels = _pixels(image)
    gray = pixels @ np.array((0.299, 0.587, 0.114))
    contrast = float(gray.std())
    assert contrast > 1.0, "a mérőterület nem tartalmaz képi részletet"
    gray = (gray - gray.mean()) / contrast
    laplace = (
        gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
        - 4.0 * gray[1:-1, 1:-1]
    )
    return float(laplace.var())


def _mean_saturation(image: QImage) -> float:
    pixels = _pixels(image)
    return float((pixels.max(axis=2) - pixels.min(axis=2)).mean())


def _open_viewer(qml_app_negyzet_kepek, qt_app, height: int):
    window, _controller, _engine = qml_app_negyzet_kepek
    window.setProperty("width", 1280)
    window.setProperty("height", height)
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    _wait_until(
        qt_app,
        lambda: _item(window, "viewerEditorPanel").property("visible") is True,
        "a valódi szerkesztőpanel nem nyílt meg",
    )
    return window, viewer, _item(window, "viewerEditorPanel")


@pytest.mark.parametrize("height", (1000, 1005, 1010), ids=("minus-5", "base", "plus-5"))
def test_felfuggesztett_ful_renderelve_elmosott_es_szines_marad(
    qml_app_negyzet_kepek, qt_app, height
):
    """A tiltott fül képe ténylegesen elmosódik, nem pusztán halványabb lesz."""
    window, _viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app, height)
    icon = _item(window, "fixesFillLightIcon")
    active = _capture_item(window, icon)
    active_sharpness = _normalized_laplacian_variance(active)
    active_saturation = _mean_saturation(active)

    _click(window, _item(window, "editTabEffects"), qt_app)
    _click(window, _item(window, "effectRadblur"), qt_app)
    _wait_until(
        qt_app,
        lambda: panel.property("paramPanelActive") is True,
        "a Soft Focus paraméterpanel nem nyílt meg",
    )
    _click(window, _item(window, "editTabFixes"), qt_app)
    _wait_until(
        qt_app,
        lambda: _item(window, "editorTabArea").property("enabled") is False,
        "a Gyakori javítások fül nem került letiltott állapotba",
    )

    disabled = _capture_item(window, icon)
    disabled_sharpness = _normalized_laplacian_variance(disabled)
    disabled_saturation = _mean_saturation(disabled)
    assert disabled_sharpness < active_sharpness * 0.7, (
        "a fül renderelt képe nem mosódott el eléggé: "
        f"aktív={active_sharpness:.3f}, nyitott effekt alatt={disabled_sharpness:.3f}"
    )
    assert disabled_saturation > active_saturation * 0.7, (
        "a csempe renderelt színtelítettsége halványítást jelez: "
        f"aktív={active_saturation:.2f}, nyitott effekt alatt={disabled_saturation:.2f}"
    )
    if height == 1005:
        output_dir = Path.cwd() / ".bt" / "4068"
        output_dir.mkdir(parents=True, exist_ok=True)
        screenshot = window.grabWindow()
        assert screenshot.save(str(output_dir / "soft-focus-after.png")), (
            "a javított állapot képernyőképe nem menthető"
        )


@pytest.mark.parametrize("height", (1000, 1005, 1010), ids=("minus-5", "base", "plus-5"))
def test_a_hat_effektpanel_fulkattintasra_letilt_es_escape_megse(
    qml_app_negyzet_kepek, qt_app, height
):
    """A csempekattintás, a fülsáv és az Escape valódi felületi esemény."""
    window, _viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app, height)
    edit = _item(window, "photoViewer").property("editCtl")
    tab_area = _item(window, "editorTabArea")
    crop_tile = _item(window, "editToolCrop")
    tab_names = {
        0: "editTabFixes",
        1: "editTabFinetune",
        2: "editTabEffects",
        3: "editTabEffects2",
        4: "editTabEffects3",
        5: "editTabEffects4",
        6: "editTabLegacy",
    }

    for label, key, tab, tile_name, tool_tab, screenshot_name in _TOOLS:
        if panel.property("activeTab") != tab:
            _click(window, _item(window, tab_names[tab]), qt_app)

        _click(window, _item(window, tile_name), qt_app)
        _wait_until(
            qt_app,
            lambda: panel.property("paramPanelActive") is True,
            f"{label}: a paraméterpanel nem nyílt meg a csempe kattintására",
        )
        assert panel.property("paramEffectName") == key
        chain_before = str(edit.property("chainValue"))

        _click(window, _item(window, "editTabFixes"), qt_app)
        _wait_until(
            qt_app,
            lambda: tab_area.property("visible") is True,
            f"{label}: az első fül tartalma nem jelent meg",
        )

        # A képernyőkép a látható bizonyíték; a teszt a vezérlők tényleges
        # enabled állapotát és a kattintás következményét is ellenőrzi.
        if height == 1005:
            output_dir = Path.cwd() / ".bt" / "4068"
            output_dir.mkdir(parents=True, exist_ok=True)
            screenshot = window.grabWindow()
            assert not screenshot.isNull(), f"{label}: üres képernyőkép"
            assert screenshot.save(str(output_dir / f"{screenshot_name}.png")), (
                f"{label}: a képernyőkép nem menthető"
            )

        assert tab_area.property("enabled") is False, (
            f"{label}: az első fül tartalma nincs letiltva"
        )
        fill_light_row = _item(window, "fixesFillLightIcon").property("parent")
        assert float(fill_light_row.property("opacity")) == pytest.approx(1.0), (
            f"{label}: a Derítőfény sora áttetszőn halványul az elmosás helyett"
        )
        assert panel.property("activeTab") == tab, (
            f"{label}: a fülsáv kiemelése elmozdult az eszköz füléről"
        )
        assert _item(window, "toolsColumn").property("visible") is True
        assert crop_tile.property("enabled") is False
        assert _item(window, "editUndoButton").property("enabled") is False
        assert _item(window, "editRedoButton").property("enabled") is False

        # Másik fül, vissza az eszköz fülére, majd csempekattintás: mind
        # ugyanabban a passzív első fül-állapotban hagyja a panelt.
        _click(window, _item(window, "editTabFinetune"), qt_app)
        _click(window, _item(window, tool_tab), qt_app)
        _click(window, crop_tile, qt_app)
        assert panel.property("paramPanelActive") is True
        assert panel.property("activeTab") == tab
        assert tab_area.property("enabled") is False
        assert panel.property("cropActive") is False
        assert str(edit.property("chainValue")) == chain_before

        QTest.keyClick(window, Qt.Key.Key_Escape)
        _wait_until(
            qt_app,
            lambda: panel.property("paramPanelActive") is False,
            f"{label}: az Escape nem a Mégse ágat futtatta",
        )
        _wait_until(
            qt_app,
            lambda: panel.property("activeTab") == 0,
            f"{label}: a Mégse után nem az első fül aktív",
        )
        assert tab_area.property("visible") is True
        assert tab_area.property("enabled") is True
        assert str(edit.property("chainValue")) == chain_before
