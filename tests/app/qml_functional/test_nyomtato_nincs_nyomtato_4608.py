"""#4608 — a telepítő ajánlott csomagjai és a nyomtató nélküli üzenet.

1. A Debian-csomag `Recommends` sora tartalmazza az `xdg-utils`-t (e-mail
   melléklet, `xdg-email`) és a `cups-client`-et (a nyomtatólista, `QPrinterInfo`).
2. A nyomtatás-párbeszéd nyomtató nélkül kimondja, mit kell tenni. Az eredeti
   Picasa őre (`IDS_MUST_INSTALL_PRINTER`, `stringres.xml`) pontosan ezt
   mondja: „A nyomtatáshoz telepítsen nyomtatót.” A PDF-cél ettől még
   választható marad — ezért az üzenet tájékoztat, nem tilt.

A próbák kattintással nyitják a párbeszédet (menüpont), és −5/0/+5 px
ablakmagassággal nézik, hogy az üzenet látszik-e és nem vágódik-e le.
"""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app as app_csomag
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt

REPO = Path(__file__).resolve().parents[3]
CONTROL = REPO / "packaging" / "debian" / "control.template"

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "PrintDialog.qml"
).read_text(encoding="utf-8")

NINCS_NYOMTATO = "printNoPrinterText"
FORRAS = "A printer must be installed in order to print."
MAGYAR = "A nyomtatáshoz telepítsen nyomtatót."


@pytest.fixture
def magyar_forditas(qt_app):
    from PySide6.QtCore import QTranslator

    from picasapy.app import application

    fordito = QTranslator(qt_app)
    qm = Path(application.__file__).parent / "i18n" / "picasapy_hu.qm"
    assert fordito.load(str(qm)), f"a magyar fordítás nem tölthető be: {qm}"
    assert qt_app.installTranslator(fordito)
    yield
    qt_app.removeTranslator(fordito)


@pytest.fixture
def qml_app_magyar(magyar_forditas, qml_app):
    """A QML a fordító telepítése után töltődjön be."""
    return qml_app


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


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


def _nyisd_meg(window, qt_app):
    """A párbeszéd a Fájl ▸ Nyomtatás… menüpontból nyílik (kattintás)."""
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    tetel = _elem(window, "menuFilePrint")
    assert tetel.property("enabled") is True
    QMetaObject.invokeMethod(
        tetel, "triggered", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    parbeszed = _elem(window, "printDialog")
    assert _var(qt_app, lambda: parbeszed.isVisible())
    return parbeszed


def _recommends_mezo() -> list[str]:
    for sor in CONTROL.read_text(encoding="utf-8").splitlines():
        if sor.startswith("Recommends:"):
            mezok = sor.split(":", 1)[1].split(",")
            return [m.strip().split(" ")[0] for m in mezok if m.strip()]
    return []


class TestCsomagAjanlasok:
    @pytest.mark.parametrize("csomag", ["xdg-utils", "cups-client"])
    def test_recommends_tartalmazza(self, csomag):
        assert csomag in _recommends_mezo(), (
            f"a Recommends sor nem tartalmazza: {csomag}"
        )


class TestNyomtatoNelkulUzenet:
    def test_a_forrasban_ott_van_az_eredeti_szoveg(self):
        assert f'objectName: "{NINCS_NYOMTATO}"' in _QML
        assert f'qsTr("{FORRAS}")' in _QML, (
            "a felirat nem a mért IDS_MUST_INSTALL_PRINTER angol szövege"
        )

    @pytest.mark.parametrize("eltolas", [-5, 0, 5])
    def test_nyomtato_nelkul_latszik_es_nem_vagodik_le(
        self, qml_app_magyar, qt_app, eltolas
    ):
        window, _c, _e = qml_app_magyar
        parbeszed = _nyisd_meg(window, qt_app)
        # tiszta gép: a rendszerben nincs nyomtató
        parbeszed.setProperty("printers", [])
        qt_app.processEvents()

        magassag = parbeszed.height()
        parbeszed.resize(parbeszed.width(), magassag + eltolas)
        assert _var(qt_app, lambda: parbeszed.height() == magassag + eltolas)

        uzenet = _elem(parbeszed, NINCS_NYOMTATO)
        assert uzenet.property("visible") is True
        assert uzenet.property("text") == MAGYAR, (
            "az üzenet nem a hivatalos magyar szöveg"
        )
        alja = uzenet.mapToScene(QPointF(0, uzenet.height())).y()
        assert alja <= parbeszed.height(), (
            f"az üzenet alja ({alja}) kilóg az ablakból "
            f"({parbeszed.height()} px magas)"
        )

        valaszto = _elem(parbeszed, "printPrinterBox")
        assert valaszto.property("count") == 1, (
            "nyomtató nélkül is a PDF-cél kell, hogy választható maradjon"
        )

    def test_nyomtatoval_nincs_uzenet(self, qml_app_magyar, qt_app):
        window, _c, _e = qml_app_magyar
        parbeszed = _nyisd_meg(window, qt_app)
        parbeszed.setProperty("printers", ["Teszt-nyomtato"])
        qt_app.processEvents()

        uzenet = _elem(parbeszed, NINCS_NYOMTATO)
        assert uzenet.property("visible") is False
