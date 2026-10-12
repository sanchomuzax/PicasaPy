"""#4541: a detektált szemek keretei kirajzolódnak és valódi kattintással törölhetők."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPen

_AUTO_EYES = ((0.25, 0.4, 0.1), (0.7, 0.6, 0.05))


def _varj_feltetelre(qt_app, feltetel, hatarido_masodperc: float = 3.0) -> bool:
    vege = time.monotonic() + hatarido_masodperc
    while time.monotonic() < vege:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _visualis_gyerekek(item):
    for child in item.childItems():
        yield child
        yield from _visualis_gyerekek(child)


def _auto_keretek(window):
    return [
        item for item in _visualis_gyerekek(window.contentItem())
        if item.objectName() == "redeyeRegionFrame"
    ]


def _kattints(qt_app, window, item, pont: QPointF | None = None) -> None:
    if pont is None:
        pont = QPointF(float(item.width()) / 2, float(item.height()) / 2)
    globalis = item.mapToScene(pont)
    for tipus in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        qt_app.sendEvent(
            window,
            QMouseEvent(
                tipus,
                globalis,
                globalis,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton
                if tipus == QEvent.Type.MouseButtonPress
                else Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            ),
        )
    qt_app.processEvents()


def _varhato_negyzet(eye, overlay):
    x, y, radius = eye
    width = float(overlay.property("width"))
    height = float(overlay.property("height"))
    scale = min(width, height)
    left = max(0.0, x - radius * scale / width)
    top = max(0.0, y - radius * scale / height)
    right = min(1.0, x + radius * scale / width)
    bottom = min(1.0, y + radius * scale / height)
    return left * width, top * height, (right - left) * width, (bottom - top) * height


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_auto_keretek_kirajzolasa_kattintas_reset_es_ujrafuttatas(
    qml_app, qt_app, tmp_path, monkeypatch, magassag_elteres
):
    window, _app_controller, _engine = qml_app
    eredeti_magassag = int(window.height())
    window.resize(int(window.width()), eredeti_magassag + magassag_elteres)
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    assert _varj_feltetelre(qt_app, lambda: viewer.property("editCtl") is not None)

    controller = viewer.property("editCtl")
    automatikus_futasok = []

    def talalatok(*_args):
        automatikus_futasok.append(True)
        return 2, _AUTO_EYES, (320, 160), (320, 160), ((1, 0, 0), (0, 1, 0))

    monkeypatch.setattr(
        controller._provider, "redeye_auto_result_with_size", talalatok
    )
    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("redeyeActive", True)
    assert _varj_feltetelre(qt_app, lambda: controller.redeyeRegionCount == 2)
    assert len(automatikus_futasok) == 1

    auto_button = window.findChild(QObject, "redeyeAutoButton")
    assert auto_button is not None
    assert auto_button.property("buttonEnabled") is False

    overlay = window.findChild(QObject, "redeyeOverlay")
    drag_area = window.findChild(QObject, "redeyeDragArea")
    assert overlay is not None and drag_area is not None
    frames = _auto_keretek(window)
    assert len(frames) == 2, "az automatikusan talált szemeknek is kell négyzet"

    varhato = [_varhato_negyzet(eye, overlay) for eye in _AUTO_EYES]
    tenyleges = []
    for frame in frames:
        pont = frame.mapToItem(overlay, QPointF(0, 0))
        tenyleges.append(
            (pont.x(), pont.y(), float(frame.width()), float(frame.height()))
        )
    for actual, expected in zip(tenyleges, varhato, strict=True):
        assert actual == pytest.approx(expected, abs=3.0)

    rendered = window.grabWindow()
    assert not rendered.isNull(), "a néző renderelt képe üres"
    rendered_path = tmp_path / "redeye-auto-4541-rendered.png"
    assert rendered.save(str(rendered_path))

    # A referencia a detektor két normált szemköréből számított négyzet.
    # A képpont-ellenőrzés csak a képrétegen fut, távol a feliratoktól.
    rendered_rgb = rendered.convertToFormat(QImage.Format.Format_RGB32)
    origin = overlay.mapToItem(window.contentItem(), QPointF(0, 0))
    dpr = rendered.devicePixelRatio()
    actual_color = QColor("#83a7bd")  # Theme.selectionBlue világos témában
    overlay_x = round(origin.x() * dpr)
    overlay_y = round(origin.y() * dpr)
    overlay_width = round(float(overlay.property("width")) * dpr)
    overlay_height = round(float(overlay.property("height")) * dpr)
    rendered_overlay = rendered_rgb.copy(
        overlay_x, overlay_y, overlay_width, overlay_height
    )
    assert not rendered_overlay.isNull(), "az átfedő képterület nem vágható ki"

    reference = QImage(
        overlay_width, overlay_height, QImage.Format.Format_RGB32
    )
    reference.fill(QColor(254, 0, 0))
    painter = QPainter(reference)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    painter.setPen(QPen(actual_color, 1))
    for expected in varhato:
        painter.drawRect(
            QRectF(
                expected[0] * dpr,
                expected[1] * dpr,
                expected[2] * dpr - 1,
                expected[3] * dpr - 1,
            )
        )
    painter.end()
    reference_path = tmp_path / "redeye-auto-4541-reference.png"
    assert reference.save(str(reference_path))
    assert rendered_overlay.save(str(rendered_path.with_name("redeye-auto-4541-overlay.png")))
    comparison = QImage(
        overlay_width * 2, overlay_height, QImage.Format.Format_RGB32
    )
    comparison.fill(QColor(35, 35, 35))
    painter = QPainter(comparison)
    painter.drawImage(0, 0, reference)
    painter.drawImage(overlay_width, 0, rendered_overlay)
    painter.end()
    assert comparison.save(str(tmp_path / "redeye-auto-4541-comparison.png"))

    for expected in varhato:
        x = round((origin.x() + expected[0] + expected[2] / 2) * dpr)
        y = round((origin.y() + expected[1]) * dpr)
        matching = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                pixel = rendered_rgb.pixelColor(x + dx, y + dy)
                if (
                    abs(pixel.red() - actual_color.red()) <= 12
                    and abs(pixel.green() - actual_color.green()) <= 12
                    and abs(pixel.blue() - actual_color.blue()) <= 12
                ):
                    matching += 1
        assert matching > 0, "a keret színe nem jelenik meg a renderelt képen"

    frame_to_remove = frames[0]
    kattintas = frame_to_remove.mapToItem(
        drag_area,
        QPointF(float(frame_to_remove.width()) / 2,
                float(frame_to_remove.height()) / 2),
    )
    _kattints(qt_app, window, drag_area, kattintas)
    assert controller.redeyeRegionCount == 1
    assert len(_auto_keretek(window)) == 1
    assert auto_button.property("buttonEnabled") is True

    reset_button = window.findChild(QObject, "redeyeResetButton")
    assert reset_button is not None
    assert reset_button.property("buttonEnabled") is True
    _kattints(qt_app, window, reset_button)
    assert _varj_feltetelre(qt_app, lambda: controller.redeyeRegionCount == 0)

    redo_message = window.findChild(QObject, "redeyeAutoRedoLabel")
    assert redo_message is not None and redo_message.property("visible") is True
    assert auto_button.property("buttonEnabled") is True
    _kattints(qt_app, window, auto_button)
    assert _varj_feltetelre(qt_app, lambda: len(automatikus_futasok) == 2)
    assert controller.redeyeRegionCount == 2
    assert auto_button.property("buttonEnabled") is False
    assert redo_message.property("visible") is False
