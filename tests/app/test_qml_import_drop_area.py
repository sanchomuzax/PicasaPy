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
