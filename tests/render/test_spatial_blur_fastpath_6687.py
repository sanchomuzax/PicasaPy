"""#6687: a képpontazonos gyors úthoz kisebb, közvetlen OpenCV-puffer kell."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.lazy_cv2 import cv2
from picasapy.render import (
    belso_ragyogas,
    glimmer_artistic,
    glimmer_color_ops,
    glimmer_creative,
    glimmer_frame_ops,
    glimmer_tone,
    iir_blur,
    nativ_blur,
    native_grain,
)
from picasapy.render.native_grain import _bajtok_rgb


def _legacy_iir(image: np.ndarray, radius_x: float, radius_y: float) -> np.ndarray:
    """A régi int64-es referenciaút, a gyors út képpontos kontrolljához."""
    work = image.astype(np.int64)
    if radius_x > 0.0:
        work = iir_blur._sweep_axis_zero(
            work.transpose(1, 0, 2), iir_blur.blur_coefficient(radius_x)
        ).transpose(1, 0, 2)
    if radius_y > 0.0:
        work = iir_blur._sweep_axis_zero(
            work, iir_blur.blur_coefficient(radius_y)
        )
    return work.astype(np.uint8)


def test_iir_elmosas_32_bites_puffere_azonos_kimenetet_ad(monkeypatch):
    """A 8 bites bemenetből levezetett fixpontos állapot int32-ben is elfér."""
    image = np.random.default_rng(6687).integers(0, 256, (31, 47, 3), dtype=np.uint8)
    vart = _legacy_iir(image, 4.75, 3.25)
    eredeti = iir_blur._sweep_axis_zero
    latott_tipusok = []

    def _figyelt(values, coefficient):
        latott_tipusok.append(values.dtype)
        return eredeti(values, coefficient)

    monkeypatch.setattr(iir_blur, "_sweep_axis_zero", _figyelt)
    kapott = iir_blur.apply_picasa_blur(image, 4.75, 3.25)

    assert latott_tipusok == [np.dtype(np.int32), np.dtype(np.int32)]
    np.testing.assert_array_equal(kapott, vart)


def test_nativ_blur_kozvetlenul_uint8_bemenetet_ad_az_opencvnek(monkeypatch):
    """Az int64 munkapufferből float32 másolat készítése nem szükséges."""
    image = np.random.default_rng(6688).integers(0, 256, (31, 47), dtype=np.uint8)
    eredeti = cv2.sepFilter2D
    latott_tipusok = []

    def _figyelt(src, ddepth, kernel_x, kernel_y, **kwargs):
        latott_tipusok.append(src.dtype)
        return eredeti(src, ddepth, kernel_x, kernel_y, **kwargs)

    monkeypatch.setattr(cv2, "sepFilter2D", _figyelt)
    kapott = nativ_blur.nativ_blur_csatorna(image, 4.5, 4.5, quality=3)

    assert latott_tipusok == [np.dtype(np.uint8)] * 6
    assert kapott.dtype == np.uint8


def test_ragyogas_dobozmenet_uint8_puffert_ad_az_opencvnek(monkeypatch):
    maszk = np.random.default_rng(6689).integers(0, 256, (29, 43), dtype=np.uint8)
    eredeti = cv2.sepFilter2D
    latott_tipusok = []

    def _figyelt(src, ddepth, kernel_x, kernel_y, **kwargs):
        latott_tipusok.append(src.dtype)
        return eredeti(src, ddepth, kernel_x, kernel_y, **kwargs)

    monkeypatch.setattr(cv2, "sepFilter2D", _figyelt)
    kapott = belso_ragyogas._dobozmenetek(maszk, 1, 7.25, 3)

    assert latott_tipusok == [np.dtype(np.uint8)] * 3
    assert kapott.shape == maszk.shape


def test_szemcsebajtok_rgb_sikjai_nem_tartanak_felesleges_negyedik_csatornat():
    szavak = np.random.default_rng(6690).integers(0, 2**32, (23, 37), dtype=np.uint32)

    r, g, b = _bajtok_rgb(szavak)

    assert not np.may_share_memory(r, g)
    assert not np.may_share_memory(g, b)
    assert (r.dtype, g.dtype, b.dtype) == (np.dtype(np.int16),) * 3
    bajtok = szavak.astype("<u4").view(np.uint8).reshape(*szavak.shape, 4)
    np.testing.assert_array_equal(r, bajtok[..., 2])
    np.testing.assert_array_equal(g, bajtok[..., 1])
    np.testing.assert_array_equal(b, bajtok[..., 0])


def test_drop_shadow_keveres_nem_hasznal_uint32_puffert(monkeypatch):
    eredeti_array = glimmer_frame_ops.np.array
    latott_uint32 = []

    def _figyelt_array(*args, **kwargs):
        if kwargs.get("dtype") == np.uint32:
            latott_uint32.append(True)
        return eredeti_array(*args, **kwargs)

    monkeypatch.setattr(glimmer_frame_ops.np, "array", _figyelt_array)
    image = np.full((17, 23, 3), 91, dtype=np.uint8)

    kapott = glimmer_frame_ops.draw_drop_shadow(
        image, (20, 40, 60), (200, 210, 220), distance=2, angle=45, blur=2, fade=0
    )

    assert not latott_uint32
    assert kapott.dtype == np.uint8


def test_pixelate_normal_es_fade_nelkuli_utja_nem_alakit_floatra(monkeypatch):
    image = np.random.default_rng(6691).integers(0, 256, (37, 53, 3), dtype=np.uint8)
    impact = 9.0
    small = glimmer_artistic.resize_image(image, int(53 / impact + 0.5), int(37 / impact + 0.5), smoothing=True)
    vart = glimmer_artistic.resize_image(small, 53, 37, smoothing=False)

    def _tiltott(*args, **kwargs):
        raise AssertionError("a normál, teljesen fedő Pixelate nem igényel float-konverziót")

    monkeypatch.setattr(glimmer_artistic, "to_float", _tiltott)
    kapott = glimmer_artistic.apply_pixelate(image, impact=impact, fade=0.0, blend_mode=9)

    np.testing.assert_array_equal(kapott, vart)


def test_pencil_sketch_egesz_keverese_megtartja_a_regi_kepet(monkeypatch):
    image = np.random.default_rng(6692).integers(0, 256, (29, 41, 3), dtype=np.uint8)
    vart = glimmer_creative.apply_pencil_sketch(image, radius=2.0, contrast=100.0, fade=0.0)

    def _tiltott(*args, **kwargs):
        raise AssertionError("a két byte-pontos blend nem igényel float32 köztes képeket")

    monkeypatch.setattr(glimmer_creative, "apply_blend_mode", _tiltott)
    kapott = glimmer_creative.apply_pencil_sketch(image, radius=2.0, contrast=100.0, fade=0.0)

    np.testing.assert_array_equal(kapott, vart)


def test_iir_menetei_folytonos_puffert_hasznalnak_es_megtartjak_a_bajtokat(monkeypatch):
    image = np.random.default_rng(6693).integers(0, 256, (67, 83, 3), dtype=np.uint8)
    vart = _legacy_iir(image, 4.75, 3.25)
    eredeti = iir_blur._sweep_axis_zero
    folytonos = []

    def _figyelt(values, coefficient):
        folytonos.append(values.flags.c_contiguous)
        return eredeti(values, coefficient)

    monkeypatch.setattr(iir_blur, "_sweep_axis_zero", _figyelt)
    kapott = iir_blur.apply_picasa_blur(image, 4.75, 3.25)

    assert folytonos == [True, True]
    np.testing.assert_array_equal(kapott, vart)


def test_local_contrast_egesz_kulonbsegekkel_azonos_kimenetu(monkeypatch):
    image = np.random.default_rng(6694).integers(0, 256, (37, 53, 3), dtype=np.uint8)
    vart = glimmer_tone.apply_local_contrast(image, radius=7.0, strength=1.5)
    eredeti = glimmer_color_ops._szorzott_resz
    tipushalmaz = []

    def _figyelt(difference, strength):
        tipushalmaz.append(difference.dtype)
        return eredeti(difference, strength)

    monkeypatch.setattr(glimmer_color_ops, "_szorzott_resz", _figyelt)
    kapott = glimmer_tone.apply_local_contrast(image, radius=7.0, strength=1.5)

    assert tipushalmaz == [np.dtype(np.int16), np.dtype(np.int16)]
    np.testing.assert_array_equal(kapott, vart)


def test_holga_szurke_kontraszt_lutja_bajtra_azonos_es_kis_puffert_hasznal(monkeypatch):
    szurke = np.random.default_rng(6695).integers(0, 256, (29, 41), dtype=np.uint8)
    image = np.repeat(szurke[..., np.newaxis], 3, axis=2)
    eredeti = glimmer_color_ops.simple_color_matrix
    vart = eredeti(image, contrast=25.0)
    alakok = []

    def _figyelt(values, **kwargs):
        alakok.append(values.shape)
        return eredeti(values, **kwargs)

    glimmer_creative._holga_contrast_lut.cache_clear()
    monkeypatch.setattr(glimmer_creative, "simple_color_matrix", _figyelt)
    kapott = glimmer_creative._holga_contrast_exact(image)

    assert alakok == [(1, 256, 3)]
    np.testing.assert_array_equal(kapott, vart)


@pytest.mark.parametrize("width", [46, 47])
def test_holga_zajkeverese_bajtra_azonos_es_a_zajplane_gyorsitotarazott(monkeypatch, width):
    szurke = np.random.default_rng(6696).integers(0, 256, (31, width), dtype=np.uint8)
    image = np.repeat(szurke[..., np.newaxis], 3, axis=2)
    vart = glimmer_creative.apply_noise(
        image,
        seed=5,
        low=217,
        high=255.0,
        grayscale=True,
        blend_alpha=0.6,
        blend_mode="multiply",
    )
    glimmer_creative._holga_noise_plane.cache_clear()
    zaj1 = glimmer_creative._holga_noise_plane(31, width, 5, 217)
    zaj2 = glimmer_creative._holga_noise_plane(31, width, 5, 217)

    def _tiltott(*args, **kwargs):
        raise AssertionError("a Holga szürke zajkeverése nem kérhet teljes RGB zajréteget")

    monkeypatch.setattr(glimmer_creative, "apply_noise", _tiltott)
    monkeypatch.setattr(glimmer_creative, "apply_blend_mode", _tiltott)
    kapott = glimmer_creative._holga_noise_blend(image, 217)

    assert zaj1 is zaj2
    assert not zaj1.flags.writeable
    np.testing.assert_array_equal(kapott, vart)


def test_holga_belso_ragyogasanak_meretfuggo_sulya_gyorsitotarazott(monkeypatch):
    image = np.random.default_rng(6699).integers(0, 256, (97, 131, 3), dtype=np.uint8)
    clear_cache = getattr(belso_ragyogas._lekicsinyitett_suly, "cache_clear", None)
    if clear_cache is not None:
        clear_cache()
    eredeti = belso_ragyogas.ragyogas_maszk_oszlopai
    hivasok = []

    def _figyelt(*args, **kwargs):
        hivasok.append(args)
        return eredeti(*args, **kwargs)

    monkeypatch.setattr(belso_ragyogas, "ragyogas_maszk_oszlopai", _figyelt)
    elso = belso_ragyogas.inner_glow(image, (0, 0, 0), 70.0, 60.0, 1.4)
    masodik = belso_ragyogas.inner_glow(image, (0, 0, 0), 70.0, 60.0, 1.4)

    assert len(hivasok) == 1
    np.testing.assert_array_equal(masodik, elso)


def _legacy_native_grain(image: np.ndarray, seed: int) -> np.ndarray:
    """A régi, gyorsítótár nélküli zajtér- és képpontkeverő referenciája."""
    height, width = image.shape[:2]
    words = native_grain.picasa_mt19937(seed, 2 * height * width).reshape(2, height, width)
    first, fresh = words[0], words[1]
    r, g, b = _bajtok_rgb(first)
    r = native_grain._simit_haromszor(native_grain._pull_127_fele(r, native_grain._K_BEEGETETT))
    g = native_grain._simit_haromszor(native_grain._pull_127_fele(g, native_grain._K_BEEGETETT))
    b = native_grain._simit_haromszor(native_grain._pull_127_fele(b, native_grain._K_BEEGETETT))
    fresh_r, fresh_g, fresh_b = _bajtok_rgb(fresh)
    r = fresh_r.astype(np.int32) + (((r.astype(np.int32) - fresh_r) * native_grain._VISSZAKEVERES_SULY) >> 8)
    g = fresh_g.astype(np.int32) + (((g.astype(np.int32) - fresh_g) * native_grain._VISSZAKEVERES_SULY) >> 8)
    b = fresh_b.astype(np.int32) + (((b.astype(np.int32) - fresh_b) * native_grain._VISSZAKEVERES_SULY) >> 8)
    y = (native_grain._Y_B * b + native_grain._Y_G * g + native_grain._Y_R * r) >> 8
    r = np.clip(r + (((y - r) * native_grain._SZURKITES_SULY) >> 8), 0, 255)
    g = np.clip(g + (((y - g) * native_grain._SZURKITES_SULY) >> 8), 0, 255)
    b = np.clip(b + (((y - b) * native_grain._SZURKITES_SULY) >> 8), 0, 255)
    source = image.astype(np.int32)
    output = np.empty_like(source)
    for channel, noise in enumerate((r, g, b)):
        center_weight = native_grain._KOZEPTONUS_CSUCS - np.abs(
            native_grain._KOZEPTONUS_KOZEP - source[..., channel]
        )
        output[..., channel] = np.clip(
            source[..., channel]
            + ((center_weight * (noise - native_grain._KOZEPTONUS_KOZEP)) >> 8),
            0,
            255,
        )
    return output.astype(np.uint8)


def test_grain2_meret_es_mag_szerint_gyorsitotarazott_teret_kever_bajtra_azonosan(monkeypatch):
    first = np.random.default_rng(6697).integers(0, 256, (13, 19, 3), dtype=np.uint8)
    second = np.random.default_rng(6698).integers(0, 256, (13, 19, 3), dtype=np.uint8)
    seed = 1234
    vart1 = _legacy_native_grain(first, seed)
    vart2 = _legacy_native_grain(second, seed)
    eredeti = native_grain.picasa_mt19937
    generator_calls = []

    def _figyelt(seed_value, count):
        generator_calls.append((seed_value, count))
        return eredeti(seed_value, count)

    native_grain._grain_noise_rgb.cache_clear()
    monkeypatch.setattr(native_grain, "picasa_mt19937", _figyelt)
    kapott1 = native_grain.apply_native_grain(first, seed)
    kapott2 = native_grain.apply_native_grain(second, seed)

    assert generator_calls == [(seed, 2 * 13 * 19)]
    np.testing.assert_array_equal(kapott1, vart1)
    np.testing.assert_array_equal(kapott2, vart2)


def test_grain2_kotegfolyam_gyorsitotarazott_zaja_egyezik_a_friss_folyammal(monkeypatch):
    image = np.full((17, 23, 3), 127, dtype=np.uint8)
    cached_noise = native_grain._grain_noise_rgb
    uncached_noise = cached_noise.__wrapped__

    def render_batch(images):
        with native_grain._grain_rand_stream():
            return [
                native_grain.apply_native_grain(image, native_grain.grain_seed(0))
                for image in images
            ]

    cached_noise.cache_clear()
    with monkeypatch.context() as patch:
        patch.setattr(native_grain, "_grain_noise_rgb", uncached_noise)
        standalone_uncached = render_batch([image])[0]
        batch_uncached = render_batch([image, image])

    cached_noise.cache_clear()
    standalone_cached = render_batch([image])[0]
    batch_cached = render_batch([image, image])

    np.testing.assert_array_equal(standalone_cached, standalone_uncached)
    np.testing.assert_array_equal(batch_cached[0], batch_uncached[0])
    np.testing.assert_array_equal(batch_cached[1], batch_uncached[1])
    np.testing.assert_array_equal(batch_cached[0], standalone_cached)
    assert not np.array_equal(batch_cached[1], standalone_cached)
