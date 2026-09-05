"""Az importálás duplikátum-szűrője a KÖNYVTÁR kulcsait az indexből veszi (#1494).

A `duplicate_paths` (#441) minden importálási körben újraszámolta a
könyvtárbeli, azonos méretű fájlok gyorskulcsát — pedig azok a fájlok
körök között változatlanok. A JELÖLTEK kulcsa marad számolt: azok a
kártyáról/kamerából jönnek, a következő körben már nem lesznek ott, tehát
az indexbe se valók (idegen útvonalú szemétsorok lennének).
"""

import os
from pathlib import Path

from picasapy.dedup.fastkey import picasa_fast_key
from picasapy.importsource import ImportCandidate, duplicate_paths
from picasapy.index import IndexFastKeySource, open_index


def _keszlet(tmp_path) -> tuple[Path, Path]:
    forras = tmp_path / "kartya"
    forras.mkdir()
    konyvtar = tmp_path / "konyvtar"
    konyvtar.mkdir()
    tartalom = bytes((i * 13 + 7) & 0xFF for i in range(70000))
    (forras / "a.jpg").write_bytes(tartalom)
    (konyvtar / "b.jpg").write_bytes(tartalom)
    return forras, konyvtar


class TestKonyvtarKulcsForras:
    def test_a_kapott_forras_csak_a_konyvtarra_hivodik(self, tmp_path):
        forras, konyvtar = _keszlet(tmp_path)
        hivasok: list[Path] = []

        def kulcsforras(path: Path) -> int | None:
            hivasok.append(path)
            return picasa_fast_key(path)

        jeloltek = (ImportCandidate(path=forras / "a.jpg", date=None),)
        eredmeny = duplicate_paths(
            jeloltek, [konyvtar / "b.jpg"], library_key_source=kulcsforras
        )

        assert hivasok == [konyvtar / "b.jpg"]
        assert eredmeny == frozenset({forras / "a.jpg"})

    def test_forras_nelkul_a_regi_viselkedes_marad(self, tmp_path):
        forras, konyvtar = _keszlet(tmp_path)
        jeloltek = (ImportCandidate(path=forras / "a.jpg", date=None),)
        assert duplicate_paths(jeloltek, [konyvtar / "b.jpg"]) == frozenset(
            {forras / "a.jpg"}
        )

    def test_a_masodik_import_a_konyvtarat_nem_olvassa_ujra(self, tmp_path):
        forras, konyvtar = _keszlet(tmp_path)
        jeloltek = (ImportCandidate(path=forras / "a.jpg", date=None),)
        db = tmp_path / "index.db"

        with open_index(db) as conn:
            elso = IndexFastKeySource(conn)
            duplicate_paths(jeloltek, [konyvtar / "b.jpg"], library_key_source=elso)
            elso.flush()
            conn.commit()

        with open_index(db) as conn:
            masodik = IndexFastKeySource(conn)
            eredmeny = duplicate_paths(
                jeloltek, [konyvtar / "b.jpg"], library_key_source=masodik
            )

        assert (elso.szamolt, elso.talalat) == (1, 0)
        assert (masodik.szamolt, masodik.talalat) == (0, 1)
        assert eredmeny == frozenset({forras / "a.jpg"})

    def test_megvaltozott_konyvtari_fajlnal_ujraszamol(self, tmp_path):
        """ŐR: a lecserélt könyvtári kép nem hozhatja vissza a régi kulcsot —
        különben egy ÚJ fénykép maradna ki szótlanul az importálásból."""
        forras, konyvtar = _keszlet(tmp_path)
        jeloltek = (ImportCandidate(path=forras / "a.jpg", date=None),)
        db = tmp_path / "index.db"

        with open_index(db) as conn:
            elso = IndexFastKeySource(conn)
            duplicate_paths(jeloltek, [konyvtar / "b.jpg"], library_key_source=elso)
            elso.flush()
            conn.commit()

        # A könyvtári kép helyére AZONOS MÉRETŰ, más tartalom kerül. Az
        # `mtime_ns` KÉZZEL áll át: azonos méretnél a fájlrendszer
        # óra-felbontásán múlna, hogy az írás megváltoztatja-e — az őr nem
        # támaszkodhat erre (#1494 átnézés, 11. lelet).
        regi = (konyvtar / "b.jpg").read_bytes()
        (konyvtar / "b.jpg").write_bytes(regi[::-1])
        os.utime(konyvtar / "b.jpg", ns=(0, 1_000_000_000))

        with open_index(db) as conn:
            masodik = IndexFastKeySource(conn)
            eredmeny = duplicate_paths(
                jeloltek, [konyvtar / "b.jpg"], library_key_source=masodik
            )

        assert masodik.szamolt == 1
        assert eredmeny == frozenset()  # már nem duplikátum
