"""#3712: a Nyomtatás párbeszéd EGYETLEN méretlistát ad, az Indexképek is
a méretlista része — a „Képenként egy lap" kapcsoló (és a hozzá tartozó
téves felirat) megszűnik.

## A lelet

A párbeszéd eddig KÉT úton mondta meg, mi kerül a papírra: egy „Layout:"
rádiópár (Egy kép laponként / Indexkép), és egy KÜLÖN nyomatméret-lista.
A felső darabszám-sor eközben azt írta, hogy „(oldalanként egy)" — pedig a
nyomatméretet a rácselrendező (`grid_layout.py`, #3647) cellaként kezeli,
és A4-en már az alapértelmezett 4×6-nál is több nyomat kerül egy lapra.

Az eredeti panelen nincs ilyen kapcsoló: a felhasználó MÉRETET választ
(Wallet · 3.5×5 · 4×6 · 5×7 · 8×10 · Full Page — és a méretlista része az
Indexképek is), a laponkénti darabszámot a program számolja.

Ez a kör a 2. utat választja: a rádiópár megszűnik, az „Indexképek" a
méretlista egyik tétele lesz (a `NyomatMeret`-készlet — #1961 — nem
változik, ez csak a QML-oldali választó szerkezete), és a darabszám-sor a
TÉNYLEGES lapszámot mondja méret szerinti és indexkép nyomtatásnál is.

## #3712-review: valódi kattintás, nem programozott jel

A legördülő kiválasztását korábban a `activated` jel közvetlen
`invokeMethod`-hívása szimulálta — ez a Qt `ComboBox`-nak azt üzente, hogy
„a felhasználó ezt választotta", anélkül hogy a legördülő ténylegesen
megnyílt vagy bármi látszott volna a képernyőn. Itt VALÓDI
`QTest.mouseClick` nyitja meg a `printSizeBox`-ot, és VALÓDI kattintás
választja a tételt a felugró listában — a `test_beallitasok_legkisebb_
szelesseg_3572.py` `_kattints_kozepere`-mintája szerint.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _nyit_sima(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()
    tetel = _elem(window, "menuFilePrint")
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "printDialog")


def _nyit_indexkeppel(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()
    tetel = _elem(window, "menuFolderPrintContactSheet")
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "printDialog")


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


def _kattints_kozepere(ablak, qt_app, elem):
    """Valódi bal kattintás `elem` közepére (a
    `test_beallitasok_legkisebb_szelesseg_3572.py` `_kattints_kozepere`
    mintája) — `ablak` az az egyetlen `QQuickWindow`, amelynek koordináta-
    rendszerében `elem` él (a `PrintDialog.qml` maga is `Window`, a
    felugró `Popup` tartalma ugyanennek az ablaknak az overlay-rétegén
    jelenik meg, tehát ugyanaz az `ablak` illik mindkettőre)."""
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _varakozzon(qt_app, feltetel, hatarido_mp=3):
    hatarido = time.monotonic() + hatarido_mp
    while time.monotonic() < hatarido and not feltetel():
        qt_app.processEvents()
        time.sleep(0.01)
    return feltetel()


def _legordulo_tetele(qt_app, lista, index):
    """A `picasaComboList` (a `PicasaComboBox` felugró `ListView`-je)
    `index`-edik delegate-je — a `ListView.itemAtIndex()` Qt-beépített
    lekérdezése, `QQmlExpression`-ön át (a `test_almenu_listas_tetel_
    kattintas_3470.py` mintája szerint), mert a delegate-nek nincs
    `objectName`-je."""
    kifejezes = QQmlExpression(qmlContext(lista), lista, f"itemAtIndex({index})")

    def _van_tetel():
        ertek, hiba = kifejezes.evaluate()
        assert not hiba, kifejezes.error()
        _van_tetel.eredmeny = ertek
        return ertek is not None

    _van_tetel.eredmeny = None
    assert _varakozzon(qt_app, _van_tetel), (
        f"a legördülő {index}. tétele nem épült fel"
    )
    return _van_tetel.eredmeny


def _valassz_a_legorduloben(dialog, qt_app, cel_azonosito):
    """A `printSizeBox` VALÓDI kattintással választ — megnyitja a
    legördülőt, megkeresi `cel_azonosito` delegate-jét, és arra kattint.
    Nem az `activated` jel programozott meghívása (#3712-review)."""
    box = _elem(dialog, "printSizeBox")
    azonositok = _lista(dialog.property("printSizeIds"))
    cel_index = azonositok.index(cel_azonosito)

    _kattints_kozepere(dialog, qt_app, box)
    assert _varakozzon(
        qt_app, lambda: box.findChild(QObject, "picasaComboList") is not None
    ), "a legördülő nem nyílt meg (a felugró listája nem épült fel)"
    lista = box.findChild(QObject, "picasaComboList")

    tetel = _legordulo_tetele(qt_app, lista, cel_index)
    _kattints_kozepere(dialog, qt_app, tetel)


class TestAKulonElrendezesValasztoEltunt:
    def test_a_ket_regi_radio_mar_nem_letezik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        dialog = _nyit_sima(window, qt_app, [0, 1])

        assert dialog.findChild(QObject, "printOnePerPageRadio") is None
        assert dialog.findChild(QObject, "printContactSheetRadio") is None


class TestAMeretlistaResze:
    def test_az_indexkep_a_meretlistaban_van(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        dialog = _nyit_sima(window, qt_app, [0, 1])

        azonositok = _lista(dialog.property("printSizeIds"))
        feliratok = _lista(dialog.property("printSizeLabels"))
        assert "CONTACT" in azonositok, azonositok
        # #3712-review: a HIVATALOS `ytPrintSizes::eContact` szöveg
        # "Contact Sheet" (stringres 3491), nem a korábbi kisbetűs saját
        # fogalmazás.
        assert "Contact Sheet" in feliratok, feliratok

    def test_a_legorduloben_kivalasztva_indexkep_modba_kapcsol(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        dialog = _nyit_sima(window, qt_app, [0, 1])
        assert dialog.property("contactSheet") is False

        _valassz_a_legorduloben(dialog, qt_app, "CONTACT")

        assert dialog.property("contactSheet") is True

    def test_a_meret_visszavaltasa_kikapcsolja_az_indexkepet(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        dialog = _nyit_indexkeppel(window, qt_app, [0, 1])
        assert dialog.property("contactSheet") is True

        _valassz_a_legorduloben(dialog, qt_app, "M4X6")

        assert dialog.property("contactSheet") is False
        assert dialog.property("printSize") == "M4X6"


class TestAMenuAKombinaltValasztoval:
    """A #1590 menüpont (Indexképek nyomtatása…) ÉS a legördülő NE
    mondjon egymásnak ellentmondó állapotot."""

    def test_a_menubol_nyitott_indexkep_a_legorduloben_is_latszik(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        dialog = _nyit_indexkeppel(window, qt_app, [0, 1])

        box = _elem(dialog, "printSizeBox")
        azonositok = _lista(dialog.property("printSizeIds"))
        assert box.property("currentIndex") == azonositok.index("CONTACT"), (
            "a párbeszéd indexkép-módban van, de a legördülő más tételt mutat"
        )


class TestADarabszamSorATenylegesLapszamotMondja:
    def test_meret_szerinti_nyomtatasnal(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        dialog = _nyit_sima(window, qt_app, [0, 1])
        qt_app.processEvents()

        # #3733: az alapállás Teljes oldal (FullPage) lett — az a méret
        # A4-en NEM enged két képet egy lapra. A darabszám-sor TÉNYLEGES
        # lapszám-logikáját ezért egy olyan méretre kattintva mérjük,
        # ahol ez a jegy szándéka szerint kettő fér egy lapra.
        _valassz_a_legorduloben(dialog, qt_app, "M4X6")
        qt_app.processEvents()

        szoveg = str(_elem(dialog, "printSelectionText").property("text"))
        lapszam = dialog.property("printPageCount")

        # Két kép 4×6-tal ugyanarra a lapra kerül a rácselrendezőben
        # (#3647) — a foga: ha ez valaha 2-re változna (pl. a rács
        # módosulna), ennek a tesztnek SZÓLNIA kell, nem csendben zöldnek
        # maradnia.
        assert lapszam == 1, lapszam
        assert szoveg == "Pictures to print: 2 (1 page(s))", szoveg

    def test_indexkep_nyomtatasnal(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        dialog = _nyit_indexkeppel(window, qt_app, [0, 1])
        dialog.setProperty("contactColumns", 1)
        QMetaObject.invokeMethod(
            dialog, "frissitsdAzElonezetet", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        # Egy oszlop mellett A4-en egy sor fér ki soronként — két kép tehát
        # két lapra kerül (ugyanaz a beállítás, mint a valódi PDF-kimenetet
        # mérő `test_indexkep_nyomtatas_1590.py`-ben).
        lapszam = dialog.property("printPageCount")
        assert lapszam == 2, lapszam

        szoveg = str(_elem(dialog, "printSelectionText").property("text"))
        assert szoveg == "Pictures to print: 2 (2 page(s))", szoveg


class TestAlapallasTeljesOldal:
    """#3733: a menüből nyitott párbeszéd alapállása Teljes oldal
    (FullPage), mint az eredetiben; a választott méret a bezárás és az
    újranyitás után megmarad."""

    def test_a_menubol_nyitva_a_teljes_oldal_van_kivalasztva(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        dialog = _nyit_sima(window, qt_app, [0, 1])

        box = _elem(dialog, "printSizeBox")
        azonositok = _lista(dialog.property("printSizeIds"))
        assert box.property("currentIndex") == azonositok.index("TELJES_OLDAL")
        assert box.property("displayText") == "FullPage"

    def test_a_valasztott_meret_ujranyitaskor_megmarad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        dialog = _nyit_sima(window, qt_app, [0, 1])

        _valassz_a_legorduloben(dialog, qt_app, "M5X7")
        _kattints_kozepere(dialog, qt_app, _elem(dialog, "printCloseButton"))
        assert dialog.property("visible") is False

        dialog = _nyit_sima(window, qt_app, [0, 1])
        box = _elem(dialog, "printSizeBox")
        azonositok = _lista(dialog.property("printSizeIds"))
        assert dialog.property("printSize") == "M5X7"
        assert box.property("currentIndex") == azonositok.index("M5X7")
