"""QML-funkcionális teszt: a mentés-műveletek párbeszédei — #444.

A Fájl menü „Mentés / Visszaállítás / Utolsó mentés visszavonása" pontjai
eddig helyfoglalók voltak. Itt az a tárgy, hogy a menü tényleg megnyitja a
megfelelő megerősítést, és hogy a **nem renderelhető láncelem** külön,
hangsúlyos kérdést kap a mentés előtt (#484).
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open(window, qt_app, method, rows):
    QMetaObject.invokeMethod(
        _child(window, "saveDialogs"), method,
        Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", rows),
    )
    qt_app.processEvents()


class TestSaveDialogs:
    def test_save_asks_first(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        _open(window, qt_app, "openSave", [0])

        assert _child(window, "saveConfirmDialog").property("visible") is True

    def test_the_empty_selection_opens_nothing(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        _open(window, qt_app, "openSave", [])

        assert _child(window, "saveConfirmDialog").property("visible") is False

    def test_revert_and_undo_save_have_their_own_dialogs(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        _open(window, qt_app, "openRevert", [0])
        assert _child(window, "revertConfirmDialog").property("visible") is True
        QMetaObject.invokeMethod(
            _child(window, "revertConfirmDialog"), "close",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        _open(window, qt_app, "openUndoSave", [0])
        assert _child(window, "undoSaveConfirmDialog").property("visible") is True

    def test_an_unrenderable_filter_gets_the_stronger_warning(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        from pathlib import Path

        from picasapy.index import open_index, sync_tree

        first = controller.photos.filePathAt(0)
        folder = Path(first).parent
        name = Path(first).name
        (folder / ".picasa.ini").write_text(
            f"[{name}]\nfilters=gamma=1,0.5;\n", encoding="utf-8"
        )
        # az indexbe a `sync_tree` viszi be az ini tartalmát; az adatbázis a
        # könyvtár mellett, a fixture tmp_path-jában él
        with open_index(folder.parent / "index.db") as conn:
            sync_tree(conn, folder)
        controller.selectFolder(str(folder))
        qt_app.processEvents()

        _open(window, qt_app, "openSave", [0])

        # a szokásos kérdés HELYETT a hangsúlyos figyelmeztetés jön
        assert _child(window, "saveConfirmDialog").property("visible") is False
        warning = _child(window, "unrenderableFiltersDialog")
        assert warning.property("visible") is True
        assert "gamma" in warning.property("names")


class TestMenuWiring:
    def test_the_restore_items_need_a_backup(self, qml_app, qt_app):
        """A Visszaállítás és az Utolsó mentés visszavonása csak akkor
        engedélyezett, ha a képnek van már biztonsági másolata."""
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        assert _child(window, "menuFileRevert").property("enabled") is False
        assert _child(window, "menuFileUndoSave").property("enabled") is False
