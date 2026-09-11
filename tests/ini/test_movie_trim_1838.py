"""#1838: a videó vágáspontjai a `filters=` láncban.

A formátum MÉRVE van (`src/picasapy/ini/movie_trim.py` docstringje): 64 bites
kisbetűs hex vezető nullák nélkül, az időegység 100 nanoszekundum
(DirectShow `REFERENCE_TIME`), a tokenek a `filters=` lánc tagjai, és a
sorrendjük nem kötött.

Az őr a jegy „Kész, ha" listáját követi, és a **valódi könyvtárból mért három
értékkel** dolgozik (`80252d`, `b40728fd`, `bf0df826`) — nem laborban
gyártott számokkal.
"""

from __future__ import annotations

import pytest
from picasapy.ini.filters import parse_filters, serialize_filters
from picasapy.ini.movie_trim import (
    MovieTrim,
    filters_with_trim,
    format_tick,
    ms_to_ticks,
    parse_tick,
    ticks_to_ms,
    trim_from_filters,
)

#: A tulajdonos könyvtárából mért három érték és a dekódolt másodperc
#: (a modul docstringjének kontroll-mérése).
VALODI = (
    ("80252d", 8_398_125, 0.840),
    ("b40728fd", 3_020_368_125, 302.037),
    ("bf0df826", 3_205_363_750, 320.536),
)


class TestAzErtekOlvasasa:
    @pytest.mark.parametrize("hexa,tick,_masodperc", VALODI)
    def test_a_VALODI_ertekek_dekodolasa(self, hexa, tick, _masodperc):
        assert parse_tick(hexa) == tick

    @pytest.mark.parametrize("hexa,tick,masodperc", VALODI)
    def test_az_IDOEGYSEG_100_nanoszekundum(self, hexa, tick, masodperc):
        """A kontroll-mérés: a videó hosszán belüli másodperc-érték."""
        assert tick / 10_000_000 == pytest.approx(masodperc, abs=0.001)

    def test_a_NAGYBETUS_hex_is_olvashato(self):
        """Idegen fájl írhatja nagybetűvel — olvasni elnézően kell."""
        assert parse_tick("B40728FD") == 3_020_368_125

    @pytest.mark.parametrize("rossz", ["", "   ", "nem-hex", "-5", "12 34"])
    def test_a_ROMLOTT_ertek_nem_vagas(self, rossz):
        """Egy romlott érték nem hiúsíthatja meg a videó megnyitását."""
        assert parse_tick(rossz) is None

    def test_a_0x_eloteg_ELFOGADOTT(self):
        """A `%I64x` a C-ben is elfogadja a `0x` előtagot (strtoul-szemantika),
        tehát nem „romlott érték" — a mi olvasónk se szigorúbb az eredetinél.

        ⚠️ Ez az eset a saját ELSŐ várakozásomat javította: romlottnak vettem,
        pedig a bináris is beolvasná."""
        assert parse_tick("0x1f") == 31

    def test_a_64_BITEN_TULI_ertek_sem(self):
        assert parse_tick("f" * 17) is None


class TestAzErtekIrasa:
    @pytest.mark.parametrize("hexa,tick,_m", VALODI)
    def test_a_kiirt_alak_a_MERT_alak(self, hexa, tick, _m):
        """Kisbetűs hex, vezető nullák nélkül — a 6 és a 8 jegyű is."""
        assert format_tick(tick) == hexa

    def test_a_ROUND_TRIP_pontos(self):
        for hexa, _tick, _m in VALODI:
            assert format_tick(parse_tick(hexa)) == hexa

    def test_az_ms_atvaltas_mindket_iranyban(self):
        assert ticks_to_ms(3_020_368_125) == 302_036
        assert ms_to_ticks(302_036) == 3_020_360_000

    def test_a_64_BITEN_TULI_ertek_iraskor_HIBA(self):
        """Írásnál nem vagyunk elnézőek: azt mi írjuk, ott a hiba a miénk."""
        with pytest.raises(ValueError):
            format_tick(2**64)


class TestALancbolOlvasas:
    def test_a_valodi_lanc_MINDKET_pontja(self):
        """A mintában a `movieend` áll ELÖL — a sorrend nem kötött."""
        trim = trim_from_filters("movieend=b40728fd;moviestart=80252d;")
        assert trim.start == 8_398_125
        assert trim.end == 3_020_368_125

    def test_a_HIANYZO_token_nem_vagas(self):
        """Nem 0 és nem a hossz — a különbség az írásnál is számít."""
        trim = trim_from_filters("moviestart=bf0df826;")
        assert trim.start == 3_205_363_750
        assert trim.end is None
        assert trim.trimmed is True

    def test_vagas_NELKULI_lanc(self):
        trim = trim_from_filters("bw=1;crop64=1,3e803e80;")
        assert trim == MovieTrim()
        assert trim.trimmed is False

    def test_URES_lanc(self):
        assert trim_from_filters("") == MovieTrim()

    def test_a_HIBAS_tag_nem_dob(self):
        """Az olvasó ág elnéző elemzőjét használjuk (#1140)."""
        assert trim_from_filters("moviestart=80252d;ez-nem-tag").start == 8_398_125

    def test_az_ms_alak(self):
        trim = trim_from_filters("moviestart=80252d;movieend=b40728fd;")
        assert trim.start_ms() == 839
        assert trim.end_ms() == 302_036


class TestALancbaIras:
    def test_a_MEGLEVO_tokent_a_helyen_irja_at(self):
        """A sorrend nem rendeződhet át — a fájlt nem mi írtuk."""
        eredmeny = filters_with_trim(
            "movieend=b40728fd;bw=1;moviestart=80252d;",
            MovieTrim(start=8_398_125, end=1_000_000),
        )
        assert eredmeny == "movieend=f4240;bw=1;moviestart=80252d;"

    def test_a_TOBBI_token_erintetlen(self):
        eredmeny = filters_with_trim(
            "bw=1;crop64=1,3e803e80;", MovieTrim(start=8_398_125)
        )
        assert eredmeny.startswith("bw=1;crop64=1,3e803e80;")
        assert eredmeny.endswith("moviestart=80252d;")

    def test_a_None_KIVESZI_a_tokent(self):
        eredmeny = filters_with_trim(
            "moviestart=80252d;bw=1;", MovieTrim(start=None)
        )
        assert eredmeny == "bw=1;"

    def test_mindkét_pont_kivetele(self):
        eredmeny = filters_with_trim(
            "movieend=b40728fd;moviestart=80252d;", MovieTrim()
        )
        assert eredmeny == ""

    def test_UJ_token_a_lanc_vegere_kerul(self):
        eredmeny = filters_with_trim("bw=1;", MovieTrim(start=1, end=2))
        assert eredmeny == "bw=1;moviestart=1;movieend=2;"

    def test_a_lanc_ujra_OLVASHATO(self):
        """Amit írunk, azt a saját olvasónk ugyanannak látja."""
        trim = MovieTrim(start=3_205_363_750, end=3_020_368_125)
        szoveg = filters_with_trim("bw=1;", trim)
        assert trim_from_filters(szoveg) == trim
        #: és a szigorú elemző sem panaszkodik rá (az ÍRÓ ág mércéje)
        assert serialize_filters(parse_filters(szoveg)) == szoveg
