"""#3884 — a `FocalZoom` zoom-elmosása az eredeti kernel szerint.

A spec: `docs/specs/filters-decoded.md`, „⛳ A FocalZoom zoom-kernele
teljesen” (#3883). A mag (`0x00bcf4b0`) nem nagyított képeket átlagol, hanem:

- `k = N … 1` sorrendben `off = ⌊k·D / N⌋` eltolással (a legnagyobb először),
- legközelebbi szomszéddal, 16.16 fixpontban mintáz (`M` cél → forrás,
  a cél képpont közepéből),
- és minden mintát `acc = (38·minta + 217·acc) >> 8` súllyal keveri rá az
  akkumulátorra — az SSE2-ágban SÁVHIBÁVAL: a négyes csoportok 2–3.
  képpontja a 0–1. képpont (előző) akkumulátorát használja.

A referencia-megvalósítás itt szándékosan skalár, képpontonkénti ciklus: a
spec szövegét követi, nem a vektoros kódot.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from picasapy.render import focal
from picasapy.render.focal import (
    apply_focal_zoom,
    zoom_blend_step,
    zoom_blur,
    zoom_max_offset,
    zoom_offsets,
    zoom_sample_count,
    zoom_sample_indices,
)


def _ref_blend(acc_prev: int, sample: int) -> int:
    return (38 * sample + 217 * acc_prev) >> 8


def _ref_step_row(acc: list[int], samples: list[int]) -> list[int]:
    """Egy sor, egy csatorna, egy lépés — a spec 4. pontja szó szerint."""
    width = len(acc)
    full = (width // 4) * 4
    out = []
    for col in range(width):
        if col < full and col % 4 in (2, 3):
            out.append(_ref_blend(acc[col - 2], samples[col]))
        else:
            out.append(_ref_blend(acc[col], samples[col]))
    return out


def _ref_index(pos: int, length: int, off: int, focus_px: float) -> int:
    scale = np.float32(length / (length + off))
    shift = np.float32(off * focus_px / length)
    u = np.float32(np.float32(pos + 0.5) * scale + shift)
    index = int(np.floor(np.float32(65536.0) * u)) >> 16
    # a képleten kívül eső mintát (fókusz a szélhez közel: x > W²/(W+off))
    # a szélső képpont adja — ezt a golden-készlet nem méri (középfókusz)
    return min(max(index, 0), length - 1)


def _ref_zoom_blur(image: np.ndarray, x: float, y: float, impact: float) -> np.ndarray:
    height, width = image.shape[:2]
    samples = zoom_sample_count(impact)
    max_offset = zoom_max_offset(width, impact)
    acc = image.astype(np.int64)
    for k in range(samples, 0, -1):
        off = (k * max_offset) // samples
        new = np.empty_like(acc)
        for row in range(height):
            src_row = _ref_index(row, height, off, y * height)
            for ch in range(image.shape[2]):
                sample_row = [
                    int(image[src_row, _ref_index(col, width, off, x * width), ch])
                    for col in range(width)
                ]
                new[row, :, ch] = _ref_step_row(list(acc[row, :, ch]), sample_row)
        acc = new
    return acc.astype(np.uint8)


class TestBandBug:
    """A Picasa SSE2-ágának sávhibája (`0x00bcf345`, `0x00bcf349`)."""

    def test_8x1_row_lanes_2_3_use_the_accumulator_of_lanes_0_1(self):
        acc = np.array([[[10], [200], [30], [40], [250], [60], [70], [80]]], dtype=np.uint8)
        sample = np.array([[[100], [0], [255], [5], [9], [128], [77], [3]]], dtype=np.uint8)
        out = zoom_blend_step(acc, sample)
        a = acc[0, :, 0].astype(int)
        s = sample[0, :, 0].astype(int)
        expected = [
            (38 * s[0] + 217 * a[0]) >> 8,
            (38 * s[1] + 217 * a[1]) >> 8,
            (38 * s[2] + 217 * a[0]) >> 8,  # a 0. képpont akkumulátora
            (38 * s[3] + 217 * a[1]) >> 8,  # az 1. képpont akkumulátora
            (38 * s[4] + 217 * a[4]) >> 8,
            (38 * s[5] + 217 * a[5]) >> 8,
            (38 * s[6] + 217 * a[4]) >> 8,
            (38 * s[7] + 217 * a[5]) >> 8,
        ]
        assert out[0, :, 0].tolist() == expected

    def test_8x1_row_differs_from_the_bug_free_blend(self):
        """Rontás-kontroll: a hibátlan keverés a 2–3. és 6–7. képponton más."""
        acc = np.array([[[10], [200], [30], [40], [250], [60], [70], [80]]], dtype=np.uint8)
        sample = np.array([[[100], [0], [255], [5], [9], [128], [77], [3]]], dtype=np.uint8)
        hibatlan = (38 * sample.astype(int) + 217 * acc.astype(int)) >> 8
        out = zoom_blend_step(acc, sample).astype(int)
        elter = np.nonzero(out[0, :, 0] != hibatlan[0, :, 0])[0].tolist()
        assert elter == [2, 3, 6, 7]

    @pytest.mark.parametrize("width", [1, 2, 3, 5, 6, 7, 9, 11])
    def test_the_row_end_remainder_blends_with_its_own_accumulator(self, width):
        rng = np.random.default_rng(width)
        acc = rng.integers(0, 256, size=(3, width, 3), dtype=np.uint8)
        sample = rng.integers(0, 256, size=(3, width, 3), dtype=np.uint8)
        out = zoom_blend_step(acc, sample)
        for row in range(3):
            for ch in range(3):
                assert out[row, :, ch].tolist() == _ref_step_row(
                    acc[row, :, ch].tolist(), sample[row, :, ch].tolist()
                )

    def test_blend_is_integer_and_can_darken_by_one_level(self):
        """A súlyok összege 255, az osztó 256: egyforma érték is sötétedhet."""
        flat = np.full((1, 4, 3), 200, dtype=np.uint8)
        out = zoom_blend_step(flat, flat)
        assert out.dtype == np.uint8
        assert np.all(out == (255 * 200) >> 8)

    def test_inputs_are_not_mutated(self):
        rng = np.random.default_rng(3)
        acc = rng.integers(0, 256, size=(2, 8, 3), dtype=np.uint8)
        sample = rng.integers(0, 256, size=(2, 8, 3), dtype=np.uint8)
        acc0, sample0 = acc.copy(), sample.copy()
        zoom_blend_step(acc, sample)
        np.testing.assert_array_equal(acc, acc0)
        np.testing.assert_array_equal(sample, sample0)


class TestSampleOrder:
    def test_offsets_descend_from_the_largest(self):
        # off = ⌊k·D / N⌋, k = N … 1
        assert zoom_offsets(5, 250) == (250, 200, 150, 100, 50)

    def test_offsets_floor_division(self):
        assert zoom_offsets(6, 4) == (4, 3, 2, 2, 1, 0)

    def test_offsets_are_non_increasing(self):
        offs = zoom_offsets(30, 853)
        assert len(offs) == 30
        assert list(offs) == sorted(offs, reverse=True)
        assert offs[0] == 853

    def test_the_order_matters_for_the_result(self):
        """A keverés nem kommutatív: fordított sorrend más képet adna — a
        kernelnek a csökkenő sorrend kimenetét kell adnia."""
        rng = np.random.default_rng(11)
        image = rng.integers(0, 256, size=(9, 13, 3), dtype=np.uint8)
        ours = zoom_blur(image, 0.4, 0.6, 30.0)
        np.testing.assert_array_equal(ours, _ref_zoom_blur(image, 0.4, 0.6, 30.0))

        height, width = image.shape[:2]
        acc = image.copy()
        for off in reversed(zoom_offsets(zoom_sample_count(30.0), zoom_max_offset(width, 30.0))):
            ys = zoom_sample_indices(height, off, 0.6 * height)
            xs = zoom_sample_indices(width, off, 0.4 * width)
            acc = zoom_blend_step(acc, image[ys][:, xs])
        assert not np.array_equal(ours, acc)


class TestSampling:
    @pytest.mark.parametrize("length", [7, 13, 120, 2560])
    @pytest.mark.parametrize("off", [0, 1, 3, 250, 853])
    @pytest.mark.parametrize("focus", [0.0, 0.3, 0.5, 1.0])
    def test_nearest_neighbour_indices_match_the_16_16_formula(self, length, off, focus):
        got = zoom_sample_indices(length, off, focus * length)
        expected = [_ref_index(p, length, off, focus * length) for p in range(length)]
        assert got.tolist() == expected

    @pytest.mark.parametrize("focus", [0.0, 0.5, 1.0])
    def test_indices_stay_inside_the_image(self, focus):
        got = zoom_sample_indices(2560, 1280, focus * 2560)
        assert got.min() >= 0 and got.max() <= 2559

    def test_centre_focus_never_needs_the_clamp(self):
        """Középfókusznál (a mért eset) a képlet magától a képen belül marad:
        `max u < W`, amíg `x < W²/(W+off)`."""
        for off in (1, 250, 853, 1280):
            u_max = (2559.5 * 2560 / (2560 + off)) + off * 1280 / 2560
            assert u_max < 2560

    def test_zero_offset_is_identity_sampling(self):
        assert zoom_sample_indices(17, 0, 8.5).tolist() == list(range(17))


class TestKernelEndToEnd:
    @pytest.mark.parametrize(
        ("shape", "x", "y", "impact"),
        [((9, 13, 3), 0.5, 0.5, 50.0), ((6, 16, 3), 0.2, 0.9, 1.0), ((11, 10, 3), 1.0, 0.0, 100.0)],
    )
    def test_matches_the_scalar_reference(self, shape, x, y, impact):
        rng = np.random.default_rng(sum(shape))
        image = rng.integers(0, 256, size=shape, dtype=np.uint8)
        np.testing.assert_array_equal(
            zoom_blur(image, x, y, impact), _ref_zoom_blur(image, x, y, impact)
        )

    @pytest.mark.parametrize("height", [63, 64, 65, 150, 201])
    def test_row_bands_join_seamlessly(self, height):
        """A `zoom_blur` sávonként dolgozik; a kimenet a teljes képes
        lépésenkénti keveréssel azonos, a sávhatárokon is."""
        rng = np.random.default_rng(height)
        image = rng.integers(0, 256, size=(height, 300, 3), dtype=np.uint8)
        acc = image.copy()
        for off in zoom_offsets(zoom_sample_count(50.0), zoom_max_offset(300, 50.0)):
            ys = zoom_sample_indices(height, off, 0.3 * height)
            xs = zoom_sample_indices(300, off, 0.6 * 300)
            acc = zoom_blend_step(acc, image[ys][:, xs])
        np.testing.assert_array_equal(zoom_blur(image, 0.6, 0.3, 50.0), acc)

    def test_full_mask_gives_the_kernel_output(self):
        """`Radius = 0` → a maszk mindenütt 1: a kimenet maga a kernel."""
        rng = np.random.default_rng(5)
        image = rng.integers(0, 256, size=(12, 20, 3), dtype=np.uint8)
        out = apply_focal_zoom(image, x=0.5, y=0.5, impact=50.0, radius=0.0, fade=0.0)
        np.testing.assert_array_equal(out, _ref_zoom_blur(image, 0.5, 0.5, 50.0))

    def test_zero_offset_steps_still_blend(self):
        """A `k·D < N` lépések `off = 0`-val mintáznak, de a 38/217-es súly
        ekkor is keveri őket: egy egyszínű kép egyenletesen sötétedik (a
        Picasa `min` exportja is ~2,5 szinttel sötétebb)."""
        image = np.full((4, 400, 3), 200, dtype=np.uint8)
        out = zoom_blur(image, 0.5, 0.5, 1.0)  # N = 6, D = 2 → off: 2,1,1,1,0,0
        assert zoom_offsets(6, 2) == (2, 1, 1, 1, 0, 0)
        assert np.all(out < 200)

    def test_the_unmeasured_border_assumption_is_gone(self):
        """A mintavétel mindig a képen belül esik: a `BORDER_REPLICATE`-es
        „méretlen feltevés” megjegyzésnek nincs tárgya."""
        source = inspect.getsource(focal)
        assert "BORDER_REPLICATE" not in source
        assert "MÉRETLEN FELTEVÉS" not in source


class TestFastLivePreview:
    """A csúszka húzása közben (`gyors_elonezet`) a natív kernel 2560 px-en
    ~1,7× lassabb a régi OpenCV-útnál; ott ugyanazokkal az indexekkel, de
    OpenCV-vel (`remap` + `addWeighted`, sávhiba nélkül) fut. Mentés, export,
    bélyegkép és az elengedés utáni kép a natív utat használja."""

    def test_fast_path_is_close_to_the_native_kernel(self):
        """Sima (fotószerű) képen a két út csak a kerekítésben és a
        sávhibában tér el — zajon a sávhiba nagyobb, de az nem fotó."""
        ys, xs = np.mgrid[0:120, 0:200]
        image = np.stack(
            [xs * 255 // 199, ys * 255 // 119, (xs + ys) * 255 // 318], axis=-1
        ).astype(np.uint8)
        native = zoom_blur(image, 0.5, 0.5, 50.0)
        fast = zoom_blur(image, 0.5, 0.5, 50.0, gyors=True)
        assert not np.array_equal(fast, native)
        diff = np.abs(fast.astype(int) - native.astype(int))
        assert diff.mean() < 1.5 and diff.max() <= 8

    def test_fast_path_samples_the_same_nearest_neighbour_indices(self):
        """Kétképpontos csíkokon a sávhiba nem hat (a 2. képpont a 0.-val
        azonos paritású): a gyors út a natív legközelebbi-szomszéd mintát
        követi (egy bilineáris ~127-es szürkére mosná), csak az OpenCV
        fixpontos keverése tér el néhány szintet."""
        image = np.zeros((40, 64, 3), dtype=np.uint8)
        image[:, ::2] = 255
        fast = zoom_blur(image, 0.5, 0.5, 50.0, gyors=True)
        acc = image.copy()
        for off in zoom_offsets(zoom_sample_count(50.0), zoom_max_offset(64, 50.0)):
            ys = zoom_sample_indices(40, off, 20.0)
            xs = zoom_sample_indices(64, off, 32.0)
            sample = image[ys][:, xs].astype(np.float64)
            acc = np.floor(sample * 38 / 256 + acc * 217 / 256)
        diff = np.abs(fast.astype(int) - acc.astype(int))
        assert diff.mean() < 1.0 and diff.max() <= 8
        assert np.abs(fast.astype(int)[:, :-1] - fast.astype(int)[:, 1:]).mean() > 30

    def test_the_chain_switches_to_the_fast_path_only_inside_the_block(self):
        from picasapy.ini.filters import parse_filters
        from picasapy.render.chain import apply_filters
        from picasapy.render.elonezeti_arany import gyors_elonezet

        rng = np.random.default_rng(8)
        image = rng.integers(0, 256, size=(60, 90, 3), dtype=np.uint8)
        chain = parse_filters("FocalZoom=1,0.5,0.5,50.0,0.0,50.0,0.0;")
        native = apply_filters(image, chain).image
        with gyors_elonezet():
            fast = apply_filters(image, chain).image
        assert not np.array_equal(native, fast)
        np.testing.assert_array_equal(native, apply_filters(image, chain).image)
