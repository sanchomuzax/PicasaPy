"""#4640 → #6340: a Súgó ▸ Frissítések keresése tétel él.

A #4640 a tételt megszűntnek jelölte (`retired: true`), mert az eredeti
frissítéskeresés egy egykori Google-szolgáltatásra épült. A tulajdonos
2026-10-31-én elfogadta a PicasaPy SAJÁT, GitHub-alapú frissítéskeresését
(#6340): a tétel aktív, pont és szürkeség nélkül, és kattintásra elindítja a
keresést. A súgó lapja sem sorolhatja többé a megszűnt szolgáltatások közé.

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

_SUGO_LAP = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "help" / "features" / "meg-nem-erheto-el.md"
)


def _frissites_tetel(menu_bar):
    return menu_bar.findChild(QObject, "menuHelpCheckUpdates6340")


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
    def test_a_tetel_el_es_nem_helyfoglalo(self, qml_app, qt_app, height_offset):
        window, _controller, _engine = qml_app
        _magassag(window, height_offset)

        _menu_bar, _menu, item = _nyisd_meg_sugo_menut(qt_app, window)

        assert item.isEnabled() is True, "a Frissítések keresése működő parancs (#6340)"
        assert item.property("retired") in (None, False)
        assert item.property("placeholder") in (None, False)

    def test_nincs_rajta_folytatas_pontja(self, qml_app, qt_app, height_offset):
        window, _controller, _engine = qml_app
        _magassag(window, height_offset)

        _menu_bar, _menu, item = _nyisd_meg_sugo_menut(qt_app, window)
        pont = item.findChild(QObject, "placeholderDot")

        assert pont is None or pont.property("visible") is False

    def test_kattintasra_elindul_a_kereses(self, qml_app, qt_app, height_offset):
        window, _controller, _engine = qml_app
        _magassag(window, height_offset)

        menu_bar, _menu, item = _nyisd_meg_sugo_menut(qt_app, window)
        kerelmek = []
        menu_bar.updateCheckRequested.connect(lambda: kerelmek.append(True))
        center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(
            item.window(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        qt_app.processEvents()

        assert kerelmek == [True], "a kattintás nem indította el a frissítéskeresést"


class TestSugoLap:
    """A működő funkció se a megszűntek, se a „még nem készült el" listában
    ne szerepeljen (#6340)."""

    @staticmethod
    def _szakasz(szoveg: str, cim: str) -> str:
        minta = re.compile(
            rf"^## {re.escape(cim)}\n(.*?)(?=^## |\Z)", re.M | re.S
        )
        talalat = minta.search(szoveg)
        assert talalat is not None, f"nincs „{cim}” szakasz a súgó lapján"
        return talalat.group(1)

    def test_a_megszunt_szolgaltatasok_kozott_nincs(self):
        szoveg = _SUGO_LAP.read_text(encoding="utf-8")
        szakasz = self._szakasz(
            szoveg, "Megszűnt szolgáltatások — ezek nem is fognak elkészülni"
        )

        assert "Frissítések keresése" not in szakasz

    def test_a_meg_nem_keszult_listaban_nincs_benne(self):
        szoveg = _SUGO_LAP.read_text(encoding="utf-8")
        szakasz = self._szakasz(szoveg, "Még nem készült el")

        assert "Frissítések keresése" not in szakasz
