"""A diavetítés moduljai maradjanak a közös méretkorlát alatt (#6173)."""

from pathlib import Path

import pytest


_MOVIE = Path(__file__).resolve().parents[2] / "src/picasapy/movie"
_MODULES = (
    "slideshow.py",
    "slideshow_transitions.py",
    "slideshow_audio.py",
    "slideshow_text.py",
    "slideshow_frames.py",
)


@pytest.mark.parametrize("module_name", _MODULES)
def test_slideshow_modules_exist_and_stay_below_800_lines(module_name: str) -> None:
    module_path = _MOVIE / module_name
    assert module_path.is_file(), f"hiányzó diavetítés-modul: {module_name}"

    line_count = len(module_path.read_text(encoding="utf-8").splitlines())
    assert line_count < 800, f"{module_name}: {line_count} sor (plafon: <800)"
    assert line_count <= 700, f"{module_name}: {line_count} sor (plafon: 700)"
