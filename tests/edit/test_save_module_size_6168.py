"""A mentési modulok maradjanak a #5951 szerinti sorplafon alatt (#6168)."""

from __future__ import annotations

from pathlib import Path


_MODULOK = (
    "src/picasapy/edit/save.py",
    "src/picasapy/edit/save_operations.py",
    "src/picasapy/edit/save_storage.py",
    "src/picasapy/edit/save_ini.py",
)


def test_a_mentesi_modulok_700_sor_alatt_maradnak() -> None:
    gyoker = Path(__file__).resolve().parents[2]
    hosszak = {
        nev: len((gyoker / nev).read_text(encoding="utf-8").splitlines())
        for nev in _MODULOK
        if (gyoker / nev).is_file()
    }
    hianyzok = sorted(set(_MODULOK) - set(hosszak))
    tulhosszuak = {nev: sor for nev, sor in hosszak.items() if sor > 700}
    assert not hianyzok and not tulhosszuak, (
        f"Hiányzó mentési modulok: {hianyzok}; 700 sor felett: {tulhosszuak}"
    )
