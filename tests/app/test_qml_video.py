"""Videó-lejátszás a nézőben (#14) — a QML-ellenőrzés alprocesszben fut.

A MediaPlayer + engine ismételt életciklusa egy processzen belül GIL↔Qt
deadlockra hajlamos (a #53-as hibaosztály), ezért a teljes videós
QML-viselkedést a qml_video_probe.py egyetlen alprocesszben ellenőrzi —
így a tesztkészlet többi (engine-t építő) tesztjét nem veszélyezteti.
A Qt Multimedia hiányában a teszt kimarad.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_video_viewer_probe(tmp_path):
    # exc_type=ImportError: a felhő-konténerben a modul megvan, de a
    # rendszerkönyvtára (libpulse) hiányzik — az is kihagyás, nem hiba
    pytest.importorskip("PySide6.QtMultimedia", exc_type=ImportError)
    probe = Path(__file__).parent / "qml_video_probe.py"
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    result = subprocess.run(
        [sys.executable, str(probe), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, (
        f"probe exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK" in result.stdout
