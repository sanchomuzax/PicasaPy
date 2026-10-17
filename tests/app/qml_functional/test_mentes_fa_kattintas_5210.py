"""#5210: a fanézet mentés-módjában a mentetlen mappa sorára vagy a pipára
kattintva a mappa megjelölődik, ugyanúgy, mint a lapos listában.

A `test_mentes_szuro_main_3681.py` lapos listás kattintásos próbájának párja
a fanézetre: a VALÓDI `Main.qml`-ben, valódi egérkattintással.

Két dolgot mér, amit a `_kattints` (`_racs_helyimenuk_5150_helpers`) nem:
* hová ment a PRESS: a kattintás a fasor egérterületére (`hierRowMouse:`)
  érkezett-e. A sor csonkolva (a lista `clip`-je miatt) a mögötte lévő
  rácsba esne, és a régi helper ezt néma kihagyásnak nézte volna.
* csak a PANELEN BELÜLI elemet kattintja: a vágáson kívüli szöveg nem
  látszik, ezért nem is lehet rajta kattintani.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
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


def _latszo(window, nev: str) -> list[QQuickItem]:
    talalat = [
        e for e in _walk(window.contentItem())
        if e.objectName() == nev and _tenyleg_latszik(e)
    ]
    return sorted(talalat, key=lambda e: e.mapToScene(QPointF(0, 0)).y())


def _fa_latszo(window, nev: str) -> list[QQuickItem]:
    """A fanézet LÁTHATÓ sorai: a lista vágásán (`clip`) belül is álljon.

    A fa mélyen fekvő útja miatt a sor szövege kiesik a 240 px-es hasábról;
    az ilyen elemre kattintás a mögötte lévő rácsba menne."""
    lista = window.findChild(QQuickItem, "folderHierarchyList")
    assert lista is not None, "a fanézet listája nem található"
    bal = lista.mapToScene(QPointF(0, 0)).x()
    return [
        e for e in _latszo(window, nev)
        if e.mapToScene(QPointF(0, 0)).x() >= bal
        and e.mapToScene(QPointF(e.width(), 0)).x() <= bal + lista.width()
    ]


def _panel(window, nev: str) -> QQuickItem:
    """A MENTÉS-panel eleme. Az Ajándék-CD gazdája ugyanezt a
    `PublishPanel`-t hordozza, azonos objectName-ekkel."""
    host = window.findChild(QObject, "backupHost")
    elem = host.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található a mentés-panelen"
    return elem


def _kozep(elem: QQuickItem) -> QPoint:
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    return QPoint(round(kozep.x()), round(kozep.y()))


def _kattints(window, elem, qt_app) -> None:
    qt_app.processEvents()
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs mérete, nem kattintható"
    )
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        _kozep(elem),
    )
    qt_app.processEvents()


def _sorra_kattints(window, elem, sor_nev: str, qt_app) -> None:
    """Valódi kattintás, és ellenőrzi, hogy a PRESS a `sor_nev` sorára ment.

    A press után a `mouseGrabberItem` az az egérterület, amely a kattintást
    kezeli; ha ez nem a fasor, a kattintás a sor mellett ment el."""
    qt_app.processEvents()
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs mérete, nem kattintható"
    )
    pont = _kozep(elem)
    # a valódi egér előbb odaér, és csak utána nyom: a hover-állapot is számít
    QTest.mouseMove(window, pont)
    qt_app.processEvents()
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()
    fogo = window.mouseGrabberItem()
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()
    leiras = (
        f"{fogo.metaObject().className()}[{fogo.objectName()}]"
        if fogo is not None else "nincs"
    )
    assert fogo is not None and fogo.objectName() == sor_nev, (
        f"a {elem.objectName()} kattintása nem a sorra ment, hanem: {leiras}"
    )


def _menutetelre_kattints(window, qt_app, fejlec: str, nev: str) -> None:
    """Felső menü és menütétel valódi egérkattintással."""
    fejlec_elem = next(
        (
            e for e in _walk(window.contentItem())
            if "MenuBarItem" in e.metaObject().className()
            and e.property("text") == fejlec
        ),
        None,
    )
    assert fejlec_elem is not None, f"a {fejlec} menü nincs a menüsávon"
    _kattints(window, fejlec_elem, qt_app)
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    assert varj_feltetelre(
        qt_app, lambda: elem.isVisible()
    ), f"a {nev} menütétel nem látható"
    _kattints(window, elem, qt_app)


def _vard_a_mappakat(host, qt_app) -> None:
    assert varj_feltetelre(
        qt_app, lambda: host.property("mappakToltodnek") is False
    ), "a mentetlen mappák listája nem érkezett meg"
    qt_app.processEvents()


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else list(ertek)


def _epitsd_az_appot(qt_app, tmp_path, monkeypatch):
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


@pytest.fixture
def app(qt_app, tmp_path, monkeypatch):
    yield from _epitsd_az_appot(qt_app, tmp_path, monkeypatch)


@pytest.fixture
def app_windows(qt_app, tmp_path, monkeypatch):
    """A windowsos kulcsképzés (#3799) Linuxon: a `flat_key` windowsos ágra
    fut, és a próbaút nagybetűt tartalmaz, hogy a kisbetűsítés látszódjon."""
    monkeypatch.setattr("picasapy.paths._platform", lambda: "win32")
    gyoker = tmp_path / "Windows-Alak"
    gyoker.mkdir()
    yield from _epitsd_az_appot(qt_app, gyoker, monkeypatch)


def _nyisd_a_mentest(window, qt_app, *, keszlet: int = 0):
    """A VALÓDI menütétel (`Eszközök ▸ Képek biztonsági mentése…`), majd a
    készlet kiválasztása."""
    _menutetelre_kattints(window, qt_app, "&Tools", "menuToolsBackup")
    qt_app.processEvents()
    host = window.findChild(QObject, "backupHost")
    assert host.property("nyitva") is True
    host.setProperty("kivalasztott", keszlet)
    _vard_a_mappakat(host, qt_app)
    return host


def _fanezet(engine, qt_app, be: bool) -> None:
    fa = engine.rootContext().contextProperty("folderHierarchyController")
    fa.setTreeView(be)
    qt_app.processEvents()


def _levelut(ut) -> str:
    """Az INDEXELT mappa sorának útja a fában (`str(Path)`)."""
    return str(ut)


class TestALaposListaKontroll:
    """Kontroll: a lapos lista sorára kattintva a mappa megjelölődik. Ha
    ez bukik, a kattintás-harness a hibás, nem a fanézet."""

    def test_a_lapos_lista_sorara_kattintva_a_mappa_pipalodik(
        self, app, qt_app
    ):
        window, _c, _e, _v, lib, _cel = app
        host = _nyisd_a_mentest(window, qt_app)
        nyaralas = _levelut(lib / "2024" / "nyaralas")
        sor = next(
            e for e in _latszo(window, "folderRowLabel")
            if e.property("text").startswith("nyaralas")
        )
        _kattints(window, sor, qt_app)
        assert _lista(host.property("pipaltMappak")) == [nyaralas]


class TestAFanezetMentesKattintas:
    """[MAGAS] a fanézet mentés-módjában a mentetlen mappa sorára vagy a
    pipára kattintva a mappa megjelölődik, mint a lapos listában."""

    def test_a_pipara_kattintva_a_mappa_pipalodik(self, app, qt_app):
        window, controller, engine, _v, lib, _cel = app
        _fanezet(engine, qt_app, True)
        host = _nyisd_a_mentest(window, qt_app)
        nyaralas = _levelut(lib / "2024" / "nyaralas")
        elotte = controller.property("currentFolder")
        pipa = _fa_latszo(window, "hierMentesCheck:" + nyaralas)
        assert len(pipa) == 1, "a mentetlen mappa pipája nem látszik a fában"

        _sorra_kattints(window, pipa[0], "hierRowMouse:" + nyaralas, qt_app)

        assert _lista(host.property("pipaltMappak")) == [nyaralas]
        assert _fa_latszo(
            window, "hierMentesCheck:" + nyaralas)[0].property("checked") is True
        assert controller.property("currentFolder") == elotte, (
            "szűrő módban a kattintás pipál, nem nyit meg mappát"
        )

    def test_a_sor_ures_reszere_kattintva_a_mappa_pipalodik(self, app, qt_app):
        window, _c, engine, _v, lib, _cel = app
        _fanezet(engine, qt_app, True)
        host = _nyisd_a_mentest(window, qt_app)
        nyaralas = _levelut(lib / "2024" / "nyaralas")
        sor = _fa_latszo(window, "hierRow:" + nyaralas)
        assert len(sor) == 1, "a mentetlen mappa sora nem látszik a fában"

        _sorra_kattints(window, sor[0], "hierRowMouse:" + nyaralas, qt_app)

        assert _lista(host.property("pipaltMappak")) == [nyaralas]

    def test_a_sor_szovegere_kattintva_a_mappa_pipalodik(self, app, qt_app):
        """Csak a rövid, nem vágott sornál: a szöveg a látható hasábon belül
        van. A `simplified` mód a köztes, üres szinteket elhagyja."""
        window, _c, engine, _v, lib, _cel = app
        fa = engine.rootContext().contextProperty("folderHierarchyController")
        fa.setSimplified(True)
        _fanezet(engine, qt_app, True)
        host = _nyisd_a_mentest(window, qt_app)
        nyaralas = _levelut(lib / "2024" / "nyaralas")
        darab = _fa_latszo(window, "hierCount:" + nyaralas)
        assert len(darab) == 1, "a darabszám nem látszik a rövid fában"

        _sorra_kattints(window, darab[0], "hierRowMouse:" + nyaralas, qt_app)

        assert _lista(host.property("pipaltMappak")) == [nyaralas]


class TestAFanezetWindowsKulcs:
    """[MAGAS] a windowsos kulcs (#3799) nem nyeli el a fa kattintását."""

    def test_a_pipara_kattintva_a_mappa_pipalodik_windowsos_kulccsal(
        self, app_windows, qt_app
    ):
        window, _c, engine, _v, lib, _cel = app_windows
        _fanezet(engine, qt_app, True)
        host = _nyisd_a_mentest(window, qt_app)
        nyaralas = _levelut(lib / "2024" / "nyaralas")
        pipa = _fa_latszo(window, "hierMentesCheck:" + nyaralas)
        assert len(pipa) == 1, "a mentetlen mappa pipája nem látszik windowsos kulccsal"

        _sorra_kattints(window, pipa[0], "hierRowMouse:" + nyaralas, qt_app)

        assert _lista(host.property("pipaltMappak")) == [nyaralas]
