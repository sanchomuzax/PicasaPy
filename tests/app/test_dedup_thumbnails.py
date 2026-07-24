"""#298: a dedup-ablak NEM cserélheti le a bélyegkép-provider
regisztrációját.

A `register_photos` a provider TELJES regisztrációját lecseréli — ha a
dedup eredménye nem esik egybe a fő rács tartalmával, a rács
`image://thumbs/<id>` URL-jei feloldhatatlanná válnak (szürke placeholder).
A helyes út a `register_additional_photos`/`unregister_additional_photos`
páros, saját (negatív) id-tartománnyal — az Import-forrás ág mintájára."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


@pytest.fixture
def provider(tmp_path):
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    return ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))


@pytest.fixture
def library(tmp_path):
    """Fő rács: `kepek/` (egy egyedi kép); dedup-találat: `mas/` egy bitre
    azonos párral — a két halmaz szándékosan DISZJUNKT, pont ez a #298 eset."""
    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "racs.jpg", size=(40, 20))
    other = tmp_path / "mas"
    other.mkdir()
    original = make_jpeg(other / "a.jpg", size=(60, 30))
    (other / "b.jpg").write_bytes(original.read_bytes())
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)
        sync_tree(conn, other)
    return lib, other, db


@pytest.fixture
def dedup(qt_app, library, provider):
    from picasapy.app.dedup_controller import DedupController

    _lib, _other, db = library
    return DedupController(db, provider)


def _register_main_grid(provider, db, folder):
    """A fő rács regisztrációja, ahogy az `AppController._show()` teszi."""
    with open_index(db) as conn:
        records = photos_in_folder(conn, folder)
    provider.register_photos(records)
    return records


def _scan(dedup, call=None):
    results = []
    dedup.scanFinished.connect(results.append)
    loop = _quit_on(dedup.scanFinished)
    (call or dedup.scanForDuplicates)()
    loop.exec()
    assert results, "scanFinished nem érkezett meg"
    return results[0]


class TestMainGridRegistrationSurvives:
    def test_grid_ids_still_resolve_after_a_dedup_scan(
        self, dedup, provider, library
    ):
        lib, _other, db = library
        records = _register_main_grid(provider, db, lib)
        assert records

        _scan(dedup)

        for record in records:
            assert provider._registry.get(str(record.id)) is not None, (
                "a dedup-keresés kiütötte a fő rács regisztrációját (#298)"
            )

    def test_grid_thumbnails_still_render_after_a_dedup_scan(
        self, dedup, provider, library
    ):
        from picasapy.app.thumbnail_provider import PLACEHOLDER_COLOR

        lib, _other, db = library
        records = _register_main_grid(provider, db, lib)

        _scan(dedup)

        image = provider.requestImage(str(records[0].id), None, None)
        assert not image.isNull()
        assert image.width() > 16 or image.pixel(0, 0) != PLACEHOLDER_COLOR

    def test_controller_does_not_call_register_photos(
        self, dedup, provider, library, monkeypatch
    ):
        calls = []
        monkeypatch.setattr(
            type(provider), "register_photos", lambda self, photos: calls.append(photos)
        )
        _scan(dedup)
        assert calls == [], "a dedup nem hívhatja a register_photos-t (#298)"


class TestOwnIdRange:
    def test_thumb_ids_are_in_the_dedup_reserved_range(self, dedup, library):
        from picasapy.app.dedup_controller import DEDUP_THUMB_ID_BASE

        groups = _scan(dedup)
        ids = [
            int(item["thumbUrl"].rsplit("/", 1)[1])
            for group in groups
            for item in group["items"]
        ]
        assert ids
        assert all(photo_id <= DEDUP_THUMB_ID_BASE for photo_id in ids)

    def test_reserved_range_does_not_collide_with_import_previews(self):
        """Az Import-forrás előnézete a -1-től lefelé foglal
        (`import_source_controller._preview_photo_record`) — a dedup
        tartománya ennél jóval lejjebb kezdődik, hogy a két dialógus
        egyszerre is nyitva lehessen."""
        from picasapy.app.dedup_controller import DEDUP_THUMB_ID_BASE

        assert DEDUP_THUMB_ID_BASE < -1000

    def test_dedup_thumbnails_are_resolvable(self, dedup, provider, library):
        groups = _scan(dedup)
        for group in groups:
            for item in group["items"]:
                photo_id = item["thumbUrl"].rsplit("/", 1)[1]
                assert provider._registry.get(photo_id) is not None


class TestCleanup:
    def test_release_removes_only_the_dedup_entries(self, dedup, provider, library):
        lib, _other, db = library
        records = _register_main_grid(provider, db, lib)
        groups = _scan(dedup)
        dedup_ids = [
            item["thumbUrl"].rsplit("/", 1)[1]
            for group in groups
            for item in group["items"]
        ]
        assert dedup_ids

        dedup.releaseThumbnails()

        for photo_id in dedup_ids:
            assert provider._registry.get(photo_id) is None
        for record in records:
            assert provider._registry.get(str(record.id)) is not None

    def test_release_is_idempotent(self, dedup, provider, library):
        _scan(dedup)
        dedup.releaseThumbnails()
        dedup.releaseThumbnails()  # nem dobhat

    def test_new_scan_drops_the_previous_dedup_entries(
        self, dedup, provider, library
    ):
        first = _scan(dedup)
        first_ids = {
            item["thumbUrl"].rsplit("/", 1)[1]
            for group in first
            for item in group["items"]
        }
        lib, _other, _db = library
        # a második keresés szűkebb hatókörű: a korábbi bejegyzéseknek
        # el kell tűnniük, nem halmozódhatnak
        _scan(dedup, lambda: dedup.scanFolder(str(lib)))

        remaining = {
            key for key in provider._registry if key in first_ids
        }
        assert remaining == set()

    def test_release_without_provider_is_safe(self, qt_app, library):
        from picasapy.app.dedup_controller import DedupController

        _lib, _other, db = library
        DedupController(db, None).releaseThumbnails()
