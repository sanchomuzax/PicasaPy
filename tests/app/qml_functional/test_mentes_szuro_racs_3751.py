"""#3751 — mentés-üzemmódban a JOBB oldali képrács (`LightboxFeed`) is a
MÉG EL NEM MENTETT mappák képeire szűkül, ugyanazzal a szerződéssel, mint a
bal hasáb (#3681, ld. `test_mentes_szuro_main_3681.py`).

A #3745 átnézése a referencia-képpel (`Colab EN 24 - Confirm (Back Up
Pictures).png`) mérte: az eredetiben a JOBB oldali rács is szűrve van —
nálunk a #3681 csak a bal hasábot szűrte, a rács változatlan maradt (a már
elmentett mappák képei is látszottak). Ez a fájl a rács oldalát méri:

* mentés-üzemmódban csak azok a mappa-csoportok látszanak a rácson, amiket
  a `BackupController` még nem mentett el a kiválasztott készletbe;
* a szűrés MAPPA-granularitású, ugyanaz a lista (`mentetlenek`), amit a
  bal hasáb is kap — nem vág bele egy-egy mappa fényképei közé;
* a rács normál (mentés-üzemmódon kívüli) használata — kijelölés valódi
  kattintással — változatlan;
* kilépéskor (Mégse) a teljes rács visszajön;
* ha a kiválasztott készlet mindent tartalmaz, a rács közepén a hivatalos
  szöveg áll, ugyanaz, amit a bal hasáb `mentesAllapotSzoveg`-je használ
  (`thumbui/lightbox_bgtext` Text2); számítás közben egyik szöveg sem
  hazudik.
"""

from __future__ import annotations

import threading

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app

_MAPPAK = {
    "elmentett": ("d.jpg", "e.jpg"),
    "friss": ("a.jpg", "b.jpg"),
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


def _latszo(window, nev: str) -> list[QQuickItem]:
    talalat = [
        e for e in _walk(window.contentItem())
        if e.objectName() == nev and _tenyleg_latszik(e)
    ]
    return sorted(talalat, key=lambda e: e.mapToScene(QPointF(0, 0)).y())


def _elem(window, nev: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _panel(window, nev: str) -> QQuickItem:
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


def _cimkek(window) -> set[str]:
    return {e.property("text") for e in _latszo(window, "folderTitleText")}


class TestARacsSzuroModban:
    """[MAGAS] a jobb oldali rács a mentetlen mappákra szűkül."""

    def test_mentes_elott_mindket_mappa_latszik(self, app, qt_app):
        window, _c, _e, _v, _lib, _cel = app
        assert _cimkek(window) == {"elmentett", "friss"}

    def test_mentes_kozben_csak_a_mentetlen_mappa_latszik(self, app, qt_app):
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        grid = _elem(window, "photoGrid")
        assert grid.property("count") == 1
        assert _cimkek(window) == {"friss"}

    def test_a_mentetlen_mappa_minden_kepe_latszik(self, app, qt_app):
        """A szűrés MAPPA-granularitású — a `friss` mindkét képe megvan."""
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        assert len(_latszo(window, "thumbMouseArea")) == 2

    def test_kattintassal_kijelolheto_a_latszo_kep(self, app, qt_app):
        """[MAGAS] a rács normál használata (kijelölés) szűrő módban is él —
        valódi kattintással, nem a kezelő közvetlen hívásával."""
        window, controller, _e, _v, lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        friss_csoport = next(
            c for c in controller.feedGroups if c["path"] == str(lib / "friss")
        )
        elsonek_latszo = _latszo(window, "thumbMouseArea")[0]

        _kattints(window, elsonek_latszo, qt_app)

        indexek = window.property("selectedIndexes")
        if hasattr(indexek, "toVariant"):
            indexek = indexek.toVariant()
        assert list(indexek) == [friss_csoport["start"]], (
            "a kattintás nem a látszó (mentetlen) mappa fényképét jelölte ki"
        )

    def test_bezaras_utan_mindket_mappa_visszajon(self, app, qt_app):
        """[MAGAS] kilépéskor a rács szűrője visszaáll — az eredetiben
        mentés-üzemmódon KÍVÜL a rács változatlan."""
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        _kattints(window, _panel(window, "publishBackupCancel"), qt_app)

        grid = _elem(window, "photoGrid")
        assert grid.property("count") == 2
        assert _cimkek(window) == {"elmentett", "friss"}


class TestATajekoztatasARacson:
    """[MAGAS] a rács se maradjon szó nélkül üresen."""

    def test_ures_keszletnel_a_hivatalos_szoveg(self, app, qt_app):
        window, _c, _e, vezerlo, lib, _cel = app
        keszlet = vezerlo.keszletek()[0]["id"]
        # a `friss` mappát is elmentjük — a készlet mostantól MINDENT tartalmaz
        vezerlo.futtasdMost(keszlet, [str(lib / "friss")])
        from picasapy.app.worker_thread import wait_for_all_background_workers

        assert wait_for_all_background_workers(30.0)
        qt_app.processEvents()

        _nyisd_a_mentest(window, qt_app)

        grid = _elem(window, "photoGrid")
        assert grid.property("count") == 0
        szoveg = _elem(window, "gridEmptyText")
        assert szoveg.property("visible") is True
        # `thumbui/lightbox_bgtext` Text2 — az eredeti mentés-ág szövege,
        # ugyanaz, amit a bal hasáb `mentesAllapotSzoveg`-je is használ
        assert szoveg.property("text") == "All Files are backed up in this set"

    def test_szamolas_alatt_a_rács_nem_hazudik(self, app, qt_app, monkeypatch):
        """Számítás közben a `mentetlenek` átmenetileg üres — a rács
        NEM állíthatja emiatt, hogy „minden el van mentve" (#1798 osztálya:
        hazudó állapot)."""
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
            szoveg = _elem(window, "gridEmptyText")
            assert szoveg.property("visible") is False
        finally:
            engedd.set()
        _vard_a_mappakat(host, qt_app)
