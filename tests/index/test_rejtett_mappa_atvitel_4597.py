"""#4597 — a 2-es (ini-be még nem írt) rejtés áthelyezéskor az új útra kerül.

Az index-réteg csak a jelölést viszi át (az ini-írást a közvetlenül utána
futó szinkron végzi); mindkét útvonal-elválasztóval működik.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index
from picasapy.index.queries import carry_pending_hidden


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


def _sor(conn, path, hidden):
    conn.execute(
        "INSERT INTO folders(path, has_ini, hidden) VALUES (?, 0, ?)", (path, hidden)
    )


def _hidden(conn, path):
    sor = conn.execute("SELECT hidden FROM folders WHERE path = ?", (path,)).fetchone()
    return None if sor is None else sor[0]


def test_windowsos_utnal_az_almappa_jelolese_atkerul(conn):
    _sor(conn, "C:\\a\\b", 2)
    _sor(conn, "C:\\a\\b\\sub", 2)
    _sor(conn, "C:\\a\\bb", 2)  # hasonló nevű, NEM része a részfának
    carry_pending_hidden(conn, "C:\\a\\b", "C:\\a\\x")
    assert _hidden(conn, "C:\\a\\x") == 2
    assert _hidden(conn, "C:\\a\\x\\sub") == 2
    assert _hidden(conn, "C:\\a\\xb") is None


def test_posix_utnal_is_atkerul(conn):
    _sor(conn, "/k/b", 2)
    _sor(conn, "/k/b/sub", 2)
    carry_pending_hidden(conn, "/k/b", "/k/x")
    assert _hidden(conn, "/k/x") == 2
    assert _hidden(conn, "/k/x/sub") == 2


def test_csak_a_2_es_jelolest_viszi_at(conn):
    _sor(conn, "/k/b", 1)
    _sor(conn, "/k/b/sub", 0)
    carry_pending_hidden(conn, "/k/b", "/k/x")
    assert _hidden(conn, "/k/x") is None
    assert _hidden(conn, "/k/x/sub") is None


def test_a_mar_letezo_cel_sort_2_esre_allitja(conn):
    _sor(conn, "/k/b", 2)
    _sor(conn, "/k/x", 0)
    carry_pending_hidden(conn, "/k/b", "/k/x")
    assert _hidden(conn, "/k/x") == 2
