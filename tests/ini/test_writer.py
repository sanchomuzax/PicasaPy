"""Fájl-I/O: betöltés, atomikus mentés, backup — írási szabályok a specből."""

import stat

import pytest

from picasapy.ini import load_document, save_document

CRLF_BYTES = b"[IMG_0001.jpg]\r\nstar=yes\r\nfilters=sat=1,-1.000000;\r\n"
BOM = b"\xef\xbb\xbf"


class TestLoadSave:
    def test_disk_roundtrip_byte_exact(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(CRLF_BYTES)
        save_document(load_document(path), path)
        assert path.read_bytes() == CRLF_BYTES

    def test_bom_preserved(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(BOM + CRLF_BYTES)
        save_document(load_document(path), path)
        assert path.read_bytes() == BOM + CRLF_BYTES

    def test_load_parses_sections(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(CRLF_BYTES)
        doc = load_document(path)
        assert doc.section("IMG_0001.jpg").get("star") == "yes"

    def test_save_new_file(self, tmp_path):
        src = tmp_path / ".picasa.ini"
        src.write_bytes(CRLF_BYTES)
        dst = tmp_path / "uj" / ".picasa.ini"
        dst.parent.mkdir()
        save_document(load_document(src), dst)
        assert dst.read_bytes() == CRLF_BYTES


class TestAtomicity:
    def test_no_temp_files_left_behind(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(CRLF_BYTES)
        save_document(load_document(path), path)
        leftovers = [p.name for p in tmp_path.iterdir() if p.name != ".picasa.ini"]
        assert leftovers == []


class TestPermissions:
    def test_save_preserves_existing_file_mode(self, tmp_path):
        # NAS-on más folyamatok (az eredeti Picasa is) olvassák: a mentés
        # nem szűkítheti a jogokat a mkstemp-féle 0600-ra.
        path = tmp_path / ".picasa.ini"
        path.write_bytes(CRLF_BYTES)
        path.chmod(0o644)
        save_document(load_document(path), path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o644


class TestBackup:
    def test_backup_holds_previous_bytes(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(CRLF_BYTES)
        doc = load_document(path).with_value("IMG_0001.jpg", "star", "no")
        save_document(doc, path, backup=True)
        assert (tmp_path / ".picasa.ini.bak").read_bytes() == CRLF_BYTES
        assert b"star=no" in path.read_bytes()

    def test_no_backup_by_default(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(CRLF_BYTES)
        save_document(load_document(path), path)
        assert not (tmp_path / ".picasa.ini.bak").exists()

    def test_backup_skipped_for_new_file(self, tmp_path):
        src = tmp_path / ".picasa.ini"
        src.write_bytes(CRLF_BYTES)
        dst = tmp_path / "uj.ini"
        save_document(load_document(src), dst, backup=True)
        assert not (tmp_path / "uj.ini.bak").exists()


class TestEncodings:
    def test_non_utf8_legacy_file_roundtrip(self, tmp_path):
        # Régi, cp1252-vel írt fájl (é = 0xe9): a latin-1 fallback byte-őrző.
        legacy = b"[K\xe9pek.jpg]\r\ncaption=nyaral\xe1s\r\n"
        path = tmp_path / ".picasa.ini"
        path.write_bytes(legacy)
        save_document(load_document(path), path)
        assert path.read_bytes() == legacy


class TestErrorHandling:
    def test_failed_replace_cleans_up_temp_file(self, tmp_path):
        src = tmp_path / ".picasa.ini"
        src.write_bytes(CRLF_BYTES)
        target_dir = tmp_path / "mappa"
        target_dir.mkdir()
        # A cél egy létező, nem üres könyvtár: az os.replace hibázik.
        (target_dir / "x").mkdir()
        with pytest.raises(OSError):
            save_document(load_document(src), target_dir)
        leftovers = [p.name for p in tmp_path.iterdir() if p.name != ".picasa.ini"]
        assert leftovers == ["mappa"]
        assert [p.name for p in target_dir.iterdir()] == ["x"]
