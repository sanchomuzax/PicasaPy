"""A filmátmenetek közös renderútja a QML-előnézethez és az exporthoz."""

from __future__ import annotations

import json
import logging
import threading
from collections import OrderedDict
from pathlib import Path

import numpy as np
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from picasapy.app.collage_preview import rgb_to_qimage
from picasapy.app.formatting import to_local_path
from picasapy.movie.slideshow import (
    MovieSettings,
    _atmeneti_kocka,
    _decode,
    _fotofelirat,
    _picasa_caption,
    _szovegdia,
    crop_to_fit,
    letterbox,
)
from picasapy.lazy_cv2 import cv2

_log = logging.getLogger(__name__)
_PROVIDER_URL = "image://moviepreview/frame?rev={}"
_FRAME_CACHE_LIMIT = 4
_PREVIEW_LONG_EDGE = 640


class MovieTransitionPreviewProvider(QQuickImageProvider):
    """Az export képkockáját adja a filmkészítő élő átmenet-előnézetéhez."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._lock = threading.RLock()
        self._image = QImage(1, 1, QImage.Format.Format_RGB888)
        self._image.fill(0)
        self._revision = 0
        self._frames: OrderedDict[tuple, np.ndarray] = OrderedDict()

    def render_transition(
        self,
        outgoing_source: str,
        incoming_source: str,
        transition: str,
        progress: float,
        width: int,
        height: int,
        cropfit: bool,
        show_captions: bool,
        show_dates: bool,
        outgoing_slide_json: str,
        incoming_slide_json: str,
        actual_size: bool,
    ) -> str:
        """Képkockát készít a slideshow ugyanazon átmenetfüggvényével."""
        render_width, render_height = _preview_size(width, height, actual_size)
        settings = MovieSettings(
            width=render_width,
            height=render_height,
            cropfit=cropfit,
            show_captions=show_captions,
            show_dates=show_dates,
        )
        try:
            outgoing = self._input_frame(
                outgoing_source,
                outgoing_slide_json,
                settings,
            )
            incoming = self._input_frame(
                incoming_source,
                incoming_slide_json,
                settings,
            )
            frame = _atmeneti_kocka(outgoing, incoming, transition, progress)
        except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError):
            _log.exception("A filmátmenet előnézeti képkockája nem készíthető el")
            frame = np.zeros((render_height, render_width, 3), dtype=np.uint8)

        image = rgb_to_qimage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        with self._lock:
            self._image = image
            self._revision += 1
            revision = self._revision
        return _PROVIDER_URL.format(revision)

    def _input_frame(
        self,
        source: str,
        slide_json: str,
        settings: MovieSettings,
    ) -> np.ndarray:
        slide = json.loads(slide_json) if slide_json else None
        if slide is not None:
            key = (
                "slide",
                slide_json,
                settings.width,
                settings.height,
            )
            return self._cached_frame(
                key, lambda: _szovegdia(slide, settings)
            )

        local_path = to_local_path(source)
        if not local_path:
            raise ValueError("A filmátmenet egyik képkockájának nincs forrása")
        path = Path(local_path)
        key = (
            "photo",
            str(path),
            path.stat().st_mtime_ns if path.exists() else None,
            settings.width,
            settings.height,
            settings.cropfit,
            settings.show_captions,
            settings.show_dates,
        )

        def create() -> np.ndarray:
            image = _decode(path)
            frame = (
                crop_to_fit(image, settings.width, settings.height)
                if settings.cropfit
                else letterbox(image, settings.width, settings.height)
            )
            caption = _picasa_caption(path, {}) if settings.show_captions else ""
            return _fotofelirat(frame, path, settings, caption)

        return self._cached_frame(key, create)

    def _cached_frame(self, key: tuple, create) -> np.ndarray:
        with self._lock:
            cached = self._frames.get(key)
            if cached is not None:
                self._frames.move_to_end(key)
                return cached
        frame = create()
        with self._lock:
            existing = self._frames.get(key)
            if existing is not None:
                return existing
            self._frames[key] = frame
            while len(self._frames) > _FRAME_CACHE_LIMIT:
                self._frames.popitem(last=False)
        return frame

    def requestImage(self, image_id, size, requested_size):  # noqa: N802 (Qt API)
        with self._lock:
            image = self._image
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


def _preview_size(width: int, height: int, actual_size: bool) -> tuple[int, int]:
    width = max(2, int(width)) // 2 * 2
    height = max(2, int(height)) // 2 * 2
    longest_edge = max(width, height)
    if actual_size or longest_edge <= _PREVIEW_LONG_EDGE:
        return width, height
    scale = _PREVIEW_LONG_EDGE / longest_edge
    scaled_width = max(2, round(width * scale)) // 2 * 2
    scaled_height = max(2, round(height * scale)) // 2 * 2
    return scaled_width, scaled_height


__all__ = ["MovieTransitionPreviewProvider"]
