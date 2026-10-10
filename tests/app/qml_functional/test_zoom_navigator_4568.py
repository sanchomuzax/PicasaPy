"""#4568: a nagyított kép áttekintője kirajzolja és húzással pásztázza a nézetet."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre


def _elem(ablak, nev: str) -> QObject:
    elem = ablak.findChild(QObject, nev)
    assert elem is not None, f"A QML-fában nem található: {nev}"
    return elem


def _kattints(ablak, elem: QObject) -> None:
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=pont)


def _megnyitott_nagyitott_nezo(qml_app_email, qt_app):
    ablak, _vezerlo, _engine = qml_app_email
    ablak.setHeight(1024)
    assert varj_feltetelre(qt_app, lambda: int(ablak.height()) == 1024, 3.0)
    ablak.setProperty("viewerOpen", True)
    nezo = _elem(ablak, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    kep = _elem(ablak, "viewerImage")
    assert varj_feltetelre(
        qt_app,
        lambda: kep.property("visible")
        and kep.property("paintedWidth") > 0
        and kep.property("paintedHeight") > 0,
        3.0,
    )
    nezo.setProperty("zoomValue", 1.0)
    return ablak, nezo, kep


def test_a_nagyito_lathato_resze_renderelve_es_ablakmagassaghoz_igazodik(
    qml_app_email, qt_app, tmp_path
):
    ablak, nezo, kep = _megnyitott_nagyitott_nezo(qml_app_email, qt_app)
    nagyito = _elem(ablak, "zoomNavigator")
    kepter = _elem(ablak, "viewerPhotoArea")
    attekinto = _elem(ablak, "zoomNavigatorImage")
    keret = _elem(ablak, "zoomNavigatorViewport")
    felirat = _elem(ablak, "zoomNavigatorZoomLabel")

    assert varj_feltetelre(qt_app, lambda: nagyito.property("visible"), 3.0)
    assert varj_feltetelre(
        qt_app,
        lambda: attekinto.property("paintedWidth") > 0
        and attekinto.property("paintedHeight") > 0,
        3.0,
    )
    assert felirat.property("text") == "Nagyítás: 400%"

    nezo.setProperty("zoomValue", 0.5)
    assert varj_feltetelre(
        qt_app, lambda: felirat.property("text") == "Nagyítás: 100%", 3.0
    )
    nezo.setProperty("zoomValue", 1.0)
    assert varj_feltetelre(qt_app, lambda: nagyito.property("visible"), 3.0)

    alapmagassag = int(ablak.height())
    for elteres in (-5, 0, 5):
        ablak.setHeight(alapmagassag + elteres)
        assert varj_feltetelre(
            qt_app,
            lambda cel=alapmagassag + elteres:
                int(ablak.height()) == cel,
            3.0,
        )
        assert keret.property("visible")
        teljes = float(attekinto.property("paintedWidth"))
        lathato = float(kepter.property("width"))
        zoom = float(nezo.property("zoomFactor"))
        arany = float(keret.property("width")) / teljes
        vart = lathato / (float(kep.property("paintedWidth")) * zoom)
        # A geometria a program saját nézetméretéből számolódik; a ±3 px-es
        # engedmény a platformonként eltérő ablak- és betűméretekre szól.
        assert abs(arany - vart) * teljes <= 3, (
            f"a jelölt nézet szélessége {arany:.3f}, a látható képé {vart:.3f}"
        )

        if elteres == 0:
            render = ablak.grabWindow()
            assert not render.isNull(), "a kirajzolt nézőablak üres"
            assert render.save(str(tmp_path / "zoom-navigator-4568.png"))
            keretpont = keret.mapToScene(QPointF(keret.width() / 2, 1))
            keretszin = QColor(keret.property("outlineColor"))
            kirajzolt = render.pixelColor(round(keretpont.x()), round(keretpont.y()))
            assert kirajzolt == keretszin, (
                f"a látható rész kerete nem rajzolódott ki: {kirajzolt.name()} "
                f"!= {keretszin.name()}"
            )


def test_a_nezetkeret_huzasa_pasztazza_a_fotot_es_a_close_elrejti(
    qml_app_email, qt_app
):
    ablak, nezo, _kep = _megnyitott_nagyitott_nezo(qml_app_email, qt_app)
    nagyito = _elem(ablak, "zoomNavigator")
    keret = _elem(ablak, "zoomNavigatorViewport")
    zaras = _elem(ablak, "zoomNavigatorCloseButton")
    assert varj_feltetelre(qt_app, lambda: nagyito.property("visible"), 3.0)

    kezdo_pan = float(nezo.property("panX"))
    kezdo = keret.mapToScene(QPointF(keret.width() / 2, keret.height() / 2)).toPoint()
    cel = kezdo + QPoint(8, 0)
    QTest.mousePress(ablak, Qt.MouseButton.LeftButton, pos=kezdo)
    QTest.mouseMove(ablak, cel, delay=10)
    QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, pos=cel)
    assert varj_feltetelre(
        qt_app, lambda: abs(float(nezo.property("panX")) - kezdo_pan) > 1, 3.0
    ), "a nézetkeret húzása nem pásztázta a nagyított képet"

    _kattints(ablak, zaras)
    assert varj_feltetelre(qt_app, lambda: not nagyito.property("visible"), 3.0), (
        "a navigátor bezárógombja nem rejtette el az ablakot"
    )


def test_a_nagyitas_felirat_a_picasa_displayfont14_beallitasat_tartja():
    fajl = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/qml/PicasaPy/ZoomNavigator.qml"
    )
    forras = fajl.read_text(encoding="utf-8")
    assert 'qsTr("Zoomed to %1%")' in forras, (
        "a felirat az eredeti Picasa ytZoomString angol szövegét használja"
    )
    assert re.search(r"font\.pixelSize\s*:\s*14\b", forras), (
        "a nav/zoom a nav.tre m_displayfont14 beállítását követi"
    )


# rontás-kontroll: a ZoomNavigator komponens eltávolítva → 2 failed.
