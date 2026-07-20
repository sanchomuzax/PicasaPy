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


def _library_with_ini(tmp_path, ini_body: str):
    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(320, 160))
    (lib / ".picasa.ini").write_text(ini_body, encoding="utf-8")
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        return photos_in_folder(conn, lib)


class TestPicasaCompatRendering:
    """#73: a Windows-os Picasa által írt lánc nem eshet placeholderre."""

    def test_picasa_tilt_with_zero_scale_renders(self, qt_app, tmp_path):
        from picasapy.app.thumbnail_provider import ThumbnailProvider

        records = _library_with_ini(
            tmp_path, "[a.jpg]\nfilters=tilt=1,-0.153061,0.000000;\n"
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=64))
        provider.register_photos(records)
        image = provider.requestImage(str(records[0].id), None, None)
        # nem a 16x16 placeholder: az eredeti 2:1 arányú thumb jön vissza
        assert abs(image.width() / image.height() - 2.0) < 0.1

    def test_broken_filter_falls_back_to_unfiltered(self, qt_app, tmp_path):
        from picasapy.app.thumbnail_provider import ThumbnailProvider

        records = _library_with_ini(
            tmp_path, "[a.jpg]\nfilters=crop64=1;\n"  # hiányzó rect64 param
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=64))
        provider.register_photos(records)
        image = provider.requestImage(str(records[0].id), None, None)
        assert abs(image.width() / image.height() - 2.0) < 0.1

    def test_unparseable_filters_value_falls_back(self, qt_app, tmp_path):
        from picasapy.app.thumbnail_provider import ThumbnailProvider

        records = _library_with_ini(
            tmp_path, "[a.jpg]\nfilters=;;;csonka\n"
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=64))
        provider.register_photos(records)
        image = provider.requestImage(str(records[0].id), None, None)
        assert abs(image.width() / image.height() - 2.0) < 0.1


class TestLazyFiltersParse:
    """#142: a register_photos NE parse-olja a filters= láncot — 50k
    fotónál a regisztráció minden frissítésnél fut, a parse viszont csak
    a ténylegesen renderelt (látótér-közeli) képekhez kell."""

    def test_register_does_not_parse_render_does(
        self, qt_app, tmp_path, monkeypatch
    ):
        import picasapy.app.thumbnail_provider as tp

        records = _library_with_crop(tmp_path)
        calls = []
        original = tp._parse_ops

        def counting_parse(photo):
            calls.append(photo.name)
            return original(photo)

        monkeypatch.setattr(tp, "_parse_ops", counting_parse)
        provider = tp.ThumbnailProvider(
            ThumbnailCache(tmp_path / "th", size=64)
        )
        provider.register_photos(records)
        assert calls == [], "a register_photos nem parse-olhat filters-t"
        image = provider.requestImage(str(records[0].id), None, None)
        assert calls, "render-kor viszont kell a parse"
        # a szerkesztés (bal fél levágva) érvényesül: 2:1 → ~1:1
        assert abs(image.width() / image.height() - 1.0) < 0.1

    def test_parse_runs_once_per_unique_chain(
        self, qt_app, tmp_path, monkeypatch
    ):
        import picasapy.app.thumbnail_provider as tp

        records = _library_with_crop(tmp_path)
        calls = []
        original = tp._parse_ops

        def counting_parse(photo):
            calls.append(photo.name)
            return original(photo)

        monkeypatch.setattr(tp, "_parse_ops", counting_parse)
        provider = tp.ThumbnailProvider(
            ThumbnailCache(tmp_path / "th", size=64)
        )
        provider.register_photos(records)
        provider.requestImage(str(records[0].id), None, None)
        provider.requestImage(str(records[0].id), None, None)
        assert len(calls) == 1, "azonos lánc csak egyszer parse-olódik"


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
