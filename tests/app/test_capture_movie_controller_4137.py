"""#4137: a webkamerás állóképek és klipek a Picasa projektmappájába mennek."""

from pathlib import Path

from picasapy.ini import load_document, read_folder_category


def test_capture_fajlnevek_es_a_projekt_ini_az_eredeti_szerint(
    tmp_path, monkeypatch
):
    from picasapy.app import camera_capture_controller as modul
    from picasapy.app.camera_capture_controller import CameraCaptureController

    celmappa = tmp_path / "Rögzített videoklipek"
    monkeypatch.setattr(modul, "capture_folder", lambda: celmappa)
    controller = CameraCaptureController()

    elso = Path(controller.reserveCapturePath("snapshot"))
    assert elso == celmappa / "snapshot-001.jpg"
    assert read_folder_category(load_document(celmappa / ".picasa.ini")) == (
        "Projects (internal)"
    )

    elso.touch()
    masodik = Path(controller.reserveCapturePath("snapshot"))
    assert masodik == celmappa / "snapshot-002.jpg"

    klip = Path(controller.reserveCapturePath("video"))
    assert klip == celmappa / "video-001.mp4"


def test_a_filmszalag_a_celmapa_videoklipjeit_adja_vissza(tmp_path, monkeypatch):
    from picasapy.app import camera_capture_controller as modul
    from picasapy.app.camera_capture_controller import CameraCaptureController

    celmappa = tmp_path / "Rögzített videoklipek"
    celmappa.mkdir()
    for name in ("z-video.mp4", "a-video.avi", "snapshot-001.jpg"):
        (celmappa / name).touch()
    (celmappa / "album").mkdir()
    (celmappa / "album" / "beagyazott.mp4").touch()
    monkeypatch.setattr(modul, "capture_folder", lambda: celmappa)

    controller = CameraCaptureController()
    assert [Path(path).name for path in controller.capturedVideos()] == [
        "a-video.avi",
        "z-video.mp4",
    ]


def test_a_felveteli_meret_es_a_forrasok_beallitasai_tartosak(tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.camera_capture_controller import CameraCaptureController

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    controller = CameraCaptureController(settings)
    controller.setCaptureSize("1280x720")
    controller.setCameraId("kamera-1")
    controller.setAudioId("mikrofon-2")

    ujrainditott = CameraCaptureController(settings)
    assert ujrainditott.captureSize == "1280x720"
    assert ujrainditott.cameraId == "kamera-1"
    assert ujrainditott.audioId == "mikrofon-2"
