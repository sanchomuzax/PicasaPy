"""A néző arcrétege a mellőzött/érvénytelen arcot elrejti, a mentettet kirajzolja.

A próba a teljes nézőablak renderéből számolja meg a halványszürke kereteket;
nem csak a `facesFor()` visszatérési értékét olvassa.
"""

from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import QObject, QPointF
from PySide6.QtGui import QImage
import pytest

from picasapy.ini.rect64 import Rect64, encode_rect64


def _rgb_tomb(image: QImage) -> np.ndarray:
    rgb = image.convertToFormat(QImage.Format.Format_RGB888)
    sor = np.frombuffer(bytes(rgb.constBits()), dtype=np.uint8).reshape(
        rgb.height(), rgb.bytesPerLine()
    )
    return sor[:, : rgb.width() * 3].reshape(
        rgb.height(), rgb.width(), 3
    ).copy()


def test_viewer_renders_only_named_face(qml_app, qt_app, tmp_path):
    named = encode_rect64(Rect64(0.08, 0.12, 0.28, 0.40))
    ignored = encode_rect64(Rect64(0.38, 0.12, 0.58, 0.40))
    zero_contact = encode_rect64(Rect64(0.68, 0.12, 0.88, 0.40))
    ini = tmp_path / "kepek" / ".picasa.ini"
    ini.write_text(
        "[Contacts2]\n"
        "8e62b2035b74b477=Kis Éva;;\n"
        "[a.jpg]\n"
        f"faces=rect64({named}),8e62b2035b74b477;"
        f"rect64({ignored}),ffffffffffffffff;"
        f"rect64({zero_contact}),0\n",
        encoding="utf-8",
    )
    window, _controller, _engine = qml_app
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    viewer.setProperty("facesVisible", True)
    qt_app.processEvents()

    overlay = window.findChild(QObject, "facesOverlay")
    assert overlay is not None
    image = window.grabWindow()
    assert not image.isNull(), "a nézőablak képe nem rajzolódott ki"
    assert image.save(str(tmp_path / "faces-overlay.png"))

    origin = overlay.mapToItem(window.contentItem(), QPointF(0, 0))
    x0, y0 = round(origin.x()), round(origin.y())
    overlay_width = float(overlay.property("width"))
    overlay_height = float(overlay.property("height"))
    x1, y1 = x0 + round(overlay_width), y0 + round(overlay_height)
    layer = _rgb_tomb(image)[y0:y1, x0:x1]
    # A #4572 referenciájának keretszíne #d0d1d0. A fénykép tesztképe piros,
    # így a halványszürke tartomány csak a megjelenített kerethez tartozik.
    pale_gray = (
        (np.abs(layer[:, :, 0].astype(np.int16) - 208) <= 24)
        & (np.abs(layer[:, :, 1].astype(np.int16) - 209) <= 24)
        & (np.abs(layer[:, :, 2].astype(np.int16) - 208) <= 24)
    ).astype(np.uint8)
    _component_count, _labels, stats, _centers = cv2.connectedComponentsWithStats(
        pale_gray, connectivity=8
    )
    frames = [row for row in stats[1:] if row[cv2.CC_STAT_AREA] > 20]

    assert len(frames) == 1, f"a kirajzolt réteg {len(frames)} keretet tartalmaz"
    left, top, width, height, _area = frames[0]
    assert left / overlay_width == pytest.approx(0.08, abs=0.02)
    assert top / overlay_height == pytest.approx(0.12, abs=0.02)
    assert (left + width) / overlay_width == pytest.approx(0.28, abs=0.02)
    assert (top + height) / overlay_height == pytest.approx(0.40, abs=0.02)
    assert len(overlay.property("faces")) == 1

    add_name = window.findChild(QObject, "faceDraftAddName")
    assert add_name is not None
    assert add_name.property("visible") is False


# rontás-kontroll: a `facesFor()` szűrésének kikapcsolása → 3 keret / 3 komponens → 1 failed.
