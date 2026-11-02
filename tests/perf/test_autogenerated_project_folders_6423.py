"""#6423: az automatikus projektmappák túlélnek egy induláskori takarítást."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QImage

from picasapy.app import collage_output, collage_prefs, movie_output
from picasapy.app.application_data import _takaritas_gyokerei
from picasapy.app.camera_capture_controller import CameraCaptureController
from picasapy.app.screen_capture import save_screenshot, screen_capture_folder
from picasapy.index import open_index, prune_foreign_folders, sync_folder


@pytest.mark.parametrize("projektmappa", ["captured_videos", "screen_captures"])
def test_automatikus_projektmappa_es_kepe_tuleli_az_ujrainditast(
    projektmappa, tmp_path, monkeypatch
):
    pictures = tmp_path / "Pictures"
    monkeypatch.setattr(movie_output, "pictures_dir", lambda: pictures)
    monkeypatch.setattr(collage_output, "pictures_dir", lambda: pictures)

    if projektmappa == "captured_videos":
        cel = Path(CameraCaptureController().reserveCapturePath("snapshot"))
        image = QImage(32, 24, QImage.Format.Format_RGB32)
        image.fill(QColor("red"))
        assert image.save(str(cel), "JPEG")
        mappa = cel.parent
    else:
        mappa = screen_capture_folder(pictures, "hu")
        image = QImage(32, 24, QImage.Format.Format_RGB32)
        image.fill(QColor("red"))
        save_screenshot(
            image,
            mappa,
            "PicasaPy",
            datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc),
            date_time_text="2026-11-02 12.00.00",
        )

    watched = tmp_path / "watched"
    watched.mkdir()
    (watched / "watched.txt").write_text("watched", encoding="utf-8")
    db = tmp_path / "index.db"
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(collage_prefs.OUTPUT_DIR_KEY, str(tmp_path / "no-collages"))

    # Az első munkamenet menti a képet és felveszi a mappát az indexbe.
    with open_index(db) as conn:
        sync_folder(conn, watched, watched)
        sync_folder(conn, mappa, mappa)
        elso_mappak = {
            row["path"] for row in conn.execute("SELECT path FROM folders")
        }
        elso_kepszam = conn.execute(
            "SELECT COUNT(*) FROM photos p JOIN folders f ON f.id = p.folder_id "
            "WHERE f.path = ?",
            (str(mappa.resolve()),),
        ).fetchone()[0]

    assert str(mappa.resolve()) in elso_mappak
    assert elso_kepszam == 1

    # Új SQLite-kapcsolat = újraindítás; a program induláskori takarítása fut.
    with open_index(db) as conn:
        prune_foreign_folders(
            conn, _takaritas_gyokerei((str(watched),), settings)
        )
        ujraindult_mappak = {
            row["path"] for row in conn.execute("SELECT path FROM folders")
        }
        ujraindult_kepszam = conn.execute(
            "SELECT COUNT(*) FROM photos p JOIN folders f ON f.id = p.folder_id "
            "WHERE f.path = ?",
            (str(mappa.resolve()),),
        ).fetchone()[0]

    assert str(mappa.resolve()) in ujraindult_mappak
    assert ujraindult_kepszam == 1
