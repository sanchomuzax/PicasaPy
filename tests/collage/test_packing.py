"""A Mozaik (`picturegrid`) bináris pakolófája (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.7, 1.9.9, 1.9.10.
"""

from __future__ import annotations

import math

import pytest

from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.packing import (
    CUT_SIDE_BY_SIDE,
    CUT_STACKED,
    FULL_SEARCH_LIMIT,
    PACK_TIME_LIMIT,
    adjust_target,
    assign_rects,
    build_guillotine,
    choose_cut,
    combined_aspect,
    pack,
    packing_cost,
)


class FakeClock:
    """Lépésenként fix idővel előrehaladó óra — a 0,5 s-os keresés
    tesztelhetővé tételéhez."""

    def __init__(self, step: float = 0.1):
        self.step = step
        self.now = 0.0

    def __call__(self) -> float:
        value = self.now
        self.now += self.step
        return value


# --- A geometria alapazonossága ---------------------------------------------


def test_egymas_melle_teve_az_oldalaranyok_OSSZEADODNAK():
    assert combined_aspect(CUT_SIDE_BY_SIDE, 1.5, 0.5) == pytest.approx(2.0)


def test_egymas_ala_teve_a_HARMONIKUS_kozep_fele():
    """`a1·a2 / (a1 + a2)` — két négyzet egymás alatt 0,5-ös arányt ad."""
    assert combined_aspect(CUT_STACKED, 1.0, 1.0) == pytest.approx(0.5)


def test_a_vagasirany_a_kozelebbi_jeloltet_valasztja():
    """Négyzetes cellába (A = 1,0) két négyzet inkább egymás ALÁ kerül:
    |2,0 − 1,0| = 1,0, de |0,5 − 1,0| = 0,5."""
    assert choose_cut(1.0, 1.0, 1.0) == CUT_STACKED
    # széles cellába viszont egymás MELLÉ
    assert choose_cut(2.0, 1.0, 1.0) == CUT_SIDE_BY_SIDE


# --- A kiigazítás (másodfokú egyenlet) --------------------------------------


def test_a_kiigazitas_egymas_mellett_pontosan_kiadja_a_celt():
    """`(a1+t) + (a2+t) = A`"""
    a1, a2, target = 1.2, 0.8, 3.0
    t = adjust_target(target, a1, a2, CUT_SIDE_BY_SIDE)
    assert (a1 + t) + (a2 + t) == pytest.approx(target)


def test_a_kiigazitas_egymas_alatt_pontosan_kiadja_a_celt():
    """`(a1+t)(a2+t) / ((a1+t)+(a2+t)) = A` — a másodfokú megoldóképlet."""
    a1, a2, target = 1.2, 0.8, 0.6
    t = adjust_target(target, a1, a2, CUT_STACKED)
    b1, b2 = a1 + t, a2 + t
    assert b1 * b2 / (b1 + b2) == pytest.approx(target)


@pytest.mark.parametrize("a1", [0.4, 1.0, 2.5])
@pytest.mark.parametrize("a2", [0.3, 1.0, 3.0])
@pytest.mark.parametrize("target", [0.2, 1.0, 4.0])
def test_a_masodfoku_egyenletnek_MINDIG_van_valos_gyoke(a1, a2, target):
    """A diszkrimináns kifejtve `(a1 − a2)² + 4A²`, ami sosem negatív —
    tehát a kiigazítás soha nem hibázhat el numerikusan."""
    t = adjust_target(target, a1, a2, CUT_STACKED)
    b1, b2 = a1 + t, a2 + t
    assert b1 * b2 / (b1 + b2) == pytest.approx(target)


# --- A faépítés és a cellák -------------------------------------------------


def test_negy_negyzet_negyzetes_lapon_KETSZER_KETTES_racs():
    """Kézzel végigszámolt eset. A gyökér egymás alá vág (0,5 közelebb az
    1,0-hoz, mint a 2,0), a kiigazítás `t = 1`, így mindkét gyerek 2,0-s
    célaránnyal épül — és ott már az egymás mellé rakás a pontos."""
    tree = build_guillotine(1.0, [1.0, 1.0, 1.0, 1.0])
    assert tree.cut == CUT_STACKED
    rects = assign_rects(tree, count=4)
    assert len(rects) == 4
    for rect in rects:
        assert rect.width == pytest.approx(0.5)
        assert rect.height == pytest.approx(0.5)


def test_a_cellak_hezagmentesen_lefedik_az_egysegnegyzetet():
    for count in (1, 2, 3, 5, 7, 11):
        aspects = [1.0 + 0.1 * i for i in range(count)]
        rects = assign_rects(build_guillotine(1.5, aspects), count=count)
        terulet = sum(r.width * r.height for r in rects)
        assert terulet == pytest.approx(1.0), f"{count} kép"


def test_a_kepek_sorrendje_megmarad():
    """A fa a lista sorrendjét őrzi — a keverés a hívó dolga."""
    rects = assign_rects(build_guillotine(1.5, [1.0] * 6), count=6)
    assert len(rects) == 6


