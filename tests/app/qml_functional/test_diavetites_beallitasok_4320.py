"""#4320: a Diavetítés beállításai valódi kattintással vezérlik a vetítőt.

A Qt Multimedia motor külön folyamatban fut: a MediaPlayer QML-lebontása
tesztfolyamatban GIL↔Qt deadlockra hajlamos (lásd test_qml_video.py).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

def test_diavetites_beallitasok_kattintassal_tarolodnak_es_hatnak(tmp_path):
    probe = Path(__file__).parents[1] / "qml_diavetites_beallitasok_probe_4320.py"
    repo_root = Path(__file__).resolve().parents[3]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    result = subprocess.run(
        [sys.executable, str(probe), str(tmp_path / "probe")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        env=env,
    )
    assert result.returncode == 0, (
        f"probe exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK #4320" in result.stdout
