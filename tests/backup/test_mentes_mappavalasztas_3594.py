"""#3594: a mentés MAPPÁNKÉNT választható, és csak a még el nem mentettet mutatja.

Az eredeti kiadás-panel mentés-üzemmódjának 2. lépése (`backuprect2`,
`publish_text.tre`, `biztonsagi-mentes.md` 10.3):

- `backuptext2`: „A Picasa most azokat a fájlokat jeleníti meg, amelyekről
  korábban nem készült biztonsági másolat."
- `backuptext3`: „Jelölje ki azokat a mappákat, amelyekről biztonsági
  másolatot szeretne készíteni, vagy »Az összes kijelölése« gombra
  kattintva az összes elemet jelölje ki."

Ez a fájl a magot méri: a terv a bepipált mappákra szűkíthető, és a
mappánkénti csoportosítás a már elmentett fájlt nem tartalmazza.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.backup import futtasd, mappankent, tervezd_meg
from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa
from support.jpeg_factory import make_jpeg


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    for mappa in ("nyaralas", "szulinap"):
        (gyoker / mappa).mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
    make_jpeg(gyoker / "szulinap" / "c.jpg")
    return gyoker


def _fajlok(gyoker: Path) -> list[Path]:
    return sorted(p for p in gyoker.rglob("*") if p.is_file())


class TestAMappaSzukites:
    def test_mappak_nelkul_minden_jelolt_bent_van(
        self, conn, tmp_path, gyujtemeny
    ):
        keszlet = keszlet_letrehozasa(conn, "Mind", str(tmp_path / "cel"))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny),
                           gyokerek=(str(gyujtemeny),))
        assert sorted(t.forras.name for t in terv.fajlok) == [
            "a.jpg", "b.jpg", "c.jpg"]

    def test_a_pipalt_mappa_SZUKITI_a_tervet(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(conn, "Egy", str(tmp_path / "cel"))
        terv = tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=(str(gyujtemeny),),
            mappak=[str(gyujtemeny / "szulinap")],
        )
        assert [t.forras.name for t in terv.fajlok] == ["c.jpg"]

    def test_ures_pipalista_semmit_nem_visz(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(conn, "Semmi", str(tmp_path / "cel"))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny),
                           gyokerek=(str(gyujtemeny),), mappak=[])
        assert terv.fajlok == ()

    def test_a_futas_csak_a_pipalt_mappat_masolja(
        self, conn, tmp_path, gyujtemeny
    ):
        cel = tmp_path / "cel"
        keszlet = keszlet_letrehozasa(conn, "Futás", str(cel))
        terv = tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=(str(gyujtemeny),),
            mappak=[str(gyujtemeny / "nyaralas")],
        )
        futtasd(conn, keszlet, terv)
        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["a.jpg", "b.jpg"]
        # a ki nem pipált mappa NEM került a nyilvántartásba: a következő
        # teljes terv még viszi
        terv2 = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny),
                            gyokerek=(str(gyujtemeny),))
        assert [t.forras.name for t in terv2.fajlok] == ["c.jpg"]


class TestAMappankentiNezet:
    def test_mappankent_csoportosit_rendezetten(
        self, conn, tmp_path, gyujtemeny
    ):
        keszlet = keszlet_letrehozasa(conn, "Csoport", str(tmp_path / "cel"))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny),
                           gyokerek=(str(gyujtemeny),))
        csoportok = mappankent(terv)
        assert list(csoportok) == [gyujtemeny / "nyaralas",
                                   gyujtemeny / "szulinap"]
        assert [t.forras.name for t in csoportok[gyujtemeny / "nyaralas"]] == [
            "a.jpg", "b.jpg"]

    def test_a_mar_elmentett_fajl_NEM_latszik(
        self, conn, tmp_path, gyujtemeny
    ):
        keszlet = keszlet_letrehozasa(conn, "Kétszer", str(tmp_path / "cel"))
        elso = tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=(str(gyujtemeny),),
            mappak=[str(gyujtemeny / "szulinap")],
        )
        futtasd(conn, keszlet, elso)

        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny),
                           gyokerek=(str(gyujtemeny),))
        csoportok = mappankent(terv)
        # a teljesen elmentett mappa el is tűnik a listából
        assert list(csoportok) == [gyujtemeny / "nyaralas"]
        assert terv.kihagyott == 1
