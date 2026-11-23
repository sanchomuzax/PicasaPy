"""A retusált kép mentése után a fő ini-ben megmaradó filters=retouch=1; tesztjei (#7379)."""

from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np
import pytest

from picasapy.edit import EditSession, ORIGINALS_DIR_NAME, save_edited
from picasapy.ini import load_document


def _solid_image(color: tuple[int, int, int], size: tuple[int, int] = (64, 64)) -> np.ndarray:
    return np.full((size[1], size[0], 3), color, dtype=np.uint8)


def _encode_jpg(image: np.ndarray) -> bytes:
    success, buffer = cv2.imencode(".jpg", image)
    assert success
    return buffer.tobytes()


@pytest.fixture
def photo_with_ini(tmp_path: Path) -> tuple[Path, bytes]:
    image_path = tmp_path / "gray_ramp.jpg"
    original_bytes = _encode_jpg(_solid_image((128, 128, 128)))
    image_path.write_bytes(original_bytes)
    ini_path = tmp_path / ".picasa.ini"
    ini_path.write_text(
        "[gray_ramp.jpg]\n"
        "filters=retouch=1;\n"
        "backuphash=24536\n",
        encoding="utf-8",
    )
    return image_path, original_bytes


def test_save_edited_retouch_retains_filters_in_main_ini(photo_with_ini: tuple[Path, bytes]) -> None:
    """#7379: retusálás mentése után a fő ini-ben megmarad a filters=retouch=1;."""
    image_path, original_bytes = photo_with_ini
    rendered = _solid_image((130, 130, 130))
    session = EditSession.from_value("retouch=1;")

    save_edited(image_path, rendered, session)

    main_doc = load_document(image_path.parent / ".picasa.ini")
    main_sec = main_doc.section("gray_ramp.jpg")
    assert main_sec is not None
    assert main_sec.get("filters") == "retouch=1;"
    assert main_sec.get("backuphash") is not None
    assert main_sec.get("redo") is None

    backup_path = image_path.parent / ORIGINALS_DIR_NAME / "gray_ramp.jpg"
    assert backup_path.exists()
    assert backup_path.read_bytes() == original_bytes

    orig_doc = load_document(image_path.parent / ORIGINALS_DIR_NAME / ".picasa.ini")
    orig_sec = orig_doc.section("gray_ramp.jpg")
    assert orig_sec is not None
    assert orig_sec.get("filters") == "retouch=1;"
    assert orig_sec.get("moddate") is not None


def test_save_edited_retouch_strips_other_filters_from_main_ini(photo_with_ini: tuple[Path, bytes]) -> None:
    """#7379: retusálás és egyéb filter mentésekor csak a retouch=1; marad a fő iniben."""
    image_path, _ = photo_with_ini
    rendered = _solid_image((130, 130, 130))
    session = EditSession.from_value("enhance=1;retouch=1;")

    save_edited(image_path, rendered, session)

    main_doc = load_document(image_path.parent / ".picasa.ini")
    main_sec = main_doc.section("gray_ramp.jpg")
    assert main_sec is not None
    assert main_sec.get("filters") == "retouch=1;"
    assert main_sec.get("backuphash") is not None


def test_save_edited_non_retouch_removes_filters_from_main_ini(photo_with_ini: tuple[Path, bytes]) -> None:
    """#7379: retusálás nélküli mentés esetén a fő iniből törlődik a filters= kulcs."""
    image_path, _ = photo_with_ini
    rendered = _solid_image((130, 130, 130))
    session = EditSession.from_value("enhance=1;")

    save_edited(image_path, rendered, session)

    main_doc = load_document(image_path.parent / ".picasa.ini")
    main_sec = main_doc.section("gray_ramp.jpg")
    assert main_sec is not None
    assert main_sec.get("filters") is None
