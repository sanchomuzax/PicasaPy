"""#1436: a „Mappa rendezésének alapja ▸" VALÓDI menütételére kattintva a
mappa TARTALMA rendeződik át — nem a mappák sorrendje.

A vezérlő-szintű őr (`tests/app/test_folder_photo_sort_1436.py`) a
viselkedést méri; ez itt a KÖTÉST: hogy a menütétel tényleg az új
vezérlőparancshoz vezet. A tételt a `triggered` jelzésén át indítjuk, nem a
Python-metódus közvetlen hívásával — pontosan azért, hogy egy elrontott
kötés ne maradhasson zölden.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open_menu(window):
    QMetaObject.invokeMethod(
        window, "openFolderContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", ""),
    )


def _trigger(window, name):
    # a MenuItem-nek nincs hívható `trigger()`-e — a `triggered` SIGNAL
    # kibocsátása a kattintás megfelelője
    QMetaObject.invokeMethod(
        _child(window, name), "triggered", Qt.ConnectionType.DirectConnection
    )


class TestSortMenuItemsAreWiredToTheFolderContents:
    def test_date_item_sets_the_photo_order(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        folders_before = controller.folderSort
        _open_menu(window)
        qt_app.processEvents()
        _trigger(window, "folderMenuSortByDate")
        qt_app.processEvents()
        # a KÉPEK rendezése váltott…
        assert controller.folderPhotoSort == "date"
        # …a MAPPÁK sorrendje viszont érintetlen
        assert controller.folderSort == folders_before

    def test_size_item_sets_the_photo_order(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _open_menu(window)
        qt_app.processEvents()
        _trigger(window, "folderMenuSortBySize")
        qt_app.processEvents()
        assert controller.folderPhotoSort == "size"

    def test_reverse_item_flips_the_photo_order(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        before = controller.folderPhotoSortReverse
        reverse_before = controller.folderSortReverse
        _open_menu(window)
        qt_app.processEvents()
        _trigger(window, "folderMenuSortReverse")
        qt_app.processEvents()
        assert controller.folderPhotoSortReverse is not before
        assert controller.folderSortReverse == reverse_before
