"""#3751 — mentés-üzemmódban a JOBB oldali képrács (`LightboxFeed`) is csak
a MÉG EL NEM MENTETT FÁJLOKAT mutatja, a bal hasáb (#3681, ld.
`test_mentes_szuro_main_3681.py`) mappalistájával összhangban.

A #3745 átnézése a referencia-képpel (`Colab EN 24 - Confirm (Back Up
Pictures).png`) mérte: az eredetiben a JOBB oldali rács is szűrve van. A
`backuptext2` fájlra szól („azokat a fájlokat jeleníti meg, amelyekről
korábban nem készült biztonsági másolat"), ezért:

* egy részben elmentett mappából csak a még el nem mentett képek látszanak —
  ugyanazok, amiket a bal hasáb a mappa sorának végén felsorol;
* a rács normál használata (kijelölés valódi kattintással, Ctrl+A) a szűrt
  listán dolgozik;
* kilépéskor (Mégse) a teljes rács visszajön, a mentés előtti görgetési
  helyzetben;
* ha a kiválasztott készlet mindent tartalmaz, a rács közepén a hivatalos
  szöveg áll (`thumbui/lightbox_bgtext` Text2); számítás közben és
  kiválasztott készlet nélkül ez a mondat nem jelenik meg.
"""
from __future__ import annotations

import shutil
import threading

import pytest
from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app

