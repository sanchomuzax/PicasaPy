"""#6443: az összevont Glimmer/legacy fül gombjai előnézetet mutatnak."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.conftest import (
    _build_qml_app,
    _module_qml_warnings,  # noqa: F401 — modul-fixture
    _module_user_folder_guard,  # noqa: F401 — modul-fixture
)
from tests.support.varakozas import var_feltetelre


_TAB_6_BUTTONS = (
    "effectMatte",
    "effectNightVision",
    "effectLocalContrast",
    "effectRoundedEdges",
    "effectPicnikGrain",
)
_PIXEL_CHECKS = {
    "effectNightVision",
    "effectLocalContrast",
    "legacyEffect_fill",
    "legacyEffect_autobacklight",
    "legacyEffect_colorfix",
}
EXPECTED_VISIBLE_ROWS = 4.5


def _make_photo(folder):
    make_minta_jpeg(folder / "a.jpg", size=(320, 240), seed=6339)


@pytest.fixture(scope="module")
def app(qt_app, tmp_path_factory, _module_qml_warnings, _module_user_folder_guard):  # noqa: F811
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider
    from picasapy.index import open_index, photos_in_folder
    from tests.support.szinkron_kepszolgaltato import SzinkronValodiBelyegkep

    root = tmp_path_factory.mktemp("effect-tabs-6339")
    generator = _build_qml_app(
        qt_app,
        root,
        kepeket_keszit=_make_photo,
        valodi_belyegkep=True,
    )
    window, _controller, engine = next(generator)
    edit_controller = engine.rootContext().contextProperty("editController")
    with open_index(root / "index.db") as conn:
        records = {
            str(record.id): record
            for record in photos_in_folder(conn, root / "kepek")
        }
    provider = EffectThumbnailProvider(records.get)
    engine.addImageProvider("effectthumb", SzinkronValodiBelyegkep(provider))
    yield window, edit_controller, provider, window.height()
    generator.close()


def _walk(item: QQuickItem):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _maybe_item(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    return window.findChild(QObject, name)


def _item(window, name: str):
    found = _maybe_item(window, name)
    assert found is not None, f"{name} nincs a kirajzolt felületen"
    return found


def _source(item) -> str:
    value = item.property("source")
    return value.toString() if hasattr(value, "toString") else str(value)


def _ready_thumb(item) -> bool:
    context = QQmlEngine.contextForObject(item)
    status_ready = QQmlExpression(context, item, "status === 1").evaluate()
    return (
        bool(item.property("visible"))
        and bool(status_ready)
        and item.property("paintedWidth") > 0
        and max(item.property("implicitWidth"), item.property("implicitHeight")) > 16
    )


def _wait(qt_app, predicate, message: str) -> None:
    assert var_feltetelre(qt_app, predicate, 10.0), message


def _scroll_into_view(qt_app, viewport, item) -> None:
    """A képpontmérés előtt a görgethető csempe kerüljön a viewportba."""
    y = item.mapToItem(viewport, 0, 0).y()
    height = item.height()
    viewport_height = viewport.height()
    current = viewport.property("contentY")
    if y < 0:
        target = current + y
    elif y + height > viewport_height:
        target = current + y + height - viewport_height
    else:
        return
    maximum = max(0.0, viewport.property("contentHeight") - viewport_height)
    viewport.setProperty("contentY", min(max(0.0, target), maximum))
    _wait(
        qt_app,
        lambda: (
            item.mapToItem(viewport, 0, 0).y() >= -0.5
            and item.mapToItem(viewport, 0, 0).y() + item.height()
                <= viewport.height() + 0.5
        ),
        f"{item.objectName()} nem került be a görgethető nézetbe",
    )


def _rgb(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8).reshape(
        height, stride
    )
    return raw[:, : width * 3].reshape(height, width, 3).copy()


def _rendered_thumb(window, thumb) -> np.ndarray:
    """A kirajzolt Image tartalmát vágja ki, a feliratot és a keretet kihagyva."""
    painted_width = float(thumb.property("paintedWidth"))
    painted_height = float(thumb.property("paintedHeight"))
    x = (thumb.width() - painted_width) / 2
    y = (thumb.height() - painted_height) / 2
    top_left = thumb.mapToScene(QPointF(x, y))
    frame = window.grabWindow()
    scale_x = frame.width() / window.width()
    scale_y = frame.height() / window.height()
    left = round(top_left.x() * scale_x)
    top = round(top_left.y() * scale_y)
    width = max(1, round(painted_width * scale_x))
    height = max(1, round(painted_height * scale_y))
    return _rgb(frame.copy(left, top, width, height))


def _assert_pixels_are_effected(window, thumb, provider) -> None:
    pixels = _rendered_thumb(window, thumb)
    assert np.unique(pixels.reshape(-1, 3), axis=0).shape[0] > 4, (
        f"{thumb.objectName()}: egyszínű vagy üres kép rajzolódott ki"
    )
    image_id = _source(thumb).split("image://effectthumb/", 1)[1]
    effect_image = provider.requestImage(image_id, None, None)
    effect_pixels = _rgb(effect_image)
    expected = _rgb(
        effect_image.scaled(
            pixels.shape[1],
            pixels.shape[0],
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    )
    render_difference = np.abs(pixels.astype(np.int16) - expected.astype(np.int16)).mean()
    assert render_difference < 12, (
        f"{thumb.objectName()}: a felület nem a szolgáltató képét rajzolta ki"
    )
    photo_id = image_id.split("/", 1)[0]
    record = provider._lookup(photo_id)
    assert record is not None
    from picasapy.app import effect_thumbnails as mod

    source = provider._source_for(
        Path(record.folder_path) / record.name, record.mtime_ns
    )
    assert source is not None
    source_thumb = mod._scale_to_thumb(mod._rgb_array_to_qimage(source))
    source_pixels = _rgb(source_thumb)
    assert not np.array_equal(effect_pixels, source_pixels), (
        f"{thumb.objectName()}: a megjelenített effekt-előnézet azonos a forrással"
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_combined_effect_tab_renders_four_and_half_rows_of_real_previews(
    app, qt_app, height_delta, tmp_path
):
    window, controller, provider, initial_height = app
    window.resize(window.width(), initial_height + height_delta)
    _wait(
        qt_app,
        lambda: window.height() == initial_height + height_delta,
        "az ablak nem vette fel a teszthez kért magasságot",
    )
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    panel = _item(window, "viewerEditorPanel")

    panel.setProperty("activeTab", 5)
    legacy_effects = {
        effect["key"]: effect for effect in controller.legacyEffects
    }
    assert _maybe_item(window, "legacyEffect_focalpixelate") is None
    assert all(
        effect["enabled"]
        for key, effect in legacy_effects.items()
        if key != "focalpixelate"
    )
    combined_names = _TAB_6_BUTTONS + tuple(
        f"legacyEffect_{key}" for key in legacy_effects
        if key != "focalpixelate"
    )
    def all_previews_ready() -> bool:
        for name in combined_names:
            button = _maybe_item(window, name)
            thumb = _maybe_item(window, name + "Thumb")
            if button is None or thumb is None or not _ready_thumb(thumb):
                return False
        return True

    _wait(
        qt_app,
        all_previews_ready,
        "az összevont fül valamelyik gombján nem töltődött be valódi előnézet",
    )
    viewport = _item(window, "effectsGrid4Viewport")
    for name in combined_names:
        button = _item(window, name)
        thumb = _item(window, name + "Thumb")
        assert button.property("enabled") is True
        assert _source(thumb).startswith("image://effectthumb/")
        if name in _PIXEL_CHECKS:
            _scroll_into_view(qt_app, viewport, thumb)
            _assert_pixels_are_effected(window, thumb, provider)

    grid = _item(window, "effectsGrid4")
    glimmer_last_position = max(
        (
            _item(window, name).mapToItem(grid, 0, 0).y(),
            _item(window, name).mapToItem(grid, 0, 0).x(),
        )
        for name in _TAB_6_BUTTONS
    )
    legacy_first_position = min(
        (
            _item(window, name).mapToItem(grid, 0, 0).y(),
            _item(window, name).mapToItem(grid, 0, 0).x(),
        )
        for name in combined_names
        if name.startswith("legacyEffect_")
    )
    assert legacy_first_position > glimmer_last_position

    tab = _item(window, "editTabEffects4")
    assert tab.property("description") == (
        "Forgotten or deprecated effects brought back to life"
    )
    assert not any(
        item.objectName() in {"editTabLegacy", "legacyEffectsIntro"}
        for item in _walk(window.contentItem())
    )
    row_pitch = _item(window, "effectRoundedEdges").y() - _item(
        window, "effectMatte"
    ).y()
    assert row_pitch > 0
    assert viewport.height() / row_pitch == pytest.approx(
        EXPECTED_VISIBLE_ROWS, abs=0.03
    )

    if height_delta == 0:
        viewport.setProperty("contentY", 0)
        _wait(
            qt_app,
            lambda: abs(viewport.property("contentY")) <= 0.5,
            "az összevont effektlista nem állt vissza a tetejére",
        )
        frame = window.grabWindow()
        scene_origin = panel.mapToScene(QPointF(0, 0))
        scale_x = frame.width() / window.width()
        scale_y = frame.height() / window.height()
        crop = frame.copy(
            round(scene_origin.x() * scale_x),
            round(scene_origin.y() * scale_y),
            round(panel.width() * scale_x),
            round(panel.height() * scale_y),
        )
        assert crop.save(str(tmp_path / "6443-editor-effects.png"))


# rontás-kontroll: tests.app.qml_functional.test_extra_effect_tabs_thumbnails_6339.EXPECTED_VISIBLE_ROWS = 2.5 → 1 failed
