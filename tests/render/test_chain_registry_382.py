"""#382 4. pont: a filterdesc-regiszter által azonosított 26 eddig sehol nem
dokumentált szűrőnév felvétele.

Öt közülük (`save`, `rot`, `crop`, `moviestart`, `movieend`) NEM képi
művelet (`mode="history"` vagy mozi-vágás-jelölő) — ezek a `picnik=1;`
mintájára néma no-op-ként nyelődnek el, NEM kerülnek a `skipped` listába. A
maradék 21 a `KNOWN_UNRENDERED_OPS`-ba kerül: felismerve, de vizuális
modell nélkül — a `skipped` listában jelennek meg (#347 mintája).

Mindegyikre round-trip tesztet is futtatunk: a `.picasa.ini`
parszer/serializer szintjén (`picasapy.ini.filters`) ezek a nevek bitre
pontosan megmaradnak — a regiszter csak a RENDERELŐ oldalon hat.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters, serialize_filters
from picasapy.render.chain import KNOWN_UNRENDERED_OPS, _NOOP_MARKERS, apply_filters

#: A #382-es issue 26 névből álló listája.
_ALL_26_NAMES = (
    "triple",
    "triple2",
    "triple3",
    "colorfix",
    "autobacklight",
    "autocontrast",
    "rainbow",
    "linblur",
    "radtint",
    "colortemp",
    "shadow",
    "blur",
    "contrast",
    "gamma",
    "backlight",
    "whitept",
    "dir_sat",
    "dir_brite",
    "dir_sharp",
    "focalpixelate",
    "debug",
    "crop",
    "rot",
    "save",
    "moviestart",
    "movieend",
)

#: Ebből a history/mozi-jelölő öt, ami NÉMA no-op (nem kihagyott effekt).
_NOOP_NAMES = ("save", "rot", "crop", "moviestart", "movieend")

#: A maradék 21, ami a `KNOWN_UNRENDERED_OPS`-ba tartozik.
_UNRENDERED_NAMES = tuple(name for name in _ALL_26_NAMES if name not in _NOOP_NAMES)


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(23)
    return rng.integers(30, 220, size=(48, 64, 3), dtype=np.uint8)


class TestAll26NamesCovered:
    def test_pontosan_26_nev_van_a_listaban(self):
        assert len(_ALL_26_NAMES) == 26
        assert len(set(_ALL_26_NAMES)) == 26

    def test_5_noop_es_21_unrendered_partitio(self):
        assert len(_NOOP_NAMES) == 5
        assert len(_UNRENDERED_NAMES) == 21
        assert set(_NOOP_NAMES) | set(_UNRENDERED_NAMES) == set(_ALL_26_NAMES)


class TestUnrenderedNamesRecognised:
    @pytest.mark.parametrize("key", _UNRENDERED_NAMES)
    def test_a_regiszterbe_felvett_nev_kihagyottkent_jelenik_meg(self, key, sample):
        assert key in KNOWN_UNRENDERED_OPS
        report = apply_filters(sample, parse_filters(f"{key}=1;"))
        assert np.array_equal(report.image, sample)
        assert key in [name.casefold() for name in report.skipped]


class TestNoopMarkersSwallowedSilently:
    @pytest.mark.parametrize("key", _NOOP_NAMES)
    def test_a_noop_marker_nema_es_nem_kihagyott(self, key, sample):
        assert key in _NOOP_MARKERS
        if key == "crop":
            # a "crop" (bare) marker paraméter nélkül fut — a "crop64" a
            # tényleges vágás, ez a filterdesc szerint csak history-jelölő
            chain = f"{key}=1;"
        else:
            chain = f"{key}=1;"
        report = apply_filters(sample, parse_filters(chain))
        assert np.array_equal(report.image, sample)
        assert report.skipped == ()

    def test_crop_bare_nem_keveredik_a_crop64tal(self, sample):
        # a bare "crop" no-op, a "crop64" viszont a valódi vágást hordozza —
        # a kettő NEM ugyanaz a kulcs, a lánc mindkettőt helyesen kezeli
        report = apply_filters(
            sample, parse_filters("crop=1;crop64=1,000000007fff7fff;")
        )
        assert report.skipped == ()


class TestRoundTrip:
    @pytest.mark.parametrize("key", _ALL_26_NAMES)
    def test_ini_szinten_bitre_pontosan_megmarad(self, key):
        value = f"{key}=1,0.500000;"
        assert serialize_filters(parse_filters(value)) == value

    @pytest.mark.parametrize("key", _ALL_26_NAMES)
    def test_parameter_nelkuli_alak_is_round_trippel(self, key):
        value = f"{key}=1;"
        assert serialize_filters(parse_filters(value)) == value
