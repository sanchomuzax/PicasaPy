"""QML-funkcionális teszt: a Visszavonás/Újra gomb felirata a lánc MINDEN
lépését néven nevezi (#465).

A gomb felirata korábban a nézőben, kézzel gondozott `switch`-ből készült,
és csak egy tucat effektet ismert — a többinél a nyers ini-kulcs került ki a
gombra („Visszavonás: crossprocess"). Ez a teszt a KÖTÉST őrzi: a panel
felirata az `EditController.undoLabel`/`redoLabel` kész szövegéből jön.
"""

import pytest
from PySide6.QtCore import QObject


class TestUndoLabelWiring:
    def _open_viewer(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        return viewer

    def _panel(self, window):
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        return panel

    def test_ures_veremnel_a_puszta_felirat(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = self._panel(window)
        edit = engine.rootContext().contextProperty("editController")
        assert edit.property("canUndo") is False
        assert panel.property("undoLabel") == edit.property("undoLabel")
        assert ":" not in panel.property("undoLabel")

    @pytest.mark.parametrize("effect", ["crossprocess", "museummatte", "sepia"])
    def test_a_felirat_megnevezi_a_lepest(self, qml_app, qt_app, effect):
        """Az effekt alkalmazása után a gomb felirata a NEVET mutatja, nem a
        belső kulcsot — a korábban névtelen effektekre is."""
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = self._panel(window)
        edit = engine.rootContext().contextProperty("editController")

        edit.applyEffect(effect)
        qt_app.processEvents()

        label = panel.property("undoLabel")
        assert label == edit.property("undoLabel")
        assert ": " in label, f"nincs lépésnév a feliratban: {label!r}"
        assert effect not in label, (
            f"a nyers ini-kulcs került a gombra: {label!r}"
        )

    def test_visszavonas_utan_az_ujra_gomb_nevezi_meg(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = self._panel(window)
        edit = engine.rootContext().contextProperty("editController")

        edit.applyEffect("nightvision")
        edit.undo()
        qt_app.processEvents()

        redo = panel.property("redoLabel")
        assert redo == edit.property("redoLabel")
        assert ": " in redo and "nightvision" not in redo, redo
