"""Olcsó frissesség-ellenőrzés a rácson látszó mappákra (#1435).

A `folder_freshness` modul Qt-mentes magja. A lényeg a KÖLTSÉG: a
tulajdonos gyűjteménye NAS-on van, mért napló-korláttal (200/mp), ezért a
sweep nem futtathat teljes `sync_folder`-t minden látszó mappára — az
mérésünk szerint fájlonként ~2 műveletbe kerül.

Helyette KÉT fázis:

1. **pecsét** — mappánként PONTOSAN két művelet (a mappa statja és a
   `.picasa.ini` statja); ez elárulja, hogy jött-e/tűnt-e el fájl, és
   változott-e az ini;
2. csak az eltérő pecsétű mappa kap teljes szinkront.

A pecsét NEM veszi észre a helyben átírt fájlt (a mappa mtime-ja ilyenkor
nem változik — lemérve, ld. a jegyet). Azt továbbra is a KIVÁLASZTOTT
mappa teljes újraolvasása fedi le, ami körönként úgyis lefut.
"""

from __future__ import annotations

import os
import time

import pytest

from support.jpeg_factory import make_jpeg


def _oregitsd_a_pecsetet(mappa) -> None:
    """A mappa (és a benne lévő ini) idejét MÚLTBA állítja.

    ⚠️ Miért kell: a fájlidő felbontása platformfüggő. Windowson a
    rendszeróra ~15,6 ms-onként lép, tehát a közvetlenül az írás UTÁN
    vett mtime bitre azonos lehet az írás ELŐTTIVEL. A CI windows-lába
    pontosan ezen bukott el (#1435):

        assert (1787659405455004900, None) != (1787659405455004900, None)

    Ez a segéd NEM tompítja az őrt, hanem HŰBB helyzetet állít elő: a
    valós működésben a tárolt pecsét a legutóbbi indexeléskor készül,
    másodpercekkel-percekkel a felhasználó módosítása előtt — nem
    ugyanabban az óraütemben. Az állítás marad ugyanaz: a valódi
    módosítás megváltoztatja a pecsétet.
    """
    regen = time.time() - 60
    for cel in (mappa, mappa / ".picasa.ini", mappa / "Picasa.ini"):
        if cel.exists():
            os.utime(cel, (regen, regen))


