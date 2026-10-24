"""#5762: fájlargumentumok külön gyorsnézegető-listába kerülnek."""

from pathlib import Path

from PySide6.QtCore import QUrl

from picasapy.app import application
from picasapy.app.models import PhotoGridModel
from picasapy.app.quick_view import (
    IMAGE_MIME_TYPES_BY_EXTENSION,
    SUPPORTED_IMAGE_MIME_TYPES,
    parse_launch_arguments,
    quick_view_records,
)
from picasapy.index.queries import PhotoRecord
from picasapy.scanner.filetypes import PHOTO_EXTENSIONS


def _record(photo_id: int, folder: str, name: str) -> PhotoRecord:
    return PhotoRecord(
        id=photo_id,
        folder_path=folder,
        name=name,
        kind="photo",
        size=1,
        mtime_ns=1,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=10,
        height=10,
    )


def test_arguments_split_local_images_from_directories_and_file_urls(tmp_path):
    image_one = tmp_path / "family photo.jpg"
    image_two = tmp_path / "second.png"
    image_one.write_bytes(b"not decoded by the argument parser")
    image_two.write_bytes(b"not decoded by the argument parser")
    library = tmp_path / "library"
    library.mkdir()
    ignored = tmp_path / "notes.txt"
    ignored.write_text("not a picture", encoding="utf-8")

    parsed = parse_launch_arguments(
        [
            "picasapy",
            QUrl.fromLocalFile(str(image_one)).toString(),
            str(library),
            str(ignored),
            str(image_two),
        ]
    )

    assert tuple(Path(path) for path in parsed.photo_paths) == (
        image_one.absolute(),
        image_two.absolute(),
    )
    assert tuple(Path(path) for path in parsed.directory_roots) == (
        library.absolute(),
    )


def test_directory_only_arguments_do_not_turn_into_photo_paths(tmp_path):
    first = tmp_path / "album one"
    second = tmp_path / "album two"
    first.mkdir()
    second.mkdir()

    parsed = parse_launch_arguments(["picasapy", str(first), str(second)])

    assert parsed.photo_paths == ()
    assert tuple(Path(path) for path in parsed.directory_roots) == (
        first.absolute(),
        second.absolute(),
    )


def test_quick_view_records_are_limited_to_explicit_files(tmp_path):
    first = tmp_path / "one.jpg"
    second_dir = tmp_path / "other"
    second_dir.mkdir()
    second = second_dir / "two.png"
    first.write_bytes(b"a")
    second.write_bytes(b"b")

    records = quick_view_records((str(first), str(second)))

    assert tuple(Path(record.folder_path) / record.name for record in records) == (
        first,
        second,
    )
    assert len({record.id for record in records}) == 2
    assert all(record.id < -1_000_000 for record in records)
    assert all(record.kind == "photo" for record in records)


def test_quick_view_navigation_crosses_input_folder_boundaries():
    model = PhotoGridModel()
    model.set_linear_navigation(True)
    model.set_photos(
        (
            _record(-2_000_001, "/one", "a.jpg"),
            _record(-2_000_002, "/two", "b.jpg"),
            _record(-2_000_003, "/one", "c.jpg"),
        )
    )

    assert model.folderNeighbor(0, 1) == 1
    assert model.folderNeighbor(1, -1) == 0
    assert model.folderNeighbor(2, 1) == 2
    assert model.folderRowRange(1) == [0, 3]


def test_desktop_mime_types_cover_every_scanner_photo_extension():
    assert set(IMAGE_MIME_TYPES_BY_EXTENSION) == set(PHOTO_EXTENSIONS)
    assert all(
        mime.startswith("image/")
        for mime in IMAGE_MIME_TYPES_BY_EXTENSION.values()
    )
    assert len(set(IMAGE_MIME_TYPES_BY_EXTENSION.values())) < len(PHOTO_EXTENSIONS)

    desktop = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "debian"
        / "picasapy.desktop"
    ).read_text(encoding="utf-8")
    mime_line = next(
        line for line in desktop.splitlines() if line.startswith("MimeType=")
    )
    declared = set(mime_line.removeprefix("MimeType=").rstrip(";").split(";"))
    assert declared == set(IMAGE_MIME_TYPES_BY_EXTENSION.values())


def test_runtime_installed_desktop_entry_keeps_image_mime_types(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(application, "_refresh_icon_cache", lambda *_: None)

    application._install_desktop_entry()

    desktop = (tmp_path / "applications" / "picasapy.desktop").read_text(
        encoding="utf-8"
    )
    mime_line = next(
        line for line in desktop.splitlines() if line.startswith("MimeType=")
    )
    declared = tuple(
        mime_line.removeprefix("MimeType=").rstrip(";").split(";")
    )
    assert declared == SUPPORTED_IMAGE_MIME_TYPES
