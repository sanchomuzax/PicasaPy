"""#440: nevesített, újrafuttatható, inkrementális mentés-készletek.

Az eredeti Picasa saját meghatározása: *„A Backup Set records where to
store backed-up files, and it also keeps a record of which files have
been backed up already, so you don't have to back them up again."*

A CD/DVD-ág szándékosan kimarad (a jegy döntése); a cél külső meghajtó
vagy hálózati megosztás.

⚠️ Ez a réteg **felület nélkül** áll: a menüpont és a párbeszéd külön
jegy. Ezért a kiadási jegyzet sem állítja, hogy a funkció elérhető.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.backup import MANIFESZT_NEVE, futtasd, tervezd_meg
from picasapy.index import open_index
from picasapy.index.backup_sets import (
    SZURO_FENYKEPEZOGEP,
    SZURO_KEPEK,
    SZURO_MINDEN,
    elmentett_allapot,
    keszlet_letrehozasa,
    keszlet_modositasa,
    keszlet_nev_szerint,
    keszlet_torlese,
    keszletek,
)
from support.jpeg_factory import make_jpeg


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
    (gyoker / "nyaralas" / ".picasa.ini").write_text(
        "[a.jpg]\nstar=yes\n", encoding="utf-8"
    )
    (gyoker / "film.avi").write_bytes(b"nem valodi video, de a kiterjesztes az")
    return gyoker


def _fajlok(gyoker: Path) -> list[Path]:
    return sorted(p for p in gyoker.rglob("*") if p.is_file())


class TestAKeszlet:
    def test_letrehozas_es_lekerdezes(self, conn, tmp_path):
        keszlet = keszlet_letrehozasa(conn, "Külső lemez", str(tmp_path / "cel"))
        assert keszlet.nev == "Külső lemez"
        assert keszlet.szuro == SZURO_MINDEN
        assert [k.nev for k in keszletek(conn)] == ["Külső lemez"]

    def test_a_nev_kotelezo(self, conn, tmp_path):
        with pytest.raises(ValueError):
            keszlet_letrehozasa(conn, "   ", str(tmp_path / "cel"))

    def test_ismeretlen_szuro_nem_menthető(self, conn, tmp_path):
        with pytest.raises(ValueError):
            keszlet_letrehozasa(conn, "X", str(tmp_path / "cel"), "valami")

    def test_a_modositas_MEGTARTJA_a_nyilvantartast(self, conn, tmp_path, gyujtemeny):
        """Az „Edit Set" nem kezdi elölről a mentést."""
        keszlet = keszlet_letrehozasa(conn, "K", str(tmp_path / "cel"))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        futtasd(conn, keszlet, terv)
        elotte = elmentett_allapot(conn, keszlet.id)
        assert elotte

        keszlet_modositasa(conn, keszlet.id, nev="Új név")
        assert elmentett_allapot(conn, keszlet.id) == elotte
        assert keszlet_nev_szerint(conn, "Új név") is not None

    def test_a_torles_a_nyilvantartast_is_viszi(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(conn, "K", str(tmp_path / "cel"))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        futtasd(conn, keszlet, terv)
        keszlet_torlese(conn, keszlet.id)
        assert keszletek(conn) == ()
        assert elmentett_allapot(conn, keszlet.id) == {}


class TestAzInkrementalitas:
    def test_masodszorra_NINCS_mit_menteni(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(conn, "K", str(tmp_path / "cel"))
        elso = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert elso.fajlok, "elsőre semmit nem talált mentendőnek"
        futtasd(conn, keszlet, elso)

        masodik = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert masodik.fajlok == (), "másodszorra is mentene — nem inkrementális"
        assert masodik.kihagyott == len(elso.fajlok)

    def test_az_UJ_fajl_bekerul(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(conn, "K", str(tmp_path / "cel"))
        futtasd(conn, keszlet, tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny]
        ))
        make_jpeg(gyujtemeny / "nyaralas" / "c.jpg")
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert [f.forras.name for f in terv.fajlok] == ["c.jpg"]
        assert terv.fajlok[0].ok == "uj"

    def test_a_MEGVALTOZOTT_fajl_ujra_bekerul(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(conn, "K", str(tmp_path / "cel"))
        futtasd(conn, keszlet, tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny]
        ))
        valtozott = gyujtemeny / "nyaralas" / "a.jpg"
        make_jpeg(valtozott, size=(200, 150))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert [f.forras.name for f in terv.fajlok] == ["a.jpg"]
        assert terv.fajlok[0].ok == "valtozott"


