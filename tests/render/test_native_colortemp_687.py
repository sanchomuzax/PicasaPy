"""A natív `colortemp` szűrő magja (#687) — `0x0090ea10`.

A szerkezet a `docs/specs/picasa-native-filter-workers.md` 2.5 pontjából
DEKOMPILÁLT: középtónus-parabolával súlyozott hideg↔meleg tengely, plusz egy
globális lekicsinyítés-visszanagyítás („fehérváltás") párost. A két csúszka
egészre skálázása viszont MÉRT (#685 mérőszettje) — ld.
`native_colortemp.apply_native_colortemp` docstringjét.

Ez NEM ugyanaz, mint a `tone.apply_color_temperature`: az a
`finetune`/`finetune2` p5 mezőjének mért modellje, és a #551-ben méréssel
JOBBNAK bizonyult ennél a natív képletnél. A két utat szándékosan nem
vezetjük egy kulcsra.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.native_colortemp import apply_native_colortemp


@pytest.fixture
def ramp() -> np.ndarray:
    levels = np.arange(256, dtype=np.uint8).reshape(1, 256, 1)
    return np.repeat(np.repeat(levels, 4, axis=0), 3, axis=2)


class TestAzonossag:
    def test_mindket_csuszka_nullan_azonossag(self, ramp):
        assert np.array_equal(apply_native_colortemp(ramp, 0.0, 0.0), ramp)

    def test_a_bemenetet_nem_mutalja(self, ramp):
        eredeti = ramp.copy()
        apply_native_colortemp(ramp, 0.5, 1.0)
        assert np.array_equal(ramp, eredeti)

    def test_uint8_kimenet_es_alak(self, ramp):
        result = apply_native_colortemp(ramp, 0.25, 0.5)
        assert result.dtype == np.uint8
        assert result.shape == ramp.shape


class TestHidegMelegTengely:
    def test_melegites_a_voroset_emeli_a_keket_huzza(self, ramp):
        result = apply_native_colortemp(ramp, 0.5, 0.0)
        assert int(result[0, 128, 0]) > 128  # vörös fel
        assert int(result[0, 128, 2]) < 128  # kék le

    def test_hutes_forditva(self, ramp):
        result = apply_native_colortemp(ramp, -0.5, 0.0)
        assert int(result[0, 128, 0]) < 128
        assert int(result[0, 128, 2]) > 128

    def test_a_zold_csak_melegitesnel_es_negyed_sullyal_mozdul(self, ramp):
        meleg = apply_native_colortemp(ramp, 0.5, 0.0)
        hideg = apply_native_colortemp(ramp, -0.5, 0.0)
        # hűtéskor a zöld helyben marad (`t_pos = t >= 1 ? t : 0`)
        assert int(hideg[0, 128, 1]) == 128
        # melegítéskor mozdul, de a vörösnél sokkal kevésbé (>>17 vs >>15)
        zold_valtozas = int(meleg[0, 128, 1]) - 128
        voros_valtozas = int(meleg[0, 128, 0]) - 128
        assert 0 < zold_valtozas < voros_valtozas / 2

    def test_a_szelso_szintek_helyben_maradnak(self, ramp):
        # a középtónus-parabola a 0 és a 255 közelében nullára fut ki
        result = apply_native_colortemp(ramp, 0.5, 0.0)
        assert int(result[0, 0, 0]) == 0
        assert int(result[0, 255, 0]) == 255


class TestFeherValtas:
    def test_a_fehervaltas_onmagaban_kozel_azonossag(self, ramp):
        # a lekicsinyítés utáni visszanagyítás a PONTOS inverze — a kimenet
        # csak a nyolcbites kvantálás miatt tér el
        result = apply_native_colortemp(ramp, 0.0, 1.0)
        assert int(np.abs(result.astype(int) - ramp.astype(int)).max()) <= 2

    def test_a_fehervaltas_felerositi_a_szinhomerseklet_hatasat(self, ramp):
        # a hideg↔meleg eltolás a LEKICSINYÍTETT értékeken fut, és a záró
        # visszanagyítás magát az eltolást is felszorozza
        nelkule = apply_native_colortemp(ramp, 0.5, 0.0)
        vele = apply_native_colortemp(ramp, 0.5, 1.0)
        assert int(vele[0, 128, 0]) > int(nelkule[0, 128, 0]) > 128
        assert int(vele[0, 128, 2]) < int(nelkule[0, 128, 2]) < 128
