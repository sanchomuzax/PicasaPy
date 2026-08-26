"""A színkeresés osztályozója (#1480) — telítettséggel súlyozott
hue-hisztogram, hét vödör, a legnagyobb vödör nyer.

A tesztek NEM saját küszöbökkel önkonzisztensek, hanem a `Picasa3.exe`
`0x009dbd10` függvényéből MÉRT szabállyal (ld.
`docs/specs/picasa-szinkereses.md`): a vödörhatárok, az `S <= 50` küszöb,
a 353,0–358,8°-os rés és a döntetlen-szabály mind mért viselkedés."""

import colorsys

import numpy as np
import pytest

from picasapy.color import (
    ACHROMATIC_TOKENS,
    HUE_BUCKET_TOKENS,
    average_color,
    avgcolor_to_rgb,
    classify_image,
    hue_histogram,
    pixel_bucket,
    resolve_color_alias,
    rgb_to_avgcolor,
)


def _rgb_for_hue_unit(hue_unit: int) -> tuple[int, int, int]:
    """Egy teljesen telített RGB, amelynek a MÉRT képlet szerinti
    H-értéke pontosan `hue_unit` (0…254).

    A bináris a hue-t 1530 egységes körön számolja (`H1530`), majd
    egészosztással hatoddal skálázza: `H = H1530 / 6`. Itt visszafelé
    építjük: `H1530 = 6 * hue_unit`, MAX = 255, MIN = 0 (tehát Δ = 255,
    S = 255), és a hat ág közül azt választjuk, amelyikbe a kívánt
    `H1530` esik."""
    h1530 = 6 * hue_unit
    if h1530 <= 255:
        return (255, h1530, 0)
    if h1530 <= 510:
        return (510 - h1530, 255, 0)
    if h1530 <= 765:
        return (0, 255, h1530 - 510)
    if h1530 <= 1020:
        return (0, 1020 - h1530, 255)
    if h1530 <= 1275:
        return (h1530 - 1020, 0, 255)
    return (255, 0, 1530 - h1530)


def _solid(rgb: tuple[int, int, int], height: int = 4, width: int = 4) -> np.ndarray:
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, :] = rgb
    return image


# A mért vödör-hozzárendelés: `b = H / 10`, és a switch-ágak (0x009dbea8—
# 0x009dbf47) szerinti vödör. A `None` a MÉRT rés (b == 25).
_EXPECTED_BUCKET_OF_DECADE = {
    0: 0,
    1: 1,
    2: 1,
    3: 1,
    4: 2,
    5: 3,
    6: 3,
    7: 3,
    8: 3,
    9: 3,
    10: 3,
    11: 3,
    12: 4,
    13: 4,
    14: 4,
    15: 4,
    16: 4,
    17: 4,
    18: 5,
    19: 5,
    20: 5,
    21: 5,
    22: 6,
    23: 6,
    24: 0,
    25: None,
}


class TestHueConstruction:
    """Az `_rgb_for_hue_unit` segédfüggvény FÜGGETLEN önellenőrzése: a
    kiszámolt RGB tényleges színárnyalatát a `colorsys` (szabványos HSV)
    adja meg, nem a mi kódunk. Ha ez a helper téved, az alatta lévő
    határesetek is hazudnának."""

    @pytest.mark.parametrize("hue_unit", list(range(0, 255, 7)) + [254])
    def test_helper_hits_the_requested_hue(self, hue_unit):
        red, green, blue = _rgb_for_hue_unit(hue_unit)
        actual = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)[0] * 360.0
        wanted = hue_unit * 360.0 / 255.0
        difference = abs(actual - wanted) % 360.0
        assert min(difference, 360.0 - difference) < 1.5


class TestPixelBucketBoundaries:
    """Mind a 26 hue-tized (`b` = 0…25) — ez tartalmazza a jegyben kért
    14 vödörhatárt is, mindkét oldalról."""

    @pytest.mark.parametrize("decade", sorted(_EXPECTED_BUCKET_OF_DECADE))
    def test_low_edge_of_each_decade(self, decade):
        rgb = _rgb_for_hue_unit(decade * 10)
        assert pixel_bucket(*rgb) == _EXPECTED_BUCKET_OF_DECADE[decade]

    @pytest.mark.parametrize("decade", sorted(_EXPECTED_BUCKET_OF_DECADE))
    def test_high_edge_of_each_decade(self, decade):
        hue_unit = min(decade * 10 + 9, 254)
        rgb = _rgb_for_hue_unit(hue_unit)
        assert pixel_bucket(*rgb) == _EXPECTED_BUCKET_OF_DECADE[decade]

    def test_the_measured_gap_drops_the_pixel(self):
        """b == 25 (H 250–254, kb. 353,0–358,8°) egyetlen vödörbe sem kerül
        — ez az EREDETI viselkedése (0x009dbf31), nem a mi hibánk. Ha egy
        későbbi „javítás" betömné, ez a teszt bukik."""
        for hue_unit in range(250, 255):
            assert pixel_bucket(*_rgb_for_hue_unit(hue_unit)) is None


class TestPixelThresholds:
    def test_black_pixel_is_dropped(self):
        """MAX == 0 → a képpont kimarad (0x009dbdd2)."""
        assert pixel_bucket(0, 0, 0) is None

    def test_saturation_50_is_dropped(self):
        """S = Δ·255/MAX = 50 → `cmp ebp, 0x32` / `jle` → kimarad."""
        assert pixel_bucket(255, 205, 205) is None

    def test_saturation_51_is_kept(self):
        assert pixel_bucket(255, 204, 204) == 0


