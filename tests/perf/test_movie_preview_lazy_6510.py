"""A ritka film-elo-nezeti csomagok csak hasznalatkor toltodjenek be (#6510)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_APP_PROGRAM = r"""
import json
import sys
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication

_original_exec = QGuiApplication.exec

def _bounded_exec():
    app = QGuiApplication.instance()
    QTimer.singleShot(9000, app.quit)
    return _original_exec()

QGuiApplication.exec = staticmethod(_bounded_exec)
from picasapy.app.__main__ import main

sys.argv = ["picasapy", sys.argv[1]]
main()
print(json.dumps({
    "cv2": "cv2" in sys.modules,
    "qt_multimedia": "PySide6.QtMultimedia" in sys.modules,
}))
"""


def _indulasi_importok(tmp_path: Path) -> dict[str, bool]:
    empty_library = tmp_path / "empty-library"
    empty_library.mkdir()
    env = dict(os.environ)
    env.update(
        {
            "PYTHONPATH": os.pathsep.join(
                [str(_REPO / "src"), env.get("PYTHONPATH", "")]
            ).rstrip(os.pathsep),
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
            "XDG_CACHE_HOME": str(tmp_path / "cache"),
        }
    )
    process = subprocess.run(
        [sys.executable, "-c", _APP_PROGRAM, str(empty_library)],
        cwd=_REPO,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    if process.returncode != 0:
        (tmp_path / "app-startup.log").write_text(
            process.stdout + process.stderr, encoding="utf-8"
        )
    assert process.returncode == 0, (
        f"app exit={process.returncode}; see {tmp_path / 'app-startup.log'}; "
        + process.stdout[-1000:]
        + process.stderr[-1000:]
    )
    return json.loads(process.stdout.strip().splitlines()[-1])


def test_movie_preview_importja_elso_hasznalatig_kimarad(tmp_path: Path):
    betoltve = _indulasi_importok(tmp_path)
    felesleges_indulasi_modulok = {
        key: loaded
        for key, loaded in betoltve.items()
        if loaded
    }

    assert not felesleges_indulasi_modulok, (
        "indulaskor betoltodtek a csak kamera-/film-elonezethez szukseges "
        "media modulok: "
        f"{felesleges_indulasi_modulok}"
    )
