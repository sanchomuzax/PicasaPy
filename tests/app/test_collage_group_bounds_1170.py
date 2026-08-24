"""#1170: a csoport-elem befoglaló téglalapja LAPEGYSÉGBEN.

A `collagepanel/groupnode` az eredetiben egy körvonalas téglalap, aminek a
tényleges mérete „a kijelölés változásakor áll be"
(`docs/specs/picasa-kollazs-felulet.md` **2/b.4**). Nálunk ez a kijelölt
csomópontok közös befoglaló téglalapja.

⚠️ **Az egység lapegység, nem képpont** — a vászon szorozza fel. Aki
képpontban gondolkodik, az álló formátumon némán elcsúszik.

⚠️ **A forgatott csomópont befoglalója NAGYOBB a doboznál.** 45°-ra
forgatott négyzet befoglalója `oldal * sqrt(2)`; aki a `width`/`height`
mezőt veszi, a sarkokat kihagyja a keretből.
"""

from __future__ import annotations

import math

import pytest

from picasapy.app.collage_model import (
    GROUP_MIN_SELECTION,
    CollageNode,
    group_bounds,
)


def _node(cx, cy, w=100.0, h=100.0, theta=0.0, selected=False):
    return CollageNode(
        path=f"/k/{cx}-{cy}.jpg",
        center_x=cx,
        center_y=cy,
        width=w,
        height=h,
        theta=theta,
        selected=selected,
    )


class TestKuszob:
    def test_a_kuszob_ketto(self):
        """Az eredeti a CSOPORT-állapotra kapcsol — egyetlen kép nem csoport."""
        assert GROUP_MIN_SELECTION == 2

    def test_kijeloles_nelkul_nincs_doboz(self):
        assert group_bounds([_node(100, 100), _node(300, 300)]) is None

    def test_egyetlen_kijelolt_kep_nem_csoport(self):
        nodes = [_node(100, 100, selected=True), _node(300, 300)]
        assert group_bounds(nodes) is None

    def test_ures_listan_sem_hibazik(self):
        assert group_bounds([]) is None


class TestBefoglalo:
    def test_ket_kijelolt_kep_kozos_dobozt_kap(self):
        nodes = [
            _node(100, 100, w=100, h=100, selected=True),
            _node(300, 200, w=100, h=60, selected=True),
        ]
        # 1.: 50…150 × 50…150 ; 2.: 250…350 × 170…230
        assert group_bounds(nodes) == pytest.approx((50.0, 50.0, 300.0, 180.0))

    def test_a_kijeloletlen_kepek_nem_szamitanak(self):
        nodes = [
            _node(100, 100, w=100, h=100, selected=True),
            _node(900, 900, w=100, h=100, selected=False),
            _node(300, 100, w=100, h=100, selected=True),
        ]
        assert group_bounds(nodes) == pytest.approx((50.0, 50.0, 300.0, 100.0))

    def test_a_forgatott_csomopont_befoglaloja_nagyobb(self):
        """45°-os négyzet befoglalója `oldal * sqrt(2)` — a sarkok is bent."""
        oldal = 100.0
        nodes = [
            _node(500, 500, w=oldal, h=oldal, theta=math.pi / 4, selected=True),
            _node(500, 500, w=1.0, h=1.0, selected=True),
        ]
        atlo = oldal * math.sqrt(2.0)
        x, y, w, h = group_bounds(nodes)
        assert w == pytest.approx(atlo)
        assert h == pytest.approx(atlo)
        assert x == pytest.approx(500.0 - atlo / 2)
        assert y == pytest.approx(500.0 - atlo / 2)

    def test_a_kilencven_fok_csak_felcsereli_az_oldalakat(self):
        nodes = [
            _node(500, 500, w=200, h=100, theta=math.pi / 2, selected=True),
            _node(500, 500, w=1.0, h=1.0, selected=True),
        ]
        _, _, w, h = group_bounds(nodes)
        assert (w, h) == pytest.approx((100.0, 200.0))

    def test_nem_modositja_a_bemenetet(self):
        nodes = (
            _node(100, 100, selected=True),
            _node(300, 300, selected=True),
        )
        elotte = tuple(nodes)
        group_bounds(nodes)
        assert tuple(nodes) == elotte
