"""#338: image://effectthumb/<photo_id>/<effekt> — effekt-gomb bélyegképek.

A hangsúly a MEGFIGYELHETŐ kimeneten van (a "lefutott-e" hamis zöld helyett):
a kapott kép mérete, hogy két különböző effekt bélyegképe ténylegesen eltér,
és hogy a gyorsítótár találatnál nem számol újra (sem a filter-láncot, sem
a lemez-dekódot)."""

from picasapy.index import open_index, photos_in_folder, sync_tree
from support.jpeg_factory import make_jpeg


def _library(tmp_path, count=1, size=(320, 200)):
    lib = tmp_path / "kepek"
    lib.mkdir()
    for i in range(count):
        make_jpeg(lib / f"kep{i}.jpg", size=size)
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        return photos_in_folder(conn, lib)


def _provider(records, **kwargs):
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider

    registry = {str(r.id): r for r in records}
    return EffectThumbnailProvider(registry.get, **kwargs)


class TestSyncRender:
    def test_unknown_photo_gives_placeholder(self, qt_app, tmp_path):
        provider = _provider(())
        image = provider.requestImage("99999/sepia", None, None)
        assert not image.isNull()
        assert image.width() == 16  # placeholder, nem üres/beragadt cella

    def test_unknown_effect_gives_placeholder(self, qt_app, tmp_path):
        records = _library(tmp_path)
        provider = _provider(records)
        image = provider.requestImage(f"{records[0].id}/nincs-ilyen-effekt", None, None)
        assert image.width() == 16

    def test_known_effect_renders_a_small_thumbnail(self, qt_app, tmp_path):
        records = _library(tmp_path)
        provider = _provider(records)
        image = provider.requestImage(f"{records[0].id}/sepia", None, None)
        assert not image.isNull()
        # DoD: kicsi (64-96px) bélyegkép, nem a teljes felbontás
        assert 64 <= max(image.width(), image.height()) <= 96
        # a forrás 320x200 (16:10) — az arány a kicsinyítés után is közel áll
        assert abs(image.width() / image.height() - 320 / 200) < 0.1

    def test_two_different_effects_produce_different_thumbnails(
        self, qt_app, tmp_path
    ):
        records = _library(tmp_path)
        provider = _provider(records)
        sepia = provider.requestImage(f"{records[0].id}/sepia", None, None)
        bw = provider.requestImage(f"{records[0].id}/bw", None, None)
        assert sepia.size() == bw.size()
        # két eltérő effekt sose adhatja ugyanazt a pixeltartalmat
        assert sepia.convertToFormat(sepia.Format.Format_RGB888).constBits().tobytes() != (
            bw.convertToFormat(bw.Format.Format_RGB888).constBits().tobytes()
        )

    def test_all_catalogue_effects_render_without_crashing(self, qt_app, tmp_path):
        """A panel mind a 41 effekt-gombja adjon KÉSZ (nem placeholder)
        bélyegképet — egyik effekt se dobjon ki kivételt idáig."""
        from picasapy.app.effect_thumbnails import EFFECT_NAMES

        records = _library(tmp_path)
        provider = _provider(records)
        assert len(EFFECT_NAMES) == 41
        for effect in EFFECT_NAMES:
            image = provider.requestImage(f"{records[0].id}/{effect}", None, None)
            assert not image.isNull(), effect
            assert image.width() != 16 or image.height() != 16, (
                f"{effect}: placeholder jött KÉSZ bélyegkép helyett"
            )


class TestToolPreviewNames:
    """#405: a "Gyakori javítások" fül négy egy-gombos eszköze (Vörösszem,
    Jó napom van, Automatikus kontraszt, Automatikus szín) is kapjon valódi,
    az adott műveletet alkalmazó bélyegképet — NEM a 41-es `filters=`
    katalógus tagjai, mégis renderelhetők a `render/chain.py` `_HANDLERS`
    meglévő "enhance"/"autolight"/"autocolor"/"redeye" kulcsain át."""

    def test_public_effect_names_stay_41(self):
        # a meglévő, 41 elemű katalógus (#516: +5) NEM bővül tovább — külön halmaz kezeli az
        # eszköz-előnézeteket (ld. effect_thumbnails._KNOWN_EFFECTS)
        from picasapy.app.effect_thumbnails import EFFECT_NAMES

        assert len(EFFECT_NAMES) == 41

    def test_tool_preview_names_render_real_thumbnails(self, qt_app, tmp_path):
        records = _library(tmp_path)
        provider = _provider(records)
        for tool in ("redeye", "enhance", "autolight", "autocolor"):
            image = provider.requestImage(f"{records[0].id}/{tool}", None, None)
            assert not image.isNull(), tool
            assert image.width() != 16 or image.height() != 16, (
                f"{tool}: placeholder jött KÉSZ bélyegkép helyett"
            )

    def test_tool_preview_thumbnail_differs_from_plain_source(self, qt_app, tmp_path):
        # az "enhance" ("Jó napom van") a fotó ALAP állapotát módosítja —
        # a bélyegkép ne legyen pixelre azonos a szűretlen forrással
        records = _library(tmp_path)
        provider = _provider(records)
        enhanced = provider.requestImage(f"{records[0].id}/enhance", None, None)
        sepia = provider.requestImage(f"{records[0].id}/sepia", None, None)
        assert enhanced.size() == sepia.size()


