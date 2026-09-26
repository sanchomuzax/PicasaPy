"""#3594 — a mentés 2. lépése a párbeszédben, VALÓDI kattintással.

Az eredeti mentés-üzemmód 2. lépése (`backuprect2`, `biztonsagi-mentes.md`
10.3):

```
Mappák és albumok kijelölése biztonsági másolat készítéséhez
A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban nem
készült biztonsági másolat.
Jelölje ki azokat a mappákat, … vagy »Az összes kijelölése« …
[✓] nyaralas   a.jpg, b.jpg
[ ] szulinap   c.jpg
[Az összes kijelölése] [Az összes kijelölés megszüntetése]
```

A mért szöveg („Jelölje ki…") szerint a mappák ALAPBÓL nincsenek
bepipálva: amíg nincs pipa, a „Back Up" nem nyomható.
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
_PARBESZED = (_QML / "PicasaPy" / "BackupDialog.qml").read_text(
    encoding="utf-8")


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _latszo_elemek(gyoker: QQuickItem, nev: str) -> list[QQuickItem]:
    """A vizuális fa LÁTHATÓ `nev` nevű elemei, a képernyő-sorrendben.

    A lista delegáltjai a `contentItem` vizuális gyerekei — ezért a
    `childItems` fán megyünk, nem a QObject-fán."""
    talalat: list[QQuickItem] = []
    verem = [gyoker]
    while verem:
        elem = verem.pop()
        if elem.objectName() == nev and elem.isVisible():
            talalat.append(elem)
        verem.extend(elem.childItems())
    return sorted(talalat, key=lambda e: e.mapToScene(e.position()).y())


def _kattints(ablak, elem, qt_app):
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
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    for mappa in ("nyaralas", "szulinap"):
        (gyoker / mappa).mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "a.jpg")
    make_jpeg(gyoker / "nyaralas" / "b.jpg")
    make_jpeg(gyoker / "szulinap" / "c.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    vezerlo = BackupController(db, (str(gyoker),))
    cel = tmp_path / "cel"
    vezerlo.ujKeszlet("Külső", str(cel), "minden", "lemez")
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    motor.rootContext().setContextProperty("backupController", vezerlo)
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QML / "PicasaPy" / "BackupDialog.qml"))
    )
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    QMetaObject.invokeMethod(ablak, "open")
    ablak.setProperty("kivalasztott", 0)
    qt_app.processEvents()
    yield ablak, vezerlo, cel
    ablak.setProperty("visible", False)
    ablak.deleteLater()


def _pipak(ablak) -> list[QQuickItem]:
    return _latszo_elemek(ablak.contentItem(), "backupFolderCheck")


class TestAMertSzovegek:
    @pytest.mark.parametrize("szoveg", [
        "Choose folders & albums to back up",
        "Picasa is now showing the files you have not previously backed up.",
        "Check the folders you want to back up, or choose 'Select All' to "
        "choose everything.",
        "Select All",
        "Select None",
    ])
    def test_a_mert_felirat_ott_van(self, szoveg):
        assert szoveg in _PARBESZED, szoveg


class TestAMappaLista:
    def test_a_mentetlen_mappak_latszanak_pipa_nelkul(self, parbeszed, qt_app):
        ablak, _, _ = parbeszed
        pipak = _pipak(ablak)
        assert len(pipak) == 2
        assert [p.property("text") for p in pipak] == ["nyaralas", "szulinap"]
        assert all(p.property("checked") is False for p in pipak)
        assert _elem(ablak, "backupRun").property("enabled") is False

    def test_az_osszes_kijelolese_es_torlese(self, parbeszed, qt_app):
        ablak, _, _ = parbeszed
        _kattints(ablak, _elem(ablak, "backupSelectAll"), qt_app)
        assert all(p.property("checked") is True for p in _pipak(ablak))
        assert _elem(ablak, "backupRun").property("enabled") is True

        _kattints(ablak, _elem(ablak, "backupSelectNone"), qt_app)
        assert all(p.property("checked") is False for p in _pipak(ablak))
        assert _elem(ablak, "backupRun").property("enabled") is False


class TestAFutas:
    def test_csak_a_pipalt_mappa_megy_es_utana_eltunik(
        self, parbeszed, qt_app
    ):
        ablak, vezerlo, cel = parbeszed
        _kattints(ablak, _pipak(ablak)[1], qt_app)   # szulinap
        assert _pipak(ablak)[1].property("checked") is True

        wait_for_signal(
            vezerlo.futasKesz,
            lambda: _kattints(ablak, _elem(ablak, "backupRun"), qt_app),
            description="a pipált mappa mentése",
        )
        qt_app.processEvents()

        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["c.jpg"]
        # a már elmentett mappa nem látszik többé
        assert [p.property("text") for p in _pipak(ablak)] == ["nyaralas"]


class TestAMagyarFelirat:
    @pytest.mark.parametrize("forras, magyar", [
        ("Choose folders & albums to back up",
         "Mappák és albumok kijelölése biztonsági másolat készítéséhez"),
        ("Picasa is now showing the files you have not previously backed up.",
         "A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban "
         "nem készült biztonsági másolat."),
        ("Select All", "Az összes kijelölése"),
        ("Select None", "Az összes kijelölés megszüntetése"),
    ])
    def test_a_hivatalos_magyar_a_qm_bol_jon(self, qt_app, forras, magyar):
        from PySide6.QtCore import QTranslator

        fordito = QTranslator()
        assert fordito.load("picasapy_hu", str(_QML.parent / "i18n"))
        assert fordito.translate("BackupDialog", forras) == magyar
