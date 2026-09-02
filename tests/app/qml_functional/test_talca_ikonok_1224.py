"""A tálca három vezérlője KÉP, nem betűjel (#1224).

## A hiba, amit ez az őr kizár

A csillag és a két forgatás-nyíl `Text` elem volt (`★`, `↺`, `↻`), tehát
az alakjuk teljes egészében a rendszer betűkészletétől és a helyettesítési
láncától függött: Windowson más glifát kapott, mint Linuxon. A tulajdonos
a #1188-ban ezeket is „eltorzultnak" látta.

Az eredeti Picasa ezeket **raszterikonként** rajzolja (`startoggle_icon`,
`rotateleft_icon`, `rotateright_icon`) — nem betűjelként.

## A MÉRT méretek

A #1914 réteg-leltárából (`respack.yt` fejlécek, a tálca 56 rétege):

| réteg | mért méret |
|---|---|
| `thumbui/startoggle_icon0` | **17 × 17** |
| `thumbui/rotateleft_icon` | **11 × 15** |
| `thumbui/rotateright_icon` | **11 × 15** |

A MÉRET az eredetiből mért, a RAJZ a sajátunk — a projekt egyetlen
kicsomagolt Picasa-képet sem szállít.

## ⚠️ Miért KÉT csillag-SVG

A QML `Image` shader nélkül nem színezhető, a `QtQuick.Effects` pedig
szándékosan nincs a projektben (`CollageSheet.qml`). A be- és kikapcsolt
állapot ezért két külön fájl, nem egy színezett kép.
"""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem

import picasapy.app

IKONOK = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "icons"
_TRAYBAR = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")

#: MÉRT méretek (#1914 réteg-leltár)
MERETEK = {
    "trayStarIcon": (17.0, 17.0),
    "trayRotateLeftIcon": (11.0, 15.0),
    "trayRotateRightIcon": (11.0, 15.0),
}


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


class TestAzIkonfajlokMegvannak:
    def test_mind_a_negy_svg_letezik(self):
        for nev in (
            "tray-star.svg", "tray-star-on.svg",
            "tray-rotate-left.svg", "tray-rotate-right.svg",
        ):
            assert (IKONOK / nev).is_file(), f"hiányzó ikon: {nev}"

    def test_a_csillagnak_KET_allapota_van(self):
        """Shader nélkül nem színezhető a kép — két fájl kell.

        Ha valaki egyre csökkentené, a bekapcsolt állapot vagy elveszne,
        vagy egy nem létező színezésre támaszkodna.
        """
        ki = (IKONOK / "tray-star.svg").read_text(encoding="utf-8")
        be = (IKONOK / "tray-star-on.svg").read_text(encoding="utf-8")
        assert 'fill="none"' in ki, "a kikapcsolt csillag ki van töltve"
        assert 'fill="none"' not in be, "a bekapcsolt csillag üres"


class TestAVezerlokKEPEK:
    def test_a_harom_vezerlo_kepet_hasznal(self, qml_app, qt_app):
        window, _c, _e = qml_app
        for nev in MERETEK:
            elem = _elem(window, nev)
            assert elem is not None, f"nincs meg: {nev}"
            # az Image-nek van `source`-a; a Textnek nincs
            assert elem.property("source") is not None, (
                f"{nev} nem kép — betűjel maradt?"
            )

    def test_a_regi_betujelek_eltuntek(self):
        """A `★`, `↺`, `↻` glifák nem lehetnek KIÍRT SZÖVEGKÉNT.

        Ez az állítás a LÉNYEG: a betűjel platformonként más alakot kap,
        és épp ezt jelentette a tulajdonos (#1188).

        ⚠️ Csak a KÓD-sorokat nézzük: a fájl elején egy ASCII-ábra
        szemlélteti az alsó sáv elrendezését, és abban a glifák jogosan
        szerepelnek. Egy tágabb kereséssel az őr a saját dokumentációnkat
        büntetné — az meg oda vezetne, hogy kivesszük az ábrát.
        """
        kod = "\n".join(
            sor for sor in _TRAYBAR.splitlines()
            if not sor.lstrip().startswith(("//", "/*", "*"))
        )
        for glif in ("★", "↺", "↻"):
            assert f'"{glif}"' not in kod, (
                f"a(z) {glif!r} betűjel még KIÍRT SZÖVEGKÉNT szerepel"
            )

    def test_a_MERT_meretek(self, qml_app, qt_app):
        window, _c, _e = qml_app
        for nev, (sz, m) in MERETEK.items():
            elem = _elem(window, nev)
            assert (elem.width(), elem.height()) == (sz, m), (
                f"{nev}: {elem.width()}×{elem.height()} a mért {sz}×{m} helyett"
            )


class TestACsillagAllapota:
    def test_csillagozatlan_kepnel_az_URES_ikon(self, qml_app, qt_app):
        window, _c, _e = qml_app
        ikon = _elem(window, "trayStarIcon")
        forras = str(ikon.property("source"))
        assert "tray-star" in forras
        assert "tray-star-on" not in forras, (
            "csillagozatlan képnél a BEKAPCSOLT ikon látszik"
        )

    def test_a_ket_allapot_KULONBOZO_forrast_ad(self):
        """A kötés a `starAt`-ra épül — a forrásban mindkét fájlnak
        szerepelnie kell, különben az állapot nem látszana."""
        assert "tray-star-on.svg" in _TRAYBAR
        assert "tray-star.svg" in _TRAYBAR
