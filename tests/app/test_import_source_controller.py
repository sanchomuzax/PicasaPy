"""ImportSourceController: "Import forrásból" (#23/#441) QML-hídja a
`picasapy.importsource`/`picasapy.fileops.copy_photo` mag fölött — valódi
ideiglenes forrás- és cél-mappával, mock nélkül (a `test_dedup_controller.py`
mintája)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QSettings

from picasapy.ini import load_document
from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


def _megvar_hattermunkat(controller) -> None:
    """DETERMINISZTIKUS szinkronpont a háttérszálas hívások után (#1634).

    A korábbi minta egy `QEventLoop`-ot indított, és egy 5 másodperces
    `QTimer.singleShot(5000, ...quit)`-tal „biztosította", hogy ne akadjon
    be. Csakhogy az időzítő nem hibaág volt, hanem a hurok MÁSODIK, NÉMA
    kijárata: ha a jelzés lassabban ért oda, a teszt nem időtúllépést
    jelentett, hanem azt, hogy a jelzés ELMARADT. A windows-lábon pontosan
    ez történt (futás `33085887241`)::

        assert events == ["started", "finished"]
        AssertionError: assert ['started'] == ['started', 'finished']

    …miközben ugyanannak a tesztnek a fixture-teardownja sikeresen
    bevárta a szálat, tehát a munka rendben LEFUTOTT, csak későn. Ugyanez
    a minta tette a `test_a_failed_scan_is_not_remembered`-et állandó,
    ~5 másodperces tesztté: ott sosem jön `sourceScanFinished`, tehát
    mindig a teljes időzítőt kivárta — helyben mérve ez volt a fájl
    leglassabb tesztje (4,75 s a 7,98 s-ból).

    Itt a szinkronpont maga a szál BEVÁRÁSA (`join`), utána a közben
    sorba állított Qt-jelzések kihajtása. Nincs `sleep`, és nincs olyan
    időkorlát, amin átcsúszva a teszt hamis leletet mondana: ha a bevárás
    mégsem sikerül, SAJÁT, beszédes hibaüzenetet ad."""
    assert controller.waitForBackgroundWorkers(30.0), (
        "az import-forrás háttérszála nem állt le"
    )
    QCoreApplication.processEvents()


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
def settings(tmp_path):
    return QSettings(str(tmp_path / "importsettings.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def make_controller(qt_app, tmp_path, settings):
    """`ImportSourceController`-gyár, ami a teszt végén MEGVÁRJA a
    háttérszálakat (#438, a #430 SIGSEGV-osztály elkerülése — a
    `test_webexport_controller.py` mintája)."""
    from picasapy.app.import_source_controller import ImportSourceController

    created = []

    def _make(provider, add_folder, index_path=None):
        controller = ImportSourceController(
            provider,
            add_folder=add_folder,
            index_path=index_path if index_path is not None else tmp_path / "index.db",
            settings=settings,
        )
        created.append(controller)
        return controller

    yield _make

    for controller in created:
        assert controller.waitForBackgroundWorkers(30.0), (
            "az import-forrás háttérszála nem állt le"
        )


@pytest.fixture
def controller(make_controller, provider, added):
    return make_controller(provider, added.append)


def _scan(controller, folder: str):
    items_seen = []
    counts_seen = []
    controller.sourceScanFinished.connect(
        lambda items, count: (items_seen.append(items), counts_seen.append(count))
    )
    controller.scanSource(folder)
    _megvar_hattermunkat(controller)
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
        controller.scanSource(str(source))
        _megvar_hattermunkat(controller)

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
            assert item["duplicate"] is False
            assert item["excluded"] is False

    def test_no_provider_gives_empty_thumb_url(self, make_controller, tmp_path, added):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        controller = make_controller(None, added.append)

        items, count = _scan(controller, str(source))

        assert count == 1
        assert items[0]["thumbUrl"] == ""

    def test_missing_source_emits_scan_failed(self, controller, tmp_path):
        messages = []
        controller.sourceScanFailed.connect(lambda msg: messages.append(msg))
        controller.scanSource(str(tmp_path / "nincs-ilyen"))
        _megvar_hattermunkat(controller)
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


class TestDuplicateExclusion:
    """#441 — "Exclude Duplicates": a már indexelt könyvtárral tartalom-
    egyező jelöltek megjelölése, és — `autoExclude` esetén — alapból
    kihagyása a válogatásból."""

    def test_duplicate_of_an_indexed_photo_is_flagged(
        self, make_controller, provider, tmp_path, added
    ):
        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(library / "eredeti.jpg", size=(64, 64))
        index_db = tmp_path / "index.db"
        from picasapy.index import open_index, sync_tree

        with open_index(index_db) as conn:
            sync_tree(conn, library)

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "eredeti.jpg", size=(64, 64))  # bitre azonos
        make_jpeg(source / "uj.jpg", size=(32, 32))  # egyedi

        controller = make_controller(provider, added.append, index_path=index_db)
        items, count = _scan(controller, str(source))

        assert count == 2
        # Path(...).name, NEM split("/") — Windowson a szeparátor "\\",
        # ott a naiv vágás az EGÉSZ útvonalat adná kulcsnak (KeyError).
        by_name = {Path(item["path"]).name: item for item in items}
        assert by_name["eredeti.jpg"]["duplicate"] is True
        assert by_name["uj.jpg"]["duplicate"] is False

    def test_autoexclude_off_by_default_keeps_duplicates_selected(
        self, make_controller, provider, tmp_path, added
    ):
        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(library / "eredeti.jpg", size=(64, 64))
        index_db = tmp_path / "index.db"
        from picasapy.index import open_index, sync_tree

        with open_index(index_db) as conn:
            sync_tree(conn, library)

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "eredeti.jpg", size=(64, 64))

        controller = make_controller(provider, added.append, index_path=index_db)
        assert controller.autoExclude is False
        items, _count = _scan(controller, str(source))

        assert items[0]["duplicate"] is True
        assert items[0]["excluded"] is False

    def test_autoexclude_on_excludes_duplicates_by_default(
        self, make_controller, provider, tmp_path, added
    ):
        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(library / "eredeti.jpg", size=(64, 64))
        index_db = tmp_path / "index.db"
        from picasapy.index import open_index, sync_tree

        with open_index(index_db) as conn:
            sync_tree(conn, library)

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "eredeti.jpg", size=(64, 64))

        controller = make_controller(provider, added.append, index_path=index_db)
        controller.setAutoExclude(True)
        items, _count = _scan(controller, str(source))

        assert items[0]["duplicate"] is True
        assert items[0]["excluded"] is True

    def test_toggling_autoexclude_after_scan_updates_selection_live(
        self, make_controller, provider, tmp_path, added
    ):
        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(library / "eredeti.jpg", size=(64, 64))
        index_db = tmp_path / "index.db"
        from picasapy.index import open_index, sync_tree

        with open_index(index_db) as conn:
            sync_tree(conn, library)

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "eredeti.jpg", size=(64, 64))

        controller = make_controller(provider, added.append, index_path=index_db)
        _scan(controller, str(source))

        updates = []
        controller.selectionChanged.connect(lambda items: updates.append(items))
        controller.setAutoExclude(True)

        assert len(updates) == 1
        assert updates[0][0]["excluded"] is True

    def test_no_duplicates_when_index_is_missing(self, make_controller, provider, tmp_path, added):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")

        controller = make_controller(
            provider, added.append, index_path=tmp_path / "nincs-ilyen" / "index.db"
        )
        items, _count = _scan(controller, str(source))

        assert items[0]["duplicate"] is False


class TestIndividualSelection:
    """#441 — egyenkénti válogatás: Exclude/Include File, Exclude/Include All."""

    def test_excluding_a_file_marks_it_excluded(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")
        _scan(controller, str(source))

        updates = []
        controller.selectionChanged.connect(lambda items: updates.append(items))
        controller.excludeFile(str(source / "a.jpg"))

        assert len(updates) == 1
        by_path = {item["path"]: item for item in updates[0]}
        assert by_path[str(source / "a.jpg")]["excluded"] is True
        assert by_path[str(source / "b.jpg")]["excluded"] is False

    def test_including_a_previously_excluded_file(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        _scan(controller, str(source))
        controller.excludeFile(str(source / "a.jpg"))

        updates = []
        controller.selectionChanged.connect(lambda items: updates.append(items))
        controller.includeFile(str(source / "a.jpg"))

        assert updates[-1][0]["excluded"] is False

    def test_exclude_all_marks_every_candidate_excluded(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")
        _scan(controller, str(source))

        controller.excludeAll()

        assert all(
            item["excluded"] for item in controller._preview_items()
        )

    def test_include_all_clears_exclusions(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")
        _scan(controller, str(source))
        controller.excludeAll()

        controller.includeAll()

        assert all(
            not item["excluded"] for item in controller._preview_items()
        )

    def test_only_included_files_are_imported(self, controller, tmp_path, added):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg", taken_at="2024:03:06 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()
        _scan(controller, str(source))
        controller.excludeFile(str(source / "a.jpg"))

        finished = []
        controller.importFinished.connect(
            lambda copied, failed: finished.append((copied, failed))
        )
        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        assert finished == [(1, 0)]
        assert (dest / "2024-03-06" / "b.jpg").exists()
        assert not (dest / "2024-03-05" / "a.jpg").exists()
        assert (source / "a.jpg").exists()  # ki lett zárva — a forrás érintetlen


class TestRunImportNamingModes:
    """#441 — a HÁROM célmappa-elnevezési mód a teljes import-folyamatba
    illesztve."""

    def test_by_date_mode_splits_into_one_folder_per_date(
        self, controller, tmp_path, added
    ):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        target = dest / "2024-03-05" / "a.jpg"
        assert target.exists()
        assert (source / "a.jpg").exists()  # másolás — a forrás megmarad
        assert added == [str(dest)]

    def test_manual_mode_uses_the_given_folder_name(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg", taken_at="2024:03:06 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        controller.runImport(str(dest), "manual", "Nyaralás", "leave")
        _megvar_hattermunkat(controller)

        assert (dest / "Nyaralás" / "a.jpg").exists()
        assert (dest / "Nyaralás" / "b.jpg").exists()

    def test_today_mode_uses_a_single_folder_for_every_candidate(
        self, controller, tmp_path
    ):
        from datetime import date

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg")  # nincs EXIF — mtime-visszaesés
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        controller.runImport(str(dest), "today", "", "leave")
        _megvar_hattermunkat(controller)

        today_folder = dest / date.today().isoformat()
        assert (today_folder / "a.jpg").exists()
        assert (today_folder / "b.jpg").exists()

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
        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        subfolder = f"{expected.year:04d}-{expected.month:02d}-{expected.day:02d}"
        assert (dest / subfolder / "a.jpg").exists()

    def test_no_candidates_finishes_immediately_without_adding_folder(
        self, controller, tmp_path, added
    ):
        finished = []
        controller.importFinished.connect(
            lambda copied, failed: finished.append((copied, failed))
        )
        controller.runImport(str(tmp_path), "date", "", "leave")
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
        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        assert finished == [(1, 1)]
        assert (dest / "2024-03-06" / "b.jpg").exists()
        assert not (dest / "2024-03-05" / "a.jpg").exists()
        assert len(failed_details) == 1
        assert "a.jpg" in failed_details[0][0]


class TestAfterCopying:
    """#441 — "After Copying:" háromállapotú forrás-törlés."""

    def test_leave_card_alone_keeps_every_source_file(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        assert (source / "a.jpg").exists()

    def test_delete_copied_removes_only_the_copied_files(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg", taken_at="2024:03:06 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        controller.excludeFile(str(source / "b.jpg"))  # b.jpg NEM importálódik
        controller.runImport(str(dest), "date", "", "delete_copied")
        _megvar_hattermunkat(controller)

        assert not (source / "a.jpg").exists()  # importálva -> törölve
        assert (source / "b.jpg").exists()  # ki volt zárva -> megmarad

    def test_delete_copied_transfers_ini_section_and_removes_it_from_source(
        self, controller, tmp_path
    ):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        (source / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        controller.runImport(str(dest), "date", "", "delete_copied")
        _megvar_hattermunkat(controller)

        source_doc = load_document(source / ".picasa.ini")
        assert source_doc.section("a.jpg") is None
        dest_doc = load_document(dest / "2024-03-05" / ".picasa.ini")
        assert dest_doc.section("a.jpg").get("star") == "yes"

    def test_delete_all_removes_excluded_files_too(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg", taken_at="2024:03:06 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))
        controller.excludeFile(str(source / "b.jpg"))  # b.jpg NEM importálódik
        controller.runImport(str(dest), "date", "", "delete_all")
        _megvar_hattermunkat(controller)

        assert not (source / "a.jpg").exists()
        assert not (source / "b.jpg").exists()  # "everything on card"

    def test_delete_all_spares_the_file_whose_copy_failed(
        self, controller, tmp_path, monkeypatch
    ):
        """RÉSZLEGES hiba: ha két jelöltből az egyik másolása elhasal, a
        "minden törlése" az ÁTJUTOTT fájlt törli, a BUKOTTAT viszont
        meghagyja — épp az nem került át, a törlése adatvesztés lenne."""
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg", taken_at="2024:03:06 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))

        import picasapy.app.import_source_controller as controller_module

        real_copy = controller_module.copy_photo

        def copy_but_fail_on_b(path, dest_folder):
            if path.name == "b.jpg":
                raise OSError("szimulált hiba")
            return real_copy(path, dest_folder)

        monkeypatch.setattr(controller_module, "copy_photo", copy_but_fail_on_b)

        controller.runImport(str(dest), "date", "", "delete_all")
        _megvar_hattermunkat(controller)

        assert not (source / "a.jpg").exists()  # átjutott -> törölhető
        assert (source / "b.jpg").exists()  # bukott -> MARAD

    def test_failed_copy_of_the_only_candidate_deletes_nothing(
        self, controller, tmp_path, monkeypatch
    ):
        """A törlés csak SIKERES másolás után futhat le — ha az egyetlen
        jelölt másolása elhasal, a forrás egyetlen fájlja sem törlődhet,
        se "delete_copied", se "delete_all" módban."""
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()

        _scan(controller, str(source))

        import picasapy.app.import_source_controller as controller_module

        def failing_copy(path, dest_folder):
            raise OSError("szimulált hiba")

        monkeypatch.setattr(controller_module, "copy_photo", failing_copy)

        controller.runImport(str(dest), "date", "", "delete_all")
        _megvar_hattermunkat(controller)

        assert (source / "a.jpg").exists()


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): a szkennelő/importáló
    háttérszál bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, controller):
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_scan_worker_thread(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        _scan(controller, str(source))
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()

    def test_wait_joins_the_import_worker_thread(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()
        _scan(controller, str(source))

        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()


class TestRotateAndStarBeforeImport:
    """#441: az eredeti import-képernyőn az előnézeten forgatni és
    csillagozni lehetett MÁR A BEMÁSOLÁS ELŐTT — a jelölés a MÁSOLAT
    `.picasa.ini`-jébe kerül, a kártyán lévő eredeti érintetlen marad."""

    def _scan_source(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir(exist_ok=True)
        make_jpeg(source / "a.jpg")
        items, _count = _scan(controller, str(source))
        return source, items

    def test_the_preview_carries_the_marks(self, controller, tmp_path):
        _source, items = self._scan_source(controller, tmp_path)
        path = items[0]["path"]
        assert items[0]["rotation"] == 0
        assert items[0]["starred"] is False

        seen = []
        controller.selectionChanged.connect(seen.append)
        controller.rotateFile(path, 1)
        controller.toggleStar(path)

        assert seen[-1][0]["rotation"] == 1
        assert seen[-1][0]["starred"] is True

    def test_the_rotation_wraps_around(self, controller, tmp_path):
        _source, items = self._scan_source(controller, tmp_path)
        path = items[0]["path"]
        seen = []
        controller.selectionChanged.connect(seen.append)

        for _ in range(4):
            controller.rotateFile(path, 1)

        assert seen[-1][0]["rotation"] == 0

    def test_rotating_left_goes_the_other_way(self, controller, tmp_path):
        _source, items = self._scan_source(controller, tmp_path)
        seen = []
        controller.selectionChanged.connect(seen.append)

        controller.rotateFile(items[0]["path"], -1)

        assert seen[-1][0]["rotation"] == 3

    def test_an_unknown_path_is_ignored(self, controller, tmp_path):
        self._scan_source(controller, tmp_path)
        seen = []
        controller.selectionChanged.connect(seen.append)

        controller.rotateFile("/nincs/ilyen.jpg", 1)
        controller.toggleStar("/nincs/ilyen.jpg")

        assert seen == []

    def test_a_new_scan_clears_the_marks(self, controller, tmp_path):
        _source, items = self._scan_source(controller, tmp_path)
        controller.rotateFile(items[0]["path"], 1)
        controller.toggleStar(items[0]["path"])

        _source, items = self._scan_source(controller, tmp_path)

        assert items[0]["rotation"] == 0
        assert items[0]["starred"] is False

    def test_the_marks_land_in_the_copy_not_the_card(
        self, controller, tmp_path
    ):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()
        items, _count = _scan(controller, str(source))
        controller.rotateFile(items[0]["path"], 1)
        controller.toggleStar(items[0]["path"])

        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        copied_ini = dest / "2024-03-05" / ".picasa.ini"
        assert copied_ini.exists()
        text = copied_ini.read_text(encoding="utf-8")
        assert "rotate=rotate(1)" in text
        assert "star=yes" in text
        # a kártyán lévő eredetihez NEM nyúlunk
        assert not (source / ".picasa.ini").exists()

    def test_without_marks_no_ini_is_written(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "konyvtar"
        dest.mkdir()
        _scan(controller, str(source))

        controller.runImport(str(dest), "date", "", "leave")
        _megvar_hattermunkat(controller)

        assert (dest / "2024-03-05" / "a.jpg").exists()
        assert not (dest / "2024-03-05" / ".picasa.ini").exists()


class TestImportSpeed:
    """#441: az eredeti haladásjelzője a SEBESSÉGET is kiírta
    („Copying %d of %d files at %s/sec")."""

    def test_the_speed_is_reported_during_the_copy(self, controller, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")
        dest = tmp_path / "konyvtar"
        dest.mkdir()
        _scan(controller, str(source))
        speeds = []
        controller.importSpeed.connect(speeds.append)

        controller.runImport(str(dest), "today", "", "leave")
        _megvar_hattermunkat(controller)

        # fájlonként egy jelzés, és a sebesség sosem negatív
        assert len(speeds) == 2
        assert all(speed >= 0 for speed in speeds)

    def test_a_failed_file_does_not_break_the_measurement(
        self, controller, tmp_path
    ):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        dest = tmp_path / "konyvtar"
        dest.mkdir()
        _scan(controller, str(source))
        (source / "a.jpg").unlink()  # a másolás el fog bukni
        speeds = []
        controller.importSpeed.connect(speeds.append)

        controller.runImport(str(dest), "today", "", "leave")
        _megvar_hattermunkat(controller)

        assert speeds == [0.0]


class TestRecentSources:
    """#441: a forrásválasztó legördülője a KORÁBBI importok listáját is
    kínálta (`LastImport…`) — a rendszeresen használt kártya/mappa így egy
    kattintással újra elérhető."""

    def _scan_folder(self, controller, tmp_path, name):
        source = tmp_path / name
        source.mkdir()
        make_jpeg(source / "a.jpg")
        _scan(controller, str(source))
        return source

    def test_the_list_starts_empty(self, controller):
        assert list(controller.recentSources) == []

    def test_a_scanned_source_is_remembered(self, controller, tmp_path):
        source = self._scan_folder(controller, tmp_path, "kartya")

        assert list(controller.recentSources) == [str(source)]

    def test_the_newest_comes_first_without_repeats(self, controller, tmp_path):
        first = self._scan_folder(controller, tmp_path, "egy")
        second = self._scan_folder(controller, tmp_path, "ketto")
        _scan(controller, str(first))  # újra az elsőt

        assert list(controller.recentSources) == [str(first), str(second)]

    def test_a_failed_scan_is_not_remembered(self, controller, tmp_path):
        _scan(controller, str(tmp_path / "nincs-ilyen"))

        assert list(controller.recentSources) == []

    def test_the_list_is_capped(self, controller, tmp_path):
        from picasapy.app.import_source_controller import MAX_RECENT_SOURCES

        for index in range(MAX_RECENT_SOURCES + 3):
            self._scan_folder(controller, tmp_path, f"kartya{index}")

        assert len(list(controller.recentSources)) == MAX_RECENT_SOURCES


class _CommitBukikKapcsolat:
    """A valódi kapcsolat, de a `commit()` zárolást jelez.

    Az `sqlite3.Connection.commit` írásvédett attribútum, tehát
    monkeypatchelni nem lehet — a hibás commit útját csak burkolóval lehet
    kipróbálni."""

    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, nev):
        return getattr(self._conn, nev)

    def commit(self):
        import sqlite3

        raise sqlite3.OperationalError("database is locked")


class TestDuplikatumokGyorstarHiba:
    """ŐR (#1494 átnézés, 1. lelet): a gyorskulcs-gyorstár mentésének
    hibája nem dobhatja el a KÉSZ duplikátum-listát.

    A `finally`-ben álló csupasz `conn.commit()` zárolt vagy tele indexen a
    külső `except`-be esett, és az "Exclude Duplicates" szótlanul ÜRES
    halmazt adott vissza — a felhasználó pedig újraimportálta a már meglévő
    képeit. A gyorstár feltöltése kényelmi szolgáltatás: a helyes eredmény
    nem függhet tőle."""

    def test_a_lista_akkor_is_megjon_ha_a_gyorstar_commitja_bukik(
        self, tmp_path, monkeypatch
    ):
        import contextlib

        from picasapy.app import import_source_controller as vezerlo
        from picasapy.importsource import ImportCandidate
        from picasapy.index import open_index, sync_tree

        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(library / "eredeti.jpg", size=(64, 64))
        index_db = tmp_path / "index.db"
        with open_index(index_db) as conn:
            sync_tree(conn, library)

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "eredeti.jpg", size=(64, 64))  # bitre azonos

        @contextlib.contextmanager
        def buko_commitu_index(path):
            with open_index(path) as conn:
                yield _CommitBukikKapcsolat(conn)

        monkeypatch.setattr(vezerlo, "open_index", buko_commitu_index)

        eredmeny = vezerlo._duplikatumok(
            index_db, (ImportCandidate(path=source / "eredeti.jpg", date=None),)
        )

        assert eredmeny == frozenset({source / "eredeti.jpg"})
