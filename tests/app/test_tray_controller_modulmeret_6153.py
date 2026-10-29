"""A tálcavezérlő moduljai maradjanak a közös 700 soros plafon alatt."""

from pathlib import Path

import pytest


_APP = Path(__file__).resolve().parents[2] / "src/picasapy/app"
_MODULOK = (
    "tray_controller.py",
    "tray_state_controller.py",
    "tray_album_controller.py",
    "tray_google_photos_controller.py",
)


@pytest.mark.parametrize("modulnev", _MODULOK)
def test_a_talca_moduljai_700_sor_alatt_maradnak(modulnev: str) -> None:
    modul = _APP / modulnev
    assert modul.is_file(), f"hiányzó tálcamodul: {modulnev}"

    sorok = len(modul.read_text(encoding="utf-8").splitlines())
    assert sorok <= 700, f"{modulnev}: {sorok} sor (plafon: 700)"
    assert sorok < 800, f"{modulnev}: {sorok} sor (plafon: <800)"
