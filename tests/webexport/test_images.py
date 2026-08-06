"""Bélyegkép/nagyméretű kép generálás a webexporthoz (#351) — a meglévő
`picasapy.export.exporter` infrastruktúrára építve."""

from picasapy.index import PhotoRecord
from picasapy.webexport.context import WebExportSettings
from picasapy.webexport.images import prepare_photo_exports
from support.jpeg_factory import make_jpeg


def _record(folder, name, **overrides):
    path = folder / name
    if not path.exists():
        make_jpeg(path, size=(80, 60))
    defaults = dict(
        id=1,
        folder_path=str(folder),
        name=name,
        kind="photo",
        size=path.stat().st_size,
        mtime_ns=0,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=80,
        height=60,
    )
    defaults.update(overrides)
    return PhotoRecord(**defaults)


class TestPreparePhotoExports:
    def test_generates_thumbnail_and_image_copies(self, tmp_path):
        library = tmp_path / "kepek"
        library.mkdir()
        record = _record(library, "a.jpg", caption="Kutya")
        target = tmp_path / "export"
        report = prepare_photo_exports((record,), target, WebExportSettings())
        assert len(report.photos) == 1
        photo = report.photos[0]
        assert photo.name == "a.jpg"
        assert photo.caption == "Kutya"
        assert (target / photo.thumbnail_rel_path).is_file()
        assert (target / photo.large_rel_path).is_file()
        assert photo.thumbnail_width > 0 and photo.thumbnail_height > 0

    def test_resizes_to_requested_max_dimension(self, tmp_path):
        library = tmp_path / "kepek"
        library.mkdir()
        record = _record(library, "a.jpg", width=800, height=600)
        make_jpeg(library / "a.jpg", size=(800, 600))
        target = tmp_path / "export"
        settings = WebExportSettings(thumbnail_max_dimension=100, image_max_dimension=400)
        report = prepare_photo_exports((record,), target, settings)
        photo = report.photos[0]
        assert max(photo.thumbnail_width, photo.thumbnail_height) <= 100
        assert max(photo.large_width, photo.large_height) <= 400

    def test_skips_video_records(self, tmp_path):
        library = tmp_path / "kepek"
        library.mkdir()
        video_path = library / "v.mp4"
        video_path.write_bytes(b"nem-igazi-video")
        record = _record(library, "v.mp4", kind="video")
        target = tmp_path / "export"
        report = prepare_photo_exports((record,), target, WebExportSettings())
        assert report.photos == ()
        assert len(report.skipped) == 1
        assert "videó" in report.skipped[0]

    def test_skips_undecodable_source_with_reason(self, tmp_path):
        library = tmp_path / "kepek"
        library.mkdir()
        broken = library / "torott.jpg"
        broken.write_bytes(b"nem valodi jpeg tartalom")
        record = _record(library, "torott.jpg")
        target = tmp_path / "export"
        report = prepare_photo_exports((record,), target, WebExportSettings())
        assert report.photos == ()
        assert len(report.skipped) == 1
        assert "torott.jpg" in report.skipped[0]

    def test_two_photos_do_not_collide_on_disk(self, tmp_path):
        library = tmp_path / "kepek"
        library.mkdir()
        r1 = _record(library, "a.jpg")
        r2 = _record(library, "b.jpg")
        target = tmp_path / "export"
        report = prepare_photo_exports((r1, r2), target, WebExportSettings())
        assert len(report.photos) == 2
        assert report.photos[0].thumbnail_rel_path != report.photos[1].thumbnail_rel_path