class TestHistogram:
    def test_weight_is_the_saturation_not_one(self):
        """Három gyenge (S = 51) zöld képpont súlya összesen 153 — kevesebb,
        mint EGYETLEN tiszta piros képponté (255)."""
        image = np.array(
            [[(204, 255, 204), (204, 255, 204)], [(204, 255, 204), (255, 0, 0)]],
            dtype=np.uint8,
        )
        histogram = hue_histogram(image)
        assert histogram[HUE_BUCKET_TOKENS.index("green")] == 153
        assert histogram[HUE_BUCKET_TOKENS.index("red")] == 255
        assert classify_image(image) == ("red",)

    def test_seven_buckets(self):
        assert len(hue_histogram(_solid((255, 0, 0)))) == 7

    def test_bgr_order(self):
        """Az OpenCV BGR-tömbjében a piros a [.., 2] csatornán van."""
        image = np.zeros((2, 2, 3), dtype=np.uint8)
        image[:, :] = (0, 0, 255)  # BGR-ben piros
        assert classify_image(image, order="bgr") == ("red",)
        assert classify_image(image, order="rgb") == ("blue",)


class TestClassifyImage:
    @pytest.mark.parametrize(
        "rgb,expected",
        [
            ((255, 0, 0), "red"),
            ((255, 128, 0), "orange"),
            ((255, 255, 0), "yellow"),
            ((0, 255, 0), "green"),
            ((0, 0, 255), "blue"),
            ((160, 0, 255), "purple"),
            ((255, 0, 160), "pink"),
        ],
    )
    def test_solid_chromatic_image(self, rgb, expected):
        assert classify_image(_solid(rgb)) == (expected,)

    @pytest.mark.parametrize("rgb", [(0, 0, 0), (128, 128, 128), (255, 255, 255)])
    def test_achromatic_image_matches_all_three_tokens(self, rgb):
        """A −1 index a névtáblában EGYSZERRE három tokent ad
        (`color:black color:white color:gray`) — a fekete/fehér/szürke
        között az eredeti NEM tesz különbséget."""
        assert classify_image(_solid(rgb)) == ACHROMATIC_TOKENS

    def test_gap_only_image_is_achromatic(self):
        """Ha MINDEN telített képpont a mért résbe esik, egyetlen vödör sem
        kap súlyt — a 8. (soha nem írt) vödör nyeri a döntetlent, tehát
        −1 = akromatikus."""
        assert classify_image(_solid(_rgb_for_hue_unit(252))) == ACHROMATIC_TOKENS

    def test_a_single_saturated_pixel_decides(self):
        """Nincs abszolút küszöb: egyetlen telített képpont is színessé
        teszi a különben szürke képet."""
        image = _solid((128, 128, 128), height=8, width=8)
        image[0, 0] = (0, 0, 255)
        assert classify_image(image) == ("blue",)

    def test_tie_goes_to_the_higher_bucket(self):
        """Döntetlennél a MAGASABB indexű vödör nyer — a mért argmax
        `v >= max`-ra frissít (0x009dbfb0 `test ah, 1` / `jne`)."""
        image = np.array([[(255, 0, 0), (0, 0, 255)]], dtype=np.uint8)
        assert classify_image(image) == ("blue",)

    def test_empty_raster_is_achromatic(self):
        assert classify_image(np.zeros((0, 0, 3), dtype=np.uint8)) == ACHROMATIC_TOKENS

    def test_alpha_channel_is_ignored(self):
        image = np.zeros((2, 2, 4), dtype=np.uint8)
        image[:, :] = (255, 0, 0, 7)
        assert classify_image(image) == ("red",)

    def test_rejects_non_image_input(self):
        with pytest.raises(ValueError):
            classify_image(np.zeros((4, 4), dtype=np.uint8))

    def test_rejects_unknown_order(self):
        with pytest.raises(ValueError):
            classify_image(_solid((255, 0, 0)), order="xyz")


class TestTokenSets:
    def test_seven_hue_buckets_in_the_measured_order(self):
        """A vödrök sorrendje a névtábláé (0x00424c20): 0=red … 6=pink."""
        assert HUE_BUCKET_TOKENS == (
            "red",
            "orange",
            "yellow",
            "green",
            "blue",
            "purple",
            "pink",
        )

    def test_achromatic_tokens(self):
        assert ACHROMATIC_TOKENS == ("black", "white", "gray")


class TestAliases:
    def test_english_tokens_map_to_themselves(self):
        for token in HUE_BUCKET_TOKENS + ACHROMATIC_TOKENS:
            assert resolve_color_alias(token) == token

    def test_hungarian_names(self):
        assert resolve_color_alias("kék") == "blue"
        assert resolve_color_alias("Rózsaszín") == "pink"

    def test_unknown_word(self):
        assert resolve_color_alias("mályva") is None


class TestAverageColor:
    """Az `avgcolor` (`.picasa.ini`/PMP-mező) VÁLTOZATLAN — de #1480 óta
    tudjuk, hogy a színkeresésnek semmi köze hozzá."""

    def test_solid_color(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)
        image[:, :] = (10, 20, 30)
        assert average_color(image) == (10, 20, 30, 255)

    def test_bgr_order(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)
        image[:, :] = (30, 20, 10)
        assert average_color(image, order="bgr") == (10, 20, 30, 255)

    def test_small_image_has_no_average(self):
        assert average_color(np.zeros((1, 2, 3), dtype=np.uint8)) is None

    def test_rejects_bad_shape(self):
        with pytest.raises(ValueError):
            average_color(np.zeros((4, 4), dtype=np.uint8))

    def test_avgcolor_roundtrip(self):
        assert avgcolor_to_rgb(rgb_to_avgcolor(1, 2, 3)) == (1, 2, 3)
        assert rgb_to_avgcolor(1, 2, 3, 4) == 0x04010203
