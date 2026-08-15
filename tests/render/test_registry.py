"""#382: a `filterdesc.xml`-ből épített szűrő-regiszter konzisztenciája.

Az elfogadási feltétel szerint a regiszternek mind a 84 szűrőt tartalmaznia
kell, minden bejegyzésnek konzisztensnek kell lennie
(`minimum <= default <= maximum`), a kulcsoknak egyedieknek, és a
`chain._HANDLERS` minden kulcsának léteznie kell a regiszterben.
"""

from __future__ import annotations

import math

import pytest

from picasapy.render.chain import _HANDLERS
from picasapy.render.registry import FILTER_REGISTRY, chain_flags, clamp_slider_value
from picasapy.render.registry_data import RAW_FILTERS


class TestRegistrySize:
    def test_84_szuro_van_a_nyers_tablaban(self):
        assert len(RAW_FILTERS) == 84

    def test_84_szuro_epult_be_a_regiszterbe(self):
        assert len(FILTER_REGISTRY) == 84

    def test_a_kulcsok_egyediek(self):
        keys = [raw[0] for raw in RAW_FILTERS]
        assert len(keys) == len(set(keys)), "duplikált kulcs a nyers táblában"

    def test_a_kulcsok_mar_kisbetusek(self):
        # a `key` mezőnek "kisbetűsítve illesztve" kell lennie (issue-spec)
        for key in FILTER_REGISTRY:
            assert key == key.casefold()


class TestSliderConsistency:
    @pytest.mark.parametrize("key", sorted(FILTER_REGISTRY))
    def test_minimum_default_maximum_sorrend(self, key):
        spec = FILTER_REGISTRY[key]
        for slider in spec.sliders:
            assert slider.minimum <= slider.maximum, (
                f"{key}/{slider.label}: minimum > maximum"
            )
            if (
                slider.default is not None
                and math.isfinite(slider.maximum)
                and slider.log_base is None
            ):
                # softclamp-kivétel: a log-jelzésű csúszkáknál a tárolt
                # (mappelt) érték SZÁNDÉKOSAN túllépheti a névleges
                # tartományt (pl. glow default 3.0, range [0,1]) — ld.
                # `registry.clamp_slider_value` docsztringjét.
                assert slider.minimum <= slider.default <= slider.maximum, (
                    f"{key}/{slider.label}: default a tartományon kívül"
                )

    @pytest.mark.parametrize("key", sorted(FILTER_REGISTRY))
    def test_csuszka_indexek_egyediek_es_novekvok(self, key):
        indices = [slider.index for slider in FILTER_REGISTRY[key].sliders]
        assert indices == sorted(set(indices)), f"{key}: csúszka-index ütközés"


class TestHandlersExistInRegistry:
    #: #711 — a `desat` az EGYETLEN dokumentált kivétel: a `CDesaturateFilter`
    #: saját, Picasa 2-korabeli ini-kulcsa, ami bizonyítottan NINCS a
    #: filterdesc.xml 84 szűrőjében (ld. `docs/specs/
    #: picasa-native-filter-registry.md` 1. pontja), ezért a `registry_data.py`
    #: nyers táblájában sem szerepel — a `chain._HANDLERS`-ben viszont igen,
    #: mert renderelése az `ansel` egzakt megfelelője (`_apply_desat_op`).
    _LEGACY_ALIAS_EXCEPTIONS = frozenset({"desat"})

    def test_minden_kezelt_kulcs_a_regiszterben_van(self):
        missing = (
            set(_HANDLERS) - set(FILTER_REGISTRY) - self._LEGACY_ALIAS_EXCEPTIONS
        )
        assert not missing, f"a _HANDLERS kulcsai hiányoznak a regiszterből: {sorted(missing)}"


class TestClampSliderValue:
    def test_tartomanyon_beluli_ertek_valtozatlan(self):
        spec = FILTER_REGISTRY["sat"]
        slider = spec.sliders[0]
        clamped, out_of_range = clamp_slider_value(spec, slider, 0.5)
        assert clamped == 0.5
        assert out_of_range is False

    def test_tartomanyon_kivuli_ertek_vagva(self):
        spec = FILTER_REGISTRY["sat"]
        slider = spec.sliders[0]
        clamped, out_of_range = clamp_slider_value(spec, slider, 5.0)
        assert clamped == slider.maximum
        assert out_of_range is True

    def test_log_csuszkanal_a_validacio_kimarad(self):
        # softclamp-kivétel: a glow/glow2 sugara a log-leképezés miatt
        # túllépheti a névleges [min,max]-ot (valós minta: glow=1,0.43,2.47)
        spec = FILTER_REGISTRY["glow2"]
        radius_slider = next(s for s in spec.sliders if s.log_base is not None)
        clamped, out_of_range = clamp_slider_value(spec, radius_slider, 250.0)
        assert clamped == 250.0
        assert out_of_range is False


class TestChainFlags:
    def test_ures_lanc_semmit_nem_jelez(self):
        assert chain_flags(()) == (False, False, False)

    def test_full_res_slow_jelzo_grain2bol(self):
        full_res, slow, resizes = chain_flags(["grain2"])
        assert full_res is True
        assert slow is True
        assert resizes is False

    def test_resize_jelzo_bordertol(self):
        full_res, slow, resizes = chain_flags(["Border"])
        assert resizes is True

    def test_ismeretlen_nev_figyelmen_kivul_marad(self):
        assert chain_flags(["nemletezoSzuro"]) == (False, False, False)

    def test_tobb_szuro_ored_jelzoi(self):
        full_res, slow, resizes = chain_flags(["sat", "grain2", "Border"])
        assert (full_res, slow, resizes) == (True, True, True)
