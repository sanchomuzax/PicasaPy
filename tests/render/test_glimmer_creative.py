"""#381: `glimmer_creative` — Cinemascope/Orton/PencilSketch/Holga/Lomo/IR/
Neon min/alap/max határeset-tesztjei.
"""

from __future__ import annotations

import time

import cv2
import numpy as np
import pytest

from picasapy.render import glimmer_creative as c
from tests.support.realistic_photo import make_realistic_photo


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(21)
    img = rng.integers(20, 235, size=(64, 96, 3), dtype=np.uint8)
    img[:20, :, 0] = 220
    return img


def _real_photo_rgb(height: int, width: int, seed: int = 7) -> np.ndarray:
    """#504 (j1): VALÓDI, folytonos hisztogramú fotó-szerű kép, a
    `render/chain.py`/`export/exporter.py` mintáját követve BGR→RGB
    konvertálva (a glimmer-csővezeték RGB-terű, ld. `glimmer_ops.py`)."""
    return cv2.cvtColor(make_realistic_photo(height=height, width=width, seed=seed), cv2.COLOR_BGR2RGB)


def _assert_valid(result):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3


class TestCinemascope:
    def test_letterbox_be(self, image):
        result = c.apply_cinemascope(image, letterbox=True)
        _assert_valid(result)
        assert result.shape[0] != image.shape[0] or result.shape[1] != image.shape[1]

    def test_letterbox_ki(self, image):
        result = c.apply_cinemascope(image, letterbox=False)
        _assert_valid(result)
        assert result.shape[1] == image.shape[1]

    def test_letterbox_sav_fekete(self, image):
        result = c.apply_cinemascope(image, letterbox=True)
        assert tuple(result[0, result.shape[1] // 2]) == (0, 0, 0)


class TestOrton:
    @pytest.mark.parametrize("bloom,brightness,fade", [(0.0, 0.0, 0.0), (25.0, 50.0, 0.0), (50.0, 100.0, 100.0)])
    def test_hatarok(self, image, bloom, brightness, fade):
        _assert_valid(c.apply_orton(image, bloom=bloom, brightness=brightness, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_orton(image, fade=100.0), image)


class TestPencilSketch:
    @pytest.mark.parametrize("radius,contrast,fade", [(1.3, 0.0, 0.0), (2.0, 100.0, 0.0), (5.0, 200.0, 100.0)])
    def test_hatarok(self, image, radius, contrast, fade):
        _assert_valid(c.apply_pencil_sketch(image, radius=radius, contrast=contrast, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_pencil_sketch(image, fade=100.0), image)


class TestHolga:
    @pytest.mark.parametrize("blur,grain,fade", [(0.0, 0.0, 0.0), (70.0, 30.0, 0.0), (100.0, 100.0, 100.0)])
    def test_hatarok(self, image, blur, grain, fade):
        _assert_valid(c.apply_holga(image, blur=blur, grain=grain, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_holga(image, fade=100.0), image)

    @pytest.mark.parametrize("height,width", [(64, 96), (600, 800)])
    def test_nem_fekete_a_kimenet(self, height, width):
        """#504: a Holga kisképe feketedett be nagy szigmájú belső
        ragyogásnál — a kimenet átlagos fényessége maradjon érdemben
        nulla fölött kicsi ÉS nagy képen is.
        """
        rng = np.random.default_rng(11)
        img = rng.integers(20, 235, size=(height, width, 3), dtype=np.uint8)
        result = c.apply_holga(img)
        assert result.mean() > 5.0


class TestLomo:
    @pytest.mark.parametrize("blur,fade", [(0.0, 0.0), (50.0, 0.0), (100.0, 100.0)])
    def test_hatarok(self, image, blur, fade):
        _assert_valid(c.apply_lomo(image, blur=blur, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_lomo(image, fade=100.0), image)

    @pytest.mark.parametrize("height,width", [(64, 96), (600, 800)])
    def test_nem_fekete_a_kimenet(self, height, width):
        """#504: a Lomo kisképe feketedett be (a 800×600-as eset a
        bejelentés szerint teljesen fekete volt, átlag ~0) — a kimenet
        átlagos fényessége maradjon érdemben nulla fölött kicsi ÉS nagy
        képen is.
        """
        rng = np.random.default_rng(11)
        img = rng.integers(20, 235, size=(height, width, 3), dtype=np.uint8)
        result = c.apply_lomo(img)
        assert result.mean() > 5.0

    def test_teljesitmeny_nagy_kepen_gyors(self):
        """#504: a nagy szigmájú belső ragyogás Gauss-elmosása O(percek)
        volt egy fényképméretű (2000×1500) képen — a leskálázott
        elmosásnak ez alá kell szorítania. Nagyvonalú korlát, hogy lassú
        CI-n se legyen ingatag (a mért érték ~1-1,5 s volt fejlesztői
        gépen, a régi kód ~37 s-ot vett igénybe ugyanitt).
        """
        import time

        rng = np.random.default_rng(11)
        img = rng.integers(20, 235, size=(1500, 2000, 3), dtype=np.uint8)
        t0 = time.perf_counter()
        c.apply_lomo(img)
        elapsed = time.perf_counter() - t0
        assert elapsed < 10.0, f"apply_lomo(2000x1500) túl lassú: {elapsed:.2f}s"


def _black_pct(img: np.ndarray) -> float:
    """A tiszta fekete (mindhárom csatornán 0) képpontok aránya, %."""
    return float(np.all(img == 0, axis=-1).mean() * 100.0)


class TestHolgaRealPhoto504510:
    """#504/#510 — VALÓDI (folytonos hisztogramú) fotóval mért regresszió,
    nem szintetikus szürke/zaj lappal (j1). A `main` állapotában a Holga
    sötét (~kétharmad tiszta fekete), de ez az `inner_glow`/`bw_tint`/
    kontraszt-lánc DOKUMENTÁLT, a `filterdesc.xml`-ből átvett receptjének
    a következménye, nem implementációs hiba — ld. a #504 utolsó
    kommentjét és a PR-jelentést. A teszt ezt a MÉRT állapotot rögzíti
    (nem "javítja meg" találgatással), plusz a #510 csatorna-sorrendet
    ellenőrzi.
    """

    def test_r_nagyobb_mint_b_a_kimeneten(self):
        """#510 elfogadási feltétel: a Holga kimenete MELEG (R>B), a
        valódi (fájlba kerülő) BGR-reprezentációban mérve — nem a
        glimmer-belső RGB-tömbön, aminek a csatornasorrendje félrevezette
        az eredeti jegy "bizonyítékát" (ld. jelentés)."""
        photo_rgb = _real_photo_rgb(200, 300)
        result_rgb = c.apply_holga(photo_rgb)
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        red_mean = float(result_bgr[..., 2].mean())
        blue_mean = float(result_bgr[..., 0].mean())
        assert red_mean > blue_mean, f"R={red_mean:.1f} nem nagyobb, mint B={blue_mean:.1f}"

    @pytest.mark.parametrize("effect_name,apply_fn", [("Holga", c.apply_holga), ("Lomo", c.apply_lomo)])
    def test_meretfuggetlen_fekete_arany_a_korlat_ALATT(self, effect_name, apply_fn):
        """j2: a KORLÁT ALATTI tartományban a fekete-arány méretfüggetlen.

        #504 után a `clamp_glow_radius` 255-ös korlátja SZÁNDÉKOSAN
        megtöri a méretfüggetlenséget — de csak ott, ahol a képlet a
        korlát fölé nőne. 96 px és 700 px legnagyobb oldalnál mind az öt
        effekt sugara a korlát ALATT marad (a legnagyobb szorzó 0,35·max
        → 245 < 255), tehát ITT a méretfüggetlenségnek szigorúan állnia
        kell. A korábbi, 96↔1600 px-es változat a két tartományt keverte,
        ezért kellett volna 30 pp-es (érdemi ellenőrzést nem adó) tűrés."""

        small = apply_fn(_real_photo_rgb(96, 72))
        large = apply_fn(_real_photo_rgb(700, 525))
        diff = abs(_black_pct(small) - _black_pct(large))
        assert diff <= 10.0, (
            f"{effect_name}: fekete-arány 96px={_black_pct(small):.1f}% "
            f"vs 700px={_black_pct(large):.1f}% — {diff:.1f}pp eltérés"
        )

    @pytest.mark.parametrize("effect_name,apply_fn", [("Holga", c.apply_holga), ("Lomo", c.apply_lomo)])
    def test_a_korlat_FOLOTT_keskenyebb_a_vignetta(self, effect_name, apply_fn):
        """#504: a korlát fölött a sugár már NEM nő a képmérettel, ezért a
        vignetta relatíve keskenyebb, és ÉRDEMBEN kevesebb a tiszta fekete
        képpont. Ez a korlát létezésének közvetlen, mérhető következménye —
        ha valaki visszavenné a `clamp_glow_radius`-t, ez a teszt bukna."""

        small = apply_fn(_real_photo_rgb(96, 72))
        huge = apply_fn(_real_photo_rgb(2560, 1920))
        assert _black_pct(huge) < _black_pct(small) - 5.0, (
            f"{effect_name}: a korlát fölött NEM csökkent érdemben a fekete-arány "
            f"(96px={_black_pct(small):.1f}%, 2560px={_black_pct(huge):.1f}%)"
        )

    def test_holga_perf_nagy_kepen(self):
        """j5: a ragyogás-lépés (közös `_border_glow`) nagy képen is
        gyors maradjon (a javítás előtt egy 4000×3000-es fotón egyetlen
        ragyogás-lépés 168 s volt — nagyvonalú korlát a lassú CI miatt)."""
        photo_rgb = _real_photo_rgb(1500, 2000)
        t0 = time.perf_counter()
        c.apply_holga(photo_rgb)
        elapsed = time.perf_counter() - t0
        assert elapsed < 20.0, f"apply_holga(2000x1500) túl lassú: {elapsed:.2f}s"


class TestIr:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(c.apply_ir(image, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_ir(image, fade=100.0), image)


class TestNeon:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(c.apply_neon(image, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_neon(image, fade=100.0), image)
