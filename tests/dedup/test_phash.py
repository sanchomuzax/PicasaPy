"""dHash számítás és Hamming-távolság tulajdonságai."""

import cv2

from picasapy.cvimage import read_image_bytes
from picasapy.dedup.phash import compute_dhash, hamming_distance

from support_images import (
    checkerboard_jpeg,
    gradient_jpeg,
    photo_like_jpeg,
    resave_as_jpeg,
)


def _full_resolution_dhash(path, hash_size=8):
    """A dHash a #294 ELŐTTI, teljes felbontású dekódolással — a redukált
    út referenciája (ugyanaz a számítás, csak IMREAD_COLOR-ral)."""
    payload = read_image_bytes(path)
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(
        gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA
    )
    value = 0
    for bit in (resized[:, 1:] > resized[:, :-1]).flatten():
        value = (value << 1) | int(bit)
    return value


class TestHammingDistance:
    def test_identical_hash_zero_distance(self):
        assert hamming_distance(0b1010, 0b1010) == 0

    def test_all_bits_flipped_is_full_width(self):
        assert hamming_distance(0, 0xFFFFFFFFFFFFFFFF) == 64

    def test_single_bit_difference(self):
        assert hamming_distance(0b0000, 0b0001) == 1


class TestComputeDhash:
    def test_missing_file_returns_none(self, tmp_path):
        assert compute_dhash(tmp_path / "nincs.jpg") is None

    def test_corrupt_file_returns_none(self, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"nem kep")
        assert compute_dhash(bad) is None

    def test_returns_64_bit_value(self, tmp_path):
        photo = gradient_jpeg(tmp_path / "grad.jpg")
        value = compute_dhash(photo)
        assert value is not None
        assert 0 <= value < (1 << 64)

    def test_same_image_two_sizes_near_zero_distance(self, tmp_path):
        # Ugyanaz a kép két méretben (a hash-számítás maga is kicsinyít,
        # ezért a kis felbontásbeli mintavételi eltérés miatt nem feltétlen
        # pontosan 0, de nagyon alacsony kell legyen).
        original = gradient_jpeg(tmp_path / "eredeti.jpg", size=(256, 256))
        resized = resave_as_jpeg(
            original, tmp_path / "kicsi.jpg", size=(64, 64), quality=90
        )
        distance = hamming_distance(compute_dhash(original), compute_dhash(resized))
        assert distance <= 2

    def test_recompressed_image_low_distance(self, tmp_path):
        original = checkerboard_jpeg(tmp_path / "eredeti.jpg", size=(200, 200))
        recompressed = resave_as_jpeg(
            original, tmp_path / "ujratomoritett.jpg", quality=40
        )
        distance = hamming_distance(
            compute_dhash(original), compute_dhash(recompressed)
        )
        assert distance <= 10

    def test_different_images_high_distance(self, tmp_path):
        gradient = gradient_jpeg(tmp_path / "grad.jpg", size=(200, 200))
        checker = checkerboard_jpeg(tmp_path / "sakktabla.jpg", size=(200, 200))
        distance = hamming_distance(compute_dhash(gradient), compute_dhash(checker))
        assert distance > 10


class TestReducedDecoding:
    """#294: a dHash redukált JPEG-dekódolással készül (a bélyegkép-cache
    `_read_flag` mintájára) — nagyságrenddel gyorsabb, és a küszöb szintjén
    NEM változtatja meg a hash-t."""

    def test_uses_the_shared_reduced_decode_helper(self, tmp_path, monkeypatch):
        import picasapy.dedup.phash as phash_module

        photo = gradient_jpeg(tmp_path / "nagy.jpg", size=(1024, 1024))
        seen = []
        original = phash_module.reduced_color_flag

        def spy(payload, goal):
            flag = original(payload, goal)
            seen.append(flag)
            return flag

        monkeypatch.setattr(phash_module, "reduced_color_flag", spy)
        assert compute_dhash(photo) is not None
        assert seen == [cv2.IMREAD_REDUCED_COLOR_8]

    def test_hash_matches_full_resolution_within_threshold(self, tmp_path):
        """A redukált és a teljes felbontású dekódolásból számolt hash
        távolsága messze a hasonlósági küszöb (10) alatt marad — a
        gyorsítás nem változtatja meg a keresés eredményét."""
        from picasapy.dedup.similar import DEFAULT_PHASH_THRESHOLD

        for name, factory, size in (
            ("grad.jpg", gradient_jpeg, (1024, 768)),
            ("fotoszeru.jpg", photo_like_jpeg, (1600, 1200)),
            ("kicsi.jpg", photo_like_jpeg, (300, 200)),
        ):
            photo = factory(tmp_path / name, size=size)
            distance = hamming_distance(
                compute_dhash(photo), _full_resolution_dhash(photo)
            )
            assert distance < DEFAULT_PHASH_THRESHOLD, name

    def test_identical_pair_still_matches_after_reduction(self, tmp_path):
        original = gradient_jpeg(tmp_path / "eredeti.jpg", size=(1200, 900))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())
        assert compute_dhash(original) == compute_dhash(copy)
