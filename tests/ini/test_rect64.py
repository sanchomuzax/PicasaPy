"""rect64 dekódolás/kódolás — spec: docs/specs/picasa-ini-format.md."""

import pytest

from picasapy.ini import Rect64, decode_rect64, encode_rect64


class TestDecode:
    def test_spec_example(self):
        rect = decode_rect64("3f845bcb59418507")
        assert rect.left == pytest.approx(0.248108, abs=1e-6)
        assert rect.top == pytest.approx(0.358566, abs=1e-6)
        assert rect.right == pytest.approx(0.348648, abs=1e-6)
        assert rect.bottom == pytest.approx(0.519638, abs=1e-6)

    def test_wrapped_form(self):
        plain = decode_rect64("3f845bcb59418507")
        wrapped = decode_rect64("rect64(3f845bcb59418507)")
        assert wrapped == plain

    def test_short_value_is_left_padded(self):
        # A Picasa elhagyja a vezető nullákat: zfill(16) kötelező.
        rect = decode_rect64("5bcb59418507")
        assert rect.left == 0.0
        assert rect.top == pytest.approx(0x5BCB / 65536, abs=1e-9)

    def test_full_frame(self):
        rect = decode_rect64("ffffffffffffffff")
        assert rect.right == pytest.approx(65535 / 65536, abs=1e-9)

    @pytest.mark.parametrize("bad", ["", "xyz", "3f845bcb594185071", "rect64()"])
    def test_invalid_raises(self, bad):
        with pytest.raises(ValueError):
            decode_rect64(bad)


class TestEncode:
    def test_roundtrip_exact(self):
        value = "3f845bcb59418507"
        assert encode_rect64(decode_rect64(value)) == value

    def test_leading_zeros_preserved(self):
        # A crop64=1,10000000f1ddff49 példában is megmaradnak a vezető nullák.
        value = "10000000f1ddff49"
        assert encode_rect64(decode_rect64(value)) == value

    def test_zero_rect(self):
        assert encode_rect64(Rect64(0.0, 0.0, 0.0, 0.0)) == "0000000000000000"

    @pytest.mark.parametrize(
        "rect",
        [
            Rect64(-0.1, 0.0, 0.5, 0.5),
            Rect64(0.0, 0.0, 1.5, 0.5),
        ],
    )
    def test_out_of_range_raises(self, rect):
        with pytest.raises(ValueError):
            encode_rect64(rect)


class TestImmutability:
    def test_rect_is_frozen(self):
        rect = Rect64(0.1, 0.2, 0.3, 0.4)
        with pytest.raises(AttributeError):
            rect.left = 0.5