class TestDirectoryStamp:
    @staticmethod
    def _muveletszam(monkeypatch, mappa) -> int:
        """Hány `os.stat` kell egy pecséthez? (CSAK a modul sajátjait
        számoljuk, hogy a pytest belső statjai ne szennyezzék a mérést.)"""
        from picasapy.app import folder_freshness

        hivasok = []
        eredeti = os.stat

        def szamlalo(*args, **kwargs):
            hivasok.append(args[0] if args else None)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(folder_freshness.os, "stat", szamlalo)
        folder_freshness.directory_stamp(mappa)
        monkeypatch.undo()
        return len(hivasok)

    def test_a_szokasos_eset_pontosan_ket_muvelet(self, tmp_path, monkeypatch):
        """A NAS-garancia: `.picasa.ini`-vel rendelkező mappa = 2 művelet.

        Ez a TÖBBSÉGI eset — a PicasaPy maga is ezt a nevet írja."""
        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        (mappa / ".picasa.ini").write_text("[k.jpg]\nstar=yes\n", encoding="utf-8")

        assert self._muveletszam(monkeypatch, mappa) == 2

    def test_a_legrosszabb_eset_harom_muvelet(self, tmp_path, monkeypatch):
        """Ini NÉLKÜLI mappánál mindkét nevet hiába próbáljuk: 3 művelet.

        Ez a FELSŐ korlát — a `SWEEP_FOLDERS_PER_TICK` költségvetése
        ezzel számol (3 × 8 = 24 művelet / 10 mp ≈ 2,4 művelet/mp)."""
        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")

        assert self._muveletszam(monkeypatch, mappa) == 3

    def test_uj_fajl_megvaltoztatja_a_pecsetet(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        _oregitsd_a_pecsetet(mappa)
        elotte = directory_stamp(mappa)

        make_jpeg(mappa / "uj.jpg")

        assert directory_stamp(mappa) != elotte

    def test_torolt_fajl_megvaltoztatja_a_pecsetet(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        make_jpeg(mappa / "masik.jpg")
        _oregitsd_a_pecsetet(mappa)
        elotte = directory_stamp(mappa)

        (mappa / "masik.jpg").unlink()

        assert directory_stamp(mappa) != elotte

    def test_az_ini_valtozasa_megvaltoztatja_a_pecsetet(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        (mappa / ".picasa.ini").write_text("[k.jpg]\nstar=yes\n", encoding="utf-8")
        _oregitsd_a_pecsetet(mappa)
        elotte = directory_stamp(mappa)

        (mappa / ".picasa.ini").write_text(
            "[k.jpg]\nstar=yes\ncaption=uj\n", encoding="utf-8"
        )

        assert directory_stamp(mappa) != elotte

    def test_hianyzo_mappara_none(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        assert directory_stamp(tmp_path / "nincs") is None

    def test_a_REGI_nevu_ini_is_szamit(self, tmp_path):
        """⚠️ A régi Picasa-verziók `Picasa.ini`-t írtak, és a tárolt
        pecsétet készítő `walker._ini_mtime` MINDKÉT nevet ismeri.

        Ha itt csak a `.picasa.ini`-t néznénk, az ilyen mappa pecsétje
        soha nem egyezne a tárolttal — tehát MINDEN körben megkapná a
        drága teljes újraolvasást, és sosem konvergálna. Épp azt a
        NAS-terhelést okozná, amit a jegy tilt."""
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "regi"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        (mappa / "Picasa.ini").write_text("[k.jpg]\nstar=yes\n", encoding="utf-8")

        _, ini_mtime = directory_stamp(mappa)

        assert ini_mtime is not None, (
            "a régi nevű Picasa.ini-t nem vettük észre — a mappa örökre "
            "elavultnak látszana"
        )
        assert ini_mtime == (mappa / "Picasa.ini").stat().st_mtime_ns

    def test_az_uj_nevu_ini_elsobbseget_elvez(self, tmp_path):
        """A `walker._ini_mtime` sorrendjével bitre egyeznünk kell."""
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "mindketto"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        (mappa / "Picasa.ini").write_text("[k.jpg]\nstar=yes\n", encoding="utf-8")
        (mappa / ".picasa.ini").write_text("[k.jpg]\nstar=no\n", encoding="utf-8")

        _, ini_mtime = directory_stamp(mappa)

        assert ini_mtime == (mappa / ".picasa.ini").stat().st_mtime_ns

    def test_a_HELYBEN_atirt_fajlt_a_pecset_NEM_latja(self, tmp_path):
        """A pecsét SZÁNDÉKOS határa — kimondva, hogy ne feltevés legyen.

        Ha egy meglévő fájl tartalma cserélődik ki (azonos név), a mappa
        mtime-ja NEM lép: a könyvtárbejegyzés változatlan. Két művelettel
        ez az eset elvileg sem deríthető ki — ehhez a mappa összes
        fájlját statolni kellene, ami épp a drága út.

        Ezért marad a KIVÁLASZTOTT mappa körönkénti teljes újraolvasása
        (#1275): a felhasználó által nézett mappában ez az eset is
        frissül. A feed többi mappájára nyitott korlát (#1435)."""
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        _oregitsd_a_pecsetet(mappa)
        elotte = directory_stamp(mappa)

        make_jpeg(mappa / "k.jpg", size=(64, 48))  # más tartalom, azonos név

        assert directory_stamp(mappa) == elotte, (
            "a pecsét mégis észrevette a helyben átírt fájlt — ha ez "
            "megbízható, a #1435 korlátja feloldható"
        )


class TestStaleFolders:
    def test_a_valtozatlan_mappa_nem_kerul_bele(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp, stale_folders

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        tarolt = {str(mappa): directory_stamp(mappa)}

        assert stale_folders((str(mappa),), tarolt) == ()

    def test_a_megvaltozott_mappa_bekerul(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp, stale_folders

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        _oregitsd_a_pecsetet(mappa)
        tarolt = {str(mappa): directory_stamp(mappa)}

        make_jpeg(mappa / "uj.jpg")

        assert stale_folders((str(mappa),), tarolt) == (str(mappa),)

    def test_az_ismeretlen_mappa_bekerul(self, tmp_path):
        """Nincs tárolt pecsét — nem tudjuk, friss-e; nézzük meg."""
        from picasapy.app.folder_freshness import stale_folders

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")

        assert stale_folders((str(mappa),), {}) == (str(mappa),)

    def test_az_eltunt_mappa_bekerul(self, tmp_path):
        """A törlést is észre kell venni: a sor takarítása a szinkroné."""
        from picasapy.app.folder_freshness import stale_folders

        hianyzo = str(tmp_path / "nincs")

        assert stale_folders((hianyzo,), {hianyzo: (123, None)}) == (hianyzo,)


class TestKonvergencia:
    """A pecsét az INDEX által tárolt pecséttel áll szemben — ha a kettő
    nem ugyanúgy készül, a mappa örökre elavult marad, és minden körben
    megkapja a drága teljes újraolvasást (a NAS-terhelés, amit tiltunk)."""

    def _stale_sync_utan(self, tmp_path, ini_nev: str | None):
        from picasapy.app.folder_freshness import stale_folders
        from picasapy.index import folder_scan_stamps, open_index, sync_tree

        root = tmp_path / "kepek"
        mappa = root / "a"
        mappa.mkdir(parents=True)
        make_jpeg(mappa / "k.jpg")
        if ini_nev is not None:
            (mappa / ini_nev).write_text("[k.jpg]\nstar=yes\n", encoding="utf-8")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, root)
            tarolt = folder_scan_stamps(conn, (str(mappa),))
        return stale_folders((str(mappa),), tarolt)

    def test_szinkron_utan_nem_elavult_ini_nelkul(self, tmp_path):
        assert self._stale_sync_utan(tmp_path, None) == ()

    def test_szinkron_utan_nem_elavult_uj_ini_nevvel(self, tmp_path):
        assert self._stale_sync_utan(tmp_path, ".picasa.ini") == ()

    def test_szinkron_utan_nem_elavult_REGI_ini_nevvel(self, tmp_path):
        """⚠️ Ez a teszt a H1 hibát fogja: a `Picasa.ini`-s mappa a
        szinkron UTÁN is elavultnak látszott, tehát nem konvergált."""
        assert self._stale_sync_utan(tmp_path, "Picasa.ini") == (), (
            "a régi nevű ini-t tartalmazó mappa a szinkron után is "
            "elavult — minden körben teljes újraolvasást kapna"
        )


class TestNextSweepBatch:
    """Körbeforgó, KORLÁTOZOTT adag — a költség független a könyvtár
    méretétől (a tulajdonosnak 40 000+ képe van)."""

    def test_a_koltseg_korlatos(self):
        from picasapy.app.folder_freshness import next_sweep_batch

        mappak = tuple(f"/m/{i}" for i in range(100))

        adag, _ = next_sweep_batch(mappak, cursor=0, budget=4)

        assert len(adag) == 4

    def test_a_kovetkezo_kor_folytatja(self):
        from picasapy.app.folder_freshness import next_sweep_batch

        mappak = tuple(f"/m/{i}" for i in range(10))

        elso, kurzor = next_sweep_batch(mappak, cursor=0, budget=3)
        masodik, _ = next_sweep_batch(mappak, cursor=kurzor, budget=3)

        assert elso == ("/m/0", "/m/1", "/m/2")
        assert masodik == ("/m/3", "/m/4", "/m/5")

    def test_korbefordul(self):
        from picasapy.app.folder_freshness import next_sweep_batch

        mappak = ("/m/0", "/m/1", "/m/2")

        adag, kurzor = next_sweep_batch(mappak, cursor=2, budget=2)

        assert adag == ("/m/2", "/m/0")
        assert kurzor == 1

    def test_nem_ad_ismetlodest_egy_adagban(self):
        """Kevés mappánál a nagy keret se kérdezze kétszer ugyanazt."""
        from picasapy.app.folder_freshness import next_sweep_batch

        mappak = ("/m/0", "/m/1")

        adag, _ = next_sweep_batch(mappak, cursor=0, budget=10)

        assert adag == ("/m/0", "/m/1")

    def test_ures_listara_ures_adag(self):
        from picasapy.app.folder_freshness import next_sweep_batch

        assert next_sweep_batch((), cursor=0, budget=4) == ((), 0)


@pytest.mark.parametrize("budget", [0, -1])
def test_nulla_keret_nem_kerdez_semmit(budget):
    from picasapy.app.folder_freshness import next_sweep_batch

    adag, _ = next_sweep_batch(("/m/0",), cursor=0, budget=budget)

    assert adag == ()
