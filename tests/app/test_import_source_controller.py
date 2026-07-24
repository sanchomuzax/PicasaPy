"""ImportSourceController: "Import forrásból" (#23) QML-hídja a
`picasapy.importsource`/`picasapy.fileops.copy_photo` mag fölött — valódi
ideiglenes forrás- és cél-mappával, mock nélkül (a `test_dedup_controller.py`
mintája)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from picasapy.ini import load_document
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
def added(request):
    """A `runImport` sikeres futása után ide kerül a cél-mappa (a
    `controller.addWatchedFolder`-t helyettesítő callback)."""
    return []


@pytest.fixture
def controller(qt_app, provider, added):
    from picasapy.app.import_source_controller import ImportSourceController

    return ImportSourceController(provider, add_folder=added.append)


def _scan(controller, folder: str):
    items_seen = []
    counts_seen = []
    controller.sourceScanFinished.connect(
        lambda items, count: (items_seen.append(items), counts_seen.append(count))
    )
    loop = _quit_on(controller.sourceScanFinished)
    controller.scanSource(folder)
    loop.exec()
    return items_seen[0] if items_seen else None, counts_seen[0] if counts_seen else None


class TestScanSource:
    def test_emits_started_before_finished(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")

        events = []
        controller.sourceScanStarted.connect(lambda: events.append("started"))
        controller.sourceScanFinished.connect(
            lambda items, count: events.append("finished")
        )
        loop = _quit_on(controller.sourceScanFinished)
        controller.scanSource(str(source))
        loop.exec()

        assert events == ["started", "finished"]

    def test_finds_pictures_with_thumb_urls(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")

        items, count = _scan(controller, str(source))

        assert count == 2
        assert isinstance(items, list)
        paths = {item["path"] for item in items}
        assert paths == {str(source / "a.jpg"), str(source / "b.jpg")}
        for item in items:
            assert item["thumbUrl"].startswith("image://thumbs/")

    def test_no_provider_gives_empty_thumb_url(self, qt_app, tmp_path, added):
        from picasapy.app.import_source_controller import ImportSourceController

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        controller = ImportSourceController(None, add_folder=added.append)

        items, count = _scan(controller, str(source))

        assert count == 1
        assert items[0]["thumbUrl"] == ""

    def test_missing_source_emits_scan_failed(self, controller, tmp_path):
        messages = []
        controller.sourceScanFailed.connect(lambda msg: messages.append(msg))
        loop = _quit_on(controller.sourceScanFailed)
        controller.scanSource(str(tmp_path / "nincs-ilyen"))
        loop.exec()
        assert len(messages) == 1
        assert messages[0]

    def test_rescanning_does_not_leak_previous_preview_registrations(
        self, controller, provider, tmp_path
    ):
        """Ismételt szkennelésnél a régi (negatív id-jű) előnézeti
        bejegyzések ne halmozódjanak a megosztott provider registry-jében."""
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        _scan(controller, str(source))

        make_jpeg(source / "b.jpg")
        _scan(controller, str(source))

        # csak a MÁSODIK szkennelés két bejegyzése maradhat a negatív
        # (import-előnézeti) id-tartományban — az első szkennelés bejegyzése
        # nem halmozódik rá
        negative_keys = {
            key for key in provider._registry if key.startswith("-")
        }
        assert len(negative_keys) == 2


class TestRunImport:
    def test_copies_files_into_date_subfolder_and_keeps_source(
        self, controller, tmp_path, added
    ):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        progresses = []
        controller.importProgress.connect(
            lambda done, total: progresses.append((done, total))
        )
        finished = []
        controller.importFinished.connect(
            lambda copied, failed: finished.append((copied, failed))
        )
        loop = _quit_on(controller.importFinished)
        controller.runImport(str(dest), "{YYYY}/{YYYY}-{MM}-{DD}", False)
        loop.exec()

        target = dest / "2024" / "2024-03-05" / "a.jpg"
        assert target.exists()
        assert (source / "a.jpg").exists()  # másolás — a forrás megmarad
        assert finished == [(1, 0)]
        assert progresses == [(1, 1)]
        assert added == [str(dest)]  # a cél a könyvtár része lesz

    def test_move_removes_the_source_file(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        loop = _quit_on(controller.importFinished)
        controller.runImport(str(dest), "{YYYY}/{YYYY}-{MM}-{DD}", True)
        loop.exec()

        assert (dest / "2024" / "2024-03-05" / "a.jpg").exists()
        assert not (source / "a.jpg").exists()

    def test_move_transfers_ini_section_and_removes_it_from_source(
        self, controller, tmp_path
    ):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        (source / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        loop = _quit_on(controller.importFinished)
        controller.runImport(str(dest), "{YYYY}/{YYYY}-{MM}-{DD}", True)
        loop.exec()

        source_doc = load_document(source / ".picasa.ini")
        assert source_doc.section("a.jpg") is None
        dest_doc = load_document(dest / "2024" / "2024-03-05" / ".picasa.ini")
        assert dest_doc.section("a.jpg").get("star") == "yes"

    def test_missing_exif_date_falls_back_to_mtime(self, controller, tmp_path):
        import os
        from datetime import datetime

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")  # nincs EXIF-dátum
        some_time = 1_700_000_000  # determinisztikus, de van érvényes mtime
        os.utime(source / "a.jpg", (some_time, some_time))
        expected = datetime.fromtimestamp(some_time).date()
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        loop = _quit_on(controller.importFinished)
        controller.runImport(str(dest), "{YYYY}/{YYYY}-{MM}-{DD}", False)
        loop.exec()

        subfolder = f"{expected.year:04d}-{expected.month:02d}-{expected.day:02d}"
        assert (dest / f"{expected.year:04d}" / subfolder / "a.jpg").exists()

    def test_no_candidates_finishes_immediately_without_adding_folder(
        self, controller, tmp_path, added
    ):
        finished = []
        controller.importFinished.connect(
            lambda copied, failed: finished.append((copied, failed))
        )
        controller.runImport(str(tmp_path), "{YYYY}", False)
        assert finished == [(0, 0)]
        assert added == []

    def test_one_bad_file_does_not_stop_the_batch(
        self, controller, tmp_path, monkeypatch
    ):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg", taken_at="2024:03:06 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))

        import picasapy.app.import_source_controller as controller_module

        original_copy = controller_module.copy_photo

        def flaky_copy(path, dest_folder):
            if path.name == "a.jpg":
                raise OSError("szimulált hiba")
            return original_copy(path, dest_folder)

        monkeypatch.setattr(controller_module, "copy_photo", flaky_copy)

        failed_details = []
        controller.importFailedDetails.connect(
            lambda details: failed_details.append(details)
        )
        finished = []
        controller.importFinished.connect(
            lambda copied, failed: finished.append((copied, failed))
        )
        loop = _quit_on(controller.importFinished)
        controller.runImport(str(dest), "{YYYY}/{YYYY}-{MM}-{DD}", False)
        loop.exec()

        assert finished == [(1, 1)]
        assert (dest / "2024" / "2024-03-06" / "b.jpg").exists()
        assert not (dest / "2024" / "2024-03-05" / "a.jpg").exists()
        assert len(failed_details) == 1
        assert "a.jpg" in failed_details[0][0]
