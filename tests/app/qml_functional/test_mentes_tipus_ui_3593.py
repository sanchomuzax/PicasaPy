"""#3593 — a mentési készlet típusa a párbeszédben, VALÓDI kattintással.

A mért űrlap (`newbackupset.fen`):

```
Backup type:  ( ) CD or DVD backup
              ( ) Disk-to-disk backup (for external and network drives)
              [Choose...]   ← csak a lemez-lemez típusnál él
```

⚠️ A mérés közben előkerült egy ÉLES hiba: a „Back Up" gomb egy
`backupOutputMode` azonosítóra hivatkozott, ami nem létezett (csak
`objectName` volt) — a kattintás hibára futott, és a mentés el sem
indult. A `TestAFutas` osztály ezt a gombnyomástól a kész kimenetig méri.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QMetaObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_signal

_QML = Path(picasapy.app.__file__).parent / "qml"


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(ablak, elem, qt_app):
    """Valódi kattintás a vezérlő KÖZEPÉRE.

    A láthatóság-váltás után az elrendezés (`RowLayout`) csak a következő
    képkockán számol újra; offscreen addig a vezérlő a RÉGI helyén áll, és
    a kattintás a szomszédjára esne. Ezért előbb kikényszerítjük az
    elrendezést a vezérlő ősein."""
    qt_app.processEvents()
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


@pytest.fixture
def parbeszed(qt_app, tmp_path, monkeypatch):
    # a lemezkép-alaphely a tmp alá — SOHA ne a fejlesztő Képek mappájába
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    make_jpeg(gyoker / "b.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    vezerlo = BackupController(db, (str(gyoker),))
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    motor.rootContext().setContextProperty("backupController", vezerlo)
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QML / "PicasaPy" / "BackupDialog.qml"))
    )
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    QMetaObject.invokeMethod(ablak, "open")
    qt_app.processEvents()
    yield ablak, vezerlo
    ablak.setProperty("visible", False)
    ablak.deleteLater()


class TestAzUrlap:
    def test_uj_keszlet_cd_dvd_tipussal(self, parbeszed, qt_app):
        ablak, vezerlo = parbeszed
        _kattints(ablak, _elem(ablak, "backupNewSet"), qt_app)
        _kattints(ablak, _elem(ablak, "backupTypeCdDvd"), qt_app)

        # CD/DVD-típusnál a hely nem választható — a vezérlő alaphelye áll
        assert _elem(ablak, "backupChooseTarget").property("enabled") is False
        assert _elem(ablak, "backupSetTarget").property("text") == (
            vezerlo.lemezkepAlapHely()
        )

        _kattints(ablak, _elem(ablak, "backupFormSave"), qt_app)

        keszletek = vezerlo.keszletek()
        assert [k["tipus"] for k in keszletek] == ["cddvd"], (
            ablak.property("uzenet"), ablak.property("urlapNev"),
            ablak.property("urlapTipus"), ablak.property("szerkesztes"))

    def test_lemez_lemez_tipusnal_a_hely_valaszthato(self, parbeszed, qt_app):
        ablak, _ = parbeszed
        _kattints(ablak, _elem(ablak, "backupNewSet"), qt_app)
        _kattints(ablak, _elem(ablak, "backupTypeDisk"), qt_app)

        assert _elem(ablak, "backupChooseTarget").property("enabled") is True
        assert _elem(ablak, "backupSetTarget").property("enabled") is True

    def test_a_szerkeszto_a_tarolt_tipust_mutatja(
        self, parbeszed, qt_app, tmp_path
    ):
        ablak, vezerlo = parbeszed
        vezerlo.ujKeszlet("Lemezre", "", "minden", "cddvd")
        ablak.setProperty("kivalasztott", 0)
        QMetaObject.invokeMethod(ablak, "frissitsd")

        _kattints(ablak, _elem(ablak, "backupEditSet"), qt_app)

        assert _elem(ablak, "backupTypeCdDvd").property("checked") is True
        assert _elem(ablak, "backupTypeDisk").property("checked") is False


class TestAFutas:
    def test_lemez_lemez_keszlet_mappaba_ment(
        self, parbeszed, qt_app, tmp_path
    ):
        ablak, vezerlo = parbeszed
        cel = tmp_path / "cel"
        vezerlo.ujKeszlet("Külső", str(cel), "minden", "lemez")
        QMetaObject.invokeMethod(ablak, "frissitsd")
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()

        assert _elem(ablak, "backupOutputMode").property("visible") is False
        # #3594: alapból nincs pipa — a futás a bepipált mappákat viszi
        _kattints(ablak, _elem(ablak, "backupSelectAll"), qt_app)
        wait_for_signal(
            vezerlo.futasKesz,
            lambda: _kattints(ablak, _elem(ablak, "backupRun"), qt_app),
            description="a mappába mentés",
        )

        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["a.jpg", "b.jpg"]

    def test_cd_dvd_keszlet_lemezkepet_ir(self, parbeszed, qt_app, tmp_path):
        ablak, vezerlo = parbeszed
        vezerlo.ujKeszlet("Lemezre", "", "minden", "cddvd")
        cel = Path(vezerlo.lemezkepAlapHely())
        assert tmp_path in cel.parents
        QMetaObject.invokeMethod(ablak, "frissitsd")
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()

        valaszto = _elem(ablak, "backupOutputMode")
        assert valaszto.property("visible") is True
        assert valaszto.property("count") == 2
        # #3594: alapból nincs pipa — a futás a bepipált mappákat viszi
        _kattints(ablak, _elem(ablak, "backupSelectAll"), qt_app)
        wait_for_signal(
            vezerlo.lemezkepekKeszek,
            lambda: _kattints(ablak, _elem(ablak, "backupRun"), qt_app),
            description="a lemezképbe mentés",
        )

        assert list(cel.rglob("*.iso")), "nem készült lemezkép"
