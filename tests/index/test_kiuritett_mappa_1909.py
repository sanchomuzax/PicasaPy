"""#1909: a KIÜRÍTETT mappa nem „jelenleg nem elérhető".

## Mit látott a tulajdonos

Törölte egy mappa tartalmát a PicasaPy-ből. A mappa **létezett és
olvasható volt, csak üres**. Ezután a sor bent ragadt a bal hasábban, dőlt
szedéssel, és a buboréksúgó azt állította:

> „Ez a mappa jelenleg nem elérhető (például lecsatolt meghajtó vagy
> hálózati megosztás)."

**Ez valótlan volt** — a meghajtó megvolt, a mappa olvasható volt.

## Az ok, és miért a kód SAJÁT szándéka ellen ment

A `folder_looks_offline` minden üres mappát offline-nak vett, arra a
feltevésre építve, hogy „a kiürített fotómappában rendszerint ott marad
legalább a `.picasa.ini`". A docstringje közben kimondta, hogy a
megkülönböztetés „szándékosan szűk, hogy a »a felhasználó kiürítette a
mappát« eset NE minősüljön offline-nak" — a védelem tehát egy VÉLETLEN
melléktermékre épült, nem magára a különbségre, és élesben megdőlt.

## Amit ez az őr állít

1. a **teljesen üres, de olvasható** mappa (`.picasa.ini` NÉLKÜL) nem
   offline;
2. az **olvashatatlan** mappa (jogosultság elvéve) továbbra is offline;
3. a **nem létező** mappa nem offline (takarítható);
4. a **nem üres** mappa nem offline;
5. a szétválasztás jele a **csatolási határ**, nem egy maradék fájl.
"""

from __future__ import annotations

import os
import stat as stat_module

import pytest

from picasapy.index import sync as sync_module
from picasapy.index.sync import folder_looks_offline


class TestAKiuritettMappa:
    def test_ures_de_olvashato_mappa_NEM_offline(self, tmp_path):
        """A jegy fő pontja: `.picasa.ini` nélkül is csak ÜRES, nem elérhetetlen."""
        ures = tmp_path / "kiuritett"
        ures.mkdir()
        assert folder_looks_offline(ures) is False

    def test_a_maradek_INI_nem_szamit_tobbe(self, tmp_path):
        """A régi viselkedés ezen a maradék-fájlon múlt — most nem múlik rajta."""
        ini_vel = tmp_path / "ini-vel"
        ini_vel.mkdir()
        (ini_vel / ".picasa.ini").write_text("[Picasa]\n", encoding="utf-8")
        ini_nelkul = tmp_path / "ini-nelkul"
        ini_nelkul.mkdir()
        assert folder_looks_offline(ini_vel) is False
        assert folder_looks_offline(ini_nelkul) is False


class TestAmiTOVABBRA_IS_offline:
    def test_az_olvashatatlan_mappa_offline(self, tmp_path):
        """Elvett jog: `scandir` OSError — a levált mount egyik képe."""
        zart = tmp_path / "zart"
        zart.mkdir()
        os.chmod(zart, 0o000)
        try:
            if os.access(zart, os.R_OK):  # root alatt nincs mit mérni
                pytest.skip("a futtató átlát a jogosultságon (root?)")
            assert folder_looks_offline(zart) is True
        finally:
            os.chmod(zart, stat_module.S_IRWXU)

    def test_a_nem_letezo_mappa_NEM_offline(self, tmp_path):
        assert folder_looks_offline(tmp_path / "nincs-ilyen") is False

    def test_a_nem_ures_mappa_NEM_offline(self, tmp_path):
        van_benne = tmp_path / "van"
        van_benne.mkdir()
        (van_benne / "kep.jpg").write_bytes(b"\xff\xd8\xff")
        assert folder_looks_offline(van_benne) is False


class TestACsatolasiHatar:
    """A szétválasztás JELE — ez adja az őr fogát.

    Ha valaki visszaírja a „minden üres mappa offline" szabályt, az 1.
    osztály bukik; ha kiveszi a csatolási-határ ágat, ez bukik.
    """

    def test_az_ELO_csatolasi_pont_meg_uresen_is_offline(
        self, tmp_path, monkeypatch
    ):
        ures = tmp_path / "mount"
        ures.mkdir()
        valodi_stat = sync_module._stat

        def hamis_stat(ut, *args, **kwargs):
            eredmeny = valodi_stat(ut, *args, **kwargs)
            if os.fspath(ut) == os.fspath(ures):
                # más eszköz, mint a szülőé → élő csatolási pont
                return os.stat_result(
                    tuple(eredmeny)[:2] + (eredmeny.st_dev + 1,) + tuple(eredmeny)[3:]
                )
            return eredmeny

        #: #1217/#1375: a MODUL fogantyúját cseréljük, nem a globális
        #: `os.stat`-ot — az minden más modulra átszivárogna.
        monkeypatch.setattr(sync_module, "_stat", hamis_stat)
        assert folder_looks_offline(ures) is True

    def test_az_azonos_eszkozon_ulo_ures_mappa_NEM_offline(self, tmp_path):
        ures = tmp_path / "kozonseges"
        ures.mkdir()
        assert os.stat(ures).st_dev == os.stat(tmp_path).st_dev
        assert folder_looks_offline(ures) is False


class TestAGyokerSzintuProbaTAGABB:
    """#1560 nem sérülhet: a gyökér ürességére továbbra is visszatartunk.

    A két kérdés különbözik, és szándékosan más a szabályuk. A gyökér
    üressége önmagában gyanús — a #1560 mérése szerint épp így néz ki a
    lecsatolt NAS, és a tévedés ára a TELJES index kiürülése volt. Egy
    MAPPA üressége viszont a leggyakoribb esetben azt jelenti, hogy a
    felhasználó kiürítette.
    """

    def test_az_ures_gyoker_visszatart(self, tmp_path):
        gyoker = tmp_path / "mnt" / "photo"
        gyoker.mkdir(parents=True)
        assert sync_module._gyoker_ures_vagy_olvashatatlan(gyoker) is True
        # …miközben ugyanez a mappa mappa-szinten csak ÜRES:
        assert folder_looks_offline(gyoker) is False

    def test_a_nem_ures_gyoker_nem_tart_vissza(self, tmp_path):
        gyoker = tmp_path / "mnt" / "photo"
        gyoker.mkdir(parents=True)
        (gyoker / "kep.jpg").write_bytes(b"\xff\xd8\xff")
        assert sync_module._gyoker_ures_vagy_olvashatatlan(gyoker) is False
