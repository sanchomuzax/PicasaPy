"""#4257: az új, mért méretek rácsát a tényleges rajzolt kimeneten őrizzük."""

from __future__ import annotations

import math

import pytest
from PySide6.QtGui import QColor, QGuiApplication, QImage

from picasapy.app.print_controller import PrintController
from picasapy.printing.dpi import NyomatMeret
from picasapy.printing.grid_layout import choose_page_orientation, page_capacity
from picasapy.printing.layout import PageGeometry, PrintFitMode


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


def _pixel(kep: QImage, x: float, y: float) -> QColor:
    return QColor(kep.pixel(int(round(x)), int(round(y))))


def _feher(szin: QColor) -> bool:
    return min(szin.red(), szin.green(), szin.blue()) >= 243


def _nyomat_szin(szin: QColor) -> bool:
    return (
        szin.red() > 150
        and szin.red() > 2 * szin.green()
        and szin.red() > 2 * szin.blue()
    )


@pytest.mark.parametrize("azonosito", ["M3X4", "M4X5", "M15X20CM"])
def test_a_kiszamolt_meretek_fit_es_fill_kimeneten_is_a_cellat_hasznaljak(
    qt_app, azonosito
):
    meret = NyomatMeret[azonosito]
    # Az oldal pixelben, 25,4 képpont/hüvelyk skálával; ez ugyanazt az
    # arányt tartja meg mind a hüvelykes, mind a centiméteres méreteknél.
    cella_szel = meret.szeles_huvelyk * 25.4
    cella_mag = meret.magas_huvelyk * 25.4
    oldal = PageGeometry(
        width=2.8 * cella_szel,
        height=2.8 * cella_mag,
        margin=0,
    )
    assert page_capacity(oldal, cella_szel, cella_mag) == (2, 2)
    fekvo_cella, lapok = choose_page_orientation(
        oldal, cella_szel, cella_mag, count=4
    )
    assert fekvo_cella is False
    assert len(lapok) == 1
    assert lapok[0].count == 4
    assert all(
        cella.width == pytest.approx(cella_szel)
        and cella.height == pytest.approx(cella_mag)
        for cella in lapok[0].cells
    )

    lap = QImage(
        math.ceil(oldal.width),
        math.ceil(oldal.height),
        QImage.Format.Format_RGB32,
    )
    piros = QImage(200, 100, QImage.Format.Format_RGB32)
    piros.fill(QColor(220, 20, 20))

    illesztett = QImage(lap)
    illesztett.fill(QColor(255, 255, 255))
    PrintController._paint_pages(illesztett, lapok, [piros] * 4, PrintFitMode.FIT)

    vagott = QImage(lap)
    vagott.fill(QColor(255, 255, 255))
    PrintController._paint_pages(vagott, lapok, [piros] * 4, PrintFitMode.FILL)

    # A lekérdezett cellageometriából vett pontokat mérünk. A FIT teljes
    # képet ad, ezért a cella felső sávja üres; a FILL kivág, ezért a cella
    # teljes területét kitölti. Betű vagy platformfüggő ablakgeometria nincs.
    for cella in lapok[0].cells:
        kozep_x = cella.x + cella.width / 2
        kozep_y = cella.y + cella.height / 2
        assert _nyomat_szin(_pixel(illesztett, kozep_x, kozep_y))
        assert _feher(_pixel(illesztett, kozep_x, cella.y + 3))
        assert _nyomat_szin(_pixel(vagott, cella.x + 3, kozep_y))
        assert _nyomat_szin(_pixel(vagott, cella.x + cella.width - 3, kozep_y))

    bal_felso, jobb_felso, bal_also, _jobb_also = lapok[0].cells
    res_x = (bal_felso.x + bal_felso.width + jobb_felso.x) / 2
    res_y = (bal_felso.y + bal_felso.height + bal_also.y) / 2
    assert _feher(_pixel(vagott, res_x, bal_felso.y + bal_felso.height / 2))
    assert _feher(_pixel(vagott, bal_felso.x + bal_felso.width / 2, res_y))
