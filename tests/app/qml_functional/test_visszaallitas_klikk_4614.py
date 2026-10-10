"""#4614: a mentési panelről, kattintással állítunk vissza képeket."""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QMetaObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.burn.iso import iso_kiirasa
from support.backup_host_harness import epits_ablakot
from support.qt_wait import varj_feltetelre

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
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("forras_tipus", ("mappa", "iso"))
@pytest.mark.parametrize("ablakmagassag_elteres", (-5, 0, 5))
def test_kattintasra_mappabol_es_iso_kepbol_bajtra_pontosan_visszaallit(
    qt_app, tmp_path, forras_tipus, ablakmagassag_elteres
):
    kepek = {
        "kep.jpg": b"PicasaPy restore click-through 1\x00\xff",
        "masik.jpg": b"PicasaPy restore click-through 2\x00\x91",
    }
    for nev, adat in kepek.items():
        kep = tmp_path / "forras" / "utazas" / nev
        kep.parent.mkdir(parents=True, exist_ok=True)
        kep.write_bytes(adat)

    if forras_tipus == "mappa":
        forras = tmp_path / "mappas-mentes"
        (forras / "utazas").mkdir(parents=True)
        sorok = []
        for nev, adat in kepek.items():
            (forras / "utazas" / nev).write_bytes(adat)
            sorok.append(f"utazas/{nev}\t{len(adat)}\t123")
        (forras / "files.txt").write_text("\n".join(sorok) + "\n", encoding="utf-8")
    else:
        for sorszam, (nev, adat) in enumerate(kepek.items(), start=1):
            kep = tmp_path / "forras" / "utazas" / nev
            lista = _manifeszt(
                tmp_path, f"utazas/{nev}\t{len(adat)}\t123\n"
            )
            iso = iso_kiirasa(
                [(f"utazas/{nev}", kep), ("files.txt", lista)],
                tmp_path / "lemezkeszlet" / f"picasapy-mentes-{sorszam:02d}.iso",
                ido=0,
            )
            if sorszam == 1:
                forras = iso

    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index

    db = tmp_path / "index.db"
    with open_index(db):
        pass
    vezerlo = BackupController(db, ())
    view, host = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(host, "nyisd")
    qt_app.processEvents()
    view.resize(view.width(), view.height() + ablakmagassag_elteres)

    _kattints(view, _elem(host, "publishBackupRestore"), qt_app)
    assert host.property("visszaallitasNyitva") is True
    host.setProperty("visszaallitasForras", str(forras))
    host.setProperty("visszaallitasCel", str(tmp_path / "visszaallitott"))
    qt_app.processEvents()
    for nev, ertek in (
        ("backupRestoreSource", str(forras)),
        ("backupRestoreTarget", str(tmp_path / "visszaallitott")),
    ):
        assert _elem(host, nev).property("text") == ertek

    _kattints(view, _elem(host, "backupRestoreGo"), qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: host.property("uzenet").startswith("Restored "),
        masodperc=3,
    ), "a visszaállítás nem fejeződött be időben"
    assert vezerlo.waitForBackgroundWorkers(5.0)

    for nev, adat in kepek.items():
        visszaallitott = tmp_path / "visszaallitott" / "utazas" / nev
        assert visszaallitott.read_bytes() == adat
    assert "2" in host.property("uzenet")
    view.hide()


def _manifeszt(tmp_path: Path, szoveg: str) -> Path:
    ut = tmp_path / "iso-files.txt"
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text(szoveg, encoding="utf-8")
    return ut
