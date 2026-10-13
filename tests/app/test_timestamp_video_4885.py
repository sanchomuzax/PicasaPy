"""A videó dátummódosítása minden platformon az indexben marad (#4885)."""

from __future__ import annotations

from datetime import datetime, timedelta

import os

import pytest

from picasapy.app import timestamp_controller
from picasapy.index import open_index, photo_by_id, sync_tree, update_photo_fields
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op

UJ_DATUM = "2021-05-06T07:08:09"
MTIME = datetime(2020, 3, 4, 10, 0, 0)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    (root / "film.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64)
    make_jpeg(
        root / "kep.jpg",
        taken_at="2020:01:01 12:00:00",
        datetime_0th="2020:01:01 12:00:00",
    )
    os.utime(root / "film.mp4", (MTIME.timestamp(), MTIME.timestamp()))
    return root


@pytest.fixture
def video_mappa(tmp_path):
    root = tmp_path / "csak_video"
    root.mkdir()
    (root / "film.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64)
    os.utime(root / "film.mp4", (MTIME.timestamp(), MTIME.timestamp()))
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    return ctl


def _sor(controller, nev: str):
    return next(
        (i, p) for i, p in enumerate(controller.photos.photos) if p.name == nev
    )


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_video_datuma_minden_platformon_az_override_mezoben_marad(
    controller, qt_app, tmp_path, library, monkeypatch, platform
):
    monkeypatch.setattr(timestamp_controller, "_platform", lambda: platform)
    letrehozasi = []
    if platform == "win32":
        # csak itt cseréljük: máshol a valódi függvény a _platform miatt kilép
        monkeypatch.setattr(
            timestamp_controller,
            "_set_creation_time_ns",
            lambda _p, ertek: letrehozasi.append(ertek),
        )
    sor, video = _sor(controller, "film.mp4")
    regi = datetime.fromtimestamp(video.sort_mtime_ns / 1e9).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    wait_for_photo_op(
        controller,
        lambda: controller.adjustPhotoDates([sor], regi, UJ_DATUM, False),
        qt_app=qt_app,
    )

    with open_index(tmp_path / "index.db") as conn:
        assert photo_by_id(conn, video.id).taken_at_override == UJ_DATUM
        # új szinkron (a fájl nem változott, de a mappa újrapásztázva)
        sync_tree(conn, library, incremental=False)
        rekord = photo_by_id(conn, video.id)
        assert rekord.taken_at_override == UJ_DATUM
        assert rekord.taken_at == UJ_DATUM
    assert letrehozasi == (
        [round(datetime.fromisoformat(UJ_DATUM).timestamp() * 1_000_000_000)]
        if platform == "win32"
        else []
    )
    _sor_uj, frissitett = _sor(controller, "film.mp4")
    assert frissitett.taken_at == UJ_DATUM


def test_jpeg_datuma_tovabbra_is_az_exifbe_kerul_override_nelkul(
    controller, qt_app, tmp_path
):
    sor, kep = _sor(controller, "kep.jpg")

    wait_for_photo_op(
        controller,
        lambda: controller.adjustPhotoDates(
            [sor], "2020-01-01 12:00:00", UJ_DATUM, False
        ),
        qt_app=qt_app,
    )

    with open_index(tmp_path / "index.db") as conn:
        rekord = photo_by_id(conn, kep.id)
    assert rekord.taken_at_override is None
    assert rekord.taken_at == UJ_DATUM


def _mappa_datuma(db, mappa) -> str | None:
    with open_index(db) as conn:
        sor = conn.execute(
            "SELECT date FROM folders WHERE path = ?", (str(mappa),)
        ).fetchone()
    return sor[0] if sor else None


def test_csak_videot_tartalmazo_mappa_datuma_is_az_ujat_kapja(
    qt_app, tmp_path, video_mappa
):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    db = tmp_path / "v.db"
    with open_index(db) as conn:
        sync_tree(conn, video_mappa)
    ctl = AppController(
        db,
        (str(video_mappa),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32)),
        settings=QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat),
        watched_file=tmp_path / "w.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(video_mappa))
    wait_for_photo_op(
        ctl,
        lambda: ctl.adjustPhotoDates(
            [0], MTIME.strftime("%Y-%m-%d %H:%M:%S"), UJ_DATUM, False
        ),
        qt_app=qt_app,
    )
    assert _mappa_datuma(db, video_mappa) == UJ_DATUM


def test_eltolasos_mod_videon_ketszer_plusz_egy_nap(controller, qt_app):
    for _ in range(2):
        sor, video = _sor(controller, "film.mp4")
        aktualis = (
            video.taken_at or MTIME.isoformat(timespec="seconds")
        ).replace("T", " ")
        cel = datetime.fromisoformat(aktualis) + timedelta(days=1)
        wait_for_photo_op(
            controller,
            lambda sor=sor, aktualis=aktualis, cel=cel: (
                controller.adjustPhotoDates(
                    [sor], aktualis, cel.isoformat(timespec="seconds"), True
                )
            ),
            qt_app=qt_app,
        )
    _sor_uj, video = _sor(controller, "film.mp4")
    assert video.taken_at == (MTIME + timedelta(days=2)).isoformat(
        timespec="seconds"
    )


def test_regi_override_sikeres_exif_iras_utan_torlodik(
    controller, qt_app, tmp_path
):
    sor, kep = _sor(controller, "kep.jpg")
    with open_index(tmp_path / "index.db") as conn:
        update_photo_fields(conn, kep.id, taken_at_override="1999-01-01T00:00:00")
    wait_for_photo_op(
        controller,
        lambda: controller.adjustPhotoDates(
            [sor], "2020-01-01 12:00:00", UJ_DATUM, False
        ),
        qt_app=qt_app,
    )
    with open_index(tmp_path / "index.db") as conn:
        assert photo_by_id(conn, kep.id).taken_at_override is None


def test_irasvedett_jpeg_override_et_kap_a_fajl_valtozatlan(
    controller, qt_app, tmp_path, library
):
    sor, kep = _sor(controller, "kep.jpg")
    forras = library / "kep.jpg"
    elotte = forras.read_bytes()
    library.chmod(0o555)  # az EXIF-írás .tmp cserét használ: könyvtár nem írható
    try:
        wait_for_photo_op(
            controller,
            lambda: controller.adjustPhotoDates(
                [sor], "2020-01-01 12:00:00", UJ_DATUM, False
            ),
            qt_app=qt_app,
        )
    finally:
        library.chmod(0o755)
    assert forras.read_bytes() == elotte
    with open_index(tmp_path / "index.db") as conn:
        assert photo_by_id(conn, kep.id).taken_at_override == UJ_DATUM
