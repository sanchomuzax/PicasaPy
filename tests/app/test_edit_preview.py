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

    def test_broken_op_falls_back_to_unfiltered(self, qt_app, tmp_path):
        """#73: hibás lánc-bejegyzésnél (pl. Picasa-írta, számunkra hiányos
        crop64) a szűretlen kép jön, nem placeholder."""
        from picasapy.ini.filters import FilterOp

        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        op = FilterOp("crop64", ("1",))  # hiányzó rect64 param
        provider.register("1", photo, (op,))
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (8, 6)

    def test_picasa_zero_scale_tilt_renders(self, qt_app, tmp_path):
        """#73: Picasa-írta tilt=1,<szög>,0.000000 nem eshet placeholderre."""
        from picasapy.ini.filters import FilterOp

        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        op = FilterOp("tilt", ("1", "-0.153061", "0.000000"))
        provider.register("1", photo, (op,))
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (8, 6)


class TestSourceCaching:
    """#72: élő csúszka-húzásnál (tilt) a register() gyakran hívódik ugyanarra
    a fotóra, csak a szűrő-lánc változik — a lemezes dekódot nem szabad
    minden hívásnál megismételni."""

    def test_repeated_register_decodes_source_once(self, qt_app, tmp_path, monkeypatch):
        from picasapy.app import edit_preview
        from picasapy.ini.filters import FilterOp

        calls = []
        original = edit_preview._decode_source

        def counting_decode(path):
            calls.append(path)
            return original(path)

        monkeypatch.setattr(edit_preview, "_decode_source", counting_decode)
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        op = FilterOp("tilt", ("1", "0.100000", "0.000000"))
        provider.register("1", photo, (op,))
        provider.register("1", photo, ())
        provider.register("1", photo, (op,))
        assert len(calls) == 1

    def test_different_photo_id_decodes_again(self, qt_app, tmp_path, monkeypatch):
        from picasapy.app import edit_preview

        calls = []
        original = edit_preview._decode_source

        def counting_decode(path):
            calls.append(path)
            return original(path)

        monkeypatch.setattr(edit_preview, "_decode_source", counting_decode)
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        provider.register("1", photo, ())
        provider.register("2", photo, ())
        assert len(calls) == 2

    def test_unregister_clears_source_cache(self, qt_app, tmp_path, monkeypatch):
        from picasapy.app import edit_preview

        calls = []
        original = edit_preview._decode_source

        def counting_decode(path):
            calls.append(path)
            return original(path)

        monkeypatch.setattr(edit_preview, "_decode_source", counting_decode)
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        provider.register("1", photo, ())
        provider.unregister("1")
        provider.register("1", photo, ())
        assert len(calls) == 2


class TestPrefixCache:
    """#140: élő csúszka-húzásnál (ugyanaz a lánc, csak az UTOLSÓ op
    paramétere változik) a prefix (az utolsó op előtti köztes eredmény)
    cache-elődik — interakció közben csak az utolsó op fut újra."""

    @staticmethod
    def _counting_apply_filters(monkeypatch):
        from picasapy.app import edit_preview

        calls: list[tuple] = []
        original = edit_preview.apply_filters

        def counting(image, ops):
            calls.append(tuple(ops))
            return original(image, ops)

        monkeypatch.setattr(edit_preview, "apply_filters", counting)
        return calls

    @staticmethod
    def _ops(tilt_param: str = "0.100000"):
        from picasapy.ini.filters import FilterOp

        fill = FilterOp("fill", ("1", "0.500000"))
        tilt = FilterOp("tilt", ("1", tilt_param, "0.000000"))
        return fill, tilt

    def test_interaction_reruns_only_last_op(self, qt_app, tmp_path, monkeypatch):
        calls = self._counting_apply_filters(monkeypatch)
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        fill, tilt = self._ops("0.100000")
        provider.register("1", photo, (fill, tilt))
        calls.clear()
        _, tilt2 = self._ops("0.200000")
        provider.register("1", photo, (fill, tilt2))
        # csak az utolsó (megváltozott) op fut újra, a fill-prefix nem
        assert calls == [(tilt2,)]

    def test_single_op_interaction_runs_one_op_per_register(
        self, qt_app, tmp_path, monkeypatch
    ):
        calls = self._counting_apply_filters(monkeypatch)
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        _, tilt = self._ops("0.100000")
        provider.register("1", photo, (tilt,))
        _, tilt2 = self._ops("0.200000")
        provider.register("1", photo, (tilt2,))
        # üres prefixhez nem kell apply_filters-hívás
        assert calls == [(tilt,), (tilt2,)]

    def test_prefix_change_recomputes(self, qt_app, tmp_path, monkeypatch):
        from picasapy.ini.filters import FilterOp

        calls = self._counting_apply_filters(monkeypatch)
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        fill, tilt = self._ops()
        provider.register("1", photo, (fill, tilt))
        calls.clear()
        sat = FilterOp("sat", ("1", "0.250000"))
        provider.register("1", photo, (sat, tilt))
        # más prefix → a prefix újraszámolódik, majd az utolsó op fut
        assert calls == [(sat,), (tilt,)]

    def test_cached_render_matches_uncached(self, qt_app, tmp_path):
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        fill, _ = self._ops()
        _, tilt2 = self._ops("0.200000")
        provider.register("1", photo, (fill, tilt2))
        cold = provider.requestImage("1", None, None)
        fill2, tilt1 = self._ops("0.100000")
        provider.register("1", photo, (fill2, tilt1))
        provider.register("1", photo, (fill2, tilt2))  # cache-találat
        warm = provider.requestImage("1", None, None)
        assert warm == cold

    def test_unregister_clears_prefix_cache(self, qt_app, tmp_path, monkeypatch):
        calls = self._counting_apply_filters(monkeypatch)
        provider = _make_provider()
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        fill, tilt = self._ops()
        provider.register("1", photo, (fill, tilt))
        provider.unregister("1")
        calls.clear()
        provider.register("1", photo, (fill, tilt))
        # leregisztrálás után nincs cache-találat: prefix + utolsó op fut
        assert calls == [(fill,), (tilt,)]


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


class TestMainThreadPreRender:
    """#54: a renderelés a register() hívásakor, a hívó (GUI) szálán fut —
    a provider-szálon nincs érdemi Python-munka (GIL-deadlock ellen)."""

    def test_render_happens_at_register_not_request(self, qt_app, tmp_path):
        from picasapy.app.edit_preview import EditPreviewProvider

        make_jpeg(tmp_path / "p.jpg", size=(320, 160))
        provider = EditPreviewProvider()
        provider.register("9", tmp_path / "p.jpg", ())
        (tmp_path / "p.jpg").unlink()  # a kérés idején a fájl már nincs meg
        image = provider.requestImage("9?rev=1", None, None)
        assert (image.width(), image.height()) == (320, 160)

    def test_decode_capped_for_preview(self, qt_app, tmp_path):
        from picasapy.app.edit_preview import EditPreviewProvider

        make_jpeg(tmp_path / "nagy.jpg", size=(4000, 2000))
        provider = EditPreviewProvider()
        provider.register("9", tmp_path / "nagy.jpg", ())
        image = provider.requestImage("9?rev=1", None, None)
        assert max(image.width(), image.height()) <= 2560
        assert abs(image.width() / image.height() - 2.0) < 0.01
