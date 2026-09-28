"""A `picasapy.render.sharpen` élesítés-tesztjei.

#3851: a natív keverés (`0x0090c4a0`, spec `filters-decoded.md`, „`unsharp` /
`unsharp2` — a keverés és az erősség kiolvasva"): `K = csonk(512 · s)`,
`ki = clamp(A + (((A − B) · K) >> 8), 0, 255)`, az erősítés tehát `2·s`
(nem a mérésből illesztett `1,21·s`). Az elmosás (B) az átméretező 2-es módja
(köbös B-spline) 1 : 1 léptéken, `1/(1,5 + 0,001)` szélesítéssel, FIXPONTOSAN:
`csonk(w·16383/Σw)`, `(Σ w·p + 255) >> 14`, előbb vízszintesen, 8 bites
köztes képpel (`filterdesc-registry.md` 5/c).

Mérve (CIE76 átlag-ΔE a Picasa-exporthoz, 684-es készlet):

| eset | előtte (`1,21·s`, lebegőpontos) | utána (`2·s`, fixpontos) |
|---|---:|---:|
| `unsharp2` alap (s = 0,6) | 0,359 | **0,172** |
| `unsharp2` max (s = 3,0) | 0,983 | **0,277** |
| `unsharp` (v1) alap | 0,359 | **0,172** |
| `unsharp2` min (s = 0) | 0,121 | 0,121 |
"""

# rontás-kontroll: a `sharpen._KEVERES_SKALA` 512-ről 310-re (≈ 1,21·256)
# átírva → 19 failed ebben a fájlban (a jegy példái, a negatív eltolás, a
# bitre menő referencia mind a 13 esete, a golden alap/max/v1); a
# `_FIX_KEREKITO` 255-ről 0-ra → 16 failed e fájlban és a
# `test_unsharp_bspline_762.py`-ban (a homogén folt, 10 referencia-eset, a
# golden alap/max/v1); a `_SZELESITO_TOBBLET` 0,001-ről 0-ra → 9 failed
# (7 referencia-eset és a fixpontos súlyok/szórás) — a goldent ez nem mozdítja.

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import sharpen
from picasapy.render.chain import apply_filters
from picasapy.render.sharpen import (
    UNSHARP_V1_STRENGTH,
    apply_unsharp,
    unsharp_blend,
)


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


# ---------------------------------------------------------------------------
# #3851 — a natív keverés és a fixpontos elmosás, független referenciával
# ---------------------------------------------------------------------------


def _bspline(x: float) -> float:
    x = abs(x)
    if x >= 2.0:
        return 0.0
    if x >= 1.0:
        return (2.0 - x) ** 3 / 6.0
    return (4.0 - 6.0 * x * x + 3.0 * x**3) / 6.0


def _ref_sulymatrix(n: int) -> np.ndarray:
    """Tengelyenkénti (n × n) egész súlymátrix, képpontonként külön
    normálva: a képen kívüli csap kimarad, a maradék a középső csapé."""
    lepték = 1.5 + 0.001
    matrix = np.zeros((n, n), dtype=np.int64)
    for i in range(n):
        csapok = [j for j in range(i - 3, i + 4) if 0 <= j < n]
        nyers = np.array([_bspline((j - i) / lepték) for j in csapok])
        egesz = np.trunc(nyers * 16383 / nyers.sum()).astype(np.int64)
        egesz[csapok.index(i)] += 16383 - int(egesz.sum())
        matrix[i, csapok] = egesz
    return matrix


def _ref_elmosas(kep: np.ndarray) -> np.ndarray:
    h, w = kep.shape[:2]
    vizszintes = np.einsum("ij,hjc->hic", _ref_sulymatrix(w), kep.astype(np.int64))
    koztes = (np.clip(vizszintes + 255, 0, 0x3FFFFF) >> 14).astype(np.uint8)
    fuggoleges = np.einsum("ij,jwc->iwc", _ref_sulymatrix(h), koztes.astype(np.int64))
    return (np.clip(fuggoleges + 255, 0, 0x3FFFFF) >> 14).astype(np.uint8)


def _ref_unsharp(kep: np.ndarray, s: float) -> np.ndarray:
    k = int(512 * s)
    a = kep.astype(np.int64)
    return np.clip(a + (((a - _ref_elmosas(kep)) * k) >> 8), 0, 255).astype(np.uint8)


