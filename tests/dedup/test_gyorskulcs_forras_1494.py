"""A gyorskulcs FORRÁSA kívülről adható (#1494).

A `dedup/exact.py` eddig mindig a lemezről számolt (`picasa_fast_key`). A
#294 dHash-gyorstárának mintájára a kulcs is kaphat külső forrást — így a
hívó (`app/dedup_controller.py`) az index `photo_hashes.originfast`
oszlopából etetheti, és a MÁSODIK kör egyetlen fájlvéget sem olvas be újra.

A réteg ÍTÉLETE ettől nem változik: a kulcs továbbra is csak előszűrő, a
„bitre azonos" kimondója a teljes SHA-256 marad.
"""

import os
from pathlib import Path

from picasapy.dedup.api import find_duplicates
from picasapy.dedup.exact import group_exact_duplicates
from picasapy.dedup.fastkey import picasa_fast_key
from picasapy.index import IndexFastKeySource, open_index


def _azonos_meretu_par(tmp_path, *, azonos: bool) -> tuple[Path, Path]:
    """Két azonos MÉRETŰ fájl — így a kulcs-előszűrő tényleg lefut."""
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    tartalom = bytes((i * 13 + 7) & 0xFF for i in range(70000))
    a.write_bytes(tartalom)
    b.write_bytes(tartalom if azonos else tartalom[::-1])
    return a, b


class TestSzamlaloForras:
    """A `group_exact_duplicates` a megadott forrást használja."""

    def test_a_kapott_forras_hivodik_meg_nem_a_lemez(self, tmp_path):
        a, b = _azonos_meretu_par(tmp_path, azonos=True)
        hivasok: list[Path] = []

        def forras(path: Path) -> int | None:
            hivasok.append(path)
            return picasa_fast_key(path)

        csoportok = group_exact_duplicates((a, b), fast_key_source=forras)

        assert sorted(hivasok, key=str) == [a, b]
        assert len(csoportok) == 1

    def test_forras_nelkul_a_regi_viselkedes_marad(self, tmp_path):
        a, b = _azonos_meretu_par(tmp_path, azonos=True)
        assert len(group_exact_duplicates((a, b))) == 1

    def test_az_eltero_kulcs_tovabbra_is_kizar(self, tmp_path):
        a, b = _azonos_meretu_par(tmp_path, azonos=False)
        assert group_exact_duplicates((a, b), fast_key_source=picasa_fast_key) == ()

    def test_a_find_duplicates_tovabbadja_a_forrast(self, tmp_path):
        a, b = _azonos_meretu_par(tmp_path, azonos=True)
        hivasok: list[Path] = []

        def forras(path: Path) -> int | None:
            hivasok.append(path)
            return picasa_fast_key(path)

        jelentes = find_duplicates(
            (a, b), fast_key_source=forras, dhash_source=lambda _: None
        )

        assert sorted(hivasok, key=str) == [a, b]
        assert len(jelentes.exact_groups) == 1


class TestIndexHatterrel:
    """A jegy lényege: a MÁSODIK kör az indexből olvas."""

    def test_a_masodik_kor_egyetlen_fajlveget_sem_olvas_ujra(self, tmp_path):
        a, b = _azonos_meretu_par(tmp_path, azonos=True)
        db = tmp_path / "index.db"

        with open_index(db) as conn:
            elso = IndexFastKeySource(conn)
            elso_csoportok = group_exact_duplicates((a, b), fast_key_source=elso)
            elso.flush()
            conn.commit()

        with open_index(db) as conn:
            masodik = IndexFastKeySource(conn)
            masodik_csoportok = group_exact_duplicates((a, b), fast_key_source=masodik)

        assert (elso.szamolt, elso.talalat) == (2, 0)
        assert (masodik.szamolt, masodik.talalat) == (0, 2)
        assert elso_csoportok == masodik_csoportok
        assert len(masodik_csoportok) == 1

    def test_megvaltozott_fajlnal_a_masodik_kor_is_szamol(self, tmp_path):
        """ŐR: a gyorstár nem hazudhatja azonosnak a kicserélt fájlt."""
        a, b = _azonos_meretu_par(tmp_path, azonos=True)
        db = tmp_path / "index.db"

        with open_index(db) as conn:
            elso = IndexFastKeySource(conn)
            assert len(group_exact_duplicates((a, b), fast_key_source=elso)) == 1
            elso.flush()
            conn.commit()

        # `b` kicserélődik: azonos MÉRET, más tartalom — ha a régi kulcs
        # jönne vissza, a pár továbbra is „azonos kulcsú" volna.
        # Az `mtime_ns` KÉZZEL áll át: azonos méretnél a fájlrendszer
        # óra-felbontásán múlna, hogy az írás egyáltalán megváltoztatja-e
        # — az őr nem támaszkodhat erre (#1494 átnézés, 11. lelet).
        b.write_bytes(b.read_bytes()[::-1])
        os.utime(b, ns=(0, 1_000_000_000))

        with open_index(db) as conn:
            masodik = IndexFastKeySource(conn)
            csoportok = group_exact_duplicates((a, b), fast_key_source=masodik)

        assert masodik.szamolt == 1  # `b` újraszámolva, `a` az indexből
        assert masodik.talalat == 1
        assert csoportok == ()
