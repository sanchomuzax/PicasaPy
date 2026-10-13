"""Közös segédek az állapotot író szerkesztőtesztekhez."""

from PySide6.QtCore import QObject


class EditorTestHelpers:
    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def _edit_controller(self, engine):
        return engine.rootContext().contextProperty("editController")
