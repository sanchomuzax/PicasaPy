"""Forrásőr: a létrehozás-vezérlő részei maradjanak kezelhető méretűek."""

from pathlib import Path


_GYOKER = Path(__file__).resolve().parents[2]
_MODULOK = (
    "src/picasapy/app/create_controller.py",
    "src/picasapy/app/create_movie_controller.py",
    "src/picasapy/app/create_collage_operations.py",
)


def test_a_letrehozas_vezerlo_reszei_800_sor_alatt_maradnak():
    for relative_path in _MODULOK:
        path = _GYOKER / relative_path
        assert path.is_file(), f"hiányzó létrehozás-modul: {relative_path}"
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        assert line_count < 800, (
            f"{relative_path}: {line_count} sor (a plafon 800)"
        )
