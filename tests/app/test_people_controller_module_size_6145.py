"""#6145: az Emberek-vezérlő moduljai a 700 soros plafon alatt maradnak."""

from pathlib import Path


_APP = Path(__file__).parents[2] / "src" / "picasapy" / "app"
_MODULES = (
    "people_controller.py",
    "people_manager_controller.py",
    "people_album_controller.py",
    "people_faces_controller.py",
    "people_controller_compat.py",
)
_MAX_LINES = 700


def test_people_controller_modules_stay_under_line_limit():
    missing = [name for name in _MODULES if not (_APP / name).is_file()]
    sizes = {
        name: len((_APP / name).read_text(encoding="utf-8").splitlines())
        for name in _MODULES
        if (_APP / name).is_file()
    }
    oversized = {name: size for name, size in sizes.items() if size > _MAX_LINES}

    assert not oversized, f"A 700 soros modulszabályt túllépő fájlok: {oversized}"
    assert not missing, f"Hiányzó People-modulok: {missing}"
