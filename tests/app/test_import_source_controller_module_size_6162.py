"""#6162: a vezérlő moduljai maradjanak a 700 soros plafon alatt."""

from pathlib import Path


_APP = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app"
_MODULES = (
    "import_source_controller.py",
    "import_source_controller_state.py",
    "import_source_controller_scanning.py",
)
_MAX_LINES = 700


def test_import_source_controller_modules_stay_under_line_limit():
    missing = [name for name in _MODULES if not (_APP / name).is_file()]
    sizes = {
        name: len((_APP / name).read_text(encoding="utf-8").splitlines())
        for name in _MODULES
        if (_APP / name).is_file()
    }
    oversized = {name: size for name, size in sizes.items() if size > _MAX_LINES}

    assert not oversized, f"A 700 soros modulszabályt túllépő fájlok: {oversized}"
    assert not missing, f"Hiányzó importforrás-modulok: {missing}"
