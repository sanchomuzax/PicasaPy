"""A filmátmenetek aszinkron, az exporttal közös előnézeti renderútja."""

from __future__ import annotations

import json
import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PySide6.QtCore import QRunnable, QSize, QThreadPool, Signal
from PySide6.QtGui import QImage, QImageReader
from PySide6.QtQuick import QQuickImageProvider

from picasapy.app.collage_preview import rgb_to_qimage
from picasapy.app.formatting import to_local_path
from picasapy.app.worker_thread import register_pool_owner
from picasapy.lazy_cv2 import cv2
from picasapy.movie import (
    MovieSettings,
    decode_photo,
    prepare_photo_frame,
    render_text_slide,
    transition_frame,
)
from picasapy.scanner import PICASA_INI_NAME

_log = logging.getLogger(__name__)
_PROVIDER_URL = "image://moviepreview/frame?rev={}"
_FRAME_CACHE_LIMIT = 8
_PREVIEW_LONG_EDGE = 640


@dataclass(frozen=True)
class _TransitionRequest:
    generation: int
    outgoing_source: str
    incoming_source: str
    transition: str
    progress: float
    width: int
    height: int
    cropfit: bool
    show_captions: bool
    show_dates: bool
    outgoing_slide_json: str
    incoming_slide_json: str
    actual_size: bool
    viewport_width: int | None = None
    viewport_height: int | None = None
    device_pixel_ratio: float = 1.0


@dataclass(frozen=True)
class _PrefetchRequest:
    source: str
    slide_json: str
    settings: MovieSettings
    preview_size: tuple[int, int]


class _TransitionJob(QRunnable):
    """Egy átmeneti képkocka előállítása a saját poolban."""

    def __init__(
        self, provider: MovieTransitionPreviewProvider, request: _TransitionRequest
    ) -> None:
        super().__init__()
        self._provider = provider
        self._request = request

    def run(self) -> None:
        try:
            frame = self._provider._render_request(self._request)
        except Exception as exc:  # noqa: BLE001 — a hibás kérés se akassza be a poolt
            self._provider._log_source_error(
                f"átmenet:{self._request.outgoing_source}->{self._request.incoming_source}",
                exc,
            )
            width, height = _preview_size(
                self._request.width,
                self._request.height,
                self._request.actual_size,
                self._request.viewport_width,
                self._request.viewport_height,
                self._request.device_pixel_ratio,
            )
            frame = np.zeros((height, width, 3), dtype=np.uint8)
        self._provider._finish_request(self._request.generation, frame)


class _FontWarmupJob(QRunnable):
    """A leggyakoribb betűfájl-keresés előkészítése a GUI-szálon kívül."""

    def run(self) -> None:
        try:
            render_text_slide(
                {"text": "PicasaPy", "font": "DejaVuSans", "size": 16},
                MovieSettings(width=320, height=240),
            )
        except Exception:  # noqa: BLE001 — a bemelegítés nem akadályozhatja a felületet
            _log.debug("A filmelőnézeti betű-bemelegítés nem sikerült", exc_info=True)


class _PrefetchJob(QRunnable):
    """A következő dia alapkockáját előre beolvassa ugyanabba a cache-be."""

    def __init__(
        self, provider: MovieTransitionPreviewProvider, request: _PrefetchRequest
    ) -> None:
        super().__init__()
        self._provider = provider
        self._request = request

    def run(self) -> None:
        try:
            self._provider._input_frame(
                self._request.source,
                self._request.slide_json,
                self._request.settings,
                self._request.preview_size,
            )
        except Exception as exc:  # noqa: BLE001 — előtöltés nem állíthatja meg az animációt
            self._provider._log_source_error(f"előtöltés:{self._request.source}", exc)


