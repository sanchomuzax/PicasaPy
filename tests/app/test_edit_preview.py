"""EditPreviewProvider: image://editpreview/<id> élő szerkesztési előnézet."""

from PySide6.QtCore import QSize

from support.jpeg_factory import make_jpeg


def _make_provider():
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


class TestRegisterUnregister:
    def test_unknown_id_gives_placeholder(self, qt_app):
        provider = _make_provider()
        image = provider.requestImage("nincs-ilyen", None, None)
        assert not image.isNull()
        assert image.width() == 16

    def test_registered_photo_renders_without_ops(self, qt_app, tmp_path):
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        provider.register("1", photo, ())
        image = provider.requestImage("1", None, None)
        assert not image.isNull()
        assert (image.width(), image.height()) == (8, 6)

    def test_unregister_falls_back_to_placeholder(self, qt_app, tmp_path):
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        provider.register("1", photo, ())
        provider.unregister("1")
        image = provider.requestImage("1", None, None)
        assert image.width() == 16

    def test_rev_query_ignored_for_lookup(self, qt_app, tmp_path):
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        provider.register("1", photo, ())
        image = provider.requestImage("1?rev=7", None, None)
        assert (image.width(), image.height()) == (8, 6)

    def test_unreadable_path_gives_placeholder(self, qt_app, tmp_path):
        provider = _make_provider()
        provider.register("1", tmp_path / "nincs.jpg", ())
        image = provider.requestImage("1", None, None)
        assert image.width() == 16


class TestFilterApplication:
    def test_crop_reduces_dimensions(self, qt_app, tmp_path):
        from picasapy.ini.filters import FilterOp
        from picasapy.ini.rect64 import Rect64, encode_rect64

        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        rect = Rect64(left=0.0, top=0.0, right=0.5, bottom=0.5)
        op = FilterOp("crop64", ("1", encode_rect64(rect)))
        provider.register("1", photo, (op,))
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (4, 3)

    def test_unsupported_op_skipped_silently(self, qt_app, tmp_path):
        from picasapy.ini.filters import FilterOp

        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        op = FilterOp("vignette", ("1",))
        provider.register("1", photo, (op,))
        image = provider.requestImage("1", None, None)
        assert not image.isNull()
        assert (image.width(), image.height()) == (8, 6)


class TestRequestedSize:
    def test_scales_to_requested_size(self, qt_app, tmp_path):
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(80, 60))
        provider.register("1", photo, ())
        image = provider.requestImage("1", None, QSize(40, 30))
        assert max(image.width(), image.height()) <= 40


class TestRequestedSizeHalfDimension:
    """#48: a néző sourceSize.width-del (magasság nélkül) kér — a (w, 0)
    kérés nem adhat üres képet (ettől maradt szürke a néző)."""

    def _provider_with_photo(self, tmp_path):
        from picasapy.app.edit_preview import EditPreviewProvider

        make_jpeg(tmp_path / "p.jpg", size=(320, 160))
        provider = EditPreviewProvider()
        provider.register("7", tmp_path / "p.jpg", ())
        return provider

    def test_width_only_request_keeps_aspect(self, qt_app, tmp_path):
        from PySide6.QtCore import QSize

        provider = self._provider_with_photo(tmp_path)
        image = provider.requestImage("7?rev=1", QSize(), QSize(160, 0))
        assert not image.isNull()
        assert (image.width(), image.height()) == (160, 80)

    def test_height_only_request_keeps_aspect(self, qt_app, tmp_path):
        from PySide6.QtCore import QSize

        provider = self._provider_with_photo(tmp_path)
        image = provider.requestImage("7?rev=1", QSize(), QSize(0, 80))
        assert (image.width(), image.height()) == (160, 80)

    def test_full_request_scales_within_box(self, qt_app, tmp_path):
        from PySide6.QtCore import QSize

        provider = self._provider_with_photo(tmp_path)
        image = provider.requestImage("7?rev=1", QSize(), QSize(100, 100))
        assert (image.width(), image.height()) == (100, 50)

    def test_no_request_returns_native_size(self, qt_app, tmp_path):
        from PySide6.QtCore import QSize

        provider = self._provider_with_photo(tmp_path)
        image = provider.requestImage("7?rev=1", QSize(), QSize(-1, -1))
        assert (image.width(), image.height()) == (320, 160)
