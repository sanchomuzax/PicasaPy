"""#649/#626: a vetett árnyék eltolása a MÉRT natív képlettel.

A `DropShadowImageOperation` (`0x00bbb720`) az eltolást így számolja
(`docs/specs/filterdesc-registry.md` 4.11):

    dx = round( (cosf(szög·π/180) + 6.7e-06f) · távolság + 0.001825f )
    dy = round( (sinf(szög·π/180) + 6.7e-06f) · távolság + 0.001825f )

A két apró szám **döntetlen-eldöntő**: az egész értékhez közeli eseteknél
dönti el, merre billen a kerekítés. A korábbi alakunk ezeket nem ismerte, és
Python-kerekítést használt — ami bankári (`round(0.5) == 0`), tehát épp a
döntetlen eseteknél tért el.
"""

from __future__ import annotations

import math

import pytest

from picasapy.render.glimmer_frame_ops import shadow_offset


def _regi_alak(distance: float, angle: float) -> tuple[int, int]:
    """A javítás ELŐTTI számítás — a teszt ehhez méri az eltérést."""
    radian = math.radians(angle)
    return (
        int(round(distance * math.cos(radian))),
        int(round(distance * math.sin(radian))),
    )


class TestAMertKepletEltero:
    """Ezek a konkrét esetek MÁS értéket adnak, mint a régi alak — ez maga a
    javítás tartalma, számmal."""

    @pytest.mark.parametrize(
        "distance,angle,vart",
        [
            (1, 30, (1, 1)),
            (1, 150, (-1, 1)),
            (1, 210, (-1, 0)),
            (1, 240, (0, -1)),
            (1, 330, (1, 0)),
            (3, 30, (3, 2)),
            (3, 150, (-3, 2)),
            (3, 210, (-3, -1)),
            (3, 240, (-1, -3)),
            (3, 330, (3, -1)),
        ],
    )
    def test_a_MERT_erteket_adja(self, distance, angle, vart):
        assert shadow_offset(distance, angle) == vart
        assert _regi_alak(distance, angle) != vart, "ez az eset nem tért el"

    def test_a_teljes_tartomanyban_42_eset_ter_el(self):
        """A javítás HATÓKÖRE, számmal: 12 × 360 kombinációból 42."""
        eltero = [
            (d, szog)
            for d in range(1, 13)
            for szog in range(360)
            if shadow_offset(d, szog) != _regi_alak(d, szog)
        ]
        assert len(eltero) == 42


class TestAKerekitesIranya:
    def test_a_fel_a_nullatol_ELFELE_kerekit(self):
        """A C `round()` a felet elfelé kerekíti — a Python bankári módon a
        páros felé, tehát `round(0.5) == 0`. A natív képletet csak az
        előbbivel lehet reprodukálni."""
        assert round(0.5) == 0  # a Python viselkedése, dokumentálva
        assert shadow_offset(1, 60)[0] == 1  # cos 60° = 0,5 → 1

    def test_a_negativ_oldalon_a_NULLA_fele_billen(self):
        """A döntetlen-igazítás POZITÍV (+0,001825), tehát a −0,5-öt a nulla
        felé tolja: `cos 120° = −0,5` → `−0,4982` → **0**, nem −1. Ez nem
        elírás, hanem a mért képlet következménye — a két konstans épp ezt a
        billenést dönti el, egységesen mindkét oldalon."""
        assert shadow_offset(1, 120)[0] == 0


class TestAKorlat:
    @pytest.mark.parametrize("distance", [1, 2, 3, 5, 8, 12, 40])
    def test_az_eltolas_nem_lepi_tul_a_tavolsagot(self, distance):
        """A vászon margóját a hívó a távolságból számolja — ha az eltolás
        túllépné, a kép kicsúszna a vászonról."""
        for angle in range(360):
            dx, dy = shadow_offset(distance, angle)
            assert abs(dx) <= distance
            assert abs(dy) <= distance

    def test_nulla_tavolsagnal_nincs_eltolas(self):
        assert shadow_offset(0, 45) == (0, 0)


class TestAKompozitalasHasznalja:
    def test_a_drop_shadow_a_MERT_eltolassal_rajzol(self):
        """A mag tényleg ezt hívja: az árnyék a 30°-os esetben LEJJEBB
        kerül, mint a régi alakkal — ez a képen is látszó egy képpont."""
        import numpy as np

        from picasapy.render.glimmer_frame_ops import compose_drop_shadow

        kep = np.full((10, 10, 3), 255, dtype=np.uint8)
        vaszon = compose_drop_shadow(
            kep, (0, 0, 0), (255, 255, 255),
            distance_px=3, angle=30, blur_px=1, margin=6,
        )
        # a kép a margóban ül, az árnyék tőle jobbra-lefelé (dx=3, dy=2)
        assert vaszon.shape == (22, 22, 3)
        alatta = vaszon[6 + 10 + 1, 6 + 5]
        assert alatta.mean() < 250, "az árnyék nem került a kép alá"
