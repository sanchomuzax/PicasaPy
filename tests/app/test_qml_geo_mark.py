"""QML-teszt: a #463-as piros geo-pin jelvény a ThumbDelegate-en.

A design-guide.md szerint ("Geo-címkés képen piros pin jelvény a jobb alsó
sarokban") — a meglévő geo-pin.svg ikont használjuk (MainToolbar
geo-szűrője), csak akkor látszik, ha hasGeo=true."""

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


class TestGeoMark:
    def test_hidden_by_default(self, qml_engine):
        delegate = _make_delegate(qml_engine)
        mark = delegate.findChild(QObject, "geoMark")
        assert mark is not None, "geoMark nem található"
        assert mark.property("visible") is False

    def test_visible_when_has_geo(self, qml_engine):
        delegate = _make_delegate(qml_engine, hasGeo=True)
        mark = delegate.findChild(QObject, "geoMark")
        assert mark.property("visible") is True

    def test_follows_property_change(self, qml_engine, qt_app):
        delegate = _make_delegate(qml_engine)
        mark = delegate.findChild(QObject, "geoMark")
        delegate.setProperty("hasGeo", True)
        qt_app.processEvents()
        assert mark.property("visible") is True
