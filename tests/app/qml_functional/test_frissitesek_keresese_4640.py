"""#4640: a Súgó ▸ Frissítések keresése tétel — megszűnt, nem ígéret.

A menütétel eddig `placeholder: true` volt: a sor végén pont jelezte, hogy
„még nem készült el". A PicasaPy saját frissítéskeresése nem paritás-feladat
(az eredeti az egykori Google-szolgáltatásra épült, amelyet a Picasa maga
letiltott Wine alatt), ezért a tétel `retired: true` jelölést kap: szürke,
kattinthatatlan, pont nélkül. A súgó lapja sem ígérhet működést.

A próbák valódi egérkattintással nyitják meg a Súgó menüt, és −5/0/+5 px
ablakmagasságnál is lefutnak.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _magassag,
    _varj,
)

#: a tétel felirata — a QML-ben objectName nélkül, a felirat alapján keresünk
FELIRATOK = {"&Check for Updates", "&Frissítések keresése"}
_SUGO_LAP = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "help" / "features" / "meg-nem-erheto-el.md"
)


def _frissites_tetel(menu_bar):
    return next(
        (
            elem
            for elem in menu_bar.findChildren(QObject)
            if elem.property("text") in FELIRATOK
        ),
        None,
    )


def _nyisd_meg_sugo_menut(qt_app, window):
    """A felső Súgó menü fejlécére kattintva megnyitja a menüt.

    A menüsort és a menüt is vissza kell adni: a hívó nélkül elengedett
    Python-hivatkozás törli a popupot, és a tétel is vele együtt megszűnik.
    """
    menu_bar = window.property("menuBar")
    menu = next(
        (
            elem
            for elem in menu_bar.findChildren(QObject)
            if elem.property("title") in {"&Help", "&Súgó"}
        ),
        None,
    )
    fejlec = next(
        (
            elem
            for elem in menu_bar.findChildren(QObject)
            if "MenuBarItem" in elem.metaObject().className()
            and elem.property("text") in {"&Help", "&Súgó"}
        ),
        None,
    )
    assert menu is not None, "a felső Súgó menü nem található"
    assert fejlec is not None, "a felső Súgó menü fejléce nem található"
    _kattints(qt_app, fejlec)
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        "a Súgó menü nem nyílt meg"
    )
    assert _varj(qt_app, lambda: _frissites_tetel(menu_bar) is not None), (
        "a Frissítések keresése tétel nem jelent meg a Súgó menüben"
    )
    return menu_bar, menu, _frissites_tetel(menu_bar)


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
class TestFrissitesekKeresese:
    def test_megszunt_tetel_nem_helyfoglalo(self, qml_app, qt_app, height_offset):
        window, _controller, _engine = qml_app
        _magassag(window, height_offset)

        _menu_bar, _menu, item = _nyisd_meg_sugo_menut(qt_app, window)

        assert item.property("retired") is True, (
            "a Frissítések keresése megszűnt szolgáltatás: `retired: true`"
        )
        assert item.property("placeholder") is False, (
            "helyfoglalóként a sor végi pont folytatást ígérne"
        )

    def test_nincs_rajta_folytatas_pontja(self, qml_app, qt_app, height_offset):
        window, _controller, _engine = qml_app
        _magassag(window, height_offset)

        _menu_bar, _menu, item = _nyisd_meg_sugo_menut(qt_app, window)
        pont = item.findChild(QObject, "placeholderDot")

        assert pont is None or pont.property("visible") is False

    def test_kattintas_nem_indit_semmit(self, qml_app, qt_app, height_offset):
        window, _controller, _engine = qml_app
        _magassag(window, height_offset)

        _menu_bar, _menu, item = _nyisd_meg_sugo_menut(qt_app, window)
        assert item.isEnabled() is False, "a tétel nem lehet aktív"

        kattintasok = []
        item.triggered.connect(lambda: kattintasok.append(True))
        center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(
            item.window(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        qt_app.processEvents()

        assert kattintasok == [], "a szürke tétel kattintásra mégis lefutott"


class TestSugoLap:
    """A súgó lapja ne ígérje később a működést: a megszűnt szolgáltatások
    között legyen, és a „még nem készült el" listában ne szerepeljen."""

    @staticmethod
    def _szakasz(szoveg: str, cim: str) -> str:
        minta = re.compile(
            rf"^## {re.escape(cim)}\n(.*?)(?=^## |\Z)", re.M | re.S
        )
        talalat = minta.search(szoveg)
        assert talalat is not None, f"nincs „{cim}” szakasz a súgó lapján"
        return talalat.group(1)

    def test_a_megszunt_szolgaltatasok_kozott_van(self):
        szoveg = _SUGO_LAP.read_text(encoding="utf-8")
        szakasz = self._szakasz(
            szoveg, "Megszűnt szolgáltatások — ezek nem is fognak elkészülni"
        )

        assert "Frissítések keresése" in szakasz

    def test_a_meg_nem_keszult_listaban_nincs_benne(self):
        szoveg = _SUGO_LAP.read_text(encoding="utf-8")
        szakasz = self._szakasz(szoveg, "Még nem készült el")

        assert "Frissítések keresése" not in szakasz
