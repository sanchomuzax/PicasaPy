"""#910: a fölös paraméterű lánc-tagot az eredeti elejti — mi is.

A `MAX_PARAM_COUNTS` tábla eddig CSAK az írás útvonalán érvényesült
(`ini/document.py`, `edit/save.py`, `ini/filter_guard.py`), a renderelésen
nem: az `autobacklight=1,0.900000;` és a `grain2=1,0.500000;` nálunk
lefutott, az eredetiben viszont tétlen (mérve, #685: ΔE 0,18 = JPEG-zaj,
szemben a mi 5,54 / 2,60 értékünkkel).

Ez a hibaosztály azért veszélyes, mert a MENTETT fájl közben helyes — a
felhasználó csak azt látja, hogy más a kép, mint a Picasában.

A záró üres mező (`grain=1,;`) mérten tolerált, és az ISMERETLEN nevű
szűrő sem esik áldozatul: arra nincs korlátunk, tehát a round-trip elv
nem sérül.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(910)
    return rng.integers(30, 220, size=(48, 64, 3), dtype=np.uint8)


class TestFolosParameteruTagElejtve:
    @pytest.mark.parametrize(
        "lanc,nev",
        [
            ("autobacklight=1,0.900000;", "autobacklight"),
            ("grain2=1,0.500000;", "grain2"),
        ],
    )
    def test_a_kep_bitre_valtozatlan(self, sample, lanc, nev):
        """Mindkettőnek NULLA csúszkája van a `filterdesc.xml` szerint,
        tehát a paraméter fölös — a Picasa a tagot elejti."""
        report = apply_filters(sample, parse_filters(lanc))
        assert np.array_equal(report.image, sample)
        assert nev in report.skipped

    def test_a_lanc_tobbi_tagja_lefut(self, sample):
        """Az elejtés csak az ADOTT tagra vonatkozik — a #301 elve
        (egy hibás tag nem állítja meg a láncot) itt is áll."""
        report = apply_filters(
            sample, parse_filters("autobacklight=1,0.900000;sat=1,0.500000;")
        )
        csak_sat = apply_filters(sample, parse_filters("sat=1,0.500000;"))
        assert np.array_equal(report.image, csak_sat.image)
        assert report.skipped == ("autobacklight",)

    def test_a_felhasznalonak_szolo_indoklas_is_megvan(self, sample):
        """Nem néma kihagyás: a `ChainReport` kimondja az okot — a
        `DEAD_LEGACY_OPS`/`MEASURED_IDLE_OPS` mintájára."""
        report = apply_filters(sample, parse_filters("grain2=1,0.500000;"))
        assert len(report.legacy_warnings) == 1
        assert "grain2" in report.legacy_warnings[0]


class TestAmiTovabbraIsHat:
    @pytest.mark.parametrize("lanc", ["grain2=1;", "grain=1,;", "autobacklight=1;"])
    def test_a_szabalyos_tag_valtozatlanul_fut(self, sample, lanc):
        """A záró ÜRES mező (`grain=1,;`) mérten tolerált — az
        `effective_param_count` nem számolja paraméternek."""
        report = apply_filters(sample, parse_filters(lanc))
        assert not np.array_equal(report.image, sample)
        assert report.skipped == ()

    def test_a_parameteres_szuro_a_sajat_korlatjaig_fut(self, sample):
        """A `sat` korlátja 1 — az egy paraméterrel LEFUT."""
        report = apply_filters(sample, parse_filters("sat=1,0.500000;"))
        assert not np.array_equal(report.image, sample)
        assert report.skipped == ()

    def test_az_ismeretlen_szuro_utja_valtozatlan(self, sample):
        """Ismeretlen névre nincs korlátunk, tehát ez a szabály nem
        nyúlhat hozzá — a kihagyás oka változatlanul az, hogy nem
        ismerjük (round-trip elv)."""
        report = apply_filters(sample, parse_filters("nincsilyen=1,2,3,4,5;"))
        assert np.array_equal(report.image, sample)
        assert report.skipped == ("nincsilyen",)
        assert report.legacy_warnings == ()
