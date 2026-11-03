"""Az indulókép logó-csoportja (embléma + szójel) a kártya vízszintes közepén van (#6498)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QSize
from PySide6.QtGui import QColor, QGuiApplication, QImage

from picasapy.app.startup_splash import (
    _ARNYEKSAV,
    _TARTALOM_MERET,
    _create_splash_pixmap,
)

_FEHER = QColor("#ffffff")
_TURES_PX = 2
_PNG = Path(__file__).resolve().parents[2] / "packaging" / "windows" / "startup-splash.png"
_APP = None


def _app():
    global _APP
    if _APP is None:
        _APP = QGuiApplication.instance() or QGuiApplication(["indulokep-kozep-test"])
    return _APP


def _kartya() -> QRect:
    return QRect(_ARNYEKSAV, _ARNYEKSAV, _TARTALOM_MERET.width(), _TARTALOM_MERET.height())


def _lathato_tinta_hatara(image: QImage, rect: QRect) -> tuple[int, int]:
    """A rect-en belüli nem-fehér, látható képpontok bal és jobb x-széle.

    A kártya a teljes kép belseje: az árnyék kívül esik, ezért nem számít bele."""
    oszlopok = []
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            szin = image.pixelColor(x, y)
            if szin.alpha() > 0 and szin != _FEHER:
                oszlopok.append(x)
    assert oszlopok, "a kártyán nincs látható tartalom"
    return min(oszlopok), max(oszlopok)


def _vizszintesen_kozepre_esik(image: QImage) -> None:
    """Az embléma bal széle és a szójel jobb széle a kártya középvonalára szimmetrikus.

    A két legkülső látható elem: az embléma a bal, a szójel a jobb szélen zár.
    A bal és a jobb oldali fehér sáv szélessége legfeljebb 2 képponttal térhet el."""
    kartya = _kartya()
    embleme_bal, szojel_jobb = _lathato_tinta_hatara(image, kartya)
    bal_sav = embleme_bal - kartya.left()
    jobb_sav = kartya.right() - szojel_jobb
    assert abs(bal_sav - jobb_sav) <= _TURES_PX, (
        f"a logó nincs középen: bal fehér sáv {bal_sav} px, jobb {jobb_sav} px"
    )


def test_az_embleme_bal_szele_es_a_szojel_jobb_szele_a_kartya_kozepere_szimmetrikus() -> None:
    _app()
    image = _create_splash_pixmap("v9.9.9").toImage()
    _vizszintesen_kozepre_esik(image)


def test_a_csomagolt_png_logoja_is_a_kartya_kozepen_van() -> None:
    image = QImage(str(_PNG)).convertToFormat(QImage.Format.Format_ARGB32)
    assert image.size() == QSize(668, 263)
    _vizszintesen_kozepre_esik(image)
