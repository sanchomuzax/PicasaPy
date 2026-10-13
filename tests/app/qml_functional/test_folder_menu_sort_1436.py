"""#1436: a „Mappa rendezésének alapja ▸" VALÓDI menütételére kattintva a
mappa TARTALMA rendeződik át — nem a mappák sorrendje.

A vezérlő-szintű őr (`tests/app/test_folder_photo_sort_1436.py`) a
viselkedést méri; ez itt a KÖTÉST: hogy a menütétel tényleg az új
vezérlőparancshoz vezet. A tételt a `triggered` jelzésén át indítjuk, nem a
Python-metódus közvetlen hívásával — pontosan azért, hogy egy elrontott
kötés ne maradhasson zölden.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from picasapy.ini.document import parse_document
from picasapy.ini.priority import olvasd_a_prioritasokat


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open_menu(window, path):
    QMetaObject.invokeMethod(
        window, "openFolderContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", path),
    )


def _trigger(window, name):
    # a MenuItem-nek nincs hívható `trigger()`-e — a `triggered` SIGNAL
    # kibocsátása a kattintás megfelelője
    QMetaObject.invokeMethod(
        _child(window, name), "triggered", Qt.ConnectionType.DirectConnection
    )


class TestSortMenuItemsAreWiredToTheFolderContents:
    def test_date_item_saves_only_the_target_folders_order(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        path = controller.currentFolder
        assert path
        folders_before = controller.folderSort
        _open_menu(window, path)
        qt_app.processEvents()
        _trigger(window, "folderMenuSortByDate")
        qt_app.processEvents()
        ini = Path(path) / ".picasa.ini"
        priorities = olvasd_a_prioritasokat(
            parse_document(ini.read_text(encoding="utf-8"))
        )
        target_names = {
            photo.name
            for photo in controller.photos.photos
            if photo.folder_path == path
        }
        assert set(priorities) == target_names
        assert controller.folderSort == folders_before

    def test_size_item_saves_a_complete_order(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        path = controller.currentFolder
        assert path
        _open_menu(window, path)
        qt_app.processEvents()
        _trigger(window, "folderMenuSortBySize")
        qt_app.processEvents()
        priorities = olvasd_a_prioritasokat(
            parse_document((Path(path) / ".picasa.ini").read_text(encoding="utf-8"))
        )
        assert sorted(priorities.values()) == list(
            map(float, range(1, len(priorities) + 1))
        )

    def test_reverse_item_saves_the_reversed_order(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        path = controller.currentFolder
        assert path
        before = [
            photo.name
            for photo in controller.photos.photos
            if photo.folder_path == path
        ]
        reverse_before = controller.folderSortReverse
        _open_menu(window, path)
        qt_app.processEvents()
        _trigger(window, "folderMenuSortReverse")
        qt_app.processEvents()
        priorities = olvasd_a_prioritasokat(
            parse_document((Path(path) / ".picasa.ini").read_text(encoding="utf-8"))
        )
        assert [
            name for name, _place in sorted(priorities.items(), key=lambda pair: pair[1])
        ] == before[::-1]
        assert controller.folderSortReverse == reverse_before
