"""Az üres rács kiírja, hogy nincs mit mutatnia (#1945).

## Mit adott eddig

**Semmit — az üres rács néma volt.** Aki olyan mappát vagy keresést nyitott
meg, aminek nincs találata, üres szürke felületet látott, magyarázat nélkül.

## Az eredeti

`layer:thumbui/static(nothing): lightbox_bgtext` — a rács **közepén**,
`m_centerXY`, `m_displayfont18_Reg` (18 pont), alapból rejtve
(`m_hidden`), és a `0x00676b10` állítja rá a hét kontextus-szöveg
egyikét (`thumbui_text.tre` 4–23).

Ez a kör a **0. indexet** építi meg — „No photos found" /
„A program nem talált fotókat" (`i18n-hu/tooltips.xml`, `Text1`). A többi
hat a webalbum-, CD- és biztonságimásolat-ághoz tartozik, ami nálunk
nincs; a spec (`docs/specs/racs-ures-allapot.md`) 4. táblája szerint a
teendő „legalább a »nincs találat« ág".

## ⛔ Amit szándékosan NEM építünk

A „Keresés mindenhol" gombot (`thumbui/lightbox_esolo_button`): a spec
négy lekérdezés-alakkal mutatta ki, hogy az **eredetiben halott**.

## A foga

A szöveg nem elég, hogy LÉTEZZEN: üres rácson **látszania** kell, tele
rácson **nem**, és munka közben sem — különben a betöltés alatt egy
pillanatra azt állítaná, hogy nincs kép, holott még számol.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_jpeg

#: `m_displayfont18_Reg` — a mért betűméret
MERT_BETUMERET = 18


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


def _rescan(controller, qt_app):
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


class TestAzUzenetLETEZIK:
    def test_van_ures_allapot_szoveg(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _elem(window, "gridEmptyText") is not None, (
            "az üres rácsnak nincs üzenete — a felhasználó üres szürke "
            "felületet lát, magyarázat nélkül"
        )

    def test_a_MERT_betumeret_18(self, qml_app, qt_app):
        """`m_displayfont18_Reg`."""
        window, _c, _e = qml_app
        szoveg = _elem(window, "gridEmptyText")
        assert szoveg.property("font").pointSize() == MERT_BETUMERET

    def test_az_EREDETI_feliratot_hasznalja(self):
        """`thumbui_text.tre` `Text1` — nem saját fogalmazás."""
        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "LightboxFeed.qml"
        ).read_text(encoding="utf-8")
        assert 'qsTr("No photos found")' in forras


class TestAzUzenetAKKOR_LATSZIK_AMIKOR_KELL:
    def test_URES_racson_latszik(self, qml_app, qt_app):
        """Valódi felhasználói út: csillag-szűrő, csillagozott kép nélkül.

        (Nem a képek törlésével ürítünk: a #1909 óta a takarítás
        SZÁNDÉKOSAN kimarad, ha egy gyökér üres eredményt ad, de az
        indexben van hozzá tartalom — így a rács nem is ürülne ki.)
        """
        window, controller, _e = qml_app
        controller.showStarred()
        qt_app.processEvents()
        racs = _elem(window, "photoGrid")
        assert _var(qt_app, lambda: racs.property("count") == 0), (
            "a csillag-szűrő nem ürítette ki a rácsot — más okból üres a teszt"
        )
        szoveg = _elem(window, "gridEmptyText")
        assert _var(qt_app, lambda: szoveg.property("visible") is True), (
            "üres rácson sem jelenik meg az üzenet"
        )

    def test_TELE_racson_NEM_latszik(self, qml_app, qt_app):
        """A foga: `visible: true`-ra kötve ez bukik."""
        window, controller, _e = qml_app
        mappa = Path(controller.watchedFolders[0]) / "van"
        mappa.mkdir(exist_ok=True)
        for i in range(3):
            make_jpeg(mappa / f"kep{i}.jpg", size=(60, 40))
        _rescan(controller, qt_app)
        szoveg = _elem(window, "gridEmptyText")
        assert _var(qt_app, lambda: szoveg.property("visible") is False), (
            "tele rácson is kiírja, hogy nincs fotó"
        )

    def test_MUNKA_kozben_NEM_latszik(self, qml_app, qt_app):
        """Betöltés alatt a rács üres, de attól még nem igaz, hogy nincs
        kép — a mondat ilyenkor hazudna."""
        window, _c, _e = qml_app
        forras = (
            Path(__import__("picasapy.app", fromlist=["app"]).__file__).parent
            / "qml" / "PicasaPy" / "LightboxFeed.qml"
        ).read_text(encoding="utf-8")
        kezdet = forras.index("gridEmptyText")
        blokk = forras[kezdet : kezdet + 900]
        assert "isWorking" in blokk, (
            "az üzenet nem nézi, hogy fut-e még munka — a betöltés alatt "
            "azt állítaná, hogy nincs kép"
        )
