"""A Pan and Zoom két jelölt kivágása (#5258), rögzített törtforrással."""

import pytest

from picasapy.app.slideshow_pan_zoom import (
    _lcg_fraction_source,
    pan_zoom_rectangles,
)


def _forras(tortek):
    it = iter(tortek)
    huzasok = []

    def kovetkezo():
        ertek = next(it)
        huzasok.append(ertek)
        return ertek

    return kovetkezo, huzasok


def test_futasideju_magforras_a_spec_szerinti_lcg_felsobb_15_bitjet_adja():
    veletlen = _lcg_fraction_source(1)

    assert veletlen() == pytest.approx(41 / 32768)
    assert veletlen() == pytest.approx(18467 / 32768)
    assert veletlen() == pytest.approx(6334 / 32768)


def test_meretkulonbseg_ujrahuzas_es_lcg_sorrendcsere():
    """A kis eltérésű u/v párt eldobja, a jelölteket a méretük szerint cseréli."""
    veletlen, huzasok = _forras(
        [0.1, 0.4, 0.2, 0.9, 0.99, 0.99, 0.01, 0.99, 0.99]
    )

    a, b = pan_zoom_rectangles(1200, 800, 1600, 900, veletlen)

    # A 16:9 alaptéglalap 1200×675; mindkét méret az alap 75–95%-a.
    meretaranyok = [a.width / 1200, b.width / 1200]
    assert meretaranyok == pytest.approx([0.93, 0.79])
    assert a.height / 675 == pytest.approx(0.93)
    assert b.height / 675 == pytest.approx(0.79)
    assert len(huzasok) == 9  # u/v, új u/v, négy eltolás, sorrendág


def test_hatarolas_csak_eltolja_a_teglalapot_es_megtartja_a_meretet():
    max_tort = 32767 / 32768
    veletlen, _huzasok = _forras(
        [0.75, 0.0, max_tort, max_tort, max_tort, 0.0, 0.1]
    )

    teglalapok = pan_zoom_rectangles(1000, 1000, 1000, 1000, veletlen)
    kicsi, nagy = sorted(teglalapok, key=lambda rect: rect.width)

    assert (kicsi.width, kicsi.height) == pytest.approx((750, 750))
    assert (kicsi.x, kicsi.y) == pytest.approx((25, 0))
    assert (nagy.width, nagy.height) == pytest.approx((900, 900))
    assert (nagy.x, nagy.y) == pytest.approx((100, 100))
    for rect in teglalapok:
        assert rect.x >= 0
        assert rect.y >= 0
        assert rect.x + rect.width <= 1000
        assert rect.y + rect.height <= 1000


@pytest.mark.parametrize(
    "meretek",
    [(0, 100, 50, 50), (100, 0, 50, 50), (100, 100, 0, 50), (100, 100, 50, 0)],
)
def test_nulla_meretnel_hibas_bemenetet_jelez(meretek):
    with pytest.raises(ValueError):
        pan_zoom_rectangles(*meretek, lambda: 0.0)
