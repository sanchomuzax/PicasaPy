"""#2074: a lemez használható kapacitása és a több lemezre osztás.

## A mért képlet (`0x0066be90`)

```
használható = szektorszám × 2048 − tartalék
```

| mennyiség | érték | cím |
|---|---:|---|
| szektorméret | **2048** | `0x0066bf35` (`push 0x800`) |
| DVD-tartalék | **4 096 000** bájt (2000 szektor) | `0x0066bf50` |
| CD-tartalék | **409 600** bájt (200 szektor) | `0x0066bf58` |
| kétrétegű kapacitás | **8 547 991 552** bájt (`0x1_FD800000`) | `0x0066bed3` |

⚠️ A kétrétegű lemeznél a méret **rögzített**, nem számolt — a bináris
közvetlenül ezt az értéket adja vissza.

## Miért nem „józan ész" szerinti kerek számok

A CD 700 MB-ja és a DVD 4,7 GB-ja marketingszám. A tartalék a lemezzáró
sávé; enélkül az utolsó lemez az írás VÉGÉN bukna el, amikor a
felhasználó már mindent rámásolt.
"""

from __future__ import annotations

import pytest

from picasapy.burn import (
    CD,
    DVD,
    KETRETEGU,
    hasznalhato_kapacitas,
    lemezekre_oszt,
)


class TestAKapacitas:
    """A három küszöb PONTOS bájtszáma — a jegy ezt kéri tételesen."""

    def test_a_ketretegu_ROGZITETT(self):
        assert hasznalhato_kapacitas(KETRETEGU) == 8_547_991_552

    def test_a_DVD_tartaleka_2000_szektor(self):
        #: egy 4,7 GB-os DVD szektorszáma
        szektor = 2_295_104
        assert hasznalhato_kapacitas(DVD, szektorszam=szektor) == (
            szektor * 2048 - 4_096_000
        )

    def test_a_CD_tartaleka_200_szektor(self):
        szektor = 360_000
        assert hasznalhato_kapacitas(CD, szektorszam=szektor) == (
            szektor * 2048 - 409_600
        )

    def test_a_szektormeret_2048(self):
        """Egy szektorral több pontosan 2048 bájttal ad többet."""
        a = hasznalhato_kapacitas(CD, szektorszam=1000)
        b = hasznalhato_kapacitas(CD, szektorszam=1001)
        assert b - a == 2048

    def test_a_tul_kicsi_lemez_NULLA(self):
        """A tartaléknál kisebb lemezre nem fér semmi — negatív méret nincs."""
        assert hasznalhato_kapacitas(CD, szektorszam=10) == 0


class TestALemezekreOsztas:
    def test_ami_belefer_EGY_lemez(self):
        fajlok = [("a", 1000), ("b", 2000)]
        lemezek = lemezekre_oszt(fajlok, kapacitas=10_000)
        assert len(lemezek) == 1
        assert [nev for nev, _ in lemezek[0]] == ["a", "b"]

    def test_a_tullogo_UJ_lemezre_megy(self):
        fajlok = [("a", 6000), ("b", 6000)]
        lemezek = lemezekre_oszt(fajlok, kapacitas=10_000)
        assert [len(lemez) for lemez in lemezek] == [1, 1]

    def test_a_SORREND_megmarad(self):
        """A sorszámozott lemezek („Ez lesz a 3. számú lemez") csak akkor
        értelmesek, ha a sorrend kiszámítható."""
        fajlok = [(betu, 4000) for betu in "abcde"]
        lemezek = lemezekre_oszt(fajlok, kapacitas=10_000)
        assert [nev for lemez in lemezek for nev, _ in lemez] == list("abcde")

    def test_a_lemezmeretnel_NAGYOBB_fajl_sajat_lemezt_kap(self):
        """Nem tűnhet el némán: saját lemezre kerül, és a hívó látja, hogy
        az a lemez túlcsordul."""
        fajlok = [("kicsi", 100), ("ORIAS", 999_999)]
        lemezek = lemezekre_oszt(fajlok, kapacitas=10_000)
        assert ["ORIAS"] in [[nev for nev, _ in lemez] for lemez in lemezek]

    def test_URES_lista_nulla_lemez(self):
        assert lemezekre_oszt([], kapacitas=10_000) == ()


class TestALemezSzam:
    """A felületnek darabszám kell: „Ez lesz a %d. lemez a %d darabból."""

    @pytest.mark.parametrize(
        "osszes, kapacitas, vart",
        [(0, 100, 0), (100, 100, 1), (101, 100, 2), (250, 100, 3)],
    )
    def test_a_becsult_darabszam(self, osszes, kapacitas, vart):
        from picasapy.burn import lemezek_szama

        assert lemezek_szama(osszes, kapacitas) == vart
