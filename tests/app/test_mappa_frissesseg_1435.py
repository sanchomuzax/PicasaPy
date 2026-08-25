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

import pytest

from support.jpeg_factory import make_jpeg


class TestDirectoryStamp:
    def test_a_pecset_pontosan_ket_muveletbe_kerul(self, tmp_path, monkeypatch):
        """A NAS-garancia: mappánként két fájlrendszer-művelet, nem több."""
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        hivasok = []
        eredeti = os.stat

        def szamlalo(*args, **kwargs):
            hivasok.append(args[0] if args else None)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(os, "stat", szamlalo)

        directory_stamp(mappa)

        assert len(hivasok) == 2, (
            f"a pecsét {len(hivasok)} műveletbe került, nem 2-be — NAS-on "
            f"ez a költség mappánként fizetendő: {hivasok}"
        )

    def test_uj_fajl_megvaltoztatja_a_pecsetet(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        elotte = directory_stamp(mappa)

        make_jpeg(mappa / "uj.jpg")

        assert directory_stamp(mappa) != elotte

    def test_torolt_fajl_megvaltoztatja_a_pecsetet(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        make_jpeg(mappa / "masik.jpg")
        elotte = directory_stamp(mappa)

        (mappa / "masik.jpg").unlink()

        assert directory_stamp(mappa) != elotte

    def test_az_ini_valtozasa_megvaltoztatja_a_pecsetet(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        mappa = tmp_path / "a"
        mappa.mkdir()
        make_jpeg(mappa / "k.jpg")
        (mappa / ".picasa.ini").write_text("[k.jpg]\nstar=yes\n", encoding="utf-8")
        elotte = directory_stamp(mappa)

        (mappa / ".picasa.ini").write_text(
            "[k.jpg]\nstar=yes\ncaption=uj\n", encoding="utf-8"
        )

        assert directory_stamp(mappa) != elotte

    def test_hianyzo_mappara_none(self, tmp_path):
        from picasapy.app.folder_freshness import directory_stamp

        assert directory_stamp(tmp_path / "nincs") is None

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
