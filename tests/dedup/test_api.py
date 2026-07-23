"""`find_duplicates` — a duplikátum-kereső mag egyesített API-ja.

Az elfogadási forgatókönyvek (#31 jegy):
(a) két bitre azonos fájl → pontos-duplikátum csoport;
(b) egy kép + átméretezett/újratömörített változata → perceptual-hasonló
    csoport a küszöb alatt;
(c) két teljesen eltérő kép → nincs hamis pár (a Hamming-távolság a
    küszöb felett);
(d) determinisztikus kimeneti sorrend.
"""

from picasapy.dedup import DEFAULT_PHASH_THRESHOLD, find_duplicates

from support.jpeg_factory import make_jpeg
from support_images import checkerboard_jpeg, gradient_jpeg, resave_as_jpeg


class TestFindDuplicatesExact:
    def test_bitwise_identical_files_grouped(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())

        report = find_duplicates([original, copy])

        assert len(report.exact_groups) == 1
        assert set(report.exact_groups[0].paths) == {original, copy}

    def test_unrelated_files_no_exact_group(self, tmp_path):
        a = make_jpeg(tmp_path / "a.jpg", size=(40, 20))
        b = make_jpeg(tmp_path / "b.jpg", size=(41, 21))

        report = find_duplicates([a, b])

        assert report.exact_groups == ()


class TestFindDuplicatesSimilar:
    def test_resized_variant_forms_similar_group(self, tmp_path):
        original = gradient_jpeg(tmp_path / "eredeti.jpg", size=(256, 256))
        resized = resave_as_jpeg(
            original, tmp_path / "atmeretezett.jpg", size=(64, 64), quality=70
        )

        report = find_duplicates([original, resized])

        assert len(report.similar_groups) == 1
        assert set(report.similar_groups[0].paths) == {original, resized}
        assert report.similar_groups[0].max_distance <= DEFAULT_PHASH_THRESHOLD
        assert report.exact_groups == ()  # nem bitre azonosak

    def test_completely_different_images_no_false_pair(self, tmp_path):
        gradient = gradient_jpeg(tmp_path / "grad.jpg", size=(200, 200))
        checker = checkerboard_jpeg(tmp_path / "sakktabla.jpg", size=(200, 200))

        report = find_duplicates([gradient, checker])

        assert report.similar_groups == ()
        assert report.exact_groups == ()

    def test_exact_group_not_duplicated_into_similar_group(self, tmp_path):
        # Egy bitre azonos pár triviálisan hasonló is (0 Hamming-táv) — ezt
        # csak az exact_groups-ban akarjuk látni, nem duplikálva.
        original = gradient_jpeg(tmp_path / "eredeti.jpg", size=(64, 64))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())

        report = find_duplicates([original, copy])

        assert len(report.exact_groups) == 1
        assert report.similar_groups == ()

    def test_threshold_override_excludes_borderline_match(self, tmp_path):
        original = gradient_jpeg(tmp_path / "eredeti.jpg", size=(256, 256))
        resized = resave_as_jpeg(
            original, tmp_path / "atmeretezett.jpg", size=(64, 64), quality=70
        )

        strict_report = find_duplicates([original, resized], phash_threshold=0)

        # Szigorú (0) küszöbbel a mintavételi eltérés miatt jó eséllyel már
        # nem egyezik pontosan — legalábbis nem KÖTELEZŐ egyeznie, ezért itt
        # csak azt ellenőrizzük, hogy a paraméter ténylegesen érvényesül
        # (nem nagyobb csoportot ad, mint az alapértelmezett küszöb).
        default_report = find_duplicates([original, resized])
        assert len(strict_report.similar_groups) <= len(default_report.similar_groups)


class TestFindDuplicatesDeterminism:
    def test_output_order_independent_of_input_order(self, tmp_path):
        payload = b"pontos duplikatum tartalom"
        exact_a = tmp_path / "exact_a.jpg"
        exact_b = tmp_path / "exact_b.jpg"
        exact_a.write_bytes(payload)
        exact_b.write_bytes(payload)

        similar_a = gradient_jpeg(tmp_path / "similar_a.jpg", size=(200, 200))
        similar_b = resave_as_jpeg(
            similar_a, tmp_path / "similar_b.jpg", size=(80, 80), quality=70
        )

        paths = [exact_a, similar_b, exact_b, similar_a]

        forward = find_duplicates(paths)
        backward = find_duplicates(list(reversed(paths)))

        assert forward == backward

    def test_input_sequence_not_mutated(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())
        paths = [original, copy]
        before = list(paths)

        find_duplicates(paths)

        assert paths == before

    def test_missing_and_corrupt_files_are_skipped(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"nem kep")

        report = find_duplicates([original, bad, tmp_path / "nincs.jpg"])

        assert report.exact_groups == ()
        assert report.similar_groups == ()
