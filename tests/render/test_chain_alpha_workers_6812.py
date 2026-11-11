"""#6812: a PicnikGrain maszkja olvassa, a Soften blendje visszaírja az alfát."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters


def _kep() -> np.ndarray:
    y, x = np.indices((32, 32))
    return np.stack(
        (35 + x * 4, 25 + y * 5, 60 + (x + y) * 3), axis=-1
    ).astype(np.uint8)


def test_picnikgrain_a_nullazott_forrasalfat_feher_maszkkent_olvassa() -> None:
    source = _kep()
    operations = parse_filters(
        "dir_brite=1,-0.884987,-0.873954;PicnikGrain=1,50,1;grain2=1;"
    )

    report = apply_filters(source, operations[:2])

    assert report.skipped == ()
    assert report.alpha == 255
    np.testing.assert_array_equal(report.image, np.full_like(source, 255))


def test_soften_utan_a_dropshadow_a_kept_rajzolja_nem_a_hattert() -> None:
    source = _kep()
    operations = parse_filters(
        "blur=1,0.2;Soften=1,0,50;"
        "DropShadow=1,0,90,0,000000,00e2e2e2,0;"
    )

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 255
    assert np.any(report.image != np.array((0xE2, 0xE2, 0xE2), dtype=np.uint8))


def test_autolight_ansel_es_autobacklight_visszaallitja_a_picnikgrain_alfajat() -> None:
    source = _kep()
    operations = parse_filters(
        "autolight=1;dir_sat=1,-0.442611,0.858774;"
        "ansel=1,ff892ecc;autobacklight=1;PicnikGrain=1,3.811999,1;"
    )

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 255
    assert not np.all(report.image == 255)


def test_ansel_a_pixelworkerben_teljesen_fedove_allitja_az_alfa_bajtot() -> None:
    source = _kep()
    operations = parse_filters("dir_sat=1,-0.442611,0.858774;ansel=1,ff892ecc;")

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 255


def test_ansel_utan_a_picnikgrain_nem_feher_maszkot_kap() -> None:
    source = _kep()
    operations = parse_filters(
        "dir_sat=1,-0.442611,0.858774;ansel=1,ff892ecc;"
        "PicnikGrain=1,3.811999,1;"
    )

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 255
    assert not np.all(report.image == 255)


@pytest.mark.parametrize("input_alpha", (0, 255))
def test_invert_megorzi_a_negyedik_alfa_csatornat(input_alpha: int) -> None:
    report = apply_filters(_kep(), parse_filters("Invert=1;"), input_alpha=input_alpha)

    assert report.skipped == ()
    # Az eredeti Picasa mérése szerint az Invert a forrásalfát őrzi (#6836).
    assert report.alpha == input_alpha


def test_invert_utan_a_dropshadow_a_kepet_rajzolja_6836() -> None:
    operations = parse_filters(
        "radtint=1,0.5,0.5,0.25;unsharp2=1,0.6;Invert=1;"
        "DropShadow=1,0,90,0,000000,00e2e2e2,0;"
    )
    report = apply_filters(_kep(), operations)

    assert report.skipped == ()
    center = report.image[report.image.shape[0] // 2, report.image.shape[1] // 2]
    assert np.any(center != np.array((0xE2, 0xE2, 0xE2), dtype=np.uint8))


@pytest.mark.parametrize(
    "glimmer",
    (
        "Lomo=1,50,0;",
        "Vignette=1,35,1.4,0,00000000;",
        "Pixelate=1,20,9,0;",
    ),
)
def test_opaque_glimmer_retegek_visszaallitjak_a_nullazott_alfat(glimmer: str) -> None:
    source = _kep()
    operations = parse_filters(f"shadow=1,0.5,0.5,0.5;{glimmer}")

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 255


@pytest.mark.parametrize(
    "glimmer",
    (
        "Lomo=1,50,100;",
        "Vignette=1,35,1.4,100,00000000;",
        "Pixelate=1,20,9,100;",
        "Soften=1,20,100;",
    ),
)
def test_fade_100_megorzi_a_bemeneti_alfaallapotot(glimmer: str) -> None:
    source = _kep()
    operations = parse_filters(f"shadow=1,0.5,0.5,0.5;{glimmer}")

    report = apply_filters(source, operations, input_alpha=255)

    assert report.skipped == ()
    assert report.alpha == 0


def test_minden_kezelohoz_van_alfa_besorolas() -> None:
    from picasapy.render.chain import (
        _ALPHA_FADE_BLENDERS,
        _ALPHA_NO_WORKER_OPS,
        _ALPHA_SOURCE_PRESERVING_WORKERS,
        _ALPHA_WORKER_OUTPUTS,
        _HANDLERS,
    )
    from picasapy.render.registry import FILTER_REGISTRY

    classified = (
        set(_ALPHA_WORKER_OUTPUTS)
        | set(_ALPHA_SOURCE_PRESERVING_WORKERS)
        | set(_ALPHA_FADE_BLENDERS)
    )

    assert classified == set(_HANDLERS)
    assert set(FILTER_REGISTRY) <= classified | set(_ALPHA_NO_WORKER_OPS)


def test_dir_sharp_pixelworker_a_zero_felsobajtot_irja() -> None:
    source = _kep()
    operations = parse_filters("dir_sharp=1,0.4,0.6;")

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 0


def test_shadow_pixelworker_a_zero_felsobajtot_irja() -> None:
    source = _kep()
    operations = parse_filters("shadow=1,0.5,0.5,0.5;")

    report = apply_filters(source, operations, input_alpha=255)

    assert report.skipped == ()
    assert report.alpha == 0


@pytest.mark.parametrize(
    "writer",
    (
        "dir_tint=1,0.5,0.5,0.5,0.5,ff336699;",
        "linblur=1,0.5,0.5,2.0;",
        "radblur=1,0.5,0.5,0.3,0.3;",
        "radsat=1,0.5,0.5,0.3,0.5;",
    ),
)
def test_egyeb_natív_alfa_255_irok_felulirjak_a_nulla_allapotot(writer: str) -> None:
    source = _kep()
    operations = parse_filters(f"dir_sat=1,-0.442611,0.858774;{writer}")

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 255


@pytest.mark.parametrize(
    "writer",
    (
        "autocolor=1;",
        "warm=1;",
        "grain=1;",
        "sat=1,0.5;",
        "backlight=1,0.5;",
        "fill=1,0.5;",
        "glow=1,0.2,10;",
        "contrast=1,0.5;",
        "colorfix=1,0.1,ff000000;",
    ),
)
def test_natív_alfa_255_irok_visszaallitjak_a_lanc_allapotat(writer: str) -> None:
    source = _kep()
    operations = parse_filters(f"dir_sat=1,-0.442611,0.858774;{writer}")

    report = apply_filters(source, operations)

    assert report.skipped == ()
    assert report.alpha == 255
