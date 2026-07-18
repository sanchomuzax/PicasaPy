"""SearchSuggestions.qml funkcionális tesztjei (#7) — a komponens önállóan
betöltve (a Main.qml-bekötés az integrátoré, ld. CONTRIBUTING.md).

A Repeater-delegátok nem QObject-gyerekek (findChildren nem látja őket),
ezért a vizuális fát (childItems) járjuk be; a visible-kötéshez a komponens
egy QQuickWindow alá kerül."""

import pytest


def _walk_items(item):
    for child in item.childItems():
        yield child
        yield from _walk_items(child)


def _by_object_name(item, name):
    return [ch for ch in _walk_items(item) if ch.objectName() == name]


@pytest.fixture
def component(qt_app):
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from PySide6.QtQuick import QQuickWindow

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    factory = QQmlComponent(
        engine,
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "SearchSuggestions.qml"),
    )
    item = factory.create()
    assert item is not None, factory.errorString()
    window = QQuickWindow()
    item.setParentItem(window.contentItem())
    yield item, qt_app
    item.deleteLater()
    window.deleteLater()
    qt_app.processEvents()


_SUGGESTIONS = [
    {"kind": "folder", "name": "HS logo", "count": 1, "param": "/kepek/HS logo"},
    {"kind": "folder", "name": "Sanoma Media logo", "count": 6,
     "param": "/kepek/Sanoma Media logo"},
    {"kind": "album", "name": "logo valogatas", "count": 3, "param": "aabb01"},
]


class TestSearchSuggestions:
    def test_hidden_without_suggestions(self, component):
        item, _ = component
        assert item.property("visible") is False

    def test_rows_follow_model(self, component):
        item, app = component
        item.setProperty("query", "logo")
        item.setProperty("suggestions", _SUGGESTIONS)
        app.processEvents()
        assert len(_by_object_name(item, "suggestionRow")) == 3
        assert item.property("visible") is True

    def test_match_highlighted_bold_and_count_shown(self, component):
        item, app = component
        item.setProperty("query", "logo")
        item.setProperty("suggestions", _SUGGESTIONS)
        app.processEvents()
        labels = [
            ch.property("text") for ch in _by_object_name(item, "suggestionLabel")
        ]
        assert any("<b>logo</b>" in t for t in labels)
        counts = [
            ch.property("text") for ch in _by_object_name(item, "suggestionCount")
        ]
        assert "(6)" in counts

    def test_highlight_is_case_insensitive(self, component):
        item, _ = component
        assert item.highlighted("HS Logo", "logo") == "HS <b>Logo</b>"

    def test_highlight_escapes_html(self, component):
        item, _ = component
        assert "&lt;" in item.highlighted("a<b", "x")

    def test_choose_emits_signal(self, component):
        item, app = component
        item.setProperty("suggestions", _SUGGESTIONS)
        app.processEvents()
        picked = []
        item.chosen.connect(
            lambda kind, name, param: picked.append((kind, name, param))
        )
        item.choose(2)
        assert picked == [("album", "logo valogatas", "aabb01")]
