"""#3681 — mentés-üzemmódban a KÖNYVTÁR (bal hasáb) a MÉG EL NEM MENTETT
mappákra szűkül, pipálható sorokkal — mindkét nézetmódon (lapos lista ÉS
mappafa).

Az eredeti Picasa mentés-módja (`backuptext2`/`backuptext3`,
`docs/specs/biztonsagi-mentes.md` 9.–10.) NEM külön sávban mutatja a
mentendő mappákat, hanem a KÖNYVTÁRBAN: a #3504 (PR #3673) egy külön sávot
(`BackupFolderStrip.qml`) vezetett be helyette, mert a hasábnak akkor még
nem volt szűrő-módja. Ez a jegy pótolja a hiányzó módot — a `mentesSzuroAktiv`
szerződéssel (`FolderPane.qml`/`FolderHierarchyView.qml` fejkomment) —, és a
strip emiatt megszűnt (BackupHost.qml).

A `FolderPane`/`FolderHierarchyView` delegátumainak sorai a `Repeater`/
`ListView` VIZUÁLIS gyerekei — a `findChild` nem éri el őket (MEMORY
2026-07-31, ld. `test_folder_hierarchy_view_702.py` fejkommentje is), ezért
mindkét osztály a vizuális fát járja be (`_walk`/`_latszo_elemek`).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

import picasapy.app.application as app_module
from picasapy.app.folder_hierarchy_controller import FolderHierarchyController
from picasapy.app.models import FolderListModel
from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg

_KEEPALIVE: list[object] = []


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása (`test_folder_hierarchy_view_702.py` mintája)."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _latszo_elemek(gyoker: QQuickItem, nev: str) -> list[QQuickItem]:
    """A `nev` nevű, ténylegesen KIRAJZOLT (látszó, nem 0 magasságú) elemek,
    képernyő-sorrendben — a duplikált delegate-objectName-ek mintája
    (`test_mentes_mappapipa_ui_3594.py`)."""
    talalat = [
        elem for elem in _walk(gyoker)
        if elem.objectName() == nev and elem.isVisible() and elem.height() > 0
    ]
    return sorted(talalat, key=lambda e: e.mapToScene(e.position()).y())


def _kattints(view, elem, qt_app) -> None:
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _sorok(*mappak: tuple[str, int]) -> list[dict]:
    """{mappa, nev, darab, fajlok, bajt} sorok — a
    `BackupController.mentetlenMappakLekerese()` alakja, kézzel."""
    return [
        {
            "mappa": mappa, "nev": mappa.rsplit("/", 1)[-1],
            "darab": darab, "fajlok": [], "bajt": 0,
        }
        for mappa, darab in mappak
    ]


def _bekot_pipalast(objektum) -> None:
    """A `BackupHost.pipald()` python-oldali tükre — a gazda ezt hívná meg
    a `mentesPipaldKert` jelzésre, itt a próba szimulálja."""

    def _pipald(mappa, be):
        jelenlegi = [m for m in objektum.property("mentesPipaltMappak") if m != mappa]
        if be:
            jelenlegi.append(mappa)
        objektum.setProperty("mentesPipaltMappak", jelenlegi)

    objektum.mentesPipaldKert.connect(_pipald)


@pytest.fixture
def library(tmp_path):
    lib = tmp_path / "kepek"
    for nev in ("nyaralas", "szulinap", "elmentett"):
        (lib / nev).mkdir(parents=True)
    make_jpeg(lib / "nyaralas" / "a.jpg")
    make_jpeg(lib / "nyaralas" / "b.jpg")
    make_jpeg(lib / "szulinap" / "c.jpg")
    make_jpeg(lib / "elmentett" / "d.jpg")
    return lib


class TestALaposLista:
    """A hasáb LAPOS mappalistája (`FolderPane.qml`, `folderListView`)."""

    @pytest.fixture
    def pane(self, qt_app, tmp_path, library):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, library)
            folders_model = FolderListModel()
            folders_model.load(conn)

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", None)
        url = QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        )
        component = QQmlComponent(engine, url)
        root = component.createWithInitialProperties({"foldersModel": folders_model})
        errors = [e.toString() for e in component.errors()]
        assert errors == [], errors
        assert root is not None
        folders_model.setParent(root)

        view = QQuickView(engine, None)
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        view.setContent(url, component, root)
        view.resize(260, 400)
        view.show()
        QTest.qWaitForWindowExposed(view)

        root.setProperty("mentesSzuroAktiv", True)
        root.setProperty(
            "mentesMentetlenMappak",
            _sorok(
                (str(library / "nyaralas"), 2),
                (str(library / "szulinap"), 1),
            ),
        )
        root.setProperty("mentesPipaltMappak", [])
        _bekot_pipalast(root)
        qt_app.processEvents()

        _KEEPALIVE.extend((engine, component, view, root, folders_model))
        yield view, root, library
        view.hide()

    def test_csak_a_mentetlen_mappak_latszanak(self, pane):
        _, root, library = pane
        cimkek = [e.property("text") for e in _latszo_elemek(root, "folderRowLabel")]
        nevek = [c.rsplit(" (", 1)[0] for c in cimkek]
        assert sorted(nevek) == ["nyaralas", "szulinap"], (
            f"az elmentett mappa nem tűnt el a szűrt listából: {nevek}"
        )

    def test_a_pipak_alapbol_uresek(self, pane):
        _, root, _ = pane
        pipak = _latszo_elemek(root, "folderRowMentesCheck")
        assert len(pipak) == 2
        assert all(p.property("checked") is False for p in pipak)

    def test_kattintas_a_soron_pipalja_a_mappat(self, pane, qt_app):
        view, root, library = pane
        pipak = _latszo_elemek(root, "folderRowMentesCheck")
        elso = pipak[0]
        assert elso.property("checked") is False

        _kattints(view, elso, qt_app)

        assert elso.property("checked") is True
        assert len(root.property("mentesPipaltMappak")) == 1

        # ugyanoda kattintva megint — jelöletlenít
        _kattints(view, elso, qt_app)
        assert elso.property("checked") is False
        assert root.property("mentesPipaltMappak") == []

    def test_kikapcsolt_szuronel_a_teljes_lista_latszik(self, pane):
        _, root, library = pane
        root.setProperty("mentesSzuroAktiv", False)

        cimkek = [e.property("text") for e in _latszo_elemek(root, "folderRowLabel")]
        nevek = sorted(c.rsplit(" (", 1)[0] for c in cimkek)
        assert nevek == ["elmentett", "nyaralas", "szulinap"], (
            "a szűrő kikapcsolása után minden mappának vissza kell térnie"
        )
        assert _latszo_elemek(root, "folderRowMentesCheck") == []


class TestAFa:
    """A hasáb hierarchikus (fa) mappanézete (`FolderHierarchyView.qml`)."""

    _QML = b"""
