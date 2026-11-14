"""A #6920 Időrend-címkártyájának képpontreceptje."""

from urllib.parse import quote

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QImage

from picasapy.app.slideshow_label_card import create_slideshow_label_card
from picasapy.app.slideshow_label_card_provider import SlideshowLabelCardProvider


def _egyszinu_kep(szin: QColor) -> QImage:
    kep = QImage(4, 4, QImage.Format.Format_RGBA8888)
    kep.fill(szin)
    return kep


def test_a_luma_gyoke_utan_160_255_fekete_fedest_kap(qt_app):
    for szin, vart in (
        (QColor(255, 0, 0), 52),
        (QColor(0, 255, 0), 73),
        (QColor(255, 255, 255), 95),
    ):
        kartya = create_slideshow_label_card(_egyszinu_kep(szin), "")
        assert kartya.pixelColor(0, 0) == QColor(vart, vart, vart, 255)


def test_a_cimkartyakeszites_nem_modositja_a_forraskepet(qt_app):
    forras = QImage(320, 240, QImage.Format.Format_RGBA8888)
    forras.fill(QColor(255, 0, 0))

    kartya = create_slideshow_label_card(forras, "Időrend gyűjtemény")

    assert kartya.size() == forras.size()
    assert kartya is not forras
    assert forras.pixelColor(0, 0) == QColor(255, 0, 0, 255)
    assert kartya.pixelColor(0, 0) == QColor(52, 52, 52, 255)


def test_a_kepszolgaltato_a_megadott_fotobol_allitja_elo_a_kartyat(
    qt_app, tmp_path
):
    fajl = tmp_path / "elso foto.png"
    forras = QImage(320, 240, QImage.Format.Format_RGBA8888)
    forras.fill(QColor(255, 255, 255))
    assert forras.save(str(fajl))
    azonosito = (
        quote(str(fajl), safe="")
        + "?name=Collection&rotation=0&viewWidth=800&viewHeight=800"
    )
    meret = QSize()

    kartya = SlideshowLabelCardProvider().requestImage(
        azonosito, meret, QSize(320, 240)
    )

    assert not kartya.isNull()
    assert meret == QSize(320, 240)
    assert kartya.pixelColor(0, 0) == QColor(95, 95, 95, 255)
