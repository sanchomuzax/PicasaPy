"""#2008: a Picasa 2 korabeli, ötszámos `crop=` alak.

## Amit a bináris ad — és amit NEM

* **AD**: a téglalap a **2–5. szám**. A forgató (`FUN_009b4c80`)
  forrás-mutatója `esp0+0x24`, ami pontosan a 2. `%d` rekesze
  (`0x004223eb: lea ecx,[esp+0x2c]`, `esp = esp0−8`).
* **AD**: a forgatás a lánc `rotate(N)` tokenjéből jön, **negálva**
  (`FUN_0042c830` + `neg eax`), nem az öt szám egyikéből.
* **NEM AD**: az **1. mező** jelentését. A forgatás nem onnan jön, a
  téglalapnak nem része — a szerepe nyitott.
* **NEM AD**: a régi számok **egységét**. Hogy képpont-e vagy a `crop64`
  16 bites skálája, nincs mérve — ezért a modul nyers számokat ad, és nem
  skáláz. Egy találgatott szorzó némán rossz vágást adna.
"""

from __future__ import annotations

import pytest

from picasapy.ini.legacy_crop import (
    forgatott_teglalap,
    parse_legacy_crop,
    rotate_lepesek,
)


class TestFelismeres:
    def test_az_otszamos_alak(self):
        crop = parse_legacy_crop("100,200,300,400,1;")
        assert crop is not None
        assert (crop.elso, crop.bal, crop.fent, crop.jobb, crop.lent) == (
            100,
            200,
            300,
            400,
            1,
        )

    def test_a_teglalap_a_2_5_szam(self):
        """A MÉRT szereposztás — nem az első négy!"""
        crop = parse_legacy_crop("9,10,20,30,40;")
        assert crop.teglalap == (10, 20, 30, 40)

    def test_a_pontosvesszo_elhagyhato(self):
        assert parse_legacy_crop("1,2,3,4,5") is not None

    @pytest.mark.parametrize(
        "ertek",
        [
            "rect64(45930000ba03defe)",   # a MAI alak
            "45930000ba03defe",           # csupasz hex
            "1,2,3,4",                    # csak négy szám
            "1,2,3,4,5,6",                # hat
            "",
            "abc",
        ],
    )
    def test_ami_NEM_regi_alak(self, ertek):
        """`None`, nem kivétel — a hívó ezután próbálja a `decode_rect64`-et."""
        assert parse_legacy_crop(ertek) is None

    def test_a_negativ_szam_is_atmegy(self):
        """A bináris `%d`-t olvas, ami előjeles."""
        crop = parse_legacy_crop("-1,0,0,10,10;")
        assert crop.elso == -1


class TestForgatasToken:
    def test_a_lancbol_kiolvassa(self):
        assert rotate_lepesek("autolight=1;rotate(3);crop64=1,ab;") == 3

    def test_nincs_token(self):
        assert rotate_lepesek("autolight=1;") == 0

    def test_ures_lanc(self):
        assert rotate_lepesek("") == 0

    def test_negativ_ertek(self):
        assert rotate_lepesek("rotate(-1)") == -1


class TestForgatas:
    BEFOGLALO = (0, 0, 100, 60)   # 100 × 60

    def test_nulla_lepes_valtozatlan(self):
        t = (10, 20, 30, 40)
        assert forgatott_teglalap(t, 0, self.BEFOGLALO) == t

    def test_negy_lepes_visszaad_onmagat(self):
        """Négy negyedfordulat = teljes kör."""
        t = (10, 20, 30, 40)
        assert forgatott_teglalap(t, 4, self.BEFOGLALO) == t

    def test_a_NEGATIV_lepesszam_is_ertelmes(self):
        """A bináris 4 szerint pozitívra hozza (`shr edx,2` idióma) —
        a −1 tehát ugyanaz, mint a +3."""
        t = (10, 20, 30, 40)
        assert forgatott_teglalap(t, -1, self.BEFOGLALO) == forgatott_teglalap(
            t, 3, self.BEFOGLALO
        )

    def test_egy_lepes_UTAN_mas(self):
        t = (10, 20, 30, 40)
        assert forgatott_teglalap(t, 1, self.BEFOGLALO) != t
