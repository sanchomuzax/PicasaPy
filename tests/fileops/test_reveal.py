"""reveal_in_file_manager: a szülőmappa megnyitása xdg-open-nel (#15)."""

from picasapy.fileops import reveal_in_file_manager


class TestRevealInFileManager:
    def test_opens_parent_folder(self, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(
            "picasapy.fileops.reveal.subprocess.run",
            lambda args, **kwargs: calls.append(args),
        )
        photo = tmp_path / "album" / "a.jpg"
        photo.parent.mkdir()
        reveal_in_file_manager(photo)
        assert calls == [["xdg-open", str(photo.parent)]]

    def test_missing_xdg_open_does_not_raise(self, tmp_path, monkeypatch):
        def _raise(*_args, **_kwargs):
            raise FileNotFoundError("xdg-open nincs telepítve")

        monkeypatch.setattr("picasapy.fileops.reveal.subprocess.run", _raise)
        reveal_in_file_manager(tmp_path / "a.jpg")  # nem emel kivételt
