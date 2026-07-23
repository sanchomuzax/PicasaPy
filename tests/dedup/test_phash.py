"""dHash számítás és Hamming-távolság tulajdonságai."""

from picasapy.dedup.phash import compute_dhash, hamming_distance

from support_images import checkerboard_jpeg, gradient_jpeg, resave_as_jpeg


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
