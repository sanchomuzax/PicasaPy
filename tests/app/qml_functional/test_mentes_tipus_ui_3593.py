"""#3593 — a mentési készlet típusa az Új/Módosítás párbeszédben, VALÓDI
kattintással.

A mért űrlap (`newbackupset.fen`):

```
Backup type:  ( ) CD or DVD backup
              ( ) Disk-to-disk backup (for external and network drives)
              [Choose...]   ← csak a lemez-lemez típusnál él
```

#3504: az űrlap ma a `BackupHost` felugró párbeszéde (`backupSetDialog`),
amit a kiadás-panel mentés-üzemmódjának „New Set…"/„Edit Set…" gombja
nyit; korábban ugyanez a `BackupDialog` beágyazott form-rácsa volt.

A gombnyomástól a kész kimenetig a `TestAFutas` osztály méri.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QMetaObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, wait_for_signal

_QML = Path(picasapy.app.__file__).parent / "qml"


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(view, elem, qt_app):
    """Valódi kattintás a vezérlő KÖZEPÉRE.

    A láthatóság-váltás után az elrendezés csak a következő képkockán
    számol újra; offscreen addig a vezérlő a RÉGI helyén áll, és a
    kattintás a szomszédjára esne. Ezért előbb kikényszerítjük az
    elrendezést a vezérlő ősein."""
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
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(ablak, "nyisd")
    qt_app.processEvents()
    yield view, ablak, vezerlo
    view.hide()


class TestAzUrlap:
    def test_uj_keszlet_cd_dvd_tipussal(self, gazda, qt_app):
        view, ablak, vezerlo = gazda
        _kattints(view, _elem(ablak, "publishNewBackupSet"), qt_app)
        _kattints(view, _elem(ablak, "backupTypeCdDvd"), qt_app)

        # CD/DVD-típusnál a hely nem választható — a vezérlő alaphelye áll
        assert _elem(ablak, "backupChooseTarget").property("enabled") is False
        assert _elem(ablak, "backupSetTarget").property("text") == (
            vezerlo.lemezkepAlapHely()
        )

        _kattints(view, _elem(ablak, "backupFormSave"), qt_app)

        keszletek = vezerlo.keszletek()
        assert [k["tipus"] for k in keszletek] == ["cddvd"], (
            ablak.property("uzenet"), ablak.property("urlapNev"),
            ablak.property("urlapTipus"), ablak.property("szerkesztes"))

    def test_lemez_lemez_tipusnal_a_hely_valaszthato(self, gazda, qt_app):
        view, ablak, _ = gazda
        _kattints(view, _elem(ablak, "publishNewBackupSet"), qt_app)
        _kattints(view, _elem(ablak, "backupTypeDisk"), qt_app)

        assert _elem(ablak, "backupChooseTarget").property("enabled") is True
        assert _elem(ablak, "backupSetTarget").property("enabled") is True

    def test_a_szerkeszto_a_tarolt_tipust_mutatja(
        self, gazda, qt_app, tmp_path
    ):
        view, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Lemezre", "", "minden", "cddvd")
        ablak.setProperty("kivalasztott", 0)
        QMetaObject.invokeMethod(ablak, "frissitsd")

        _kattints(view, _elem(ablak, "publishEditBackupSet"), qt_app)

        assert _elem(ablak, "backupTypeCdDvd").property("checked") is True
        assert _elem(ablak, "backupTypeDisk").property("checked") is False


class TestAFutas:
    def test_lemez_lemez_keszlet_mappaba_ment(
        self, gazda, qt_app, tmp_path
    ):
        view, ablak, vezerlo = gazda
        cel = tmp_path / "cel"
        vezerlo.ujKeszlet("Külső", str(cel), "minden", "lemez")
        QMetaObject.invokeMethod(ablak, "frissitsd")
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()

        assert _elem(ablak, "publishBackupOutputMode").property("visible") is False
        # #3594: alapból nincs pipa — a futás a bepipált mappákat viszi;
        # a mappa-lista háttérszálon készül, előbb be kell várni
        assert varj_feltetelre(
            qt_app, lambda: ablak.property("mappakToltodnek") is False)
        qt_app.processEvents()
        _kattints(view, _elem(ablak, "publishBackupSelectAll"), qt_app)
        wait_for_signal(
            vezerlo.futasKesz,
            lambda: _kattints(view, _elem(ablak, "publishBackupGo"), qt_app),
            description="a mappába mentés",
        )

        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["a.jpg", "b.jpg"]

    def test_cd_dvd_keszlet_lemezkepet_ir(self, gazda, qt_app, tmp_path):
        view, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Lemezre", "", "minden", "cddvd")
        cel = Path(vezerlo.lemezkepAlapHely())
        assert tmp_path in cel.parents
        QMetaObject.invokeMethod(ablak, "frissitsd")
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()

        valaszto = _elem(ablak, "publishBackupOutputMode")
        assert valaszto.property("visible") is True
        assert valaszto.property("count") == 2
        # #3594: alapból nincs pipa — a futás a bepipált mappákat viszi;
        # a mappa-lista háttérszálon készül, előbb be kell várni
        assert varj_feltetelre(
            qt_app, lambda: ablak.property("mappakToltodnek") is False)
        qt_app.processEvents()
        _kattints(view, _elem(ablak, "publishBackupSelectAll"), qt_app)
        wait_for_signal(
            vezerlo.lemezkepekKeszek,
            lambda: _kattints(view, _elem(ablak, "publishBackupGo"), qt_app),
            description="a lemezképbe mentés",
        )

        assert list(cel.rglob("*.iso")), "nem készült lemezkép"
