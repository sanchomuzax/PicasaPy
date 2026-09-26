"""#3596: a képmérettől függő öt csúszka `.picasa.ini`-értéke SZÁZALÉK.

Az eredeti ezeket `glimmer::DynamicRangeSlider`-ként építi (`0x00bb25f0`),
és a tárolt `t`-t 0–100 közé szorítva vetíti a pillanatnyi tartományra
(`0x00bbd3d0`):

    érték = minimum + (maximum − minimum) · min(max(t, 0), 100) / 100

(`docs/specs/filters-decoded.md`, #3591). A tesztkép 960 × 640 — a mért
`684-merokeszlet` mérete: `min(W, H)/2 = 320`, `H/6 = 106,67`.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import chain, focal
from picasapy.render import glimmer_frames as frames
from picasapy.render.dinamikus_csuszka import dinamikus_csuszka_ertek
from picasapy.render.elonezeti_arany import elonezeti_arany

_W, _H = 960, 640


@pytest.fixture
def kep() -> np.ndarray:
    return np.full((_H, _W, 3), 128, dtype=np.uint8)


class TestKeplet:
    @pytest.mark.parametrize(
        ("szazalek", "vart"),
        [(0.0, 10.0), (50.0, 165.0), (100.0, 320.0), (105.0, 320.0), (-5.0, 10.0)],
    )
    def test_fokuszsugar_960x640(self, szazalek, vart):
        assert dinamikus_csuszka_ertek(szazalek, 10.0, 320.0) == pytest.approx(vart)

    @pytest.mark.parametrize(
        ("szazalek", "vart"),
        [(0.0, 0.0), (50.0, 160.0), (100.0, 320.0), (105.0, 320.0)],
    )
    def test_sarokrádiusz_960x640(self, szazalek, vart):
        assert dinamikus_csuszka_ertek(szazalek, 0.0, 320.0) == pytest.approx(vart)

    def test_mert_merokeszlet_sugara(self):
        # `Radius = 105` → 100 %-ra szorul → 320 px; a belső sugár
        # `320 · 50/101 = 158,4` (mérve ~157)
        assert dinamikus_csuszka_ertek(105.0, 10.0, 320.0) * 50 / 101 == pytest.approx(158.4, abs=0.05)


def _elkapo(monkeypatch, modul, nev):
    kapott: dict = {}

    def elkap(image, **kwargs):
        kapott.update(kwargs)
        return image

    monkeypatch.setattr(modul, nev, elkap)
    return kapott


class TestLancKezelok:
    @pytest.mark.parametrize(("szazalek", "vart"), [(0, 10.0), (50, 165.0), (100, 320.0), (105, 320.0)])
    def test_picnik_focal_pixelate_radius(self, monkeypatch, kep, szazalek, vart):
        kapott = _elkapo(monkeypatch, chain, "apply_focal_pixelate")
        chain.apply_filters(kep, parse_filters(f"PicnikFocalPixelate=1,0.5,0.5,20,{szazalek},50,0,0;"))
        assert kapott["radius"] == pytest.approx(vart)

    @pytest.mark.parametrize(("szazalek", "vart"), [(0, 10.0), (50, 165.0), (100, 320.0), (105, 320.0)])
    def test_focal_zoom_radius(self, monkeypatch, kep, szazalek, vart):
        kapott = _elkapo(monkeypatch, chain, "apply_focal_zoom")
        chain.apply_filters(kep, parse_filters(f"FocalZoom=1,0.5,0.5,50,{szazalek},50,0;"))
        assert kapott["radius"] == pytest.approx(vart)
        assert kapott["scale"] == pytest.approx(1.0)

    def test_focal_zoom_teljes_felbontasu_tartomany_elonezeten(self, monkeypatch, kep):
        # a tartomány `min(fullResImageWidth, fullResImageHeight)/2`: fél
        # méretű előnézeten a teljes kép 1920 × 1280 → max 640 px, a maszk
        # pedig a natív `scale`-lel (0,5) kerül vissza az előnézetre
        kapott = _elkapo(monkeypatch, chain, "apply_focal_zoom")
        with elonezeti_arany(0.5):
            chain.apply_filters(kep, parse_filters("FocalZoom=1,0.5,0.5,50,100,50,0;"))
        assert kapott["radius"] == pytest.approx(640.0)
        assert kapott["scale"] == pytest.approx(0.5)

    @pytest.mark.parametrize(("szazalek", "vart"), [(0, 0.0), (50, 160.0), (100, 320.0), (105, 320.0)])
    def test_rounded_edges_corner_radius(self, monkeypatch, kep, szazalek, vart):
        kapott = _elkapo(monkeypatch, frames, "apply_rounded_edges")
        chain.apply_filters(kep, parse_filters(f"RoundedEdges=1,{szazalek},00ffffff;"))
        assert kapott["corner_radius"] == pytest.approx(vart)

    @pytest.mark.parametrize(
        ("szazalek", "sarok", "felirat"),
        [(0, 0.0, 0.0), (50, 160.0, 640 / 12), (100, 320.0, 640 / 6), (105, 320.0, 640 / 6)],
    )
    def test_border_corner_radius_es_caption_height(self, monkeypatch, kep, szazalek, sarok, felirat):
        kapott = _elkapo(monkeypatch, frames, "apply_border")
        chain.apply_filters(
            kep,
            parse_filters(f"Border=1,20,5,{szazalek},00000000,00ffffff,{szazalek};"),
        )
        assert kapott["corner_radius"] == pytest.approx(sarok)
        assert kapott["caption_height"] == pytest.approx(felirat)

    def test_valodi_render_felirat_savja_a_szazalekbol(self, kep):
        # vég-a-végig: 100 % felirat 960 × 640-en `H/6 = 106,67` → 107 sor
        # (az `add_caption` meglévő kerekítése)
        kimenet, kihagyott = chain.apply_filters(
            kep, parse_filters("Border=1,0,0,0,00000000,00ffffff,100;")
        )
        assert kihagyott == ()
        assert kimenet.shape[0] == _H + 107


def test_focal_modul_kulcsszavai_valtozatlanok():
    # a kezelő `scale`-t ad át — a natív maszk ezt a paramétert várja
    import inspect

    assert "scale" in inspect.signature(focal.apply_focal_zoom).parameters
