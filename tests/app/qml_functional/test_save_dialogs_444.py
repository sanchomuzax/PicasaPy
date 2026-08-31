"""QML-funkcionális teszt: a mentés-műveletek párbeszédei — #444.

A Fájl menü „Mentés / Visszaállítás / Utolsó mentés visszavonása" pontjai
eddig helyfoglalók voltak. Itt az a tárgy, hogy a menü tényleg megnyitja a
megfelelő megerősítést, és hogy a **nem renderelhető láncelem** külön,
hangsúlyos kérdést kap a mentés előtt (#484).
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from support.halasztott_parbeszed import nyisd_meg


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open(window, qt_app, method, rows):
    # #1720: a mentés-párbeszédek HALASZTOTTAK — a Fájl ▸ Mentés
    # menüponttal (valódi út) építtetjük fel a köteget, és csak utána
    # hívjuk a konkrét sorokkal.
    nyisd_meg(window, "saveDialogs")
    qt_app.processEvents()
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

        # #1791: az „Undo Save" külön párbeszéde MEGSZŰNT — az eredetiben
        # ez a Visszaállítás párbeszéd GOMBJA, nem önálló megerősítés.
        # A gombot a `test_undosave_a_parbeszedben_1791.py` méri.
        _open(window, qt_app, "openRevert", [0])
        assert _child(window, "revertUndoSaveButton") is not None

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
            f"[{name}]\nfilters=rainbow=1,0.5;\n", encoding="utf-8"
        )
        # az indexbe a `sync_tree` viszi be az ini tartalmát; az adatbázis a
        # könyvtár mellett, a fixture tmp_path-jában él
        with open_index(folder.parent / "index.db") as conn:
            sync_tree(conn, folder)
        controller.selectFolder(str(folder))
        qt_app.processEvents()

        _open(window, qt_app, "openSave", [0])

        # a szokásos kérdés HELYETT a hangsúlyos figyelmeztetés jön
        # (#687: korábban `gamma` volt a példa — az azóta renderelhető)
        assert _child(window, "saveConfirmDialog").property("visible") is False
        warning = _child(window, "unrenderableFiltersDialog")
        assert warning.property("visible") is True
        assert "rainbow" in warning.property("names")


class TestMenuWiring:
    def test_the_restore_items_need_a_backup(self, qml_app, qt_app):
        """A Visszaállítás csak akkor engedélyezett, ha a képnek van már
        biztonsági másolata.

        #1791: az „Utolsó mentés visszavonása" MÁR NEM menütétel — az
        eredetiben a Visszaállítás párbeszéd gombja. Ezért itt csak a
        Visszaállítás marad."""
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        assert _child(window, "menuFileRevert").property("enabled") is False
        assert window.findChild(QObject, "menuFileUndoSave") is None
