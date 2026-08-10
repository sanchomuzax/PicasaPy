"""has_enough_free_space / required_bytes_for (#459, jegy 4. pontja:
lemezhely-ellenőrzés nagy műveletek előtt)."""

from picasapy.fileops import has_enough_free_space, required_bytes_for


class TestRequiredBytesFor:
    def test_sums_existing_file_sizes(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"x" * 100)
        b.write_bytes(b"y" * 250)
        assert required_bytes_for([a, b]) == 350

    def test_skips_missing_files(self, tmp_path):
        a = tmp_path / "a.jpg"
        a.write_bytes(b"x" * 10)
        missing = tmp_path / "missing.jpg"
        assert required_bytes_for([a, missing]) == 10

    def test_empty_iterable_is_zero(self, tmp_path):
        assert required_bytes_for([]) == 0


class TestHasEnoughFreeSpace:
    def test_true_when_requirement_well_below_free_space(self, tmp_path):
        assert has_enough_free_space(tmp_path, required_bytes=1) is True

    def test_false_when_requirement_exceeds_free_space(self, tmp_path):
        # a valós szabad hely szinte biztosan kisebb, mint 1 exabájt
        huge = 10**18
        assert has_enough_free_space(tmp_path, required_bytes=huge) is False

    def test_walks_up_to_existing_ancestor_for_missing_target(self, tmp_path):
        not_yet_created = tmp_path / "export" / "subdir"
        assert has_enough_free_space(not_yet_created, required_bytes=1) is True

    def test_defensively_true_when_usage_cannot_be_determined(self, tmp_path, monkeypatch):
        import shutil

        def boom(_path):
            raise OSError("nem érhető el")

        monkeypatch.setattr(shutil, "disk_usage", boom)
        assert has_enough_free_space(tmp_path, required_bytes=10**18) is True
