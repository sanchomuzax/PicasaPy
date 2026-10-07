"""#4482: mappaátnevezés tényleges párbeszéd-kattintással, három magasságon."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.app.models import FolderListModel
from picasapy.index import open_index, sync_tree
from picasapy.ini import (
    parse_document,
    save_document,
    with_folder_date_override,
    with_folder_music,
)
from support.jpeg_factory import make_jpeg


def _wait(qt_app, condition, seconds=5.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        try:
            if condition():
                return True
        except (AttributeError, RuntimeError):
            pass
        time.sleep(0.01)
    return bool(condition())


def _click(window, item):
    assert item is not None and item.property("enabled") is True
    center = item.mapToScene(
        QPointF(float(item.property("width")) / 2,
                float(item.property("height")) / 2)
    )
    assert 0 <= center.x() < window.width()
    assert 0 <= center.y() < window.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _type_text(window, item, value):
    _click(window, item)
    QTest.keyClick(
        window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier
    )
    assert value.isascii()
    for char in value:
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(char))


def _folder_paths(controller):
    model = controller.folders
    return {
        model.data(model.index(row, 0), FolderListModel.PathRole)
        for row in range(model.rowCount())
        if model.data(model.index(row, 0), FolderListModel.KindRole) == "folder"
    }


def _open_properties(window, controller, folder, qt_app):
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    assert dialog is not None
    dialog.setProperty("mode", "folder")
    dialog.setProperty("folderPath", str(folder))
    dialog.setProperty("folderName", folder.name)
    dialog.setProperty("currentDate", controller.folderDateOverride(str(folder)))
    dialog.setProperty(
        "currentDescription", controller.folderDescriptionOf(str(folder))
    )
    dialog.setProperty(
        "currentMusicEnabled", controller.folderMusicEnabled(str(folder))
    )
    dialog.setProperty(
        "currentMusicFile", controller.folderMusicFile(str(folder))
    )
    dialog.open()
    assert _wait(
        qt_app,
        lambda: dialog.property("opened")
        and window.findChild(QObject, "folderPropertiesNameField") is not None
        and window.findChild(QObject, "folderPropertiesNameField").property(
            "selectedText"
        ) == folder.name,
    ), "a mappa Név mezője nem nyílt meg kijelölt szöveggel"
    return dialog, window.findChild(QObject, "folderPropertiesNameField")


def _wait_idle(controller, qt_app):
    assert _wait(
        qt_app,
        lambda: not controller._sync_running and not controller._dirty_running,
        12.0,
    ), "az átnevezés utáni indexfrissítés nem fejeződött be"


def test_nev_mezo_ok_atnevezes_es_mappalista_kepek_harom_ablakmagassagon(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    folder = library / "old-name"
    (folder / "child").mkdir(parents=True)
    make_jpeg(folder / "photo.jpg")
    make_jpeg(folder / "child" / "nested.jpg")
    music = tmp_path / "background.mp3"
    music.write_bytes(b"zene")
    ini = parse_document("").with_value(
        "Picasa", "description", "Megőrzött leírás"
    )
    ini = with_folder_date_override(ini, "2024-02-03")
    ini = with_folder_music(ini, True, str(music))
    save_document(ini, folder / ".picasa.ini")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload(preserve_scroll=True)
    controller.selectFolder(str(folder))

    original_height = window.height()
    try:
        for delta, new_name in ((-5, "renamedm5"), (0, "renamed0"), (5, "renamedp5")):
            window.resize(window.width(), original_height + delta)
            assert _wait(
                qt_app,
                lambda d=delta: window.height() == original_height + d,
            )
            _wait_idle(controller, qt_app)
            dialog, name_field = _open_properties(
                window, controller, folder, qt_app
            )
            assert name_field.property("enabled") is True
            _type_text(window, name_field, new_name)
            assert _wait(
                qt_app,
                lambda field=name_field, expected=new_name: (
                    field.property("text") == expected
                ),
            )
            ok = window.findChild(QObject, "folderPropertiesOkButton")
            assert ok is not None
            _click(window, ok)

            target = folder.with_name(new_name)
            assert _wait(
                qt_app,
                lambda current_dialog=dialog, new_path=target: (
                    not current_dialog.property("opened")
                    and controller._current_folder == str(new_path)
                ),
            ), "az OK nem nevezte át a kijelölt mappát"
            assert target.is_dir() and not folder.exists()
            assert str(target) in _folder_paths(controller)
            assert str(target / "child") in _folder_paths(controller)
            assert str(folder) not in _folder_paths(controller)
            assert [
                photo.name
                for photo in controller.photos.photos
                if photo.folder_path == str(target)
            ] == ["photo.jpg"]
            assert controller.folderDescriptionOf(str(target)) == "Megőrzött leírás"
            assert controller.folderDateOverride(str(target)) == "2024-02-03"
            assert controller.folderMusicEnabled(str(target)) is True
            assert controller.folderMusicFile(str(target)) == str(music)
            _wait_idle(controller, qt_app)
            folder = target
    finally:
        window.resize(window.width(), original_height)


def test_lefoglalt_celnel_kattintasra_hiba_latszik_es_semmi_nem_valtozik(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    folder = library / "source-name"
    target = library / "alreadyexists"
    folder.mkdir()
    target.mkdir()
    make_jpeg(folder / "source.jpg")
    make_jpeg(target / "target.jpg")
    (target / "sentinel.txt").write_text("marad", encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload(preserve_scroll=True)
    controller.selectFolder(str(folder))

    original_height = window.height()
    try:
        for delta in (-5, 0, 5):
            window.resize(window.width(), original_height + delta)
            assert _wait(
                qt_app,
                lambda d=delta: window.height() == original_height + d,
            )
            dialog, name_field = _open_properties(
                window, controller, folder, qt_app
            )
            # A mező tényleges gépelését a sikerút teszteli; itt a már
            # foglalt cél nevét állítjuk be, és az OK kattintás hibaútját mérjük.
            name_field.setProperty("text", "alreadyexists")
            ok = window.findChild(QObject, "folderPropertiesOkButton")
            _click(window, ok)

            error_dialog = window.findChild(
                QObject, "folderPropertiesRenameErrorDialog"
            )
            assert _wait(
                qt_app,
                lambda message_dialog=error_dialog: (
                    message_dialog is not None
                    and message_dialog.property("visible")
                ),
            ), (
                "ütköző névnél nem jelent meg a hibaüzenet: "
                f"{dialog.property('renameError')!r}"
            )
            assert "már létezik" in error_dialog.property("text")
            assert dialog.property("opened") is True
            assert folder.is_dir() and target.is_dir()
            assert (folder / "source.jpg").exists()
            assert (target / "sentinel.txt").read_text(encoding="utf-8") == "marad"
            assert str(folder) in _folder_paths(controller)
            assert str(target) in _folder_paths(controller)
            error_dialog.close()
            dialog.close()
            assert _wait(
                qt_app,
                lambda properties_dialog=dialog, message_dialog=error_dialog: (
                    not properties_dialog.property("opened")
                    and not message_dialog.property("visible")
                ),
            )
    finally:
        window.resize(window.width(), original_height)


def test_enter_a_nev_mezoben_ugyanugy_atnevez_mint_az_ok_gomb(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    folder = library / "old-name"
    folder.mkdir(parents=True)
    make_jpeg(folder / "photo.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload(preserve_scroll=True)
    controller.selectFolder(str(folder))

    original_height = window.height()
    try:
        for delta, new_name in ((-5, "enter-m5"), (0, "enter-0"), (5, "enter-p5")):
            window.resize(window.width(), original_height + delta)
            assert _wait(qt_app, lambda d=delta: window.height() == original_height + d)
            _wait_idle(controller, qt_app)
            dialog, name_field = _open_properties(window, controller, folder, qt_app)
            _type_text(window, name_field, new_name)
            assert _wait(qt_app, lambda f=name_field, n=new_name: f.property("text") == n)

            QTest.keyClick(window, Qt.Key.Key_Return)

            target = folder.with_name(new_name)
            assert _wait(
                qt_app,
                lambda current_dialog=dialog, new_path=target: (
                    not current_dialog.property("opened")
                    and controller._current_folder == str(new_path)
                ),
            ), "az Enter nem indította el ugyanazt az átnevezést, mint az OK"
            assert target.is_dir() and not folder.exists()
            assert str(target) in _folder_paths(controller)
            assert any(photo.folder_path == str(target) for photo in controller.photos.photos)
            _wait_idle(controller, qt_app)
            folder = target
    finally:
        window.resize(window.width(), original_height)
