"""#59: a rács-bélyegkép a szerkesztett (filters= láncos) képet mutatja."""

from pathlib import Path

from picasapy.edit.session import EditSession
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.ini.rect64 import Rect64
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _library_with_crop(tmp_path):
    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(320, 160))
    value = EditSession().set_crop(
        Rect64(left=0.0, top=0.0, right=0.5, bottom=1.0)
    ).to_value()
    (lib / ".picasa.ini").write_text(
        f"[a.jpg]\nfilters={value}\n", encoding="utf-8"
    )
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        return photos_in_folder(conn, lib)


class TestThumbnailAppliesFilters:
    def test_cropped_thumb_has_cropped_aspect(self, qt_app, tmp_path):
        from picasapy.app.thumbnail_provider import ThumbnailProvider

        records = _library_with_crop(tmp_path)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=64))
        provider.register_photos(records)
        image = provider.requestImage(str(records[0].id), None, None)
        # bal felét vágtuk: az arány 2:1-ről ~1:1-re változik
        assert abs(image.width() / image.height() - 1.0) < 0.1


class TestThumbUrlCacheBuster:
    def test_url_changes_with_filters(self, qt_app, tmp_path):
        from picasapy.app.models import PhotoGridModel

        records = _library_with_crop(tmp_path)
        model = PhotoGridModel()
        model.set_photos(records)
        url_a = model.thumbUrlAt(0)
        assert "&f=" in url_a
        plain = records[0].__class__(**{**records[0].__dict__, "filters": None})
        model.set_photos((plain,))
        assert model.thumbUrlAt(0) != url_a
