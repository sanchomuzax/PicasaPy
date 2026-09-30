"""A `resize_image` 5-ös módja: Lanczos-3 (#3998, spec 16. H) 3.).

Mag: `|x| >= 3` → 0, egyébként `sinc(π|x|) · sinc(π|x|/3)`; a sugár
kicsinyítéskor a léptékkel nyúlik; a súlyok fixpontosak (`csonk(w·16383/Σw)`,
a maradék a `csonk(c)` csapé), a kimenet `(Σ w·p + 255) >> 14`, előbb a
vízszintes menet. A referencia itt tiszta Python, a termékkódtól függetlenül.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from picasapy.render import glimmer_ops as ops


def _sinc(x: float) -> float:
    return 1.0 if x == 0 else math.sin(math.pi * x) / (math.pi * x)


def _mag(x: float) -> float:
    x = abs(x)
    return 0.0 if x >= 3 else _sinc(x) * _sinc(x / 3)


def _referencia_tengely(sor: list[int], ki: int) -> list[int]:
    be = len(sor)
    skala = np.float32(be) / np.float32(ki)
    nyujtas = max(1.0, float(skala))
    sugar = 3.0 * nyujtas
    kimenet = []
    for i in range(ki):
        c = float((np.float32(i) + np.float32(0.5)) * skala)
        csapok = [
            (j, _mag((j + 0.5 - c) / nyujtas))
            for j in range(be)
            if abs(j + 0.5 - c) < sugar
        ]
        osszeg = sum(w for _, w in csapok)
        egesz = {j: int(w * 16383 / osszeg) for j, w in csapok}
        maradek = 16383 - sum(egesz.values())
        cel = min(max(int(c), min(egesz)), max(egesz))
        egesz[cel] += maradek
        ertek = (sum(w * sor[j] for j, w in egesz.items()) + 255) >> 14
        kimenet.append(min(max(ertek, 0), 255))
    return kimenet


def test_a_mag_ertekei():
    x = np.array([0.0, 1.0, 2.0, 3.0, 3.5, 0.5, -0.5])
    ki = ops.lanczos3(x)
    assert ki[0] == pytest.approx(1.0)
    assert ki[1] == pytest.approx(0.0, abs=1e-12)
    assert ki[2] == pytest.approx(0.0, abs=1e-12)
    assert ki[3] == 0.0 and ki[4] == 0.0
    assert ki[5] == pytest.approx(_mag(0.5)) and ki[6] == ki[5]
    assert ki[5] == pytest.approx(0.6079271, abs=1e-6)
    assert ops.lanczos3(np.array([1.5]))[0] < 0  # negatív oldallebeny


@pytest.mark.parametrize("be,ki", [(10, 4), (23, 7), (16, 8), (9, 9), (7, 12)])
def test_a_tengely_megegyezik_a_tiszta_python_referenciaval(be, ki):
    rng = np.random.default_rng(be * 100 + ki)
    sor = [int(v) for v in rng.integers(0, 256, be)]
    kep = np.array(sor, dtype=np.uint8).reshape(1, be, 1).repeat(3, axis=2)
    ki_kep = ops.resize_image(kep, ki, 1, lanczos3=True)
    assert ki_kep[0, :, 0].tolist() == _referencia_tengely(sor, ki)


def test_ketto_tengely_elobb_vizszintes():
    rng = np.random.default_rng(7)
    kep = rng.integers(0, 256, (13, 17, 3), dtype=np.uint8)
    ki = ops.resize_image(kep, 6, 5, lanczos3=True)
    vizsz = np.array(
        [[_referencia_tengely(kep[y, :, c].tolist(), 6) for c in range(3)] for y in range(13)]
    ).transpose(0, 2, 1)
    var = np.array(
        [[_referencia_tengely(vizsz[:, x, c].tolist(), 5) for c in range(3)] for x in range(6)]
    ).transpose(2, 0, 1)
    assert ki.tolist() == var.tolist()


def test_allando_kep_allando_marad():
    kep = np.full((40, 60, 3), 123, dtype=np.uint8)
    assert (ops.resize_image(kep, 25, 17, lanczos3=True) == 123).all()


def test_azonos_meret_valtozatlan():
    kep = np.random.default_rng(1).integers(0, 256, (9, 11, 3), dtype=np.uint8)
    ki = ops.resize_image(kep, 11, 9, lanczos3=True)
    assert ki.tolist() == kep.tolist() and ki is not kep


def test_eles_elen_van_alul_es_tullovest_a_doboz_nem_ad():
    kep = np.zeros((4, 32, 3), dtype=np.uint8)
    kep[:, 16:] = 200
    lanc = ops.resize_image(kep, 8, 4, lanczos3=True)[0, :, 0].astype(int)
    doboz = ops.resize_image(kep, 8, 4)[0, :, 0].astype(int)
    assert doboz.max() <= 200 and doboz.min() >= 0
    assert lanc.max() > 200 and lanc.min() == 0  # túllövés az él mellett, alul a vágás


def test_az_alapertek_nem_valtozik():
    kep = np.random.default_rng(2).integers(0, 256, (20, 30, 3), dtype=np.uint8)
    a = ops.resize_image(kep, 10, 8)
    b = ops.resize_image(kep, 10, 8, lanczos3=False)
    assert a.tolist() == b.tolist()
