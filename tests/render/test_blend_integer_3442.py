"""#3442: a keverési módok a Picasa EGÉSZ, csonkoló képletével számolnak.

A spec: `docs/specs/filterdesc-registry.md`, „A `BlendInstruction`:
tizenegy keverési mód" B–D szakasz, és a „három maszk-utasítás" A)
szakasza. `b` = alsó elem (a művelet bemenete), `t` = felső (a kimenete);
a `÷255` mindenütt CSONKOLÓ.

A referencia-képletek itt szándékosan skalár-egyszerűek (Python-egészek a
spec táblája szerint), és KIMERÍTŐEN vetjük össze a megvalósítással: mind
a 65 536 (b, t) bájtparon, a maszkolt keverésnél mind a 256 maszkértékre.
"""

from __future__ import annotations

import struct

import numpy as np
import pytest

from picasapy.render import glimmer_ops as g

# --- Referencia a spec C) táblája szerint -------------------------------------


def _f(x: int, y: int) -> int:
    """Az Overlay/Hardlight közös alapfüggvénye (`0x008f53f0`)."""
    if x <= 127:
        return 2 * x * y // 255
    if x == 255 and y == 255:
        return 255
    return (65024 - 2 * (255 - x) * (255 - y)) // 255


def _softlight(b: int, t: int) -> int:
    bv = b & 0xFE
    if t < 128:
        return t * (bv + 128) // 255
    return (65025 - (382 - bv) * (255 - t)) // 255


_REFERENCIA = {
    "add": lambda b, t: min(b + t, 255),
    "darken": min,
    "lighten": max,
    "difference": lambda b, t: abs(b - t),
    "subtract": lambda b, t: max(b - t, 0),
    "multiply": lambda b, t: b * t // 255,
    "screen": lambda b, t: (65025 - (255 - b) * (255 - t)) // 255,
    "overlay": lambda b, t: _f(b, t),
    "hardlight": lambda b, t: _f(t, b),
    "softlight": _softlight,
    "normal": lambda b, t: t,
}

#: A natív módtábla (`0x00cf0e98`) sorszámai.
_SORSZAM = {
    0: "add",
    1: "darken",
    2: "difference",
    3: "hardlight",
    4: "lighten",
    5: "multiply",
    6: "overlay",
    7: "screen",
    8: "subtract",
    9: "normal",
    10: "softlight",
}


def _parok() -> tuple[np.ndarray, np.ndarray]:
    """Mind a 65 536 (b, t) pár, (256, 256, 1) alakú float32 „képként"."""
    b, t = np.meshgrid(np.arange(256), np.arange(256), indexing="ij")
    return (
        b.astype(np.float32)[..., np.newaxis],
        t.astype(np.float32)[..., np.newaxis],
    )


def _referencia_tabla(fuggveny) -> np.ndarray:
    return np.array([[fuggveny(b, t) for t in range(256)] for b in range(256)], dtype=np.float32)[
        ..., np.newaxis
    ]


def _atlatszosag_ref(b: np.ndarray, t: np.ndarray, alpha: float) -> np.ndarray:
    """`0x009dc4b0`: `w = trunc(256α)`, és ha `w > 0`, `w − 1`;
    `(b·(255−w) + t·w) >> 8`."""
    w = int(np.float32(alpha) * np.float32(256.0))
    if w > 0:
        w -= 1
    bi = b.astype(np.int64)
    ti = t.astype(np.int64)
    return ((bi * (255 - w) + ti * w) >> 8).astype(np.float32)


# --- A tizenegy mód, kimerítően -----------------------------------------------


