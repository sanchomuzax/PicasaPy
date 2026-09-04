"""#2103 — „Nyomtató telepítése": belépési pont a nyomtató saját beállításaihoz.

Az eredeti nyomtatás-panelján van egy gomb (`printpanel/psetupbutton`), ami
a **nyomtató-illesztőprogram** tulajdonságlapját nyitja meg — a klasszikus
háromlépéses Win32-minta (`0x00861750`): `OpenPrinter` →
`DocumentProperties` (méret) → `DocumentProperties` (megjelenítés).

| | angol | magyar |
|---|---|---|
| felirat (`printpanel/setuplabel`) | **Printer Setup** | **Nyomtató telepítése** |
| buboréksúgó (`printpanel/psetupbutton`) | Open printer setup controls for the selected printer | **Nyomtató beállításvezérlőinek megnyitása a kijelölt nyomtatóhoz** |

⚠️ **A tartalom nem másolható:** a `DocumentProperties` a Windows
illesztőprogramé. Linuxon a megfelelője a Qt saját oldalbeállítója. A gomb
**helye és felirata** az, ami átvehető — a próbák ezért a belépési pontot és
a bekötést mérik, nem a párbeszéd tartalmát.
"""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app as app_csomag
from PySide6.QtCore import QMetaObject, QObject, Qt

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "PrintDialog.qml"
).read_text(encoding="utf-8")
#: A forrás-őrökhöz: a QML a hosszú szövegeket tördelheti, a keresett minta
#: viszont egy sor. A sortörés nem tartalmi különbség.
_QML_EGYSOROS = " ".join(_QML.split())
_TS = (
    Path(app_csomag.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

GOMB = "printPrinterSetupButton"


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


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _nyomtatas_parbeszed(window, qt_app):
    """A párbeszéd a MENÜBŐL nyílik — enélkül nem is létezik (Loader).

    A #1472 mintája: előbb megköveteljük, hogy a menütétel egyáltalán
    elérhető legyen, különben egy halott tételen is „sikerülne" a nyitás.
    """
    # a Nyomtatás… csak kijelölt képpel elérhető (#1472)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    tetel = _elem(window, "menuFilePrint")
    assert tetel.property("enabled") is True, (
        "a Nyomtatás… menüpont kijelölt képpel sem elérhető"
    )
    QMetaObject.invokeMethod(
        tetel, "triggered", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    return _elem(window, "printDialog")


class TestAGombLETEZIK:
    def test_a_parbeszedben_ott_van(self):
        assert f'objectName: "{GOMB}"' in _QML, (
            "nincs belépési pont a nyomtató saját beállításaihoz — a "
            "felhasználó nem éri el a papírméretet, a tálcát, a kétoldalast"
        )

    def test_a_MERT_angol_feliratot_hasznalja(self):
        kezd = _QML.index(f'objectName: "{GOMB}"')
        blokk = _QML[kezd:kezd + 900]
        assert 'qsTr("Printer Setup")' in blokk, (
            "a felirat nem a mért `printpanel/setuplabel` szövege"
        )

    def test_a_buboreksugo_is_a_MERT_szoveg(self):
        kezd = _QML_EGYSOROS.index(f'objectName: "{GOMB}"')
        blokk = _QML_EGYSOROS[kezd:kezd + 900]
        assert (
            'qsTr( "Open printer setup controls for the selected printer")'
            in blokk
            or 'qsTr("Open printer setup controls for the selected printer")'
            in blokk
        ), "a buboréksúgó nem a mért szöveg"


class TestAMagyarSzovegek:
    """A hivatalos magyar alakok a `tooltips.xml`-ből — nem szabad
    szabadon fordítani őket."""

    def test_a_ket_MAGYAR_alak_a_forditasban(self):
        for forras, magyar in (
            ("Printer Setup", "Nyomtató telepítése"),
            (
                "Open printer setup controls for the selected printer",
                "Nyomtató beállításvezérlőinek megnyitása a kijelölt "
                "nyomtatóhoz",
            ),
        ):
            assert f"<source>{forras}</source>" in _TS, (
                f"hiányzik a fordítási bejegyzés: {forras}"
            )
            assert f"<translation>{magyar}</translation>" in _TS, (
                f"hiányzik vagy más a magyar alak: {magyar}"
            )


class TestAPdfCelnalINAKTIV:
    def test_pdf_modban_le_van_tiltva(self, qml_app, qt_app):
        """PDF-nél nincs illesztőprogram, tehát nincs mit beállítani."""
        window, _c, _e = qml_app
        parbeszed = _nyomtatas_parbeszed(window, qt_app)
        gomb = _elem(parbeszed, GOMB)

        # a választó 0. eleme a PDF-cél
        _elem(parbeszed, "printPrinterBox").setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert parbeszed.property("pdfSelected") is True
        assert gomb.property("enabled") is False, (
            "PDF-célnál is aktív a nyomtatóbeállítás — nincs mit beállítani"
        )


class TestABekotes:
    def test_a_kattintas_a_VEZERLOT_hivja(self, qml_app, qt_app):
        """A gomb nem díszlet: a vezérlő `openPrinterSetup`-ját süti el,
        a kiválasztott nyomtató nevével."""
        window, _c, _e = qml_app
        parbeszed = _nyomtatas_parbeszed(window, qt_app)

        assert "printController.openPrinterSetup(" in _QML, (
            "a gomb nem a vezérlőt hívja — halott vezérlő"
        )
        assert parbeszed.property("printerName") is not None


# ----------------------------------------------------------------------
# A VEZÉRLŐ oldala. A `QPageSetupDialog` modális rendszerpárbeszéd —
# tesztben megállítaná a futást —, ezért a vezérlő külön metódusban
# gyártja, és itt azt cseréljük le. A termékkódba így nem kerül
# tesztkapcsoló.
# ----------------------------------------------------------------------

import pytest  # noqa: E402
from PySide6.QtGui import QPageLayout, QPageSize  # noqa: E402

from picasapy.app.print_controller import PrintController  # noqa: E402


class HamisParbeszed:
    """A `QPageSetupDialog` helyettese: az `exec()` eredményét a teszt adja."""

    def __init__(self, printer, elfogadja: bool, elrendezes=None):
        self._printer = printer
        self._elfogadja = elfogadja
        self._elrendezes = elrendezes

    def exec(self) -> int:
        if self._elfogadja and self._elrendezes is not None:
            self._printer.setPageLayout(self._elrendezes)
        return 1 if self._elfogadja else 0


@pytest.fixture()
def vezerlo(qt_app):
    return PrintController(lambda: [])


#: Egy név, amit a hamis `QPrinterInfo` ismerni fog.
PROBA_NYOMTATO = "PicasaPy-proba-nyomtato-2103"


class HamisInfo:
    """A `QPrinterInfo` helyettese a modul névterében.

    ⚠️ Enélkül a két legfontosabb próba (az elrendezés megjegyzése és a
    megszakítás) **kimaradna a gépeken, ahol nincs telepített nyomtató** —
    a CI futói ilyenek. A kihagyott próba nem őr: pontosan azt engedné át,
    amit védeni akar.
    """

    def __init__(self, letezik: bool) -> None:
        self._letezik = letezik

    def isNull(self) -> bool:  # noqa: N802 — Qt-névalak
        return not self._letezik

    @staticmethod
    def printerInfo(nev: str) -> "HamisInfo":  # noqa: N802 — Qt-névalak
        return HamisInfo(nev == PROBA_NYOMTATO)

    @staticmethod
    def availablePrinterNames() -> list[str]:  # noqa: N802 — Qt-névalak
        return [PROBA_NYOMTATO]


class TestAVezerloBeallitoja:
    def test_ures_nevre_HIBAT_jelez(self, vezerlo):
        hibak = []
        vezerlo.printFailed.connect(hibak.append)
        assert vezerlo.openPrinterSetup("") is False
        assert hibak, "üres nyomtatónévre némán tér vissza"

    def test_ISMERETLEN_nyomtatora_hibat_jelez(self, vezerlo):
        hibak = []
        vezerlo.printFailed.connect(hibak.append)
        assert vezerlo.openPrinterSetup("nincs-ilyen-nyomtato-2103") is False
        assert hibak

    def test_az_ELFOGADOTT_elrendezest_MEGJEGYZI(self, vezerlo, monkeypatch):
        """A jegy feltétele: „a bezárás után a nyomtatás azt használja" —
        enélkül a párbeszéd díszlet lenne."""
        from PySide6.QtCore import QMarginsF

        import picasapy.app.print_controller as pc_modul

        monkeypatch.setattr(pc_modul, "QPrinterInfo", HamisInfo)
        nev = PROBA_NYOMTATO

        cel = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A5),
            QPageLayout.Orientation.Landscape,
            QMarginsF(),
        )
        monkeypatch.setattr(
            vezerlo,
            "_page_setup_dialog",
            lambda printer: HamisParbeszed(printer, True, cel),
        )
        zarasok = []
        vezerlo.printerSetupClosed.connect(
            lambda n, ok: zarasok.append((n, ok))
        )

        assert vezerlo.openPrinterSetup(nev) is True
        assert zarasok == [(nev, True)]
        assert vezerlo._oldalelrendezes is not None
        assert (
            vezerlo._oldalelrendezes.pageSize().id() == QPageSize.PageSizeId.A5
        )

    def test_a_MEGSZAKITAS_nem_jegyez_meg_semmit(self, vezerlo, monkeypatch):
        import picasapy.app.print_controller as pc_modul

        monkeypatch.setattr(pc_modul, "QPrinterInfo", HamisInfo)
        nev = PROBA_NYOMTATO

        monkeypatch.setattr(
            vezerlo,
            "_page_setup_dialog",
            lambda printer: HamisParbeszed(printer, False),
        )
        zarasok = []
        vezerlo.printerSetupClosed.connect(
            lambda n, ok: zarasok.append((n, ok))
        )

        assert vezerlo.openPrinterSetup(nev) is False
        assert zarasok == [(nev, False)]
        assert vezerlo._oldalelrendezes is None, (
            "megszakításkor is megjegyezte az elrendezést"
        )


class TestANyomtatasHASZNALJA:
    """⚠️ Ez a próba a magvetésből született: az `_alkalmazd_...` hívás
    törlésére EGYETLEN próba sem bukott el, pedig a jegy feltétele
    kimondja, hogy „a bezárás után a nyomtatás azt használja". A gomb
    enélkül díszlet lenne — a párbeszéd megnyílna, a beállítás elveszne."""

    def test_a_printRows_a_MEGJEGYZETT_elrendezessel_indul(
        self, vezerlo, monkeypatch
    ):
        from PySide6.QtCore import QMarginsF

        import picasapy.app.print_controller as pc_modul

        monkeypatch.setattr(pc_modul, "QPrinterInfo", HamisInfo)
        cel = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A5),
            QPageLayout.Orientation.Landscape,
            QMarginsF(),
        )
        monkeypatch.setattr(
            vezerlo,
            "_page_setup_dialog",
            lambda printer: HamisParbeszed(printer, True, cel),
        )
        assert vezerlo.openPrinterSetup(PROBA_NYOMTATO) is True

        latott = {}

        def _hamis_run(printer, *args, **kwargs):
            latott["meret"] = printer.pageLayout().pageSize().id()
            return True

        monkeypatch.setattr(vezerlo, "_run", _hamis_run)
        vezerlo.printRows([0], PROBA_NYOMTATO, "fit", "portrait")

        assert latott.get("meret") == QPageSize.PageSizeId.A5, (
            "a nyomtatás nem a beállítóban elfogadott lapméretet használja "
            "— a párbeszéd díszlet"
        )
