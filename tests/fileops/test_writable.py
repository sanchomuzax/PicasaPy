"""is_folder_writable (#459, jegy 1. pontja: csak-olvasható mappa
felismerése szerkesztés-mentés előtt). POSIX-only: a chmod-alapú
csak-olvashatóvá tétel Windowson nem megbízható (CLAUDE.md (h) szabály)."""

import os
import sys

import pytest

from picasapy.fileops import is_folder_writable

pytestmark = pytest.mark.skipif(
    sys.platform.startswith("win")
    or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="chmod-alapú read-only szimuláció POSIX-only, és root megkerüli a jogokat",
)


class TestIsFolderWritable:
    def test_true_for_normal_writable_folder(self, tmp_path):
        assert is_folder_writable(tmp_path) is True

    def test_false_for_missing_folder(self, tmp_path):
        assert is_folder_writable(tmp_path / "nincs-ilyen") is False

    def test_false_for_read_only_folder(self, tmp_path):
        folder = tmp_path / "readonly"
        folder.mkdir()
        os.chmod(folder, 0o500)
        try:
            assert is_folder_writable(folder) is False
        finally:
            os.chmod(folder, 0o700)  # takarítás, hogy tmp_path törölhető maradjon
