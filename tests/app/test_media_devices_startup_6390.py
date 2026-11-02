"""#6390: Qt multimédia-eszközök maradjanak elérhetők a korai Qt-indítás után."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_a_qt_plugin_naplojabol_kiveszi_a_hatter_nevet():
    from picasapy.app.startup_diagnostics import _multimedia_backend_name

    assert _multimedia_backend_name(
        ['Available backends QList("ffmpeg")', 'Loading media backend "ffmpeg"']
    ) == "ffmpeg"
    assert (
        _multimedia_backend_name(['Loading media backend "windows"']) == "windows"
    )


def test_a_diagnosztika_darabszamot_ir_es_nem_eszkoz_neveket():
    from picasapy.app.startup_diagnostics import (
        _MultimediaDeviceSnapshot,
        _multimedia_device_summary,
    )

    summary = _multimedia_device_summary(
        _MultimediaDeviceSnapshot(2, 1, "ffmpeg")
    )

    assert "videóbemenetek=2" in summary
    assert "hangbemenetek=1" in summary
    assert "háttér=ffmpeg" in summary
    assert "Logitech" not in summary


def test_ures_kameralistanal_a_qml_elmondja_mit_ellenorizzen():
    qml_path = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/qml/PicasaPy/CaptureMoviePanelPopup.qml"
    )
    qml = qml_path.read_text(encoding="utf-8")

    assert (
        'qsTr("Check Windows camera privacy settings and close other apps that may '
        'be using the camera.")'
        in qml
    )
    normalized_qml = " ".join(qml.split())
    assert (
        'visible: Qt.platform.os === "windows" && !panel.settingsPage '
        '&& !panel.cameraAvailable'
    ) in normalized_qml


def test_u_res_kamerabemenetet_a_naplo_nevezze_meg_az_ellenorizendo_okokat(
    monkeypatch,
):
    from picasapy.app import startup_diagnostics

    class FakeProgressLog:
        messages: list[str]

        def __init__(self):
            self.messages = []

        def mark(self, message: str):
            self.messages.append(message)

    monkeypatch.setattr(
        startup_diagnostics,
        "_multimedia_device_snapshot",
        lambda: startup_diagnostics._MultimediaDeviceSnapshot(0, 1, "ffmpeg"),
    )
    monkeypatch.setattr(startup_diagnostics, "_platform", lambda: "win32")
    progress = FakeProgressLog()

    startup_diagnostics._log_multimedia_device_diagnostics(progress)

    assert any("videóbemenetek=0" in line for line in progress.messages)
    assert any("háttér=ffmpeg" in line for line in progress.messages)
    assert any("kamera-adatvédelmi" in line for line in progress.messages)
    assert any("másik program" in line for line in progress.messages)


def test_a_multimedia_diagnosztika_az_elso_kepkocka_utan_indul():
    prepare_path = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/application_startup_prepare.py"
    )
    prepare_source = prepare_path.read_text(encoding="utf-8")
    startup_step = prepare_source.split("def _startup_step_log_and_qt_setup", 1)[1]
    startup_step = startup_step.split("\ndef _startup_step_prepare_storage", 1)[0]
    assert "_log_multimedia_device_diagnostics(progress_log)" not in startup_step

    application_path = prepare_path.with_name("application.py")
    application_source = application_path.read_text(encoding="utf-8")
    first_frame_handler = application_source.split("def _on_first_frame()", 1)[1]
    first_frame_handler = first_frame_handler.split("\n    app = state.app", 1)[0]
    assert "_schedule_multimedia_device_diagnostics(progress_log)" in first_frame_handler


def test_a_multimedia_diagnosztika_kesleltetve_hatterben_indul(monkeypatch):
    from PySide6.QtCore import QTimer

    from picasapy.app import startup_diagnostics

    scheduled: list[tuple[int, object]] = []
    started: list[object] = []
    created: list[object] = []

    class FakeProgressLog:
        def mark(self, message: str) -> None:
            pass

    class FakeThread:
        def __init__(self, *, target, args, name, daemon):
            self.target = target
            self.args = args
            self.name = name
            self.daemon = daemon
            created.append(self)

        def start(self):
            started.append(self)

    monkeypatch.setattr(
        QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )
    monkeypatch.setattr(startup_diagnostics, "_thread", FakeThread)

    startup_diagnostics._schedule_multimedia_device_diagnostics(FakeProgressLog())

    assert len(scheduled) == 1
    assert scheduled[0][0] == 2000
    assert created == []
    scheduled[0][1]()
    assert len(created) == 1
    assert created[0].target is startup_diagnostics._log_multimedia_device_diagnostics
    assert created[0].daemon is True
    assert started == created


def _probe_media_devices(order: str) -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[2]
    probe = r"""
import json
import sys

if sys.argv[1] == "early":
    from picasapy.app.startup_splash import start_early_startup
    start_early_startup(["picasapy", "/nosplash"])
else:
    from PySide6.QtMultimedia import QMediaDevices
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication(["picasapy"])

from dataclasses import asdict
from picasapy.app.startup_diagnostics import _multimedia_device_snapshot
print(json.dumps(asdict(_multimedia_device_snapshot())))
"""
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), env.get("PYTHONPATH", "")]
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", probe, order],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            "A Qt Multimedia eszközfelsorolás 20 másodperc alatt nem fejeződött be.\n"
            f"stdout:\n{exc.stdout or ''}\nstderr:\n{exc.stderr or ''}",
            pytrace=False,
        )
    assert result.returncode == 0, (
        f"A {order} indítású próbafolyamat kilépési kódja {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return json.loads(result.stdout)


def test_a_korai_alkalmazas_mellett_az_eszkozfelsorolas_megegyezik_a_regivel():
    """Kameramentes Windows CI-n is lefut: a Qt háttérnaplója bizonyítja,
    hogy mindkét sorrend ténylegesen elérte a multimédia-backendet."""
    legacy = _probe_media_devices("legacy")
    early = _probe_media_devices("early")

    assert early["backend_name"] != "ismeretlen"
    assert early["backend_name"] == legacy["backend_name"]
    assert isinstance(early["video_input_count"], int)
    assert early["video_input_count"] == legacy["video_input_count"]
    assert early["audio_input_count"] == legacy["audio_input_count"]
    if sys.platform == "win32":
        assert isinstance(early["audio_input_count"], int)
