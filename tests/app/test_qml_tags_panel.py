"""QML-funkcionális tesztek: Címkék-panel (#12, Ctrl+T).

Két szint: a TagsPanel önálló komponens-viselkedése (inline betöltés, a
test_qml_editor_panel.py mintája), és a Main.qml-be kötött út a közös
qml_app fixture-rel (láthatóság, címke-írás a controlleren át).
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.metadata import read_file_metadata

# a QML-gyökerek élő Python-referencia nélkül a JS-GC prédái lennének
_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


def _tags_of(panel) -> list:
    value = panel.property("tags")
    return list(value) if value is not None else []


class TestTagsPanelComponent:
    def _make_panel(self, qml_engine, has_selection=True):
        return _load(
            qml_engine,
            "import QtQuick\nimport PicasaPy 1.0\n"
            "TagsPanel { hasSelection: %s }\n"
            % ("true" if has_selection else "false"),
        )

    def test_submit_emits_add_and_clears_input(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        added = []
        panel.addRequested.connect(lambda kw: added.append(kw))
        tag_input = panel.findChild(QObject, "tagInput")
        tag_input.setProperty("text", "  balaton  ")
        QMetaObject.invokeMethod(
            panel, "submit", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert added == ["balaton"]  # trimmelve
        assert tag_input.property("text") == ""

    def test_submit_empty_input_no_signal(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        added = []
        panel.addRequested.connect(lambda kw: added.append(kw))
        panel.findChild(QObject, "tagInput").setProperty("text", "   ")
        QMetaObject.invokeMethod(
            panel, "submit", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert added == []

    def test_submit_without_selection_no_signal(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine, has_selection=False)
        added = []
        panel.addRequested.connect(lambda kw: added.append(kw))
        tag_input = panel.findChild(QObject, "tagInput")
        tag_input.setProperty("text", "címke")
        QMetaObject.invokeMethod(
            panel, "submit", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert added == []
        assert tag_input.property("enabled") is False

    def test_tag_list_shows_tags(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        panel.setProperty("tags", ["alma", "körte"])
        qt_app.processEvents()
        tag_list = panel.findChild(QObject, "tagList")
        assert tag_list.property("count") == 2

    def test_close_button_emits_close(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        closed = []
        panel.closeRequested.connect(lambda: closed.append(True))
        panel.closeRequested.emit()
        qt_app.processEvents()
        assert closed == [True]


class TestTagsPanelInMain:
    def _panel(self, window):
        panel = window.findChild(QObject, "tagsPanel")
        assert panel is not None, "tagsPanel nincs a Main.qml-ben"
        return panel

    def test_panel_hidden_by_default_and_toggles(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        panel = self._panel(window)
        assert panel.property("visible") is False
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        assert panel.property("visible") is True

    def test_menu_item_present_and_enabled(self, qml_app):
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "menuViewTags")
        assert item is not None
        assert item.property("enabled") is True

    def test_add_tag_writes_iptc_and_refreshes_panel(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        panel = self._panel(window)
        assert panel.property("hasSelection") is True
        panel.findChild(QObject, "tagInput").setProperty("text", "vitorlás")
        QMetaObject.invokeMethod(
            panel, "submit", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert read_file_metadata(lib / "a.jpg").keywords == ("vitorlás",)
        assert _tags_of(panel) == ["vitorlás"]

    def test_remove_tag_updates_file_and_panel(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        panel = self._panel(window)
        controller.addKeywordToRows([0], "törlendő")
        qt_app.processEvents()
        assert _tags_of(panel) == ["törlendő"]
        panel.removeRequested.emit("törlendő")
        qt_app.processEvents()
        assert read_file_metadata(lib / "a.jpg").keywords == ()
        assert _tags_of(panel) == []

    def test_multi_selection_shows_union(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.addKeywordToRows([0], "zebra")
        controller.addKeywordToRows([1], "alma")
        window.setProperty("tagsPanelOpen", True)
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        panel = self._panel(window)
        assert _tags_of(panel) == ["alma", "zebra"]
