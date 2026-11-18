"""#7206: a forrásimport a főablak panelje, nagy képelőnézettel."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QUrl, Qt
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from support.jpeg_factory import make_minta_jpeg
from support.varakozas import var_feltetelre


def _bejara(item):
    yield item
    if hasattr(item, "childItems"):
        for child in item.childItems():
            yield from _bejara(child)


def _elem(root, name: str):
    found = root.findChild(QObject, name)
    if found is None:
        found = next((item for item in _bejara(root) if item.objectName() == name), None)
    assert found is not None, f"{name} nem található"
    return found


def _kattint(window: QQuickWindow, item, qt_app) -> None:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _import_panel(window, qt_app, height_delta: int = 0):
    window.resize(1280, 800)
    window.show()
    qt_app.processEvents()
    _kattint(window, _elem(window, "toolbarImportButton"), qt_app)
    assert var_feltetelre(
        qt_app,
        lambda: window.findChild(QObject, "importSourceDialog") is not None,
        5,
    ), "az Import belépő nem nyitotta meg a panelt"
    window.setProperty("height", 800 + height_delta)
    qt_app.processEvents()
    return _elem(window, "importSourceDialog")


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_import_panel_is_embedded_and_large_preview_tracks_the_clicked_photo(
    qml_app, qt_app, tmp_path, height_delta
):
    window, _controller, _engine = qml_app
    panel = _import_panel(window, qt_app, height_delta)

    assert isinstance(panel, QQuickItem), "az importfelület nem főablak-panel"
    assert panel.window() == window, "az importfelület külön ablakban nyílt meg"

    source = tmp_path / "forras"
    source.mkdir()
    first = source / "elso.jpg"
    second = source / "masodik.jpg"
    make_minta_jpeg(first, seed=1)
    make_minta_jpeg(second, seed=2)
    panel.setProperty("sourceFolder", str(source))
    panel.setProperty("destFolder", str(tmp_path / "cel"))
    assert QMetaObject.invokeMethod(
        panel, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    assert var_feltetelre(
        qt_app,
        lambda: not panel.property("scanning")
        and panel.property("previewCount") == 2,
        10,
    ), "a próbaképek beolvasása nem fejeződött be"

    thumbnail = _elem(panel, "importSourceThumb:1")
    _kattint(window, thumbnail, qt_app)
    assert panel.property("selectedPreviewIndex") == 1
    preview = _elem(panel, "importSourceLargePreviewImage")
    assert preview.property("visible") is True
    assert QUrl(preview.property("source")).toLocalFile() == str(second)
    assert QUrl(preview.property("source")).toLocalFile() != str(first)


def test_main_window_close_prompts_before_importing_scanned_photos(
    qml_app, qt_app, tmp_path
):
    window, _controller, _engine = qml_app
    panel = _import_panel(window, qt_app)
    source = tmp_path / "forras"
    source.mkdir()
    make_minta_jpeg(source / "kep.jpg")
    (tmp_path / "cel").mkdir()
    panel.setProperty("sourceFolder", str(source))
    panel.setProperty("destFolder", str(tmp_path / "cel"))
    panel.setProperty("namingMode", "date")
    assert QMetaObject.invokeMethod(
        panel, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    assert var_feltetelre(
        qt_app,
        lambda: not panel.property("scanning")
        and panel.property("previewCount") == 1
        and panel.property("canImportAll"),
        10,
    ), "a próbakép nem vált importálhatóvá"

    window.close()

    assert window.isVisible(), "a főablak kérdés nélkül bezárult"
    confirm = _elem(window, "importBeforeCloseDialog")
    assert confirm.property("visible") is True
    assert confirm.property("message") == "Import images before closing Picasa?"
    assert confirm.property("yesText") == "Import Images"
    assert confirm.property("noText") == "Quit"
