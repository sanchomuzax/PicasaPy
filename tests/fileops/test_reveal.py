"""reveal_in_file_manager: a szülőmappa megnyitása xdg-open-nel (#15, #112).

A #112 javítás előtt a hibák (hiányzó `xdg-open` bináris, nemnulla exit
kód) néma naplózásban vesztek el — a felhasználó semmilyen visszajelzést
nem kapott. Mostantól `OSError`-t emel, hogy a hívó (`FileOpsController`)
az `operationFailed` jelzésre tudja fordítani, ahogy a többi fájlműveletnél
(rename/move/delete) is teszi."""

import pytest

from picasapy.fileops import reveal_in_file_manager


class TestRevealInFileManager:
    def test_opens_parent_folder(self, tmp_path, monkeypatch):
        calls = []

        class _CompletedProcess:
            returncode = 0

        monkeypatch.setattr(
            "picasapy.fileops.reveal.subprocess.run",
            lambda args, **kwargs: calls.append(args) or _CompletedProcess(),
        )
        photo = tmp_path / "album" / "a.jpg"
        photo.parent.mkdir()
        reveal_in_file_manager(photo)
        assert calls == [["xdg-open", str(photo.parent)]]

    def test_missing_xdg_open_raises(self, tmp_path, monkeypatch):
        def _raise(*_args, **_kwargs):
            raise FileNotFoundError("xdg-open nincs telepítve")

        monkeypatch.setattr("picasapy.fileops.reveal.subprocess.run", _raise)
        with pytest.raises(OSError):
            reveal_in_file_manager(tmp_path / "a.jpg")

    def test_nonzero_exit_code_raises(self, tmp_path, monkeypatch):
        class _CompletedProcess:
            returncode = 1

        monkeypatch.setattr(
            "picasapy.fileops.reveal.subprocess.run",
            lambda args, **kwargs: _CompletedProcess(),
        )
        with pytest.raises(OSError):
            reveal_in_file_manager(tmp_path / "a.jpg")
