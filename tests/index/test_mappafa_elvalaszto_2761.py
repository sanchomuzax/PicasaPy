"""A mappafa-minta a PLATFORM elválasztóját használja (#2761).

## A hiba

A `_mappafa_parameterek` fixen `/`-t fűzött a `LIKE`-mintához:

```python
return (folder_path, vedett.rstrip("/") + "/%")
```

Az index viszont **platform-natív** útvonalat tárol (`index/paths.py`:
`str(Path(...).resolve())`, a `sync.py` írja a `folders.path`-ba). Windowson a
tárolt `C:\\kepek\\alfa` tehát sosem illeszkedett a generált `C:\\\\kepek/%`
mintára ⇒ **a kizárt mappa ALFÁI nem kapták meg a jelölést**, és a következő
szkennelés újra végigment volna rajtuk.

A CI windows-lába ezt a #2519 három őrén mutatta ki (`assert 1 == 2`: a két
fotóból csak a közvetlenül a mappában lévő kapott jelölést).

## Miért ez a lap

A hiba **szerkezetileg láthatatlan** azon a platformon, ahol fejlesztünk: a
POSIX-ágon a `/` véletlenül helyes. Ezért a próba az elválasztót
**paraméterként** adja meg, és MINDKÉT alakot méri — a fejlesztői gépen is.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from picasapy.index import open_index
from picasapy.index.faces_detected import (
    OK_KIZARVA,
    _mappafa_parameterek,
    face_scan_done,
    mark_folder_excluded,
)


class TestMinta:
    """#2765: MINDKÉT elválasztóra illeszkedünk — nincs platform-elágazás."""

    def test_mindket_minta_megjon(self):
        pontos, perjel, fordított = _mappafa_parameterek("/kepek")
        assert pontos == "/kepek"
        assert perjel == "/kepek/%"
        # a `\` a mintában DUPLÁZÓDIK: a `LIKE` `ESCAPE '\'`-t használ,
        # tehát ott a backslash önmagát is escape-eli
        assert fordított == "/kepek\\\\%"

    def test_windows_alaku_ut(self):
        pontos, perjel, fordított = _mappafa_parameterek(r"C:\kepek")
        assert pontos == r"C:\kepek"
        assert perjel == "C:\\\\kepek/%"
        assert fordított == "C:\\\\kepek\\\\%"

    @pytest.mark.parametrize("zaro", ["/", "\\"])
    def test_a_zaro_elvalasztot_levagja(self, zaro):
        """A záró elválasztó nem duplázódhat a mintában — MINDKÉT alakot le
        kell vágni (a perjelre szűkített vágás a fordított perjelet
        bent hagyta)."""
        _pontos, perjel, fordított = _mappafa_parameterek(f"C:\\kepek{zaro}")
        assert perjel == "C:\\\\kepek/%", perjel
        assert fordított == "C:\\\\kepek\\\\%", fordított

    def test_a_LIKE_jokereket_escape_eli(self):
        """Egy valódi mappanévben is állhat `%` vagy `_` — mindkettő joker."""
        _pontos, perjel, fordított = _mappafa_parameterek("/a_b/c%d")
        for minta in (perjel, fordított):
            assert "\\_" in minta and "\\%" in minta, minta


