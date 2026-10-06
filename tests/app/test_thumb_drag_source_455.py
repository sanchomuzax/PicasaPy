"""A rács fogd-és-vidd forrása — #455.

A húzás MÁR KIJELÖLT képről indul; a ki nem jelölt területről továbbra is
lasszó lesz, különben elveszne a rács legfontosabb kijelölő gesztusa.

Önálló komponens-teszt (a `test_qml_edits_mark.py` betöltési mintája): a
GridView/Repeater delegate-jei `findChild`-dal nem érhetők el.
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QTimer, Qt, QUrl
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

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

    def test_selected_file_uris_are_exported_and_mouse_drag_still_starts(
        self, qml_engine, qt_app, tmp_path
    ):
        """A kiválasztott fájlok URL-jei a Qt-húzás MIME-adatai legyenek.

        A pointeres rész valódi QTest lenyomás/mozdítás/felengedés, és
        ellenőrzi, hogy elindul a natív QDrag. Az offscreen környezetben
        időzített egérfelengedés zárja le a húzást külső fogadó nélkül.
        """
        from picasapy.app.tray_controller import TrayMixin

        paths = [tmp_path / "egy kép.jpg", tmp_path / "második#kép.png"]
        uri_list = TrayMixin().fileUriList([str(path) for path in paths])
        expected_uris = [QUrl.fromLocalFile(str(path)).toString() for path in paths]
        assert uri_list.split("\r\n") == expected_uris

        delegate = _make_delegate(
            qml_engine,
            selected=True,
            dragMimeData={"text/uri-list": uri_list},
        )
        proxy = delegate.findChild(QObject, "thumbDragProxy")
        assert proxy is not None
        attached_drag = next(
            child
            for child in proxy.children()
            if child.metaObject().className() == "QQuickDragAttached"
        )
        assert attached_drag.property("mimeData") == {"text/uri-list": uri_list}
        assert attached_drag.property("supportedActions") == (
            Qt.DropAction.CopyAction
            | Qt.DropAction.MoveAction
            | Qt.DropAction.LinkAction
        )

        native_started = []
        attached_drag.dragStarted.connect(lambda: native_started.append(True))
        window = QQuickWindow()
        window.resize(240, 120)
        delegate.setWidth(80)
        delegate.setHeight(80)
        delegate.setParentItem(window.contentItem())
        window.show()
        qt_app.processEvents()
        _KEEPALIVE.append(window)

        for height_delta in (-5, 0, 5):
            window.resize(240, 120 + height_delta)
            qt_app.processEvents()
            center = delegate.mapToScene(delegate.boundingRect().center())
            start = QPoint(round(center.x()), round(center.y()))
            finish = start + QPoint(24, 0)
            QTest.mouseMove(window, start)
            QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
            previous_count = len(native_started)
            # A QDrag saját eseményhurkában engedjük fel a pointert, hogy a
            # natív húzás offscreen módban is determinisztikusan befejeződjön.
            QTimer.singleShot(
                0,
                lambda position=finish: QTest.mouseRelease(
                    window, Qt.MouseButton.LeftButton, pos=position
                ),
            )
            # Lépésenként mozgatunk, ahogy a valódi egér: a húzásfelismerés
            # (startDragDistance) Qt 6.11-en egyetlen nagy ugrásra nem indul el.
            for dx in range(4, 25, 4):
                QTest.mouseMove(window, start + QPoint(dx, 0))
                qt_app.processEvents()
            QTest.mouseMove(window, finish)
            qt_app.processEvents()
            assert len(native_started) == previous_count + 1, (
                "a valódi pointerhúzás nem indította el a QDrag-et"
            )
