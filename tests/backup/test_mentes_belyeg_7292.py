"""#7292: a mentés a készlet-bélyeget a `.picasa.ini`-ből olvassa és oda írja.

Az eredeti Picasa a mentésben nem a képfájlt nézi, hanem a kép
`.picasa.ini`-szakaszának két kulcsát: a sima `backuphash`-t és a
`BKTag <készletnév>-backuphash` társkulcsot (`docs/specs/biztonsagi-mentes.md`
9.2). Egy metaadat-szerkesztés (felirat, csillag, forgatás ...) a sima
kulcsot új értékre írja, ettől a kép újra mentendő, pedig a képfájl
változatlan.

⚠️ Ez a fájl a MŰKÖDÉST méri (terv, ini-tartalom), a vizuális megjelenést
nem érinti.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from picasapy.backup import (
    belyegezd,
    futtasd,
    keszlet_kulcs,
    keszlet_modositasa,
    tervezd_meg,
)
from picasapy.backup import futtatas
from picasapy.index import open_index
from picasapy.index.backup_sets import (
    jegyezd_fel_az_elmentettet,
    keszlet_letrehozasa,
    keszlet_nev_szerint,
)
from picasapy.ini import (
    backuphash_for_local_datetime,
    load_document,
    update_document,
    with_backuphash,
)
from picasapy.ini.names import INI_NAME, LEGACY_INI_NAME
from support.jpeg_factory import make_jpeg

_KESZLET = "Heti mentés"
_KULCS = keszlet_kulcs(_KESZLET)


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


@pytest.fixture
def gyoker(tmp_path) -> Path:
    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
    (gyoker / "nyaralas" / INI_NAME).write_text(
        "[a.jpg]\nstar=yes\nbackuphash=100\n", encoding="utf-8"
    )
    return gyoker


def _fajlok(gyoker: Path) -> list[Path]:
    return sorted(p for p in gyoker.rglob("*.jpg") if p.is_file())


def _tervezz(conn, keszlet, gyoker):
    return tervezd_meg(conn, keszlet, _fajlok(gyoker), gyokerek=[gyoker])


def _ment(conn, keszlet, gyoker):
    futtasd(conn, keszlet, _tervezz(conn, keszlet, gyoker))


def _ertek(gyoker: Path, fajl: str, kulcs: str) -> str | None:
    szakasz = load_document(gyoker / "nyaralas" / INI_NAME).section(fajl)
    return None if szakasz is None else szakasz.get(kulcs)


def _mas_belyeg(eddigi: str | None) -> datetime:
    """Egy időpont, amelynek a lenyomata más, mint az `eddigi` (determinisztikus)."""
    alap = datetime(2026, 1, 1, 12, 0, 0)
    for lepes in range(200):
        mikor = alap + timedelta(seconds=lepes * 7)
        if str(backuphash_for_local_datetime(mikor)) != eddigi:
            return mikor
    raise AssertionError("nem találtam eltérő lenyomatot")


def _szerkeszt(gyoker: Path, fajl: str, mikor: datetime) -> None:
    """Amit a PicasaPy egy felirat-szerkesztéskor tesz: felirat + új `backuphash`."""
    update_document(
        gyoker / "nyaralas" / INI_NAME,
        lambda d: with_backuphash(
            d.with_value(fajl, "caption", "új felirat"), fajl, mikor
        ),
    )


@pytest.fixture
def keszlet(conn, tmp_path):
    return keszlet_letrehozasa(conn, _KESZLET, str(tmp_path / "cel"))


class TestAMentesAKeszletBelyegetIrja:
    def test_mentes_utan_a_ket_kulcs_EGYEZIK_es_nem_nulla(
        self, conn, keszlet, gyoker
    ):
        _ment(conn, keszlet, gyoker)
        for fajl in ("a.jpg", "b.jpg"):
            sima = _ertek(gyoker, fajl, "backuphash")
            keszletes = _ertek(gyoker, fajl, _KULCS)
            assert sima is not None, f"{fajl}: nincs sima backuphash"
            assert keszletes == sima, f"{fajl}: a két kulcs eltér"
            assert int(sima) not in (0, 0xFFFF)

    def test_a_meglevo_sima_backuphash_ERTEKE_megmarad(
        self, conn, keszlet, gyoker
    ):
        """Hiányzik vagy 0 esetén jön új bélyeg; a meglévő nem íródik át."""
        _ment(conn, keszlet, gyoker)
        assert _ertek(gyoker, "a.jpg", "backuphash") == "100"
        assert _ertek(gyoker, "a.jpg", _KULCS) == "100"

    def test_a_nulla_sima_backuphash_helyere_uj_belyeg_kerul(
        self, conn, keszlet, gyoker
    ):
        (gyoker / "nyaralas" / INI_NAME).write_text(
            "[a.jpg]\nbackuphash=0\n", encoding="utf-8"
        )
        _ment(conn, keszlet, gyoker)
        sima = _ertek(gyoker, "a.jpg", "backuphash")
        assert sima not in (None, "0")
        assert _ertek(gyoker, "a.jpg", _KULCS) == sima

    def test_a_belyegzes_a_KEPFAJL_mtime_jat_nem_valtoztatja(
        self, conn, keszlet, gyoker
    ):
        """A kép mtime-ja a nyilvántartás döntésének része, és az eredeti
        fényképet sem írjuk át: a bélyeg csak az ini-be megy."""
        elotte = {k.name: k.stat().st_mtime_ns for k in _fajlok(gyoker)}
        _ment(conn, keszlet, gyoker)
        utana = {k.name: k.stat().st_mtime_ns for k in _fajlok(gyoker)}
        assert utana == elotte

    def test_a_tobbi_kulcs_es_a_kodolas_NEM_serul(self, conn, keszlet, gyoker):
        _ment(conn, keszlet, gyoker)
        assert _ertek(gyoker, "a.jpg", "star") == "yes"

    def test_a_mentes_utan_a_terv_ures(self, conn, keszlet, gyoker):
        _ment(conn, keszlet, gyoker)
        terv = _tervezz(conn, keszlet, gyoker)
        assert terv.fajlok == ()
        assert terv.kihagyott == 2

    def test_az_archivalt_ini_mar_a_belyeggel_kerul_a_celba(
        self, conn, keszlet, gyoker, tmp_path
    ):
        """Az archívum ini-je a mentés UTÁNI állapot: a visszaállított
        mappa is tudja, hogy a kép el van mentve."""
        _ment(conn, keszlet, gyoker)
        archivalt = load_document(tmp_path / "cel" / "nyaralas" / INI_NAME)
        assert archivalt.section("b.jpg").get(_KULCS) is not None

    def test_a_belyeg_a_nulla_es_a_FFFF_erteket_SOHA_nem_kapja(
        self, conn, keszlet, gyoker, monkeypatch
    ):
        """A 0 „soha nem mentett”, a 0xFFFF „sosem mentendő”: egy véletlen
        XOR-találat egyik jelentést sem kaphatja meg."""
        for hamis in (0, 0xFFFF):
            monkeypatch.setattr(
                "picasapy.backup.belyeg.backuphash_for_local_datetime",
                lambda _mikor, hamis=hamis: hamis,
            )
            (gyoker / "nyaralas" / INI_NAME).write_text(
                "[b.jpg]\nstar=yes\n", encoding="utf-8"
            )
            belyegezd(_KESZLET, [gyoker / "nyaralas" / "b.jpg"])
            sima = int(_ertek(gyoker, "b.jpg", "backuphash"))
            assert sima not in (0, 0xFFFF)
            assert int(_ertek(gyoker, "b.jpg", _KULCS)) == sima


class TestAMetaadatSzerkesztesUjraMentendoVeszi:
    def test_a_felirat_szerkesztese_utan_a_terv_1_tetel(
        self, conn, keszlet, gyoker
    ):
        """A #7290 M2 mérése: ez eddig 0 tétel volt."""
        _ment(conn, keszlet, gyoker)
        _szerkeszt(gyoker, "a.jpg", _mas_belyeg(_ertek(gyoker, "a.jpg", "backuphash")))

        terv = _tervezz(conn, keszlet, gyoker)
        assert [f.forras.name for f in terv.fajlok] == ["a.jpg"]
        assert terv.fajlok[0].ok == "valtozott"
        assert terv.kihagyott == 1

    def test_az_ujramentes_utan_ismet_naprakesz(self, conn, keszlet, gyoker):
        _ment(conn, keszlet, gyoker)
        _szerkeszt(gyoker, "a.jpg", _mas_belyeg(_ertek(gyoker, "a.jpg", "backuphash")))
        _ment(conn, keszlet, gyoker)

        assert _tervezz(conn, keszlet, gyoker).fajlok == ()
        assert _ertek(gyoker, "a.jpg", _KULCS) == _ertek(
            gyoker, "a.jpg", "backuphash"
        )

    def test_az_ujramentes_az_UJ_felirattal_viszi_at_az_ini_t(
        self, conn, keszlet, gyoker, tmp_path
    ):
        _ment(conn, keszlet, gyoker)
        _szerkeszt(gyoker, "a.jpg", _mas_belyeg(_ertek(gyoker, "a.jpg", "backuphash")))
        _ment(conn, keszlet, gyoker)

        archivalt = load_document(tmp_path / "cel" / "nyaralas" / INI_NAME)
        assert archivalt.section("a.jpg").get("caption") == "új felirat"

    def test_a_kozvetlen_backuphash_csere_is_ujra_mentendo(
        self, conn, keszlet, gyoker
    ):
        """A brief szerinti forgatókönyv: `backuphash=100` -> mentés ->
        felirat és `backuphash=200`."""
        _ment(conn, keszlet, gyoker)
        update_document(
            gyoker / "nyaralas" / INI_NAME,
            lambda d: d.with_value("a.jpg", "caption", "x").with_value(
                "a.jpg", "backuphash", "200"
            ),
        )
        assert [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok] == [
            "a.jpg"
        ]

    def test_a_nem_szerkesztett_kep_NEM_kerul_vissza(self, conn, keszlet, gyoker):
        _ment(conn, keszlet, gyoker)
        _szerkeszt(gyoker, "a.jpg", _mas_belyeg(_ertek(gyoker, "a.jpg", "backuphash")))
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert "b.jpg" not in nevek

    def test_a_kivulrol_modositott_kepfajl_tovabbra_is_ujra_mentendo(
        self, conn, keszlet, gyoker
    ):
        """A (méret, mtime) ellenőrzés KIEGÉSZÍTÉSKÉNT marad: az eredeti a
        kívülről módosított fájlt nem veszi észre, mi igen."""
        _ment(conn, keszlet, gyoker)
        make_jpeg(gyoker / "nyaralas" / "b.jpg", size=(200, 150))
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert nevek == ["b.jpg"]


