"""Az eszköztár új, üres albumot hoz létre ini-írás nélkül (#6278)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


def _real_thumbnail_photos(folder: Path) -> None:
    make_minta_jpeg(folder / "a.jpg", size=(640, 400), seed=2)
    make_minta_jpeg(folder / "b.jpg", size=(500, 500), seed=5)


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


def _click(window, qt_app, item) -> None:
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    qt_app.processEvents()


def _type(window, qt_app, text: str) -> None:
    for character in text:
        QTest.keyClick(window, character)
        qt_app.processEvents()


def _app(qt_app, tmp_path):
    return _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_real_thumbnail_photos,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _open_toolbar_dialog(window, qt_app, height_offset: int = 0):
    target_height = window.height() + height_offset
    window.setHeight(target_height)
    assert var_feltetelre(qt_app, lambda: window.height() == target_height, 3.0)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    _click(window, qt_app, _item(window, "toolbarNewAlbumButton"))
    dialog = _item(window, "toolbarNewAlbumPropertiesDialog")
    assert var_feltetelre(qt_app, lambda: dialog.property("opened") is True, 3.0)
    return dialog


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_toolbar_opens_album_properties_and_creates_empty_album(
    qt_app, tmp_path, height_offset
):
    app = _app(qt_app, tmp_path)
    window, controller, _engine = next(app)
    try:
        assert var_feltetelre(qt_app, lambda: controller.photos.rowCount() == 2, 3.0)
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_before = ini_path.read_bytes() if ini_path.exists() else None
        dialog = _open_toolbar_dialog(window, qt_app, height_offset)
        assert dialog.property("title") == "Album Properties"
        name_field = _item(dialog, "folderPropertiesNameField")
        assert name_field.property("text") == "Untitled"
        assert name_field.property("selectedText") == "Untitled"

        screenshot = os.environ.get("PICASAPY_5812_SCREENSHOT")
        if screenshot and height_offset == 0:
            output = Path(screenshot)
            output.parent.mkdir(parents=True, exist_ok=True)
            image = window.grabWindow()
            assert not image.isNull()
            assert image.save(str(output), "JPG", 90)

        _type(window, qt_app, "Budapest")
        assert name_field.property("text") == "Budapest"
        _click(window, qt_app, _item(dialog, "folderPropertiesOkButton"))
        assert var_feltetelre(qt_app, lambda: dialog.property("opened") is False, 3.0)

        albums = list(controller.albums)
        album = next(a for a in albums if a["name"] == "Budapest")
        assert album["count"] == 0
        pane = _item(window, "folderPane")
        model = pane.property("albumsModel")
        if hasattr(model, "toVariant"):
            model = model.toVariant()
        assert any(a["token"] == album["token"] and a["count"] == 0 for a in model)
        ini_after = ini_path.read_bytes() if ini_path.exists() else None
        assert ini_after == ini_before, (
            "az új, üres album létrehozása módosította a mappa .picasa.ini-jét"
        )

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, tmp_path / "kepek")
        controller._reload_after_sync()
        assert next(
            a for a in controller.albums if a["token"] == album["token"]
        )["count"] == 0
    finally:
        app.close()


def test_toolbar_cancel_does_not_write_an_album(qt_app, tmp_path):
    app = _app(qt_app, tmp_path)
    window, controller, _engine = next(app)
    try:
        assert var_feltetelre(qt_app, lambda: controller.photos.rowCount() == 2, 3.0)
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        before = ini_path.read_bytes() if ini_path.exists() else None

        dialog = _open_toolbar_dialog(window, qt_app)
        _click(window, qt_app, _item(dialog, "folderPropertiesCancelButton"))
        assert var_feltetelre(qt_app, lambda: dialog.property("opened") is False, 3.0)

        assert controller.albums == []
        after = ini_path.read_bytes() if ini_path.exists() else None
        assert after == before
    finally:
        app.close()