class MovieTransitionPreviewProvider(QQuickImageProvider):
    """A slideshow átmenetfüggvényével készülő, friss képkocka-szolgáltató."""

    frameReady = Signal(str, int)

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._lock = threading.RLock()
        self._image_lock = threading.Lock()
        self._image = QImage(1, 1, QImage.Format.Format_RGB888)
        self._image.fill(0)
        self._revision = 0
        self._frames: OrderedDict[tuple, np.ndarray] = OrderedDict()
        self._logged_sources: set[str] = set()
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(1)
        self._pool.setExpiryTimeout(30_000)
        self._generation = 0
        self._running = False
        self._pending: _TransitionRequest | None = None
        register_pool_owner(self)
        self._pool.start(_FontWarmupJob())

    def request_transition(
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
        viewport_width: int | None = None,
        viewport_height: int | None = None,
        device_pixel_ratio: float = 1.0,
    ) -> int:
        """Azonnal visszatér; a két alapképet és az átmenetet a pool készíti."""
        with self._lock:
            self._generation += 1
            generation = self._generation
            request = _TransitionRequest(
                generation,
                outgoing_source,
                incoming_source,
                transition,
                progress,
                width,
                height,
                cropfit,
                show_captions,
                show_dates,
                outgoing_slide_json,
                incoming_slide_json,
                actual_size,
                viewport_width,
                viewport_height,
                device_pixel_ratio,
            )
            if self._running:
                # A lassú képkockát a legfrissebb állapot váltja; a GUI nem
                # gyűjt felhalmozódó, már elavult animációs munkát.
                self._pending = request
            else:
                self._running = True
                self._pool.start(_TransitionJob(self, request))
        return generation

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
        viewport_width: int | None = None,
        viewport_height: int | None = None,
        device_pixel_ratio: float = 1.0,
    ) -> str:
        """Szinkron render-mag tesztekhez; a felület az aszinkron metódust hívja."""
        request = _TransitionRequest(
            0,
            outgoing_source,
            incoming_source,
            transition,
            progress,
            width,
            height,
            cropfit,
            show_captions,
            show_dates,
            outgoing_slide_json,
            incoming_slide_json,
            actual_size,
            viewport_width,
            viewport_height,
            device_pixel_ratio,
        )
        return self._store_frame(self._render_request(request))

    def prefetch_frame(
        self,
        source: str,
        slide_json: str,
        width: int,
        height: int,
        cropfit: bool,
        show_captions: bool,
        show_dates: bool,
        actual_size: bool,
        viewport_width: int,
        viewport_height: int,
        device_pixel_ratio: float,
    ) -> None:
        """A megadott dia alapképét betölti a következő átmenet előtt."""
        if not source and not slide_json:
            return
        settings = MovieSettings(
            width=width,
            height=height,
            cropfit=cropfit,
            show_captions=show_captions,
            show_dates=show_dates,
        )
        preview_size = _preview_size(
            width,
            height,
            actual_size,
            viewport_width,
            viewport_height,
            device_pixel_ratio,
        )
        request = _PrefetchRequest(source, slide_json, settings, preview_size)
        self._pool.start(_PrefetchJob(self, request))

    def _render_request(self, request: _TransitionRequest) -> np.ndarray:
        render_width, render_height = _preview_size(
            request.width,
            request.height,
            request.actual_size,
            request.viewport_width,
            request.viewport_height,
            request.device_pixel_ratio,
        )
        try:
            settings = MovieSettings(
                width=request.width,
                height=request.height,
                cropfit=request.cropfit,
                show_captions=request.show_captions,
                show_dates=request.show_dates,
            )
            outgoing = self._input_frame(
                request.outgoing_source,
                request.outgoing_slide_json,
                settings,
                (render_width, render_height),
            )
            incoming = self._input_frame(
                request.incoming_source,
                request.incoming_slide_json,
                settings,
                (render_width, render_height),
            )
            return transition_frame(
                outgoing, incoming, request.transition, request.progress
            )
        except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._log_source_error(
                f"átmenet:{request.outgoing_source}->{request.incoming_source}", exc
            )
            return np.zeros((render_height, render_width, 3), dtype=np.uint8)

    def _input_frame(
        self,
        source: str,
        slide_json: str,
        settings: MovieSettings,
        preview_size: tuple[int, int],
    ) -> np.ndarray:
        preview_width, preview_height = preview_size
        slide = json.loads(slide_json) if slide_json else None
        if slide is not None:
            key = (
                "slide",
                slide_json,
                settings.width,
                settings.height,
                preview_size,
            )
            return self._cached_frame(
                key,
                lambda: _resize_to_preview(
                    render_text_slide(slide, settings), preview_size
                ),
                source=f"dia:{slide_json}",
                size=preview_size,
            )

        local_path = to_local_path(source)
        if not local_path:
            raise ValueError("A filmátmenet egyik képkockájának nincs forrása")
        path = Path(local_path)
        try:
            modified = path.stat().st_mtime_ns
        except OSError:
            modified = None
        ini_path = path.parent / PICASA_INI_NAME
        try:
            ini_modified = ini_path.stat().st_mtime_ns
        except OSError:
            ini_modified = None
        key = (
            "photo",
            str(path),
            modified,
            ini_modified,
            settings.width,
            settings.height,
            preview_size,
            settings.cropfit,
            settings.show_captions,
            settings.show_dates,
            settings.background,
        )

        def create() -> np.ndarray:
            frame = prepare_photo_frame(
                path,
                settings,
                {},
                decoder=lambda photo_path: _decode_preview(
                    photo_path,
                    preview_width,
                    preview_height,
                    settings.cropfit,
                ),
            )
            return _resize_to_preview(frame, preview_size)

        return self._cached_frame(
            key,
            create,
            source=str(path),
            size=preview_size,
        )

    def _cached_frame(self, key, create, *, source: str, size) -> np.ndarray:
        with self._lock:
            if key in self._frames:
                self._frames.move_to_end(key)
                return self._frames[key]
        try:
            frame = create()
        except Exception as exc:  # noqa: BLE001 — a rossz kép maradjon helyben
            self._log_source_error(source, exc)
            width, height = size
            frame = np.zeros((height, width, 3), dtype=np.uint8)
        with self._lock:
            existing = self._frames.get(key)
            if existing is not None:
                return existing
            self._frames[key] = frame
            while len(self._frames) > _FRAME_CACHE_LIMIT:
                self._frames.popitem(last=False)
        return frame

    def _log_source_error(self, source: str, error: Exception) -> None:
        with self._lock:
            if source in self._logged_sources:
                return
            self._logged_sources.add(source)
        _log.warning("A filmelőnézeti forrás nem olvasható (%s): %s", source, error)

    def _finish_request(self, generation: int, frame: np.ndarray) -> None:
        next_request = None
        url = None
        with self._lock:
            # A régebbi kész kocka is hasznos köztes állapot. A QML monoton
            # generációszám alapján szűr, ezért a lassú render nem éhezteti ki.
            url = self._store_frame(frame)
            if self._pending is not None:
                next_request = self._pending
                self._pending = None
            else:
                self._running = False
        if url is not None:
            self.frameReady.emit(url, generation)
        if next_request is not None:
            self._pool.start(_TransitionJob(self, next_request))

    def _store_frame(self, frame: np.ndarray) -> str:
        image = rgb_to_qimage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        with self._image_lock:
            self._image = image
            self._revision += 1
            revision = self._revision
        return _PROVIDER_URL.format(revision)

    def wait_for_done(self, msecs: int = 10_000) -> bool:
        """A saját pool bevárása a teszt- és alkalmazáslebontáshoz."""
        return self._pool.waitForDone(msecs)

    def requestImage(self, image_id, size, requested_size):  # noqa: N802 (Qt API)
        with self._image_lock:
            image = self._image
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


