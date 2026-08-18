"""Élő kollázs-előnézet képszolgáltatója (#920).

A Kollázs nálunk eddig **vakon** dolgozott: a párbeszédben ki kellett
választani az elrendezést és a keretet, majd a program egyben kirenderelte
a képet fájlba — a felhasználó csak utána látta, mit kapott. Az eredetiben
a panel jobb oldalán **élő vászon** áll, amin a kollázs azonnal látszik.

Ez a modul az első lépcső: egyetlen, rendereletlen QImage-et tart, amit a
`create_controller` frissít, és amit a QML az

    image://collagepreview/kollazs?rev=<n>

URL-lel kér le. A `rev` csak gyorsítótár-törésre való — a Qt különben nem
töltené újra ugyanazt az URL-t.

**Miért nem a meglévő `EditPreviewProvider`:** az fotó-azonosítóra kulcsolt,
LRU-tárakkal és szerkesztő-specifikus mellékágakkal (hisztogram, GPU-prefix)
dolgozik. A kollázsnak egyetlen, kompozit előnézete van, ami nem tartozik
egyetlen fotóhoz sem — külön, kicsi szolgáltató kevesebbet hazudik a
szándékról, mint egy idegen fogalomra ráhúzott.
"""

from __future__ import annotations

import threading

import numpy as np
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


def rgb_to_qimage(image: np.ndarray) -> QImage:
    """RGB `uint8` (H, W, 3) tömbből QImage, a puffer MÁSOLATÁVAL.

    A másolat nem elhagyható: a `QImage` nem birtokolja a numpy-puffert, és
    ha a tömb felszabadul, a Qt már felszabadított memóriát rajzolna.
    """
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"RGB képet várok (H, W, 3), kaptam: {image.shape}")
    height, width = image.shape[:2]
    contiguous = np.ascontiguousarray(image)
    return QImage(
        contiguous.data, width, height, 3 * width, QImage.Format.Format_RGB888
    ).copy()


class CollagePreviewProvider(QQuickImageProvider):
    """`image://collagepreview/<bármi>?rev=<n>` — a legutóbbi kollázs-előnézet."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._lock = threading.Lock()
        self._image: QImage | None = None

    def set_image(self, image: np.ndarray) -> None:
        """Az előnézet cseréje (háttérszálról is hívható)."""
        rendered = rgb_to_qimage(image)
        with self._lock:
            self._image = rendered

    def clear(self) -> None:
        with self._lock:
            self._image = None

    @property
    def has_image(self) -> bool:
        with self._lock:
            return self._image is not None

    def requestImage(self, image_id, size, requested_size):  # noqa: N802 (Qt API)
        with self._lock:
            image = self._image
        if image is None:
            # üres, 1×1-es kép: a QML `Image` így `Ready` állapotba kerül,
            # nem marad `Error`-ban — a hívó a `has_image`-ből tudja az igazat
            image = QImage(1, 1, QImage.Format.Format_RGB888)
            image.fill(0xFFFFFF)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


__all__ = ["CollagePreviewProvider", "rgb_to_qimage"]