class TestAzEredetiPicasaBelyege:
    def test_egyezo_kulcsokkal_a_terv_NULLA(self, conn, keszlet, gyoker):
        """Az eredeti Picasa által mentett mappa: nincs nyilvántartás az
        indexben, de a két kulcs egyezik, tehát a kép naprakész."""
        (gyoker / "nyaralas" / INI_NAME).write_text(
            f"[a.jpg]\nbackuphash=40037\n{_KULCS}=40037\n"
            f"[b.jpg]\nbackuphash=40037\n{_KULCS}=40037\n",
            encoding="utf-8",
        )
        terv = _tervezz(conn, keszlet, gyoker)
        assert terv.fajlok == ()
        assert terv.kihagyott == 2

    def test_eltero_kulcsok_mentendok(self, conn, keszlet, gyoker):
        (gyoker / "nyaralas" / INI_NAME).write_text(
            f"[a.jpg]\nbackuphash=40038\n{_KULCS}=40037\n"
            f"[b.jpg]\nbackuphash=40037\n{_KULCS}=40037\n",
            encoding="utf-8",
        )
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert nevek == ["a.jpg"]

    def test_a_nulla_keszletkulcs_soha_nem_mentett(self, conn, keszlet, gyoker):
        (gyoker / "nyaralas" / INI_NAME).write_text(
            f"[a.jpg]\nbackuphash=40037\n{_KULCS}=0\n"
            f"[b.jpg]\nbackuphash=40037\n{_KULCS}=40037\n",
            encoding="utf-8",
        )
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert nevek == ["a.jpg"]

    def test_a_hianyzo_keszletkulcs_mentendo(self, conn, keszlet, gyoker):
        (gyoker / "nyaralas" / INI_NAME).write_text(
            "[a.jpg]\nbackuphash=40037\n", encoding="utf-8"
        )
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert "a.jpg" in nevek

    def test_a_0xFFFF_keszletkulcs_KIHAGY(self, conn, keszlet, gyoker):
        (gyoker / "nyaralas" / INI_NAME).write_text(
            f"[a.jpg]\nbackuphash=1\n{_KULCS}=65535\n", encoding="utf-8"
        )
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert "a.jpg" not in nevek

    def test_a_0xFFFF_a_nyilvantartas_valtozasa_mellett_is_kihagy(
        self, conn, keszlet, gyoker
    ):
        (gyoker / "nyaralas" / INI_NAME).write_text(
            f"[a.jpg]\nbackuphash=1\n{_KULCS}=65535\n", encoding="utf-8"
        )
        jegyezd_fel_az_elmentettet(
            conn, keszlet.id, [(str(gyoker / "nyaralas" / "a.jpg"), 1, 1)]
        )
        conn.commit()
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert "a.jpg" not in nevek

    def test_a_masik_keszlet_belyege_NEM_szamit(self, conn, keszlet, gyoker, tmp_path):
        """A bélyeg készletenként külön él: az egyik készlet mentése a
        másikat nem teszi naprakésszé."""
        _ment(conn, keszlet, gyoker)
        masik = keszlet_letrehozasa(conn, "Másik", str(tmp_path / "cel2"))
        terv = _tervezz(conn, masik, gyoker)
        assert {f.forras.name for f in terv.fajlok} == {"a.jpg", "b.jpg"}


