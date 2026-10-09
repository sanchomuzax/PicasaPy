"""#4601: albumzene a diavetítés és a film alapértelmezett hangsávjaként."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_album_zene_kattintassal_a_diavetitesbe_es_a_filmbe_jut(tmp_path):
    probe = Path(__file__).parents[1] / "qml_album_zene_probe_4601.py"
    repo_root = Path(__file__).resolve().parents[3]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    try:
        result = subprocess.run(
            [sys.executable, str(probe), str(tmp_path / "probe")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
            env=env,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise AssertionError(
            f"probe timed out\nstdout:\n{stdout}\nstderr:\n{stderr[-2000:]}"
        ) from error
    assert result.returncode == 0, (
        f"probe exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK #4601" in result.stdout
