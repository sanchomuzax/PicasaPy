"""A cache-elt bélyegképet bájtként olvassa be a provider (#5542)."""

from picasapy.app import thumbnail_provider as provider_module
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def test_cache_thumbnail_load_does_not_depend_on_qt_path_open(
    qt_app, tmp_path, monkeypatch
):
    library = tmp_path / "library"
    library.mkdir()
    make_jpeg(library / "photo.jpg", size=(320, 240))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library)

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=64))
    provider.register_photos(photos)

    real_qimage = provider_module.QImage

    class PathOpenUnavailable:
        """A Windows-style Qt path-open failure; in-memory decoding works."""

        Format = real_qimage.Format

        def __new__(cls, *args, **kwargs):
            if len(args) == 1 and isinstance(args[0], str):
                return real_qimage()
            return real_qimage(*args, **kwargs)

        @staticmethod
        def fromData(data, *args, **kwargs):
            return real_qimage.fromData(data, *args, **kwargs)

    monkeypatch.setattr(provider_module, "QImage", PathOpenUnavailable)

    image = provider.requestImage(str(photos[0].id), None, None)

    assert not image.isNull()
    assert max(image.width(), image.height()) == 64
