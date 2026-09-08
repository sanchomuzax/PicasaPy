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
    def test_posix_elvalaszto(self):
        pontos, minta = _mappafa_parameterek("/kepek", elvalaszto="/")
        assert pontos == "/kepek"
        assert minta == "/kepek/%"

    def test_windows_elvalaszto(self):
        """A `\\` a mintában DUPLÁZÓDIK: a `LIKE` `ESCAPE '\\'`-t használ,
        tehát ott a backslash önmagát is escape-eli."""
        pontos, minta = _mappafa_parameterek(r"C:\kepek", elvalaszto="\\")
        assert pontos == r"C:\kepek"
        assert minta == "C:\\\\kepek\\\\%"

    @pytest.mark.parametrize("elvalaszto", ["/", "\\"])
    def test_a_zaro_elvalasztot_levagja(self, elvalaszto):
        """A záró elválasztó nem duplázódhat a mintában — a régi kód a `\\`-t
        nem vágta le (`rstrip("/")`), tehát Windowson `…\\\\\\\\%` jött ki."""
        ut = f"/kepek{elvalaszto}" if elvalaszto == "/" else f"C:\\kepek{elvalaszto}"
        _pontos, minta = _mappafa_parameterek(ut, elvalaszto=elvalaszto)
        vart_veg = "/%" if elvalaszto == "/" else "\\\\%"
        assert minta.endswith(vart_veg), minta
        assert not minta.endswith(vart_veg * 2), f"dupla elválasztó a mintában: {minta}"

    @pytest.mark.parametrize("elvalaszto", ["/", "\\"])
    def test_a_LIKE_jokereket_escape_eli(self, elvalaszto):
        """Egy valódi mappanévben is állhat `%` vagy `_` — mindkettő joker."""
        ut = f"/a_b{elvalaszto}c%d" if elvalaszto == "/" else f"C:\\a_b{elvalaszto}c%d"
        _pontos, minta = _mappafa_parameterek(ut, elvalaszto=elvalaszto)
        assert "\\_" in minta and "\\%" in minta, minta


class TestAdatbazis:
    """A minta a VALÓDI `LIKE`-lekérdezésben is illeszkedjen — mindkét
    elválasztóval, a fejlesztői gépen is."""

    @pytest.mark.parametrize("elvalaszto", ["/", "\\"])
    def test_az_alfa_fotoja_is_jelolest_kap(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, elvalaszto: str
    ) -> None:
        from picasapy.index import faces_detected

        monkeypatch.setattr(faces_detected, "_ELVALASZTO", elvalaszto)
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

    def test_a_hasonlo_nevu_TESTVER_mappa_nem_erintett(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`C:\\lib` kizárása nem érintheti a `C:\\lib-masolat`-ot."""
        from picasapy.index import faces_detected

        monkeypatch.setattr(faces_detected, "_ELVALASZTO", "\\")
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
    _pontos, minta = _mappafa_parameterek(r"C:\lib", elvalaszto="\\")
    sorok = [
        sor[0]
        for sor in conn.execute(
            "SELECT p FROM t WHERE p LIKE ? ESCAPE '\\' ORDER BY p", (minta,)
        )
    ]
    assert sorok == [r"C:\lib\alfa"], sorok