def _decode_preview(
    path: Path, width: int, height: int, cropfit: bool
) -> np.ndarray:
    """A Qt képdekódere kicsinyítve olvas; a RAW képek a közös dekóderre esnek."""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    source_size = reader.size()
    if reader.canRead() and source_size.isValid():
        scale = (
            max(width / source_size.width(), height / source_size.height())
            if cropfit
            else min(width / source_size.width(), height / source_size.height())
        )
        scaled_size = QSize(
            max(1, round(source_size.width() * scale)),
            max(1, round(source_size.height() * scale)),
        )
        reader.setScaledSize(scaled_size)
        image = reader.read()
        if not image.isNull():
            rgb = image.convertToFormat(QImage.Format.Format_RGB888)
            bytes_per_line = rgb.bytesPerLine()
            rows = np.frombuffer(rgb.bits(), dtype=np.uint8).reshape(
                rgb.height(), bytes_per_line
            )
            pixels = rows[:, : rgb.width() * 3].reshape(
                rgb.height(), rgb.width(), 3
            ).copy()
            return cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR)
    return decode_photo(path, goal=max(width, height))


def _resize_to_preview(
    frame: np.ndarray, preview_size: tuple[int, int]
) -> np.ndarray:
    width, height = preview_size
    if frame.shape[1] == width and frame.shape[0] == height:
        return frame
    interpolation = (
        cv2.INTER_AREA
        if width < frame.shape[1] or height < frame.shape[0]
        else cv2.INTER_LINEAR
    )
    return cv2.resize(frame, (width, height), interpolation=interpolation)


def _preview_size(
    width: int,
    height: int,
    actual_size: bool,
    viewport_width: int | None = None,
    viewport_height: int | None = None,
    device_pixel_ratio: float = 1.0,
) -> tuple[int, int]:
    width = max(2, int(width))
    height = max(2, int(height))
    if actual_size:
        return width // 2 * 2, height // 2 * 2
    if viewport_width is not None and viewport_height is not None:
        dpr = max(0.5, float(device_pixel_ratio))
        max_width = max(2, round(viewport_width * dpr))
        max_height = max(2, round(viewport_height * dpr))
        aspect = width / height
        render_width = min(max_width, round(max_height * aspect))
        render_height = round(render_width / aspect)
        if render_height > max_height:
            render_height = max_height
            render_width = round(render_height * aspect)
        return max(2, render_width // 2 * 2), max(2, render_height // 2 * 2)

    width = width // 2 * 2
    height = height // 2 * 2
    longest_edge = max(width, height)
    if longest_edge <= _PREVIEW_LONG_EDGE:
        return width, height
    scale = _PREVIEW_LONG_EDGE / longest_edge
    scaled_width = max(2, round(width * scale)) // 2 * 2
    scaled_height = max(2, round(height * scale)) // 2 * 2
    return scaled_width, scaled_height


__all__ = ["MovieTransitionPreviewProvider"]
