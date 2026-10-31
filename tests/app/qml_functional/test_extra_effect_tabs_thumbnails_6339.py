"""#6339: a 6. és 7. effektfül használható gombjai valódi előnézetet mutatnak."""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QImage
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
}


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


def _item(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    found = window.findChild(QObject, name)
    assert found is not None, f"{name} nincs a kirajzolt felületen"
    return found


def _source(item) -> str:
    value = item.property("source")
    return value.toString() if hasattr(value, "toString") else str(value)


def _ready_thumb(item) -> bool:
    return (
        bool(item.property("visible"))
        and item.property("paintedWidth") > 0
        and max(item.property("implicitWidth"), item.property("implicitHeight")) > 16
    )


def _wait(qt_app, predicate, message: str) -> None:
    assert var_feltetelre(qt_app, predicate, 10.0), message


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
    from pathlib import Path
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
def test_sixth_and_legacy_effect_tabs_render_real_effect_previews(
    app, qt_app, height_delta
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
    _wait(
        qt_app,
        lambda: all(
            _ready_thumb(_item(window, name + "Thumb"))
            for name in _TAB_6_BUTTONS
            if _item(window, name) is not None
        )
        and all(_item(window, name) is not None for name in _TAB_6_BUTTONS),
        "a 6. fül valamelyik gombján nem töltődött be valódi effekt-előnézet",
    )
    for name in _TAB_6_BUTTONS:
        button = _item(window, name)
        thumb = _item(window, name + "Thumb")
        assert _source(thumb).startswith("image://effectthumb/")
        if name in _PIXEL_CHECKS:
            _assert_pixels_are_effected(window, thumb, provider)

    panel.setProperty("activeTab", 6)
    legacy_effects = {
        effect["key"]: effect for effect in controller.legacyEffects
    }
    legacy_names = {f"legacyEffect_{key}" for key in legacy_effects}
    _wait(
        qt_app,
        lambda: legacy_names.issubset(
            {item.objectName() for item in _walk(window.contentItem())}
        ),
        "a 7. fül örökölt effektgombjai nem épültek fel",
    )
    legacy_buttons = {name: _item(window, name) for name in legacy_names}
    enabled = {
        f"legacyEffect_{key}": legacy_buttons[f"legacyEffect_{key}"]
        for key, effect in legacy_effects.items()
        if effect["enabled"]
    }
    disabled = {
        f"legacyEffect_{key}": legacy_buttons[f"legacyEffect_{key}"]
        for key, effect in legacy_effects.items()
        if not effect["enabled"]
    }
    assert enabled, "a 7. fülön nincs engedélyezett effektgomb"
    assert disabled, "a 7. fül letiltott effektgombjai eltűntek"
    _wait(
        qt_app,
        lambda: all(_ready_thumb(_item(window, name + "Thumb")) for name in enabled),
        "a 7. fül valamelyik engedélyezett gombján nincs valódi előnézet",
    )
    for name in enabled:
        thumb = _item(window, name + "Thumb")
        assert _source(thumb).startswith("image://effectthumb/")
        if name in _PIXEL_CHECKS:
            _assert_pixels_are_effected(window, thumb, provider)
    for name, button in disabled.items():
        thumb = _item(window, name + "Thumb")
        assert button.property("opacity") == pytest.approx(0.45)
        assert _source(thumb) == ""
        assert not thumb.property("visible")
