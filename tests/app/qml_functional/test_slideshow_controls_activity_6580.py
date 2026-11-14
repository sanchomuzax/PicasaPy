"""#6580: a vetítő sávját csak nagy egérmozgás hozza elő."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QWindow
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre


def _objektum(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _vetites_indit(qml_app, qt_app, magassag_elteres: int = 0):
    window, _controller, _engine = qml_app
    window.show()
    window.requestActivate()
    celmagassag = window.height() + magassag_elteres
    QMetaObject.invokeMethod(
        window,
        "startSlideshow",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", -1),
        Q_ARG("QVariant", False),
    )
    show = _objektum(window, "slideshowView")
    window.setVisibility(QWindow.Visibility.Windowed)
    window.resize(window.width(), celmagassag)
    assert varj_feltetelre(
        qt_app, lambda: window.height() == celmagassag, 3.0
    ), f"az ablak magassága nem lett {celmagassag}: {window.height()}"
    assert varj_feltetelre(
        qt_app, lambda: show.property("visible") is True, 3.0
    ), "a diavetítés nem indult el"
    show.setProperty("playing", False)
    controls = _objektum(window, "slideshowControls")
    return window, show, controls


def _mozgas(window, qt_app, x: int, y: int) -> None:
    QTest.mouseMove(window, QPoint(x, y))
    qt_app.processEvents()


def _var_eltelt(qt_app, masodperc: float) -> None:
    hatarido = time.monotonic() + masodperc
    assert varj_feltetelre(
        qt_app, lambda: time.monotonic() >= hatarido, masodperc + 1.0
    ), f"nem telt el {masodperc} másodperc"


def _kepernyokep(window, nev: str) -> None:
    konyvtar = os.environ.get("PICASA_6580_CAPTURE_DIR")
    if not konyvtar:
        return
    cel = Path(konyvtar)
    cel.mkdir(parents=True, exist_ok=True)
    assert window.grabWindow().save(str(cel / nev), "PNG"), (
        f"nem menthető a vetítő képernyőképe: {cel / nev}"
    )


def _mozgas_alapoz(window, qt_app, controls, x: int, y: int) -> tuple[int, int]:
    """A tényleges mutatómozgástól és egy esetleges áttűnéstől induljon."""
    vegertek = 1 / 256
    _mozgas(window, qt_app, x, y)
    if controls.property("shown"):
        assert varj_feltetelre(
            qt_app, lambda: controls.property("shown") is False, 2.0
        ), "az előkészítő mozgás után nem indult el az elrejtés"
    assert varj_feltetelre(
        qt_app,
        lambda: float(controls.property("opacity")) <= vegertek + 0.001,
        1.8,
    ), "a sáv nem ért el rejtett állapotot"
    _var_eltelt(qt_app, 0.55)
    x += 60
    _mozgas(window, qt_app, x, y)
    assert controls.property("shown") is False, (
        "500 ms tétlenség után az új mutatóhely nem lett vonatkoztatási pont"
    )
    return x, y


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_a_50_pixeles_kuszob_es_a_fel_masodperces_ujraalapitas(
    qml_app, qt_app, magassag_elteres
):
    window, _show, controls = _vetites_indit(
        qml_app, qt_app, magassag_elteres
    )
    x, y = window.width() // 3, window.height() // 3
    x, y = _mozgas_alapoz(window, qt_app, controls, x, y)
    if magassag_elteres == 0:
        _kepernyokep(window, "slideshow-controls-hidden.png")

    _mozgas(window, qt_app, x + 30, y)
    assert controls.property("shown") is False, (
        "az 50 képpontnál kisebb mozdulat előhozta a sávot"
    )

    _mozgas(window, qt_app, x + 50, y)
    assert controls.property("shown") is False, (
        "az 50 képpontos mozdulat átlépte a szigorú küszöböt"
    )
    _mozgas(window, qt_app, x + 51, y)
    assert varj_feltetelre(
        qt_app, lambda: controls.property("shown") is True, 1.0
    ), "az 50 képpontnál nagyobb mozdulat nem hozta elő a sávot"
    assert varj_feltetelre(
        qt_app, lambda: float(controls.property("opacity")) >= 0.99, 1.0
    ), "a sáv nem jelent meg teljesen"
    if magassag_elteres == 0:
        _kepernyokep(window, "slideshow-controls-visible.png")


def test_a_sav_a_feletti_mutato_mellett_1500_ms_utan_is_kint_marad(
    qml_app, qt_app
):
    window, _show, controls = _vetites_indit(qml_app, qt_app)
    x, y = window.width() // 3, window.height() // 3
    x, y = _mozgas_alapoz(window, qt_app, controls, x, y)
    _mozgas(window, qt_app, x + 51, y)
    assert varj_feltetelre(
        qt_app, lambda: float(controls.property("opacity")) >= 0.99, 1.0
    ), "a küszöböt átlépő mozgás nem hozta elő a sávot"

    hide_timer = _objektum(window, "slideshowHideTimer")
    assert hide_timer.property("interval") == 1500, (
        "az elrejtés időzítője nem 1500 ms"
    )
    lebeges = _objektum(window, "slideshowControlsHover")
    kozep = controls.mapToScene(
        QPointF(controls.width() / 2, controls.height() / 2)
    )
    _mozgas(window, qt_app, round(kozep.x()), round(kozep.y()))
    assert varj_feltetelre(
        qt_app, lambda: lebeges.property("hovered") is True, 2.0
    ), "a mutató nem került a vezérlősáv fölé"

    _var_eltelt(qt_app, 1.7)
    assert controls.property("shown") is True, (
        "a sáv eltűnt, miközben a mutató fölötte maradt"
    )


def test_az_1500_ms_varakozas_es_a_250_1200_ms_atmenet(qml_app, qt_app):
    window, _show, controls = _vetites_indit(qml_app, qt_app)
    hide_timer = _objektum(window, "slideshowHideTimer")
    assert hide_timer.property("interval") == 1500, (
        "az elrejtés időzítője nem 1500 ms"
    )

    x, y = window.width() // 3, window.height() // 3
    x, y = _mozgas_alapoz(window, qt_app, controls, x, y)
    mozgas_kezdete = time.monotonic()
    _mozgas(window, qt_app, x + 51, y)
    assert varj_feltetelre(
        qt_app, lambda: float(controls.property("opacity")) >= 0.99, 1.0
    ), "a sáv áttűnéssel nem jelent meg"
    megjelenesi_ido = time.monotonic() - mozgas_kezdete
    assert 0.24 <= megjelenesi_ido <= 0.6, (
        f"a megjelenési áttűnés nem 250 ms körüli: {megjelenesi_ido:.3f} s"
    )

    assert varj_feltetelre(
        qt_app, lambda: controls.property("shown") is False, 2.2
    ), "1,5 s tétlenség után nem indult el a sáv eltűnése"
    eltunes_indul = time.monotonic()
    assert 1.4 <= eltunes_indul - mozgas_kezdete <= 1.8, (
        "az eltűnés nem 1500 ms tétlenség után indult: "
        f"{eltunes_indul - mozgas_kezdete:.3f} s"
    )

    assert varj_feltetelre(
        qt_app,
        lambda: float(controls.property("opacity")) <= (1 / 256) + 0.001,
        1.8,
    ), "az eltűnési áttűnés nem érte el az 1/256 átlátszatlanságot"
    eltunes_vege = time.monotonic()
    assert 1.1 <= eltunes_vege - eltunes_indul <= 1.6, (
        "az eltűnési áttűnés nem 1200 ms körüli: "
        f"{eltunes_vege - eltunes_indul:.3f} s"
    )
