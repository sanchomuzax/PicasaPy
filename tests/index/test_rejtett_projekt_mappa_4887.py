"""#4887 — a Projektek hasáb sem mutat rejtett projekt-mappát (név és darabszám).

A rejtett mappa (`folders.hidden != 0`) a közös láthatósági kapuval
(`index/hidden_scope.py`) együtt szűnik meg a listából; a kapcsoló
bekapcsolása után újra megjelenik.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, project_folders, set_folder_hidden, sync_tree
from picasapy.index.hidden_scope import set_hidden_folders_visible

_PROJECTS = "[Picasa]\nP2category=Projects (internal)\n"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    for name in ("Kollázsok", "titkos projekt"):
        (root / name).mkdir(parents=True)
        (root / name / "IMG_0001.jpg").write_bytes(b"x" * 10)
        (root / name / ".picasa.ini").write_text(_PROJECTS, encoding="utf-8")
    return root


@pytest.fixture
def index_path(tmp_path, library):
    path = tmp_path / "index.db"
    with open_index(path) as conn:
        sync_tree(conn, library)
        set_folder_hidden(conn, str(library / "titkos projekt"), True)
        conn.commit()
    return path


def _projektek(index_path) -> dict[str, int]:
    with open_index(index_path) as conn:
        return {folder.name: folder.photo_count for folder in project_folders(conn)}


def test_rejtett_projekt_mappa_nem_jelenik_meg(index_path):
    assert _projektek(index_path) == {"Kollázsok": 1}


def test_kapcsolo_bekapcsolasa_utan_a_rejtett_projekt_is_megjelenik(index_path):
    set_hidden_folders_visible(index_path, True)
    assert _projektek(index_path) == {"Kollázsok": 1, "titkos projekt": 1}
