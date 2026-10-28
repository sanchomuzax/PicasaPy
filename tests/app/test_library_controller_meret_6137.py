"""A #6137 felbontott könyvtár-vezérlő moduljai maradjanak 800 sor alatt."""

from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_MODULOK = (
    "src/picasapy/app/library_controller.py",
    "src/picasapy/app/library_controller_activity.py",
    "src/picasapy/app/library_controller_folders.py",
    "src/picasapy/app/library_controller_sync.py",
    "src/picasapy/app/library_controller_resync.py",
)


def test_a_konyvtarvezerlo_modulok_800_sor_alatt_maradnak():
    for relative_path in _MODULOK:
        source = _REPO / relative_path
        assert source.is_file(), f"hiányzó modul: {relative_path}"
        lines = len(source.read_text(encoding="utf-8").splitlines())
        assert lines < 800, f"{relative_path}: {lines} sor (a plafon 799)"