class TestARegiNyilvantartasNemMentUjraFolosleg:
    def test_a_regi_nyilvantartasu_szerkesztetlen_kep_marad_elmentett(
        self, conn, keszlet, gyoker
    ):
        """Az ezen változtatás ELŐTT mentett, azóta nem szerkesztett kép
        (nincs sima `backuphash`, nincs készletkulcs) nem megy újra."""
        (gyoker / "nyaralas" / INI_NAME).write_text(
            "[a.jpg]\nstar=yes\n", encoding="utf-8"
        )
        for kep in _fajlok(gyoker):
            allapot = kep.stat()
            jegyezd_fel_az_elmentettet(
                conn, keszlet.id, [(str(kep), allapot.st_size, allapot.st_mtime_ns)]
            )
        conn.commit()
        assert _tervezz(conn, keszlet, gyoker).fajlok == ()

    def test_a_regi_nyilvantartasu_de_azota_szerkesztett_kep_ujra_mentendo(
        self, conn, keszlet, gyoker
    ):
        """Van sima `backuphash`, de nincs készletkulcs: nem tudható, hogy a
        szerkesztés a mentés előtt vagy után történt, ezért a kép mentendő
        (adatvédelem: inkább egyszer fölösleges másolat)."""
        for kep in _fajlok(gyoker):
            allapot = kep.stat()
            jegyezd_fel_az_elmentettet(
                conn, keszlet.id, [(str(kep), allapot.st_size, allapot.st_mtime_ns)]
            )
        conn.commit()
        # a gyoker fixture `a.jpg`-jén `backuphash=100` áll
        nevek = [f.forras.name for f in _tervezz(conn, keszlet, gyoker).fajlok]
        assert nevek == ["a.jpg"]


