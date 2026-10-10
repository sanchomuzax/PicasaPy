"""#4596: az importálás forrása kijelölt FÁJLOK listája is lehet, nem csak mappa."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QSettings, QUrl

from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.import_source_controller import ImportSourceController
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    ctrl = ImportSourceController(
        provider, add_folder=lambda _p: None,
        index_path=tmp_path / "index.db", settings=settings,
    )
    yield ctrl
    assert ctrl.waitForBackgroundWorkers(30.0)


def _var(ctrl) -> None:
    assert ctrl.waitForBackgroundWorkers(30.0)
    QCoreApplication.processEvents()


def _forras(tmp_path: Path) -> tuple[Path, Path, Path]:
    forras = tmp_path / "forras"
    forras.mkdir()
    egy = forras / "a.jpg"
    ketto = forras / "b.jpg"
    harmadik = forras / "c.jpg"
    for fajl in (egy, ketto, harmadik):
        make_jpeg(fajl, taken_at="2024:03:05 10:00:00")
    (forras / "jegyzet.txt").write_text("nem média")
    return egy, ketto, harmadik


def test_scan_files_lists_only_the_selected_files(controller, tmp_path):
    egy, ketto, _harmadik = _forras(tmp_path)
    kapott = []
    controller.sourceScanFinished.connect(lambda items, count: kapott.append((items, count)))

    controller.scanFiles([str(egy), QUrl.fromLocalFile(str(ketto)).toString()])
    _var(controller)

    items, count = kapott[0]
    assert count == 2
    assert {Path(i["path"]).name for i in items} == {"a.jpg", "b.jpg"}


def test_selected_files_are_imported_and_the_rest_of_the_folder_is_not(
    controller, tmp_path
):
    egy, ketto, harmadik = _forras(tmp_path)
    cel = tmp_path / "cel"
    cel.mkdir()
    kesz = []
    controller.importFinished.connect(lambda ok, hiba: kesz.append((ok, hiba)))

    controller.scanFiles([str(egy), str(ketto)])
    _var(controller)
    controller.runImport(str(cel), "date", "", "leave")
    _var(controller)

    assert kesz[-1] == (2, 0)
    assert (cel / "2024-03-05" / "a.jpg").is_file()
    assert (cel / "2024-03-05" / "b.jpg").is_file()
    assert not (cel / "2024-03-05" / "c.jpg").exists()
    assert harmadik.is_file()


def test_manual_folder_name_check_still_applies_to_files(controller, tmp_path):
    egy, _k, _h = _forras(tmp_path)
    cel = tmp_path / "cel"
    cel.mkdir()
    controller.scanFiles([str(egy)])
    _var(controller)
    controller.runImport(str(cel), "manual", "../kiszokes", "leave")
    _var(controller)
    assert list(cel.iterdir()) == []


def test_non_media_and_missing_files_are_skipped(controller, tmp_path):
    egy, _k, _h = _forras(tmp_path)
    kapott = []
    controller.sourceScanFinished.connect(lambda items, count: kapott.append(count))
    controller.scanFiles(
        [str(egy), str(tmp_path / "forras" / "jegyzet.txt"), str(tmp_path / "nincs.jpg")]
    )
    _var(controller)
    assert kapott == [1]


def test_empty_selection_fails_with_a_message(controller):
    hibak = []
    controller.sourceScanFailed.connect(hibak.append)
    controller.scanFiles([])
    _var(controller)
    assert len(hibak) == 1
