"""#6332: a Snapshot várja meg a kamerát, és a kész JPEG bekerül a könyvtárba."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from PySide6.QtCore import (
    QByteArray,
    QMetaObject,
    QObject,
    QSettings,
    QUrl,
)
from PySide6.QtQml import QQmlComponent

from picasapy.index import open_index
from support.jpeg_factory import make_jpeg
from support.varakozas import var_feltetelre


_FAKE_IMAGE_CAPTURE = """
import QtQml
QtObject {
    property bool readyForCapture: false
    property string errorString: "Camera rejected the request"
    property int requestId: 21
    property int captureCalls: 0
    property string lastPath: ""
    signal imageSaved(int id, string path)
    signal errorOccurred(int id, int error, string errorString)
    function captureToFile(path) {
        ++captureCalls
        lastPath = path
        return requestId
    }
    function completeSave() { imageSaved(requestId, lastPath) }
}
"""


def _obj(window, name: str):
    found = window.findChild(QObject, name)
    assert found is not None, f"{name} nem található a QML-fában"
    return found


def _fake_image_capture(engine, qt_app):
    component = QQmlComponent(engine)
    component.setData(
        QByteArray(_FAKE_IMAGE_CAPTURE.encode("utf-8")),
        QUrl("inmemory:/fake-image-capture.qml"),
    )
    assert var_feltetelre(
        qt_app, lambda: component.status() != QQmlComponent.Status.Loading, 5.0
    ), "a kamera-helyettesítő QML-objektum nem töltődött be"
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    fake = component.create()
    assert fake is not None, component.errorString()
    return component, fake


def _popup_with_fake_camera(qml_app, qt_app, tmp_path, monkeypatch):
    from picasapy.app import camera_capture_controller as camera_module
    from picasapy.app.camera_capture_controller import CameraCaptureController

    window, controller, engine = qml_app
    panel_loader = _obj(window, "captureMoviePanelLoader")
    panel_loader.setProperty("active", True)
    assert var_feltetelre(
        qt_app,
        lambda: window.findChild(QObject, "captureMoviePanelPopup") is not None,
        5.0,
    ), "a kamerafelvevő panel nem jött létre"
    popup = _obj(window, "captureMoviePanelPopup")
    popup.setProperty("visible", False)
    capture_folder = tmp_path / "Rögzített videoklipek"
    monkeypatch.setattr(camera_module, "capture_folder", lambda: capture_folder)
    settings = QSettings(
        str(tmp_path / "camera-settings.ini"), QSettings.Format.IniFormat
    )
    storage = CameraCaptureController(settings, popup)
    popup.setProperty("storage", storage)
    component, fake = _fake_image_capture(engine, qt_app)
    fake.setParent(popup)
    assert popup.setProperty("imageCaptureOverride", fake), (
        "a QML nem fogadja el a kamera helyettesítő objektumát"
    )
    snapshot_flow = _obj(window, "snapshotCaptureRequest")
    return popup, snapshot_flow, component, fake, controller, capture_folder


def _invoke(target, method: str) -> None:
    assert QMetaObject.invokeMethod(target, method), f"nem hívható a QML-függvény: {method}"


def test_a_pillanatkep_varakozik_keszsegre_es_az_idotullepest_kiirja(
    qml_app, qt_app, tmp_path, monkeypatch
):
    (
        popup,
        snapshot_flow,
        _fake_component,
        fake,
        _controller,
        capture_folder,
    ) = _popup_with_fake_camera(qml_app, qt_app, tmp_path, monkeypatch)
    _invoke(popup, "takeSnapshot")
    assert fake.property("captureCalls") == 0
    expected_path = os.path.normpath(str(capture_folder / "snapshot-001.jpg"))
    assert os.path.normpath(snapshot_flow.property("pendingSnapshotPath")) == expected_path

    fake.setProperty("readyForCapture", True)
    assert var_feltetelre(
        qt_app, lambda: fake.property("captureCalls") == 1, 2.0
    ), "a készenlétre váró kérés nem indult el"
    assert fake.property("captureCalls") == 1
    assert os.path.normpath(fake.property("lastPath")) == expected_path
    Path(str(fake.property("lastPath"))).touch()
    _invoke(fake, "completeSave")

    fake.setProperty("readyForCapture", False)
    timer = _obj(qml_app[0], "snapshotReadyTimer")
    assert timer.property("interval") == 5000
    timer.setProperty("interval", 20)
    _invoke(popup, "takeSnapshot")
    timeout_message = "Capture failed"
    assert var_feltetelre(
        qt_app, lambda: popup.property("statusMessage") == timeout_message, 2.0
    ), "az időtúllépés nem jelent meg az állapotsorban"


def test_az_azonnali_capture_hiba_errorstringgel_es_utvonallal_naplozodik(
    qml_app, qt_app, tmp_path, monkeypatch, caplog
):
    import logging

    (
        popup,
        _snapshot_flow,
        _fake_component,
        fake,
        _controller,
        capture_folder,
    ) = _popup_with_fake_camera(qml_app, qt_app, tmp_path, monkeypatch)
    fake.setProperty("readyForCapture", True)
    fake.setProperty("requestId", -1)

    with caplog.at_level(logging.WARNING, logger="picasapy.app.camera_capture_controller"):
        _invoke(popup, "takeSnapshot")

    path = str(capture_folder / "snapshot-001.jpg")
    assert popup.property("statusMessage") == "Camera rejected the request"
    assert "-1" in caplog.text
    assert "Camera rejected the request" in caplog.text
    assert path in caplog.text


def test_a_sikeresen_mentett_kep_azonnal_indexbe_kerul(
    qml_app, qt_app, tmp_path, monkeypatch
):
    (
        popup,
        _snapshot_flow,
        _fake_component,
        fake,
        controller,
        capture_folder,
    ) = _popup_with_fake_camera(qml_app, qt_app, tmp_path, monkeypatch)
    fake.setProperty("readyForCapture", True)
    _invoke(popup, "takeSnapshot")
    path = Path(str(capture_folder / "snapshot-001.jpg"))
    make_jpeg(path, size=(12, 8))
    _invoke(fake, "completeSave")

    def index_contains_snapshot() -> bool:
        try:
            with open_index(controller._db_path) as conn:
                return conn.execute(
                    "SELECT 1 FROM photos WHERE name = ?", (path.name,)
                ).fetchone() is not None
        except sqlite3.OperationalError:
            return False

    assert var_feltetelre(qt_app, index_contains_snapshot, 10.0), (
        "a mentett pillanatkép nem jelent meg az indexben"
    )
    assert popup.property("statusMessage") == "Snapshot saved"