class TestAdatbazis:
    """A minta a VALÓDI `LIKE`-lekérdezésben is illeszkedjen — mindkét
    elválasztóval, a fejlesztői gépen is."""

    @pytest.mark.parametrize("elvalaszto", ["/", "\\"])
    def test_az_alfa_fotoja_is_jelolest_kap(
        self, tmp_path: Path, elvalaszto: str
    ) -> None:
        gyoker = "/lib" if elvalaszto == "/" else r"C:\lib"
        alfa = f"{gyoker}{elvalaszto}alfa"
        masik = "/masik" if elvalaszto == "/" else r"C:\masik"

        path = tmp_path / "index.db"
        with open_index(path) as conn:
            for azonosito, mappa in enumerate((gyoker, alfa, masik), start=1):
                conn.execute(
                    "INSERT INTO folders(id, path, has_ini) VALUES (?, ?, 0)",
                    (azonosito, mappa),
                )
                conn.execute(
                    "INSERT INTO photos(id, folder_id, name, kind, size, mtime_ns)"
                    " VALUES (?, ?, 'a.jpg', 'photo', 10, 5)",
                    (azonosito, azonosito),
                )
            conn.commit()

            erintett = mark_folder_excluded(conn, gyoker)

            assert erintett == 2, (
                f"{elvalaszto!r} elválasztóval csak {erintett} fotó kapott "
                f"jelölést — az ALFA kimaradt (ez bukott a CI windows-lábán)"
            )
            assert face_scan_done(conn, 1, mtime_ns=99, size=99)
            assert face_scan_done(conn, 2, mtime_ns=99, size=99), "az alfa fotója"
            assert not face_scan_done(conn, 3, mtime_ns=5, size=10), "idegen mappa"
            okok = {sor[0] for sor in conn.execute("SELECT ok FROM face_scan")}
            assert okok == {OK_KIZARVA}

    def test_a_hasonlo_nevu_TESTVER_mappa_nem_erintett(self, tmp_path: Path) -> None:
        """`C:\\lib` kizárása nem érintheti a `C:\\lib-masolat`-ot."""
        path = tmp_path / "index.db"
        with open_index(path) as conn:
            for azonosito, mappa in enumerate((r"C:\lib", r"C:\lib-masolat"), start=1):
                conn.execute(
                    "INSERT INTO folders(id, path, has_ini) VALUES (?, ?, 0)",
                    (azonosito, mappa),
                )
                conn.execute(
                    "INSERT INTO photos(id, folder_id, name, kind, size, mtime_ns)"
                    " VALUES (?, ?, 'a.jpg', 'photo', 10, 5)",
                    (azonosito, azonosito),
                )
            conn.commit()
            assert mark_folder_excluded(conn, r"C:\lib") == 1
            assert not face_scan_done(conn, 2, mtime_ns=5, size=10)


def test_a_sqlite_LIKE_tenyleg_igy_escape_el(tmp_path: Path) -> None:
    """Kontroll: a fenti minta-alak a VALÓDI SQLite `LIKE`-jában viselkedik
    így — nem csak a mi elképzelésünkben."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t(p TEXT)")
    conn.executemany(
        "INSERT INTO t VALUES (?)",
        [(r"C:\lib",), (r"C:\lib\alfa",), (r"C:\lib-masolat",), (r"C:\libX\a",)],
    )
    _pontos, _perjel, fordított = _mappafa_parameterek(r"C:\lib")
    sorok = [
        sor[0]
        for sor in conn.execute(
            "SELECT p FROM t WHERE p LIKE ? ESCAPE '\\' ORDER BY p", (fordított,)
        )
    ]
    assert sorok == [r"C:\lib\alfa"], sorok


def test_VEGYES_utak_ugyanabban_az_indexben(tmp_path: Path) -> None:
    """#2765: a két alak KIZÁRTA egymást, amíg egyetlen elválasztóra szűrtünk.

    A `folders.path` alakja nem a futó gépé, hanem azé, ahol az index
    készült — egy átvett adatbázisban (vagy másik gépről hozott
    `.picasa.ini`-korpuszban) POSIX-alak is állhat egy windowsos gépen. Ez a
    próba ezért EGY indexbe teszi mindkettőt.
    """
    path = tmp_path / "index.db"
    with open_index(path) as conn:
        mappak = ["/lib", "/lib/alfa", r"C:\lib", r"C:\lib\alfa"]
        for azonosito, mappa in enumerate(mappak, start=1):
            conn.execute(
                "INSERT INTO folders(id, path, has_ini) VALUES (?, ?, 0)",
                (azonosito, mappa),
            )
            conn.execute(
                "INSERT INTO photos(id, folder_id, name, kind, size, mtime_ns)"
                " VALUES (?, ?, 'a.jpg', 'photo', 10, 5)",
                (azonosito, azonosito),
            )
        conn.commit()

        assert mark_folder_excluded(conn, "/lib") == 2, "a POSIX-fa két fotója"
        assert face_scan_done(conn, 2, mtime_ns=99, size=99), "a POSIX alfa"
        assert not face_scan_done(conn, 3, mtime_ns=5, size=10), "a windowsos ág"

        assert mark_folder_excluded(conn, r"C:\lib") == 2, "a windowsos fa két fotója"
        assert face_scan_done(conn, 4, mtime_ns=99, size=99), "a windowsos alfa"
