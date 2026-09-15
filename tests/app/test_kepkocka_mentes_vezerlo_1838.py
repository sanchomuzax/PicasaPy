"""#1838: a `capture_frame` vezérlő-oldala — a videóból mentett képkocka.

A tiszta névadást és a `%s-%03lu` egyediesítőt a
`tests/movie/test_kepkocka_mentes_1838.py` méri; ez a lap a vezérlőt:
melyik sorra hajlandó dolgozni, hova ment, és mit tesz, ha nem sikerül.

A célmappa a **Rögzített videoklipek** (`CCaptureFrame::CaptureFolder`) —
ugyanaz, ahová a webkamera-felvétel menne (#853 szerint az kimarad, de a
mappa közös).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject

from picasapy.index import PhotoRecord


def _felvetel(mappa: Path, nev: str, kind: str = "video") -> PhotoRecord:
    return PhotoRecord(
        id=11,
        folder_path=str(mappa),
        name=nev,
        kind=kind,
        size=1000,
        mtime_ns=5,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
    )


class _Proba(QObject):
    def __init__(self, modell):
        super().__init__()
        self.photos = modell


@pytest.fixture
def keret(qt_app, tmp_path, monkeypatch):
    from picasapy.app import frame_capture_controller
    from picasapy.app.frame_capture_controller import FrameCaptureMixin
    from picasapy.app.models import PhotoGridModel
    from picasapy.app.movie_trim_controller import MovieTrimMixin
    from picasapy.app.worker_thread import BackgroundWorkerMixin

    class _Vezerlo(FrameCaptureMixin, MovieTrimMixin, BackgroundWorkerMixin, _Proba):
        pass

    celmappa = tmp_path / "Rögzített videoklipek"
    monkeypatch.setattr(frame_capture_controller, "capture_folder", lambda: celmappa)

    def epit(nev: str = "nyaralas.MP4", kind: str = "video"):
        modell = PhotoGridModel()
        modell.set_photos((_felvetel(tmp_path, nev, kind),))
        (tmp_path / nev).write_bytes(b"nem valodi video")
        return _Vezerlo(modell), celmappa

    return epit


def _varj(vezerlo, qt_app, timeout_s: float = 5.0) -> None:
    import time

    hatarido = time.monotonic() + timeout_s
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if not vezerlo.backgroundWorkersRunning():
            qt_app.processEvents()
            return
        time.sleep(0.005)
    raise AssertionError("a képkocka-mentés háttérszála nem állt le")


class TestKepkockaVezerlo:
    def test_fotora_nem_csinal_semmit(self, keret, qt_app):
        """A `capture_frame` videó-parancs; fényképre hívva nem indul munka."""
        vezerlo, celmappa = keret(nev="kep.jpg", kind="photo")
        vezerlo.captureMovieFrame(0, 1000)
        _varj(vezerlo, qt_app)
        assert not celmappa.exists()

    def test_ervenytelen_sorra_nem_csinal_semmit(self, keret, qt_app):
        vezerlo, celmappa = keret()
        vezerlo.captureMovieFrame(7, 1000)
        _varj(vezerlo, qt_app)
        assert not celmappa.exists()

    def test_olvashatatlan_video_eseten_HIBAT_JELEZ(self, keret, qt_app):
        """A fájl nem valódi videó — a bukás nem lehet néma."""
        vezerlo, celmappa = keret()
        hibak = []
        vezerlo.movieFrameCaptureFailed.connect(lambda: hibak.append(1))
        vezerlo.captureMovieFrame(0, 0)
        _varj(vezerlo, qt_app)
        assert hibak == [1]
        assert not celmappa.exists()

    def test_sikeres_mentes_a_celmappaba_megy(self, keret, qt_app, monkeypatch):
        from picasapy.app import frame_capture_controller

        kocka = np.zeros((6, 8, 3), dtype=np.uint8)
        monkeypatch.setattr(
            frame_capture_controller, "dekodolj_kepkockat", lambda *_: kocka
        )
        vezerlo, celmappa = keret()
        kesz = []
        vezerlo.movieFrameCaptured.connect(kesz.append)
        vezerlo.captureMovieFrame(0, 2500)
        _varj(vezerlo, qt_app)
        assert len(kesz) == 1
        mentett = Path(kesz[0])
        assert mentett.parent == celmappa
        assert mentett.name == "nyaralas.jpg"
        assert mentett.exists()

    def test_a_masodik_mentes_sorszamot_kap(self, keret, qt_app, monkeypatch):
        from picasapy.app import frame_capture_controller

        kocka = np.zeros((6, 8, 3), dtype=np.uint8)
        monkeypatch.setattr(
            frame_capture_controller, "dekodolj_kepkockat", lambda *_: kocka
        )
        vezerlo, celmappa = keret()
        kesz = []
        vezerlo.movieFrameCaptured.connect(kesz.append)
        vezerlo.captureMovieFrame(0, 0)
        _varj(vezerlo, qt_app)
        vezerlo.captureMovieFrame(0, 1000)
        _varj(vezerlo, qt_app)
        assert [Path(ut).name for ut in kesz] == ["nyaralas.jpg", "nyaralas-001.jpg"]

    def test_a_pozicio_eljut_a_dekoderig(self, keret, qt_app, monkeypatch):
        from picasapy.app import frame_capture_controller

        latott = []

        def hamis(utvonal, position_ms):
            latott.append(position_ms)
            return np.zeros((4, 4, 3), dtype=np.uint8)

        monkeypatch.setattr(frame_capture_controller, "dekodolj_kepkockat", hamis)
        vezerlo, _ = keret()
        vezerlo.captureMovieFrame(0, 12_345)
        _varj(vezerlo, qt_app)
        assert latott == [12_345]