_MAPPAK = {
    # sok kép, hogy a rács görgethető legyen (a görgetési helyzet próbája)
    "elmentett": tuple(f"k{i:02d}.jpg" for i in range(48)),
    "friss": ("a.jpg", "b.jpg"),
    # részben elmentett: a `h.jpg` a mentés után került a mappába
    "vegyes": ("f.jpg", "g.jpg", "h.jpg"),
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
    return sorted(
        talalat,
        key=lambda e: (e.mapToScene(QPointF(0, 0)).y(),
                       e.mapToScene(QPointF(0, 0)).x()),
    )


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
        felre = tmp_path / "felre"
        felre.mkdir()
        shutil.move(str(lib / "vegyes" / "h.jpg"), str(felre / "h.jpg"))
        vezerlo.futtasdMost(
            keszlet, [str(lib / "elmentett"), str(lib / "vegyes")]
        )
        assert wait_for_all_background_workers(30.0)
        shutil.move(str(felre / "h.jpg"), str(lib / "vegyes" / "h.jpg"))
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


def _kijeloltek(window) -> list[int]:
    indexek = window.property("selectedIndexes")
    if hasattr(indexek, "toVariant"):
        indexek = indexek.toVariant()
    return sorted(int(i) for i in indexek)


def _varj(qt_app, kor: int = 10) -> None:
    for _ in range(kor):
        qt_app.processEvents()
        QTest.qWait(20)


class TestARacsSzuroModban:
    """[KRITIKUS] a jobb oldali rács a mentetlen FÁJLOKRA szűkül."""

    def test_mentes_elott_minden_mappa_latszik(self, app, qt_app):
        window, controller, _e, _v, _lib, _cel = app
        assert {c["name"] for c in controller.feedGroups} == {
            "elmentett", "friss", "vegyes"}

    def test_mentes_kozben_csak_a_mentetlen_mappak_latszanak(self, app, qt_app):
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        grid = _elem(window, "photoGrid")
        assert grid.property("count") == 2
        assert _cimkek(window) == {"friss", "vegyes"}

    def test_a_reszben_mentett_mappabol_csak_a_mentetlen_fajl_latszik(
        self, app, qt_app
    ):
        """A `vegyes` három képéből kettő már el van mentve: a rácson egy
        marad — ugyanaz, amit a bal hasáb a mappa sorában felsorol."""
        window, controller, _e, _v, lib, _cel = app
        host = _nyisd_a_mentest(window, qt_app)
        assert len(_latszo(window, "thumbMouseArea")) == 3  # friss 2 + vegyes 1

        vegyes = next(
            c for c in controller.feedGroups if c["path"] == str(lib / "vegyes")
        )
        assert vegyes["count"] == 1
        assert controller.photos.photos[vegyes["start"]].name == "h.jpg"

        sorok = host.property("mentetlenek")
        if hasattr(sorok, "toVariant"):
            sorok = sorok.toVariant()
        bal_hasab = next(s for s in sorok if s["mappa"] == str(lib / "vegyes"))
        assert list(bal_hasab["fajlok"]) == ["h.jpg"]

    def test_kattintassal_kijelolheto_a_latszo_kep(self, app, qt_app):
        """[MAGAS] a rács normál használata (kijelölés) szűrő módban is él —
        valódi kattintással, nem a kezelő közvetlen hívásával."""
        window, controller, _e, _v, lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        vegyes = next(
            c for c in controller.feedGroups if c["path"] == str(lib / "vegyes")
        )
        # a látszó bélyegek a feed sorrendjében: a sorszám a szűrt listáé
        _kattints(window, _latszo(window, "thumbMouseArea")[vegyes["start"]], qt_app)

        assert _kijeloltek(window) == [vegyes["start"]], (
            "a kattintás nem a látszó (mentetlen) fényképet jelölte ki"
        )
        assert controller.photos.photos[vegyes["start"]].name == "h.jpg"

    def test_ctrl_a_a_mappa_latszo_kepeit_jeloli_ki(self, app, qt_app):
        """A Ctrl+A a mappán belül marad (#1184) — a részben elmentett
        mappában csak a látszó, mentetlen képet jelöli ki."""
        window, controller, _e, _v, lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        vegyes = next(
            c for c in controller.feedGroups if c["path"] == str(lib / "vegyes")
        )
        _kattints(window, _latszo(window, "thumbMouseArea")[vegyes["start"]], qt_app)
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        qt_app.processEvents()
        assert _kijeloltek(window) == [vegyes["start"]]
        assert controller.photos.photos[vegyes["start"]].name == "h.jpg"

    def test_bezaras_utan_minden_mappa_visszajon(self, app, qt_app):
        """[MAGAS] kilépéskor a rács szűrője visszaáll — az eredetiben
        mentés-üzemmódon KÍVÜL a rács változatlan."""
        window, controller, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        _kattints(window, _panel(window, "publishBackupCancel"), qt_app)

        grid = _elem(window, "photoGrid")
        assert grid.property("count") == 3
        assert controller.photos.rowCount() == 48 + 2 + 3


class TestAGorgetesiHelyzet:
    """[MAGAS] a mentés megnyitása és bezárása nem ugrasztja a rácsot."""

    def test_bezaras_utan_a_racs_ott_all_ahol_elotte(self, app, qt_app):
        window, controller, _e, _v, _lib, _cel = app
        grid = _elem(window, "photoGrid")
        _varj(qt_app)
        grid.setProperty("contentY", 600.0)
        _varj(qt_app, 5)
        elotte = grid.property("contentY")
        assert elotte == pytest.approx(600.0)

        _nyisd_a_mentest(window, qt_app)
        _varj(qt_app, 5)
        assert grid.property("count") == 2, "a szűrő nem kapcsolt be"
        # a szűrt rács a tetejéről indul
        assert grid.property("contentY") == pytest.approx(grid.property("originY"))
        _kattints(window, _panel(window, "publishBackupCancel"), qt_app)
        _varj(qt_app)

        assert grid.property("count") == 3
        assert grid.property("contentY") == pytest.approx(elotte)


def _csoport_elem(grid, index: int):
    """A `index`-edik mappacsoport delegate-je, vagy `None`, ha a ListView
    még (vagy már) nem példányosította."""
    return QMetaObject.invokeMethod(
        grid, "itemAtIndex", Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG("QQuickItem*"), Q_ARG("int", index),
    )


def _csoportkoz_y(grid, index: int) -> float:
    """Az `index`-edik csoport ALATTI térköz (`spacing`) közepe — a viewport
    teteje itt egyik csoport delegate-jébe sem esik bele."""
    elem = _csoport_elem(grid, index)
    assert elem is not None, f"a(z) {index}. csoport nincs példányosítva"
    koz = float(grid.property("spacing"))
    assert koz > 1, "a csoportok között nincs térköz — a próba értelmetlen"
    return elem.y() + elem.height() + koz / 2


class TestACsoportkozHorgony:
    """[MAGAS] a csoportok közti térköz is a görgetési helyzet része.

    A CI ubuntu-lábán (2026-09-27) a görgetési próba 600 helyett 428-ra állt
    vissza. Helyben a DejaVu betűkészlettel reprodukálva: a csoportok
    `0+291, 305+291, 610+1425` helyen álltak, tehát a `contentY = 600` a 2. és
    a 3. csoport közti 14 px-es térközbe esett. A `captureAnchor` ilyenkor
    egyik csoportot sem találta, a horgony régi (itt üres) maradt, és a
    mentés bezárása a nyers `y`-ra esett vissza — azt pedig a még becsült
    `contentHeight`-ra vágta (901 − 462 = 439)."""

    def test_a_csoportkozben_allo_nezet_horgonya_a_felette_allo_csoport(
        self, app, qt_app
    ):
        window, controller, _e, _v, _lib, _cel = app
        grid = _elem(window, "photoGrid")
        _varj(qt_app)
        y = _csoportkoz_y(grid, 0)
        grid.setProperty("contentY", y)
        _varj(qt_app, 5)
        assert grid.property("contentY") == pytest.approx(y)
        assert grid.property("anchorPath") == controller.feedGroups[0]["path"]
        assert grid.property("anchorOffset") == pytest.approx(
            y - _csoport_elem(grid, 0).y())

    def test_csoportkozbol_nyitva_bezaras_utan_ugyanott_all(self, app, qt_app):
        window, _c, _e, _v, _lib, _cel = app
        grid = _elem(window, "photoGrid")
        _varj(qt_app)
        y = _csoportkoz_y(grid, 1)
        grid.setProperty("contentY", y)
        _varj(qt_app, 5)
        elotte = grid.property("contentY")
        assert elotte == pytest.approx(y)

        _nyisd_a_mentest(window, qt_app)
        _varj(qt_app, 5)
        assert grid.property("count") == 2, "a szűrő nem kapcsolt be"
        _kattints(window, _panel(window, "publishBackupCancel"), qt_app)
        _varj(qt_app)

        assert grid.property("count") == 3
        assert grid.property("contentY") == pytest.approx(elotte)


class TestAVisszaallasBecsultMagassagnal:
    """[MAGAS] a visszaállás nem vághat a még BECSÜLT tartalommagasságra.

    A ListView a nem példányosított csoportok magasságát átlagból becsli; a
    nagy (48 képes) csoport helyén így a `contentHeight` jóval kisebb a
    valódinál. Mérve a CI-hiba helyi másán (DejaVu betűvel): a visszaállás
    pillanatában `contentHeight` 901 (valódi: 2035), a rács magassága 462,
    tehát a vágás 439-re tette a 600-as célt, és a delegate-ek beérkezése
    után ott is maradt.

    A helyzet a valódi mentés-nyitásból NEM idézhető elő determinisztikusan
    (a bezárás és a delegate-ek példányosodása közti verseny), ezért itt a
    visszaállító függvényt hívjuk, a versenyhelyzetet pedig pontosan
    beállítjuk: nincs gyorsítótár-sáv, a nagy csoport nincs példányosítva."""

    def test_a_nem_peldanyositott_csoportba_eso_cel_nem_vagodik(
        self, app, qt_app
    ):
        window, controller, _e, _v, _lib, _cel = app
        window.resize(1280, 700)
        grid = _elem(window, "photoGrid")
        grid.setProperty("cacheBuffer", 0)
        _varj(qt_app)
        utolso = int(grid.property("count")) - 1
        # a cél a nagy csoport belsejében (a valódi geometriából)
        grid.setProperty("contentY", _csoportkoz_y(grid, 0))
        _varj(qt_app, 3)
        cel = _csoportkoz_y(grid, utolso - 1) + 200.0
        grid.setProperty("contentY", cel)
        _varj(qt_app, 3)
        assert grid.property("contentY") == pytest.approx(cel)

        grid.setProperty("contentY", 0.0)
        _varj(qt_app, 3)
        assert _csoport_elem(grid, utolso) is None, (
            "a próba előfeltétele: a nagy csoport nincs példányosítva")
        assert grid.property("contentHeight") - grid.property("height") < cel, (
            "a próba előfeltétele: a becsült tartalommagasság a cél alá vág")

        QMetaObject.invokeMethod(
            grid, "mentesHelyzetVissza", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", {"path": "", "offset": 0.0, "y": cel}),
        )
        _varj(qt_app, 3)
        assert grid.property("contentY") == pytest.approx(cel)


class TestATajekoztatasARacson:
    """[MAGAS] a rács se maradjon szó nélkül üresen — és ne is hazudjon."""

    def test_ures_keszletnel_a_hivatalos_szoveg(self, app, qt_app):
        window, _c, _e, vezerlo, lib, _cel = app
        keszlet = vezerlo.keszletek()[0]["id"]
        # a többi fájlt is elmentjük — a készlet mostantól MINDENT tartalmaz
        vezerlo.futtasdMost(keszlet, None)
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

    def test_keszlet_nelkul_nem_allitja_hogy_minden_mentve(self, app, qt_app):
        """Kiválasztott készlet nélkül nincs mihez mérni: a rács a bal
        hasábhoz hasonlóan üres, de a „minden el van mentve" mondat hamis
        volna — nem jelenik meg."""
        window, _c, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app, keszlet=-1)
        _varj(qt_app, 3)
        grid = _elem(window, "photoGrid")
        assert grid.property("count") == 0
        assert _elem(window, "gridEmptyText").property("visible") is False

    def test_keszletrol_leveve_eltunik_a_szoveg(self, app, qt_app):
        window, _c, _e, vezerlo, _lib, _cel = app
        keszlet = vezerlo.keszletek()[0]["id"]
        vezerlo.futtasdMost(keszlet, None)
        from picasapy.app.worker_thread import wait_for_all_background_workers

        assert wait_for_all_background_workers(30.0)
        host = _nyisd_a_mentest(window, qt_app)
        szoveg = _elem(window, "gridEmptyText")
        assert szoveg.property("visible") is True
        host.setProperty("kivalasztott", -1)
        qt_app.processEvents()
        assert szoveg.property("visible") is False

    def test_szamolas_alatt_a_racs_a_regi_tartalmat_tartja(
        self, app, qt_app, monkeypatch
    ):
        """Számítás közben a `mentetlenek` átmenetileg üres — a rács ettől
        nem ürül ki, és NEM állíthatja, hogy „minden el van mentve" (#1798
        osztálya: hazudó állapot)."""
        import picasapy.app.backup_controller as modul

        window, _c, _e, _v, _lib, _cel = app
        host = _nyisd_a_mentest(window, qt_app)
        grid = _elem(window, "photoGrid")
        assert grid.property("count") == 2
        engedd = threading.Event()
        eredeti = modul.tervezd_meg

        def _lassu(*args, **kwargs):
            engedd.wait(5.0)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "tervezd_meg", _lassu)
        try:
            QMetaObject.invokeMethod(host, "frissitsdAMappakat")
            qt_app.processEvents()
            assert host.property("mappakToltodnek") is True
            assert grid.property("count") == 2
            szoveg = _elem(window, "gridEmptyText")
            assert szoveg.property("visible") is False
        finally:
            engedd.set()
        _vard_a_mappakat(host, qt_app)


