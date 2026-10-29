"""Forrásőr: a FileOpsController bontott moduljai maradjanak kezelhető méretűek."""

from pathlib import Path

import pytest


_MODULOK = (
    "fileops_controller.py",
    "fileops_controller_move_mixin.py",
    "fileops_controller_delete_mixin.py",
    "fileops_controller_clipboard_mixin.py",
    "fileops_controller_open_mixin.py",
)
_KONYVTAR = Path(__file__).resolve().parents[1] / "src/picasapy/app"


@pytest.mark.parametrize("modulnev", _MODULOK)
def test_fileops_controller_modulok_legfeljebb_700_sorosak(modulnev):
    modul = _KONYVTAR / modulnev
    assert modul.is_file(), f"hiányzó modul: {modul}"
    sorok = len(modul.read_text(encoding="utf-8").splitlines())
    assert sorok <= 700, f"{modulnev}: {sorok} sor (plafon: 700)"
