"""Feltételes QML-képvárakozások a #4058 kiegyenesítési próbáihoz."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QSignalSpy, QTest

from tests.support.varakozas import var_feltetelre


def _pont(item, x: float, y: float) -> QPoint:
    point = item.mapToScene(QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _felvetel(window, utvonal: Path) -> QImage:
    kep = window.grabWindow()
    assert not kep.isNull(), "a néző ablaka nem rajzolódott ki"
    assert kep.save(str(utvonal), "PNG"), f"nem menthető a felvétel: {utvonal}"
    return kep


def _felvetel_kirajzolas_utan(window, qt_app, utvonal: Path) -> QImage:
    """A következő QQuickWindow-képkocka után készít képet."""
    frames = QSignalSpy(window.frameSwapped)
    window.update()
    assert var_feltetelre(qt_app, lambda: frames.count() > 0, 3.0), (
        "a felületi állapotváltás utáni képkocka nem rajzolódott ki"
    )
    return _felvetel(window, utvonal)


def _kep_betoltve(image) -> bool:
    """A QML Image betöltése kész, és már van forrásmérete."""
    size = image.property("sourceSize")
    return (
        image.property("progress") == 1.0
        and size.width() > 0
        and size.height() > 0
    )


def _forrasra_var(
    image, qt_app, forras_elotte: str, cel_forras: str, leiras: str
) -> None:
    assert var_feltetelre(
        qt_app,
        lambda: image.property("source").toString() == cel_forras
        and cel_forras != forras_elotte
        and _kep_betoltve(image),
        10.0,
    ), (
        f"{leiras}: a kép új forrása nem töltődött be; "
        f"előtte={forras_elotte!r}, most={image.property('source')!r}, "
        f"várt={cel_forras!r}, betöltés={image.property('progress')}"
    )


def _tilt_huzasa_egerrel(
    window, qt_app, slider, *, preview_image=None, preview_controller=None
) -> None:
    kezdo = _pont(slider, slider.width() / 2, slider.height() / 2)
    veg = _pont(slider, slider.width() * 0.78, slider.height() / 2)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kezdo)
    assert var_feltetelre(
        qt_app, lambda: slider.property("pressed") is False, 3.0
    ), "az előző próba lenyomva hagyta az egeret"
    slider.setProperty("value", 0.0)
    assert var_feltetelre(
        qt_app, lambda: float(slider.property("value")) == 0.0, 3.0
    ), "a csúszka nem a nulla kiindulóértéken áll"
    forras_elotte = (
        preview_image.property("source").toString()
        if preview_image is not None
        else ""
    )
    try:
        QTest.mouseMove(window, kezdo, 10)
        QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kezdo)
        assert var_feltetelre(
            qt_app, lambda: slider.property("pressed") is True, 3.0
        ), "az egérlenyomás nem érte el a csúszkát"
        koztes = _pont(slider, slider.width() * 0.62, slider.height() / 2)
        QTest.mouseMove(window, koztes, 10)
        assert var_feltetelre(
            qt_app,
            lambda: slider.property("pressed") is True
            and abs(float(slider.property("value"))) > 0.1,
            3.0,
        ), "a csúszka nem vette át a köztes húzást"
        QTest.mouseMove(window, veg, 10)
        assert var_feltetelre(
            qt_app,
            lambda: slider.property("pressed") is True
            and abs(float(slider.property("value"))) >= 0.2,
            3.0,
        ), "a csúszka elengedte a végpont előtt, vagy nem változott az értéke"
    finally:
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, veg)
        assert var_feltetelre(
            qt_app, lambda: slider.property("pressed") is False, 3.0
        ), "a csúszka nem engedte el az egeret"
    if preview_image is not None:
        _forrasra_var(
            preview_image,
            qt_app,
            forras_elotte,
            str(preview_controller.property("previewSource")),
            "a kiegyenesítés előnézete",
        )
        frames = QSignalSpy(window.frameSwapped)
        window.update()
        assert var_feltetelre(qt_app, lambda: frames.count() > 0, 3.0), (
            "a kiegyenesítés új képkockája nem rajzolódott ki"
        )