class TestMasNezetbenATeljesLista:
    """[MAGAS] a szűrő a mentés-panel melletti KÖNYVTÁR-rácsé: keresésben,
    időrendben a teljes lista látszik; a szűrt rácsról nyitott néző viszont
    a szűrt listán lapoz."""

    _OSSZES = 48 + 2 + 3

    def test_keresesben_a_teljes_lista_utana_ismet_szurt(self, app, qt_app):
        window, controller, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        assert controller.photos.rowCount() == 3

        _kattints(window, _elem(window, "searchField"), qt_app)
        for betu in (Qt.Key.Key_J, Qt.Key.Key_P, Qt.Key.Key_G):
            QTest.keyClick(window, betu)
        _varj(qt_app)
        assert controller.searchActive is True
        assert controller.photos.rowCount() == self._OSSZES, (
            "a keresés a mentés-szűrőn át csak a mentetlen képeket adta"
        )

        _kattints(window, _elem(window, "searchClear"), qt_app)
        _varj(qt_app)
        assert controller.searchActive is False
        assert controller.photos.rowCount() == 3, (
            "a keresésből visszatérve a rács nem szűkült újra"
        )

    def test_idorendben_a_teljes_lista_utana_ismet_szurt(self, app, qt_app):
        """⚠️ Az Időrend belépési pontjai inaktívak (#1903: a menütétel
        szürke, a Ctrl+5 nem sül el), tehát valódi kattintással nem nyitható
        — az állapotot közvetlenül állítjuk."""
        window, controller, _e, _v, _lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        assert controller.photos.rowCount() == 3

        window.setProperty("timelineOpen", True)
        _varj(qt_app)
        assert controller.photos.rowCount() == self._OSSZES

        window.setProperty("timelineOpen", False)
        _varj(qt_app)
        assert controller.photos.rowCount() == 3

    def test_a_szurt_racsrol_nyitott_nezo_a_szurt_listan_lapoz(self, app, qt_app):
        window, controller, _e, _v, lib, _cel = app
        _nyisd_a_mentest(window, qt_app)
        vegyes = next(
            c for c in controller.feedGroups if c["path"] == str(lib / "vegyes")
        )
        cel = _latszo(window, "thumbMouseArea")[vegyes["start"]]
        kozep = cel.mapToScene(cel.boundingRect().center())
        QTest.mouseDClick(
            window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            QPoint(round(kozep.x()), round(kozep.y())),
        )
        _varj(qt_app)
        assert window.property("viewerOpen") is True
        assert controller.backupFilterActive is True
        assert controller.photos.rowCount() == 3

        QTest.keyClick(window, Qt.Key.Key_Escape)
        _varj(qt_app)
        assert window.property("viewerOpen") is False
        assert controller.photos.rowCount() == 3
