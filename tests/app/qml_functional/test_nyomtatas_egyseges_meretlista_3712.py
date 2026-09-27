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
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


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
        assert "Contact sheet" in feliratok, feliratok

    def test_a_legorduloben_kivalasztva_indexkep_modba_kapcsol(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        dialog = _nyit_sima(window, qt_app, [0, 1])
        assert dialog.property("contactSheet") is False

        box = _elem(dialog, "printSizeBox")
        azonositok = _lista(dialog.property("printSizeIds"))
        cel_index = azonositok.index("CONTACT")
        box.setProperty("currentIndex", cel_index)
        ok = QMetaObject.invokeMethod(
            box, "activated", Qt.ConnectionType.DirectConnection,
            Q_ARG("int", cel_index),
        )
        qt_app.processEvents()

        assert ok
        assert dialog.property("contactSheet") is True

    def test_a_meret_visszavaltasa_kikapcsolja_az_indexkepet(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        dialog = _nyit_indexkeppel(window, qt_app, [0, 1])
        assert dialog.property("contactSheet") is True

        box = _elem(dialog, "printSizeBox")
        azonositok = _lista(dialog.property("printSizeIds"))
        cel_index = azonositok.index("M4X6")
        box.setProperty("currentIndex", cel_index)
        QMetaObject.invokeMethod(
            box, "activated", Qt.ConnectionType.DirectConnection,
            Q_ARG("int", cel_index),
        )
        qt_app.processEvents()

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

        szoveg = str(_elem(dialog, "printSelectionText").property("text"))
        lapszam = dialog.property("printPageCount")

        assert "one per page" not in szoveg
        assert "contact sheet" not in szoveg
        assert str(lapszam) in szoveg, szoveg

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
        assert dialog.property("printPageCount") == 2

        szoveg = str(_elem(dialog, "printSelectionText").property("text"))
        assert "2" in szoveg, szoveg
        assert "one per page" not in szoveg
