"""#649/#626/#3809: a vetett árnyék eltolása a natív képlettel.

A `DropShadowImageOperation` az eltolást így számolja (`0x00bcdea0`,
`docs/specs/filterdesc-registry.md`, „A Polaroid geometriája”):

    dx = floor( (cos(szög·π/180) + 6,7e−06) · távolság + 0,001825 )
    dy = floor( (sin(szög·π/180) + 6,7e−06) · távolság + 0,001825 )

A kerekítés **`floor`** (`0x00bcdece` `call 0x00c0b1e0`). A két apró tag nem
döntetlen-eldöntő, hanem lebegőpontos védelem: a 2,9999… alakban kijövő,
valójában egész szorzatot emeli az egész fölé, mielőtt a `floor` lecsípné.

A #649 még C-kerekítést (`round`) feltételezett; a #3809 helyesbítette.
"""

# rontás-kontroll: a `shadow_offset` `math.floor` helyett a régi C-kerekítéssel
# (`floor(v + 0,5)`, a nullától elfelé) → 10 failed (a jegy táblájának négy
# nem tengelyirányú esete, a `TestAFloorEltero` hat próbája); ugyanekkor a
# `test_polaroid_irany_szin_3420.py` golden-je mindhárom Polaroid-állásban
# bukik. A két kis tag nélkül (`floor(cos·d)`) → 3 failed (a 71%-os hatókör,
# és a `TestAVedelem` 270°-os és 360°-os esete). Ellenőrizve lefuttatva.

from __future__ import annotations

import math

import pytest

from picasapy.render.glimmer_frame_ops import shadow_offset


def _c_round_alak(distance: float, angle: float) -> tuple[int, int]:
    """A #3809 ELŐTTI számítás (C-kerekítés) — a teszt ehhez méri az eltérést."""

    def c_round(v: float) -> int:
        return int(math.floor(v + 0.5)) if v >= 0 else -int(math.floor(-v + 0.5))

    radian = math.radians(angle)
    return (
        c_round((math.cos(radian) + 6.7e-06) * distance + 0.001825),
        c_round((math.sin(radian) + 6.7e-06) * distance + 0.001825),
    )


class TestAJegyTablaja:
    """A #3809 „Kész, ha” első pontja, számra."""

    @pytest.mark.parametrize(
        "distance,angle,vart",
        [
            (3, 85, (0, 2)),
            (3, 100, (-1, 2)),
            (4, 45, (2, 2)),
            (3, 90, (0, 3)),
            (3, 80, (0, 2)),
        ],
    )
    def test_a_floor_os_erteket_adja(self, distance, angle, vart):
        assert shadow_offset(distance, angle) == vart


class TestAFloorEltero:
    """Ezek az esetek a régi C-kerekítéssel MÁST adtak — ez a javítás
    tartalma, számmal."""

    @pytest.mark.parametrize(
        "distance,angle,vart",
        [
            (1, 30, (0, 0)),
            (1, 60, (0, 0)),
            (1, 120, (-1, 0)),
            (3, 30, (2, 1)),
            (3, 85, (0, 2)),
        ],
    )
    def test_a_regi_alak_mast_adott(self, distance, angle, vart):
        assert shadow_offset(distance, angle) == vart
        assert _c_round_alak(distance, angle) != vart, "ez az eset nem tért el"

    def test_a_parok_71_szazaleka_elter(self):
        """A javítás HATÓKÖRE: (távolság 0–30, szög 0–359°) → 7980 / 11160."""
        eltero = sum(
            shadow_offset(d, szog) != _c_round_alak(d, szog)
            for d in range(31)
            for szog in range(360)
        )
        assert eltero == 7980


class TestAVedelem:
    """A két kis tag nélkül a `cos 90°` (6e−17) és a `cos 180°` (−1) körüli
    lebegőpontos zaj a `floor` alatt egy képpontot csíphetne le."""

    @pytest.mark.parametrize(
        "distance,angle,vart",
        [
            (1, 90, (0, 1)),
            (3, 90, (0, 3)),
            (5, 180, (-5, 0)),
            (5, 270, (0, -5)),
            (30, 0, (30, 0)),
            (30, 360, (30, 0)),
        ],
    )
    def test_a_tengelyiranyu_eltolas_egesz(self, distance, angle, vart):
        assert shadow_offset(distance, angle) == vart


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



# A kompozitálás ugyanezt az eltolást használja: `test_dropshadow_nativ_3474.py`
# `test_az_elmosas_a_nativ_ut` a várt képet a `shadow_offset`-ből rakja össze.
