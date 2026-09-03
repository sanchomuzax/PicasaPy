"""#2049: a mappa-borító fotó-kupacának elrendezése.

A szabályok mind a `Picasa3.exe`-ből vannak kiolvasva
(`docs/specs/pmp-database.md` 7. szakasz, összeállító: `0x00423780`):

- a kupacba az elemlista első `min(N, 4)` eleme kerül;
- a `0.` elem kerül legfelülre (a rajzoló ciklus visszafelé megy);
- a szórás DETERMINISZTIKUS: `srand(mag)`, MSVCRT-generátor;
- `α = 0.2·(r₁ − 1.5)`, `tₓ = 4·i·uₓ`, `t_y = −i·(4·r₃ + 1)`;
- a LEGALSÓ lapra nincs forgatás — és emiatt eggyel kevesebb `rand()`
  jut rá, ami az egész sorozatot eltolja.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from picasapy.thumbs.album_borito import (
    ARNYEK_ALFA,
    ARNYEK_SUGAR,
    LAPOK_MAXIMUMA,
    befoglalo_meret,
    keszits_boritot,
    kupac_elrendezes,
    mappa_magja,
    msvcrt_rand,
)


class TestAzMsvcrtGenerator:
    def test_az_1_es_maggal_a_KLASSZIKUS_sorozatot_adja(self):
        """Független ellenőrzés: az MSVC `rand()` `srand(1)` utáni első öt
        értéke közismerten 41, 18467, 6334, 26500, 19169."""
        gen = msvcrt_rand(1)
        assert [next(gen) for _ in range(5)] == [41, 18467, 6334, 26500, 19169]

    def test_a_tartomany_15_bites(self):
        gen = msvcrt_rand(0x133475)
        assert all(0 <= next(gen) <= 0x7FFF for _ in range(200))


class TestAKupacElrendezese:
    def test_egyetlen_kepnel_egy_lap_all_kozepen(self):
        lapok = kupac_elrendezes(1, mag=7)
        assert len(lapok) == 1
        assert lapok[0].index == 0
        assert lapok[0].tx == 0.0 and lapok[0].ty == 0.0
        # egyszerre legfelső ÉS legalsó -> forgatás nélkül
        assert lapok[0].szog == 0.0

    def test_legfeljebb_negy_lap_kerul_be(self):
        assert len(kupac_elrendezes(9, mag=7)) == LAPOK_MAXIMUMA == 4

    def test_a_legfelso_lap_eltolas_nelkul_kozepen_all(self):
        felso = kupac_elrendezes(4, mag=7)[0]
        assert felso.index == 0
        assert felso.tx == 0.0 and felso.ty == 0.0

    def test_a_LEGALSO_lap_nem_kap_forgatast(self):
        lapok = kupac_elrendezes(4, mag=7)
        assert lapok[-1].index == 3
        assert lapok[-1].szog == 0.0

    def test_a_forgatas_a_mert_savban_marad(self):
        for lap in kupac_elrendezes(4, mag=123)[:-1]:
            assert -0.1 <= lap.szog < 0.1, f"{lap.index}. lap szöge kilóg"
            assert abs(math.degrees(lap.szog)) <= 5.7296

    def test_az_eltolasok_a_mert_kepletet_kovetik(self):
        for lap in kupac_elrendezes(4, mag=123):
            i = lap.index
            assert abs(lap.tx) <= 4 * i, f"{i}. lap x-eltolása kilóg"
            # t_y = −i·(4·r₃+1), r₃ ∈ [1,2)  ⇒  (−9i, −5i]
            assert -9 * i < lap.ty <= -5 * i or i == 0

    def test_ugyanaz_a_mag_ugyanazt_az_elrendezest_adja(self):
        assert kupac_elrendezes(4, mag=42) == kupac_elrendezes(4, mag=42)

    def test_mas_mag_mas_elrendezest_ad(self):
        assert kupac_elrendezes(4, mag=42) != kupac_elrendezes(4, mag=43)

    def test_ures_kupacra_nincs_lap(self):
        assert kupac_elrendezes(0, mag=7) == ()

    def test_negativ_darabszam_hibat_ad(self):
        with pytest.raises(ValueError):
            kupac_elrendezes(-1, mag=7)


class TestAMappaMagja:
    """Az eredetiben a mag a Picasa TÁROLÓBELI rés-indexe — nálunk ilyen
    nincs, ezért a mappa útvonalából képezzük. A követelmény ugyanaz:
    ugyanaz a mappa mindig ugyanúgy nézzen ki."""

    def test_ugyanaz_az_utvonal_ugyanazt_a_magot_adja(self):
        assert mappa_magja("/kepek/nyar") == mappa_magja("/kepek/nyar")

    def test_mas_utvonal_mas_magot_ad(self):
        assert mappa_magja("/kepek/nyar") != mappa_magja("/kepek/tel")

    def test_a_mag_futasok_kozott_is_allando(self):
        """`hash()` NEM jó: a PYTHONHASHSEED miatt futásonként más lenne,
        és a borító minden indításnál átrendeződne."""
        assert mappa_magja("/kepek/nyar") == 4_211_017_661



def _proba_kep(szin, meret=(40, 30)):
    """Egyszínű BGR kép (szélesség, magasság)."""
    sz, ma = meret
    kep = np.zeros((ma, sz, 3), dtype=np.uint8)
    kep[:, :] = szin
    return kep


class TestABoritoRajzolasa:
    def test_a_mert_arnyek_ertekek(self):
        """Kódból: 0.6×255 = 153 alfa, 5.0 képpont sugár."""
        assert ARNYEK_ALFA == 153
        assert ARNYEK_SUGAR == 5.0

    def test_negy_csatornas_kimenet(self):
        borito = keszits_boritot([_proba_kep((0, 0, 255))], mag=7)
        assert borito.ndim == 3 and borito.shape[2] == 4, "nem RGBA a kimenet"
        assert borito.dtype == np.uint8

    def test_a_borito_KIVAGOTT_alakzat(self):
        """Élő adaton a borító nem téglalap: mintánként 1400–2200
        teljesen átlátszó képpont van benne.

        A saroknál NEM lehet `== 0`-t állítani: az árnyék lefutása odáig
        is elér (a valódi mintákban is), ezért az arányt mérjük."""
        borito = keszits_boritot(
            [_proba_kep((0, 0, 255)), _proba_kep((0, 255, 0)), _proba_kep((255, 0, 0))],
            mag=7,
        )
        alfa = borito[..., 3]
        assert int((alfa == 0).sum()) > 0, "egyetlen teljesen átlátszó képpont sincs"
        # A NÉGY SAROK egyike sem lehet takarva: a kupac kifordított
        # lapjai közül egyik sem ér el odáig.
        for y, x, nev in (
            (0, 0, "bal felső"),
            (0, -1, "jobb felső"),
            (-1, 0, "bal alsó"),
            (-1, -1, "jobb alsó"),
        ):
            assert alfa[y, x] < 128, f"a {nev} sarok takarva van ({alfa[y, x]})"

    def test_reszlegesen_atlatszo_perem_van(self):
        """Élő adaton a képpontok 32,2%-a részlegesen átlátszó — ez
        élsimítással nem magyarázható, csak a lágy árnyékkal."""
        borito = keszits_boritot(
            [_proba_kep((0, 0, 255)), _proba_kep((0, 255, 0))], mag=7
        )
        alfa = borito[..., 3]
        reszleges = int(((alfa > 0) & (alfa < 255)).sum())
        assert reszleges > 0.10 * alfa.size, (
            f"csak {reszleges} részlegesen átlátszó képpont — nincs lágy árnyék"
        )

    def test_van_teljesen_atlatszatlan_resz(self):
        borito = keszits_boritot([_proba_kep((0, 0, 255))], mag=7)
        assert int(borito[..., 3].max()) == 255, "sehol nincs takaró képpont"

    def test_a_meret_a_befoglalo_teglalap_plusz_az_arnyek(self):
        """A vászon a lapok befoglalója; az árnyék ezen TÚL is terjed,
        ezért a kimenet legfeljebb kétszer a sugárral nagyobb."""
        kepek = [_proba_kep((0, 0, 255)) for _ in range(4)]
        lapok = kupac_elrendezes(len(kepek), mag=7)
        sz, ma = befoglalo_meret(lapok, 40, 30)
        borito = keszits_boritot(kepek, mag=7)
        perem = 2 * int(math.ceil(ARNYEK_SUGAR * 2))
        assert sz <= borito.shape[1] <= sz + perem, borito.shape
        assert ma <= borito.shape[0] <= ma + perem, borito.shape

    def test_tobb_kep_NAGYOBB_boritot_ad(self):
        egy = keszits_boritot([_proba_kep((0, 0, 255))], mag=7)
        negy = keszits_boritot([_proba_kep((0, 0, 255)) for _ in range(4)], mag=7)
        assert negy.shape[0] > egy.shape[0], "a kupac nem nőtt a lapokkal"

    def test_ugyanaz_a_mag_ugyanazt_a_kepet_adja(self):
        kepek = [_proba_kep((0, 0, 255)), _proba_kep((0, 255, 0))]
        assert np.array_equal(
            keszits_boritot(kepek, mag=11), keszits_boritot(kepek, mag=11)
        )

    def test_a_LEGELSO_kep_van_felul(self):
        """A `0.` elem kerül legfelülre — a kupac közepén az ő színe áll."""
        piros = _proba_kep((0, 0, 255))
        zold = _proba_kep((0, 255, 0))
        borito = keszits_boritot([piros, zold], mag=7)
        kozep = borito[borito.shape[0] // 2, borito.shape[1] // 2]
        assert kozep[3] == 255
        assert kozep[2] > kozep[1], f"nem a legelső kép van felül: {kozep}"

    def test_ures_listara_hibat_ad(self):
        with pytest.raises(ValueError):
            keszits_boritot([], mag=7)
