"""#4936: a Filmszemcse valódi QML-kattintás után a golden kimenetet rajzolja."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

from support.meroadat_kit import extract_meroadat_files
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


_GOLDEN_MEMBERS = (
    "684-merokeszlet/grain__alap.jpg",
    "684-merokeszlet/export/grain__alap.jpg",
)
_GRAIN_SEED_0 = 0x2D8228BE


def _golden_tools():
    root = Path(__file__).resolve().parents[3]
    path = str(root / "tools" / "golden")
    if path not in sys.path:
        sys.path.insert(0, path)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


def _qimage_rgb(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    raw = raw.reshape((height, converted.bytesPerLine()))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


@pytest.fixture
def grain_app(qt_app, tmp_path):
    extracted = extract_meroadat_files(_GOLDEN_MEMBERS, tmp_path / "golden")
    if extracted is None:
        pytest.skip("a helyi mérőadat-archívum nem tartalmazza a 684-es szemcsemintát")

    def create_photo(library: Path) -> None:
        shutil.copyfile(extracted[_GOLDEN_MEMBERS[0]], library / "a.jpg")

    app_root = tmp_path / "app"
    app_root.mkdir()
    app = _build_qml_app(
        qt_app,
        app_root,
        kepeket_keszit=create_photo,
        valodi_belyegkep=True,
    )
    try:
        yield (*next(app), extracted)
    finally:
        app.close()


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_shift_kattintas_a_renderelt_szemcset_a_picasa_goldenhez_igazítja(
    grain_app, qt_app, height_delta
) -> None:
    window, _controller, engine, golden = grain_app
    window.show()
    window.requestActivate()
    window.setProperty("viewerOpen", True)

    viewer = window.findChild(QObject, "photoViewer")
    panel = window.findChild(QObject, "viewerEditorPanel")
    edit_controller = engine.rootContext().contextProperty("editController")
    assert viewer is not None and panel is not None and edit_controller is not None
    viewer.setProperty("currentIndex", 0)
    assert varj_feltetelre(
        qt_app,
        lambda: str(edit_controller.previewSource).startswith("image://editpreview/"),
        10.0,
    ), "a próbakép szerkesztési előnézete nem indult el"

    panel.setProperty("activeTab", 5)
    assert varj_feltetelre(
        qt_app,
        lambda: panel.findChild(QObject, "effectPicnikGrain") is not None,
        5.0,
    ), "a Filmszemcse csempe nem épült fel"
    original_height = window.height()
    window.setHeight(original_height + height_delta)
    assert varj_feltetelre(
        qt_app, lambda: window.height() == original_height + height_delta, 3.0
    ), "a főablak nem vette fel a tesztmagasságot"

    QTest.keyPress(window, Qt.Key.Key_Shift)
    try:
        assert varj_feltetelre(
            qt_app, lambda: panel.property("shiftMasodlagos") is True, 3.0
        ), "a Shift nem választotta ki a régi Filmszemcse effektet"
        button = panel.findChild(QObject, "effectPicnikGrain")
        assert button is not None and button.isVisible()
        assert button.property("szuro") == "grain"
        center = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
    finally:
        QTest.keyRelease(window, Qt.Key.Key_Shift)

    assert varj_feltetelre(
        qt_app,
        lambda: dict(edit_controller.effectChainCounts) == {"grain": 1},
        5.0,
    ), "a valódi csempekattintás nem fűzte a grain réteget a lánchoz"

    preview_url = str(edit_controller.previewSource)
    photo_id = preview_url.split("image://editpreview/", 1)[1].split("?", 1)[0]
    provider = edit_controller._provider
    load, mean_de = _golden_tools()
    source = load(golden[_GOLDEN_MEMBERS[0]])
    export = load(golden[_GOLDEN_MEMBERS[1]])
    from picasapy.render.color import apply_grain

    expected = apply_grain(source, seed=_GRAIN_SEED_0)

    def actual_matches_expected() -> bool:
        image = provider.requestImage(photo_id, None, None)
        return not image.isNull() and np.array_equal(_qimage_rgb(image), expected)

    assert varj_feltetelre(
        qt_app, actual_matches_expected, 30.0
    ), "a QML-kattintás után megjelenő renderelt grain kép nem a k=0 magot használja"

    rendered = _qimage_rgb(provider.requestImage(photo_id, None, None))
    de = mean_de(rendered, export)
    assert de <= 1.6, f"kattintással renderelt grain ΔE {de:.3f} > 1,6"
    screenshot = window.grabWindow()
    assert not screenshot.isNull(), "a QML-ablak nem adott renderelt képkockát"
