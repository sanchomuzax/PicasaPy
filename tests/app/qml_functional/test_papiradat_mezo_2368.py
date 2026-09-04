"""#2368: a papíradat-mező a FUTÓ nyomtatási párbeszéden.

A vezérlő-oldali `paperInfo()` tartalmát a `tests/app/test_papiradat_kijelzo_2368.py`
méri. Ez az őr azt méri, ami abból nem látszik: hogy a mező **ki is jut a
felületre**, és nem üresen. A #1471/#1454 tanulsága szerint épp ez a
gyenge pont — a lánc egyik vége kész, a másik nincs bekötve.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt

MEZO = "printPaperInfoText"


def _elem(root, nev):
    objektum = root.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.01)
    return False


def _nyomtatas_parbeszed(window, qt_app):
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    tetel = _elem(window, "menuFilePrint")
    assert tetel.property("enabled") is True, (
        "a Nyomtatás… menüpont kijelölt képpel sem elérhető"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "printDialog")


def test_a_mezo_kijut_a_felultre_es_nem_ures(qml_app, qt_app):
    window, _controller, _engine = qml_app
    parbeszed = _nyomtatas_parbeszed(window, qt_app)
    mezo = _elem(parbeszed, MEZO)

    assert _var(qt_app, lambda: bool(str(mezo.property("text")).strip())), (
        "a papíradat-mező ÜRES a futó párbeszéden — a vezérlő adja az "
        "adatot, de a felületre nem jut ki"
    )
    szoveg = str(mezo.property("text"))
    assert any(karakter.isdigit() for karakter in szoveg), (
        f"a mező nem mutat mérőszámot: {szoveg!r}"
    )
