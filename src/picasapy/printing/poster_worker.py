"""Képlapok készítése a Qt-folyamattól elkülönített OpenCV-folyamatban."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

from picasapy.printing.poster import make_poster_tiles


def main(arguments: Sequence[str] | None = None) -> int:
    """Elvégzi a vágást és a fájlneveket eredményfájlba írja.

    A PyInstaller ablakos programjában nincs konzolstream; a fájlos válaszút
    ezért a fagyasztott és a forrásból indított workerben is működik.
    """
    args = list(sys.argv[1:] if arguments is None else arguments)
    if len(args) != 5:
        return 2

    source, magnification, paper_size, overlap, result_path = args
    try:
        pages = make_poster_tiles(
            source,
            int(magnification),
            paper_size,
            overlap == "1",
        )
    except Exception as exc:  # noqa: BLE001 — a vezérlőnek fájlban jelez
        result = {"error": str(exc)}
        exit_code = 1
    else:
        result = {"pages": [str(page) for page in pages]}
        exit_code = 0

    try:
        Path(result_path).write_text(
            json.dumps(result), encoding="utf-8"
        )
    except OSError:
        return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
