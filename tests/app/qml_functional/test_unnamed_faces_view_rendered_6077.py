"""A Névtelen arcok nézet képpontőre a QML-bontás előtt rögzített képekhez."""

from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import Property, QPoint, QPointF, QUrl, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from test_unnamed_faces_view import _StubController, _StubFaceScanController
from tests.support.betucsalad import BETU_FORRAS
from tests.support.varakozas import var_feltetelre

_QML_DIR = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
_GOLDEN_DIR = Path(__file__).parent / "golden" / "unnamed_faces_view_6077"
_HEIGHT_OFFSETS = (-5, 0, 5)
_WINDOW_WIDTH = 1028
_VIEW_WIDTH = 1000
_VIEW_X = 28
_VIEW_Y = 8
_VIEW_HEIGHT = 1005
_FONT_MASK_MARGIN = 4


class _SnapshotFaceScanController(_StubFaceScanController):
    unnamedCountChanged = Signal()

    @Property(int, notify=unnamedCountChanged)
    def unnamedCount(self):
        return sum(len(group.get("faces", [])) for group in self._groups)


@pytest.fixture
def rogzitett_betu(qt_app):
    """A felület minden szövege a csomagolt Open Sansszal rajzolódik.

    A rendszerbetű gépenként más (helyben Noto, a CI-n DejaVu), és a magasabb
    fejléc a teljes arcrácsot lejjebb tolja. A feliratok képpontjai maszkolva
    vannak, de az elrendezést csak azonos betűméretek teszik összevethetővé.
    """
    azonosito = QFontDatabase.addApplicationFont(str(BETU_FORRAS))
    assert azonosito >= 0, "a csomagolt betű nem tölthető be"
    csalad = QFontDatabase.applicationFontFamilies(azonosito)[0]
    eredeti = QGuiApplication.font()
    rogzitett = QFont(eredeti)
    rogzitett.setFamilies([csalad])
    QGuiApplication.setFont(rogzitett)
    QFont.insertSubstitution("Georgia", csalad)
    try:
        yield
    finally:
        QFont.removeSubstitutions("Georgia")
        QGuiApplication.setFont(eredeti)
        QFontDatabase.removeApplicationFont(azonosito)


def _find_item(root: QQuickItem, object_name: str) -> QQuickItem | None:
    if root.objectName() == object_name:
        return root
    for child in root.childItems():
        found = _find_item(child, object_name)
        if found is not None:
            return found
    return None


def _walk_items(root: QQuickItem):
    yield root
    for child in root.childItems():
        yield from _walk_items(child)


def _wait(qt_app, predicate, description: str) -> None:
    assert var_feltetelre(qt_app, predicate, 3.0), description


def _click(window: QQuickWindow, item: QQuickItem, qt_app) -> None:
    assert item.isVisible() and item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _pixels(image: QImage) -> np.ndarray:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    stride = rgba.bytesPerLine()
    data = np.frombuffer(rgba.constBits(), dtype=np.uint8)
    return data.reshape(rgba.height(), stride)[:, : rgba.width() * 4].reshape(
        rgba.height(), rgba.width(), 4
    ).copy()


