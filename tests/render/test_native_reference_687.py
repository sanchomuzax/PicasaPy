"""A #687 pontonkénti modelljei a MÉRT Picasa-görbékhez képest.

A `tests/support/native_filter_reference/` a #685 mérőszettjének (valódi
Picasa 3.9-export) desztillált görbéit hordozza. Ez a készlet nem szintetikus
horgonyértékeket ellenőriz, hanem azt, hogy a modellek **a valódi kimenetet**
adják — és így fogja meg a kalibrációs konstansok elcsúszását:

* a `gamma` kitevőjének IRÁNYA (`exp(−szint)`, nem `exp(+szint)`),
* a `colortemp` két egészre skálázása (×256 és ×128).

Ezek egyike sem következik a dekompilátumból: a natív kódban az x87-veremen
mennek át, a Ghidra elveszti őket. Mérés nélkül tehát találgatás lenne — a
tesztkészlet ezért itt az igazságforrás.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.native_colortemp import apply_native_colortemp
from picasapy.render.native_tone import (
    apply_gamma,
    apply_native_contrast,
    apply_native_levels,
)
from tests.support.native_filter_reference import (
    MeasuredCase,
    measured_cases,
    pointwise_luts,
)

#: Esetenkénti hibakorlát a mért görbéhez képest (darabszámmal súlyozott
#: átlagos abszolút csatorna-eltérés a 0..255 skálán). Az értékek a MAI
#: modellek 2026-08-15-én mért hibájából származnak, ~50 % ráhagyással —
#: céljuk a regresszió elkapása, nem a jövőbeli javítás megakadályozása.
#: A mért érték zárójelben; mindegyik a szett saját JPEG-zaja (0,08–1,22)
#: körül vagy alatta van, tehát ezek a modellek **pixelpontosak**.
_ERROR_LIMITS: dict[str, float] = {
    "contrast_alap": 0.5,  # (0,300)
    "contrast_max": 0.5,  # (0,295)
    "contrast_min": 0.3,  # (0,151)
    "gamma_alap": 0.8,  # (0,537)
    "gamma_max": 0.8,  # (0,502)
    "gamma_min": 0.7,  # (0,442)
    "colortemp_alap": 0.7,  # (0,479)
    "colortemp_max": 1.2,  # (0,821)
    "colortemp_min": 0.7,  # (0,449)
    "triple2_min": 0.2,  # (0,059)
}


def _model_luts(case: MeasuredCase) -> tuple[np.ndarray, ...]:
    """A modell csatorna-LUT-jai az eset paramétereivel."""
    if case.filter_key == "contrast":
        return pointwise_luts(
            lambda image: apply_native_contrast(image, case.params[0])
        )
    if case.filter_key == "gamma":
        return pointwise_luts(lambda image: apply_gamma(image, case.params[0]))
    if case.filter_key == "colortemp":
        return pointwise_luts(
            lambda image: apply_native_colortemp(
                image, case.params[0], case.params[1]
            )
        )
    if case.filter_key == "triple2":
        # az alsó állásban a Derítőfény 0, a fehérpont a natív védés miatt
        # 0,001 — a szinthúzás mindent a felső végre lök
        return pointwise_luts(
            lambda image: apply_native_levels(image, case.params[1], 0.001)
        )
    raise AssertionError(f"Ismeretlen mérési eset: {case.filter_key}")


class TestMertGorbek:
    @pytest.mark.parametrize(
        "case", measured_cases(), ids=lambda case: case.name
    )
    def test_a_modell_a_mert_hibakorlaton_belul_marad(self, case):
        limit = _ERROR_LIMITS[case.name]
        error = case.weighted_error(_model_luts(case))
        assert error <= limit, (
            f"{case.name}: a modell hibája {error:.3f} > {limit} "
            f"(a mérés saját zaja {case.noise_floor:.3f})"
        )

    @pytest.mark.parametrize(
        "case", measured_cases(), ids=lambda case: case.name
    )
    def test_a_modell_jobb_az_azonossagnal(self, case):
        """A modellnek érdemben jobbnak kell lennie annál, mintha nem
        csinálnánk semmit — különben a hibakorlát csak azt méri, hogy a
        mérőesetben kicsi a hatás."""
        identity = tuple(np.arange(256, dtype=np.float64) for _ in range(3))
        assert case.weighted_error(_model_luts(case)) < case.weighted_error(
            identity
        )


class TestKalibraciosKonstansok:
    """A két, KIZÁRÓLAG mérésből ismert konstans irányának őrzése."""

    def test_a_gamma_kitevoje_forditva_sokkal_rosszabb(self):
        from tests.support.native_filter_reference import case_by_name

        case = case_by_name("gamma_max")
        helyes = case.weighted_error(_model_luts(case))
        forditva = case.weighted_error(
            pointwise_luts(lambda image: apply_gamma(image, -case.params[0]))
        )
        assert forditva > 10 * helyes

    def test_a_fehervaltas_skalaja_nem_a_hidegmelege(self):
        from picasapy.render import native_colortemp
        from tests.support.native_filter_reference import case_by_name

        case = case_by_name("colortemp_max")
        helyes = case.weighted_error(_model_luts(case))
        eredeti = native_colortemp._WHITE_SHIFT_SCALE
        try:
            native_colortemp._WHITE_SHIFT_SCALE = 256.0
            rossz = case.weighted_error(_model_luts(case))
        finally:
            native_colortemp._WHITE_SHIFT_SCALE = eredeti
        assert rossz > 3 * helyes
