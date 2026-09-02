"""#1927: az alsó sáv NÉGY panelkapcsolója (Emberek · Helyek · Címkék · Tulajdonságok).

## A lelet

A panelek MEGVANNAK nálunk (`activeDrawerTab`: people/places/tags/
properties), a menütételek is — csak a **második belépési pont**, az alsó
sávbeli négy kapcsológomb hiányzott. Két független keresés adott nullát:
név szerint (`people_toggle` …) és funkció szerint is.

## A geometria — mérve (a #1914 respack-rétegfejlécei)

A tálca függőleges méretei 1:1-ben képpontok.

| réteg | x | méret |
|---|---|---|
| `thumbui/rect: metadata_group` | 545…785 | **240×24** |
| `people_toggle` | 545…605 | 60×24 |
| `places_toggle` | 605…665 | 60×24 |
| `tags_toggle` | 665…725 | 60×24 |
| `properties_toggle` | 725…785 | 60×24 |

A négy gomb **érintkezik** (nincs köztük rés), és a típusneveik a
szegmens-szerepet is megadják: `buttcon_LS_` · `_MS_` · `_MS_` · `_RS_`
⇒ összefüggő szegmenssáv, nem négy különálló gomb.

## ⚠️ Amit ez az őr NEM állít

Hogy a négy kapcsoló KIZÁRÓ csoport-e az EREDETIBEN — az nincs megmérve
(a #1927 nyitott kérdése). Nálunk egyetlen `activeDrawerTab` írja le mind
a négy panelt (#1773), és a gombok ezt tükrözik.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app

_TRAYBAR = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")

_NEVEK = ("people", "places", "tags", "properties")


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for it in _walk(window.contentItem()):
        if it.objectName() == nev:
            return it
    return window.findChild(QObject, nev)


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _kattints(window, elem, qt_app):
    """VALÓDI egérkattintás — a projekt szabálya: a vezérlőre kattints,
    ne a metódust hívd."""
    assert elem.width() > 0 and elem.height() > 0, "kattinthatatlan (0 méret)"
    assert elem.isEnabled(), "tiltott"
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


class TestAGeometria:
    def test_mind_a_negy_gomb_ott_van(self, qml_app, qt_app):
        window, _c, _e = qml_app
        for nev in _NEVEK:
            assert _elem(window, f"trayPanelToggle_{nev}") is not None, nev

    def test_gombonkent_60x24(self, qml_app, qt_app):
        window, _c, _e = qml_app
        for nev in _NEVEK:
            gomb = _elem(window, f"trayPanelToggle_{nev}")
            assert (gomb.width(), gomb.height()) == (60.0, 24.0), (
                f"{nev}: {gomb.width()}×{gomb.height()} a mért 60×24 helyett"
            )

    def test_a_csoport_240_szeles(self, qml_app, qt_app):
        window, _c, _e = qml_app
        csoport = _elem(window, "trayMetadataGroup")
        assert csoport.width() == 240.0, (
            f"{csoport.width()} a mért `metadata_group` 240 helyett"
        )

    def test_a_gombok_ERINTKEZNEK(self, qml_app, qt_app):
        """A mérés szerint nincs köztük rés (545→605→665→725→785)."""
        window, _c, _e = qml_app
        gombok = [_elem(window, f"trayPanelToggle_{n}") for n in _NEVEK]
        for elozo, kovetkezo in zip(gombok, gombok[1:], strict=False):
            res = kovetkezo.x() - (elozo.x() + elozo.width())
            assert res == 0.0, f"{res} képpont rés a gombok közt"


class TestABekotes:
    """A #1798/#1052 osztálya: a gomb ne legyen néma. VALÓDI kattintással."""

    def test_mind_a_negy_gomb_MEGNYITJA_a_sajat_panelját(self, qml_app, qt_app):
        window, _c, _e = qml_app
        for nev in _NEVEK:
            window.setProperty("activeDrawerTab", "")
            qt_app.processEvents()
            _kattints(window, _elem(window, f"trayPanelToggle_{nev}"), qt_app)
            assert _var(
                qt_app, lambda n=nev: window.property("activeDrawerTab") == n
            ), f"{nev}: a kattintás nem nyitotta meg a panelt"

    def test_az_AKTIV_gombra_kattintva_BEZARUL(self, qml_app, qt_app):
        """#1773 rádió-csapda: az aktív elemre kattintva ne maradjon a
        felület állapot nélkül — itt a fiók bezárul, ami a helyes."""
        window, _c, _e = qml_app
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        _kattints(window, _elem(window, "trayPanelToggle_tags"), qt_app)
        assert _var(qt_app, lambda: window.property("activeDrawerTab") == "")

    def test_a_gomb_JELZI_az_aktiv_allapotot(self, qml_app, qt_app):
        window, _c, _e = qml_app
        gomb = _elem(window, "trayPanelToggle_places")
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()
        assert gomb.property("aktiv") is False
        window.setProperty("activeDrawerTab", "places")
        assert _var(qt_app, lambda: gomb.property("aktiv") is True)


class TestASajatRajz:
    """A projekt egyetlen kicsomagolt Picasa-képet sem szállít."""

    def test_az_ikonok_SAJAT_SVG_k(self):
        ikonok = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "icons"
        for fajl in (
            "panel-emberek.svg", "panel-helyek.svg",
            "panel-cimkek.svg", "panel-tulajdonsagok.svg",
        ):
            ut = ikonok / fajl
            assert ut.exists(), fajl
            assert "sajat rajz" in ut.read_text(encoding="utf-8"), (
                f"{fajl}: a fejlécnek ki kell mondania, hogy saját rajz"
            )

    def test_a_forras_kimondja_hogy_a_kizarolagossag_NINCS_MEG(self):
        assert "NINCS MEG" in _TRAYBAR and "#1773" in _TRAYBAR