def test_unnamed_faces_render_failure_saves_comparison_images(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("PICASAPY_RENDER_FAILURE_DIR", str(tmp_path))
    actual = QImage(2, 2, QImage.Format.Format_RGBA8888)
    actual.fill(QColor("#222222"))
    actual.setPixelColor(0, 0, QColor("#ff0000"))
    reference = QImage(2, 2, QImage.Format.Format_RGBA8888)
    reference.fill(QColor("#222222"))

    _save_failure_images(actual, reference, "hiba-proba", 0)

    output_dir = tmp_path / "unnamed_faces_view_6077"
    actual_path = output_dir / "hiba-proba_+0_aktualis.png"
    reference_path = output_dir / "hiba-proba_+0_referencia.png"
    diff_path = output_dir / "hiba-proba_+0_elteres.png"
    assert all(path.is_file() for path in (actual_path, reference_path, diff_path))
    assert QImage(str(actual_path)).pixelColor(0, 0) == QColor("#ff0000")
    assert QImage(str(reference_path)).pixelColor(0, 0) == QColor("#222222")
    difference = QImage(str(diff_path))
    assert difference.pixelColor(0, 0) == QColor("#ff00ff")
    assert difference.pixelColor(1, 1) == QColor("#202020")


def _save_failure_images(
    actual: QImage, reference: QImage, state: str, height_offset: int
) -> None:
    output_dir = os.environ.get("PICASAPY_RENDER_FAILURE_DIR")
    if not output_dir:
        return

    width = max(actual.width(), reference.width())
    height = max(actual.height(), reference.height())
    actual_pixels = np.full((height, width, 4), (32, 32, 32, 255), dtype=np.uint8)
    reference_pixels = np.full_like(actual_pixels, (32, 32, 32, 255))
    actual_array = _pixels(actual)
    reference_array = _pixels(reference)
    actual_pixels[: actual.height(), : actual.width()] = actual_array
    reference_pixels[: reference.height(), : reference.width()] = reference_array

    different = np.any(actual_pixels != reference_pixels, axis=2)
    difference_pixels = np.full_like(actual_pixels, (32, 32, 32, 255))
    difference_pixels[different] = (255, 0, 255, 255)
    difference = QImage(
        difference_pixels.data,
        width,
        height,
        width * 4,
        QImage.Format.Format_RGBA8888,
    ).copy()

    target = Path(output_dir) / "unnamed_faces_view_6077"
    target.mkdir(parents=True, exist_ok=True)
    stem = f"{state}_{height_offset:+d}"
    assert actual.save(str(target / f"{stem}_aktualis.png"), "PNG")
    assert reference.save(str(target / f"{stem}_referencia.png"), "PNG")
    assert difference.save(str(target / f"{stem}_elteres.png"), "PNG")


def _image_status(image: QQuickItem | None) -> str:
    if image is None:
        return "Missing"
    context = QQmlEngine.contextForObject(image)
    expression = QQmlExpression(
        context,
        image,
        "status === Image.Ready ? 'Ready' "
        ": status === Image.Loading ? 'Loading' "
        ": status === Image.Error ? 'Error' : 'Null'",
    )
    value, failed = expression.evaluate()
    return "Unknown" if failed else str(value)


def _text_free_pixels(view: QQuickItem, width: int, height: int) -> np.ndarray:
    valid = np.ones((height, width), dtype=bool)
    for item in _walk_items(view):
        if not item.metaObject().className().startswith("QQuickText"):
            continue
        if not item.isVisible() or item.width() <= 0 or item.height() <= 0:
            continue
        point = item.mapToScene(QPointF(0, 0))
        left = max(0, math.floor(point.x()) - _FONT_MASK_MARGIN)
        top = max(0, math.floor(point.y()) - _FONT_MASK_MARGIN)
        right = min(
            width,
            math.ceil(point.x() + item.width()) + _FONT_MASK_MARGIN,
        )
        bottom = min(
            height,
            math.ceil(point.y() + item.height()) + _FONT_MASK_MARGIN,
        )
        if left < right and top < bottom:
            valid[top:bottom, left:right] = False
    return valid


def _stable_frame(window: QQuickWindow, qt_app, state: str) -> QImage:
    previous: QImage | None = None
    latest: QImage | None = None
    same_frames = 0

    def settled() -> bool:
        nonlocal previous, latest, same_frames
        current = window.grabWindow()
        if current.isNull():
            return False
        same_frames = same_frames + 1 if previous is not None and current == previous else 0
        previous = current
        latest = current
        return same_frames >= 1

    _wait(qt_app, settled, f"nem állt be stabil képkocka: {state}")
    assert latest is not None
    return latest


def _capture_and_compare(
    window: QQuickWindow,
    view: QQuickItem,
    state: str,
    height_offset: int,
    qt_app,
) -> None:
    frames = QSignalSpy(window.frameSwapped)
    window.update()
    _wait(qt_app, lambda: frames.count() > 0, f"nem rajzolódott ki: {state}")
    image = _stable_frame(window, qt_app, state)
    assert not image.isNull(), f"üres képkocka: {state}"

    output_dir = Path.cwd() / ".bt" / "unnamed-faces-6077"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{state}_{height_offset:+d}.png"
    assert image.save(str(output), "PNG")

    reference = _GOLDEN_DIR / f"{state}_{height_offset:+d}.png"
    if os.environ.get("PICASAPY_6077_RECORD") == "1":
        _GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        assert image.save(str(reference), "PNG")
        return

    expected = QImage(str(reference))
    assert not expected.isNull(), f"hiányzik a bontás előtti referencia: {reference}"
    if (
        abs(image.width() - expected.width()) > 3
        or abs(image.height() - expected.height()) > 3
    ):
        _save_failure_images(image, expected, state, height_offset)
    assert abs(image.width() - expected.width()) <= 3, (
        f"{state}: a kép szélessége {image.width()} px, "
        f"a referencia {expected.width()} px"
    )
    assert abs(image.height() - expected.height()) <= 3, (
        f"{state}: a kép magassága {image.height()} px, "
        f"a referencia {expected.height()} px"
    )
    width = min(image.width(), expected.width())
    height = min(image.height(), expected.height())
    current_pixels = _pixels(image)[:height, :width]
    expected_pixels = _pixels(expected)[:height, :width]
    valid = _text_free_pixels(view, width, height)[:height, :width]
    differing_pixels = np.any(current_pixels != expected_pixels, axis=2) & valid
    differing_count = int(np.count_nonzero(differing_pixels))
    if differing_count:
        _save_failure_images(image, expected, state, height_offset)
    assert differing_count == 0, (
        f"{state}: {differing_count} feliratoktól független képpont tér el "
        f"az összevetett {width}×{height} képen"
    )


def _make_scene(qt_app, height_offset: int):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    context_controller = _StubController()
    face_controller = _SnapshotFaceScanController(groups=[])
    engine.rootContext().setContextProperty("controller", context_controller)
    qml_warnings: list[str] = []
    engine.warnings.connect(
        lambda warnings: qml_warnings.extend(
            warning.toString() for warning in warnings
        )
    )
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(str(_QML_DIR / "UnnamedFacesView.qml")),
    )
    view = component.createWithInitialProperties(
        {"faceScanController": face_controller}
    )
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    assert view is not None
    QQmlEngine.setObjectOwnership(view, QQmlEngine.ObjectOwnership.CppOwnership)

    window = QQuickWindow()
    window.setWidth(_WINDOW_WIDTH)
    window.setHeight(_VIEW_HEIGHT + _VIEW_Y + height_offset)
    window.setColor("#e2e2e2")
    view.setParentItem(window.contentItem())
    view.setX(_VIEW_X)
    view.setY(_VIEW_Y)
    view.setWidth(_VIEW_WIDTH)
    view.setHeight(window.height() - _VIEW_Y)
    window.show()
    _wait(
        qt_app,
        lambda: window.isExposed()
        and window.width() == _WINDOW_WIDTH
        and window.height() == _VIEW_HEIGHT + _VIEW_Y + height_offset,
        "a próbaablak nem állt be a kért geometriára",
    )
    return (
        engine,
        component,
        context_controller,
        face_controller,
        window,
        view,
        qml_warnings,
    )


