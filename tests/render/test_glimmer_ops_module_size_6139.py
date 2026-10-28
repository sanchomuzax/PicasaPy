"""A Glimmer műveleti modulok forrásméret-korlátja (#6139)."""

from pathlib import Path

import pytest


_RENDER = Path(__file__).resolve().parents[2] / "src/picasapy/render"
_MODULOK = (
    "glimmer_ops.py",
    "glimmer_blend_ops.py",
    "glimmer_autofix_ops.py",
    "glimmer_color_ops.py",
    "glimmer_noise_ops.py",
    "glimmer_gradient_ops.py",
    "glimmer_mask_ops.py",
    "glimmer_resize_ops.py",
)


@pytest.mark.parametrize("modulnev", _MODULOK)
def test_minden_glimmer_modul_legfeljebb_700_sor(modulnev: str) -> None:
    """A régi import-homlokzat és minden kiemelt műveleti fájl is kis marad."""
    sorok = len((_RENDER / modulnev).read_text(encoding="utf-8").splitlines())

    assert sorok <= 700, f"{modulnev}: {sorok} sor, a plafon 700"
