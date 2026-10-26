"""#5715: a képkocka-folyamat állapotai a QML-ben követik a mentési lépéseket."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtQml import QQmlComponent, QQmlEngine


def test_a_qml_a_rogzites_mentes_es_vegso_allapotokat_osszekoti(qt_app):
    gyoker = Path(__file__).resolve().parents[3]
    qml = (
        gyoker
        / "src/picasapy/app/qml/PicasaPy/PhotoViewerPhotoArea.qml"
    ).read_text(encoding="utf-8")
    controller = (
        gyoker / "src/picasapy/app/frame_capture_controller.py"
    ).read_text(encoding="utf-8")

    qml_allapotok = (
        'function onMovieFrameCapturing() {',
        'qsTr("Capturing frame...")',
        'function onMovieFrameSaving() {',
        'qsTr("Saving to Captured Videos")',
        'function onMovieFrameCaptured(path)',
        'qsTr("Saved %1 to Captured Videos")',
        'function onMovieFrameCaptureFailed()',
        'qsTr("Failed to capture frame")',
    )
    assert all(elem in qml for elem in qml_allapotok)
    assert [qml.index(elem) for elem in qml_allapotok] == sorted(
        qml.index(elem) for elem in qml_allapotok
    )

    capturing = controller.index("self.movieFrameCapturing.emit()")
    worker = controller.index("def munka() -> None:")
    dekodolas = controller.index("dekodolj_kepkockat(video, pozicio)", worker)
    saving = controller.index("self.movieFrameSaving.emit()", worker)
    iras = controller.index(
        "mentsd_a_kepkockat(kocka, capture_folder(), alapnev)", worker
    )
    hatter = controller.index(
        'self._start_background(munka, name="picasapy-capture-frame")'
    )

    assert capturing < hatter
    assert dekodolas < saving < iras

    class _Jelzesek(QObject):
        movieFrameCapturing = Signal()
        movieFrameSaving = Signal()
        movieFrameCaptured = Signal(str)
        movieFrameCaptureFailed = Signal()

    engine = QQmlEngine()
    jelzesek = _Jelzesek()
    engine.rootContext().setContextProperty("controller", jelzesek)
    component = QQmlComponent(engine)
    component.setData(
        b"""
        import QtQuick
        Item {
            id: root
            property alias noticeText: notice.text
            function mutasd(message) { notice.text = message }
            Text { id: notice; objectName: "videoCaptureNotice"; text: "" }
            Connections {
                target: controller
                function onMovieFrameCapturing() {
                    root.mutasd(qsTr("Capturing frame..."))
                }
                function onMovieFrameSaving() {
                    root.mutasd(qsTr("Saving to Captured Videos"))
                }
                function onMovieFrameCaptured(path) {
                    root.mutasd(qsTr("Saved %1 to Captured Videos").arg(
                        path.substring(path.lastIndexOf("/") + 1)))
                }
                function onMovieFrameCaptureFailed() {
                    root.mutasd(qsTr("Failed to capture frame"))
                }
            }
        }
        """,
        QUrl(),
    )
    assert not component.isError(), "a képkocka-jelzés QML-je nem fordul"
    root = component.create()
    assert root is not None, "a képkocka-jelzés QML-je nem épült fel"

    jelzesek.movieFrameCapturing.emit()
    qt_app.processEvents()
    assert root.property("noticeText") == "Capturing frame..."

    jelzesek.movieFrameSaving.emit()
    qt_app.processEvents()
    assert root.property("noticeText") == "Saving to Captured Videos"

    jelzesek.movieFrameCaptured.emit("/tmp/Captured Videos/frame.jpg")
    qt_app.processEvents()
    assert root.property("noticeText") == "Saved frame.jpg to Captured Videos"

    jelzesek.movieFrameCaptureFailed.emit()
    qt_app.processEvents()
    assert root.property("noticeText") == "Failed to capture frame"

    engine.deleteLater()
    qt_app.processEvents()
