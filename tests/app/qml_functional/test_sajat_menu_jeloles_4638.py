"""#4638: a PicasaPy saját menüparancsai kék jelölést kapnak.

Három tétel az eredeti Picasa 3.9-ben nincs meg (`docs/specs/ui-audit-menus.md`
szerint szándékos PicasaPy-bővítés), ezért `sajat: true` jelölést kell kapniak
(`docs/decisions/sajat-funkciok-jelolese.md`, #1701), jelölést kell kapniuk:

- Nézet ▸ Sötét téma       (`menuViewDarkTheme`)
- Eszközök ▸ Arcok keresése… (`menuToolsFaceScan`)
- Súgó ▸ Teljesítmény-monitor (`menuHelpPerfMonitor`)

A jelölés nem rontja el a parancsot: a kattintás továbbra is végrehajtja.
Minden tesztet −5 / 0 / +5 px ablakmagassággal futtatunk.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject

import picasapy.app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _magassag,
    _objektum,
    _varj,
)

_QML_DIR = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"

#: (menü-kulcs, a felső sáv fejlécének lehetséges feliratai, tétel objectName)
_SAJAT_TETELEK = (
    ("view", {"&View", "&Nézet"}, "menuViewDarkTheme"),
    ("tools", {"&Tools", "&Eszközök"}, "menuToolsFaceScan"),
    ("help", {"&Help", "&Súgó"}, "menuHelpPerfMonitor"),
)

#: a jelölés mércéje: egy eredeti, jelöletlen parancs felirat-színe
_EREDETI_TETEL = "menuFileExit"


def _nyisd_meg(qt_app, window, feliratok):
    """A felső sáv megadott menüjét megnyitja valódi kattintással."""
    menu_bar = window.property("menuBar")
    fejlec = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if "MenuBarItem" in item.metaObject().className()
            and item.property("text") in feliratok
        ),
        None,
    )
    assert fejlec is not None, f"a felső menü fejléce nem található: {feliratok}"
    _kattints(qt_app, fejlec)
    menu = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if item.property("title") in feliratok
        ),
        None,
    )
    assert menu is not None, f"a felső menü nem található: {feliratok}"
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        f"a menü nem nyílt meg: {feliratok}"
    )
    # a hívó tartsa életben: a Python-oldali hivatkozás megszűnésekor a
    # QML-fa darabjai megsemmisülhetnek (a 4329-es helper is visszaadja)
    return menu_bar, menu, fejlec


def _tetel(window, nev):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


@pytest.mark.parametrize(("menu", "feliratok", "nev"), _SAJAT_TETELEK)
def test_a_sajat_tetel_kek_jelolest_es_kiegeszito_sugot_kap(
    qml_app, qt_app, menu, feliratok, nev
):
    """A jelölés és a súgó egy menünyitásban mérve; az ablakmagasság itt nem
    számít (a kattintásos próbák alább három magasságon futnak) — így a fájl
    a CI memóriaplafonja alatt marad (#4764)."""
    window, _controller, _engine = qml_app
    _kep = _nyisd_meg(qt_app, window, feliratok)
    tetel = _tetel(window, nev)

    assert tetel.property("sajat") is True, (
        f"{nev} eredeti Picasa-parancs nélküli saját tétel, de nincs "
        "`sajat: true` jelölése (#4638)"
    )
    szin = tetel.property("contentItem").property("color")
    eredeti = _tetel(window, _EREDETI_TETEL).property("contentItem").property(
        "color"
    )
    assert szin != eredeti, f"{nev} felirata nem tér el a jelöletlen tételtől"
    # a szín önmagában nem elég (színvakság): a súgó mondja ki
    sugo = tetel.property("sajatSugo")
    assert sugo and "PicasaPy" in sugo, (
        f"{nev} buboréksúgója nem mondja ki, hogy ez a PicasaPy kiegészítése"
    )


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_a_sotet_tema_kattintasa_is_kapcsol(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    _magassag(window, magassag_eltolas)
    _kep = _nyisd_meg(qt_app, window, {"&View", "&Nézet"})
    tetel = _tetel(window, "menuViewDarkTheme")
    assert tetel.property("checked") is False

    _kattints(qt_app, tetel)

    assert _varj(qt_app, lambda: tetel.property("checked") is True)


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_az_arckereses_kattintasa_megnyitja_a_parbeszedet(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    _magassag(window, magassag_eltolas)
    _kep = _nyisd_meg(qt_app, window, {"&Tools", "&Eszközök"})
    tetel = _tetel(window, "menuToolsFaceScan")
    assert tetel.property("enabled") is True

    _kattints(qt_app, tetel)

    assert _varj(
        qt_app,
        lambda: (
            _objektum(window, "faceScanDialog") is not None
            and _objektum(window, "faceScanDialog").property("visible") is True
        ),
    ), "az Arcok keresése… nem nyitotta meg a párbeszédet"


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_a_teljesitmeny_monitor_kattintasa_kapcsol(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    _magassag(window, magassag_eltolas)
    _kep = _nyisd_meg(qt_app, window, {"&Help", "&Súgó"})
    tetel = _tetel(window, "menuHelpPerfMonitor")
    assert tetel.property("checked") is False

    _kattints(qt_app, tetel)

    assert _varj(qt_app, lambda: tetel.property("checked") is True)


class TestForrasJelolese:
    """A forrásban is látszik a jelölés (a grep-es őr a PicasaMenuBar-ra)."""

    @pytest.mark.parametrize(("_menu", "_feliratok", "nev"), _SAJAT_TETELEK)
    def test_a_forras_tetele_sajat_jelolest_visel(self, _menu, _feliratok, nev):
        szoveg = (_QML_DIR / "PicasaMenuBar.qml").read_text(encoding="utf-8")
        blokk = re.search(
            rf'objectName: "{nev}"([^{{}}]*)',
            szoveg,
        )
        assert blokk is not None, f"{nev} nem szerepel a PicasaMenuBar.qml-ben"
        assert "sajat: true" in blokk.group(1), (
            f"{nev} tételében nincs `sajat: true` a forrásban"
        )
