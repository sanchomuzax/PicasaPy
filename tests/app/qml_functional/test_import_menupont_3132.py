"""#3132 — a db3-import belépési pontja: `Eszközök ▸ Import a Picasából…`.

A mag a #3002/#3184 óta kész, de a `src/` alól semmi nem hívta: a felhasználó
nem tudta elindítani. A tulajdonos 2026-09-18-án az **A** megoldást
választotta (menüpont), tehát az átvétel KÉRÉSRE fut és megismételhető.

⚠️ Ez SAJÁT FUNKCIÓ: az eredeti Picasának nincs mit másolni ezen a ponton —
ő MAGA a db3 gazdája, nekünk viszont át kell vennünk tőle. Ezért a tétel a
#1701 jelölését kapja (`sajat: true`), ahogy a duplikátum-KEZELŐ is.

Ez a fájl a bekötést méri (a jegy 4. elfogadási feltétele: „őr a bekötésre,
nem csak a magra"): a menüpont létezik, meg van jelölve sajátként, a jelzése
kimegy, és a párbeszéd a vezérlő SZÁMAIT mutatja.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app as app_csomag
from tests.support.qml_blokk import blokk_horgonyra

_APP = Path(app_csomag.__file__).parent
_MENU = (_APP / "qml" / "PicasaPy" / "PicasaMenuBar.qml").read_text(encoding="utf-8")
_MAIN = (_APP / "qml" / "Main.qml").read_text(encoding="utf-8")
_PARBESZED = (_APP / "qml" / "PicasaPy" / "PicasaDataImportDialog.qml").read_text(encoding="utf-8")
_TS = (_APP / "i18n" / "picasapy_hu.ts").read_text(encoding="utf-8")


def _tetel() -> str:
    return blokk_horgonyra(_MENU, 'objectName: "menuToolsImportFromPicasa"')


class TestAMenupont:
    def test_letezik_az_ESZKOZOK_menuben(self):
        eszkozok = blokk_horgonyra(_MENU, 'title: qsTr("&Tools")')
        assert 'objectName: "menuToolsImportFromPicasa"' in eszkozok, (
            "a db3-importnak nincs belépési pontja az Eszközök menüben"
        )

    def test_SAJAT_funkciokent_van_megjelolve(self):
        """#1701: amit az eredeti nem tud, azt jelöljük — nem adjuk ki
        Picasa-funkciónak."""
        assert "sajat: true" in _tetel()

    def test_a_jelzest_bocsatja_ki_nem_kozvetlenul_a_vezerlot_hivja(self):
        assert "picasaDataImportRequested()" in _tetel()
        assert "signal picasaDataImportRequested()" in _MENU

    def test_a_felirata_le_van_forditva_magyarra(self):
        assert 'text: qsTr("Import from Picasa...")' in _tetel()
        assert "<source>Import from Picasa...</source>" in _TS
        assert "Import a Picasából…" in _TS


class TestABekotes:
    def test_a_Main_qml_a_parbeszedet_nyitja(self):
        assert "onPicasaDataImportRequested" in _MAIN
        assert "picasaDataImportDialog" in _MAIN

    def test_a_parbeszed_a_vezerlo_jelzeseire_iratkozik(self):
        for nev in ("onImportFinished", "onImportFailed", "onNoInstallationFound"):
            assert nev in _PARBESZED, f"hiányzik a(z) {nev} kezelő"

    def test_a_parbeszed_a_vezerlot_INDITJA_el(self):
        assert "startImport()" in _PARBESZED

    def test_a_hianyzo_vezerlore_is_VED(self):
        """#1572: a próbák stub-környezetében nincs minden kontextus-objektum
        — az őr a `scripts/qml_undefined_or.py`."""
        assert 'typeof picasaImportController !== "undefined"' in _PARBESZED


class TestAmitAFelhasznaloLAT:
    def test_mind_a_negy_SZAM_megjelenik(self):
        """A jegy 3. teendője: hány fotóhoz hány adat került be, és mennyit
        hagytunk ki meglévő érték miatt."""
        for mezo in ("mappak", "kulcsszo", "hely", "arc", "kihagyott"):
            assert mezo in _PARBESZED, f"a(z) {mezo} szám nem jelenik meg"

    def test_a_nincs_telepites_eset_KULON_szoveget_kap(self):
        """Nem hiba, hanem üres eredmény — mást kell mondani rá."""
        assert "No Picasa data found" in _PARBESZED
        assert "<source>No Picasa data found" in _TS


# --- ÉLŐ mérés: a betöltött felületen és a valódi párbeszéden -------------

from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl  # noqa: E402
from PySide6.QtQml import QQmlComponent, QQmlEngine  # noqa: E402

import picasapy.app.application as app_module  # noqa: E402

#: a Qt-tulajdonú objektumokat életben kell tartani, amíg a teszt fut
_ELETBEN: list = []


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class _HamisVezerlo(QObject):
    """A valódi vezérlő JELZÉSEIVEL, de db3 nélkül — a felület a számokat a
    jelzésből kapja, nem a fájlrendszerből."""

    from PySide6.QtCore import Property, Signal

    importFinished = Signal(int, int, int, int, int)
    importFailed = Signal(str)
    noInstallationFound = Signal()
    runningChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.inditasok = 0

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return False

    from PySide6.QtCore import Slot

    @Slot()
    def startImport(self) -> None:
        self.inditasok += 1


def _parbeszed(qt_app):
    """A `PicasaDataImportDialog.qml` ÖNÁLLÓ betöltése, hamis vezérlővel."""
    vezerlo = _HamisVezerlo()
    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("picasaImportController", vezerlo)
    elem = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(_APP / "qml" / "PicasaPy" / "PicasaDataImportDialog.qml")
        ),
    )
    assert elem.status() == QQmlComponent.Status.Ready, elem.errorString()
    obj = elem.create()
    assert [e.toString() for e in elem.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _ELETBEN.extend([engine, elem, obj, vezerlo])
    return obj, vezerlo


class TestAzELOFelulet:
    def test_a_menupont_ott_van_es_NEM_tiltott(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        tetel = _elem(window, "menuToolsImportFromPicasa")
        assert tetel.property("enabled") is True, (
            "az import menüpontja le van tiltva — a felhasználó nem éri el"
        )

    def test_a_megnyitas_ELINDITJA_az_atvetelt(self, qt_app):
        parbeszed, vezerlo = _parbeszed(qt_app)
        QMetaObject.invokeMethod(parbeszed, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert vezerlo.inditasok == 1, "a párbeszéd megnyílt, de nem indult import"

    def test_a_JELENTES_szamai_megjelennek_a_feluleten(self, qt_app):
        parbeszed, vezerlo = _parbeszed(qt_app)
        QMetaObject.invokeMethod(parbeszed, "open", Qt.ConnectionType.DirectConnection)
        vezerlo.importFinished.emit(3, 12, 4, 7, 2)
        qt_app.processEvents()
        eredmeny = _elem(parbeszed, "picasaImportResult").property("text")
        for szam in ("3", "12", "4", "7"):
            assert szam in eredmeny, f"a(z) {szam} nem látszik: {eredmeny!r}"
        kihagyott = _elem(parbeszed, "picasaImportSkipped")
        assert kihagyott.property("visible") is True
        assert "2" in kihagyott.property("text")

    def test_ha_nincs_kihagyott_a_sor_sem_latszik(self, qt_app):
        parbeszed, vezerlo = _parbeszed(qt_app)
        QMetaObject.invokeMethod(parbeszed, "open", Qt.ConnectionType.DirectConnection)
        vezerlo.importFinished.emit(1, 1, 0, 0, 0)
        qt_app.processEvents()
        assert _elem(parbeszed, "picasaImportSkipped").property("visible") is False

    def test_a_nincs_adat_eset_SZOVEGET_kap_nem_nullakat(self, qt_app):
        parbeszed, vezerlo = _parbeszed(qt_app)
        QMetaObject.invokeMethod(parbeszed, "open", Qt.ConnectionType.DirectConnection)
        vezerlo.noInstallationFound.emit()
        qt_app.processEvents()
        fejlec = _elem(parbeszed, "picasaImportHeadline").property("text")
        assert "No Picasa data found" in fejlec
        assert _elem(parbeszed, "picasaImportResult").property("visible") is False

    def test_a_HIBA_szovege_kimegy_a_felhasznalonak(self, qt_app):
        parbeszed, vezerlo = _parbeszed(qt_app)
        QMetaObject.invokeMethod(parbeszed, "open", Qt.ConnectionType.DirectConnection)
        vezerlo.importFailed.emit("hiányzó thumbindex")
        qt_app.processEvents()
        fejlec = _elem(parbeszed, "picasaImportHeadline").property("text")
        assert "hiányzó thumbindex" in fejlec
