"""#3681 — a mentés-szűrő a VALÓDI `Main.qml`-ben, valódi kattintással.

A `test_mentes_konyvtar_szuro_3681.py` az önálló `FolderPane`/
`FolderHierarchyView` komponenst méri; ez a fájl a teljes alkalmazást: a
`Main.qml` köti a hasábot a mentés-panelhez (`mentesSzuroAktiv`), és a
lelet-osztályok éppen ebből a bekötésből jöttek (az átnézés #3745):

* fanézetben a BECSUKOTT ágban lévő mentetlen mappa nem látszott, mert a
  szűrő a vezérlő kilapított — csak a nyitott ágakat tartalmazó — soraiból
  válogatott;
* szűrő módban a görgő és a fel/le nyíl a kiszűrt mappákat is megnyitotta;
* a mappánkénti „(darab) fájlnevek” sor, a „Számítás…” és az üres készlet
  szövege a megszűnt sávval együtt eltűnt;
* a pipák a panel bezárása után is megmaradtak.

A próbakönyvtár BEÁGYAZOTT mappát is tartalmaz (`2024/nyaralas`), és a
fanézet `expandAll()` NÉLKÜL fut: a `2024` ág a megnyitáskor csukva van.
"""

from __future__ import annotations

import threading

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, wait_for_signal
from tests.app.qml_functional.conftest import _build_qml_app

_MAPPAK = {
    "2024/nyaralas": ("a.jpg", "b.jpg"),
    "2024/szulinap": ("c.jpg",),
    "elmentett": ("d.jpg",),
    "masik": ("e.jpg",),
}


def _keszit(lib) -> None:
    for mappa, fajlok in _MAPPAK.items():
        (lib / mappa).mkdir(parents=True, exist_ok=True)
        for fajl in fajlok:
            make_jpeg(lib / mappa / fajl, size=(64, 48))


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _tenyleg_latszik(elem: QQuickItem) -> bool:
    if elem.width() <= 0 or elem.height() <= 0:
        return False
    os_ = elem
    while os_ is not None:
        if not os_.isVisible():
            return False
        os_ = os_.parentItem()
    return True


def _latszo(window, nev: str, *, elotag: bool = False) -> list[QQuickItem]:
    talalat = [
        e for e in _walk(window.contentItem())
        if (e.objectName().startswith(nev) if elotag else e.objectName() == nev)
        and _tenyleg_latszik(e)
    ]
    return sorted(talalat, key=lambda e: e.mapToScene(QPointF(0, 0)).y())


