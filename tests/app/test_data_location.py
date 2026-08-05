"""Az adatgyökér-felülbírálás (#368) — `picasapy.app.data_location`."""

from __future__ import annotations

from picasapy.app.data_location import clear_data_root, read_data_root, write_data_root


class TestReadDataRoot:
    def test_returns_none_when_no_override_file(self, tmp_path):
        assert read_data_root(tmp_path) is None

    def test_returns_none_for_empty_file(self, tmp_path):
        (tmp_path / "data-location.txt").write_text("", encoding="utf-8")
        assert read_data_root(tmp_path) is None

    def test_returns_none_for_missing_config_dir(self, tmp_path):
        assert read_data_root(tmp_path / "nincs-ilyen") is None


class TestWriteDataRoot:
    def test_write_then_read_roundtrips(self, tmp_path):
        config_dir = tmp_path / "config"
        new_root = tmp_path / "uj-adathely"

        write_data_root(config_dir, new_root)

        assert read_data_root(config_dir) == new_root

    def test_creates_config_dir_if_missing(self, tmp_path):
        config_dir = tmp_path / "nincs-meg" / "config"
        write_data_root(config_dir, tmp_path / "adat")
        assert config_dir.exists()

    def test_overwrites_previous_value(self, tmp_path):
        config_dir = tmp_path / "config"
        write_data_root(config_dir, tmp_path / "elso")
        write_data_root(config_dir, tmp_path / "masodik")
        assert read_data_root(config_dir) == tmp_path / "masodik"


class TestClearDataRoot:
    def test_removes_override_file(self, tmp_path):
        config_dir = tmp_path / "config"
        write_data_root(config_dir, tmp_path / "adat")
        clear_data_root(config_dir)
        assert read_data_root(config_dir) is None

    def test_tolerates_missing_file(self, tmp_path):
        clear_data_root(tmp_path / "config")  # nincs kivétel
