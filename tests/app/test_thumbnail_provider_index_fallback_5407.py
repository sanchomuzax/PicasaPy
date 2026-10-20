"""A hiányzó album-regisztrációt az indexből oldja fel a provider (#5407)."""

from __future__ import annotations

from pathlib import Path

from picasapy.app.face_scan_controller import _face_tile_payload
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import (
    faces_for_photo,
    open_index,
    photos_in_folder,
    replace_faces,
    sync_tree,
)
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _face() -> FaceDetection:
    return FaceDetection(
        left=50,
        top=40,
        right=270,
        bottom=210,
        score=0.99,
        landmarks=FaceLandmarks(
            right_eye=(110, 90),
            left_eye=(210, 90),
            nose=(160, 125),
            mouth_right=(125, 165),
            mouth_left=(195, 165),
        ),
    )


def test_face_thumbnail_resolves_photo_from_index_outside_open_album(
    qt_app, tmp_path
):
    opened_folder = tmp_path / "library" / "opened"
    other_folder = tmp_path / "library" / "other"
    opened_folder.mkdir(parents=True)
    other_folder.mkdir(parents=True)
    make_jpeg(opened_folder / "open.jpg", size=(320, 240))
    make_jpeg(other_folder / "other.jpg", size=(320, 240))
    db_path = tmp_path / "index.db"

    with open_index(db_path) as conn:
        sync_tree(conn, tmp_path / "library")
        opened_photos = photos_in_folder(conn, opened_folder)
        other_photos = photos_in_folder(conn, other_folder)
        assert len(opened_photos) == len(other_photos) == 1
        replace_faces(conn, other_photos[0].id, [_face()])
        face = faces_for_photo(conn, other_photos[0].id)[0]
        conn.commit()

    provider = ThumbnailProvider(
        ThumbnailCache(tmp_path / "thumbs", size=128), index_path=db_path
    )
    provider.register_photos(opened_photos)
    assert provider.photo_record(str(other_photos[0].id)) is None

    thumb_id = _face_tile_payload(face)["thumbUrl"].split("image://thumbs/", 1)[1]
    response = provider.requestImageResponse(thumb_id, None)
    assert response._done.wait(10), "az indexből kért arc-bélyegkép nem készült el"
    image = response._image

    assert not image.isNull()
    assert image.width() > 16 and image.height() > 16, (
        "a másik mappa fotójára placeholder jött vissza"
    )
    remembered = provider.photo_record(str(other_photos[0].id))
    assert remembered is not None
    assert remembered.id == other_photos[0].id
    assert Path(remembered.folder_path) == other_folder
