"""#878 — a `Neon` visszafejtett csővezetéke és a két új Glimmer-primitív.

A jegy leletje: a `Neon` a #685 mérőszettjének LEGROSSZABB effektje volt
(ΔE 113,89, SSIM −0,002), mert a modell szerkezetileg volt hibás. A javítás
után ugyanazon a golden páron ΔE 4,72 / SSIM 0,866.

A mérőszett képei nem kerülhetnek a publikus repóba, ezért az itteni őrök a
csővezeték **szerkezeti** állításait rögzítik — azokat, amelyek a régi
(Canny + szorzó-tint) modellel elbuknak —, valamint a `TintImageOperation`
golden párból MÉRT számhármasait.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_creative import apply_neon
from picasapy.render.glimmer_edges import edge_detection_b
from picasapy.render.glimmer_ops import luma, tint_luma_preserving

REC601 = (0.299, 0.587, 0.114)


def _flat(value: int, height: int = 24, width: int = 32) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


def _hard_edge(height: int = 48, width: int = 64) -> np.ndarray:
    """Bal fele fekete, jobb fele fehér — egyetlen, maximálisan erős él."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, width // 2 :] = 255
    return image


def _luma_of(pixel) -> float:
    return float(sum(w * float(c) for w, c in zip(REC601, pixel, strict=True)))


class TestEdgeDetectionB:
    """`EdgeDetectionB` = FEHÉR alap, sötét élek (a háromszög-görbe miatt)."""

    def test_sik_felulet_feher_lesz(self):
        # A Sobel válasza sík felületen 0 → a 128-as eltolás után a
        # {(0,0),(128,255),(255,0)} görbe csúcsa: 255.
        result = edge_detection_b(_flat(120))
        assert result.min() >= 250, f"a sík felületnek fehérnek kell lennie, min={result.min()}"

    def test_eles_el_sotet_vonalat_ad(self):
        result = edge_detection_b(_hard_edge())
        middle = result[:, 30:34]
        assert middle.min() <= 5, f"az élnek sötétnek kell lennie, min={middle.min()}"

    def test_a_hatter_az_eltol_tavol_feher_marad(self):
        result = edge_detection_b(_hard_edge())
        assert result[:, :20].min() >= 250
        assert result[:, 44:].min() >= 250

    @pytest.mark.parametrize("detail", [-0.1, 100.1])
    def test_tartomanyon_kivuli_detail_hibat_dob(self, detail):
        with pytest.raises(ValueError, match="detail"):
            edge_detection_b(_flat(128), detail=detail)


class TestTintLumaPreserving:
    """`TintImageOperation`: a bemenet luminanciáját bájtra megőrzi."""

    @pytest.mark.parametrize("value", [0, 16, 64, 128, 200, 255])
    @pytest.mark.parametrize("color", [(128, 207, 255), (255, 0, 0), (0, 255, 0)])
    def test_a_luminancia_megmarad(self, value, color):
        result = tint_luma_preserving(_flat(value), color)
        assert abs(float(luma(result.astype(np.float32)).mean()) - value) <= 1.0

    def test_fekete_fekete_marad_es_feher_feher(self):
        # Ez a döntő különbség a szorzó-tinthez képest: a szorzó-tint a
        # feketéből is, a fehérből is TISZTA SZÍNT csinálna.
        assert tint_luma_preserving(_flat(0), (255, 0, 0)).max() == 0
        assert tint_luma_preserving(_flat(255), (255, 0, 0)).min() == 255

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(16, (0, 16, 65)), (128, (69, 147, 195)), (248, (231, 255, 255))],
    )
    def test_mert_golden_harmasok(self, value, expected):
        """A #685 `picniktint__alap.jpg` golden párjából mért mediánok
        (`PicnikTint=1,0.000000,0080cfff;`, szín RGB `(128, 207, 255)`).
        A 248-as sor a döntő: két csatorna 255-ön áll, a harmadik pontosan
        arra az értékre, amellyel a luminancia visszajön.
        """
        result = tint_luma_preserving(_flat(value), (128, 207, 255))[0, 0]
        assert np.allclose(result, expected, atol=3), f"{tuple(int(c) for c in result)} != {expected}"
        assert abs(_luma_of(result) - value) <= 1.5


class TestNeon:
    def test_fade_100_bajtra_valtozatlan(self):
        image = _hard_edge()
        np.testing.assert_array_equal(apply_neon(image, fade=100.0), image)

    def test_sik_felulet_feketere_valt(self):
        """A régi Canny-modell itt FEHÉR (invertált, tint nélkül üres)
        képet adott; a valódi Neon sík felületen FEKETE."""
        result = apply_neon(_flat(120), fade=0.0)
        assert result.max() <= 5, f"a sík felületnek feketének kell lennie, max={result.max()}"

    def test_az_el_vilagos_vonalkent_marad_meg(self):
        result = apply_neon(_hard_edge(), fade=0.0)
        assert result[:, 30:34].max() >= 200
        assert result[:, :20].max() <= 5

    def test_a_fade_monoton_halvanyit(self):
        """0 → 100 között a kimenet MONOTON közelít az eredetihez."""
        image = _hard_edge()
        source = image.astype(np.int32)
        distances = [
            float(np.abs(apply_neon(image, fade=fade).astype(np.int32) - source).mean())
            for fade in (0.0, 25.0, 50.0, 75.0, 100.0)
        ]
        assert distances == sorted(distances, reverse=True), distances
        assert distances[-1] == 0.0

    def test_a_szin_a_kozepes_eleket_festi(self):
        """A neonszín a NEM telített éleken látszik: zöld színnel a zöld
        csatorna vezet. (Szorzó-tinttel a fehér élmag is színes lenne.)"""
        gradient = np.tile(
            np.linspace(0, 255, 64, dtype=np.uint8)[np.newaxis, :, np.newaxis], (48, 1, 3)
        )
        result = apply_neon(gradient, color=(0, 255, 0), fade=0.0).astype(np.int32)
        colored = result[..., 1] > result[..., 0]
        assert colored.any(), "a neonszínnek meg kell jelennie a képen"
