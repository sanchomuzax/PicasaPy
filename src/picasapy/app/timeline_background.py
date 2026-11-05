"""Az Időrend kiválasztott fotójának szürke, fedőképes háttere (#6577)."""

from __future__ import annotations

import threading
from collections import OrderedDict

from picasapy.lazy_cv2 import cv2
import numpy as np
from PySide6.QtCore import QSize, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtQuick import QQuickImageProvider

from picasapy.render.native_tone import native_gamma_lut
from picasapy.render.ops_levels import apply_enhance

_ALAP_SZELESSEG = 600
_ALAP_MAGASSAG = 480
_CACHE_KAPACITAS = 8


def _ellenoriz_rgb(image: np.ndarray) -> None:
    if (
        not isinstance(image, np.ndarray)
        or image.ndim != 3
        or image.shape[2] != 3
        or image.dtype != np.uint8
        or image.shape[0] == 0
        or image.shape[1] == 0
    ):
        shape = getattr(image, "shape", None)
        raise ValueError(f"RGB uint8 (H, W, 3) képet várok, kaptam: {shape}")


def _kozepre_meretez(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """A fotót aránytartva panelméretre tölti, majd középről vágja."""
    _ellenoriz_rgb(image)
    width, height = max(1, int(width)), max(1, int(height))
    source_height, source_width = image.shape[:2]
    scale = max(width / source_width, height / source_height)
    scaled_width = max(width, round(source_width * scale))
    scaled_height = max(height, round(source_height * scale))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    scaled = cv2.resize(
        image, (scaled_width, scaled_height), interpolation=interpolation
    )
    left = (scaled_width - width) // 2
    top = (scaled_height - height) // 2
    return scaled[top : top + height, left : left + width].copy()


def prepare_timeline_background(
    image: np.ndarray, width: int, height: int
) -> np.ndarray:
    """Középre illeszt, a zöld csatornából szürkít, enhance-ol és gammázik."""
    centered = _kozepre_meretez(image, width, height)
    green_gray = np.repeat(centered[:, :, 1:2], 3, axis=2)
    stretched = apply_enhance(green_gray)
    return native_gamma_lut(3.0)[stretched]


def _qimage_rgba_array(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    rows = raw.reshape((height, stride))
    return rows[:, : width * 4].reshape((height, width, 4)).copy()


# Az eredeti 640x480-as `overlays/overlay` réteg MÉRT értékei (#6577; mérési
# minta, a réteget magát nem használjuk): az oválison kívül átlátszatlan szürke,
# az ovális az egyetlen áttetsző rész, így a fotó csak azon át látszik.
_ALAP_SZURKE = (138, 138, 138, 255)
_OVALIS_SZIN = (52, 57, 68, 179)
_OVALIS_KOZEP = (432 / 640, 150 / 480)
_OVALIS_SUGAR = (366 / 640, 202 / 480)
_IV_SZIN = (153, 153, 153, 255)
_IV_PONTOK = (
    (14 / 640, 170 / 480),
    (16 / 640, 222 / 480),
    (30 / 640, 258 / 480),
    (60 / 640, 303 / 480),
    (120 / 640, 345 / 480),
    (200 / 640, 375 / 480),
    (232 / 640, 382 / 480),
)
_IV_VASTAGSAG = 8 / 640
# alsó sáv: (sor/480, szürkeszint) a mért függőleges menet szerint
_SAV_TETEJE = 400 / 480
_SAV_MENET = (
    (400, 138), (402, 184), (408, 211), (414, 201), (420, 196),
    (426, 189), (432, 173), (438, 154), (444, 166), (450, 186), (480, 186),
)


def _sima_iv(points: list[tuple[float, float]]) -> QPainterPath:
    """A mért pontokon áthaladó sima görbe (Catmull-Rom köbös Bézier-alakban)."""
    path = QPainterPath()
    path.moveTo(*points[0])
    for i in range(len(points) - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        path.cubicTo(*c1, *c2, *p2)
    return path


def _szurke(value: int, alpha: int = 255) -> QColor:
    return QColor(value, value, value, alpha)


def create_timeline_overlay(width: int, height: int) -> np.ndarray:
    """Saját rajzolású RGBA fedőréteg az eredeti réteg mért alakja és színei szerint."""
    width, height = max(1, int(width)), max(1, int(height))
    overlay = QImage(width, height, QImage.Format.Format_RGBA8888)
    overlay.fill(QColor(*_ALAP_SZURKE))

    painter = QPainter(overlay)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)

    # Halvány, világosabb ív a bal oldalon (az ovális alatt fut ki).
    arc = _sima_iv([(x * width, y * height) for x, y in _IV_PONTOK])
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(
        QPen(
            QColor(*_IV_SZIN),
            max(1.0, _IV_VASTAGSAG * width),
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.drawPath(arc)

    # Alsó, átlátszatlan sáv a mért függőleges színmenettel.
    band_top = _SAV_TETEJE * height
    gradient = QLinearGradient(0, band_top, 0, height)
    span = 480 - _SAV_MENET[0][0]
    for row, value in _SAV_MENET:
        gradient.setColorAt((row - _SAV_MENET[0][0]) / span, _szurke(value))
    painter.setBrush(gradient)
    painter.drawRect(QRectF(0, band_top, width, height - band_top))
    painter.end()
    rgba = _qimage_rgba_array(overlay)

    # Az ovális fedettségét külön maszkra rajzoljuk, és a színt meg az alfát
    # pontosan, előszorzás nélkül keverjük (a QPainter kerekítene).
    coverage = _ovalis_fedettseg(width, height, band_top)
    oval = np.array(_OVALIS_SZIN, dtype=np.float32)
    mixed = rgba.astype(np.float32) * (1.0 - coverage) + oval * coverage
    return np.rint(mixed).astype(np.uint8)


def _ovalis_fedettseg(width: int, height: int, band_top: float) -> np.ndarray:
    mask = QImage(width, height, QImage.Format.Format_Grayscale8)
    mask.fill(0)
    painter = QPainter(mask)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255))
    cx, cy = _OVALIS_KOZEP[0] * width, _OVALIS_KOZEP[1] * height
    rx, ry = _OVALIS_SUGAR[0] * width, _OVALIS_SUGAR[1] * height
    painter.drawEllipse(QRectF(cx - rx, cy - ry, 2 * rx, 2 * ry))
    painter.end()
    stride = mask.bytesPerLine()
    raw = np.frombuffer(bytes(mask.constBits()), dtype=np.uint8)
    cover = raw.reshape((height, stride))[:, :width].astype(np.float32) / 255.0
    # az alsó sáv az ovális fölé kerül
    cover[int(np.ceil(band_top)):, :] = 0.0
    return cover[:, :, None]


def _rafed(image: np.ndarray, overlay: np.ndarray) -> np.ndarray:
    alpha = overlay[:, :, 3:4].astype(np.uint16)
    base = image.astype(np.uint16)
    color = overlay[:, :, :3].astype(np.uint16)
    return (
        (base * (255 - alpha) + color * alpha + 127) // 255
    ).astype(np.uint8)


def render_timeline_background(
    image: np.ndarray, width: int, height: int
) -> np.ndarray:
    """A négy képfeldolgozó lépés után a saját rajzú fedőképet keveri rá."""
    prepared = prepare_timeline_background(image, width, height)
    return _rafed(prepared, create_timeline_overlay(width, height))


def _qimage_rgb_array(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    return raw.reshape((height, stride))[:, : width * 3].reshape(
        (height, width, 3)
    ).copy()


def _rgb_qimage(image: np.ndarray) -> QImage:
    contiguous = np.ascontiguousarray(image)
    height, width = contiguous.shape[:2]
    return QImage(
        contiguous.data,
        width,
        height,
        width * 3,
        QImage.Format.Format_RGB888,
    ).copy()


class TimelineBackgroundProvider(QQuickImageProvider):
    """A bélyegkép-szolgáltatóból kér képet és a háttér eredményét gyorsítótárazza."""

    def __init__(self, thumbnail_provider) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._thumbnail_provider = thumbnail_provider
        self._lock = threading.Lock()
        self._cache: OrderedDict[tuple[str, int, int], QImage] = OrderedDict()

    def requestImage(self, image_id, size, requested_size):  # noqa: N802 (Qt API)
        width = requested_size.width() if requested_size is not None else 0
        height = requested_size.height() if requested_size is not None else 0
        width = width if width > 0 else _ALAP_SZELESSEG
        height = height if height > 0 else _ALAP_MAGASSAG
        key = (str(image_id), width, height)

        with self._lock:
            image = self._cache.get(key)
            if image is None:
                source_size = QSize()
                source = self._thumbnail_provider.requestImage(
                    str(image_id), source_size, QSize()
                )
                if source.isNull():
                    return QImage()
                rendered = render_timeline_background(
                    _qimage_rgb_array(source), width, height
                )
                image = _rgb_qimage(rendered)
                self._cache[key] = image
                while len(self._cache) > _CACHE_KAPACITAS:
                    self._cache.popitem(last=False)
            else:
                self._cache.move_to_end(key)

        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image.copy()