class TestCsakASikeresenMasoltFajlKapBelyeget:
    def test_a_bukott_masolas_fajlja_belyeg_nelkul_marad(
        self, conn, keszlet, gyoker, monkeypatch
    ):
        eredeti = futtatas._masol

        def hamis(forras, cel, *args, **kwargs):
            if Path(forras).name == "b.jpg":
                raise OSError("a cél nem írható")
            return eredeti(forras, cel, *args, **kwargs)

        monkeypatch.setattr(futtatas, "_masol", hamis)
        masoltak = futtasd(conn, keszlet, _tervezz(conn, keszlet, gyoker))

        assert [p.name for p in masoltak] == ["a.jpg"]
        assert _ertek(gyoker, "a.jpg", _KULCS) is not None
        assert _ertek(gyoker, "b.jpg", _KULCS) is None, (
            "a le nem másolt fájl bélyeget kapott: a következő futás "
            "elmentettnek hinné"
        )

    def test_a_megszakitott_futas_a_hatralevoket_nem_belyegzi(
        self, conn, keszlet, gyoker
    ):
        hivasok = iter([False, True, True])
        futtasd(
            conn, keszlet, _tervezz(conn, keszlet, gyoker),
            megszakitva=lambda: next(hivasok),
        )
        assert _ertek(gyoker, "a.jpg", _KULCS) is not None
        assert _ertek(gyoker, "b.jpg", _KULCS) is None

    def test_az_ini_iras_hibaja_nem_buktatja_a_mentest(
        self, conn, keszlet, gyoker, monkeypatch
    ):
        def hibas(*_args, **_kwargs):
            raise PermissionError("írásvédett mappa")

        monkeypatch.setattr("picasapy.backup.belyeg.update_document", hibas)
        masoltak = futtasd(conn, keszlet, _tervezz(conn, keszlet, gyoker))
        assert len(masoltak) == 2


