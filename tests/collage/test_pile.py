"""A Képkupac (`picturepile`) — méret, „legjobb jelölt" szórás, legyezőszög.

Forrás: `docs/specs/picasa-create-features.md` 1.9.2 és 1.9.12 (#431).
"""

from __future__ import annotations

import math

import pytest

from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.pile import (
    PILE_BASE_RATIO,
    PILE_CANDIDATES,
    pile_layout,
    pile_rotation,
    pile_scale,
    pile_size,
    pile_top_left,
    scatter_centers,
)


class ScriptedRandom:
    """Előre megírt `[0,1)` sorozat — a szórás pontos elvárásához."""

    def __init__(self, values):
        self._values = list(values)
        self.calls = 0

    def uniform01(self) -> float:
        value = self._values[self.calls % len(self._values)]
        self.calls += 1
        return value


# --- Méret ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("index", "expected"),
    [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 0.8995), (10, 0.6801), (100, 0.3333)],
)
def test_pile_scale_a_specifikalt_tablazatot_adja(index, expected):
    assert pile_scale(index) == pytest.approx(expected, abs=5e-5)


def test_pile_scale_egy_alatt_hibat_dob():
    with pytest.raises(ValueError):
        pile_scale(0)


def test_pile_meret_a_valodi_cxf_mintat_reprodukalja():
    """A felhasználó `.cxf`-mintája (spec 1.6): a lap ≈ 1021 képpont széles,
    a kilenc kép `scale` mezője 337/337/337/337/303/280/263/249/238.

    Ez a képlet egyetlen független, valódi mérése — ha ez elromlik, a
    Képkupac mérete nem az eredetié."""
    page_width = 1021
    tenyleges = [pile_size(i, page_width) for i in range(1, 10)]
    assert tenyleges == [337, 337, 337, 337, 303, 280, 263, 249, 238]


def test_pile_meret_a_lap_szelessegenek_harmincharom_szazaleka():
    assert PILE_BASE_RATIO == 0.33
    assert pile_size(1, 1000) == 330


# --- Szórás („legjobb jelölt") ----------------------------------------------


def test_a_szoras_KEPENKENT_OT_jeloltet_sorsol():
    """Ez a jegyben külön kiemelt csapda: nem sima `rand()`.

    Öt jelölt, jelöltenként két véletlen szám (x és y) — tehát képenként
    tíz hívás, akkor is, ha az első képnél még nincs mihez mérni."""
    rng = ScriptedRandom([0.0])
    scatter_centers(3, 1000, 1000, rng)
    assert PILE_CANDIDATES == 5
    assert rng.calls == 3 * PILE_CANDIDATES * 2


def test_a_legmesszebbi_jelolt_nyer():
    """Két kép, kézzel megírt sorozattal.

    `pile_scale(2)` = 1,0, tehát a sáv 0,505 széles, az eltolás 0,2475.
    Az első kép az első jelöltet kapja (nincs mihez mérni). A másodiknál
    az öt jelölt közül a 0,9-es a legtávolabbi, azt kell választania."""
    values = [
        0.0, 0.0,  0.0, 0.0,  0.0, 0.0,  0.0, 0.0,  0.0, 0.0,   # 1. kép
        0.0, 0.0,  0.5, 0.5,  0.9, 0.9,  0.0, 0.9,  0.1, 0.1,   # 2. kép
    ]  # fmt: skip
    first, second = scatter_centers(2, 1000, 1000, ScriptedRandom(values))
    assert first == pytest.approx((247.5, 247.5))
    assert second == pytest.approx((702.0, 702.0))


def test_a_kupac_lazabb_mint_a_sima_veletlen():
    """A viselkedés lényege: az öt jelöltből a legtávolabbi választása
    „kék zajos", laza eloszlást ad. Egy naiv, egyjelöltes szórás csomós
    lesz — ezt a legközelebbi szomszédok legkisebb távolsága mutatja."""

    def legkisebb_tavolsag(points):
        return min(
            math.dist(a, b)
            for i, a in enumerate(points)
            for b in points[i + 1 :]
        )

    best = scatter_centers(20, 1000, 1000, MsvcRandom(2026))
    naiv = scatter_centers(20, 1000, 1000, MsvcRandom(2026), candidates=1)
    assert legkisebb_tavolsag(best) > legkisebb_tavolsag(naiv)


def test_a_sav_a_kepszammal_szelesedik():
    """Kevés képnél a középpontok a lap középső felében maradnak; sok
    képnél a szórás majdnem a teljes lapra kiterjed."""
    kevés = scatter_centers(2, 1000, 1000, ScriptedRandom([0.0]))
    sok = scatter_centers(100, 1000, 1000, ScriptedRandom([0.0]))
    assert kevés[0][0] == pytest.approx(247.5)  # (1 − 0.505) / 2
    assert sok[0][0] < kevés[0][0]


def test_a_kozeppontok_a_lapon_belul_maradnak():
    for point in scatter_centers(30, 800, 600, MsvcRandom(7)):
        assert 0.0 <= point[0] <= 800.0
        assert 0.0 <= point[1] <= 600.0


# --- Forgatás ---------------------------------------------------------------


def test_a_szog_a_lap_HETVEN_szazalekanal_nulla():
    """`fok = u * (18x − 12.6)`, tehát x = 0,7-nél mindig 0."""
    assert pile_rotation(1.0, 700.0, 1000) == pytest.approx(0.0, abs=1e-9)


def test_a_szog_balra_nagyobb_es_negativ():
    """Nem szimmetrikus szórás, hanem enyhe legyezőhatás: a bal szélen
    0…−12,6°, a jobb szélen 0…+5,4°."""
    bal = math.degrees(pile_rotation(1.0, 0.0, 1000))
    jobb = math.degrees(pile_rotation(1.0, 1000.0, 1000))
    assert bal == pytest.approx(-12.6, abs=1e-4)
    assert jobb == pytest.approx(5.4, abs=1e-4)
    assert abs(bal) > abs(jobb)


def test_a_szog_radianban_van():
    """A `.cxf` `theta` mezője radián; a felület `*180/π`-vel írja ki."""
    theta = pile_rotation(1.0, 0.0, 1000)
    assert abs(theta) < math.pi / 8


def test_nulla_veletlennel_nincs_forgatas():
    assert pile_rotation(0.0, 123.0, 1000) == 0.0


# --- Teljes elrendezés ------------------------------------------------------


def test_pile_layout_minden_kepre_ad_helyet():
    places = pile_layout(6, 1000, 750, MsvcRandom(1))
    assert len(places) == 6
    assert [p.index for p in places] == list(range(6))
    assert places[0].size >= places[5].size


def test_pile_layout_azonos_maggal_azonos_eredmeny():
    """A véletlenforrás befecskendezhető, tehát a teszt megismételhető —
    a valós viselkedés (friss mag futásonként) viszont az eredetié marad."""
    a = pile_layout(8, 1000, 750, MsvcRandom(99))
    b = pile_layout(8, 1000, 750, MsvcRandom(99))
    assert a == b


def test_pile_top_left_a_kozeppontbol_a_bal_felso_sarkot_adja():
    """A számított hely a kép KÖZEPÉRE hivatkozik, és a lap koordinátáira
    normalizálódik."""
    assert pile_top_left(500.0, 200, 1000, 1000) == pytest.approx(400.0)
    # fél akkora lapra vetítve minden feleződik
    assert pile_top_left(500.0, 200, 1000, 500) == pytest.approx(200.0)


def test_pile_layout_ervenytelen_bemenet():
    with pytest.raises(ValueError):
        pile_layout(0, 1000, 750, MsvcRandom(1))
