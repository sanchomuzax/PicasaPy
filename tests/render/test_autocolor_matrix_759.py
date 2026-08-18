"""#759 — az `autocolor` 3×3 színmátrixa és a csonkoló egész-osztás.

Az `autocolor` **nem** három független csatorna-erősítés, hanem egy
`M · diag(g) · M⁻¹` színmátrix, amibe a becsült erősítések a mátrix
TERÉBEN épülnek be. Ezért nem ment 2,35 alá semmilyen csatornánkénti
modell: hiányoztak a kereszt-tagok.

Mért eredmény a 12 golden páron (`referencia/imfeellucky/ImFeelLucky-noeffect/`
→ `referencia/autocolor/AutoColor/`, a mérőszkript a privát repóban):

| modell | átlagos csatorna-eltérés |
|---|---:|
| érintetlen kép | 5,287 |
| a korábbi, csatornánkénti modellünk (#541) | 2,352 |
| `M⁻¹ · diag(g) · M` (rossz sorrend) | 2,169 |
| **`M · diag(g) · M⁻¹`, padlózó osztással** | 1,370 |
| **`M · diag(g) · M⁻¹`, CSONKOLÓ osztással** | **0,614** |

A 0,614 a JPEG-újratömörítés zajszintje (~0,69) ALATT van.

A golden képek nem kerülhetnek a publikus repóba, ezért az itteni őrök a
**képfüggetlen** állításokat rögzítik — azokat, amelyek a hibás modellel
elbuknak.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.autocolor_matrix import (
    AUTOCOLOR_MATRIX,
    autocolor_matrix_16_16,
    c_divide,
    estimate_illuminant,
)


class TestCsonkoloOsztas:
    """A C `/` (x86 `idiv`) NULLA FELÉ csonkol, a Python `//` PADLÓZ.

    Ez a különbség adta a maradék hiba több mint felét (1,370 → 0,614):
    negatív számlálónál a kettő 1-gyel tér el, és ez végigfut a képen.
    """

    @pytest.mark.parametrize(
        ("szamlalo", "oszto", "vart"),
        [(7, 2, 3), (-7, 2, -3), (7, -2, -3), (-7, -2, 3), (0, 5, 0), (-1, 2, 0)],
    )
    def test_nulla_fele_csonkol(self, szamlalo, oszto, vart):
        assert int(c_divide(szamlalo, oszto)) == vart

    def test_negativnal_ELTER_a_python_padlozastol(self):
        """Ez a teszt a hibát nevezi meg: `//` itt −4-et adna."""
        assert int(c_divide(-7, 2)) == -3
        assert -7 // 2 == -4

    def test_tombon_is_mukodik(self):
        szamlalo = np.array([-7, 7, -1, 0])
        eredmeny = c_divide(szamlalo, 2)
        np.testing.assert_array_equal(eredmeny, np.array([-3, 3, 0, 0]))


class TestMatrix:
    def test_a_kilenc_konstans(self):
        """A natív `0x0090eda0` legelső dolga ezt a kilenc floatot másolja
        egy kilenc elemű tömbbe (`rep movsd`, `ecx = 9`), SORFOLYTONOSAN."""
        vart = np.array(
            [[1.9044, 0.4508, -0.3826], [-0.0532, 1.8018, 0.1995], [0.0491, -0.3057, 1.8576]],
            dtype=np.float32,
        )
        np.testing.assert_allclose(AUTOCOLOR_MATRIX, vart, rtol=0, atol=0)

    def test_semleges_becsles_EGYSEGMATRIXOT_ad(self):
        """`kR = kG = kB = 128` → `g = 1` → `M · I · M⁻¹ = I`.

        Ez az `M⁻¹` irányának képfüggetlen bizonyítéka: a másik olvasat
        (`M · diag(g) · M`) itt `M²`-et adna, ami a középszürkét fehérre
        égetné."""
        A = autocolor_matrix_16_16(128, 128, 128)
        np.testing.assert_array_equal(A, np.diag([65536, 65536, 65536]))

    def test_float32_KELL_kulonben_65535(self):
        """A natív mag float32-ben számol. float64-gyel az egységmátrix
        0,99999999-re jön ki, és a csonkítás 65535-öt adna 65536 helyett —
        ez képpontonként egy szintnyi, rendszeres sötétítés."""
        A = autocolor_matrix_16_16(128, 128, 128)
        assert A[0, 0] == 65536, f"{A[0, 0]} — float64-es számítás jele"

    def test_szinontet_eseten_NEM_egysegmatrix(self):
        A = autocolor_matrix_16_16(148, 128, 124)
        assert not np.array_equal(A, np.diag([65536, 65536, 65536]))

    def test_a_kereszt_tagok_NEM_nullak(self):
        """A lényeg: ez NEM három független csatorna-erősítés. Egy
        csatornánkénti modell átlós mátrixot adna."""
        A = autocolor_matrix_16_16(148, 128, 124)
        atlon_kivul = A - np.diag(np.diag(A))
        assert np.abs(atlon_kivul).max() > 0, "a kereszt-tagok hiányoznak"


class TestBecslo:
    def test_szurke_kepre_semleges(self):
        kep = np.full((32, 32, 3), 128, dtype=np.uint8)
        assert estimate_illuminant(kep) == (128, 128)

    def test_ures_maszk_eseten_semleges(self):
        """Csupa sötét kép: a `32 ≤ G ≤ 224` feltétel senkit nem enged át."""
        assert estimate_illuminant(np.zeros((16, 16, 3), dtype=np.uint8)) == (128, 128)

    def test_szinontetet_eszrevesz(self):
        rng = np.random.default_rng(5)
        kep = rng.integers(90, 170, size=(64, 64, 3), dtype=np.uint8)
        kep[..., 0] = np.clip(kep[..., 0].astype(np.int16) + 30, 0, 255)  # vörös öntet
        kR, kB = estimate_illuminant(kep)
        assert kR > 128, f"a vörös öntetet észre kell venni (kR={kR})"


class TestAlkalmazas:
    def test_semleges_kepen_BAJTRA_valtozatlan(self):
        """A #759 mellékelete: a KORÁBBI modellünk egy semleges mérőképen
        0,812-nyit elmozdított, pedig a Picasa hozzá sem nyúlt (0,238 =
        JPEG-zaj). A mátrix-modellnél ez szerkezetileg lehetetlen."""
        from picasapy.render.ops import apply_autocolor

        rng = np.random.default_rng(11)
        szurke = rng.integers(60, 200, size=(48, 48), dtype=np.uint8)
        kep = np.stack([szurke, szurke, szurke], axis=-1)
        np.testing.assert_array_equal(apply_autocolor(kep), kep)

    def test_alak_es_tipus_megmarad(self):
        from picasapy.render.ops import apply_autocolor

        rng = np.random.default_rng(3)
        kep = rng.integers(0, 255, size=(24, 32, 3), dtype=np.uint8)
        eredmeny = apply_autocolor(kep)
        assert eredmeny.shape == kep.shape and eredmeny.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self):
        from picasapy.render.ops import apply_autocolor

        rng = np.random.default_rng(4)
        kep = rng.integers(0, 255, size=(24, 32, 3), dtype=np.uint8)
        eredeti = kep.copy()
        apply_autocolor(kep)
        np.testing.assert_array_equal(kep, eredeti)
