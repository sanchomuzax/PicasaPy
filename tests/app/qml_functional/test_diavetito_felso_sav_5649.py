"""#5649: a vetítő tetején levő kattintósáv a lejátszás gombot követi."""

# rontás-kontroll: SlideshowView.qml#slideshowAuto2Area = kihagyva → 3 failed

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg

#: a kiadáskép csak kérésre készül (a mappát a hívó adja meg); a teszt
#: magától nem ír a gyökérkönyvtáron kívülre
KIADASKEP_MAPPA = "PICASAPY_KIADASKEP_MAPPA"


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Mintázatos tesztképekkel: a kiadásképen valódi kép látszik (agent #225)."""

    def kepek(lib):
        make_minta_jpeg(lib / "a.jpg", size=(1280, 720), seed=11)
        make_minta_jpeg(lib / "b.jpg", size=(1280, 720), seed=12)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepek,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _gyerek(window, nev: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem: QQuickItem) -> None:
    """Valódi kattintás az elem aktuális, ablakra leképzett közepén."""
    pont = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _annotalt_kiadas_kep(window, sav: QQuickItem, mappa: Path) -> Path:
    """A tényleges vetítőképen kiemeli a felső kattintósáv helyét."""
    kep = window.grabWindow()
    assert not kep.isNull(), "a vetítő kiadásképe üres"
    arany = kep.devicePixelRatio()
    bal_fel = sav.mapToScene(QPointF(0, 0))
    jobb_lent = sav.mapToScene(QPointF(sav.width(), sav.height()))
    sav_rect = kep.rect().adjusted(0, 0, 0, 0)
    sav_rect.setLeft(round(bal_fel.x() * arany))
    sav_rect.setTop(round(bal_fel.y() * arany))
    sav_rect.setRight(round(jobb_lent.x() * arany) - 1)
    sav_rect.setBottom(round(jobb_lent.y() * arany) - 1)

    festo = QPainter(kep)
    festo.setBrush(QColor(255, 196, 0, 54))
    festo.setPen(QPen(QColor("#ffd400"), max(1, round(2 * arany))))
    festo.drawRect(sav_rect)
    betu = QFont("Sans Serif")
    betu.setPixelSize(max(12, round(14 * arany)))
    festo.setFont(betu)
    szoveg = "Felső auto2 kattintósáv · 14 px"
    szoveg_rect = festo.fontMetrics().boundingRect(szoveg)
    szoveg_rect.moveTopLeft(
        QPoint(round(12 * arany), round((sav.height() + 10) * arany))
    )
    festo.fillRect(
        szoveg_rect.adjusted(-5, -3, 5, 3), QColor(0, 0, 0, 190)
    )
    festo.setPen(QColor("#ffffff"))
    festo.drawText(szoveg_rect, Qt.AlignmentFlag.AlignLeft, szoveg)
    festo.end()

    cel = mappa / "kiadaskep_5649.png"
    assert kep.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"
    return cel


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_felso_sav_es_lejatszas_azonos_allapotot_valt_es_a_tobbi_kattintas_marad(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.show()
    window.setVisibility(QWindow.Visibility.Windowed)
    alapmagassag = window.height()
    celmagassag = alapmagassag + magassag_eltolas
    window.resize(window.width(), celmagassag)
    assert varj_feltetelre(
        qt_app, lambda: window.height() == celmagassag, 2.0
    ), f"az ablak nem vette fel a kért magasságot: {window.height()}"

    show = _gyerek(window, "slideshowView")
    QMetaObject.invokeMethod(
        show,
        "start",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
    )
    assert varj_feltetelre(qt_app, lambda: show.property("visible") is True), (
        "a vetítés nem indult el"
    )
    show.setProperty("playing", False)
    controls = _gyerek(window, "slideshowControls")
    controls.setProperty("shown", True)
    assert varj_feltetelre(
        qt_app, lambda: controls.property("opacity") >= 0.99, 3.0
    ), "a vezérlősáv nem jelent meg"

    felso_sav = window.findChild(QQuickItem, "slideshowAuto2Area")
    assert felso_sav is not None, "hiányzik a vetítő felső kattintósávja"
    assert felso_sav.height() == 14, "a felső kattintósáv magassága nem 14 px"
    assert felso_sav.width() == show.width(), (
        "a felső kattintósáv nem tölti ki a vetítőt"
    )
    assert felso_sav.x() == 0 and felso_sav.y() == 0, (
        "a kattintósáv nem a vetítő bal felső sarkából indul"
    )

    # A képközép kattintása maradjon semleges.
    _kattints(window, qt_app, show)
    assert show.property("playing") is False, (
        "a sáv alatti képterület kattintása megváltoztatta a lejátszást"
    )

    # Mindkét út ugyanabból a szünetelt állapotból ugyanoda jusson.
    _kattints(window, qt_app, felso_sav)
    felso_sav_utan = show.property("playing")
    assert felso_sav_utan is True, "a felső sáv kattintása nem indította el a vetítést"

    show.setProperty("playing", False)
    lejatszas_gomb = _gyerek(window, "slideshowPlayButton")
    _kattints(window, qt_app, lejatszas_gomb)
    lejatszas_gomb_utan = show.property("playing")
    assert lejatszas_gomb_utan == felso_sav_utan, (
        "a felső sáv és a lejátszás gomb eltérő állapotot adott"
    )

    mappa = os.environ.get(KIADASKEP_MAPPA)
    if magassag_eltolas == 0 and mappa:
        show.setProperty("playing", False)
        assert varj_feltetelre(
            qt_app, lambda: controls.property("opacity") >= 0.99, 3.0
        )
        _annotalt_kiadas_kep(window, felso_sav, Path(mappa))
