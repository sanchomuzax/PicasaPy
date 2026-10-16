"""#237: az ImportDropArea komponens — drop → kontroller-híd + visszajelzés.

Önállóan betöltve (a Main.qml gyökerére helyezés az integrátoré). A valódi
asztali drag-and-drop eseményt offscreen nem lehet előállítani, ezért a
DropArea onDropped-ja egy külön submitUrls() függvényre vezet, és a teszt
azt hívja közvetlenül.
"""

import pytest
from PySide6.QtCore import QObject, Signal, Slot


class FakeDropController(QObject):
    dropRejected = Signal(str)

    def __init__(self):
        super().__init__()
        self.received = []

    @Slot(list)
    def importDroppedUrls(self, urls) -> None:
        self.received.append([str(u) for u in urls])


@pytest.fixture
def drop_area(qt_app):
    """Az ImportDropArea.qml önállóan betöltve, fake kontrollerrel."""
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    fake = FakeDropController()
    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("dropImportController", fake)
    factory = QQmlComponent(
        engine,
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "ImportDropArea.qml"),
    )
    item = factory.create()
    assert item is not None, factory.errorString()
    yield item, fake, qt_app
    item.deleteLater()
    qt_app.processEvents()


def _invoke_submit(area, urls) -> None:
    from PySide6.QtCore import QMetaObject, Q_ARG, Qt

    ok = QMetaObject.invokeMethod(
        area,
        "submitUrls",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", urls),
    )
    assert ok, "a submitUrls() nem hívható"


class TestImportDropArea:
    def test_forwards_urls_to_controller(self, drop_area):
        area, fake, qt_app = drop_area
        _invoke_submit(area, ["file:///tmp/a.jpg", "file:///tmp/b.jpg"])
        qt_app.processEvents()
        assert fake.received == [["file:///tmp/a.jpg", "file:///tmp/b.jpg"]]

    def test_feedback_hidden_by_default(self, drop_area):
        area, _fake, _qt_app = drop_area
        toast = area.findChild(QObject, "dropFeedback")
        assert toast is not None, "dropFeedback nem található"
        assert toast.property("visible") is False

    def test_rejection_shows_feedback_text(self, drop_area):
        area, fake, qt_app = drop_area
        fake.dropRejected.emit("A jegyzet.txt nem kép vagy mappa.")
        qt_app.processEvents()
        toast = area.findChild(QObject, "dropFeedback")
        assert toast.property("visible") is True
        assert "jegyzet.txt" in str(toast.property("message"))


class TestMainWiring:
    """A Main.qml-bekötés (integrátori kör): a teljes felületen át egy kép
    ráejtése a kép mappáját a figyelt gyökerek közé teszi."""

    def test_dropped_image_folder_becomes_watched(
        self, qml_app, qt_app, tmp_path
    ):
        from support.jpeg_factory import make_jpeg

        window, controller, _lib, _engine = qml_app
        area = window.findChild(QObject, "importDropArea")
        assert area is not None, "importDropArea nincs a Main.qml-ben"
        extra = tmp_path / "ejtett"
        extra.mkdir()
        make_jpeg(extra / "c.jpg", size=(64, 64))
        _invoke_submit(area, [(extra / "c.jpg").as_uri()])
        qt_app.processEvents()
        assert str(extra) in list(controller.watchedFolders)


_BELSO_HUZAS_QML = b"""
import QtQuick
import QtQuick.Window
import PicasaPy
Window {
    width: 400; height: 300; visible: true
    property int alattaEjtesek: 0
    DropArea {
        objectName: "alattaFekvo"
        anchors.fill: parent
        onDropped: function(drop) { drop.accept(); alattaEjtesek += 1 }
    }
    ImportDropArea { objectName: "importReteg"; anchors.fill: parent; z: 95 }
    Item {
        objectName: "belsoForras"
        x: 10; y: 10; width: 1; height: 1
        readonly property string payload: "photos"
        Drag.dragType: Drag.Internal
        Drag.mimeData: ({ "text/uri-list": "file:///tmp/belso.jpg" })
    }
}
"""


class TestBelsoHuzasNemImport:
    """#5105: a programon belüli húzás (van `source`-a) nem import — az
    ablakot fedő réteg nem nyelheti el, az alatta fekvő cél kapja meg."""

    def test_belso_huzas_az_alatta_fekvo_celhoz_er(self, qt_app):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine
        from PySide6.QtQuick import QQuickItem

        fake = FakeDropController()
        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("dropImportController", fake)
        component = QQmlComponent(engine)
        component.setData(_BELSO_HUZAS_QML, "")
        window = component.create()
        assert window is not None, component.errorString()
        qt_app.processEvents()
        forras = window.findChild(QQuickItem, "belsoForras")
        drag = next(
            child for child in forras.children()
            if child.metaObject().className() == "QQuickDragAttached"
        )
        drag.setProperty("active", True)
        forras.setX(200)
        forras.setY(150)
        qt_app.processEvents()
        assert QMetaObjectInvoke(drag, "drop")
        qt_app.processEvents()
        try:
            assert fake.received == [], "a belső húzás importként futott le"
            assert window.property("alattaEjtesek") == 1, (
                "az ablakot fedő import-réteg elnyelte a belső ledobást"
            )
        finally:
            window.deleteLater()
            qt_app.processEvents()


def QMetaObjectInvoke(obj, name: str) -> bool:
    from PySide6.QtCore import QMetaObject, Qt

    return QMetaObject.invokeMethod(obj, name, Qt.ConnectionType.DirectConnection)
