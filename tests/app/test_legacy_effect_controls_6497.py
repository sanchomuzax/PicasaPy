"""#6497: a régi effektek vezérlői a filterdesc-regisztert követik."""

from __future__ import annotations

import pytest

from picasapy.app.effect_params import effect_params
from picasapy.render.chain import can_offer_filter_control
from picasapy.render.legacy_effects import LEGACY_EFFECTS
from picasapy.render.registry import FILTER_REGISTRY


_IRANYITOTT = {"dir_sat", "dir_brite", "dir_sharp"}
_KEZZEL_KATALOGUSOZOTT = {"colorfix", "radtint", "whitept"}


def _regiszter_csuszkak(kulcs: str):
    return tuple(
        slider
        for slider in FILTER_REGISTRY[kulcs].sliders
        if not slider.hidden
    )


def _feluleten_lathato_csuszkak(kulcs: str):
    params = effect_params(kulcs)
    # A meglévő fókuszpuckos katalógusok az ini-koordinátákat külön sorban
    # tartják; ezek nem az eredeti csúszkák. A három irányított kivételnél a
    # puck a két valódi iránycsúszkát vezérli.
    return tuple(
        param
        for param in params
        if param.kind == "slider"
        and not (kulcs not in _IRANYITOTT and param.key in {"x", "y"})
    )


def test_minden_lathato_legacy_csuszka_kap_vezerlot_a_regiszterbol():
    for effect in LEGACY_EFFECTS:
        if not can_offer_filter_control(effect.key):
            continue
        vart = _regiszter_csuszkak(effect.key)
        if not vart:
            continue

        kapott = _feluleten_lathato_csuszkak(effect.key)
        assert len(kapott) == len(vart), (
            f"{effect.key}: {len(vart)} látható registry-csúszkához "
            f"{len(kapott)} felületi vezérlő van"
        )


def test_uj_legacy_vezerlok_neve_tartomanya_es_alapja_a_regisztert_koveti():
    for effect in LEGACY_EFFECTS:
        if not can_offer_filter_control(effect.key):
            continue
        if effect.key in _KEZZEL_KATALOGUSOZOTT:
            continue
        vart = _regiszter_csuszkak(effect.key)
        kapott = _feluleten_lathato_csuszkak(effect.key)
        assert [param.label for param in kapott] == [
            slider.label for slider in vart
        ], effect.key
        for param, slider in zip(kapott, vart, strict=True):
            assert param.minimum == pytest.approx(slider.minimum), effect.key
            assert param.maximum == pytest.approx(slider.maximum), effect.key
            assert param.default == pytest.approx(
                0.0 if slider.default is None else slider.default
            ), effect.key


def test_linblur_a_registry_mennyisegcsuszkajat_es_puckjat_adja():
    params = effect_params("linblur")
    assert [(p.kind, p.label, p.minimum, p.maximum, p.default) for p in params] == [
        ("puck", "", 0.0, 1.0, 0.5),
        ("puck", "", 0.0, 1.0, 0.5),
        ("slider", "Amount", 0.0, 10.0, 2.0),
    ]


@pytest.mark.parametrize("kulcs", sorted(_IRANYITOTT))
def test_iranyitott_effekt_csuszkai_es_puckja(kulcs: str):
    params = effect_params(kulcs)
    assert [(p.label, p.minimum, p.maximum, p.default) for p in params] == [
        ("Left to Right", -1.0, 1.0, 0.0),
        ("Top to Bottom", -1.0, 1.0, 0.0),
    ]


def test_registry_alapertelmezett_nelkul_a_zero_alapallast_adja():
    for kulcs in ("triple", "triple2", "triple3", "shadow"):
        sliders = _regiszter_csuszkak(kulcs)
        params = _feluleten_lathato_csuszkak(kulcs)
        assert len(params) == len(sliders)
        for param, slider in zip(params, sliders, strict=True):
            assert param.minimum == pytest.approx(slider.minimum)
            assert param.maximum == pytest.approx(slider.maximum)
            assert param.default == pytest.approx(
                0.0 if slider.default is None else slider.default
            )


def test_linblur_es_dir_sat_ertekei_az_ini_alakban_visszatolthetok(
    qt_app, tmp_path
):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from tests.support.jpeg_factory import make_jpeg

    photo = make_jpeg(tmp_path / "regi-effekt.jpg", size=(48, 32))
    controller = EditController(EditPreviewProvider())
    controller.beginEdit("6497", str(photo))
    controller.applyEffectWithParams("linblur", [0.25, 0.75, 8.5])
    controller.applyEffectWithParams("dir_sat", [0.65, -0.4])

    mentett_lanc = controller.effectChain
    assert "linblur=1,0.250000,0.750000,8.500000;" in mentett_lanc
    assert "dir_sat=1,0.650000,-0.400000;" in mentett_lanc
    ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
    assert (
        "filters=linblur=1,0.250000,0.750000,8.500000;"
        "dir_sat=1,0.650000,-0.400000;" in ini_text
    )

    reloaded = EditController(EditPreviewProvider())
    reloaded.beginEdit("6497", str(photo))
    assert reloaded.effectChain == mentett_lanc
