"""Perceptuális-hasonlóság klaszterezés (Hamming-távolság + union-find)."""

import random
from pathlib import Path

from picasapy.dedup.phash import hamming_distance
from picasapy.dedup.similar import group_similar


def _naive_groups(hashes, threshold):
    """Referencia-implementáció: a #294 ELŐTTI, minden párt összevető
    O(n²) klaszterezés — csak az útvonal-halmazokat adja vissza."""
    ordered = sorted(hashes, key=lambda item: str(item[0]))
    parent = list(range(len(ordered)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            if hamming_distance(ordered[i][1], ordered[j][1]) <= threshold:
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[root_i] = root_j

    clusters = {}
    for index in range(len(ordered)):
        clusters.setdefault(find(index), []).append(ordered[index][0])
    return {frozenset(members) for members in clusters.values() if len(members) >= 2}


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


class TestBucketedCandidates:
    """#294: az O(n²) páronkénti összevetés helyett sávos (banding)
    jelöltszűrés — az eredménynek BITRE ugyanannak kell maradnia."""

    def test_matches_the_naive_all_pairs_result_on_random_hashes(self):
        rng = random.Random(20260724)
        for threshold in (0, 3, 10, 20):
            hashes = []
            for i in range(120):
                if i % 5 == 0 and hashes:
                    # néhány közeli variáns, hogy legyenek valódi klaszterek
                    base = hashes[-1][1]
                    value = base ^ (1 << rng.randrange(64)) ^ (1 << rng.randrange(64))
                else:
                    value = rng.getrandbits(64)
                hashes.append((Path(f"/kepek/{i:03d}.jpg"), value))
            actual = {frozenset(group.paths) for group in group_similar(
                hashes, threshold=threshold
            )}
            assert actual == _naive_groups(hashes, threshold), threshold

    def test_no_false_negative_at_exactly_the_threshold(self):
        """A sávos szűrés pigeonhole-elve: `küszöb+1` sávnál a küszöbnyi
        eltérő bit nem eshet MINDEN sávba — pontosan a küszöbön lévő párt
        is meg kell találnia."""
        threshold = 10
        base = 0xA5A5_5A5A_0F0F_F0F0
        # 10 bit átbillentése, szándékosan szétszórva a 64 biten
        flipped = base
        for bit in range(0, 60, 6):  # 0, 6, ..., 54 → pontosan 10 bit
            flipped ^= 1 << bit
        assert hamming_distance(base, flipped) == threshold
        hashes = [(Path("/kepek/a.jpg"), base), (Path("/kepek/b.jpg"), flipped)]

        groups = group_similar(hashes, threshold=threshold)

        assert len(groups) == 1
        assert groups[0].max_distance == threshold

    def test_compares_far_fewer_pairs_than_all_pairs(self, monkeypatch):
        """A Hamming-összevetések száma töredéke a teljes n(n-1)/2-nek.
        VÉLETLEN (maximálisan szórt) hash-eken ez a legrosszabb eset —
        valódi könyvtárban a sávok ennél is jobban szűrnek, mert a
        fényképek hash-ei nem egyenletesen töltik ki a 64 bites teret."""
        import picasapy.dedup.similar as similar_module

        rng = random.Random(4711)
        hashes = [
            (Path(f"/kepek/{i:04d}.jpg"), rng.getrandbits(64)) for i in range(400)
        ]
        calls = 0
        real = similar_module.hamming_distance

        def counting(a, b):
            nonlocal calls
            calls += 1
            return real(a, b)

        monkeypatch.setattr(similar_module, "hamming_distance", counting)
        group_similar(hashes)

        all_pairs = len(hashes) * (len(hashes) - 1) // 2
        assert calls < all_pairs // 4

    def test_huge_identical_cluster_does_not_blow_up(self):
        """Sok ezer AZONOS lenyomatú kép (egyszínű/üres felvételek tömege)
        a naiv úton n²/2 összevetés lenne — a réteg ezeket egyetlen
        reprezentánsba olvasztja, a max-távolságot pedig korlátos
        költséggel adja meg. A teszt ténye, hogy egyáltalán lefut."""
        hashes = [(Path(f"/kepek/{i:05d}.jpg"), 0) for i in range(20_000)]
        groups = group_similar(hashes)
        assert len(groups) == 1
        assert len(groups[0].paths) == 20_000
        assert groups[0].max_distance == 0


class TestCancellation:
    def test_should_stop_aborts_and_reports_partial(self):
        hashes = [(Path(f"/kepek/{i:04d}.jpg"), i) for i in range(500)]
        groups = group_similar(hashes, should_stop=lambda: True)
        assert groups == ()