def _make_faces() -> list[dict[str, object]]:
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "face_type_a_name_reference_en38.png"
    thumb_url = QUrl.fromLocalFile(str(fixture)).toString()
    return [
        {
            "faceId": face_id,
            "photoId": face_id,
            "thumbUrl": thumb_url,
            "suggestedName": "",
        }
        for face_id in range(1, 7)
    ]


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_unnamed_faces_states_match_pre_split_images(
    qt_app, rogzitett_betu, height_offset
):
    (
        engine,
        component,
        _context_controller,
        face_controller,
        window,
        view,
        qml_warnings,
    ) = _make_scene(qt_app, height_offset)
    try:
        _capture_and_compare(window, view, "ures", height_offset, qt_app)

        faces = _make_faces()
        face_controller._groups = [{"label": "Csoport", "faces": faces}]
        face_controller.unnamedCountChanged.emit()
        view.reload()
        images = [
            _find_item(view, f"faceImage_{face_id}") for face_id in range(1, 7)
        ]
        loaded = var_feltetelre(
            qt_app,
            lambda: all(
                item is not None
                and _image_status(item) == "Ready"
                and item.property("progress") >= 1.0
                and item.property("paintedWidth") > 0
                for item in images
            ),
            3.0,
        )
        if not loaded:
            actual = window.grabWindow()
            reference = QImage(str(_GOLDEN_DIR / f"arcok_{height_offset:+d}.png"))
            if not actual.isNull() and not reference.isNull():
                _save_failure_images(actual, reference, "arcok", height_offset)
            statuses = []
            for face_id, item in zip(range(1, 7), images, strict=True):
                progress = item.property("progress") if item is not None else "n/a"
                painted_width = (
                    item.property("paintedWidth") if item is not None else "n/a"
                )
                statuses.append(
                    f"{face_id}={_image_status(item)}"
                    f"(progress={progress}, paintedWidth={painted_width})"
                )
            warning_text = " | ".join(qml_warnings) or "nincs QML-betöltési figyelmeztetés"
            pytest.fail(
                "a próbaarcok indexképei nem jutottak Ready állapotba "
                f"(státuszok: {', '.join(statuses)}; QML: {warning_text})"
            )
        _capture_and_compare(window, view, "arcok", height_offset, qt_app)

        first_tile = _find_item(view, "faceTile_1")
        assert first_tile is not None
        _click(window, first_tile, qt_app)
        _wait(
            qt_app,
            lambda: view.property("selectedCount") == 1,
            "az első arckártya nem lett kijelölve",
        )
        _capture_and_compare(window, view, "kijeloles", height_offset, qt_app)

        group_toggle = _find_item(view, "clusterToggleButton")
        assert group_toggle is not None
        _click(window, group_toggle, qt_app)
        _wait(
            qt_app,
            lambda: view.property("grouped") is False,
            "nem nyílt ki a névadó sáv",
        )
        for face_id in (1, 2):
            tile = _find_item(view, f"faceTile_{face_id}")
            assert tile is not None
            _click(window, tile, qt_app)
        name_field = _find_item(view, "unnamedNameField")
        assert name_field is not None and name_field.isVisible()
        _wait(
            qt_app,
            lambda: view.property("selectedCount") == 2,
            "a névadó sávhoz nem jelölődött ki két arc",
        )
        _capture_and_compare(window, view, "nevadó_sav", height_offset, qt_app)
    finally:
        window.close()
        view.setParentItem(None)
        engine.deleteLater()
        qt_app.processEvents()


def test_unnamed_faces_qml_parts_are_each_under_800_lines():
    parts = sorted(_QML_DIR.glob("UnnamedFacesView*.qml"))
    assert parts, "az UnnamedFacesView QML-fájljai nem találhatók"
    oversized = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in parts
        if len(path.read_text(encoding="utf-8").splitlines()) > 800
    }
    assert not oversized, f"800 sornál hosszabb nézetkomponens: {oversized}"
