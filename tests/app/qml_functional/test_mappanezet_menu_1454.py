"""#1454: a `Nézet ▸ Mappanézet` almenü a bal hasáb SZERKEZETÉT állítja.

Az almenü korábban a `Mappa ▸ Sort By` szó szerinti másolata volt: öt
rendezési tétel, ugyanazzal a `folderSort` bekötéssel. Az eredetiben ez az
almenü nem rendez, hanem a bal hasáb gyökerét és hierarchiáját szabja meg
— három tétellel, amelyek közül nálunk egyetlen sem volt elérhető menüből
(`docs/specs/picasa-mappanezet.md`).

A pipa-logika mérve (`0x00574b70`, spec 3.): az „Egyszerű mappanézet" és a
„Fanézet" EGYETLEN bájt két állapota, tehát kizáró pár; az
„Egyszerűsített fanézet" ettől FÜGGETLEN, önálló kapcsoló.

Minden itteni teszt a VALÓDI menütételt aktiválja — a kattintás mindkét
lépésével (`toggle()` + `triggered`, ld. a `_trigger` docstringjét) —, nem
a mögötte lévő Python-metódust hívja, és a KIMENETET méri: mi látszik a bal
hasábon. Egy elrontott kötés így nem maradhat zölden.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

_MENU_QML = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "picasapy"
    / "app"
    / "qml"
    / "PicasaPy"
    / "PicasaMenuBar.qml"
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _hierarchy(engine):
    ctl = engine.rootContext().contextProperty("folderHierarchyController")
    assert ctl is not None, "a folderHierarchyController nincs regisztrálva"
    return ctl


def _trigger(root, name):
    """A menütétel aktiválása — a VALÓDI kattintás két lépése.

    A `QQuickAbstractButton` kattintás-útja előbb `toggle()`-t hív (ez
    IMPERATÍVAN írja a `checked`-et, felülütve a QML-kötést), és csak utána
    dördül el a `triggered`. Ha a teszt csak a jelzést bocsátaná ki, a pipa
    viselkedése méretlen maradna — pedig épp ott volt hiba (#1454): a már
    aktív tételre kattintva mindkét pipa eltűnt.
    """
    item = _child(root, name)
    if item.property("checkable"):
        QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


def _menu_item_texts(menu) -> list[str]:
    """Az almenü ÖSSZES menütételének felirata — objectName nélkül is.

    A stílusozott tételek osztályneve `MenuItem_QMLTYPE_…`, a helykitöltőké
    `PicasaMenuItem_QMLTYPE_…` — ezért részlet-egyezést nézünk. A `text`
    property több belső elemen (címke, ikon) is megjelenik, azokat az
    osztálynév zárja ki.
    """
    return [
        child.property("text")
        for child in menu.findChildren(QObject)
        if "MenuItem" in child.metaObject().className()
    ]


class TestAMappanezetAlmenuTartalma:
    """Kész, ha: három szerkezeti tétel, egyetlen rendezési tétel nélkül."""

    def test_nincs_benne_rendezesi_tetel(self, qml_app):
        window, _controller, _engine = qml_app
        texts = _menu_item_texts(_child(window, "menuViewFolderView"))
        assert texts, "a Mappanézet almenüben egyetlen tétel sincs"
        rendezes = [t for t in texts if "Sort" in t or "Reverse" in t]
        assert rendezes == [], (
            f"a Mappanézet almenüben rendezési tétel maradt: {rendezes}"
        )

    def test_a_harom_szerkezeti_tetel_all_benne(self, qml_app):
        window, _controller, _engine = qml_app
        texts = _menu_item_texts(_child(window, "menuViewFolderView"))
        assert texts == [
            "Flat Folder View",
            "Tree View",
            "Simplified Tree View",
        ]

    def test_a_menusavban_csak_egy_helyen_marad_a_folderSort(self):
        """A `Mappa ▸ Sort By` négy szempontja + a megfordítás — és semmi
        más. Forrásszintű őr: a duplikálás pont így csúszott be."""
        source = _MENU_QML.read_text(encoding="utf-8")
        assert source.count("controller.setFolderSort(") == 4
        assert source.count("controller.toggleFolderSortReverse()") == 1


class TestEgyszeruEsFaKizaroPar:
    """`0x00574b70`: egyetlen bájt (`[+0x9d]`) két állapota."""

    def test_a_fanezet_tetele_atvaltja_a_bal_hasabot(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        assert _child(window, "folderListView").property("visible") is True

        _trigger(window, "menuViewTreeView")
        qt_app.processEvents()

        # a KIMENET: a lapos lista eltűnik, a fa jelenik meg
        assert _child(window, "folderListView").property("visible") is False
        fa = _child(window, "folderHierarchyList")
        assert fa.property("visible") is True
        assert fa.property("count") > 0
        assert _hierarchy(engine).treeView is True

    def test_az_egyszeru_tetele_visszavalt(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        _trigger(window, "menuViewTreeView")
        qt_app.processEvents()
        _trigger(window, "menuViewFlatFolderView")
        qt_app.processEvents()

        assert _child(window, "folderListView").property("visible") is True
        assert _child(window, "folderHierarchyList").property("visible") is False
        assert _hierarchy(engine).treeView is False

    def test_a_mar_aktiv_tetelre_kattintva_marad_a_pipa(self, qml_app, qt_app):
        """MÉRT hiba volt (#1454): a kattintás átbillenti a `checked`-et,
        és ha a vezérlő állapota nem változik, a kötés nem értékelődik újra
        — a menü újranyitásakor EGYIK tételen sem lett volna pipa."""
        window, _controller, engine = qml_app
        lapos = _child(window, "menuViewFlatFolderView")
        assert lapos.property("checked") is True

        _trigger(window, "menuViewFlatFolderView")  # már lapos módban vagyunk
        qt_app.processEvents()

        assert _hierarchy(engine).treeView is False
        assert lapos.property("checked") is True, (
            "a már aktív nézetmód pipája eltűnt"
        )
        assert _child(window, "menuViewTreeView").property("checked") is False

    def test_a_ket_pipa_egyszerre_sosem_all(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        lapos = _child(window, "menuViewFlatFolderView")
        fa = _child(window, "menuViewTreeView")

        assert lapos.property("checked") is True
        assert fa.property("checked") is False

        _trigger(window, "menuViewTreeView")
        qt_app.processEvents()

        assert lapos.property("checked") is False
        assert fa.property("checked") is True


class TestEgyszerusitettFanezetFuggetlenKapcsolo:
    """`0x9db8` pipája a `[+0x9d]`-től FÜGGETLEN (spec 3.)."""

    def test_bekapcsolhato_lapos_modban_is(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        _trigger(window, "menuViewSimplifiedTreeView")
        qt_app.processEvents()

        hier = _hierarchy(engine)
        assert hier.simplified is True
        # …és a nézetmódhoz nem nyúlt hozzá
        assert hier.treeView is False
        assert _child(window, "menuViewSimplifiedTreeView").property("checked") is True

    def test_a_nezetmod_valtasa_nem_kapcsolja_ki(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        _trigger(window, "menuViewSimplifiedTreeView")
        qt_app.processEvents()
        _trigger(window, "menuViewTreeView")
        qt_app.processEvents()

        hier = _hierarchy(engine)
        assert hier.simplified is True
        assert hier.treeView is True

    def test_a_fan_tenylegesen_kevesebb_sor_marad(self, qml_app, qt_app):
        """A KIMENET mérése: az egyszerűsítés összevonja a köztes
        szinteket, tehát a kirajzolt fa rövidebb lesz."""
        window, _controller, engine = qml_app
        hier = _hierarchy(engine)
        _trigger(window, "menuViewTreeView")
        hier.expandAll()
        qt_app.processEvents()
        elotte = _child(window, "folderHierarchyList").property("count")

        _trigger(window, "menuViewSimplifiedTreeView")
        qt_app.processEvents()
        utana = _child(window, "folderHierarchyList").property("count")

        assert elotte > 1, "a mért fa túl sekély ahhoz, hogy legyen mit összevonni"
        assert utana < elotte, (
            f"az egyszerűsítés nem rövidítette a fát ({elotte} → {utana})"
        )


class TestARendezesAMaradtHelyenMukodik:
    """A `Mappa ▸ Sort By` regressziós őre — a jegy kifejezetten kiköti."""

    def test_a_mappa_rendezes_tovabbra_is_a_folderSortot_allitja(
        self, qml_app, qt_app
    ):
        window, controller, engine = qml_app
        _trigger(window, "menuFolderSortBySize")
        qt_app.processEvents()

        assert controller.folderSort == "size"
        # …és a nézetmódhoz nem nyúlt
        assert _hierarchy(engine).treeView is False

    def test_a_megforditas_tovabbra_is_hat(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        elotte = controller.folderSortReverse
        _trigger(window, "menuFolderSortReverse")
        qt_app.processEvents()
        assert controller.folderSortReverse is not elotte

    def test_a_nezetmod_valtasa_nem_rendez_at(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        elotte = (controller.folderSort, controller.folderSortReverse)
        _trigger(window, "menuViewTreeView")
        _trigger(window, "menuViewSimplifiedTreeView")
        qt_app.processEvents()
        assert (controller.folderSort, controller.folderSortReverse) == elotte


class TestAHelyiMenuEgyszerusitettTetele:
    """`FolderListContextMenu` — a tétel eddig `placeholder: true` volt."""

    def test_a_tetel_elo(self, qml_app):
        window, _controller, _engine = qml_app
        item = _child(window, "folderListMenuSimplifiedTree")
        assert item.property("enabled") is True

    def test_kattintasra_valtozik_a_kirajzolt_fa(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        hier = _hierarchy(engine)
        _trigger(window, "menuViewTreeView")
        hier.expandAll()
        qt_app.processEvents()
        elotte = _child(window, "folderHierarchyList").property("count")

        pane = _child(window, "folderPane")
        QMetaObject.invokeMethod(
            pane,
            "openFolderListContextMenu",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        _trigger(window, "folderListMenuSimplifiedTree")
        qt_app.processEvents()

        assert hier.simplified is True
        utana = _child(window, "folderHierarchyList").property("count")
        assert elotte > 1
        assert utana < elotte

    def test_a_pipaja_a_vezerlo_allapotat_mutatja(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        item = _child(window, "folderListMenuSimplifiedTree")
        assert item.property("checked") is False

        _hierarchy(engine).setSimplified(True)
        qt_app.processEvents()

        assert item.property("checked") is True


def test_a_folderpane_a_vezerlobol_veszi_a_nezetmodot(qml_app, qt_app):
    """A `Main.qml` korábban `treeViewMode: false`-t égetett be — a hasáb
    így akkor sem váltott volna, ha a menü már bekötött."""
    window, _controller, engine = qml_app
    pane = _child(window, "folderPane")
    assert pane.property("treeViewMode") is False

    _hierarchy(engine).setTreeView(True)
    qt_app.processEvents()

    assert pane.property("treeViewMode") is True
