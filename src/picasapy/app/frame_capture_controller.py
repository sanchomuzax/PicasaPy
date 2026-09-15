"""Képkocka mentése a videóból — az AppController szelete (#1838).

Az eredeti Picasa `movieeditpanel/capture_frame` gombja („Take Snapshot" /
**„Pillanatfelvétel készítése"**) az aktuális képkockát menti JPEG-ként a
**Rögzített videoklipek** mappába (`CCaptureFrame::CaptureFolder`) — abba,
amelyikbe a webkamera-felvétel is megy (`app/project_folder_names.py`).
A név felépítése és az egyediesítő mérve: `movie/frame_capture.py`.

## Amit ez a szelet eldönt

* **Melyik képkocka.** A felület a lejátszási pozíciót adja át
  ezredmásodpercben; a képkockát ebből a pozícióból dekódoljuk. Nem a
  megjelenített felületet mentjük ki: a videó-felület méretezett és
  esetleg átfedett, a dekódolt képkocka viszont a FÁJL saját felbontása.
* **Háttérben fut.** Egy nagy fájlban a keresés lassú lehet; a munka a
  `_start_background`-on megy, tehát a jobb-felső sarki jelzőn (#2966) is
  látszik. A dekódolás a `cv2`-t használja, ami a GIL-t elengedi.
* **A bukás nem néma.** Az eredeti négy állapotszöveget ad, köztük a
  `captureframeprog4`-et („Nem sikerült a képkocka rögzítése"); nálunk a
  `movieFrameCaptureFailed` jelzés hordozza ugyanezt.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.movie.frame_capture import kepkocka_alapneve, mentsd_a_kepkockat

logger = logging.getLogger(__name__)


def capture_folder(language: str | None = None) -> Path:
    """A célmappa: a Rögzített videoklipek a Képek/Picasa alatt.

    A meglévő (esetleg más nyelvű) alak nyer — ld.
    `project_folder_names.letezo_vagy_honos_mappa`. A mappát nem hozzuk
    létre itt: azt a mentés végzi, ha tényleg lesz mit beletenni.
    """
    from .collage_output import _felulet_nyelve
    from .movie_output import pictures_dir
    from .project_folder_names import ProjectFolderKind, letezo_vagy_honos_mappa

    nyelv = language or _felulet_nyelve()
    return letezo_vagy_honos_mappa(
        pictures_dir() / "Picasa", ProjectFolderKind.CAPTURED_VIDEOS, nyelv
    )


def dekodolj_kepkockat(video_utvonal: str | Path, position_ms: int):
    """A videó egy képkockája RGB `uint8` tömbként, a megadott pozícióból.

    `None`, ha a fájl nem nyitható meg vagy nincs ott képkocka — a hívó
    ebből ad hibajelzést, kivétel nélkül.
    """
    from picasapy.lazy_cv2 import cv2
    from picasapy.thumbs.cache import open_video

    # ⚠️ NEM saját `cv2.VideoCapture`: a #673 óta a videó-megnyitásnak
    # rögzített háttere van (FFMPEG kényszerítve, illetve sorosított
    # tartalék) — a projektben EGY ilyen út van, és ez az.
    kapu = open_video(Path(video_utvonal))
    try:
        if not kapu.isOpened():
            return None
        if position_ms > 0:
            kapu.set(cv2.CAP_PROP_POS_MSEC, float(position_ms))
        sikeres, kocka = kapu.read()
        if not sikeres or kocka is None:
            return None
        # a dekóder BGR-t ad, a mentő RGB-t vár (a projekt render-konvenciója)
        return kocka[..., ::-1].copy()
    finally:
        kapu.release()


class FrameCaptureMixin:
    """`captureMovieFrame` — a `movieeditpanel/capture_frame` párja."""

    #: a képkocka elkészült — a mentett fájl teljes útvonalával
    #: (`CCaptureFrame::captureframeprog3` üzenetének adata)
    movieFrameCaptured = Signal(str)
    #: nem sikerült (`CCaptureFrame::captureframeprog4`)
    movieFrameCaptureFailed = Signal()

    @Slot(int, int)
    def captureMovieFrame(self, row: int, position_ms: int) -> None:
        """A sorhoz tartozó videó egy képkockájának mentése.

        A sor kiválasztása ugyanazon a kapun megy, mint a vágásé
        (`_vago_sor`): fotóra hívva nem történik semmi.
        """
        felvetel = self._vago_sor(row)
        if felvetel is None:
            return
        video = Path(felvetel.folder_path) / felvetel.name
        alapnev = kepkocka_alapneve(video)
        pozicio = max(0, int(position_ms))

        def munka() -> None:
            try:
                kocka = dekodolj_kepkockat(video, pozicio)
                if kocka is None:
                    logger.warning("#1838: nem olvasható képkocka: %s", video)
                    self.movieFrameCaptureFailed.emit()
                    return
                cel = mentsd_a_kepkockat(kocka, capture_folder(), alapnev)
            except Exception:
                logger.exception("#1838: a képkocka mentése elbukott: %s", video)
                self.movieFrameCaptureFailed.emit()
                return
            self.movieFrameCaptured.emit(str(cel))

        self._start_background(munka, name="picasapy-capture-frame")


__all__ = ["FrameCaptureMixin", "capture_folder", "dekodolj_kepkockat"]
