"""#3544: a külön ablakban nyíló párbeszédekben is él a Shift+F1.

A #3463 a főablak paneljeit és a főablak rétegében nyíló párbeszédeket kötötte
be. A külön ablakos, ALKALMAZÁS-MODÁLIS párbeszédekben (Nyomtatás,
Mappakezelő, Beállítások, Importálás forrásból, Exportálás weboldalként) a
Shift+F1 nem nyitott semmit: a főablak gyorsbillentyűje ott nem él, a súgó
pedig a főablak rétegében élő `Dialog` — onnan nyitva a modális párbeszéd
MÖGÉ kerülne, és kezelni sem lehetne.

A javítás: a párbeszéd saját, ablakszintű Shift+F1-e egy KÜLÖN súgóablakot
nyit (`HelpWindow.qml`), amely a párbeszéd fölött, maga is modálisan áll.
Ez a fájl a VALÓDI billentyűeseményt küldi a párbeszéd ablakára, és azt méri,
hogy a súgóablak látszik, a párbeszédhez tartozik (fölötte áll), és a
párbeszéd saját fejezetét mutatja.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        time.sleep(0.01)
    qt_app.processEvents()
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


#: (a párbeszéd objectName-je, a nyitás útja, a várt fejezet). A nyitás
#: `menu:` előtaggal a VALÓDI menütétel, egyébként a főablak függvénye.
PARBESZEDEK = [
    ("printDialog", "openPrint", "features/nyomtatas.md"),
    ("folderManagerDialog", "menu:menuToolsFolderManager", "features/mappakezelo.md"),
    ("optionsDialog", "menu:menuToolsOptions", "features/beallitasok.md"),
    ("importSourceDialog", "menu:menuFileImportFrom", "features/importalas.md"),
    ("webExportDialog", "openWebExport", "features/exportalas.md"),
]


def _nyisd_meg(window, qt_app, nev, nyito):
    if nyito.startswith("menu:"):
        tetel = window.findChild(QObject, nyito[len("menu:"):])
        assert tetel is not None, f"{nyito} nem található"
        assert tetel.property("enabled") is True, f"{nyito} nem engedélyezett"
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection)
    else:
        assert window.metaObject().indexOfMethod(f"{nyito}()") >= 0, (
            f"a főablakon nincs {nyito}()")
        window.metaObject().invokeMethod(window, nyito)

    def _ablak():
        p = window.findChild(QObject, nev)
        return p if p is not None and p.property("visible") else None

    assert _var(qt_app, lambda: _ablak() is not None), f"a(z) {nev} nem nyílt meg"
    return _ablak()


@pytest.mark.parametrize("nev,nyito,tema", PARBESZEDEK)
def test_shift_f1_a_parbeszed_sajat_fejezetet_nyitja_elol(
    qml_app, qt_app, nev, nyito, tema
):
    window, _controller, _engine = qml_app
    parbeszed = _nyisd_meg(window, qt_app, nev, nyito)

    parbeszed.requestActivate()
    assert QTest.qWaitForWindowActive(parbeszed, 3000), f"a(z) {nev} nem lett aktív"
    QTest.keyClick(parbeszed, Qt.Key.Key_F1, Qt.KeyboardModifier.ShiftModifier)

    def _sugo():
        s = parbeszed.findChild(QObject, "helpWindow")
        return s if s is not None and s.property("visible") else None

    assert _var(qt_app, lambda: _sugo() is not None), (
        f"a(z) {nev} Shift+F1-ére nem nyílt súgóablak")
    sugo = _sugo()
    # ELÖL: a súgó a párbeszéd átmeneti gyermeke (az ablakkezelő fölé
    # rendeli), és maga is modális — a párbeszéd modalitása nem zárja ki.
    assert sugo.transientParent() is parbeszed, (
        "a súgóablak nem a párbeszédhez tartozik — mögé kerülhet")
    assert sugo.modality() == Qt.WindowModality.ApplicationModal
    belso = sugo.findChild(QObject, "helpWindowDialog")
    assert belso is not None and belso.property("visible")
    assert belso.property("topic") == tema

    # kezelhető: a súgó bezárható, és ezzel az ablaka is eltűnik
    belso.metaObject().invokeMethod(belso, "close")
    assert _var(qt_app, lambda: not sugo.property("visible")), (
        "a súgó bezárása után az ablaka nyitva maradt")

    parbeszed.setProperty("visible", False)
    qt_app.processEvents()


def test_f1_a_parbeszedbol_a_tartalomjegyzeket_nyitja(qml_app, qt_app):
    window, controller, _engine = qml_app
    parbeszed = _nyisd_meg(window, qt_app, "optionsDialog", "menu:menuToolsOptions")
    parbeszed.requestActivate()
    assert QTest.qWaitForWindowActive(parbeszed, 3000)
    QTest.keyClick(parbeszed, Qt.Key.Key_F1)

    def _belso():
        s = parbeszed.findChild(QObject, "helpWindow")
        if s is None or not s.property("visible"):
            return None
        return s.findChild(QObject, "helpWindowDialog")

    assert _var(qt_app, lambda: _belso() is not None), "az F1 nem nyitott súgót"
    assert _belso().property("topic") == controller.property("helpHomeTopic")
    parbeszed.setProperty("visible", False)
    qt_app.processEvents()


def test_a_parbeszed_bezarasa_utan_a_foablak_sugoja_ujra_el(qml_app, qt_app):
    """A főablak F1/Shift+F1-e a párbeszéd idejére hallgat (különben a Qt
    kétértelműnek látná a kettőt) — a bezárás után vissza kell kapcsolnia."""
    window, _controller, _engine = qml_app
    parbeszed = _nyisd_meg(window, qt_app, "optionsDialog", "menu:menuToolsOptions")
    parbeszed.setProperty("visible", False)
    qt_app.processEvents()

    window.requestActivate()
    assert QTest.qWaitForWindowActive(window, 3000)
    QTest.keyClick(window, Qt.Key.Key_F1)

    def _nyitott():
        p = window.findChild(QObject, "helpDialog")
        return p is not None and p.property("visible")

    assert _var(qt_app, _nyitott), "a párbeszéd után a főablak F1-e nem nyit súgót"
