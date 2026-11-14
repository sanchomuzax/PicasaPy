"""Az Időrend első vetített képének szürke címkártyája (#6920)."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter


def create_slideshow_label_card(
    source_image: QImage,
    collection_name: str,
    *,
    display_scale: float = 1.0,
) -> QImage:
    """Készítsen új QImage-et a specifikáció szerinti szürke címkártyából.

    A szürkítés a bináris 77/151/28-as luma-képletét, azután a
    `rint(255 * sqrt(i / 255))` LUT-ot és a 160/255-ös fekete fedést követi.
    A címet a kép közepére rajzolja; a betű 20 képernyőképpontos, ezért a
    forrásképre a QML-ben megjelenítő lépték reciprokával kerül.
    """
    if source_image.isNull():
        return QImage()

    source = source_image.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = source.width(), source.height()
    bytes_per_line = source.bytesPerLine()
    source_rows = np.frombuffer(
        source.constBits(), count=source.sizeInBytes(), dtype=np.uint8
    ).reshape(height, bytes_per_line)
    source_pixels = source_rows[:, : width * 4].reshape(height, width, 4)

    red = source_pixels[:, :, 0].astype(np.uint16)
    green = source_pixels[:, :, 1].astype(np.uint16)
    blue = source_pixels[:, :, 2].astype(np.uint16)
    luma = ((77 * red + 151 * green + 28 * blue) >> 8).astype(np.uint8)
    gamma_lut = np.rint(
        255.0 * np.sqrt(np.arange(256, dtype=np.float64) / 255.0)
    ).astype(np.uint8)
    gamma = gamma_lut[luma]
    gray = np.rint(gamma.astype(np.float64) * (95.0 / 255.0)).astype(np.uint8)

    output_pixels = np.empty((height, width, 4), dtype=np.uint8)
    output_pixels[:, :, :3] = gray[:, :, np.newaxis]
    output_pixels[:, :, 3] = 255
    result = QImage(
        output_pixels.tobytes(),
        width,
        height,
        width * 4,
        QImage.Format.Format_RGBA8888,
    ).copy()

    if collection_name:
        scale = float(display_scale)
        pixel_size = max(1, round(20.0 / scale)) if scale > 0 else 20
        painter = QPainter(result)
        font = QFont("Helvetica Neue")
        font.setStyleName("Medium Condensed")
        font.setPixelSize(pixel_size)
        painter.setFont(font)
        painter.setPen(QColor(207, 207, 207, 207))
        painter.drawText(
            QRect(0, 0, width, height),
            Qt.AlignmentFlag.AlignCenter,
            collection_name,
        )
        painter.end()

    return result
