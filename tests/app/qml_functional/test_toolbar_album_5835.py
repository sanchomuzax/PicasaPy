"""Az eszköztár az üres albumot a profil-indexben tartja (#6278, #5835)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


ALBUM_TOKEN = "58355835583558355835583558355835"
KIADASKEP_MAPPA = "PICASAPY_5835_KIADASKEP_MAPPA"


def _timeline_photo(library: Path) -> None:
    current_folder = library / "a_current"
    album_folder = library / "b_album"
    current_folder.mkdir()
    album_folder.mkdir()
    make_minta_jpeg(current_folder / "current.jpg", size=(640, 400), seed=5835)
    make_minta_jpeg(album_folder / "a.jpg", size=(640, 400), seed=5836)
    (album_folder / ".picasa.ini").write_text(
        f"[.album:{ALBUM_TOKEN}]\n"
        "name=Időrendi próbaalbum\n"
        f"token={ALBUM_TOKEN}\n"
        "[a.jpg]\n"
        f"albums={ALBUM_TOKEN}\n",
        encoding="utf-8",
    )


def _photo(library: Path) -> None:
    make_minta_jpeg(library / "a.jpg", size=(640, 400), seed=5836)


def _item(parent, name: str):
    item = parent.findChild(QObject, name)
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


def _app(qt_app, tmp_path, photos):
    return _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=photos,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _timeline_album_without_folder(window, controller, engine, qt_app) -> None:
    timeline_controller = engine.rootContext().contextProperty("timelineController")
    window.requestActivate()
    QTest.keyClick(window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier)
    assert var_feltetelre(
        qt_app, lambda: window.property("timelineOpen") is True, 3.0
    )
    assert var_feltetelre(
        qt_app,
        lambda: any(
            collection["kind"] == "album"
            and collection["albumToken"] == ALBUM_TOKEN
            for collection in timeline_controller.collections
        ),
        5.0,
    ), "az album nem jelent meg az Időrendben"
    timeline = _item(window, "timelineView")
    collections = list(timeline_controller.collections)
    album_index = next(
        index
        for index, collection in enumerate(collections)
        if collection["kind"] == "album"
        and collection["albumToken"] == ALBUM_TOKEN
    )
    timeline.requestActivate()
    current_index = int(timeline.property("currentIndex"))
    key = Qt.Key.Key_Right if album_index >= current_index else Qt.Key.Key_Left
    for _ in range(abs(album_index - current_index)):
        QTest.keyClick(timeline, key)
        expected_index = current_index + (
            1 if key == Qt.Key.Key_Right else -1
        )
        assert var_feltetelre(
            qt_app,
            lambda expected_index=expected_index: int(
                timeline.property("currentIndex")
            )
            == expected_index,
            3.0,
        )
        current_index = expected_index

    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    assert var_feltetelre(
        qt_app,
        lambda: window.property("timelineOpen") is False
        and controller.currentAlbumToken == ALBUM_TOKEN
        and window.property("selectedIndex") == 0,
        5.0,
    ), "az Időrendből visszatérve nem az album képe lett kijelölve"
    assert controller.viewModeName == "album"
    assert controller.currentFolder != str(
        Path(controller.photos.filePathAt(0)).parent
    )


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_timeline_selected_photo_creates_empty_album_in_its_folder(
    qt_app, tmp_path, height_offset
):
    app = _app(qt_app, tmp_path, _timeline_photo)
    window, controller, engine = next(app)
    try:
        assert var_feltetelre(qt_app, lambda: controller.photos.rowCount() == 2, 5.0)
        other_folder = tmp_path / "kepek" / "a_current"
        album_folder = tmp_path / "kepek" / "b_album"
        controller.selectFolder(str(other_folder))
        assert Path(controller.currentFolder) == other_folder
        target_height = window.height() + height_offset
        window.setHeight(target_height)
        assert var_feltetelre(qt_app, lambda: window.height() == target_height, 3.0)

        _timeline_album_without_folder(window, controller, engine, qt_app)
        ini_path = album_folder / ".picasa.ini"
        ini_before = ini_path.read_bytes() if ini_path.exists() else None
        _click(window, qt_app, _item(window, "toolbarNewAlbumButton"))
        dialog = _item(window, "toolbarNewAlbumPropertiesDialog")
        assert var_feltetelre(qt_app, lambda: dialog.property("opened") is True, 3.0)
        name_field = _item(dialog, "folderPropertiesNameField")
        assert var_feltetelre(
            qt_app,
            lambda: name_field.property("selectedText") == "Untitled",
            3.0,
        )
        name_field.setProperty("text", "Timeline Empty Album 5835")
        assert name_field.property("text") == "Timeline Empty Album 5835"
        _click(window, qt_app, _item(dialog, "folderPropertiesOkButton"))
        assert var_feltetelre(qt_app, lambda: dialog.property("opened") is False, 3.0)

        album = next(
            album
            for album in controller.albums
            if album["name"] == "Timeline Empty Album 5835"
        )
        assert album["count"] == 0
        pane = _item(window, "folderPane")
        albums_model = pane.property("albumsModel")
        if hasattr(albums_model, "toVariant"):
            albums_model = albums_model.toVariant()
        assert any(
            entry["token"] == album["token"] and entry["count"] == 0
            for entry in albums_model
        ), "a bal sávban nem jelent meg a 0 tagú album"

        capture_dir = os.environ.get(KIADASKEP_MAPPA)
        if height_offset == 0 and capture_dir:
            QTest.qWait(500)
            capture = window.grabWindow()
            assert not capture.isNull(), "az új album kiadásképe üres"
            target = Path(capture_dir)
            target.mkdir(parents=True, exist_ok=True)
            assert capture.save(str(target / "uj-album-idorendbol-5835.png"))

        ini_after = ini_path.read_bytes() if ini_path.exists() else None
        assert ini_after == ini_before, (
            "az új, üres album megváltoztatta a mappa .picasa.ini-jét"
        )
        assert not (other_folder / ".picasa.ini").exists()
    finally:
        app.close()


def test_empty_search_shows_folder_required_error_without_ini_write(qt_app, tmp_path):
    app = _app(qt_app, tmp_path, _photo)
    window, controller, _engine = next(app)
    try:
        assert var_feltetelre(qt_app, lambda: controller.photos.rowCount() == 1, 5.0)
        controller.search("nincs-ilyen-kép-5835")
        window.clearSelection()
        assert var_feltetelre(
            qt_app,
            lambda: controller.photos.rowCount() == 0
            and controller.searchActive
            and controller.viewModeName == "search",
            5.0,
        )

        ini_path = tmp_path / "kepek" / ".picasa.ini"
        before = ini_path.read_bytes() if ini_path.exists() else None
        _click(window, qt_app, _item(window, "toolbarNewAlbumButton"))
        dialog = _item(window, "toolbarNewAlbumPropertiesDialog")
        assert var_feltetelre(qt_app, lambda: dialog.property("opened") is True, 3.0)
        name_field = _item(dialog, "folderPropertiesNameField")
        assert var_feltetelre(
            qt_app,
            lambda: name_field.property("selectedText") == "Untitled",
            3.0,
        )
        name_field.setProperty("text", "Unsavable Album 5835")
        _click(window, qt_app, _item(dialog, "folderPropertiesOkButton"))

        error_banner = _item(window, "errorBanner")
        error_text = _item(window, "errorBannerText")
        assert var_feltetelre(
            qt_app,
            lambda: bool(error_banner.property("visible"))
            and str(error_text.property("text")).strip() != "",
            3.0,
        ), "az albummentési hiba nem jelent meg"
        message = str(error_text.property("text")).lower()
        assert "folder" in message or "mapp" in message
        assert controller.albums == []
        after = ini_path.read_bytes() if ini_path.exists() else None
        assert after == before, "a sikertelen mentés megírta a .picasa.ini fájlt"
    finally:
        app.close()
