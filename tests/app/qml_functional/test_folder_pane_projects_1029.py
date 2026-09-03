"""QML-funkcionális teszt: a bal hasáb **Projektek** gyűjteménye (#1029).

A jegy panasza az volt, hogy a Projektek gyűjtemény alatt a felhasználó
SEMMIT nem lát — ezért ez a teszt nem azt állítja, hogy „beolvastuk a
kulcsot", hanem hogy a `P2category=Projects (internal)` mappa KIRAJZOLT
sort kap a hasábon (`projectFolderRepeater`), a fejléc darabszáma követi,
és a sorra kattintva a mappa meg is nyílik (`Main.qml` bekötés).

A dinamikus delegate-példányok `findChild`-dal nem érhetők el (MEMORY
2026-07-31), ezért — a `test_folder_pane_albums.py` mintájára — a Repeater
`count`-ján és a szekció jelzésének közvetlen emittálásán át mérünk.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem

from picasapy.index import open_index, sync_tree

_PROJECTS = "[Picasa]\nP2category=Projects (internal)\n"


def _repeater_item(root, repeater_name, index):
    """A `Repeater` index. delegate-példánya — a `findChild` nem látja
    (MEMORY 2026-07-31), a `test_left_pane_757.py` segédjének mintája."""
    repeater = root.findChild(QObject, repeater_name)
    assert repeater is not None, f"{repeater_name} nem található"
    item = QMetaObject.invokeMethod(
        repeater,
        "itemAt",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(QQuickItem),
        Q_ARG(int, index),
    )
    assert item is not None, f"{repeater_name}[{index}] nem jött létre"
    return item


def _add_project_folder(lib, name="Kollázsok"):
    """A megosztott `qml_app` könyvtárába egy Picasa-projektmappa."""
    folder = lib / name
    folder.mkdir()
    (folder / "kollazs.jpg").write_bytes(b"x" * 10)
    (folder / ".picasa.ini").write_text(_PROJECTS, encoding="utf-8")
    return folder


def _sync(controller, tmp_path, lib, qt_app):
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    qt_app.processEvents()


class TestProjectFoldersVisibleInPane:
    def test_project_folder_gets_a_row_in_the_pane(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        folder = _add_project_folder(lib)
        _sync(controller, tmp_path, lib, qt_app)

        pane = window.findChild(QObject, "folderPane")
        assert pane is not None, "folderPane nem található"
        model = pane.property("projectFolders")
        if hasattr(model, "toVariant"):
            model = model.toVariant()
        assert [row["name"] for row in model] == ["Kollázsok"]
        assert model[0]["path"] == str(folder)

        repeater = window.findChild(QObject, "projectFolderRepeater")
        assert repeater is not None, "projectFolderRepeater nem található"
        assert repeater.property("count") == 1

    def test_projects_header_counts_the_folders(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        header = window.findChild(QObject, "projectsHeader")
        assert header is not None, "projectsHeader nem található"
        assert header.property("text").endswith("(0)")

        lib = tmp_path / "kepek"
        _add_project_folder(lib)
        _sync(controller, tmp_path, lib, qt_app)

        assert header.property("text").endswith("(1)")

    def test_projects_collection_is_open_by_default(
        self, qml_app, qt_app, tmp_path
    ):
        """⚠️ A gyűjtemény NYITVA indul (#1029) — csukott alapállapottal a
        felhasználó a javítás után is üresnek látná a Projekteket, amíg rá
        nem kattint a fejlécre."""
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        _add_project_folder(lib)
        _sync(controller, tmp_path, lib, qt_app)

        pane = window.findChild(QObject, "folderPane")
        section = window.findChild(QObject, "projectsSection")
        assert section is not None, "projectsSection nem található"

        assert pane.property("projectsCollapsed") is False
        assert section.property("collapsed") is False
        item = _repeater_item(window, "projectFolderRepeater", 0)
        assert item.property("visible") is True, (
            "a projekt-mappa sora nem látszik a hasábon"
        )


class TestProjectFolderClickWiring:
    def test_clicking_a_project_folder_opens_it(self, qml_app, qt_app, tmp_path):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        folder = _add_project_folder(lib)
        _sync(controller, tmp_path, lib, qt_app)

        section = window.findChild(QObject, "projectsSection")
        assert section is not None, "projectsSection nem található"
        section.folderChosen.emit(str(folder))
        qt_app.processEvents()

        assert controller.currentFolder == str(folder)


class TestFoldersViewIsNotBroken:
    """⚠️ A legvalószínűbb regresszió: a Mappák gyűjtemény listája ne
    veszítsen sort attól, hogy a Projektek megtelt.

    #2031: a projekt-mappa **szándékosan** kimarad innen (a #1033
    verdiktje), a többi mappa viszont nem tűnhet el."""

    def test_folder_list_still_shows_every_folder(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        _add_project_folder(lib)
        (lib / "nyaralas").mkdir()
        (lib / "nyaralas" / "IMG_0001.jpg").write_bytes(b"x" * 10)
        (lib / "nyaralas" / ".picasa.ini").write_text(
            "[Picasa]\nP2category=Folders on Disk\n", encoding="utf-8"
        )
        _sync(controller, tmp_path, lib, qt_app)

        folder_list = window.findChild(QObject, "folderListView")
        assert folder_list is not None, "folderListView nem található"
        model = folder_list.property("model")
        # a gyökér + a `nyaralas` — a projekt-mappa a Projektek alá került (#2031)
        assert model.property("folderCount") == 2
        assert str(lib / "nyaralas") in controller.folders.folder_paths()
