"""QML-funkcionális teszt: a háttér-beolvasás haladása az albumlistában —
#449.

Az eredeti Picasa nem modális ablakban mutatta a beolvasást, hanem MAGÁN
a „Névtelenek" album tételén: *„While scanning, progress information
appears in the Unnamed album item."* (#26) — a felhasználót közben semmi
nem blokkolta. Itt az a tárgy, hogy a tétel beolvasás közben a százalékot
mutatja, és akkor is látszik, ha még nulla névtelen arc van.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestFaceScanProgressRow:
    def test_it_shows_the_album_name_when_nothing_is_scanning(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        pane = _child(window, "folderPane")
        pane.setProperty("peopleCollapsed", False)
        pane.setProperty("unnamedFaceCount", 3)
        qt_app.processEvents()

        assert "3" in _child(window, "unnamedFacesLabel").property("text")

    def test_it_appears_with_the_percentage_while_scanning(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        pane = _child(window, "folderPane")

        # a vezérlő helyett közvetlenül a hasáb tulajdonságát állítjuk: a
        # kötés (Main.qml → faceScanController.scanPercent) külön, a
        # vezérlő-tesztben van lefedve
        pane.setProperty("peopleCollapsed", False)
        pane.setProperty("faceScanPercent", 42)
        qt_app.processEvents()

        row = _child(window, "unnamedFacesLabel")
        assert row.property("visible") is True
        assert "42" in row.property("text")

    def test_the_row_appears_even_before_the_first_face_is_found(
        self, qml_app, qt_app
    ):
        """Az első beolvasáskor még NULLA névtelen arc van — a haladásnak
        akkor is látszania kell."""
        window, _controller, _engine = qml_app
        pane = _child(window, "folderPane")
        pane.setProperty("peopleCollapsed", False)
        pane.setProperty("unnamedFaceCount", 0)
        pane.setProperty("faceScanPercent", 7)
        qt_app.processEvents()

        assert _child(window, "unnamedFacesItem").property("visible") is True

    def test_nothing_modal_blocks_the_user(self, qml_app, qt_app):
        """A haladásnak NINCS saját ablaka — ez a lényege (#449)."""
        window, _controller, _engine = qml_app

        assert window.findChild(QObject, "faceScanProgressDialog") is None
