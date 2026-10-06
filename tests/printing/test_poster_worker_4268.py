"""#4268 — a poszter-worker ne függjön a konzolstreamektől."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest


def _worker_command(source: Path, result: Path) -> list[str]:
    gyoker = Path(__file__).resolve().parents[2]
    script = (
        "import sys; "
        "sys.path.insert(0, sys.argv[1]); "
        "sys.stdout = None; sys.stderr = None; "
        "from picasapy.printing.poster_worker import main; "
        "raise SystemExit(main(sys.argv[2:]))"
    )
    return [
        sys.executable,
        "-c",
        script,
        str(gyoker / "src"),
        str(source),
        "200",
        "4x6",
        "0",
        str(result),
    ]


def test_worker_writes_page_list_when_stdout_and_stderr_are_unavailable(tmp_path):
    source = tmp_path / "source.png"
    result = tmp_path / "result.json"
    Image.new("RGB", (80, 80), color=(20, 40, 60)).save(source)

    completed = subprocess.run(
        _worker_command(source, result),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert json.loads(result.read_text(encoding="utf-8")) == {
        "pages": [
            str(tmp_path / "0-0-source.png"),
            str(tmp_path / "0-1-source.png"),
            str(tmp_path / "1-0-source.png"),
            str(tmp_path / "1-1-source.png"),
        ]
    }


def test_worker_writes_error_when_input_is_missing_and_stderr_is_unavailable(
    tmp_path,
):
    result = tmp_path / "result.json"

    completed = subprocess.run(
        _worker_command(tmp_path / "missing.png", result),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert json.loads(result.read_text(encoding="utf-8"))["error"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX fájlnév-kódolási eset")
def test_worker_json_preserves_a_non_utf8_filename(tmp_path):
    source = tmp_path / os.fsdecode(b"source-\xff.png")
    result = tmp_path / "result.json"
    Image.new("RGB", (80, 80), color=(20, 40, 60)).save(source)

    completed = subprocess.run(
        _worker_command(source, result),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert completed.returncode == 0
    pages = json.loads(result.read_text(encoding="utf-8"))["pages"]
    assert len(pages) == 4
    assert all(Path(page).is_file() for page in pages)
