"""#3681: a mentés-panel „Készlet módosítása…" gombja a hivatalos
„Készlet szerkesztése" feliratot kapja.

A `publish/editbackupset` gomb angol forrása (`Edit Set...`) marad — csak a
magyar FORDÍTÁS változik. A hivatalos magyar felirat forrása a
`~/picasapy-agent/referencia/panel-feliratok-hu.tsv` (`tooltips` · `Label` ·
`publish/editbackupset` → „Készlet szerkesztése").

A renderelt gombon azt is kimondjuk, hogy a hosszabb felirat elfér: nem
csonk, és nem magasabb a gombnál (a `test_mentes_panel_geometria_3504.py`
mintájára, a gazdát a SAJÁT magasságán renderelve).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QCoreApplication, QMetaObject, QTranslator
from PySide6.QtQuick import QQuickItem

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre

_TS = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
_QML = Path(picasapy.app.__file__).parent / "qml"
_HIVATALOS = "Készlet szerkesztése"


def _kontextus_blokk(nev: str) -> str:
    szoveg = _TS.read_text(encoding="utf-8")
    kezd = szoveg.index(f"<name>{nev}</name>")
    return szoveg[kezd:szoveg.index("</context>", kezd)]


def test_a_szerkesztes_gomb_forditasa_HIVATALOS():
    blokk = _kontextus_blokk("PublishPanel")
    kezd = blokk.index("<source>Edit Set...</source>")
    uzenet = blokk[kezd:blokk.index("</message>", kezd)]
    assert f"<translation>{_HIVATALOS}</translation>" in uzenet, (
        "a hivatalos felirat 'Készlet szerkesztése', nem 'Készlet módosítása…'"
    )


def test_a_qm_bol_is_a_hivatalos_felirat_jon(qt_app):
    fordito = QTranslator()
    assert fordito.load("picasapy_hu", str(_TS.parent))
    assert fordito.translate("PublishPanel", "Edit Set...") == _HIVATALOS


@pytest.fixture
def magyar_panel(qt_app, tmp_path, monkeypatch):
    fordito = QTranslator()
    assert fordito.load("picasapy_hu", str(_TS.parent))
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
    vezerlo.ujKeszlet("Külső meghajtó", str(tmp_path / "cel"), "minden",
                      "lemez")
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(ablak, "nyisd")
    ablak.setProperty("kivalasztott", 0)
    assert varj_feltetelre(
        qt_app, lambda: ablak.property("mappakToltodnek") is False)
    qt_app.processEvents()
    try:
        yield ablak
    finally:
        view.hide()
        QCoreApplication.removeTranslator(fordito)


def test_a_renderelt_gomb_felirata_elfer(magyar_panel):
    gomb = magyar_panel.findChild(QQuickItem, "publishEditBackupSet")
    assert gomb is not None
    assert gomb.isVisible() and gomb.width() > 0 and gomb.height() > 0
    assert gomb.property("text") == _HIVATALOS
    felirat = gomb.property("contentItem")
    assert felirat.property("text") == _HIVATALOS
    assert felirat.property("truncated") is False
    assert felirat.property("paintedHeight") <= felirat.height() + 0.5
    assert felirat.property("paintedHeight") <= gomb.height()
    assert felirat.property("paintedWidth") <= felirat.width() + 0.5
