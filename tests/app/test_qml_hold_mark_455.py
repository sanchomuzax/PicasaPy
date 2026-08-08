"""QML-teszt: a #455-ös zöld "megtartva" (Hold Selection) jelvény a
ThumbDelegate-en — a `test_qml_geo_mark.py` mintája (#463), bal alsó
sarokban, hogy ne fedje a jobb alsó sarok csillag/geo-pin jelvényeit."""

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


class TestHoldMark:
    def test_hidden_by_default(self, qml_engine):
        delegate = _make_delegate(qml_engine)
        mark = delegate.findChild(QObject, "holdMark")
        assert mark is not None, "holdMark nem található"
        assert mark.property("visible") is False

    def test_visible_when_held(self, qml_engine):
        delegate = _make_delegate(qml_engine, held=True)
        mark = delegate.findChild(QObject, "holdMark")
        assert mark.property("visible") is True

    def test_follows_property_change(self, qml_engine, qt_app):
        delegate = _make_delegate(qml_engine)
        mark = delegate.findChild(QObject, "holdMark")
        delegate.setProperty("held", True)
        qt_app.processEvents()
        assert mark.property("visible") is True

    def test_does_not_conflict_with_star_geo_corner(self, qml_engine):
        """A jelvény a BAL alsó sarokban ül — a csillag/geo (jobb alsó)
        egyidejűleg is látszódhat, nem fedik egymást."""
        delegate = _make_delegate(qml_engine, held=True, star=True, hasGeo=True)
        hold_mark = delegate.findChild(QObject, "holdMark")
        star_geo_row = delegate.findChild(QObject, "thumbCornerBadges")
        assert hold_mark.property("visible") is True
        assert star_geo_row.property("visible") is True
