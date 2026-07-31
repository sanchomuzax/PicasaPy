"""QML-funkcionális teszt: a bal hasáb Albumok gyűjteménye (#9, 2. lépés).

Az index-réteg (`picasapy.index.albums`) és a vezérlő (`AppController.albums`
/ `showAlbum`) már megvan — ez a teszt azt ellenőrzi, hogy a `FolderPane.qml`
a csillagozott sor ALATT felsorolja az albumokat (a `pane.albumsModel`-en át
kapott név + darabszám elemekhez egy-egy sort rendelve — `albumRepeater`),
hogy a fejléc darabszáma követi őket, és hogy egy album-kattintás (a
`folderChosen` mintáját követő `pane.albumChosen(token)` jelzésen át) a
helyes tokent viszi el a `Main.qml` bekötésén keresztül a
`controller.showAlbum`-ig.

A dinamikusan (Repeater/ListView) létrehozott delegate-példányok nem
`QObject`-gyerekei a szülőjüknek (Qt/PySide sajátosság — a `parentItem`
elválik a `QObject::parent()`-től), ezért `window.findChild`-dal nem
érhetők el egyenként; a hasáb tartalmát ezért a `pane.albumsModel` adatán
és az `albumRepeater.count`-on át ellenőrizzük, ahogy a `folderChosen`
meglévő tesztje (`test_search.py`) is a pane-jelzés közvetlen emittálásával
teszteli a Main.qml-bekötést, nem valódi egérkattintással."""

from __future__ import annotations

from PySide6.QtCore import QObject

from picasapy.index import open_index, sync_tree

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"


def _add_album(lib) -> None:
    """A megosztott `qml_app` fixture (a.jpg, b.jpg) mappájába ír egy
    egyetlen albumot (a.jpg taggal) — utána a hívó szinkronizál."""
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\n"
        f"name=Nyaralás\n"
        f"token={_TOKEN}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN}\n",
        encoding="utf-8",
    )


def _sync_with_album(controller, tmp_path, lib, qt_app) -> None:
    _add_album(lib)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    qt_app.processEvents()


class TestAlbumsListedInPane:
    def test_album_appears_in_panes_model_and_repeater(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        _sync_with_album(controller, tmp_path, lib, qt_app)

        assert {"token": _TOKEN, "name": "Nyaralás", "count": 1} in controller.albums

        pane = window.findChild(QObject, "folderPane")
        assert pane is not None, "folderPane nem található"
        model = pane.property("albumsModel")
        if hasattr(model, "toVariant"):
            model = model.toVariant()
        assert {"token": _TOKEN, "name": "Nyaralás", "count": 1} in model

        repeater = window.findChild(QObject, "albumRepeater")
        assert repeater is not None, "albumRepeater nem található"
        assert repeater.property("count") == 1

    def test_albums_header_count_reflects_album_list(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        header = window.findChild(QObject, "albumsHeader")
        assert header.property("text").endswith("(1)")  # csak a csillagozott sor

        lib = tmp_path / "kepek"
        _sync_with_album(controller, tmp_path, lib, qt_app)

        assert header.property("text").endswith("(2)")  # + 1 album


class TestAlbumClickWiring:
    def test_album_chosen_signal_carries_correct_token_to_controller(
        self, qml_app, qt_app, tmp_path
    ):
        # A Main.qml onAlbumChosen bekötésének ellenőrzése — ugyanaz a
        # minta, mint a folderChosen meglévő tesztjéé
        # (test_search.py: `pane.folderChosen.emit(...)`).
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        _sync_with_album(controller, tmp_path, lib, qt_app)

        pane = window.findChild(QObject, "folderPane")
        assert pane is not None, "folderPane nem található"

        pane.albumChosen.emit(_TOKEN)
        qt_app.processEvents()

        assert controller.currentAlbumToken == _TOKEN
        assert controller.filterActive is True
        assert controller.photos.rowCount() == 1
        assert controller.photos.filePathAt(0).endswith("a.jpg")

    def test_selecting_album_clears_folder_highlight(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        _sync_with_album(controller, tmp_path, lib, qt_app)

        pane = window.findChild(QObject, "folderPane")
        assert pane.property("selectedPath") != ""  # a fixture mappát választ

        pane.albumChosen.emit(_TOKEN)
        qt_app.processEvents()

        assert pane.property("selectedAlbumToken") == _TOKEN
        # a mappa-útvonal a controlleren megmarad (visszaváltáshoz), de a
        # hasáb a mappa-sort album-nézetben már nem emeli ki (FolderPane.qml
        # isSelectedFolder feltétele a selectedAlbumToken-t is nézi)
        assert pane.property("selectedPath") == controller.currentFolder

    def test_clear_filter_after_album_restores_folder_highlight(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        _sync_with_album(controller, tmp_path, lib, qt_app)

        pane = window.findChild(QObject, "folderPane")
        pane.albumChosen.emit(_TOKEN)
        qt_app.processEvents()
        assert pane.property("selectedAlbumToken") == _TOKEN

        controller.clearFilter()
        qt_app.processEvents()
        assert pane.property("selectedAlbumToken") == ""
