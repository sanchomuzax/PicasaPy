"""A teljes effekt-regiszter besorolása és a térszelvény mintavétele (#6522)."""

# SAJÁT FUNKCIÓ (#6522): a regiszter- és próbakép-őrök a PicasaPy új térszelvényét védik.

from __future__ import annotations

import numpy as np
from types import SimpleNamespace

from picasapy.app.effect_slice import EFFECT_VIEW_TYPES, classify_effect
from picasapy.app.effect_slice_render import _color_cube, render_surface, slider_sweep
from picasapy.app.photo_grid_model import PhotoGridModel
from picasapy.render.registry import FILTER_REGISTRY


def test_mind_a_84_regisztralt_effekt_nezettipust_kap():
    assert len(FILTER_REGISTRY) == 84
    assert set(EFFECT_VIEW_TYPES) == set(FILTER_REGISTRY)
    assert set(EFFECT_VIEW_TYPES.values()) <= {
        "tone",
        "color",
        "image",
        "point",
        "grain",
        "none",
    }


def test_jellegzetes_effektek_a_minta_szerinti_nezetet_kapjak():
    assert classify_effect("finetune2") == "tone"
    assert classify_effect("crossprocess") == "color"
    assert classify_effect("vignette") == "image"
    assert classify_effect("unsharp") == "point"
    assert classify_effect("picnikgrain") == "grain"
    assert classify_effect("crop64") == "none"


def test_a_csuszkatartomany_mind_a_tizenkettő_mintapontjat_felveszi():
    points = slider_sweep(-1.0, 1.0, 0.25, count=12)

    assert len(points) == 12
    assert points[0] == -1.0
    assert points[-1] == 1.0
    assert np.all(np.diff(points) > 0)


def test_a_nezo_elerheti_a_kijelolt_foto_teljes_lancat():
    model = PhotoGridModel()
    model._photos = (SimpleNamespace(filters="finetune2=1,0,0,0,0,0"),)

    assert model.filtersAt(0) == "finetune2=1,0,0,0,0,0"


def test_ures_lanc_azonos_bemenet_kimenet_atlot_ad():
    surface = render_surface(None, (), "tone")

    assert surface["kind"] == "identity"
    assert surface["line"] == ((0.0, 0.0), (1.0, 1.0))


def test_szinkocka_merese_nem_modositja_a_valtozatlan_szineket():
    surface = _color_cube(())

    assert len(surface["points"]) == 125
    assert surface["points"][0]["color"] == [0, 0, 0]
    assert surface["points"][-1]["color"] == [255, 255, 255]