class TestTizenegyModKimeritoen:
    @pytest.mark.parametrize("mod", sorted(_REFERENCIA))
    def test_mind_a_65536_paron_bitre(self, mod):
        b, t = _parok()
        ki = g.apply_blend_mode(b, t, mod, 1.0)
        np.testing.assert_array_equal(ki, _referencia_tabla(_REFERENCIA[mod]))

    @pytest.mark.parametrize("sorszam", sorted(_SORSZAM))
    def test_a_mod_sorszammal_is_megadhato(self, sorszam):
        b, t = _parok()
        np.testing.assert_array_equal(
            g.apply_blend_mode(b, t, sorszam, 1.0),
            g.apply_blend_mode(b, t, _SORSZAM[sorszam], 1.0),
        )

    def test_a_sorszam_tabla_a_nativ_sorrend(self):
        assert g.BLEND_MODE_BY_INDEX == _SORSZAM

    @pytest.mark.parametrize("sorszam", [-1, 11])
    def test_ismeretlen_sorszam_hiba(self, sorszam):
        b, t = _parok()
        with pytest.raises(ValueError):
            g.apply_blend_mode(b, t, sorszam, 1.0)

    def test_a_softlight_eldobja_az_also_elem_legalso_bitjet(self):
        b = np.array([[[100.0, 101.0]]], dtype=np.float32)
        t = np.array([[[200.0, 200.0]]], dtype=np.float32)
        ki = g.apply_blend_mode(b, t, "softlight", 1.0)
        assert ki[0, 0, 0] == ki[0, 0, 1]

    def test_overlay_255_255_kulon_ag(self):
        b = np.array([[[255.0]]], dtype=np.float32)
        assert g.apply_blend_mode(b, b, "overlay", 1.0)[0, 0, 0] == 255.0

    def test_a_kimenet_float32(self):
        b, t = _parok()
        assert g.apply_blend_mode(b, t, "multiply", 1.0).dtype == np.float32


# --- Átlátszóság-keverés ------------------------------------------------------


class TestAtlatszosagKevereseEgesz:
    @pytest.mark.parametrize("alpha", [0.25, 0.5, 0.6, 0.75, 0.9, 0.01, 0.999])
    def test_alpha_blend_kimeritoen(self, alpha):
        b, t = _parok()
        np.testing.assert_array_equal(g.alpha_blend(b, t, alpha), _atlatszosag_ref(b, t, alpha))

    @pytest.mark.parametrize("alpha", [0.25, 0.5, 0.9])
    @pytest.mark.parametrize("mod", ["multiply", "screen", "softlight", "normal"])
    def test_mod_utani_atlatszosag(self, mod, alpha):
        b, t = _parok()
        kevert = _referencia_tabla(_REFERENCIA[mod])
        np.testing.assert_array_equal(
            g.apply_blend_mode(b, t, mod, alpha), _atlatszosag_ref(b, kevert, alpha)
        )

    def test_ket_255_os_bemenetbol_254(self):
        """A súlyok összege 255, az osztó 256 (spec D)."""
        b = np.full((1, 1, 1), 255.0, dtype=np.float32)
        assert g.alpha_blend(b, b, 0.5)[0, 0, 0] == 254.0

    def test_alfa_kozel_egy_a_felso_elem_valtozatlan(self):
        """`α ≈ 1` (bitmintán < 8 eltérés): a végrehajtó a keverést meg sem hívja."""
        b, t = _parok()
        kozel = struct.unpack(
            "<f", struct.pack("<i", struct.unpack("<i", struct.pack("<f", 1.0))[0] - 7)
        )[0]
        np.testing.assert_array_equal(g.alpha_blend(b, t, kozel), t)
        np.testing.assert_array_equal(g.apply_blend_mode(b, t, "normal", kozel), t)

    def test_alfa_kozel_nulla_az_also_elem(self):
        b, t = _parok()
        np.testing.assert_array_equal(g.alpha_blend(b, t, 0.0), b)
        np.testing.assert_array_equal(g.apply_blend_mode(b, t, "screen", 0.0), b)

    def test_az_alfa_vagva(self):
        b, t = _parok()
        np.testing.assert_array_equal(g.alpha_blend(b, t, 100.0), t)
        np.testing.assert_array_equal(g.alpha_blend(b, t, -3.0), b)


# --- Maszkolt keverés ---------------------------------------------------------


class TestMaszkoltKevereseEgesz:
    def test_mind_a_256_maszkertekre_kimeritoen(self):
        b, t = _parok()
        bi = b.astype(np.int64)
        ti = t.astype(np.int64)
        for m in range(256):
            maszk = np.full(b.shape[:2], m, dtype=np.uint8)
            vart = ((ti * m + bi * (255 - m)) // 255).astype(np.float32)
            np.testing.assert_array_equal(g.masked_blend(b, t, maszk), vart, err_msg=f"m={m}")

    def test_float_maszk_bajtra_kerekitve(self):
        b, t = _parok()
        maszk_f = np.full(b.shape[:2], 0.5, dtype=np.float32)
        maszk_b = np.full(b.shape[:2], 128, dtype=np.uint8)
        np.testing.assert_array_equal(g.masked_blend(b, t, maszk_f), g.masked_blend(b, t, maszk_b))
