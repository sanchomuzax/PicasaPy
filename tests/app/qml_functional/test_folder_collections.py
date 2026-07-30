"""#320 első lépése: a bal hasáb öt Picasa-hű gyűjtemény-fejléce.

Az audit (docs/specs/ui-audit-mainwindow.md, mappafa szakasz) szerint a bal
hasáb gyökerén öt önálló, csukható gyűjtemény áll egymás alatt (Albumok,
Emberek, Projektek, Mappák, Egyéb), és csak a Mappák gyűjtemény tagolt
évszám-szakaszokra. Ez a teszt a FolderPane.qml öt fejlécét, a
nyitva/csukva állapot perzisztálását és a Mappák-tartalom sértetlenségét
ellenőrzi.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject


class TestFiveCollectionHeaders:
    def test_five_headers_present_in_picasa_order(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        names = (
            "albumsHeader",
            "peopleHeader",
            "projectsHeader",
            "folderPaneHeader",
            "otherHeader",
        )
        headers = [window.findChild(QObject, name) for name in names]
        for name, header in zip(names, headers):
            assert header is not None, f"{name} nem található"

        labels = ("Albums", "People", "Projects", "Folders", "Other")
        for header, label in zip(headers, labels):
            assert label in header.property("text")

    def test_default_collapsed_state_matches_spec(self, qml_app, qt_app):
        # collections.DEFAULT_COLLAPSED: albums+folders nyitva, a többi
        # (tartalom nélküli) csukva.
        window, _controller, _ = qml_app
        expectations = {
            "albumsHeaderRow": False,
            "peopleHeaderRow": True,
            "projectsHeaderRow": True,
            "folderPaneHeaderRow": False,
            "otherHeaderRow": True,
        }
        for row_name, expected_collapsed in expectations.items():
            row = window.findChild(QObject, row_name)
            assert row is not None, f"{row_name} nem található"
            assert row.property("collapsed") is expected_collapsed


class TestCollectionToggle:
    def test_toggle_flips_state_and_persists_via_controller(self, qml_app, qt_app):
        window, controller, _ = qml_app
        row = window.findChild(QObject, "peopleHeaderRow")
        assert row is not None, "peopleHeaderRow nem található"
        assert controller.isCollectionCollapsed("people") is True

        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert row.property("collapsed") is False
        assert controller.isCollectionCollapsed("people") is False

        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert row.property("collapsed") is True
        assert controller.isCollectionCollapsed("people") is True

    def test_toggle_albums_hides_starred_row(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        starred = window.findChild(QObject, "starredItem")
        assert starred is not None, "starredItem nem található"
        assert starred.property("visible") is True

        row = window.findChild(QObject, "albumsHeaderRow")
        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert starred.property("visible") is False

    def test_toggle_folders_hides_folder_list(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        folder_list = window.findChild(QObject, "folderListView")
        assert folder_list is not None, "folderListView nem található"
        assert folder_list.property("visible") is True

        row = window.findChild(QObject, "folderPaneHeaderRow")
        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert folder_list.property("visible") is False


class TestFolderContentUnaffected:
    def test_folder_pane_header_still_reflects_search(self, qml_app, qt_app):
        window, controller, _ = qml_app
        header = window.findChild(QObject, "folderPaneHeader")
        assert header is not None, "folderPaneHeader nem található"
        assert "Folders" in header.property("text")

        controller.search("a")
        qt_app.processEvents()
        assert header.property("text") == 'Search results for "a" (1)'

        controller.search("")
        qt_app.processEvents()
        assert "Folders" in header.property("text")

    def test_empty_collections_show_zero_and_do_not_crash(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        for name in ("peopleHeader", "projectsHeader", "otherHeader"):
            header = window.findChild(QObject, name)
            assert header.property("text").endswith("(0)")
