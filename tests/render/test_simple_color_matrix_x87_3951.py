"""#3951 (átnézés, J1): a `SimpleColorMatrix` mátrix-összefűzése a NATÍV
sorrendben és pontossággal (`0x008f28d0`): x87-FPU, `G ← G × Ú`, az összegzés
`l = 0…3` sorrendben, a gyűjtő `0,0`-ról indul (`[0xcf3a60]`), és minden
részösszeg float32-be tárolódik (`fstp dword`). `M = S · C · B` (linked:
`M = S · L`).

Rontás-kontroll: az eltolás régi `k·b + t` alakú számolásával (a telítettség
soronkénti összegét 1-nek véve) a két értékes eset (−40,374996 / b = −159, és
b = 180) pirosra vált.
"""

from __future__ import annotations

import numpy as np

from picasapy.render import glimmer_ops as g

F32 = np.float32


def _egyseg4() -> np.ndarray:
    return np.eye(4, dtype=F32)


class TestSzorzasX87:
    def test_a_reszosszeg_float32_ba_tarolodik(self):
        """`2^24 + 1 + 1`: float32-ben minden lépés visszakerekít `2^24`-re
        (a `+1` páros felé), float64-es gyűjtővel `2^24 + 2` jönne ki."""
        gm = np.zeros((4, 4), dtype=F32)
        gm[0, :3] = 1.0
        um = np.zeros((4, 4), dtype=F32)
        um[:3, 0] = [2.0**24, 1.0, 1.0]
        assert g._szorzas_x87(gm, um)[0, 0] == F32(2.0**24)

    def test_az_osszegzes_l_szerint_novekvo_sorrendben_megy(self):
        """Ugyanaz fordított sorrendben: `1 + 1 + 2^24` = `2^24 + 2`."""
        gm = np.zeros((4, 4), dtype=F32)
        gm[0, :3] = 1.0
        um = np.zeros((4, 4), dtype=F32)
        um[:3, 0] = [1.0, 1.0, 2.0**24]
        assert g._szorzas_x87(gm, um)[0, 0] == F32(2.0**24 + 2.0)

    def test_a_gyujto_kezdoerteke_pozitiv_nulla(self):
        """`0,0 + (−0,0) = +0,0`: a `−0,0`-ból induló gyűjtő előjelet adna."""
        gm = np.full((4, 4), -0.0, dtype=F32)
        um = _egyseg4()
        assert not np.signbit(g._szorzas_x87(gm, um)[0, 1])

    def test_azonossaggal_szorozva_valtozatlan(self):
        rng = np.random.default_rng(3)
        gm = rng.uniform(-3, 3, size=(4, 4)).astype(F32)
        np.testing.assert_array_equal(g._szorzas_x87(gm, _egyseg4()), gm)
        np.testing.assert_array_equal(g._szorzas_x87(_egyseg4(), gm), gm)

    def test_bal_es_jobb_tenyezo_nem_cserelheto(self):
        gm = np.arange(16, dtype=F32).reshape(4, 4)
        um = np.arange(16, 0, -1, dtype=F32).reshape(4, 4)
        expected = (gm.astype(np.float64) @ um.astype(np.float64)).astype(F32)
        np.testing.assert_array_equal(g._szorzas_x87(gm, um), expected)
        assert not np.array_equal(g._szorzas_x87(gm, um), g._szorzas_x87(um, gm))


class TestMatrixOsszefuzes:
    def test_nem_linked_s100_c25_b75(self):
        """Átnézés x87-emulációval mérve: az eltolás −40,374996 (nem −40,375),
        és `b = trunc(−40,374996·4 − 0,5) + 2 = −159` (nem −160)."""
        _matrix, offset = g._szinmatrix_osszefuzve(-100.0, -25.0, -75.0, linked=False)
        assert offset.dtype == F32
        assert offset.tolist() == [F32(-40.374996)] * 3
        assert offset[0] != F32(-40.375)
        assert g._fixpont_bias(offset).tolist() == [-159, -159, -159]

    def test_linked_s100_c100_b65(self):
        """`b = 180` (a `k·b + t` alak 181-et adna)."""
        _matrix, offset = g._szinmatrix_osszefuzve(-100.0, -100.0, -65.0, linked=True)
        assert offset.tolist() == [F32(44.624996)] * 3
        assert g._fixpont_bias(offset).tolist() == [180, 180, 180]

    def test_a_c_egyutthato_valtozatlan_f32_s_k(self):
        matrix, _offset = g._szinmatrix_osszefuzve(-100.0, -25.0, -75.0, linked=False)
        k = F32(1.0 + g._kontraszt_gorbe(-25.0))
        sat = g._saturation_matrix(-100.0)
        np.testing.assert_array_equal(matrix, sat * k)

    def test_telitettseg_nelkul_az_eltolas_k_b_plusz_t(self):
        """`S = I`: az összefűzés bitre azonos a régi `f32(k)·f32(b) + f32(t)`-vel."""
        _matrix, offset = g._szinmatrix_osszefuzve(None, 30.0, 20.0, linked=False)
        k = 1.0 + g._kontraszt_gorbe(30.0)
        t = (1.0 - k) * 127.0 * 0.5
        assert offset.tolist() == [F32(F32(k) * F32(20.0) + F32(t))] * 3

    def test_csak_fenyero_eltolas_b(self):
        matrix, offset = g._szinmatrix_osszefuzve(None, 0.0, 12.0, linked=False)
        np.testing.assert_array_equal(matrix, np.eye(3, dtype=F32))
        assert offset.tolist() == [F32(12.0)] * 3

    def test_a_kep_a_fixpontos_alkalmazon_a_fuzott_matrixszal_fut(self):
        rng = np.random.default_rng(5)
        image = rng.integers(0, 256, size=(6, 6, 3), dtype=np.uint8)
        matrix, offset = g._szinmatrix_osszefuzve(-100.0, -25.0, -75.0, linked=False)
        expected = g._fixpontos_szinmatrix(image, matrix, offset)
        result = g.simple_color_matrix(
            image, brightness=-75.0, contrast=-25.0, saturation=-100.0, linked=False
        )
        np.testing.assert_array_equal(result, expected)

    def test_a_presetek_c_egyutthatoja_int16_hatar_alatt_marad(self):
        """A natív `c`-t int16-ként tárolja (`0x008f240f`): `|c| < 32768`
        (a mai presetekben `|m| ≤ ~10,5`). Preset-jellegű állásokra mérve."""
        esetek = ((20.0, 35.0, 5.0), (-25.0, 0.0, 0.0), (0.0, 100.0, 0.0), (0.0, -100.0, 100.0))
        for saturation, contrast, brightness in esetek:
            matrix, _ = g._szinmatrix_osszefuzve(saturation, contrast, brightness, linked=False)
            assert np.abs(g._fixpont_egyutthato(matrix)).max() < 32768
