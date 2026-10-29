"""#6009: az eredeti radiális forrás-/célgradiens-keverés."""

from __future__ import annotations

import numpy as np

import picasapy.render.retouch as retouch


def test_smoothstep_suly_a_binari_sugarhatarain() -> None:
    weight = getattr(retouch, "_retouch_gradient_weight", None)
    assert callable(weight), "hiányzik a #6009 radiális súlyfüggvénye"

    distances = np.array([0.0, 11.25, 16.875, 22.5, 25.0])
    actual = weight(distances, radius=25.0)

    # r=25: R=min(0.9r, r-1)=22.5, a=sR=11.25, s=0.5.
    np.testing.assert_allclose(actual, [0.0, 0.0, 0.5, 1.0, 1.0], atol=1e-12)


def test_szin_tetikus_folt_peremen_a_forrasgradiens_celre_valt() -> None:
    mix = getattr(retouch, "_mix_retouch_gradients", None)
    assert callable(mix), "hiányzik a #6009 gradienskeverő függvénye"

    # Két mesterséges RGB-foltrámpa: a forrás +2, a cél -4 szintet változik
    # élpáronként. A középső él még forrást, a perem felőli él már célgradienst
    # adjon; a smoothstep közepe a két irány átlagát adja.
    source_ramp = np.arange(4, dtype=np.float32)[:, None] * np.array(
        [[2.0, 0.0, 0.0]], dtype=np.float32
    )
    target_ramp = 200.0 - np.arange(4, dtype=np.float32)[:, None] * np.array(
        [[4.0, 0.0, 0.0]], dtype=np.float32
    )
    source_gradient = np.diff(source_ramp, axis=0)
    target_gradient = np.diff(target_ramp, axis=0)
    distance = np.array([0.5, 16.875, 22.5])

    actual = mix(source_gradient, target_gradient, distance, radius=25.0)

    np.testing.assert_allclose(actual[:, 0], [2.0, -1.0, -4.0], atol=1e-6)
    np.testing.assert_allclose(actual[:, 1:], 0.0, atol=1e-6)
