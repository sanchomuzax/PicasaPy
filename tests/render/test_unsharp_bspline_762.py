"""#762: az `unsharp` elmosómagja köbös B-spline, 3 képpont tartósugárral.

A mag MÉRVE van (a `sharpen` modul docstringje adja a címeket): az `unsharp`
az átméretezőt hívja 1 : 1 léptékkel, a **2-es** szűrőmóddal, és a beégetett
`1,5f` a szélesítő szorzóba megy — a tényleges tartósugár ezért **3 képpont**.

Az elfogadási feltétel a **SÚLYOKRA** van kimondva, nem ΔE-re: a #685
mérőszett képei nincsenek a repóban (csak a verdikt-JSON), tehát a váltás
ΔE-újramérése új exportot igényelne. Amit a ΔE-ről tudunk: a korábbi
Gauss-közelítés eltérése max erősségen 0,466 volt („JÓ" verdikt) — ez a
változás **finomítás, nem hibajavítás**.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from picasapy.render.sharpen import (
    UNSHARP_V1_STRENGTH,
    apply_unsharp,
    unsharp_blur,
    unsharp_blur_kernel,
)

#: A #762 mérésének súlyai, négy tizedesre.
MERT_SULYOK = (0.0, 0.0328, 0.2459, 0.4426, 0.2459, 0.0328, 0.0)


class TestAMag:
    def test_a_MERT_sulyok(self):
        kernel = unsharp_blur_kernel()
        assert len(kernel) == 7
        for kapott, vart in zip(kernel, MERT_SULYOK, strict=True):
            assert round(float(kapott), 4) == vart

    def test_a_sulyok_osszege_egy(self):
        assert float(unsharp_blur_kernel().sum()) == pytest.approx(1.0, abs=1e-6)

    def test_SZIMMETRIKUS(self):
        kernel = unsharp_blur_kernel()
        assert np.allclose(kernel, kernel[::-1])

    def test_a_SZORAS_0_8684_nem_1_0(self):
        """Ez a lényegi különbség a korábbi Gauss σ = 1,0-hoz képest: a mért
        mag egy hajszállal kevesebbet mos."""
        kernel = unsharp_blur_kernel().astype(np.float64)
        idx = np.arange(-3, 4)
        szoras = math.sqrt(float((kernel * idx * idx).sum()))
        assert round(szoras, 4) == 0.8684

    def test_a_KULSO_csap_pontosan_nulla(self):
        """`B₃(2) = 0`, tehát a mag valójában 5 csapos — a hetes szélesség a
        tartósugárból következik, nem többlet-elmosásból."""
        kernel = unsharp_blur_kernel()
        assert float(kernel[0]) == 0.0
        assert float(kernel[-1]) == 0.0

    def test_a_kozepso_csap_a_LEGNAGYOBB(self):
        kernel = unsharp_blur_kernel()
        assert float(kernel[3]) == float(kernel.max())

    def test_MONOTON_a_kozeptol_kifele(self):
        kernel = unsharp_blur_kernel().astype(np.float64)
        assert (np.diff(kernel[:4]) >= 0).all()


class TestAzElmosas:
    def test_a_mag_NEM_INTERPOLALO_tehat_1_1_arányban_is_mos(self):
        """Ez a hiányzó láncszem volt: a B-spline `w(±1) = 1/6 ≠ 0`, ezért
        1 : 1 léptéken is elmos — egy Lanczos-mag ugyanitt pontos másolatot
        adna, és akkor az `unsharp` nem élesítene semmit."""
        kep = np.zeros((9, 9, 3), np.uint8)
        kep[:, 5:] = 255  # lépcsős él
        elmosott = unsharp_blur(kep)
        #: az él MELLETTI képpont már nem 0 és nem 255
        assert 0 < float(elmosott[4, 4, 0]) < 255

    def test_az_EGYENLETES_folt_valtozatlan(self):
        """A súlyok összege 1 — konstans bemenetre az elmosás azonosság."""
        kep = np.full((8, 8, 3), 120, np.uint8)
        assert np.allclose(unsharp_blur(kep), 120.0, atol=0.01)


class TestAzElesites:
    def test_nulla_erossegnel_valtozatlan(self):
        kep = np.full((6, 6, 3), 100, np.uint8)
        assert np.array_equal(apply_unsharp(kep, 0.0), kep)

    def test_negativ_erosseget_elutasit(self):
        with pytest.raises(ValueError):
            apply_unsharp(np.zeros((4, 4, 3), np.uint8), -0.5)

    def test_az_EL_kontrasztja_NO(self):
        kep = np.zeros((9, 9, 3), np.uint8)
        kep[:, 5:] = 200
        elesitett = apply_unsharp(kep, 1.0)
        #: a világos oldalon túllő, a sötét oldalon alálő — ez az unsharp
        assert int(elesitett[4, 5, 0]) > 200
        assert int(elesitett[4, 4, 0]) == 0  # a 0 alá klippel

    def test_az_EGYENLETES_folt_elesitve_is_valtozatlan(self):
        kep = np.full((8, 8, 3), 77, np.uint8)
        assert np.array_equal(apply_unsharp(kep, 1.0), kep)

    def test_a_v1_erosseg_a_MERT_egyenertekes(self):
        assert UNSHARP_V1_STRENGTH == 0.6

    def test_a_kimenet_uint8(self):
        kep = np.full((5, 5, 3), 50, np.uint8)
        assert apply_unsharp(kep, 0.6).dtype == np.uint8
