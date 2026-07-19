"""QML-teszt: a #100-as kék „visszahajtás" jelölő a ThumbDelegate-en.

Önálló komponens-teszt (a test_qml_context_menu.py betöltési mintája):
a jelölő csak hasEdits=true esetén látszik, és a színe a Theme.infoBar —
szándékosan nem a kijelölés azúrja."""

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _make_delegate(qml_engine, **overrides):
    import picasapy.app.application as app_module

    properties = {
        "name": "a.jpg",
        "thumbUrl": "image://thumbs/1",
        "star": False,
        "caption": "",
        "isVideo": False,
        "index": 0,
        "keywords": "",
        "resolution": "320x160",
    }
    properties.update(overrides)
    comp = QQmlComponent(
        qml_engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
        ),
    )
    delegate = comp.createWithInitialProperties(properties)
    assert comp.errors() == [], [e.toString() for e in comp.errors()]
    assert delegate is not None
    QQmlEngine.setObjectOwnership(delegate, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(comp)
    _KEEPALIVE.append(delegate)
    return delegate


class TestEditsFoldMark:
    def test_hidden_by_default(self, qml_engine):
        delegate = _make_delegate(qml_engine)
        mark = delegate.findChild(QObject, "editsFoldMark")
        assert mark is not None, "editsFoldMark nem található"
        assert mark.property("visible") is False

    def test_visible_when_has_edits(self, qml_engine):
        delegate = _make_delegate(qml_engine, hasEdits=True)
        mark = delegate.findChild(QObject, "editsFoldMark")
        assert mark.property("visible") is True

    def test_color_is_info_bar_blue_not_selection_azure(self, qml_engine):
        # #100: a jelölő kékje a Theme.infoBar (#568fb7) — NEM a kijelölés
        # thumbSelection-azúrja (#009eff), a két jelentés nem mosódhat össze
        delegate = _make_delegate(qml_engine, hasEdits=True)
        mark = delegate.findChild(QObject, "editsFoldMark")
        fold = mark.findChildren(QObject)
        colors = {
            child.property("color").name()
            for child in fold
            if child.property("color") is not None
        }
        assert "#568fb7" in colors
        assert "#009eff" not in colors

    def test_follows_property_change(self, qml_engine, qt_app):
        delegate = _make_delegate(qml_engine)
        mark = delegate.findChild(QObject, "editsFoldMark")
        delegate.setProperty("hasEdits", True)
        qt_app.processEvents()
        assert mark.property("visible") is True
