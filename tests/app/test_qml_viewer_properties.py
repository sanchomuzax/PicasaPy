"""#192: a Tulajdonságok-panel a nagy (egyképes) nézőben is látszik.

A panel a könyvtár-nézet közös kapcsolóját (window.propertiesPanelOpen)
követi — ha be van kapcsolva, a nézőben is megjelenik jobb oldalt, és a
nézett kép adatait mutatja.
"""

from PySide6.QtCore import QObject


def _panel(window):
    panel = window.findChild(QObject, "viewerPropertiesPanel")
    assert panel is not None, "viewerPropertiesPanel nincs a PhotoViewer-ben"
    return panel


def _entries(panel) -> dict:
    value = panel.property("entries")
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return {e["label"]: e["value"] for e in (value or [])}


def _open_viewer(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


class TestViewerPropertiesPanel:
    def test_hidden_by_default(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        assert _panel(window).property("visible") is False

    def test_follows_library_toggle(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        window.setProperty("propertiesPanelOpen", True)
        qt_app.processEvents()
        panel = _panel(window)
        assert panel.property("visible") is True
        assert panel.property("hasSelection") is True
        assert _entries(panel).get("File name") == "a.jpg"

    def test_entries_follow_navigation(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        window.setProperty("propertiesPanelOpen", True)
        qt_app.processEvents()
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        assert _entries(_panel(window)).get("File name") == "b.jpg"

    def test_close_clears_shared_state(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        window.setProperty("propertiesPanelOpen", True)
        qt_app.processEvents()
        panel = _panel(window)
        panel.closeRequested.emit()
        qt_app.processEvents()
        assert window.property("propertiesPanelOpen") is False
        assert panel.property("visible") is False