def _elem(window, nev: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _panel(window, nev: str) -> QQuickItem:
    """A MENTÉS-panel eleme — az Ajándék-CD gazdája ugyanezt a
    `PublishPanel`-t hordozza, azonos objectName-ekkel."""
    host = window.findChild(QObject, "backupHost")
    elem = host.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található a mentés-panelen"
    return elem


def _kattints(window, elem, qt_app) -> None:
    qt_app.processEvents()
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _vard_a_mappakat(host, qt_app) -> None:
    assert varj_feltetelre(
        qt_app, lambda: host.property("mappakToltodnek") is False
    ), "a mentetlen mappák listája nem érkezett meg"
    qt_app.processEvents()


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else list(ertek)


@pytest.fixture
def app(qt_app, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController
    from picasapy.app.worker_thread import wait_for_all_background_workers

    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_keszit)
    window, controller, engine = next(gen)
    try:
        window.resize(1280, 900)
        lib = tmp_path / "kepek"
        vezerlo = BackupController(tmp_path / "index.db", (str(lib),))
        engine.rootContext().setContextProperty("backupController", vezerlo)
        qt_app.processEvents()
        cel = tmp_path / "cel"
        vezerlo.ujKeszlet("Saját mentés", str(cel), "minden", "lemez")
        keszlet = vezerlo.keszletek()[0]["id"]
        vezerlo.futtasdMost(keszlet, [str(lib / "elmentett")])
        assert wait_for_all_background_workers(30.0)
        qt_app.processEvents()
        yield window, controller, engine, vezerlo, lib, cel
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def _nyisd_a_mentest(window, qt_app, *, keszlet: int = 0):
    """A VALÓDI menütétel (`Eszközök ▸ Képek biztonsági mentése…`), majd a
    készlet kiválasztása."""
    QMetaObject.invokeMethod(
        _elem(window, "menuToolsBackup"), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()
    host = window.findChild(QObject, "backupHost")
    assert host.property("nyitva") is True
    host.setProperty("kivalasztott", keszlet)
    if keszlet >= 0:
        _vard_a_mappakat(host, qt_app)
    return host


def _fanezet(engine, qt_app, be: bool) -> None:
    fa = engine.rootContext().contextProperty("folderHierarchyController")
    fa.setTreeView(be)
    qt_app.processEvents()


def _levelut(ut) -> str:
    """Az INDEXELT mappa sorának útja a fában: a `build_hierarchy` a valódi
    mappa útját betűre pontosan megtartja (`str(Path)`, Windowson `C:\\…`).
    """
    return str(ut)


def _koztes_ut(ut) -> str:
    """A fa által KÖZBEÜLTETETT szint útja (nincs az indexben): perjeles."""
    return ut.as_posix()


def _fa_utak(window) -> list[str]:
    elotag = "hierRow:"
    return [
        e.objectName()[len(elotag):]
        for e in _latszo(window, elotag, elotag=True)
    ]


class TestAFaBecsukottAggal:
    """[MAGAS] a becsukott ágban lévő mentetlen mappa is látszik."""

    def test_a_beagyazott_mentetlen_mappa_latszik_expandall_nelkul(
        self, app, qt_app
    ):
        window, _controller, engine, _v, lib, _cel = app
        _fanezet(engine, qt_app, True)
        fa = engine.rootContext().contextProperty("folderHierarchyController")
        kinyitott_elotte = [
            sor["path"] for sor in fa.rows if sor["expanded"]
        ]
        assert _koztes_ut(lib / "2024") not in kinyitott_elotte, (
            "a próba feltétele: a 2024 ág a megnyitáskor csukva van"
        )

        _nyisd_a_mentest(window, qt_app)

        utak = _fa_utak(window)
        for mappa in ("2024/nyaralas", "2024/szulinap", "masik"):
            assert _levelut(lib / mappa) in utak, (mappa, utak)
        assert _levelut(lib / "elmentett") not in utak, utak
        # az ős megmarad, hogy a fa olvasható legyen — pipa NÉLKÜL
        assert _koztes_ut(lib / "2024") in utak, utak
        assert _latszo(window, "hierMentesCheck:" + _koztes_ut(lib / "2024")) == []
        assert len(_latszo(
            window, "hierMentesCheck:" + _levelut(lib / "2024" / "nyaralas"))) == 1

    def test_a_beagyazott_sor_kattintasra_pipalodik(self, app, qt_app):
        window, controller, engine, _v, lib, _cel = app
        _fanezet(engine, qt_app, True)
        host = _nyisd_a_mentest(window, qt_app)
        nyaralas = _levelut(lib / "2024" / "nyaralas")
        elotte = controller.property("currentFolder")

        _kattints(window, _latszo(window, "hierRowMouse:" + nyaralas)[0], qt_app)

        assert _lista(host.property("pipaltMappak")) == [nyaralas]
        pipa = _latszo(window, "hierMentesCheck:" + nyaralas)[0]
        assert pipa.property("checked") is True
        assert controller.property("currentFolder") == elotte, (
            "szűrő módban a kattintás pipál, nem nyit meg mappát"
        )

    def test_a_fasoron_a_darab_es_a_fajlnevek(self, app, qt_app):
        window, _c, engine, _v, lib, _cel = app
        _fanezet(engine, qt_app, True)
        _nyisd_a_mentest(window, qt_app)
        ut = _levelut(lib / "2024" / "nyaralas")
        darab = _latszo(window, "hierCount:" + ut)
        assert [d.property("text") for d in darab] == ["(2)"]
        # a fájlnevek csak akkor látszanak, ha elférnek (a mély próba-
        # útvonal behúzása mellett itt nem) — a szöveg akkor is a sor része
        fajlok = [
            e for e in _walk(window.contentItem())
            if e.objectName() == "hierMentesFiles:" + ut
        ]
        assert [f.property("text") for f in fajlok] == ["a.jpg, b.jpg"]

    def test_bezaras_utan_a_teljes_fa_visszajon(self, app, qt_app):
        window, _c, engine, _v, lib, _cel = app
        _fanezet(engine, qt_app, True)
        _nyisd_a_mentest(window, qt_app)
        fa = engine.rootContext().contextProperty("folderHierarchyController")
        _kattints(window, _panel(window, "publishBackupCancel"), qt_app)

        # a vezérlő nyitott/csukott állapota szerinti TELJES fa tér vissza —
        # a szűrő nem nyitott ki semmit tartósan
        assert _fa_utak(window) == [sor["path"] for sor in fa.rows]
        assert _levelut(lib / "2024" / "nyaralas") not in _fa_utak(window)
        assert _latszo(window, "hierMentesCheck:", elotag=True) == []


class TestALeptetesSzuroModban:
    """[MAGAS] szűrő módban a görgő és a nyíl NEM nyit meg kiszűrt mappát."""

    def _lapos_cimke(self, window):
        cimkek = _latszo(window, "folderRowLabel")
        assert cimkek, "nincs látszó mappasor"
        return cimkek[0]

    def test_a_gorgo_nem_leptet(self, app, qt_app):
        window, controller, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        elotte = controller.property("currentFolder")
        cimke = self._lapos_cimke(window)
        pont = cimke.mapToScene(cimke.boundingRect().center())
        for _ in range(3):
            esemeny = QWheelEvent(
                pont, window.mapToGlobal(pont), QPoint(0, 0), QPoint(0, -120),
                Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                Qt.ScrollPhase.NoScrollPhase, False,
            )
            qt_app.sendEvent(window, esemeny)
            qt_app.processEvents()
        assert controller.property("currentFolder") == elotte

    def test_a_nyil_nem_leptet(self, app, qt_app):
        window, controller, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        elotte = controller.property("currentFolder")
        _elem(window, "folderListView").forceActiveFocus()
        for billentyu in (Qt.Key.Key_Down, Qt.Key.Key_Down, Qt.Key.Key_Up):
            QTest.keyClick(window, billentyu)
            qt_app.processEvents()
        assert controller.property("currentFolder") == elotte

    def test_bezaras_utan_a_gorgo_ujra_leptet(self, app, qt_app):
        """A foga: a tiltás CSAK a szűrő módra szól."""
        window, controller, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        _kattints(window, _panel(window, "publishBackupCancel"), qt_app)
        elotte = controller.property("currentFolder")
        cimke = self._lapos_cimke(window)
        pont = cimke.mapToScene(cimke.boundingRect().center())
        esemeny = QWheelEvent(
            pont, window.mapToGlobal(pont), QPoint(0, 0), QPoint(0, -120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase, False,
        )
        qt_app.sendEvent(window, esemeny)
        qt_app.processEvents()
        assert controller.property("currentFolder") != elotte


class TestATajekoztatas:
    """[MAGAS] a bal hasáb nem üres szó nélkül."""

    def test_a_lapos_soron_a_darab_es_a_fajlnevek(self, app, qt_app):
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        cimkek = {
            c.property("text") for c in _latszo(window, "folderRowLabel")
        }
        assert cimkek == {"nyaralas (2)", "szulinap (1)", "masik (1)"}
        sorok = {
            s.property("text") for s in _latszo(window, "folderRowMentesFiles")
        }
        assert sorok == {"a.jpg, b.jpg", "c.jpg", "e.jpg"}

    def test_szamolas_alatt_a_szamitas_felirat(self, app, qt_app, monkeypatch):
        import picasapy.app.backup_controller as modul

        window, _c, _e, _v, _lib, _cel = app
        host = _nyisd_a_mentest(window, qt_app)
        engedd = threading.Event()
        eredeti = modul.tervezd_meg

        def _lassu(*args, **kwargs):
            engedd.wait(5.0)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "tervezd_meg", _lassu)
        try:
            QMetaObject.invokeMethod(host, "frissitsdAMappakat")
            qt_app.processEvents()
            felirat = _latszo(window, "folderPaneMentesAllapot")
            assert [f.property("text") for f in felirat] == ["Calculating…"]
        finally:
            engedd.set()
        _vard_a_mappakat(host, qt_app)
        assert _latszo(window, "folderPaneMentesAllapot") == []

    def test_ures_keszletnel_a_hivatalos_szoveg(self, app, qt_app):
        window, _c, _e, vezerlo, lib, _cel = app
        keszlet = vezerlo.keszletek()[0]["id"]
        vezerlo.futtasdMost(keszlet)
        from picasapy.app.worker_thread import wait_for_all_background_workers

        assert wait_for_all_background_workers(30.0)
        _nyisd_a_mentest(window, qt_app)
        felirat = _latszo(window, "folderPaneMentesAllapot")
        # `thumbui/lightbox_bgtext` Text2 — az eredeti mentés-ág szövege
        assert [f.property("text") for f in felirat] == [
            "All Files are backed up in this set"]
        assert _latszo(window, "folderRowMentesCheck") == []

    def test_keszlet_nelkul_utmutatas(self, app, qt_app):
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app, keszlet=-1)
        felirat = _latszo(window, "folderPaneMentesAllapot")
        assert [f.property("text") for f in felirat] == [
            "Create a Set or use an existing one"]


class TestAGombokEsAFutas:
    """[KÖZEPES] a törölt tesztek lényege az új felületen."""

    def test_az_osszes_kijelolese_es_megszuntetese(self, app, qt_app):
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        pipak = lambda: _latszo(window, "folderRowMentesCheck")  # noqa: E731
        go = _panel(window, "publishBackupGo")
        assert len(pipak()) == 3
        assert all(p.property("checked") is False for p in pipak())
        assert go.property("enabled") is False

        _kattints(window, _panel(window, "publishBackupSelectAll"), qt_app)
        assert all(p.property("checked") is True for p in pipak())
        assert go.property("enabled") is True

        _kattints(window, _panel(window, "publishBackupSelectNone"), qt_app)
        assert all(p.property("checked") is False for p in pipak())
        assert go.property("enabled") is False

    def test_pipa_mentes_es_a_mappa_eltunik(self, app, qt_app):
        window, _c, _e, vezerlo, lib, cel = app
        host = _nyisd_a_mentest(window, qt_app)
        masik = [
            c for c in _latszo(window, "folderRowLabel")
            if c.property("text").startswith("masik")
        ]
        _kattints(window, masik[0], qt_app)
        assert _lista(host.property("pipaltMappak")) == [str(lib / "masik")]

        wait_for_signal(
            vezerlo.futasKesz,
            lambda: _kattints(window, _panel(window, "publishBackupGo"), qt_app),
            description="a pipált mappa mentése",
        )
        qt_app.processEvents()
        assert sorted(p.name for p in cel.rglob("*.jpg")) == ["d.jpg", "e.jpg"]
        assert varj_feltetelre(
            qt_app,
            lambda: len(_latszo(window, "folderRowMentesCheck")) == 2,
        ), "a mentett mappa nem tűnt el a listából"
        _vard_a_mappakat(host, qt_app)
        nevek = sorted(
            c.property("text") for c in _latszo(window, "folderRowLabel"))
        assert nevek == ["nyaralas (2)", "szulinap (1)"]


class TestABezaras:
    def test_bezaraskor_a_pipak_torlodnek(self, app, qt_app):
        """[KÖZEPES] újranyitáskor ne maradjon ott a régi kijelölés."""
        window, _c, _e, _v, _lib, _cel = app
        host = _nyisd_a_mentest(window, qt_app)
        _kattints(window, _panel(window, "publishBackupSelectAll"), qt_app)
        assert len(_lista(host.property("pipaltMappak"))) == 3

        _kattints(window, _panel(window, "publishBackupCancel"), qt_app)
        assert _lista(host.property("pipaltMappak")) == []

        _nyisd_a_mentest(window, qt_app)
        assert all(
            p.property("checked") is False
            for p in _latszo(window, "folderRowMentesCheck"))

    def test_a_szuro_a_panel_lathatosagat_koveti(self, app, qt_app):
        """[ALACSONY] nézegető közben a panel nem látszik — a hasáb szűrője
        sem él; visszatérve újra szűr."""
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        pane = _elem(window, "folderPane")
        assert pane.property("mentesSzuroAktiv") is True

        window.setProperty("viewerOpen", True)
        qt_app.processEvents()
        assert pane.property("mentesSzuroAktiv") is False

        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert pane.property("mentesSzuroAktiv") is True
