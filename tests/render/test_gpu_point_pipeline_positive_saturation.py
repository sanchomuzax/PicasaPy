"""GPU pozitív telítettség — a shader-matematika numpy-referenciája (#696).

A #696 jegy megállapítása (a #693 következménye): a `sat` szűrő CPU-oldali
igazságforrása (`picasapy.render.saturation_positive.
apply_positive_saturation`) a POZITÍV oldalon natív, csatornánkénti gamma-
modellt futtat, amire semmilyen skalár erősítés nem illeszthető. A régi
GPU-előnézet (`saturation_gain()` + `mix(vec3(luma), toned, satGain)`)
mégis egy skalárt kapott — emiatt élő csúszka-húzás közben az előnézet a
végleges képtől eltért (a jegy táblázata szerint 3–13 szint, a golden-kit
mérésen).

**A valódi GL-út ebben a futtatókörnyezetben NEM mérhető** — a
`tests/app/test_gpu_point_filter_shader.py` is SKIP-el itt: nincs
elérhető RHI-grafikai kontextus ebben az ágens-sandboxban (`/dev/dri` van,
de a Qt Quick a `software` jelenetgráf-adapterre esik vissza — ld. annak
a fájlnak a skip-üzenete). Ez a teszt ezért a tervezett GLSL-képlet
(`PointFilter.frag` `applyPositiveSaturation()`) SZÁMÍTÁSÁT futtatja
numpy-ban (`gpu_point_pipeline.simulate_positive_saturation_shader()`) —
ez NEM helyettesíti a valódi GPU-mérést, csak a matematikai modellt
igazolja. RPi5-ön/valódi GPU-n a `test_gpu_point_filter_shader.py`
parity-tesztje adja a tényleges GL-bizonyítékot; ott (ha fut) ennek is
teljesülnie kell.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import apply_saturation
from picasapy.render.gpu_point_pipeline import (
    _POSITIVE_SATURATION_RATIO_CLAMP,
    build_point_pipeline_uniforms,
    saturation_gain,
    simulate_positive_saturation_shader,
)
from picasapy.render.saturation_positive import _LUT_RANGE


def _old_scalar_gain_shader_reference(image: np.ndarray, amount: float) -> np.ndarray:
    """A #696 ELŐTTI GPU-shader matematikájának numpy-mása: luma-tartó
    skalár erősítés (`mix(vec3(luma), toned, satGain)`, Rec.601 luma) — ez
    volt a `PointFilter.frag` POZITÍV ágon (is) futó, téves modellje.

    Szándékosan NEM a mai (javított) `gpu_point_pipeline`-t hívja: a régi
    matek szó szerinti másolata, hogy a lenti bukó teszt a #696 ELŐTTI
    hibát reprodukálja — függetlenül attól, hogy a mai kód már javítva
    van. Ha valaki visszaállna erre a modellre a pozitív ágon, ez a teszt
    újra elkapná."""
    gain = saturation_gain(amount)
    luma = (
        0.299 * image[..., 0].astype(np.float64)
        + 0.587 * image[..., 1].astype(np.float64)
        + 0.114 * image[..., 2].astype(np.float64)
    )[..., np.newaxis]
    blended = luma + gain * (image.astype(np.float64) - luma)
    return np.clip(np.round(blended), 0, 255).astype(np.uint8)


def _sample_image() -> np.ndarray:
    """Vegyes minta: véletlen (teljes tartományú) sáv + közel-fekete sáv —
    a natív gamma-modell legszélsőségesebb (legjobban görbülő) esetei a
    majdnem-fekete, erősen színezett pixeleken jelentkeznek (ld.
    `simulate_positive_saturation_shader` docsztringje a `luma == 0`
    ágválasztásról és a `_POSITIVE_SATURATION_RATIO_CLAMP`-ról)."""
    rng = np.random.default_rng(696)
    bright = rng.integers(0, 256, size=(48, 48, 3), dtype=np.uint8)
    dark = rng.integers(0, 24, size=(16, 48, 3), dtype=np.uint8)
    return np.concatenate([bright, dark], axis=0)


#: A jegy táblázatának négy csúszka-állása (0,10 / 0,37 / 0,62 / 0,87).
_POSITIVE_AMOUNTS = (0.10, 0.37, 0.62, 0.87)

#: A régi (skalár-erősítéses) modell tűrés-küszöbe: a #696 jegy táblázata
#: 3,07–13,34 szintet mér a golden-kit mintán; a lenti `_sample_image()`-en
#: mérve a régi modell átlagos hibája 3,5–19,3 szint. A küszöb ennek a
#: sávnak a JÓVAL ALATTA áll (nem a közepén sem), hogy a bukó teszt
#: biztosan bukjon, ne legyen esetleges egy másik random maggal sem.
_OLD_MODEL_ERROR_FLOOR = 2.5

#: Az új (per-csatorna gamma) modell tűrése: a mért átlagos abszolút hiba
#: 0,78–1,35 szint között mozog a fenti mintán, minden mintázott
#: erősségnél — ez a küszöb közel kétszeres (>1,8×) tartalékot hagy, és
#: messze a régi modell hibája (fent) alatt marad.
_NEW_MODEL_MEAN_ERROR_TOLERANCE = 2.5


class TestOldScalarGainModelFailsPositiveBranch:
    """RED — a #696 ELŐTTI GPU-matek messze eltér a CPU-igazságforrástól a
    pozitív ágon. Ez a teszt a RÉGI matematikát futtatja (nem a mai
    `gpu_point_pipeline`-t) — bizonyítékként marad a suite-ban, hogy a
    javítás nélkül (vagy egy jövőbeli visszaállással) a hiba visszatérne.

    Ez a teszt osztály fut le elsőként `pytest -k Old` módon reprodukálva
    a #696 jegy megállapítását — a javítás ELŐTT ez lett volna az egyetlen
    (bukó) teszt ebben a fájlban."""

    @pytest.mark.parametrize("amount", _POSITIVE_AMOUNTS)
    def test_old_model_mean_error_exceeds_floor(self, amount: float) -> None:
        image = _sample_image()
        truth = apply_saturation(image, amount).astype(np.int32)
        old_preview = _old_scalar_gain_shader_reference(image, amount).astype(np.int32)
        mean_abs_error = float(np.abs(old_preview - truth).mean())
        assert mean_abs_error > _OLD_MODEL_ERROR_FLOOR, (
            "A régi skalár-erősítéses modellnek jóval a CPU-igazságforrás "
            f"fölött kellene hibáznia (amount={amount}); mért érték: "
            f"{mean_abs_error:.3f} (küszöb: {_OLD_MODEL_ERROR_FLOOR})."
        )


class TestPositiveSaturationShaderSimulationMatchesCpuTruth:
    """GREEN — a #696 javítás: a shader tervezett gamma-modellje
    (`simulate_positive_saturation_shader`, a `PointFilter.frag`
    `applyPositiveSaturation()`-jének numpy-mása) nagyságrendekkel
    közelebb áll a CPU-igazságforráshoz, mint a régi skalár modell."""

    @pytest.mark.parametrize("amount", _POSITIVE_AMOUNTS)
    def test_new_model_mean_error_within_tolerance(self, amount: float) -> None:
        image = _sample_image()
        truth = apply_saturation(image, amount).astype(np.int32)
        new_preview = simulate_positive_saturation_shader(image, amount).astype(np.int32)
        mean_abs_error = float(np.abs(new_preview - truth).mean())
        assert mean_abs_error < _NEW_MODEL_MEAN_ERROR_TOLERANCE, (
            f"Az új gamma-modell hibája túllépte a tűrést (amount={amount}); "
            f"mért érték: {mean_abs_error:.3f} "
            f"(tűrés: {_NEW_MODEL_MEAN_ERROR_TOLERANCE})."
        )

    @pytest.mark.parametrize("amount", _POSITIVE_AMOUNTS)
    def test_new_model_is_far_better_than_old_model(self, amount: float) -> None:
        """Nem elég, hogy az új modell tűrésen belül van — bizonyítani
        kell, hogy VALÓBAN sokkal jobb, mint a régi (a #696 jegy fő
        állítása). Legalább feleannyi hibát követelünk meg, a mért
        arány (kb. 4–17×) bőséges tartalékkal."""
        image = _sample_image()
        truth = apply_saturation(image, amount).astype(np.int32)
        old_preview = _old_scalar_gain_shader_reference(image, amount).astype(np.int32)
        new_preview = simulate_positive_saturation_shader(image, amount).astype(np.int32)
        old_error = float(np.abs(old_preview - truth).mean())
        new_error = float(np.abs(new_preview - truth).mean())
        assert new_error < old_error / 2.0, (
            f"amount={amount}: régi hiba={old_error:.3f}, új hiba={new_error:.3f} "
            "— az új modellnek legalább feleannyi hibát kellene adnia."
        )

    def test_identity_at_zero_amount(self) -> None:
        image = _sample_image()
        result = simulate_positive_saturation_shader(image, 0.0)
        np.testing.assert_array_equal(result, image)

    def test_identity_at_negative_amount(self) -> None:
        """A negatív ágra a hívónak `saturation_gain()`-t kell választania
        (`build_point_pipeline_uniforms`) — ez a függvény önmagában
        identitást ad negatív `amount`-ra, nem hívja hibásan a gamma-utat."""
        image = _sample_image()
        result = simulate_positive_saturation_shader(image, -0.5)
        np.testing.assert_array_equal(result, image)


class TestPositiveSaturationRatioClampMatchesNativeLutRange:
    """A folytonos modell `_POSITIVE_SATURATION_RATIO_CLAMP` vágása a natív
    LUT `x`-tartományának (`saturation_positive._LUT_RANGE`) szándékosan
    duplikált másolata (ld. a `gpu_point_pipeline` modul docsztringje,
    hogy miért nem import) — ez a teszt őrzi az egyezést, ha bármelyik
    érték változna."""

    def test_clamp_matches_native_lut_range(self) -> None:
        assert _POSITIVE_SATURATION_RATIO_CLAMP == pytest.approx(_LUT_RANGE)


class TestBuildPointPipelineUniformsPositiveBranch:
    """`build_point_pipeline_uniforms` a natív `sat` két ágának megfelelően
    KÉT külön uniformot tölt — sosem mindkettőt egyszerre (#696)."""

    def test_positive_saturation_sets_strength_not_gain(self) -> None:
        uniforms = build_point_pipeline_uniforms(saturation=0.5)
        assert uniforms.sat_positive_strength == pytest.approx(1.5)
        assert uniforms.sat_gain == pytest.approx(1.0)

    def test_negative_saturation_sets_gain_not_strength(self) -> None:
        uniforms = build_point_pipeline_uniforms(saturation=-0.5)
        assert uniforms.sat_positive_strength == pytest.approx(0.0)
        assert uniforms.sat_gain == pytest.approx(saturation_gain(-0.5))

    def test_zero_saturation_is_identity_on_both(self) -> None:
        uniforms = build_point_pipeline_uniforms(saturation=0.0)
        assert uniforms.sat_positive_strength == pytest.approx(0.0)
        assert uniforms.sat_gain == pytest.approx(1.0)
