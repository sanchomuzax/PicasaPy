"""#4273: render the official start/end labels on the video trim track."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_TRIM_QML = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "picasapy"
    / "app"
    / "qml"
    / "PicasaPy"
    / "VideoTrimSlider.qml"
)


def _render_probe(height: int, screenshot: Path) -> str:
    probe = Path(__file__).with_name("video_trim_labels_probe.py")
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    # #4355: Windowson a konzol cp1252 — a próba ékezetes sorát UTF-8-ban kérjük
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    result = subprocess.run(
        [sys.executable, str(probe), str(height), str(screenshot)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        env=env,
    )
    assert result.returncode == 0, (
        f"probe exit={result.returncode}\nstdout:\n{result.stdout}"
        f"\nstderr:\n{result.stderr}"
    )
    assert "Binding loop detected" not in result.stderr
    return result.stdout


@pytest.mark.parametrize("height", [80, 75, 85])
def test_rendered_trim_labels_are_official_and_follow_their_handles(
    height, tmp_path
):
    screenshot = tmp_path / f"video-trim-{height}.png"
    output = _render_probe(height, screenshot)

    assert screenshot.is_file() and screenshot.stat().st_size > 0
    assert f"OK #4273 height={height}" in output
    assert "start=Kezdőpont" in output
    assert "end=Végpont" in output


def test_labels_keep_qsTr_sources_and_explicit_font_setting():
    qml = _TRIM_QML.read_text(encoding="utf-8")

    assert 'text: qsTr("Start Point")' in qml
    assert 'text: qsTr("End Point")' in qml
    assert "font.pixelSize: 10" in qml
