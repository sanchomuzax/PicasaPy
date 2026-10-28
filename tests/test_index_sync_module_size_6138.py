"""Source guard for the index sync module split requested by #6138."""

from pathlib import Path

import pytest


SYNC_MODULES = sorted((Path(__file__).parents[1] / "src/picasapy/index").glob("sync*.py"))


@pytest.mark.parametrize("module_path", SYNC_MODULES, ids=lambda path: path.name)
def test_sync_modules_stay_below_800_lines(module_path: Path) -> None:
    line_count = len(module_path.read_text(encoding="utf-8").splitlines())

    assert line_count < 800, f"{module_path.name}: {line_count} lines (limit: <800)"


@pytest.mark.parametrize("module_path", SYNC_MODULES, ids=lambda path: path.name)
def test_sync_modules_obey_the_700_line_ceiling(module_path: Path) -> None:
    line_count = len(module_path.read_text(encoding="utf-8").splitlines())

    assert line_count <= 700, f"{module_path.name}: {line_count} lines (limit: 700)"
