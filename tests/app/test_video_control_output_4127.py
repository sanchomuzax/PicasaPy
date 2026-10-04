"""#4127: a videó 1:1 és teljes képernyős vezérlői kimenet alapján."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _qml_modul_hianyzik(nev: str) -> bool:
    from PySide6.QtCore import QLibraryInfo

    import_ut = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath))
    return not (import_ut / nev).is_dir()


def test_video_meret_es_teljes_kepernyo_kimenet(tmp_path):
    pytest.importorskip("PySide6.QtMultimedia", exc_type=ImportError)
    if _qml_modul_hianyzik("QtMultimedia"):
        pytest.skip("a QtMultimedia QML-modulja hiányzik ezen a gépen")
    repo_root = Path(__file__).resolve().parents[2]
    probe = Path(__file__).with_name("qml_video_controls_probe.py")
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    result = subprocess.run(
        [sys.executable, str(probe)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    assert result.returncode == 0, (
        f"probe exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK #4127" in result.stdout
