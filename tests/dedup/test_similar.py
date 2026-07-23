"""Perceptuális-hasonlóság klaszterezés (Hamming-távolság + union-find)."""

from picasapy.dedup.similar import group_similar


class TestGroupSimilar:
    def test_close_hashes_form_a_group(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        # 3 bit eltérés — a 10-es alapértelmezett küszöb alatt.
        hashes = [(a, 0b0000_0000), (b, 0b0000_0111)]

        groups = group_similar(hashes)

        assert len(groups) == 1
        assert groups[0].paths == (a, b)
        assert groups[0].max_distance == 3

    def test_far_hashes_produce_no_group(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        hashes = [(a, 0x0), (b, 0xFFFF_FFFF_FFFF_FFFF)]  # 64 bit eltérés

        assert group_similar(hashes) == ()

    def test_threshold_is_configurable(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        hashes = [(a, 0b0000), (b, 0b0111)]  # 3 bit eltérés

        assert group_similar(hashes, threshold=2) == ()
        assert len(group_similar(hashes, threshold=3)) == 1

    def test_chained_similarity_merges_into_one_cluster(self, tmp_path):
        # A~B (3 bit) és B~C (3 bit), de A~C (6 bit, a küszöb felett lenne
        # önmagában) — union-find miatt mégis egy klaszterbe kerülnek.
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        c = tmp_path / "c.jpg"
        hashes = [(a, 0b000000), (b, 0b000111), (c, 0b111111)]

        groups = group_similar(hashes, threshold=3)

        assert len(groups) == 1
        assert groups[0].paths == (a, b, c)

    def test_single_image_forms_no_group(self, tmp_path):
        a = tmp_path / "a.jpg"
        assert group_similar([(a, 0)]) == ()

    def test_empty_input_returns_empty(self):
        assert group_similar([]) == ()

    def test_input_sequence_not_mutated(self, tmp_path):
        a = tmp_path / "b.jpg"
        b = tmp_path / "a.jpg"
        hashes = [(a, 0b0000), (b, 0b0001)]
        before = list(hashes)

        group_similar(hashes)

        assert hashes == before

    def test_deterministic_order_independent_of_input_order(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        c = tmp_path / "c.jpg"
        d = tmp_path / "d.jpg"
        all_ones = 0xFFFF_FFFF_FFFF_FFFF
        hashes = [(a, 0), (b, 1), (c, all_ones), (d, all_ones ^ 1)]

        forward = group_similar(hashes)
        backward = group_similar(list(reversed(hashes)))

        assert forward == backward
        assert [group.paths[0].name for group in forward] == ["a.jpg", "c.jpg"]
