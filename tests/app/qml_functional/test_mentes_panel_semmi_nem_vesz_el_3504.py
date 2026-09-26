"""#3504 — „semmi nem veszhet el" a párbeszédből a panelre költözéskor.

Az átnézés (#3673) három veszteséget talált; ez a fájl mindhármat VALÓDI
kattintással (vagy a teljes ablakban) méri:

1. a készlet CÉLHELYE és UTOLSÓ FUTÁSA eltűnt — a régi ablak listája
   soronként mutatta („%1 — last run: %2" / „%1 — not run yet"). Most a
   mért `publish/backupinfo` állapotsor mutatja, amelynek a helyőrzője az
   eredetiben is „active backup set info";
2. az Új/Módosítás űrlap `AcceptRole`-lal bezárult a mentés ELŐTT — ha a
   vezérlő elutasította (üres név, hiányzó hely), a beírt adat elveszett.
   A régi ablak nyitva tartotta;
3. az Ajándék-CD és a mentés panelje egymásra nyílhatott.

⚠️ Az EGYETLEN készlet törlése szándékosan nem lehetséges: az eredetiben a
`publish/deletebackupset` rejtett, ha a készletek száma legfeljebb egy
(`biztonsagi-mentes.md` 15.3/2). Ez nem veszteség, hanem a mért viselkedés
— a teszt ki is mondja.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg

_QML = Path(picasapy.app.__file__).parent / "qml"


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(view, elem, qt_app):
    qt_app.processEvents()
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


@pytest.fixture
def gazda(qt_app, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    vezerlo = BackupController(db, (str(gyoker),))
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(ablak, "nyisd")
    qt_app.processEvents()
    yield view, ablak, vezerlo
    view.hide()


class TestACelhelyEsAzUtolsoFutas:
    def test_a_valasztott_keszlet_celhelye_latszik(
        self, gazda, qt_app, tmp_path
    ):
        _, ablak, vezerlo = gazda
        cel = str(tmp_path / "cel")
        vezerlo.ujKeszlet("Külső", cel, "minden", "lemez")
        qt_app.processEvents()
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()

        info = _elem(ablak, "publishBackupInfo")
        assert info.isVisible()
        assert info.property("text") == f"{cel} — not run yet"

    def test_futas_utan_az_utolso_futas_is_latszik(
        self, gazda, qt_app, tmp_path
    ):
        _, ablak, vezerlo = gazda
        cel = str(tmp_path / "cel")
        vezerlo.ujKeszlet("Külső", cel, "minden", "lemez")
        keszlet = vezerlo.keszletek()[0]
        # az utolsó futás a nyilvántartásból jön — a vezérlő adja
        ablak.setProperty("keszletek", [
            {**keszlet, "utolsoFutas": "2026-09-26 10:00"}])
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()

        assert _elem(ablak, "publishBackupInfo").property("text") == (
            f"{cel} — last run: 2026-09-26 10:00")

    def test_az_uzenet_elsobbseget_kap_de_keszletvaltaskor_eltunik(
        self, gazda, qt_app, tmp_path
    ):
        _, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Egy", str(tmp_path / "c1"), "minden", "lemez")
        vezerlo.ujKeszlet("Kettő", str(tmp_path / "c2"), "minden", "lemez")
        ablak.setProperty("kivalasztott", 0)
        ablak.setProperty("uzenet", "Backup Complete")
        qt_app.processEvents()
        info = _elem(ablak, "publishBackupInfo")
        assert info.property("text") == "Backup Complete"

        ablak.setProperty("kivalasztott", 1)
        qt_app.processEvents()
        assert info.property("text").startswith(str(tmp_path / "c"))


class TestAzUrlapNemVesziElAzAdatot:
    def test_elutasitott_keszletnel_az_urlap_nyitva_marad(
        self, gazda, qt_app
    ):
        view, ablak, vezerlo = gazda
        _kattints(view, _elem(ablak, "publishNewBackupSet"), qt_app)
        _kattints(view, _elem(ablak, "backupTypeDisk"), qt_app)
        # lemez-lemez típus, hely NÉLKÜL → a vezérlő elutasítja
        _kattints(view, _elem(ablak, "backupFormSave"), qt_app)

        assert vezerlo.keszletek() == []
        assert ablak.property("szerkesztes") is True
        urlap = ablak.findChild(QObject, "backupSetDialog")
        assert urlap.property("visible") is True, "az űrlap bezárult"
        assert _elem(ablak, "backupSetName").property("text") == (
            "My Backup Set"), "a beírt név elveszett"
        hiba = _elem(ablak, "backupFormError")
        assert hiba.isVisible()
        assert hiba.property("text") == "Choose where to save the backup."

    def test_sikeres_mentes_utan_bezarul(self, gazda, qt_app, tmp_path):
        view, ablak, vezerlo = gazda
        _kattints(view, _elem(ablak, "publishNewBackupSet"), qt_app)
        _kattints(view, _elem(ablak, "backupTypeDisk"), qt_app)
        ablak.setProperty("urlapCel", str(tmp_path / "cel"))
        _kattints(view, _elem(ablak, "backupFormSave"), qt_app)

        assert [k["nev"] for k in vezerlo.keszletek()] == ["My Backup Set"]
        assert ablak.property("szerkesztes") is False
        assert ablak.property("urlapHiba") == ""


class TestAzEgyetlenKeszlet:
    def test_egyetlen_keszlet_nem_torolheto_ez_a_mert_viselkedes(
        self, gazda, qt_app, tmp_path
    ):
        _, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Egy", str(tmp_path / "c1"), "minden", "lemez")
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()
        assert not _elem(ablak, "publishDeleteBackupSet").isVisible()

        vezerlo.ujKeszlet("Kettő", str(tmp_path / "c2"), "minden", "lemez")
        qt_app.processEvents()
        assert _elem(ablak, "publishDeleteBackupSet").isVisible()


class TestEgyszerreEgyUzemmod:
    """A kiadás-panel egyszerre egy üzemmódban látszik (teljes ablak)."""

    def test_a_ket_panel_kizarja_egymast(self, qml_app, qt_app):
        window, _, _ = qml_app
        ajandek = window.findChild(QObject, "giftCdHost")
        mentes = window.findChild(QObject, "backupHost")
        assert ajandek is not None and mentes is not None

        QMetaObject.invokeMethod(ajandek, "nyisd")
        qt_app.processEvents()
        QMetaObject.invokeMethod(mentes, "nyisd")
        qt_app.processEvents()
        assert mentes.property("nyitva") is True
        assert ajandek.property("nyitva") is False

        QMetaObject.invokeMethod(ajandek, "nyisd")
        qt_app.processEvents()
        assert ajandek.property("nyitva") is True
        assert mentes.property("nyitva") is False
