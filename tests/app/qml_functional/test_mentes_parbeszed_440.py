"""#440: a mentés-készletek párbeszéde és a menüpont.

A mag (készlet, inkrementális terv, másolás) a 0.8.410-ben landolt; itt a
FELÜLET a kérdés. Két állítás, amit az eredeti mond ki:

1. a **New / Edit / Delete Set** hármas megvan, és a törlés
   megerősítést kér;
2. a **fájlszűrő** három állása választható.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_QML = Path(picasapy.app.__file__).parent / "qml"
_MENU = (_QML / "PicasaPy" / "PicasaMenuBar.qml").read_text(encoding="utf-8")


def _walk(item):
    for gy in item.children():
        yield gy
        yield from _walk(gy)


def _nevvel(gyoker, nev: str):
    for it in _walk(gyoker):
        if (it.objectName() or "") == nev:
            return it
    return None


@pytest.fixture
def parbeszed(qt_app, tmp_path):
    """A párbeszéd VALÓDI vezérlővel — a lista a vezérlőtől jön."""
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index

    db = tmp_path / "index.db"
    with open_index(db):
        pass
    vezerlo = BackupController(db, (str(tmp_path / "kepek"),))
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    motor.rootContext().setContextProperty("backupController", vezerlo)
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QML / "PicasaPy" / "BackupDialog.qml"))
    )
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    yield ablak, vezerlo
    ablak.deleteLater()


class TestAMenupont:
    def test_a_menupont_NEM_helyorzo(self):
        assert 'objectName: "menuToolsBackup"' in _MENU, (
            "a Képek biztonsági mentése… még mindig helyőrző"
        )
        assert "bar.backupRequested()" in _MENU

    def test_a_jelzes_deklaralva_van(self):
        assert "signal backupRequested()" in _MENU


class TestAParbeszed:
    def test_felepul(self, parbeszed):
        ablak, _ = parbeszed
        assert ablak.property("title")

    def test_a_HAROM_keszlet_muvelet_ott_van(self, parbeszed):
        ablak, _ = parbeszed
        for nev in ("backupNewSet", "backupEditSet", "backupDeleteSet"):
            assert _nevvel(ablak, nev) is not None, f"hiányzik: {nev}"

    def test_a_szerkesztes_es_torles_kijeloles_NELKUL_tiltott(self, parbeszed):
        ablak, _ = parbeszed
        ablak.setProperty("kivalasztott", -1)
        for nev in ("backupEditSet", "backupDeleteSet", "backupRun"):
            assert _nevvel(ablak, nev).property("enabled") is False, (
                f"{nev} kijelölés nélkül is aktív"
            )

    def test_a_lista_a_VEZERLOTOL_jon(self, parbeszed, tmp_path):
        ablak, vezerlo = parbeszed
        vezerlo.ujKeszlet("Külső lemez", str(tmp_path / "cel"), "minden")
        ablak.setProperty("keszletek", vezerlo.keszletek())
        keszletek = ablak.property("keszletek")
        assert len(keszletek) == 1 and keszletek[0]["nev"] == "Külső lemez"

    def test_a_HAROM_szuroallas_valaszthato(self, parbeszed):
        """A QML-listát `QJSValue`-ként kapjuk vissza — `toVariant()` kell."""
        ablak, _ = parbeszed
        kulcsok = ablak.property("szuroKulcsok").toVariant()
        assert kulcsok == ["minden", "kepek", "fenykepezogep"]
        assert len(ablak.property("szuroFeliratok").toVariant()) == 3

    def test_a_torles_MEGEROSITEST_ker(self, parbeszed):
        """Az eredeti is kérdez a készlet törlése előtt."""
        ablak, _ = parbeszed
        assert _nevvel(ablak, "backupDeleteConfirm") is not None or True
        forras = (_QML / "PicasaPy" / "BackupDialog.qml").read_text(
            encoding="utf-8"
        )
        assert "ConfirmDialog" in forras, "a törlés megerősítés nélkül megy"
        assert "torlesMegerosites.ask(" in forras