import QtQuick
import PicasaPy 1.0
Item {
    objectName: "hierRoot"
    FolderHierarchyView {
        id: hierView
        objectName: "folderHierarchyView"
        anchors.fill: parent
        hierarchy: folderHierarchyController
    }
}
"""

    @pytest.fixture
    def fa(self, qt_app):
        controller = FolderHierarchyController()
        controller.setFolders([
            {"path": "/kepek/nyaralas", "count": 2},
            {"path": "/kepek/szulinap", "count": 1},
            {"path": "/kepek/elmentett", "count": 1},
        ])
        controller.expandAll()

        view = QQuickView()
        view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
        view.engine().rootContext().setContextProperty(
            "folderHierarchyController", controller
        )
        component = QQmlComponent(view.engine())
        component.setData(self._QML, QUrl())
        errors = [e.toString() for e in component.errors()]
        assert errors == [], errors
        root = component.create()
        assert root is not None
        root.setParentItem(view.contentItem())
        view.resize(280, 300)
        root.setWidth(280)
        root.setHeight(300)
        view.show()
        QTest.qWaitForWindowExposed(view)

        hier_view = root.findChild(QQuickItem, "folderHierarchyView")
        assert hier_view is not None
        hier_view.setProperty("mentesSzuroAktiv", True)
        hier_view.setProperty(
            "mentesMentetlenMappak",
            _sorok(
                ("/kepek/nyaralas", 2),
                ("/kepek/szulinap", 1),
            ),
        )
        hier_view.setProperty("mentesPipaltMappak", [])
        _bekot_pipalast(hier_view)
        qt_app.processEvents()

        _KEEPALIVE.extend((view, component, root, controller, hier_view))
        yield view, root, hier_view, controller
        view.hide()

    def _sor_utak(self, root) -> set[str]:
        prefix = "hierRow:"
        return {
            elem.objectName()[len(prefix):]
            for elem in _walk(root)
            if elem.objectName().startswith(prefix)
            and elem.isVisible() and elem.height() > 0
        }

    def test_csak_a_gyoker_es_a_mentetlen_mappak_latszanak(self, fa):
        _, root, _hier_view, _controller = fa
        assert self._sor_utak(root) == {"", "/kepek/nyaralas", "/kepek/szulinap"}, (
            "az elmentett mappa és a köztes csomópont nem tűnt el a szűrt fáról"
        )

    def test_a_pipak_alapbol_uresek(self, fa):
        _, root, _hier_view, _controller = fa
        pipak = _latszo_elemek(root, "hierMentesCheck:/kepek/nyaralas") \
            + _latszo_elemek(root, "hierMentesCheck:/kepek/szulinap")
        assert len(pipak) == 2
        assert all(p.property("checked") is False for p in pipak)

    def test_kattintas_a_faasoron_pipalja_a_mappat(self, fa, qt_app):
        view, root, hier_view, _controller = fa
        pipa = _latszo_elemek(root, "hierMentesCheck:/kepek/nyaralas")[0]
        assert pipa.property("checked") is False

        sormouse = _latszo_elemek(root, "hierRowMouse:/kepek/nyaralas")[0]
        _kattints(view, sormouse, qt_app)

        assert pipa.property("checked") is True
        assert hier_view.property("mentesPipaltMappak") == ["/kepek/nyaralas"]

    def test_kikapcsolt_szuronel_a_teljes_fa_latszik(self, fa):
        _, root, hier_view, _controller = fa
        hier_view.setProperty("mentesSzuroAktiv", False)

        assert self._sor_utak(root) == {
            "", "/", "/kepek",
            "/kepek/nyaralas", "/kepek/szulinap", "/kepek/elmentett",
        }
        assert _latszo_elemek(root, "hierMentesCheck:/kepek/nyaralas") == []
