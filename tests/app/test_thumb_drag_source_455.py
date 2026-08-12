"""A rács fogd-és-vidd forrása — #455.

A húzás MÁR KIJELÖLT képről indul; a ki nem jelölt területről továbbra is
lasszó lesz, különben elveszne a rács legfontosabb kijelölő gesztusa.

Önálló komponens-teszt (a `test_qml_edits_mark.py` betöltési mintája): a
GridView/Repeater delegate-jei `findChild`-dal nem érhetők el.
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
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
        "index": 3,
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
    _KEEPALIVE.extend((comp, delegate))
    return delegate


def _begin(delegate):
    QMetaObject.invokeMethod(
        delegate, "beginPhotoDrag", Qt.ConnectionType.DirectConnection
    )


class TestDragSource:
    def test_an_unselected_photo_does_not_start_a_drag(self, qml_engine):
        delegate = _make_delegate(qml_engine, selected=False)
        started = []
        delegate.photoDragStarted.connect(started.append)

        _begin(delegate)

        assert started == []

    def test_a_selected_photo_starts_a_drag_with_its_index(self, qml_engine):
        delegate = _make_delegate(qml_engine, selected=True)
        started = []
        delegate.photoDragStarted.connect(started.append)

        _begin(delegate)

        assert started == [3]

    def test_the_payload_says_it_is_photos(self, qml_engine):
        """A bal hasáb CSAK saját fotó-húzást fogad el — a külső fájlok
        ejtése az importálásé (#146), azt nem szabad elorozni."""
        delegate = _make_delegate(qml_engine, selected=True)

        proxy = delegate.findChild(QObject, "thumbDragProxy")

        assert proxy is not None
        assert proxy.property("payload") == "photos"
