"""#7079: a keresőmező háttere jelzi a találatot, és a sáv az eredeti szövegeket mondja.

Eredeti (`docs/specs/paritas-ellenorzes.md`, #7072 E4/E9; mért hívó:
`0x00662d0b sbb esi,esi; and esi,0xffe5261a; add esi,0xffffcbcb`): nem üres
szövegnél a mező háttere `0xFFE4F1E5` (van találat) vagy `0xFFFFCBCB` (nincs),
üresnél alapszín. A sáv szövege `Search results for "%s"` illetve `No matches`,
a gombos szűrőknél `%d results: ` és a gomb szava.

A próba a valódi főablakon, valódi gépeléssel és kattintással megy; a színeket
a kirajzolt elem `color` tulajdonságából olvassa (a vizuális egyezést, azaz a
képernyőképes összevetést ez NEM méri: a mintavétel a bináris hívójából jött,
nem képernyőképből).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtTest import QTest

from tests.support.qt_wait import varj_kattinthatora
from tests.support.varakozas import var_feltetelre

#: a bináris hívójából mért színek (`0xFFE4F1E5`, `0xFFFFCBCB`)
VILAGOS_TALALAT = "#e4f1e5"
VILAGOS_NINCS_TALALAT = "#ffcbcb"


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _gepel(mezo, szoveg: str, qt_app) -> None:
    for karakter in szoveg:
        kod = Qt.Key(ord(karakter.upper()))
        for tipus in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            QCoreApplication.sendEvent(
                mezo,
                QKeyEvent(tipus, kod, Qt.KeyboardModifier.NoModifier, karakter),
            )
    qt_app.processEvents()


def _kattint(window, elem, qt_app) -> None:
    assert elem is not None, "a kattintandó elem nem található"
    assert _var(
        qt_app,
        lambda: elem.isVisible() and elem.width() > 0 and elem.height() > 0,
    ), "a kattintandó elem nem kapott kirajzolható méretet"
    varj_kattinthatora(window, elem)
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _szin(elem) -> QColor:
    szin = elem.property("color")
    assert isinstance(szin, QColor), f"nem szín: {szin!r}"
    return szin


def _fenyesseg(szin: QColor) -> float:
    def linearis(csatorna: float) -> float:
        return (
            csatorna / 12.92
            if csatorna <= 0.03928
            else ((csatorna + 0.055) / 1.055) ** 2.4
        )

    return (
        0.2126 * linearis(szin.redF())
        + 0.7152 * linearis(szin.greenF())
        + 0.0722 * linearis(szin.blueF())
    )


def _kontraszt(elo: QColor, hatter: QColor) -> float:
    a, b = sorted((_fenyesseg(elo), _fenyesseg(hatter)), reverse=True)
    return (a + 0.05) / (b + 0.05)


class _Ablak:
    """A főablak keresőmezője, törlőgombja és a keresési beállítások ablaka."""

    def __init__(self, qml_app, qt_app):
        self.window, self.controller, self.engine = qml_app
        self.qt_app = qt_app
        self.window.show()
        self.window.requestActivate()
        qt_app.processEvents()
        self.doboz = self.window.findChild(QObject, "toolbarSearchBox")
        self.mezo = self.window.findChild(QObject, "searchField")
        assert self.doboz is not None and self.mezo is not None
        self.tema = self.engine.singletonInstance("PicasaPy", "Theme")
        assert self.tema is not None

    def gepel(self, szoveg: str) -> None:
        _kattint(self.window, self.mezo, self.qt_app)
        assert _var(self.qt_app, lambda: self.mezo.property("activeFocus") is True)
        _gepel(self.mezo, szoveg, self.qt_app)

    def torol(self) -> None:
        gomb = self.window.findChild(QObject, "searchClear")
        _kattint(self.window, gomb, self.qt_app)
        assert _var(self.qt_app, lambda: not self.controller.searchActive)

    def beallitasok_megnyitasa(self) -> None:
        """A keresési beállítások ablaka a két valódi úton.

        Gépelt szövegnél a `searchbutton` kattintása nyitja; üres mezőnél a
        gomb a lenyomás pillanatában eltűnik (a mező elveszti a fókuszt), ezért
        ott a `Ctrl+F` az út, amely ugyanazt a popupot nyitja."""
        popup = self.window.findChild(QObject, "searchOptionsPopup")
        if popup.property("visible") is True:
            return
        if str(self.mezo.property("text")):
            gomb = self.window.findChild(QObject, "searchbutton")
            assert _var(self.qt_app, lambda: gomb is not None and gomb.isVisible())
            _kattint(self.window, gomb, self.qt_app)
        else:
            for tipus in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
                QCoreApplication.sendEvent(
                    self.window,
                    QKeyEvent(
                        tipus, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier
                    ),
                )
            self.qt_app.processEvents()
        assert _var(
            self.qt_app, lambda: popup.property("visible") is True
        ), "a keresési beállítások nem nyíltak meg"

    def sav_szovege(self) -> str:
        self.beallitasok_megnyitasa()
        sav = self.window.findChild(QObject, "searchresult")
        assert sav is not None
        return str(sav.property("text"))


@pytest.fixture
def ablak(qml_app, qt_app):
    return _Ablak(qml_app, qt_app)


def test_ures_mezo_az_alapszint_mutatja(ablak):
    assert ablak.controller.searchFeedback == "none"
    assert _szin(ablak.doboz) == ablak.tema.property("controlBase")


def test_talalatnal_vilagoszold_a_mezo(ablak):
    ablak.gepel("a")
    assert _var(
        ablak.qt_app,
        lambda: ablak.controller.searchActive
        and ablak.controller.searchResultCount == 1,
    ), "a keresés nem szűrt egy találatra"
    assert ablak.controller.searchFeedback == "found"
    assert _szin(ablak.doboz).name() == VILAGOS_TALALAT
    assert _szin(ablak.doboz) == ablak.tema.property("searchFieldFoundBg")


def test_talalat_nelkul_halvanypiros_a_mezo(ablak):
    ablak.gepel("zzzqq")
    assert _var(
        ablak.qt_app,
        lambda: ablak.controller.searchActive
        and ablak.controller.searchResultCount == 0,
    )
    assert ablak.controller.searchFeedback == "notfound"
    assert _szin(ablak.doboz).name() == VILAGOS_NINCS_TALALAT
    assert _szin(ablak.doboz) == ablak.tema.property("searchFieldNotFoundBg")


def test_a_torles_visszaadja_az_alapszint(ablak):
    ablak.gepel("zzzqq")
    assert _var(
        ablak.qt_app,
        lambda: _szin(ablak.doboz).name() == VILAGOS_NINCS_TALALAT,
    )
    ablak.torol()
    assert _var(
        ablak.qt_app,
        lambda: _szin(ablak.doboz) == ablak.tema.property("controlBase"),
    ), "a ✕ gomb után a mező nem tért vissza az alapszínre"


def test_a_szin_a_gepelessel_koveti_a_talalatot(ablak):
    ablak.gepel("zzzqq")
    assert _var(
        ablak.qt_app,
        lambda: _szin(ablak.doboz).name() == VILAGOS_NINCS_TALALAT,
    )
    ablak.torol()
    ablak.gepel("a")
    assert _var(
        ablak.qt_app,
        lambda: _szin(ablak.doboz).name() == VILAGOS_TALALAT,
    ), "a találatos kifejezésnél nem lett világoszöld a mező"


@pytest.mark.parametrize("sotet", [False, True])
@pytest.mark.parametrize("kifejezes", ["a", "zzzqq"])
def test_a_beirt_szoveg_mindket_temaban_olvashato(ablak, sotet, kifejezes):
    ablak.controller.setDarkTheme(sotet)
    try:
        assert ablak.tema.property("dark") is sotet
        ablak.gepel(kifejezes)
        assert _var(ablak.qt_app, lambda: ablak.controller.searchActive)
        hatter = _szin(ablak.doboz)
        assert hatter != ablak.tema.property("controlBase")
        felirat = _szin(ablak.mezo)
        assert _kontraszt(felirat, hatter) >= 4.5, (
            f"olvashatatlan: {felirat.name()} a(z) {hatter.name()} hátteren "
            f"(sötét={sotet}, kifejezés={kifejezes!r})"
        )
    finally:
        ablak.controller.setDarkTheme(False)


def test_a_sav_talalatnal_az_eredeti_fejleceket_mondja(ablak):
    ablak.gepel("a")
    assert _var(
        ablak.qt_app,
        lambda: ablak.controller.searchActive
        and ablak.controller.searchResultCount == 1,
    )
    assert ablak.sav_szovege() == 'Search results for "a"'


def test_a_sav_talalat_nelkul_az_eredeti_nincs_talalat_szoveget_mondja(ablak):
    ablak.gepel("zzzqq")
    assert _var(
        ablak.qt_app,
        lambda: ablak.controller.searchActive
        and ablak.controller.searchResultCount == 0,
    )
    assert ablak.sav_szovege() == "No matches"


def test_az_arcszuro_valodi_kattintasra_a_gomb_szavat_irja_ki(ablak):
    ablak.beallitasok_megnyitasa()
    gomb = ablak.window.findChild(QObject, "facesearch")
    _kattint(ablak.window, gomb, ablak.qt_app)
    assert _var(ablak.qt_app, lambda: ablak.controller.viewModeName == "faces")
    assert _var(ablak.qt_app, lambda: ablak.sav_szovege() == "0 results: faces")


def test_a_csillagszuro_a_gomb_szavat_irja_ki(ablak):
    ablak.controller.showStarred()
    assert _var(ablak.qt_app, lambda: ablak.controller.viewModeName == "starred")
    assert _var(ablak.qt_app, lambda: ablak.sav_szovege() == "0 results: starred")


def test_a_filmszuro_a_gomb_szavat_irja_ki(ablak):
    ablak.controller.showVideosOnly()
    assert _var(ablak.qt_app, lambda: ablak.controller.viewModeName == "videos")
    assert _var(ablak.qt_app, lambda: ablak.sav_szovege() == "0 results: movies")
