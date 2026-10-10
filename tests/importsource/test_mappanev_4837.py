"""#4837: a kézi importmappanév EGYETLEN útvonal-elem — nem vezethet ki a célból."""

from datetime import date

import pytest

from picasapy.importsource import (
    NAMING_MANUAL,
    destination_subpath_for_mode,
    is_valid_folder_name,
)

INVALID = [
    "", "   ", "/", "\\", "..", ".", "/etc", "C:\\x", "C:", "a/b", "a\\b",
    "../x", "..\\x", "<", ">", ":", '"', "|", "?", "*", "a\x00b", "a\x1fb",
    "a\x7fb",
]


@pytest.mark.parametrize("name", INVALID)
def test_invalid_names_rejected(name):
    assert is_valid_folder_name(name) is False


@pytest.mark.parametrize("name", ["Nyaralás 2026", "2026-10-10", "a.b", " x "])
def test_valid_names_accepted(name):
    assert is_valid_folder_name(name) is True


@pytest.mark.parametrize("name", INVALID)
def test_destination_subpath_raises_for_invalid(name):
    with pytest.raises(ValueError):
        destination_subpath_for_mode(
            date(2026, 1, 1), NAMING_MANUAL, manual_name=name
        )


def test_valid_name_is_single_element():
    path = destination_subpath_for_mode(
        None, NAMING_MANUAL, manual_name=" Nyaralás 2026 "
    )
    assert path.parts == ("Nyaralás 2026",)


@pytest.mark.parametrize("name", ["../x", "../../x", "/etc", "a/../../x"])
def test_no_file_created_outside_destination(tmp_path, name):
    dest = tmp_path / "dest"
    dest.mkdir()
    try:
        target = dest / destination_subpath_for_mode(
            None, NAMING_MANUAL, manual_name=name
        )
    except ValueError:
        pass
    else:  # pragma: no cover - a hiba esetén bukik
        target.mkdir(parents=True, exist_ok=True)
    assert [p for p in tmp_path.rglob("*") if dest not in p.parents and p != dest] == []
