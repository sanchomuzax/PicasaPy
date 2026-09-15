"""#1402: az áthelyezés után a RÉGI példány LOMTÁRBA megy, nem törlődik.

A mérés szerint (`docs/specs/picasa-menu-parancsok-viselkedes.md`,
`ID_MOVE_DATABASE` kilenc pontja) az eredeti Picasa a régi adatbázist és
album-mappát a **Lomtárba** teszi. Nálunk `unlink`/`rmtree` futott: egy
elrontott áthelyezés után az adatbázis **visszaállíthatatlanul** eltűnt.

A `index/` csomag SZÁNDÉKOSAN nem ismeri a `fileops/` lomtárát (a két sáv
között ma egyetlen import sincs, egyik irányban sem): a magot a hívó
paraméterezi. Ez a lap a paramétert és a régi, végleges viselkedés
maradását is méri.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from picasapy.index.relocate import relocate_data_root


def _forras(tmp_path: Path) -> tuple[Path, Path]:
    regi = tmp_path / "regi"
    regi.mkdir()
    db = regi / "index.db"
    # ⚠️ A `with sqlite3.connect(...)` NEM zárja a kapcsolatot — csak a
    # tranzakciót kezeli. Windowson a nyitva hagyott fájlt a törlés nem tudja
    # elvinni (`WinError 32: used by another process`), és a próba pont a
    # törlést állítja. Ezért explicit `close()`.
    conn = sqlite3.connect(db)
    try:
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
    finally:
        conn.close()
    cache = regi / "thumbs"
    cache.mkdir()
    (cache / "a.jpg").write_bytes(b"kep")
    return db, cache


class TestRegiPeldanyTorlese:
    def test_alapbol_a_HIVO_torlojet_hasznalja(self, tmp_path):
        """A mag nem dönt a törlés módjáról — a hívó adja meg."""
        db, cache = _forras(tmp_path)
        torolt: list[Path] = []
        eredmeny = relocate_data_root(
            db,
            cache,
            tmp_path / "uj",
            delete_old=lambda ut: torolt.append(Path(ut)),
        )
        assert eredmeny.old_cleanup_error is None
        # a törlő MINDKETTŐT megkapta: az adatbázist és a gyorsítótárat
        assert db in torolt
        assert cache in torolt
        # …és a mag maga NEM nyúlt hozzájuk
        assert db.exists()
        assert cache.exists()

    def test_a_torlo_hibaja_nem_bukik_meg_az_athelyezest(self, tmp_path):
        """Az áthelyezés ezen a ponton már ellenőrzötten sikeres — egy
        törlési hiba nem teheti sikertelenné, csak jelezni kell."""
        db, cache = _forras(tmp_path)

        def bukik(_ut):
            raise OSError("nincs lomtár")

        eredmeny = relocate_data_root(db, cache, tmp_path / "uj", delete_old=bukik)
        assert eredmeny.old_cleanup_error is not None
        assert "nincs lomtár" in eredmeny.old_cleanup_error
        assert (tmp_path / "uj" / "index.db").exists()

    def test_torlo_nelkul_a_regi_VEGLEGESEN_tunik_el(self, tmp_path):
        """Visszafelé kompatibilitás: paraméter nélkül a korábbi viselkedés."""
        db, cache = _forras(tmp_path)
        eredmeny = relocate_data_root(db, cache, tmp_path / "uj")
        assert eredmeny.old_cleanup_error is None
        assert not db.exists()
        assert not cache.exists()
