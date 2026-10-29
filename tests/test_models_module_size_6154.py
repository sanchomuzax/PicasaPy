"""Source guard for the list model's named implementation modules (#6154)."""

from pathlib import Path

import pytest


_APP = Path(__file__).parents[1] / "src" / "picasapy" / "app"
_MODEL_MODULES = (
    "models.py",
    "folder_list_model.py",
    "model_helpers.py",
    "photo_grid_model.py",
    "photo_grid_state.py",
    "photo_grid_access.py",
    "photo_grid_navigation.py",
)


@pytest.mark.parametrize("module_name", _MODEL_MODULES)
def test_list_model_modules_stay_within_700_lines(module_name: str) -> None:
    path = _APP / module_name
    assert path.is_file(), f"A named model module is missing: {path}"

    line_count = len(path.read_text(encoding="utf-8").splitlines())
    assert line_count <= 700, f"{path} has {line_count} lines (maximum: 700)"