class TestNativKeveres3851:
    @pytest.mark.parametrize(("s", "vart"), [(0.6, 111), (3.0, 160)])
    def test_a_jegy_peldaja(self, s: float, vart: int) -> None:
        a = np.full((1, 1, 3), 100, dtype=np.uint8)
        b = np.full((1, 1, 3), 90, dtype=np.uint8)
        assert int(unsharp_blend(a, b, s)[0, 0, 0]) == vart

    def test_a_negativ_kulonbseg_aritmetikai_eltolas(self) -> None:
        """`(−10 · 307) >> 8 = ⌊−11,99⌋ = −12` (a `sar` lefelé kerekít)."""
        a = np.full((1, 1, 3), 90, dtype=np.uint8)
        b = np.full((1, 1, 3), 100, dtype=np.uint8)
        assert int(unsharp_blend(a, b, 0.6)[0, 0, 0]) == 78

    def test_klippel_mindket_iranyban(self) -> None:
        a = np.array([[[250, 5, 128]]], dtype=np.uint8)
        b = np.array([[[200, 60, 128]]], dtype=np.uint8)
        np.testing.assert_array_equal(unsharp_blend(a, b, 3.0), [[[255, 0, 128]]])

    def test_az_illesztett_1_21_eltunt(self) -> None:
        assert not hasattr(sharpen, "_UNSHARP_AMOUNT_PER_STRENGTH")

    @pytest.mark.parametrize("s", [0.6, 1.0, 3.0])
    @pytest.mark.parametrize("alak", [(11, 13), (5, 4), (1, 9), (40, 37)])
    def test_bitre_a_referencia(self, s: float, alak: tuple[int, int]) -> None:
        rng = np.random.default_rng(3851 + alak[0] * 100 + alak[1])
        kep = rng.integers(0, 256, size=(*alak, 3), dtype=np.uint8)
        np.testing.assert_array_equal(apply_unsharp(kep, s), _ref_unsharp(kep, s))

    def test_bitre_a_referencia_sima_kepen(self) -> None:
        """Sima gradiens + él: itt a kerekítés (+255) és a köztes 8 bites
        kép számít, nem a zaj."""
        y, x = np.mgrid[0:24, 0:31]
        kep = np.stack([(x * 7) % 256, (y * 9) % 256, ((x + y) * 5) % 256], axis=-1)
        kep = kep.astype(np.uint8)
        kep[:, 15:] = np.clip(kep[:, 15:].astype(int) + 60, 0, 255).astype(np.uint8)
        np.testing.assert_array_equal(apply_unsharp(kep, 3.0), _ref_unsharp(kep, 3.0))


# ---------------------------------------------------------------------------
# FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal; ha a készlet
# nincs a gépen, skip.
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: A mért érték + 0,05-ös tűrés.
_TURES = 0.05

#: (név, lánc, mért ΔE) — a jegy küszöbe: alap ≤ 0,2, max ≤ 0,3.
_GOLDEN_ESETEK = [
    ("unsharp2__alap", "unsharp2=1,0.600000;", 0.172),
    ("unsharp2__max", "unsharp2=1,3.000000;", 0.277),
    ("unsharp__alap", "unsharp=1,0.600000;", 0.172),
    ("unsharp2__min", "unsharp2=1,0.000000;", 0.121),
]


def _golden_eszkozok():
    gyoker = Path(__file__).resolve().parents[2]
    utvonal = str(gyoker / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


@pytest.mark.parametrize(
    ("nev", "lanc", "vart_de"), _GOLDEN_ESETEK, ids=[e[0] for e in _GOLDEN_ESETEK]
)
def test_golden_684_a_hatarertek_alatt(nev: str, lanc: str, vart_de: float) -> None:
    export_ut = _KIT / "export" / f"{nev}.jpg"
    if not export_ut.is_file():
        pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
    load, mean_de = _golden_eszkozok()
    kep = apply_filters(load(_KIT / f"{nev}.jpg"), parse_filters(lanc)).image
    de = mean_de(kep, load(export_ut))
    assert de <= vart_de + _TURES, f"{nev}: ΔE {de:.3f} > {vart_de + _TURES:.3f}"