def test_paros_hatarra_igazitas():
    """`ha (közép & 1) != 0 és n > 2, akkor közép++` — három képnél ezért
    kettő kerül az egyik oldalra, nem egy."""
    tree = build_guillotine(1.0, [1.0, 1.0, 1.0])
    assert tree.left is not None and tree.right is not None
    assert tree.left.leaf_count == 2
    assert tree.right.leaf_count == 1


# --- A költség --------------------------------------------------------------


def test_a_tokeletes_illeszkedes_koltsege_nulla():
    """Négy négyzet egy 2×2-es rácsban hiánytalanul kitölti a celláit."""
    tree = build_guillotine(1.0, [1.0] * 4)
    rects = assign_rects(tree, count=4)
    assert packing_cost(rects, [1.0] * 4) == pytest.approx(0.0)


def test_a_koltseg_a_CELLABAN_URESEN_maradó_terulet():
    """Egy 2:1-es cellába tett négyzetes kép a cella felét üresen hagyja."""
    from picasapy.collage.rects import NormRect

    cella = NormRect(0.0, 0.0, 1.0, 0.5)  # 1×0,5 → oldalarány 2,0
    assert packing_cost((cella,), [1.0]) == pytest.approx(0.25)


def test_a_kep_nem_torzul_csak_a_cella_marad_uresen():
    """A költség sosem negatív, és a torzításmentes illesztésből jön."""
    from picasapy.collage.rects import NormRect

    for aspect in (0.25, 0.5, 1.0, 2.0, 4.0):
        cost = packing_cost((NormRect(0.0, 0.0, 1.0, 1.0),), [aspect])
        assert cost >= 0.0


# --- A keresés --------------------------------------------------------------


def test_a_keresest_az_ORA_allitja_meg():
    """A 0,5 másodperces korlát valós órához van kötve. Beinjektált órával
    pontosan megszámolható, hány kör fut le."""
    assert PACK_TIME_LIMIT == 0.5
    clock = FakeClock(step=0.1)
    pack([1.0, 1.5, 0.7, 2.0], 1.5, MsvcRandom(3), clock=clock)
    assert clock.now == pytest.approx(0.6, abs=1e-9)


def test_azonos_maggal_es_orraval_azonos_eredmeny():
    """A Mozaik élesben NEM determinisztikus (valós óra + `rand()`), de
    befecskendezett órával és maggal a teszt megismételhető."""
    a = pack([1.0, 1.5, 0.7, 2.0], 1.5, MsvcRandom(11), clock=FakeClock())
    b = pack([1.0, 1.5, 0.7, 2.0], 1.5, MsvcRandom(11), clock=FakeClock())
    assert a == b


def test_a_kereses_nem_ront_a_kiindulasin():
    """A kezdeti (eredeti sorrendű) fa a jelölt, és csak SZIGORÚAN jobb
    válthatja le — a végeredmény sosem rosszabb."""
    aspects = [1.6, 0.6, 1.0, 2.2, 0.8, 1.3]
    kiindulo = assign_rects(build_guillotine(1.5, aspects), count=len(aspects))
    keresett = pack(aspects, 1.5, MsvcRandom(5), clock=FakeClock(step=0.05))
    assert packing_cost(keresett, aspects) <= packing_cost(kiindulo, aspects)


def test_a_kereses_minden_kepnek_ad_cellat():
    for count in (1, 2, 6, 13, 20):
        rects = pack([1.4] * count, 1.5, MsvcRandom(1), clock=FakeClock(step=0.3))
        assert len(rects) == count
        assert sum(r.width * r.height for r in rects) == pytest.approx(1.0)


class CountingRandom(MsvcRandom):
    """`MsvcRandom`, ami számolja a hívásait."""

    def __init__(self, seed: int = 1):
        super().__init__(seed)
        self.calls = 0

    def rand(self) -> int:
        self.calls += 1
        return super().rand()


def test_a_finomito_kor_CSAK_tizennegy_alatt_fut():
    """14-nél kevesebb képnél `CFullSearchTree` fut, és utána még száz
    csere-jelöltet is kiértékel (kettő véletlen szám jelöltenként);
    14-től az alaposztály, finomítás nélkül.

    Az órát úgy állítjuk, hogy a külső keresés egyetlen kört se fusson —
    így minden véletlenhívás a finomító köré."""
    assert FULL_SEARCH_LIMIT == 14

    kevés = CountingRandom(4)
    pack([1.3] * 13, 1.5, kevés, clock=FakeClock(step=1.0))
    assert kevés.calls == 2 * 100

    sok = CountingRandom(4)
    pack([1.3] * 14, 1.5, sok, clock=FakeClock(step=1.0))
    assert sok.calls == 0


def test_ervenytelen_bemenet():
    with pytest.raises(ValueError):
        pack([], 1.5, MsvcRandom(1))
    with pytest.raises(ValueError):
        pack([1.0, -1.0], 1.5, MsvcRandom(1))
    with pytest.raises(ValueError):
        build_guillotine(0.0, [1.0])


def test_a_cellak_ervenyes_normalizalt_teglalapok():
    rects = pack([1.0, 2.0, 0.5, 1.2, 0.9], 1.3, MsvcRandom(8), clock=FakeClock())
    for rect in rects:
        assert 0.0 <= rect.x0 < rect.x1 <= 1.0
        assert 0.0 <= rect.y0 < rect.y1 <= 1.0
        assert not math.isnan(rect.width)
