"""A `picasapy.render.color.apply_grain` (`grain`/`grain2`) tesztjei a
golden-elemzés dokumentált spec-je ellen (`docs/specs/filters-decoded.md`,
„⛳ `grain` / `grain2` — a munkafüggvény kiolvasva", #3927/#3928): a szemcse
sztochasztikus, pixelhűen NEM reprodukálható — az elfogadás statisztikai
(tónussávonkénti szórás, szomszéd-korreláció, átlagos eltolás), nem
pixel-diff. A régi (#3928 ELŐTTI) modell EGYENLETES, korrelálatlan,
tónusfüggetlen Gauss-zaj volt — az alábbi statisztikai tesztek pont ezt a
három tulajdonságot (csomósság, középtónus-súlyozás, sötétítő eltolás)
különböztetik meg tőle, rögzített maggal reprodukálhatóan.

rontás-kontroll (#3928): a `native_grain._simit_haromszor` háromszori
kétirányú simítását kikapcsolva (egyetlen menetre csökkentve) vagy a
`_K_BEEGETETT`-et 0-ra állítva a `TestApplyGrainCsomosSzemcse` mindhárom
teszte elbukik — a korreláció 0,15 alá esik, a közép/szél szórásarány
1,5 alá, az eltolás −1,0 fölé megy."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.color import apply_grain


def _uniform_image(value: int | tuple[int, int, int], size: int = 40) -> np.ndarray:
    return np.full((size, size, 3), value, dtype=np.uint8)


def _gradient_image(width: int = 256, height: int = 150) -> np.ndarray:
    """Egy teljes 0–255 tartományú sor, sokszor ismételve (stabil sávstatisztika)."""
    row = np.arange(min(width, 256), dtype=np.uint8)
    if width > 256:
        row = np.resize(row, width)
    tile = np.tile(row, (height, 1))
    return np.stack([tile, tile, tile], axis=-1).astype(np.uint8)


def _diff_mean_channels(result: np.ndarray, image: np.ndarray) -> np.ndarray:
    return result.astype(np.float64).mean(axis=2) - image.astype(np.float64).mean(axis=2)


def _neighbor_correlation(field: np.ndarray) -> tuple[float, float]:
    horizontal = float(np.corrcoef(field[:, :-1].ravel(), field[:, 1:].ravel())[0, 1])
    vertical = float(np.corrcoef(field[:-1, :].ravel(), field[1:, :].ravel())[0, 1])
    return horizontal, vertical


class TestApplyGrain:
    def test_alak_es_dtype_megmarad(self) -> None:
        image = _uniform_image(128)
        result = apply_grain(image, seed=1)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(128)
        original = image.copy()
        apply_grain(image, seed=1)
        np.testing.assert_array_equal(image, original)

    def test_azonos_mag_reprodukalhato(self) -> None:
        image = _uniform_image(128)
        first = apply_grain(image, seed=42)
        second = apply_grain(image, seed=42)
        np.testing.assert_array_equal(first, second)

    def test_elteroe_mag_elteroe_kimenet(self) -> None:
        image = _uniform_image(128)
        first = apply_grain(image, seed=1)
        second = apply_grain(image, seed=2)
        assert not np.array_equal(first, second)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_grain(np.zeros((4, 4), dtype=np.uint8))


class TestApplyGrainCsomosSzemcse:
    """A csomós, középtónusban erős szemcse — a spec „kiolvasott algoritmus"
    oszlopa szerint (#3928). Mindhárom teszt megbukik a #3928 előtti,
    egyenletes/korrelálatlan/tónusfüggetlen Gauss-zajos modellel."""

    def test_szomszed_korrelacio_csomos(self) -> None:
        """A régi modell korrelálatlan (≈0,0); a kiolvasott algoritmus
        vízszintesen 0,25–0,28, függőlegesen 0,27–0,28 körül korrelál."""
        image = _gradient_image()
        result = apply_grain(image, seed=42)
        diff = _diff_mean_channels(result, image)
        horizontal, vertical = _neighbor_correlation(diff)
        assert horizontal > 0.15, f"vízszintes korreláció {horizontal:.3f} <= 0,15"
        assert vertical > 0.15, f"függőleges korreláció {vertical:.3f} <= 0,15"

    def test_kozeptonus_eroesebb_a_szeleknel(self) -> None:
        """A súly a középtónusban 160/256, a két végén 32/256 — a
        középtónus szórásának a szélek szórásának legalább 2,5-szörösét
        kell elérnie. A régi modell tónusfüggetlen (az arány ≈1,0)."""
        low = apply_grain(_uniform_image(10, size=150), seed=42)
        mid = apply_grain(_uniform_image(128, size=150), seed=42)
        high = apply_grain(_uniform_image(245, size=150), seed=42)

        sigma_low = float(_diff_mean_channels(low, _uniform_image(10, size=150)).std())
        sigma_mid = float(_diff_mean_channels(mid, _uniform_image(128, size=150)).std())
        sigma_high = float(_diff_mean_channels(high, _uniform_image(245, size=150)).std())

        assert sigma_mid > 2.5 * sigma_low, f"σ_közép={sigma_mid:.2f}, σ_alacsony={sigma_low:.2f}"
        assert sigma_mid > 2.5 * sigma_high, f"σ_közép={sigma_mid:.2f}, σ_magas={sigma_high:.2f}"

    def test_atlagos_eltolas_sotetit(self) -> None:
        """A Picasa a képet átlagban ~2 szinttel sötétíti (mérve: −1,96); a
        régi modell átlaga ≈0."""
        image = _gradient_image()
        result = apply_grain(image, seed=42)
        shift = float(result.astype(np.float64).mean() - image.astype(np.float64).mean())
        assert shift < -1.0, f"átlagos eltolás {shift:.3f} nem elég negatív"
        assert shift > -3.0, f"átlagos eltolás {shift:.3f} irreálisan nagy"


#: A 684-es mérőkészlet NAS-os elérése — a session csak ezt az egy,
#: névvel ismert mappát nyitja meg (a NAS más ága nem járható be).
_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: A jegy „kiolvasott algoritmus" oszlopa (0–40 / 40–90 / 90–170 / 170–215 /
#: 215–255 tónussáv), a szomszéd-korreláció és az átlagos eltolás.
_VART_SZORAS_SAVONKENT = (2.5, 4.4, 5.5, 4.4, 2.4)
_SAVOK = ((0, 40), (40, 90), (90, 170), (170, 215), (215, 255))
_VART_KORRELACIO = (0.28, 0.28)
_VART_ELTOLAS = -1.96
_TURES_SZORAS_KORRELACIO = 0.3
_TURES_ELTOLAS = 0.1
_VART_DE_HATAR = 2.70


def _golden_eszkozok():
    gyoker = Path(__file__).resolve().parents[2]
    utvonal = str(gyoker / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
class TestApplyGrain684Merokeszlet:
    """A jegy „Kész, ha" pontjai a valódi `grain__alap` Picasa-exporttal."""

    def test_delta_e_legfeljebb_2_70(self) -> None:
        load, mean_de = _golden_eszkozok()
        forras = load(_KIT / "grain__alap.jpg")
        export = load(_KIT / "export" / "grain__alap.jpg")
        eredmeny = apply_grain(forras, seed=0)
        de = mean_de(eredmeny, export)
        assert de <= _VART_DE_HATAR, f"ΔE {de:.3f} > {_VART_DE_HATAR}"

    def test_tonussavonkenti_szoras_es_korrelacio_es_eltolas(self) -> None:
        load, _ = _golden_eszkozok()
        forras = load(_KIT / "grain__alap.jpg")
        eredmeny = apply_grain(forras, seed=0)
        diff = _diff_mean_channels(eredmeny, forras)
        src_luma = forras.astype(np.float64).mean(axis=2)

        for (lo, hi), vart in zip(_SAVOK, _VART_SZORAS_SAVONKENT, strict=True):
            mask = (src_luma >= lo) & (src_luma < hi)
            szoras = float(diff[mask].std())
            also = vart - _TURES_SZORAS_KORRELACIO
            felso = vart + _TURES_SZORAS_KORRELACIO
            assert also <= szoras <= felso, (
                f"sáv {lo}-{hi}: szórás {szoras:.3f} nincs [{also:.2f}, {felso:.2f}]-ben"
            )

        horizontal, vertical = _neighbor_correlation(diff)
        for irany, mert, vart in zip(
            ("vízszintes", "függőleges"), (horizontal, vertical), _VART_KORRELACIO, strict=True
        ):
            also = vart - _TURES_SZORAS_KORRELACIO
            felso = vart + _TURES_SZORAS_KORRELACIO
            assert also <= mert <= felso, f"{irany} korreláció {mert:.3f} nincs [{also:.2f}, {felso:.2f}]-ben"

        eltolas = float(diff.mean())
        also = _VART_ELTOLAS - _TURES_ELTOLAS
        felso = _VART_ELTOLAS + _TURES_ELTOLAS
        assert also <= eltolas <= felso, f"átlagos eltolás {eltolas:.3f} nincs [{also:.2f}, {felso:.2f}]-ben"