class TestAKeszletAtnevezese:
    def test_az_osszes_kepszakasz_kulcsa_atnevezodik(
        self, conn, keszlet, gyoker
    ):
        _ment(conn, keszlet, gyoker)
        keszlet_modositasa(conn, keszlet.id, nev="Éves mentés")

        ujkulcs = keszlet_kulcs("Éves mentés")
        for fajl in ("a.jpg", "b.jpg"):
            assert _ertek(gyoker, fajl, _KULCS) is None, (
                f"{fajl}: a régi nevű kulcs megmaradt"
            )
            assert _ertek(gyoker, fajl, ujkulcs) == _ertek(
                gyoker, fajl, "backuphash"
            )

    def test_atnevezes_utan_a_terv_tovabbra_is_ures(
        self, conn, keszlet, gyoker
    ):
        _ment(conn, keszlet, gyoker)
        keszlet_modositasa(conn, keszlet.id, nev="Éves mentés")
        atnevezett = keszlet_nev_szerint(conn, "Éves mentés")
        assert _tervezz(conn, atnevezett, gyoker).fajlok == ()

    def test_a_masik_keszlet_kulcsa_nem_erintett(self, conn, keszlet, gyoker, tmp_path):
        _ment(conn, keszlet, gyoker)
        masik = keszlet_letrehozasa(conn, "Másik", str(tmp_path / "cel2"))
        _ment(conn, masik, gyoker)

        keszlet_modositasa(conn, keszlet.id, nev="Éves mentés")
        assert _ertek(gyoker, "a.jpg", keszlet_kulcs("Másik")) is not None

    def test_a_nem_nevet_erinto_modositas_nem_nyul_az_ini_hez(
        self, conn, keszlet, gyoker
    ):
        _ment(conn, keszlet, gyoker)
        elotte = (gyoker / "nyaralas" / INI_NAME).read_bytes()
        keszlet_modositasa(conn, keszlet.id, szuro="kepek")
        assert (gyoker / "nyaralas" / INI_NAME).read_bytes() == elotte

    def test_az_azonos_nevre_valo_modositas_nem_nyul_az_ini_hez(
        self, conn, keszlet, gyoker
    ):
        _ment(conn, keszlet, gyoker)
        elotte = (gyoker / "nyaralas" / INI_NAME).read_bytes()
        keszlet_modositasa(conn, keszlet.id, nev=_KESZLET)
        assert (gyoker / "nyaralas" / INI_NAME).read_bytes() == elotte


class TestARegiPicasaIniNemIrodikFelul:
    def test_a_csak_Picasa_ini_mappa_nem_kap_uj_fajlt(
        self, conn, keszlet, tmp_path
    ):
        """A régi `Picasa.ini` SOHA nem írási cél (#4839): bélyeget nem
        írunk bele, és helyette sem hozunk létre `.picasa.ini`-t."""
        mappa = tmp_path / "regi"
        mappa.mkdir()
        kep = mappa / "k.jpg"
        make_jpeg(kep)
        (mappa / LEGACY_INI_NAME).write_bytes(b"[k.jpg]\r\nstar=yes\r\n")

        futtasd(conn, keszlet, tervezd_meg(conn, keszlet, [kep], gyokerek=[tmp_path]))

        assert not (mappa / INI_NAME).exists()
        assert (mappa / LEGACY_INI_NAME).read_bytes() == b"[k.jpg]\r\nstar=yes\r\n"

    def test_a_regi_ini_mappa_a_nyilvantartasra_tamaszkodik(
        self, conn, keszlet, tmp_path
    ):
        """Bélyeg híján a döntés a nyilvántartásé: második futás 0 tétel,
        akkor is, ha a régi ini-ben van sima `backuphash`."""
        mappa = tmp_path / "regi"
        mappa.mkdir()
        kep = mappa / "k.jpg"
        make_jpeg(kep)
        (mappa / LEGACY_INI_NAME).write_bytes(b"[k.jpg]\r\nbackuphash=7\r\n")

        futtasd(conn, keszlet, tervezd_meg(conn, keszlet, [kep], gyokerek=[tmp_path]))
        masodik = tervezd_meg(conn, keszlet, [kep], gyokerek=[tmp_path])
        assert masodik.fajlok == ()
