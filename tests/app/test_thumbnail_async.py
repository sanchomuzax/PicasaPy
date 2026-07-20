"""#144: aszinkron thumbnail-provider (QThreadPool) + szűrt-thumb memóriacache."""

from picasapy.edit.session import EditSession
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.ini.rect64 import Rect64
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _library(tmp_path, ini_body: str | None = None, count: int = 1):
    lib = tmp_path / "kepek"
    lib.mkdir()
    for i in range(count):
        make_jpeg(lib / f"kep{i}.jpg", size=(320, 160))
    if ini_body is not None:
        (lib / ".picasa.ini").write_text(ini_body, encoding="utf-8")
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        return photos_in_folder(conn, lib)


def _crop_ini(names) -> str:
    value = EditSession().set_crop(
        Rect64(left=0.0, top=0.0, right=0.5, bottom=1.0)
    ).to_value()
    return "".join(f"[{name}]\nfilters={value}\n" for name in names)


def _provider(tmp_path, records, **kwargs):
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    provider = ThumbnailProvider(
        ThumbnailCache(tmp_path / "th", size=64), **kwargs
    )
    provider.register_photos(records)
    return provider


class TestAsyncResponse:
    def test_response_delivers_image(self, qt_app, tmp_path):
        records = _library(tmp_path)
        provider = _provider(tmp_path, records)
        response = provider.requestImageResponse(str(records[0].id), None)
        assert response._done.wait(10)
        image = response._image
        assert not image.isNull()
        assert abs(image.width() / image.height() - 2.0) < 0.1

    def test_texture_factory_carries_image(self, qt_app, tmp_path):
        records = _library(tmp_path)
        provider = _provider(tmp_path, records)
        response = provider.requestImageResponse(str(records[0].id), None)
        assert response._done.wait(10)
        factory = response.textureFactory()
        assert factory is not None
        assert factory.textureSize().width() == response._image.width()

    def test_unknown_id_gives_placeholder(self, qt_app, tmp_path):
        provider = _provider(tmp_path, ())
        response = provider.requestImageResponse("99999", None)
        assert response._done.wait(10)
        assert response._image.width() == 16  # placeholder, nem beragadt cella

    def test_parallel_requests_all_complete(self, qt_app, tmp_path):
        records = _library(tmp_path, count=8)
        provider = _provider(tmp_path, records)
        responses = [
            provider.requestImageResponse(str(r.id), None) for r in records
        ]
        assert provider.wait_for_done(20_000)
        for response in responses:
            assert response._done.wait(1)
            assert not response._image.isNull()

    def test_pool_capped_at_four_threads(self, qt_app, tmp_path):
        provider = _provider(tmp_path, ())
        assert 1 <= provider._pool.maxThreadCount() <= 4

    def test_busy_counter_pairs_emitted(self, qt_app, tmp_path):
        # #70: az aszinkron úton is ki kell mennie az 1 → 0 párnak
        records = _library(tmp_path)
        provider = _provider(tmp_path, records)
        from PySide6.QtCore import Qt

        counts = []
        provider.activeCountChanged.connect(
            counts.append, Qt.ConnectionType.DirectConnection
        )
        response = provider.requestImageResponse(str(records[0].id), None)
        assert response._done.wait(10)
        provider.wait_for_done()
        assert counts[0] == 1 and counts[-1] == 0


class TestFilteredThumbMemo:
    def test_second_request_skips_filter_chain(self, qt_app, tmp_path):
        # DoD: cache-találatnál NEM futhat a filters-lánc — a második kérés
        # a memóriacache-ből jön, a lemez-cache-t sem éri el.
        records = _library(tmp_path, ini_body=_crop_ini(["kep0.jpg"]))
        provider = _provider(tmp_path, records)
        calls = []
        original = ThumbnailCache.get_or_create_edited

        def counting(self, *args, **kwargs):
            calls.append(args)
            return original(self, *args, **kwargs)

        ThumbnailCache.get_or_create_edited = counting
        try:
            first = provider.requestImage(str(records[0].id), None, None)
            assert len(calls) == 1
            second = provider.requestImage(str(records[0].id), None, None)
            assert len(calls) == 1  # memo-találat: se lánc, se lemez-dekód
        finally:
            ThumbnailCache.get_or_create_edited = original
        assert first.size() == second.size()

    def test_unfiltered_thumb_not_memoized(self, qt_app, tmp_path):
        # a memóriacache a SZŰRT thumboké — a nyers út a lemez-cache-ről fut
        records = _library(tmp_path)
        provider = _provider(tmp_path, records)
        provider.requestImage(str(records[0].id), None, None)
        assert len(provider._memo._items) == 0

    def test_memo_key_includes_rotation(self, qt_app, tmp_path):
        records = _library(tmp_path, ini_body=_crop_ini(["kep0.jpg"]))
        provider = _provider(tmp_path, records)
        plain = provider.requestImage(str(records[0].id), None, None)
        rotated_record = records[0].__class__(
            **{**records[0].__dict__, "rotate_steps": 1}
        )
        provider.register_photos((rotated_record,))
        rotated = provider.requestImage(str(records[0].id), None, None)
        # 90°-os forgatás: a memo NEM adhatja vissza a forgatatlan képet
        assert (rotated.width(), rotated.height()) == (
            plain.height(),
            plain.width(),
        )

    def test_memo_key_includes_chain(self, qt_app, tmp_path):
        # eltérő lánc → eltérő kulcs: a crop-os kép után a lánc nélküli
        # változat nem jöhet a memóból
        records = _library(tmp_path, ini_body=_crop_ini(["kep0.jpg"]))
        provider = _provider(tmp_path, records)
        cropped = provider.requestImage(str(records[0].id), None, None)
        assert abs(cropped.width() / cropped.height() - 1.0) < 0.1
        plain_record = records[0].__class__(
            **{**records[0].__dict__, "filters": None}
        )
        provider.register_photos((plain_record,))
        plain = provider.requestImage(str(records[0].id), None, None)
        assert abs(plain.width() / plain.height() - 2.0) < 0.1

    def test_memo_capacity_bounded(self, qt_app, tmp_path):
        from picasapy.app.thumbnail_provider import _FilteredThumbMemo
        from PySide6.QtGui import QImage

        memo = _FilteredThumbMemo(capacity=3)
        for i in range(5):
            memo.put(("k", i), QImage(4, 4, QImage.Format.Format_RGB32))
        assert len(memo._items) == 3
        assert memo.get(("k", 0)) is None  # a legrégebbi kilakoltatva
        assert memo.get(("k", 4)) is not None
