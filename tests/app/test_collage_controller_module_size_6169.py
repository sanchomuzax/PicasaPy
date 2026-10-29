"""#6169: a kollázs-vezérlő moduljai maradjanak a 700 soros plafon alatt."""

from pathlib import Path

import pytest


_APP = Path(__file__).resolve().parents[2] / "src/picasapy/app"
_MAX_LINES = 700


@pytest.mark.parametrize(
    "module_path",
    sorted(_APP.glob("collage_controller*.py")),
    ids=lambda path: path.name,
)
def test_collage_controller_modules_stay_under_line_limit(module_path: Path) -> None:
    assert module_path.is_file(), f"hiányzó kollázsmodul: {module_path.name}"

    line_count = len(module_path.read_text(encoding="utf-8").splitlines())
    assert line_count <= _MAX_LINES, (
        f"{module_path.name}: {line_count} sor (plafon: {_MAX_LINES})"
    )
    assert line_count < 800, f"{module_path.name}: {line_count} sor (plafon: <800)"
