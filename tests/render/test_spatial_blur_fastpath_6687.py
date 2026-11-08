"""#6687: a képpontazonos gyors úthoz kisebb, közvetlen OpenCV-puffer kell."""

from __future__ import annotations

import numpy as np

from picasapy.lazy_cv2 import cv2
from picasapy.render import (
    belso_ragyogas,
    glimmer_artistic,
    glimmer_creative,
    glimmer_frame_ops,
    iir_blur,
    nativ_blur,
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
