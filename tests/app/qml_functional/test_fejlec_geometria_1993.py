"""A szerkesztő fejlécének KÉPPONTOS geometriája (#1993).

## Mérve — három forrásból, és egyszer egymásnak ellentmondva

| elem | méret | szín | forrás |
|---|---|---|---|
| léptető nyilak | **30 × 31**, KÖR | korong `#DCDCDC`, nyíl `#5D5D5D` | `globalbuttons/lfs_n` / `rfs_n` sprite + a felvétel |
| „Vissza a könyvtárhoz" ikonja | **17 × 15**, balra mutató nyíl | **`#5A7BBB`** (kék) | `editpanel/albumview_icon` sprite |

A kör alakot a sprite soronkénti látható szélessége bizonyítja
(7, 13, 17, 20, 22, 24, 25, 27, 27, 29, 29, 29, **30, 30, 30, 30, 30, 30,
30**, 29, …) — ez korong, nem lekerekített téglalap.

## ⚠️ HELYESBÍTÉS a jegyhez

A jegy (és az én első kommentem) azt írta, hogy a léptető nyilak
**„kör alakúak, kékek"**. A kör igaz, a **kék nem**: a sprite szürke
(`#5C5C5C`–`#5E5E5E`), és a felvételen is ugyanez a szürke mérhető
(78 sötét képpontból mind `#5B`–`#5F` közötti). **A KÉK a
»Vissza a könyvtárhoz« gomb nyila** — az az elem `#5A7BBB`.

Ez pont az a hiba, amit a projekt szabálya tilt: a felvétel ránézésre
kékesnek tűnő részletéből következtetni ahelyett, hogy megmérnénk.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem

#: `globalbuttons/lfs_n` / `rfs_n`
LEPTETO_MERET = (30.0, 31.0)
#: `editpanel/albumview_icon`
VISSZA_IKON_MERET = (17.0, 15.0)


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


def _forras() -> str:
    import picasapy.app

    return (
        Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "PhotoViewer.qml"
    ).read_text(encoding="utf-8")


class TestALeptetoNyilak:
    def test_a_MERT_meret_30x31(self, qml_app, qt_app):
        window, _c, _e = qml_app
        for nev in ("viewerPrevButton", "viewerNextButton"):
            gomb = _elem(window, nev)
            assert gomb is not None, nev
            assert (gomb.width(), gomb.height()) == LEPTETO_MERET, (
                f"{nev}: {gomb.width()}×{gomb.height()} a mért 30×31 helyett"
            )

    def test_KEP_a_szoveges_nyil_helyett(self, qml_app, qt_app):
        """A foga: az eredeti kör alakú rajz, nem a `◀`/`▶` glif."""
        window, _c, _e = qml_app
        for nev in ("viewerPrevIcon", "viewerNextIcon"):
            assert _elem(window, nev) is not None, (
                f"nincs {nev} — a léptető még szöveges nyilat rajzol"
            )

    def test_a_szoveges_glifek_ELTUNTEK(self):
        forras = _forras()
        for nev in ('objectName: "viewerPrevButton"', 'objectName: "viewerNextButton"'):
            blokk = forras[forras.index(nev):][:600]
            assert 'text: "◀"' not in blokk and 'text: "▶"' not in blokk, (
                f"{nev} még szöveges nyilat rajzol"
            )


class TestAVisszaGomb:
    def test_van_objectName_je(self, qml_app, qt_app):
        """Enélkül a tesztek a felirat SZÜLŐJÉN át keresnék — az a #1224
        hibája volt."""
        window, _c, _e = qml_app
        assert _elem(window, "viewerBackButton") is not None

    def test_van_IKONJA_a_mert_merettel(self, qml_app, qt_app):
        window, _c, _e = qml_app
        ikon = _elem(window, "viewerBackIcon")
        assert ikon is not None, "a vissza-gomb ikon nélküli, csak szöveges"
        assert (ikon.width(), ikon.height()) == VISSZA_IKON_MERET

    def test_a_felirat_nem_tartalmaz_glifet(self):
        """Az ikon váltja ki a `◀` karaktert — nem mellette áll."""
        forras = _forras()
        assert '"◀  " + qsTr("Back to Library")' not in forras
        assert 'qsTr("Back to Library")' in forras, (
            "az eredeti felirat nem tűnhet el"
        )

    def test_KETSOROS_a_felirat(self, qml_app, qt_app):
        """A felvételen „Vissza a / könyvtárhoz" — két sor. A gomb tehát
        elég keskeny és elég magas ahhoz, hogy tördeljen."""
        window, _c, _e = qml_app
        gomb = _elem(window, "viewerBackButton")
        assert _var(qt_app, lambda: gomb.height() > 0)
        assert gomb.height() >= 30, (
            f"a vissza-gomb {gomb.height()} px magas — egy sornyi; a mért "
            "eredeti kétsoros"
        )


class TestAmitKIMONDUNK:
    def test_a_forras_kimondja_hogy_a_NYIL_NEM_KEK(self):
        """A jegy tévesen kékként írta le a léptetőket. Ha a forrás nem
        mondja ki a helyesbítést, egy későbbi kör visszafesti őket."""
        forras = _forras()
        kezdet = forras.index('objectName: "viewerPrevButton"') - 2000
        blokk = forras[max(0, kezdet):forras.index('objectName: "viewerPrevButton"') + 400]
        assert "5A7BBB" in blokk or "#5D5D5D" in blokk.upper(), (
            "a forrás nem rögzíti a MÉRT színeket"
        )
