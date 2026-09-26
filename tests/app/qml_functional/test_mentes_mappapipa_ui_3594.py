"""#3594 — a mentés 2. lépése a kiadás-panelen, VALÓDI kattintással.

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
bepipálva: amíg nincs pipa, a „Lemezre írás" nem nyomható.

Az átnézés (#3643) után a lista HÁTTÉRSZÁLON készül: amíg számol, a panel
az eredeti `il_BurnPanel::calculating` feliratát mutatja („Calculating…" /
„Számítás…", `biztonsagi-mentes.md` 15.7), és egy kiválasztás-váltás
EGYETLEN lekérdezést indít.

#3504: a felület a `BackupHost` + `PublishPanel` mentés-üzemmódja — a
korábbi, külön ablakban futó `BackupDialog` helyett. A `BackupHost` már
nem `Window`, ezért a valódi kattintáshoz `QQuickView`-ba ágyazva fut
(`support.backup_host_harness`).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
import threading

from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, Qt, Slot
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, wait_for_signal

_QML = Path(picasapy.app.__file__).parent / "qml"
_PANEL = (_QML / "PicasaPy" / "PublishPanel.qml").read_text(encoding="utf-8")


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


def _vard_a_mappakat(ablak, qt_app) -> None:
    """Megvárja, amíg a háttérben számolt mappa-lista megérkezik."""
    assert varj_feltetelre(
        qt_app, lambda: ablak.property("mappakToltodnek") is False
    ), "a mappa-lista nem érkezett meg"
    qt_app.processEvents()


def _epits(qt_app, tmp_path, monkeypatch, *, osztaly=None, nyaralas=2):
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    for mappa in ("nyaralas", "szulinap"):
        (gyoker / mappa).mkdir(parents=True)
    if nyaralas == 2:
        make_jpeg(gyoker / "nyaralas" / "a.jpg")
        make_jpeg(gyoker / "nyaralas" / "b.jpg")
    else:
        for i in range(nyaralas):
            make_jpeg(gyoker / "nyaralas" / f"k{i:02d}.jpg")
    make_jpeg(gyoker / "szulinap" / "c.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    vezerlo = (osztaly or BackupController)(db, (str(gyoker),))
    cel = tmp_path / "cel"
    vezerlo.ujKeszlet("Külső", str(cel), "minden", "lemez")
    view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
    QMetaObject.invokeMethod(ablak, "nyisd")
    ablak.setProperty("kivalasztott", 0)
    _vard_a_mappakat(ablak, qt_app)
    return view, ablak, vezerlo, cel


@pytest.fixture
def gazda(qt_app, tmp_path, monkeypatch):
    view, ablak, vezerlo, cel = _epits(qt_app, tmp_path, monkeypatch)
    yield view, ablak, vezerlo, cel
    view.hide()


def _pipak(ablak) -> list[QQuickItem]:
    return _latszo_elemek(ablak, "publishBackupFolderCheck")


def _gordits_latvanyba(ablak, index: int, qt_app) -> None:
    """A `backuprect2` MÉRT doboza (324×166) csak pár sort mutat egyszerre
    — a valódi kattintáshoz a sort a `ListView`-nek kell látványba
    görgetnie, ahogy egy felhasználó is görgetne (`ListView.Contain`)."""
    lista = _elem(ablak, "publishBackupFolderList")
    QMetaObject.invokeMethod(
        lista, "positionViewAtIndex", Q_ARG(int, index), Q_ARG(int, 4)
    )
    qt_app.processEvents()


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
        assert szoveg in _PANEL, szoveg


class TestAMappaLista:
    def test_a_mentetlen_mappak_latszanak_pipa_nelkul(self, gazda, qt_app):
        _, ablak, _, _ = gazda
        pipak = _pipak(ablak)
        assert len(pipak) == 2
        assert [p.property("text") for p in pipak] == ["nyaralas", "szulinap"]
        assert all(p.property("checked") is False for p in pipak)
        assert _elem(ablak, "publishBackupGo").property("enabled") is False

    def test_az_osszes_kijelolese_es_torlese(self, gazda, qt_app):
        view, ablak, _, _ = gazda
        _kattints(view, _elem(ablak, "publishBackupSelectAll"), qt_app)
        assert all(p.property("checked") is True for p in _pipak(ablak))
        assert _elem(ablak, "publishBackupGo").property("enabled") is True

        _kattints(view, _elem(ablak, "publishBackupSelectNone"), qt_app)
        assert all(p.property("checked") is False for p in _pipak(ablak))
        assert _elem(ablak, "publishBackupGo").property("enabled") is False


class TestAFutas:
    def test_csak_a_pipalt_mappa_megy_es_utana_eltunik(
        self, gazda, qt_app
    ):
        view, ablak, vezerlo, cel = gazda
        _gordits_latvanyba(ablak, 1, qt_app)
        _kattints(view, _pipak(ablak)[1], qt_app)   # szulinap
        assert _pipak(ablak)[1].property("checked") is True

        wait_for_signal(
            vezerlo.futasKesz,
            lambda: _kattints(view, _elem(ablak, "publishBackupGo"), qt_app),
            description="a pipált mappa mentése",
        )
        qt_app.processEvents()

        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["c.jpg"]
        # a már elmentett mappa nem látszik többé — a lista a háttérből jön
        assert varj_feltetelre(
            qt_app, lambda: len(_pipak(ablak)) == 1)
        _vard_a_mappakat(ablak, qt_app)
        assert [p.property("text") for p in _pipak(ablak)] == ["nyaralas"]


class TestHatterbenSzamol:
    """[MAGAS] a lista háttérszálon készül, közben a mért felirat látszik."""

    def test_szamitas_kozben_a_calculating_felirat_latszik(
        self, gazda, qt_app, monkeypatch
    ):
        import picasapy.app.backup_controller as modul

        _, ablak, vezerlo, _ = gazda
        engedd = threading.Event()
        eredeti = modul.tervezd_meg

        def _lassu(*args, **kwargs):
            engedd.wait(5.0)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "tervezd_meg", _lassu)
        try:
            QMetaObject.invokeMethod(ablak, "frissitsdAMappakat")
            qt_app.processEvents()
            felirat = _elem(ablak, "publishBackupFolderLoading")
            assert felirat.isVisible()
            assert felirat.property("text") == "Calculating…"
            assert ablak.property("mappakToltodnek") is True
        finally:
            engedd.set()
        _vard_a_mappakat(ablak, qt_app)
        assert not _elem(ablak, "publishBackupFolderLoading").isVisible()
        assert [p.property("text") for p in _pipak(ablak)] == [
            "nyaralas", "szulinap"]

    def test_a_kivalasztas_valtasa_egyetlen_lekerdezest_indit(
        self, qt_app, tmp_path, monkeypatch
    ):
        """[KÖZEPES] a törlés átállítja a kiválasztást — az
        `onKivalasztottChanged` már kér, a `frissitsd` ne kérjen még egyszer."""
        from picasapy.app.backup_controller import BackupController

        class _Szamlalo(BackupController):
            lekeresek = 0

            @Slot(int, result=int)
            def mentetlenMappakLekerese(self, keszlet_id):  # noqa: N802
                type(self).lekeresek += 1
                return super().mentetlenMappakLekerese(keszlet_id)

        view, ablak, vezerlo, cel = _epits(
            qt_app, tmp_path, monkeypatch, osztaly=_Szamlalo)
        try:
            vezerlo.ujKeszlet("Másik", str(tmp_path / "cel2"), "minden")
            ablak.setProperty("kivalasztott", 1)
            _vard_a_mappakat(ablak, qt_app)
            masodik = vezerlo.keszletek()[1]["id"]

            _Szamlalo.lekeresek = 0
            # a törlés után a kiválasztás 1 → 0 lesz
            vezerlo.torisdAKeszletet(masodik)
            qt_app.processEvents()
            _vard_a_mappakat(ablak, qt_app)
            assert ablak.property("kivalasztott") == 0
            assert _Szamlalo.lekeresek == 1
        finally:
            view.hide()


class TestAFajlnevek:
    """[KÖZEPES] sok fájlnál csak az első néhány név megy át, a darabszám
    látszik, és a folytatást „…" jelzi."""

    def test_sok_fajlnal_a_sor_a_darabot_es_a_folytatast_mutatja(
        self, qt_app, tmp_path, monkeypatch
    ):
        view, ablak, vezerlo, cel = _epits(
            qt_app, tmp_path, monkeypatch, nyaralas=25)
        try:
            sorok = _latszo_elemek(ablak, "publishBackupFolderFiles")
            szoveg = sorok[0].property("text")
            assert szoveg.startswith("(25)  k00.jpg, ")
            assert "k19.jpg" in szoveg
            assert "k20.jpg" not in szoveg
            assert szoveg.endswith(", …")
            # a kevés fájlos mappa sorában nincs folytatásjel
            assert sorok[1].property("text") == "(1)  c.jpg"
        finally:
            view.hide()


class TestAMagyarFelirat:
    @pytest.mark.parametrize("forras, magyar", [
        ("Choose folders & albums to back up",
         "Mappák és albumok kijelölése biztonsági másolat készítéséhez"),
        ("Picasa is now showing the files you have not previously backed up.",
         "A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban "
         "nem készült biztonsági másolat."),
        ("Select All", "Az összes kijelölése"),
        ("Select None", "Az összes kijelölés megszüntetése"),
        # `il_BurnPanel::calculating` (`biztonsagi-mentes.md` 15.7)
        ("Calculating…", "Számítás…"),
    ])
    def test_a_hivatalos_magyar_a_qm_bol_jon(self, qt_app, forras, magyar):
        from PySide6.QtCore import QTranslator

        fordito = QTranslator()
        assert fordito.load("picasapy_hu", str(_QML.parent / "i18n"))
        assert fordito.translate("PublishPanel", forras) == magyar
