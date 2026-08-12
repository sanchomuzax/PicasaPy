"""Hibanapló — #449: „megnyitható napló, ne néma összeomlás".

Az eredeti indulási adatbázis-hiba esetén felajánlotta a hibanapló
megtekintését (`PicasaApp::DBError`). Ez a fájl-oldal tesztje.
"""

import logging

from picasapy.app.error_log import (
    ERROR_LOG_NAME,
    error_log_path,
    install_error_log,
    rotate_if_large,
)


def _detach(path):
    """A teszt által felrakott kezelő leszedése — különben a következő
    teszt is ebbe a fájlba írna."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == str(
            path
        ):
            root.removeHandler(handler)
            handler.close()


class TestInstall:
    def test_a_warning_reaches_the_file(self, tmp_path):
        path = install_error_log(tmp_path)
        try:
            logging.getLogger("picasapy.teszt").warning("valami elromlott")
        finally:
            _detach(path)

        assert path == error_log_path(tmp_path)
        assert "valami elromlott" in path.read_text(encoding="utf-8")

    def test_an_info_message_is_not_noise_in_the_log(self, tmp_path):
        path = install_error_log(tmp_path)
        try:
            logging.getLogger("picasapy.teszt").info("csak tájékoztatás")
            logging.getLogger("picasapy.teszt").error("ez viszont hiba")
        finally:
            _detach(path)

        text = path.read_text(encoding="utf-8")
        assert "csak tájékoztatás" not in text
        assert "ez viszont hiba" in text

    def test_the_name_follows_the_original(self, tmp_path):
        assert error_log_path(tmp_path).name == ERROR_LOG_NAME

    def test_an_unwritable_directory_is_survivable(self, tmp_path):
        # a napló hiánya SOSEM akaszthatja meg a programot
        blocked = tmp_path / "fajl.txt"
        blocked.write_text("nem mappa", encoding="utf-8")

        assert install_error_log(blocked) is None


class TestRotation:
    def test_a_large_log_is_rotated_once(self, tmp_path):
        path = error_log_path(tmp_path)
        path.write_text("x" * 100, encoding="utf-8")

        rotate_if_large(path, max_bytes=10)

        assert not path.exists()
        assert path.with_suffix(path.suffix + ".1").read_text(
            encoding="utf-8"
        ) == "x" * 100

    def test_a_small_log_is_left_alone(self, tmp_path):
        path = error_log_path(tmp_path)
        path.write_text("rovid", encoding="utf-8")

        rotate_if_large(path, max_bytes=1024)

        assert path.read_text(encoding="utf-8") == "rovid"

    def test_only_two_generations_are_kept(self, tmp_path):
        path = error_log_path(tmp_path)
        backup = path.with_suffix(path.suffix + ".1")
        backup.write_text("regi", encoding="utf-8")
        path.write_text("x" * 100, encoding="utf-8")

        rotate_if_large(path, max_bytes=10)

        assert backup.read_text(encoding="utf-8") == "x" * 100
        assert not path.exists()

    def test_a_missing_log_is_not_an_error(self, tmp_path):
        rotate_if_large(error_log_path(tmp_path))
