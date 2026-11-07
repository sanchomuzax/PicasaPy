"""Átmeneti zárolás után a kötegelt mozgatás próbálkozzon újra (#6658)."""

from pathlib import Path

from picasapy.fileops import batch


def test_move_photos_retries_a_transient_permission_error(tmp_path, monkeypatch):
    source = tmp_path / "forras"
    destination = tmp_path / "cel"
    source.mkdir()
    destination.mkdir()
    photo = source / "locked.jpg"
    photo.write_bytes(b"kep")
    attempts = []

    def move_once_locked(path: Path, folder: Path) -> Path:
        attempts.append(path)
        if len(attempts) == 1:
            raise PermissionError("a fájl átmenetileg zárolt")
        target = folder / path.name
        path.rename(target)
        return target

    monkeypatch.setattr(batch, "_move_with_rename", move_once_locked)

    result = batch.move_photos([photo], destination)

    assert len(attempts) == 2, "a zárolt fájl újrapróbálása elmaradt"
    assert result.done == ((photo, destination / photo.name),)
    assert result.failed == ()
    assert not photo.exists()
    assert (destination / photo.name).read_bytes() == b"kep"
