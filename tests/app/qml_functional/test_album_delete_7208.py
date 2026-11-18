"""#7208: az üres album Delete-re törlődik, jóváhagyott törlés után könyvtár látszik.

1. A megnyitott, tag nélküli album a Delete billentyűre megerősítés nélkül
   törlődik, utána a bal hasáb következő albuma lesz az aktív és megnyitott.
2. A képeket tartalmazó albumnál a Delete kijelölés nélkül semmit nem csinál.
3. Az Album ▸ Delete... jóváhagyása után, ha a törölt album volt megnyitva, a bal
   hasábban semmi nincs kijelölve, és a rács a könyvtár elejét mutatja.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.support.varakozas import var_feltetelre

_TOKEN_1 = "72080000000000000000000000000001"
_TOKEN_2 = "72080000000000000000000000000002"


def _wait(qt_app, condition, label: str, timeout: float = 10.0) -> None:
    assert var_feltetelre(qt_app, condition, timeout), (
        f"határidőn belül nem teljesült: {label}"
    )


def _child(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"a(z) {name} nem található"
    return item


def _click(window, qt_app, item) -> None:
    assert item is not None and item.width() > 0 and item.height() > 0
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _press_delete(window, qt_app) -> None:
    QTest.keyClick(window, Qt.Key.Key_Delete)
    qt_app.processEvents()


def _open_delete_item(window, qt_app):
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a menüsáv nem található"
    album_view = bool(menu_bar.property("currentAlbumToken"))
    titles = {"&Album"} if album_view else {"F&older", "&Folder", "&Mappa"}
    menu = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if item.property("title") in titles
        ),
        None,
    )
    assert menu is not None, "a Mappa/Album menü nem található"
    header = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if "MenuBarItem" in item.metaObject().className()
            and item.property("text") in titles
        ),
        None,
    )
    assert header is not None, "a Mappa/Album menü fejléce nem található"
    if menu.property("opened") is not True:
        _click(window, qt_app, header)
    _wait(
        qt_app,
        lambda: menu.property("opened") is True,
        "a Mappa/Album menü megnyitása",
    )
    item = _child(window, "menuFolderDelete")
    _wait(qt_app, lambda: item.property("visible") is True, "a Delete... tétel")
    return item


def _setup_library(lib: Path, tmp_path, controller, qt_app) -> None:
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN_1}]\n"
        "name=Elso Album\n"
        f"token={_TOKEN_1}\n"
        f"[.album:{_TOKEN_2}]\n"
        "name=Masodik Album\n"
        f"token={_TOKEN_2}\n"
        "[a.jpg]\n"
        f"albums={_TOKEN_2}\n"
        "[b.jpg]\n"
        f"albums={_TOKEN_2}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    qt_app.processEvents()


def test_ures_album_delete_billentyure_megerosites_nelkul_torlodik_es_kovetkezo_lesz_aktiv(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    _setup_library(library, tmp_path, controller, qt_app)

    # Az első album üres, a másodikban 2 kép van
    assert any(a["token"] == _TOKEN_1 and a["count"] == 0 for a in controller.albums)
    assert any(a["token"] == _TOKEN_2 and a["count"] == 2 for a in controller.albums)

    # Megnyitjuk az üres első albumot
    controller.showAlbum(_TOKEN_1)
    _wait(
        qt_app,
        lambda: controller.currentAlbumToken == _TOKEN_1,
        "az üres album megnyitása",
    )
    window.clearSelection()
    qt_app.processEvents()

    # Lenyomjuk a Delete billentyűt
    _press_delete(window, qt_app)

    # Az üres album eltűnt a bal hasábból
    _wait(
        qt_app,
        lambda: not any(a["token"] == _TOKEN_1 for a in controller.albums),
        "az üres album törlése a modellből",
    )

    # Megerősítő ablak nem nyílt meg
    dialog = window.findChild(QObject, "deleteAlbumDialog")
    assert dialog is None or dialog.property("visible") is False

    # A bal hasáb következő albuma (_TOKEN_2) lett az aktív és megnyitott
    _wait(
        qt_app,
        lambda: controller.currentAlbumToken == _TOKEN_2,
        "a következő album aktiválása",
    )
    assert controller.currentAlbumToken == _TOKEN_2
    folder_pane = _child(window, "folderPane")
    assert folder_pane.property("selectedAlbumToken") == _TOKEN_2


def test_ket_kepes_album_kijeloles_nelkul_delete_semmit_nem_valtoztat(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    _setup_library(library, tmp_path, controller, qt_app)

    # A második album megnyitása (ebben 2 kép van)
    controller.showAlbum(_TOKEN_2)
    _wait(
        qt_app,
        lambda: controller.currentAlbumToken == _TOKEN_2,
        "a két képes album megnyitása",
    )
    window.clearSelection()
    qt_app.processEvents()

    ini_elotte = (library / ".picasa.ini").read_text(encoding="utf-8")

    # Kijelölés nélkül lenyomjuk a Delete billentyűt
    _press_delete(window, qt_app)

    # Semmi nem változik: az album megvan, az ini azonos, a nézet változatlan
    assert any(a["token"] == _TOKEN_2 for a in controller.albums)
    assert controller.currentAlbumToken == _TOKEN_2
    assert (library / ".picasa.ini").read_text(encoding="utf-8") == ini_elotte

    dialog = window.findChild(QObject, "deleteAlbumDialog")
    assert dialog is None or dialog.property("visible") is False


def test_album_delete_menu_jovahagyas_utan_konyvtar_latszik_kijeloles_nelkul(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    _setup_library(library, tmp_path, controller, qt_app)

    controller.showAlbum(_TOKEN_2)
    _wait(
        qt_app,
        lambda: controller.currentAlbumToken == _TOKEN_2,
        "az album megnyitása",
    )

    original_height = int(window.height())
    for offset in (-5, 0, 5):
        target_height = original_height + offset
        window.setHeight(target_height)
        _wait(
            qt_app,
            lambda target_height=target_height: window.height() == target_height,
            f"ablakmagasság {offset:+} px",
        )
        delete_item = _open_delete_item(window, qt_app)
        assert delete_item.property("enabled") is True
        _click(window, qt_app, delete_item)

        dialog = _child(window, "deleteAlbumDialog")
        _wait(
            qt_app,
            lambda dialog=dialog: dialog.property("visible") is True,
            "Delete Album megerősítő ablak",
        )

        if offset != 5:
            # Nem az utolsó kör: elutasítjuk a No gombbal, hogy kipróbáljuk a következő magasságot is
            _click(window, qt_app, _child(window, "deleteAlbumNoButton"))
            _wait(
                qt_app,
                lambda dialog=dialog: dialog.property("visible") is False,
                "No elutasítás",
            )
            assert any(a["token"] == _TOKEN_2 for a in controller.albums)

    # Jóváhagyjuk a törlést
    yes_button = _child(window, "deleteAlbumYesButton")
    _click(window, qt_app, yes_button)

    _wait(
        qt_app,
        lambda: not any(a["token"] == _TOKEN_2 for a in controller.albums),
        "az album eltávolítása a modellből",
    )

    # Bal hasábban semmi sincs kijelölve
    folder_pane = _child(window, "folderPane")
    _wait(
        qt_app,
        lambda: folder_pane.property("selectedAlbumToken") == ""
        and folder_pane.property("selectedPath") == ""
        and folder_pane.property("selectedPersonName") == "",
        "bal hasábban nincs kijelölés",
    )
    assert controller.currentAlbumToken == ""
    assert controller.currentFolder == ""

    # A rács a könyvtár elejét mutatja (viewMode == folder, képek látszanak, nem üres albumnézet)
    assert controller.viewModeName == "folder"
    assert controller.photos.rowCount() == 2
