"""QML-funkcionális teszt: a háttér-beolvasás haladása az albumlistában —
#449.

Az eredeti Picasa nem modális ablakban mutatta a beolvasást, hanem a bal
hasáb albumlistájában („Scanning for faces… %d%% complete") — a felhasználót
közben semmi nem blokkolta. Itt az a tárgy, hogy a sor csak beolvasás
közben látszik, és a százalékot mutatja.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestFaceScanProgressRow:
    def test_it_is_hidden_when_nothing_is_scanning(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        assert _child(window, "faceScanProgressText").property("visible") is False

    def test_it_appears_with_the_percentage_while_scanning(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        pane = _child(window, "folderPane")

        # a vezérlő helyett közvetlenül a hasáb tulajdonságát állítjuk: a
        # kötés (Main.qml → faceScanController.scanPercent) külön, a
        # vezérlő-tesztben van lefedve
        pane.setProperty("peopleCollapsed", False)
        pane.setProperty("faceScanPercent", 42)
        qt_app.processEvents()

        row = _child(window, "faceScanProgressText")
        assert row.property("visible") is True
        assert "42" in row.property("text")

    def test_nothing_modal_blocks_the_user(self, qml_app, qt_app):
        """A haladásnak NINCS saját ablaka — ez a lényege (#449)."""
        window, _controller, _engine = qml_app

        assert window.findChild(QObject, "faceScanProgressDialog") is None
