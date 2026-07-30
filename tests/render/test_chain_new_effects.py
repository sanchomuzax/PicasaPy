"""#329/#330: az új effektek a RENDERLÁNCBÓL is elérhetők.

A modul megléte önmagában semmit sem ér: amíg a `chain._HANDLERS` nem ismeri
a `filters=` kulcsot, a Picasával szerkesztett kép némán effekt nélkül
jelenik meg (a lánc ismeretlen névként kihagyja). Ez a teszt azt őrzi, hogy
a kulcs → handler bekötés tényleg megtörtént, és hogy a lánc a KIMENETET is
megváltoztatja.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import _HANDLERS, apply_filters

_CREATIVE_KEYS = (
    "ir",
    "lomo",
    "holga",
    "hdr",
    "cinemascope",
    "orton",
    "sixties",
    "invert",
    "heatmap",
    "crossprocess",
    "quantizepalette",
    "twotone",
)


@pytest.fixture
def sample() -> np.ndarray:
    """Színes, strukturált kép — a legtöbb effekt ezen mérhetően változtat."""
    rng = np.random.default_rng(7)
    image = rng.integers(40, 215, size=(64, 96, 3), dtype=np.uint8)
    image[:20, :, 0] = 200  # vízszintes sávok, hogy legyen éldetektálható él
    image[40:, :, 2] = 60
    return image


class TestCreativeEffectsAreWired:
    @pytest.mark.parametrize("key", _CREATIVE_KEYS)
    def test_handler_registered(self, key):
        assert key in _HANDLERS, f"a(z) {key!r} nincs bekötve a láncba"

    @pytest.mark.parametrize("key", _CREATIVE_KEYS)
    def test_chain_applies_it_and_skips_nothing(self, key, sample):
        result, skipped = apply_filters(sample, parse_filters(f"{key}=1;"))
        assert skipped == (), f"a lánc kihagyta: {skipped}"
        assert result.shape[2] == 3 and result.dtype == np.uint8

    @pytest.mark.parametrize("key", _CREATIVE_KEYS)
    def test_output_actually_changes(self, key, sample):
        result, _ = apply_filters(sample, parse_filters(f"{key}=1;"))
        if result.shape != sample.shape:
            return  # a cinemascope sávozhat/vághat — a méretváltozás is hatás
        assert not np.array_equal(result, sample), (
            f"a(z) {key!r} nem változtatott a képen — hamis zöld veszélye"
        )

    def test_original_picasa_spelling_is_recognised(self, sample):
        # a Picasa NAGY kezdőbetűvel írja: `HeatMap=1;`, `QuantizePalette=1;`
        for spelled in ("HeatMap", "QuantizePalette", "CrossProcess", "TwoTone", "IR"):
            _result, skipped = apply_filters(sample, parse_filters(f"{spelled}=1;"))
            assert skipped == (), f"{spelled}: a lánc nem ismerte fel"

    def test_input_is_not_mutated(self, sample):
        before = sample.copy()
        for key in _CREATIVE_KEYS:
            apply_filters(sample, parse_filters(f"{key}=1;"))
        assert np.array_equal(sample, before)


_ARTISTIC_KEYS = (
    "boost",
    "soften",
    "pixelate",
    "focalzoom",
    "pencilsketch",
    "neon",
    "comicize",
    "border",
    "dropshadow",
    "museummatte",
    "polaroid",
)

#: Ezek keretet tesznek a kép köré, tehát MEGNÖVELIK a méretet (#330).
_FRAME_KEYS = ("border", "dropshadow", "museummatte", "polaroid")


class TestArtisticEffectsAreWired:
    @pytest.mark.parametrize("key", _ARTISTIC_KEYS)
    def test_handler_registered(self, key):
        assert key in _HANDLERS, f"a(z) {key!r} nincs bekötve a láncba"

    @pytest.mark.parametrize("key", _ARTISTIC_KEYS)
    def test_chain_applies_it(self, key, sample):
        result, skipped = apply_filters(sample, parse_filters(f"{key}=1;"))
        assert skipped == (), f"a lánc kihagyta: {skipped}"
        assert result.dtype == np.uint8 and result.shape[2] == 3

    @pytest.mark.parametrize("key", _FRAME_KEYS)
    def test_frames_enlarge_the_picture(self, key, sample):
        result, _ = apply_filters(sample, parse_filters(f"{key}=1;"))
        assert result.shape[0] > sample.shape[0]
        assert result.shape[1] > sample.shape[1]


class TestArtisticParametersReachTheRenderer:
    """#332: az ini-ben ott álló paraméterek (a Picasában elhúzott csúszkák)
    tényleg hassanak — ne az alapérték fusson helyettük."""

    @pytest.mark.parametrize(
        ("weak", "strong"),
        [
            ("Boost=1,5.000000;", "Boost=1,95.000000;"),
            ("Soften=1,5.000000,20.000000;", "Soften=1,95.000000,90.000000;"),
            ("Pixelate=1,4.000000,9.000000,0.000000;", "Pixelate=1,32.000000,9.000000,0.000000;"),
            (
                "PencilSketch=1,2.000000,40.000000,0.000000;",
                "PencilSketch=1,9.000000,140.000000,0.000000;",
            ),
            ("Comicize=1,5.000000,20.000000,20.000000;", "Comicize=1,60.000000,90.000000,90.000000;"),
        ],
    )
    def test_different_parameters_give_different_output(self, weak, strong, sample):
        a, skipped_a = apply_filters(sample, parse_filters(weak))
        b, skipped_b = apply_filters(sample, parse_filters(strong))
        assert skipped_a == () and skipped_b == ()
        assert not np.array_equal(a, b), "a paraméter nem jutott el a rendererhez"

    def test_border_width_changes_the_size(self, sample):
        thin, _ = apply_filters(
            sample,
            parse_filters("Border=1,5.000000,5.000000,0.000000,00000000,00ffffff,0.000000;"),
        )
        thick, _ = apply_filters(
            sample,
            parse_filters("Border=1,40.000000,5.000000,0.000000,00000000,00ffffff,0.000000;"),
        )
        assert thick.shape[0] > thin.shape[0]

    def test_polaroid_width_changes_the_size(self, sample):
        thin, _ = apply_filters(sample, parse_filters("Polaroid=1,3.000000,00e2e2e2;"))
        thick, _ = apply_filters(sample, parse_filters("Polaroid=1,15.000000,00e2e2e2;"))
        assert thick.shape[0] > thin.shape[0]

    def test_broken_parameter_does_not_stop_the_chain(self, sample):
        # #301: a hibás bejegyzés kimarad, a lánc többi tagja lefut
        result, skipped = apply_filters(
            sample, parse_filters("Boost=1,zzz;Invert=1;")
        )
        assert "Boost" in skipped
        assert not np.array_equal(result, sample), "az Invert ettől még lefutott"


class TestCropRunsBeforeTheFrame:
    """A vágás koordinátái az EREDETI képre vonatkoznak (spec), a keret
    viszont utólag kerül köré — különben a keret szélességével elcsúszna a
    vágás, és a kereten belül rossz kivágás látszana."""

    def test_crop_then_border(self, sample):
        # a bal felső negyed kivágása + fehér keret
        chain = "crop64=1,000000007fff7fff;border=1;"
        result, skipped = apply_filters(sample, parse_filters(chain))
        assert skipped == ()
        cropped_only, _ = apply_filters(sample, parse_filters("crop64=1,000000007fff7fff;"))
        # a keret mindkét irányban ugyanannyival nagyobb a VÁGOTT képnél
        grow_y = result.shape[0] - cropped_only.shape[0]
        grow_x = result.shape[1] - cropped_only.shape[1]
        assert grow_y > 0 and grow_x > 0
        # és a szélső pixelsor a keret (fehér), nem a fotó
        assert (result[0, :, :] > 200).all()

    def test_frame_does_not_break_a_later_crop(self, sample):
        # fordított sorrend a láncban: a crop akkor is az eredetire vonatkozik
        result, skipped = apply_filters(
            sample, parse_filters("border=1;crop64=1,000000007fff7fff;")
        )
        assert skipped == ()
        assert result.shape[0] > 0 and result.shape[1] > 0
