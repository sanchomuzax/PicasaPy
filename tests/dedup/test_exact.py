"""Pontos (bitre azonos) duplikátum-keresés."""

from picasapy.dedup.exact import file_content_hash, group_exact_duplicates

from support.jpeg_factory import make_jpeg


class TestFileContentHash:
    def test_identical_bytes_same_hash(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"ugyanaz a tartalom")
        b.write_bytes(b"ugyanaz a tartalom")
        assert file_content_hash(a) == file_content_hash(b)

    def test_different_bytes_different_hash(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"elso tartalom")
        b.write_bytes(b"masodik tartalom")
        assert file_content_hash(a) != file_content_hash(b)

    def test_missing_file_returns_none(self, tmp_path):
        assert file_content_hash(tmp_path / "nincs.jpg") is None


class TestGroupExactDuplicates:
    def test_two_identical_files_form_a_group(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())

        groups = group_exact_duplicates((original, copy))

        assert len(groups) == 1
        assert groups[0].paths == tuple(sorted((original, copy), key=str))

    def test_unique_files_produce_no_group(self, tmp_path):
        one = make_jpeg(tmp_path / "egy.jpg", size=(40, 20))
        two = make_jpeg(tmp_path / "ketto.jpg", size=(41, 20))  # eltérő méret/tartalom

        assert group_exact_duplicates((one, two)) == ()

    def test_different_size_never_hashed_as_pair(self, tmp_path):
        small = tmp_path / "kicsi.bin"
        big = tmp_path / "nagy.bin"
        small.write_bytes(b"x" * 10)
        big.write_bytes(b"x" * 20)
        assert group_exact_duplicates((small, big)) == ()

    def test_three_way_duplicate_single_group(self, tmp_path):
        payload = b"harmas duplikatum"
        paths = []
        for name in ("c.jpg", "a.jpg", "b.jpg"):
            path = tmp_path / name
            path.write_bytes(payload)
            paths.append(path)

        groups = group_exact_duplicates(paths)

        assert len(groups) == 1
        assert groups[0].paths == tuple(sorted(paths, key=str))

    def test_input_sequence_not_mutated(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())
        paths = [copy, original]
        before = list(paths)

        group_exact_duplicates(paths)

        assert paths == before

    def test_deterministic_group_order(self, tmp_path):
        payload_1 = b"elso duplikatum part"
        payload_2 = b"masodik duplikatum part"
        names_and_payloads = [
            ("z1.jpg", payload_1),
            ("a1.jpg", payload_1),
            ("z2.jpg", payload_2),
            ("a2.jpg", payload_2),
        ]
        paths = []
        for name, payload in names_and_payloads:
            path = tmp_path / name
            path.write_bytes(payload)
            paths.append(path)

        forward = group_exact_duplicates(paths)
        backward = group_exact_duplicates(list(reversed(paths)))

        assert forward == backward
        assert [group.paths[0].name for group in forward] == ["a1.jpg", "a2.jpg"]

    def test_missing_file_is_skipped_not_raised(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        assert group_exact_duplicates((original, tmp_path / "nincs.jpg")) == ()
