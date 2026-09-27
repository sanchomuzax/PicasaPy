"""#3713 — a mentés-panel indítógombja (`publishBackupGo`) a kiválasztott
készlet szerint „Biztonsági mentés" vagy „Írás", nem állandó „Lemezre írás".

Az eredetiben a `publish/backup_go` felirata futásidőben változik (spec
`docs/specs/biztonsagi-mentes.md` 15.3/1. szabály, `0x0067051b`–`0x00670581`):
ha van kiválasztott készlet (neve nem üres) → `il_BurnPanel::bkbutton` =
„Biztonsági mentés"; ha nincs → `il_BurnPanel::burnbutton` = „Írás". A
gombkattintás valódi `QTest.mouseClick` — a `test_mentes_terv_klikk_3645.py`
mintája —, a felirat a betöltött magyar `.qm`-mel is ellenőrizve.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import (
    QCoreApplication, QMetaObject, QPoint, QPointF, Qt, QTranslator,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, wait_for_signal

_QML = Path(picasapy.app.__file__).parent / "qml"
_I18N = _QML.parent / "i18n"


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


def _lathato_sorok(view):
    """A nyitott legördülő LÁTHATÓ sorai, fentről lefelé — a
    `test_qml_options_dialog._lathato_sorok` mintája (a sor saját `text`-je
    üres, a feliratot a belső `Text` rajzolja, ezért a sorrend azonosít)."""
    sorok = []
    verem = [view.contentItem()]
    while verem:
        elem = verem.pop()
        cn = elem.metaObject().className()
        if elem.isVisible() and ("ItemDelegate" in cn or "MenuItem" in cn):
            sorok.append(elem)
        verem.extend(elem.childItems())
    return sorted(sorok, key=lambda e: e.mapToScene(QPointF(0, 0)).y())


def _valassz_keszletet(view, qt_app, kombo, index):
    """A `publishBackupSetMenu` legördülő lenyitása és az `index`. sorának
    kiválasztása — mindkettő VALÓDI kattintás."""
    modell = kombo.property("model")
    _kattints(view, kombo, qt_app)
    assert varj_feltetelre(
        qt_app, lambda: len(_lathato_sorok(view)) == len(modell)
    ), "a legördülő lista nem nyílt le"
    _kattints(view, _lathato_sorok(view)[index], qt_app)


@pytest.fixture
def gazda(qt_app, tmp_path, monkeypatch):
    # a hivatalos magyar feliratokkal mérünk (`il_BurnPanel::bkbutton`/
    # `burnbutton`)
    fordito = QTranslator()
    assert fordito.load("picasapy_hu", str(_I18N))
    QCoreApplication.installTranslator(fordito)

    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    vezerlo = BackupController(db, (str(gyoker),))
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(ablak, "nyisd")
    qt_app.processEvents()

    yield view, ablak, vezerlo

    view.hide()
    QCoreApplication.removeTranslator(fordito)


class TestAGombFelirata:
    def test_nincs_kivalasztott_keszlet_iras_feliratot_mutat(
        self, gazda, qt_app, tmp_path
    ):
        view, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        QMetaObject.invokeMethod(ablak, "frissitsd")
        qt_app.processEvents()

        assert ablak.property("kivalasztott") == -1
        assert _elem(ablak, "publishBackupGo").property("text") == "Írás"

    def test_kivalasztott_keszletnel_biztonsagi_mentes_feliratot_mutat(
        self, gazda, qt_app, tmp_path
    ):
        view, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        QMetaObject.invokeMethod(ablak, "frissitsd")
        qt_app.processEvents()
        _valassz_keszletet(view, qt_app, _elem(ablak, "publishBackupSetMenu"), 0)

        assert _elem(ablak, "publishBackupGo").property("text") == (
            "Biztonsági mentés"
        )

    def test_masik_keszletre_valtva_a_felirat_visszavaltozik(
        self, gazda, qt_app, tmp_path
    ):
        """A gomb felirata a KIVÁLASZTÁSSAL együtt vált, nem csak induláskor
        — a váltás VALÓDI kattintással a `publishBackupSetMenu` legördülőn."""
        view, ablak, vezerlo = gazda
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        vezerlo.ujKeszlet("Második", str(tmp_path / "cel2"), "minden")
        QMetaObject.invokeMethod(ablak, "frissitsd")
        qt_app.processEvents()
        gomb = _elem(ablak, "publishBackupGo")
        kombo = _elem(ablak, "publishBackupSetMenu")

        assert ablak.property("kivalasztott") == -1
        assert gomb.property("text") == "Írás"

        _valassz_keszletet(view, qt_app, kombo, 0)
        assert ablak.property("kivalasztott") == 0
        assert gomb.property("text") == "Biztonsági mentés"

        _valassz_keszletet(view, qt_app, kombo, 1)
        assert ablak.property("kivalasztott") == 1
        assert gomb.property("text") == "Biztonsági mentés"


class TestAKattintasFunkciojaMegmarad:
    """A felirat-javítás nem törheti a valódi mentést — VALÓDI kattintással."""

    def test_biztonsagi_mentes_feliratu_gomb_kattintva_tenylegesen_ment(
        self, gazda, qt_app, tmp_path
    ):
        view, ablak, vezerlo = gazda
        cel = tmp_path / "cel"
        vezerlo.ujKeszlet("Külső", str(cel), "minden")
        QMetaObject.invokeMethod(ablak, "frissitsd")
        ablak.setProperty("kivalasztott", 0)
        qt_app.processEvents()

        gomb = _elem(ablak, "publishBackupGo")
        assert gomb.property("text") == "Biztonsági mentés"

        assert varj_feltetelre(
            qt_app, lambda: ablak.property("mappakToltodnek") is False)
        qt_app.processEvents()
        _kattints(view, _elem(ablak, "publishBackupSelectAll"), qt_app)
        wait_for_signal(
            vezerlo.futasKesz,
            lambda: _kattints(view, gomb, qt_app),
            description="a mappába mentés",
        )

        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["a.jpg"]