class TestAMasolas:
    def test_a_mappaszerkezet_megmarad(self, conn, tmp_path, gyujtemeny):
        cel = tmp_path / "cel"
        keszlet = keszlet_letrehozasa(conn, "K", str(cel))
        futtasd(conn, keszlet, tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny]
        ))
        assert (cel / "nyaralas" / "a.jpg").is_file()
        assert (cel / "film.avi").is_file()

    def test_a_picasa_ini_a_kepek_MELLE_kerul(self, conn, tmp_path, gyujtemeny):
        """A jegy 4. pontja: enélkül a mentés nem teljes értékű archívum."""
        cel = tmp_path / "cel"
        keszlet = keszlet_letrehozasa(conn, "K", str(cel))
        futtasd(conn, keszlet, tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny]
        ))
        ini = cel / "nyaralas" / ".picasa.ini"
        assert ini.is_file(), "a .picasa.ini nem ment a képekkel"
        assert "star=yes" in ini.read_text(encoding="utf-8")

    def test_a_MANIFESZT_a_cel_gyokereben_all(self, conn, tmp_path, gyujtemeny):
        cel = tmp_path / "cel"
        keszlet = keszlet_letrehozasa(conn, "K", str(cel))
        futtasd(conn, keszlet, tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny]
        ))
        manifeszt = cel / MANIFESZT_NEVE
        assert manifeszt.is_file()
        sorok = manifeszt.read_text(encoding="utf-8").splitlines()
        assert any(sor.startswith("nyaralas/a.jpg\t") for sor in sorok)

    def test_a_manifeszt_a_TELJES_mentest_irja_le(self, conn, tmp_path, gyujtemeny):
        """A második futás hozzáír, nem felülír — a mentés egésze látszik."""
        cel = tmp_path / "cel"
        keszlet = keszlet_letrehozasa(conn, "K", str(cel))
        futtasd(conn, keszlet, tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny]
        ))
        make_jpeg(gyujtemeny / "nyaralas" / "c.jpg")
        futtasd(conn, keszlet, tervezd_meg(
            conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny]
        ))
        sorok = (cel / MANIFESZT_NEVE).read_text(encoding="utf-8").splitlines()
        nevek = {sor.split("\t", 1)[0] for sor in sorok if sor.strip()}
        assert {"nyaralas/a.jpg", "nyaralas/c.jpg"} <= nevek

    def test_az_ABSZOLUT_ut_nem_logik_ki_a_celbol(self, conn, tmp_path):
        """Gyökér nélkül a fájl a saját mappanevével kerül be — a
        `C:\\…`/`/home/…` kezdet sosem megy át a célra."""
        forras = tmp_path / "valahol" / "mappa"
        forras.mkdir(parents=True)
        make_jpeg(forras / "k.jpg")
        cel = tmp_path / "cel"
        keszlet = keszlet_letrehozasa(conn, "K", str(cel))
        futtasd(conn, keszlet, tervezd_meg(conn, keszlet, [forras / "k.jpg"]))
        assert (cel / "mappa" / "k.jpg").is_file()


class TestASzuro:
    def test_minden_fajltipus(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(
            conn, "K", str(tmp_path / "cel"), SZURO_MINDEN
        )
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert {f.forras.name for f in terv.fajlok} == {"a.jpg", "b.jpg", "film.avi"}

    def test_kepek_videok_nelkul(self, conn, tmp_path, gyujtemeny):
        keszlet = keszlet_letrehozasa(
            conn, "K", str(tmp_path / "cel"), SZURO_KEPEK
        )
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert {f.forras.name for f in terv.fajlok} == {"a.jpg", "b.jpg"}

    def test_csak_fenykepezogep_adatos_JPEG(self, conn, tmp_path):
        """A harmadik állás a FÁJLT nézi, nem a kiterjesztést."""
        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        make_jpeg(gyoker / "gepbol.jpg", camera=("Canon", "EOS 400D"))
        make_jpeg(gyoker / "kezzel.jpg")
        keszlet = keszlet_letrehozasa(
            conn, "K", str(tmp_path / "cel"), SZURO_FENYKEPEZOGEP
        )
        terv = tervezd_meg(conn, keszlet, _fajlok(gyoker), gyokerek=[gyoker])
        assert {f.forras.name for f in terv.fajlok} == {"gepbol.jpg"}

    def test_a_nem_media_fajl_SOHA_nem_kerul_be(self, conn, tmp_path):
        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        (gyoker / "jegyzet.txt").write_text("nem kép", encoding="utf-8")
        keszlet = keszlet_letrehozasa(
            conn, "K", str(tmp_path / "cel"), SZURO_MINDEN
        )
        terv = tervezd_meg(conn, keszlet, _fajlok(gyoker), gyokerek=[gyoker])
        assert terv.fajlok == ()
