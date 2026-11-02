"""A Név nélküliek „Learn more...” gombja a valódi főablakban (#6403).

A gomb a beépített súgó Emberek fejezetét nyitja meg a főablak súgóablakában,
és nem nyit böngészőt. A teljes láncot méri, valódi kattintással: gomb ->
nézet jele -> főablak (`MainLibraryCanvas`) -> súgó (`helpDialog`).
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre

EMBEREK_FEJEZET = "features/emberek.md"


class _UrlFogo(QObject):
    """A `http` séma kezelője a teszt idejére: a kért címeket rögzíti."""

    def __init__(self):
        super().__init__()
        self.cimek: list[str] = []

    @Slot("QUrl")
    def kezel(self, url):  # noqa: D102 - a Qt hívja
        self.cimek.append(url.toString())


def _elem(ablak, nev: str):
    talalat = ablak.findChild(QObject, nev)
    assert talalat is not None, f"a(z) {nev} elem nincs a főablakban"
    return talalat


def _sugo(ablak):
    return ablak.findChild(QObject, "helpDialog")


def _varj(qt_app, feltetel, leiras: str, hatarido: float = 10.0) -> None:
    if not var_feltetelre(qt_app, feltetel, hatarido):
        raise AssertionError(f"időkorláton belül nem teljesült: {leiras}")


def _kattint(ablak, elem) -> None:
    """Valódi egérkattintás az elem pillanatnyi középpontjára."""
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def test_a_learn_more_gomb_a_beepitett_sugo_emberek_fejezetet_nyitja(qml_app, qt_app):
    ablak, _vezerlo, _engine = qml_app
    ablak.setProperty("unnamedFacesOpen", True)
    ablak.setProperty("facesAlbumMode", "unnamed")
    nezet = _elem(ablak, "unnamedFacesView")
    _varj(qt_app, lambda: nezet.isVisible(), "a Névtelenek nézet megjelenése")
    udvozlo = _elem(ablak, "unnamedWelcomeDialog")
    _varj(
        qt_app,
        lambda: udvozlo.property("visible") is True,
        "az üdvözlőablak megnyílása",
    )
    gomb = _elem(ablak, "unnamedWelcomeLearnMoreButton")
    _varj(
        qt_app,
        lambda: gomb.isVisible() and gomb.width() > 0,
        "a „Learn more...” gomb láthatósága",
    )

    fogo = _UrlFogo()
    QDesktopServices.setUrlHandler("http", fogo, "kezel")
    try:
        _kattint(ablak, gomb)
        _varj(
            qt_app,
            lambda: _sugo(ablak) is not None
            and _sugo(ablak).property("visible") is True,
            "a súgó megnyílása",
        )
        assert _sugo(ablak).property("topic") == EMBEREK_FEJEZET
        assert fogo.cimek == [], "a „Learn more...” külső címet nyitott"
        assert udvozlo.property("visible") is True, (
            "a „Learn more...” kattintás bezárta az üdvözlőablakot"
        )
    finally:
        QDesktopServices.unsetUrlHandler("http")
        if _sugo(ablak) is not None:
            QMetaObject.invokeMethod(_sugo(ablak), "close")
        QMetaObject.invokeMethod(udvozlo, "close")
