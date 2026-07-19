"""A `picasapy.render.sharpen` élesítés-tesztjei (unsharp/unsharp2 modell:
Gauss-alapú unsharp mask, σ≈1,0 px, erősítés ≈1,21·s — filters-decoded.md)."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.sharpen import UNSHARP_V1_STRENGTH, apply_unsharp


def _edge_image() -> np.ndarray:
    """Bal fele 100, jobb fele 200 — éles függőleges éllel."""
    image = np.full((10, 20, 3), 100, dtype=np.uint8)
    image[:, 10:] = 200
    return image


class TestApplyUnsharp:
    def test_homogen_kep_valtozatlan(self) -> None:
        image = np.full((8, 8, 3), 120, dtype=np.uint8)
        np.testing.assert_array_equal(apply_unsharp(image, 0.6), image)

    def test_elek_menten_noveli_a_kontrasztot(self) -> None:
        image = _edge_image()
        result = apply_unsharp(image, 0.6)
        # az él világos oldalán túllövés felfelé, a sötét oldalán lefelé
        assert int(result[5, 10, 0]) > 200
        assert int(result[5, 9, 0]) < 100

    def test_v1_alapertelmezes_0_6(self) -> None:
        # mérve: unsharp=1 (v1) bitre azonos az unsharp2=1,0.600000-val
        image = _edge_image()
        np.testing.assert_array_equal(
            apply_unsharp(image), apply_unsharp(image, UNSHARP_V1_STRENGTH)
        )

    def test_nulla_erosseg_identitas(self) -> None:
        image = _edge_image()
        np.testing.assert_array_equal(apply_unsharp(image, 0.0), image)

    def test_negativ_erosseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_unsharp(_edge_image(), -0.1)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _edge_image()
        original = image.copy()
        apply_unsharp(image, 1.0)
        np.testing.assert_array_equal(image, original)