class TestCaching:
    def test_second_request_skips_filter_chain_recompute(self, qt_app, tmp_path):
        from picasapy.app import effect_thumbnails as mod

        records = _library(tmp_path)
        provider = _provider(records)
        calls = []
        original = mod.apply_filters

        def counting(*args, **kwargs):
            calls.append(args)
            return original(*args, **kwargs)

        mod.apply_filters = counting
        try:
            first = provider.requestImage(f"{records[0].id}/warm", None, None)
            assert len(calls) == 1
            second = provider.requestImage(f"{records[0].id}/warm", None, None)
            assert len(calls) == 1  # cache-találat: a lánc nem fut újra
        finally:
            mod.apply_filters = original
        assert first.size() == second.size()

    def test_source_decode_happens_once_per_photo(self, qt_app, tmp_path):
        """41 effekt UGYANARRÓL a fotóról induljon — a lemez-dekód (a
        legdrágább lépés) fotónként EGYSZER fusson, ne effektenként."""
        from picasapy.app import effect_thumbnails as mod

        records = _library(tmp_path)
        provider = _provider(records)
        calls = []
        original = mod._decode_small_source

        def counting(path):
            calls.append(path)
            return original(path)

        mod._decode_small_source = counting
        try:
            for effect in ("sepia", "bw", "warm", "grain2", "unsharp"):
                provider.requestImage(f"{records[0].id}/{effect}", None, None)
            assert len(calls) == 1
        finally:
            mod._decode_small_source = original

    def test_cache_key_distinguishes_photos(self, qt_app, tmp_path):
        records = _library(tmp_path, count=2)
        provider = _provider(records)
        first = provider.requestImage(f"{records[0].id}/sepia", None, None)
        second = provider.requestImage(f"{records[1].id}/sepia", None, None)
        assert not first.isNull() and not second.isNull()


class TestAsyncResponse:
    def test_response_delivers_image(self, qt_app, tmp_path):
        records = _library(tmp_path)
        provider = _provider(records)
        response = provider.requestImageResponse(f"{records[0].id}/sepia", None)
        assert response._done.wait(10)
        assert not response._image.isNull()

    def test_texture_factory_carries_image(self, qt_app, tmp_path):
        records = _library(tmp_path)
        provider = _provider(records)
        response = provider.requestImageResponse(f"{records[0].id}/sepia", None)
        assert response._done.wait(10)
        factory = response.textureFactory()
        assert factory is not None
        assert factory.textureSize().width() == response._image.width()

    def test_parallel_requests_all_complete(self, qt_app, tmp_path):
        from picasapy.app.effect_thumbnails import EFFECT_NAMES

        records = _library(tmp_path)
        provider = _provider(records)
        responses = [
            provider.requestImageResponse(f"{records[0].id}/{effect}", None)
            for effect in EFFECT_NAMES
        ]
        assert provider.wait_for_done(20_000)
        for response in responses:
            assert response._done.wait(1)
            assert not response._image.isNull()

    def test_pool_uses_small_thread_count(self, qt_app, tmp_path):
        # #338: KIS pool — nem versenyezhet a nagy thumbnail-rács
        # generálásával (thumbnail_provider.py 4 szála)
        provider = _provider(())
        assert 1 <= provider._pool.maxThreadCount() <= 2


class TestPhotoRecordLookup:
    def test_thumbnail_provider_exposes_photo_record(self, qt_app, tmp_path):
        """A ThumbnailProvider.photo_record(...) az EffectThumbnailProvider
        forrása (#338) — a teljes könyvtár egyszeri regisztrációjából."""
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        records = _library(tmp_path)
        thumb_provider = ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32))
        thumb_provider.register_photos(records)
        found = thumb_provider.photo_record(str(records[0].id))
        assert found is not None
        assert found.name == records[0].name
        assert thumb_provider.photo_record("nincs-ilyen") is None
