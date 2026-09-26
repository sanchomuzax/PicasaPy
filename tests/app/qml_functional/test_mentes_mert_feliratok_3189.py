"""#3189: a mentés-felület MÉRT feliratai az eredeti Picasából.

## A mérés

| elem / szövegkulcs | angol | hivatalos magyar | forrás |
|---|---|---|---|
| `publish/label_backupname` | Backup Set | **Mentési készlet** | `ajandek-cd-kimenet.md` 13.2 |
| `il_BurnPanel::bksetname` | My Backup Set | **Saját mentési készlet** | `biztonsagi-mentes.md` 9. |
| `il_NewBkDialog::EditOKButton` | Change | **Módosítás** | ugyanott |
| `il_BurnPanel::BackupCopy::3` | Backup Complete | **A mentés elkészült** | ugyanott |
| `il_BurnPanel::BackupCopy::1` | Copying (%1$d/%2$d) files | **Fájlok másolása (…)** | ugyanott |

Ezek eddig **saját fogalmazású** szövegek voltak nálunk („Name:",
üres névmező, „OK", „Backup complete: %1 file(s).").

## ⚠️ Amit SZÁNDÉKOSAN nem veszünk át

Az eredeti magyar `BackupCopy::1` sora **megcseréli a két argumentumot**
(`%2$d/%1$d`), tehát „kész/összes" helyett „összes/kész"-t írna ki. Ez az
eredeti hibája, nem a szöveg jelentése — a sorrendünk marad `kész/összes`.

## Ami NEM ebben van

A `publish` panel alakja (311×166 lépés-keretek) és az Ajándék-CD mód — a
#2508-on, illetve a #2074 tulajdonosi döntése után.

## #3504

A mentés-üzemmód a `BackupDialog` külön ablaka helyett a kiadás-panel
(`PublishPanel` + `BackupHost`) mentés-üzemmódja lett — a MÉRT `backup_
group` vezérlők (`publish/label_backupname` és társai) a `PublishPanel`-be
kerültek, az Új/Módosítás párbeszéd és az állapot-üzenetek a
`BackupHost`-ba.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_PANEL = _QML / "PublishPanel.qml"
_GAZDA = _QML / "BackupHost.qml"
_TS = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"


def _forras(fajl: Path) -> str:
    return fajl.read_text(encoding="utf-8")


def _ts() -> str:
    return _TS.read_text(encoding="utf-8")


def _kontextus_blokk(szoveg: str, nev: str) -> str:
    kezd = szoveg.index(f"<name>{nev}</name>")
    return szoveg[kezd:szoveg.index("</context>", kezd)]


class TestAMertFeliratok:
    def test_a_nev_mezo_felirata_a_MERT(self):
        """`publish/label_backupname` — nem a saját „Name:"."""
        panel = _forras(_PANEL)
        gazda = _forras(_GAZDA)
        assert 'qsTr("Backup Set")' in panel
        assert 'qsTr("Backup Set")' in gazda
        assert 'qsTr("Name:")' not in panel
        assert 'qsTr("Name:")' not in gazda, (
            "a sajat fogalmazasu Name: felirat meg bent van"
        )

    def test_az_uj_keszlet_ALAPNEVET_kap(self):
        """Az eredeti nem üres mezővel indít (`il_BurnPanel::bksetname`)."""
        assert 'host.urlapNev = qsTr("My Backup Set")' in _forras(_GAZDA)

    def test_a_szerkesztes_gombja_MODOSITAS(self):
        """`il_NewBkDialog::EditOKButton` — csak SZERKESZTÉSKOR."""
        forras = _forras(_GAZDA)
        assert 'qsTr("Change") : qsTr("OK")' in forras, (
            "a Change/OK kettosseg hianyzik - szerkeszteskor Modositas kell"
        )

    def test_a_zaro_uzenet_a_MERT(self):
        forras = _forras(_GAZDA)
        assert 'qsTr("Backup Complete")' in forras
        assert "Backup complete: %1 file(s)." not in forras


class TestAMagyarForditasok:
    def test_mind_a_negy_uj_szoveg_le_van_forditva(self):
        blokk = _kontextus_blokk(_ts(), "BackupHost")
        vart = {
            "Backup Set": "Mentési készlet",
            "My Backup Set": "Saját mentési készlet",
            "Change": "Módosítás",
            "Backup Complete": "A mentés elkészült",
        }
        for forras, magyar in vart.items():
            assert f"<source>{forras}</source>" in blokk, (
                f"a(z) {forras} nincs a BackupHost kontextusaban"
            )
            assert f"<translation>{magyar}</translation>" in blokk, (
                f"hiányzik a fordítás: {magyar}"
            )

    def test_a_masolas_sora_a_MERT_magyart_kapta(self):
        blokk = _kontextus_blokk(_ts(), "BackupHost")
        assert "<translation>Fájlok másolása (%1/%2)</translation>" in blokk

    def test_az_argumentum_sorrend_NEM_fordul_meg(self):
        """Az eredeti magyar sora `%2$d/%1$d`-t ír — ezt nem vesszük át."""
        blokk = _kontextus_blokk(_ts(), "BackupHost")
        assert "Fájlok másolása (%2/%1)" not in blokk


_QMLDIR = Path(picasapy.app.__file__).parent / "qml"


def _bejar(elem):
    for gy in elem.children():
        yield gy
        yield from _bejar(gy)


def _nevvel(gyoker, nev: str) -> QObject | None:
    for it in _bejar(gyoker):
        if (it.objectName() or "") == nev:
            return it
    return None


@pytest.fixture
def gazda(qt_app, tmp_path):
    """A gazda VALÓDI vezérlővel (a #440 fixtúrájának alakja)."""
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index

    db = tmp_path / "index.db"
    with open_index(db):
        pass
    vezerlo = BackupController(db, (str(tmp_path / "kepek"),))
    motor = QQmlEngine()
    motor.addImportPath(str(_QMLDIR))
    motor.rootContext().setContextProperty("backupController", vezerlo)
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QMLDIR / "PicasaPy" / "BackupHost.qml"))
    )
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    yield ablak, vezerlo
    ablak.deleteLater()


class TestAMukodesben:
    """A forrás-őr nem elég: a ténylegesen MEGJELENŐ szöveget mérjük."""

    def test_az_UJ_keszlet_urlapja_alapnevvel_nyilik(self, gazda, qt_app):
        ablak, _ = gazda
        ablak.metaObject().invokeMethod(ablak, "ujKeszletUrlap")
        qt_app.processEvents()

        mezo = _nevvel(ablak, "backupSetName")
        assert mezo is not None
        assert mezo.property("text") == "My Backup Set", (
            f"az új készlet neve nem az alapnév: {mezo.property('text')!r}"
        )

    def test_a_MENTES_gomb_uj_keszletnel_OK(self, gazda, qt_app):
        ablak, _ = gazda
        ablak.metaObject().invokeMethod(ablak, "ujKeszletUrlap")
        qt_app.processEvents()

        assert _nevvel(ablak, "backupFormSave").property("text") == "OK"

    def test_a_MENTES_gomb_szerkeszteskor_Change(self, gazda, qt_app, tmp_path):
        ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Proba", str(tmp_path / "cel"), "minden")
        ablak.setProperty("keszletek", vezerlo.keszletek())
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()
        ablak.metaObject().invokeMethod(ablak, "szerkesztoUrlap")
        qt_app.processEvents()

        assert _nevvel(ablak, "backupFormSave").property("text") == "Change", (
            "szerkesztéskor a mért felirat Change (Módosítás)"
        )
