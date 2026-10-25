"""A Fájl ▸ Move to New Folder a közös Folder Properties párbeszédet nyitja (#5853)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QDate, QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.ini import load_or_empty, read_folder_date_override, read_folder_music
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


def _make_photos(library: Path) -> None:
    make_minta_jpeg(library / "a.jpg", size=(640, 400), seed=2)
    make_minta_jpeg(library / "b.jpg", size=(500, 500), seed=5)


@pytest.fixture
def app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_make_photos,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _wait(qt_app, condition, timeout=10.0) -> bool:
    return var_feltetelre(qt_app, condition, timeout)


def _item(root, name: str):
    item = _objektum(root, name)
    assert item is not None, f"{name} nem található"
    return item


def _open_properties(window, qt_app):
    menu_bar = window.property("menuBar")
    file_menu = next(
        menu for menu in menu_bar.findChildren(QObject)
        if menu.property("title") in {"&File", "&Fájl"}
    )
    QMetaObject.invokeMethod(
        file_menu, "open", Qt.ConnectionType.DirectConnection
    )
    menu_item = _item(window, "menuFileMoveToNewFolder")
    assert _wait(qt_app, lambda: menu_item.property("visible") is True)
    _kattints(qt_app, menu_item)
    dialog = _item(window, "moveToNewFolderDialog")
    assert _wait(qt_app, lambda: dialog.property("opened") is True), (
        "a Fájl ▸ Move to New Folder kattintása nem nyitott párbeszédet"
    )
    return dialog


def _replace_text(window, qt_app, item, value: str) -> None:
    _kattints(qt_app, item)
    QTest.keyEvent(
        QTest.KeyAction.Click,
        window,
        Qt.Key.Key_A,
        Qt.KeyboardModifier.ControlModifier,
    )
    for character in value:
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(character))
    qt_app.processEvents()


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_move_to_new_folder_properties_cancel_then_ok(
    app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = app
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    assert _wait(qt_app, lambda: controller.photos.rowCount() == 2)
    base_height = window.height()
    target_height = base_height + height_offset
    window.resize(window.width(), target_height)
    assert _wait(qt_app, lambda: window.height() == target_height)

    source = Path(controller.photos.filePathAt(0))
    other = Path(controller.photos.filePathAt(1))
    assert source.is_file() and other.is_file()
    source_ini = source.parent / ".picasa.ini"
    original_ini = source_ini.read_bytes() if source_ini.exists() else None
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    dialog = _open_properties(window, qt_app)
    assert dialog.property("title") == "Folder Properties"
    name = _item(dialog, "folderPropertiesNameField")
    assert name.property("text") == "Untitled"
    assert name.property("selectedText") == "Untitled"

    today = QDate.currentDate().toString(Qt.DateFormat.ISODate)
    date = _item(dialog, "folderPropertiesDateField")
    assert dialog.property("currentDate") == today
    assert date.property("text")
    assert dialog.property("_dateValid") is True
    assert _item(dialog, "folderPropertiesUseMusic") is not None
    assert _item(dialog, "folderPropertiesMusicBrowseButton") is not None
    assert _item(dialog, "folderPropertiesLocation") is not None
    assert _item(dialog, "folderPropertiesDescription") is not None
    # job-261: az eredeti Move to New Folder párbeszédében nincs „Automatic date”.
    assert _item(dialog, "folderPropertiesAutomaticDate").property("visible") is False

    screenshot = os.environ.get("PICASA_5853_SCREENSHOT")
    if screenshot and height_offset == 0:
        output = Path(screenshot)
        output.parent.mkdir(parents=True, exist_ok=True)
        image = window.grabWindow()
        assert not image.isNull()
        assert image.save(str(output), "PNG")

    _kattints(qt_app, _item(dialog, "folderPropertiesCancelButton"))
    assert _wait(qt_app, lambda: dialog.property("opened") is False)
    assert source.is_file()
    assert other.is_file()
    assert not (source.parent / "Trip 5853").exists()
    assert (
        source_ini.read_bytes() if source_ini.exists() else None
    ) == original_ini

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    dialog = _open_properties(window, qt_app)
    name = _item(dialog, "folderPropertiesNameField")
    for character in "Trip 5853":
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(character))
    qt_app.processEvents()
    assert name.property("text") == "Trip 5853"

    _kattints(qt_app, _item(dialog, "folderPropertiesUseMusic"))
    assert _item(dialog, "folderPropertiesMusicPath").property("enabled") is True
    music_file = tmp_path / "sample.mp3"
    music_file.write_bytes(b"music placeholder")
    _replace_text(
        window, qt_app, _item(dialog, "folderPropertiesMusicPath"), str(music_file)
    )
    _replace_text(
        window, qt_app, _item(dialog, "folderPropertiesLocation"), "California"
    )
    _replace_text(
        window, qt_app, _item(dialog, "folderPropertiesDescription"), "Trip notes"
    )
    _kattints(qt_app, _item(dialog, "folderPropertiesOkButton"))
    assert _wait(qt_app, lambda: dialog.property("opened") is False)

    target = source.parent / "Trip 5853"
    moved = target / source.name
    assert _wait(qt_app, moved.is_file), f"a kép nem került át ide: {moved}"
    assert not source.exists(), "a kép a forrásmappában is megmaradt"
    assert other.is_file(), "a nem kijelölt kép is elmozdult"

    document = load_or_empty(target / ".picasa.ini")
    properties = document.section("Picasa")
    assert read_folder_date_override(document) == today
    assert properties is not None
    assert properties.get("location") == "California"
    assert properties.get("description") == "Trip notes"
    music_enabled, stored_music_file = read_folder_music(document)
    assert music_enabled is True
    assert Path(stored_music_file) == music_file


def test_enter_accepts_folder_properties_and_moves_selected_photo(app, qt_app):
    window, controller, _engine = app
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    assert _wait(qt_app, lambda: controller.photos.rowCount() == 2)
    source = Path(controller.photos.filePathAt(0))
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    dialog = _open_properties(window, qt_app)
    name = _item(dialog, "folderPropertiesNameField")
    assert name.property("selectedText") == "Untitled"
    for character in "Enter Folder":
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(character))
    QTest.keyEvent(QTest.KeyAction.Click, window, Qt.Key.Key_Return)
    assert _wait(qt_app, lambda: dialog.property("opened") is False)
    assert _wait(qt_app, lambda: (source.parent / "Enter Folder" / source.name).is_file())
    assert not source.exists()
