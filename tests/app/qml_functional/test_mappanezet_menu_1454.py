"""#1454: a `Nézet ▸ Mappanézet` almenü a bal hasáb SZERKEZETÉT állítja.

Az almenü korábban a `Mappa ▸ Sort By` szó szerinti másolata volt: öt
rendezési tétel, ugyanazzal a **`folderSort`** bekötéssel. Ez a másolat
hibás volt, és a #1454 helyesen távolította el.

⚠️ **HELYESBÍTÉS (#1766).** A #1454 ebből azt a következtetést is levonta,
hogy az almenüben *egyáltalán nincs* rendezés — csak szerkezeti tételek.
**Ez megdőlt.** A tulajdonos képernyőképe
(`research/#1766-nezet-mappanezet-almenu.png`) szerint az almenü így néz ki:

    ✓ Egyszerű mappanézet          [szerkezet]
      Fanézet                      [szerkezet]
      ────────────────────────────
    ✓ Rendezés létrehozási dátum alapján
      Rendezés a legutóbbi változtatások alapján
      Rendezés méret alapján
      Rendezés név alapján
      Rendezés megfordítása
      ────────────────────────────
      Gyorsbillentyűk ▸            [#1407]
      ────────────────────────────
      Indexképek megjelenítése a könyvtárban
      Egyszerűsített fanézet       [szerkezet]

Tehát **van** rendezés az almenüben — de a `eMenuView::` HOSSZÚ feliratú
ötös (`paneSort`), nem a Mappa menü rövid, négyes `folderSort` készlete.
A #1454 a ROSSZ készletet vette ki helyesen; a HELYESET a #1766 tette be.

A két készlet szétválasztása marad a lényeg: ezt az alábbi
`test_a_menusavban_csak_egy_helyen_marad_a_folderSort` őrzi.

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
from PySide6.QtQuick import QQuickItem

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


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a delegátumoknak nincs QObject-szülőjük."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _rendered_tree_paths(window) -> set[str]:
    """A ténylegesen KIRAJZOLT fasorok útvonalai.

    A `visible` öröklődik, ezért az `isVisible()`-t ÉS a valódi magasságot
    nézzük — a `folderHierarchyList.count` önmagában a modellből jön, és
    akkor is „helyes" volna, ha a fa sosem látszik (mutációval mérve).
    """
    prefix = "hierRow:"
    return {
        item.objectName()[len(prefix):]
        for item in _walk(_child(window, "folderPane"))
        if item.objectName().startswith(prefix)
        and item.isVisible()
        and item.height() > 0
    }


def _menu_item_texts(menu) -> list[str]:
    """Az almenü ÖSSZES menütételének felirata — objectName nélkül is.

    A stílusozott tételek osztályneve `MenuItem_QMLTYPE_…`, a helykitöltőké
    `PicasaMenuItem_QMLTYPE_…` — ezért részlet-egyezést nézünk. A `text`
    property több belső elemen (címke, ikon) is megjelenik, azokat az
    osztálynév zárja ki.
    """
    #: ⚠️ #2152: az `&` a MNEMONIK jelölése, nem a felirat tartalma — ez a
    #: fájl a KÉSZLETET méri (mely tételek vannak az almenüben).
    return [
        str(child.property("text") or "").replace("&", "")
        for child in menu.findChildren(QObject)
        if "MenuItem" in child.metaObject().className()
    ]


class TestAMappanezetAlmenuTartalma:
    """Kész, ha: a három szerkezeti tétel megvan, és a rendezés a HELYES
    (`paneSort`) készletből való — a `folderSort` négyesből egy sem."""

    def test_nincs_benne_a_MAPPA_menu_negyese(self, qml_app):
        """#1766: a tiltás a ROSSZ készletre szól, nem minden rendezésre.

        A Mappa menü rövid feliratai (`&Date`, `&Name`, `&Size`,
        `&Reverse order`) ide másolva ugyanaz a hiba lenne, amit a #1454
        javított."""
        window, _controller, _engine = qml_app
        texts = _menu_item_texts(_child(window, "menuViewFolderView"))
        assert texts, "a Mappanézet almenüben egyetlen tétel sincs"
        rovid = [t for t in texts if t in ("&Date", "&Name", "&Size",
                                           "&Reverse order")]
        assert rovid == [], (
            f"a Mappa menü RÖVID készlete beszivárgott ide: {rovid}"
        )

    def test_a_harom_szerkezeti_tetel_all_benne(self, qml_app):
        window, _controller, _engine = qml_app
        texts = _menu_item_texts(_child(window, "menuViewFolderView"))
        for szerkezeti in ("Flat Folder View", "Tree View",
                           "Simplified Tree View"):
            assert szerkezeti in texts, f"hiányzik: {szerkezeti}"

    def test_a_HOSSZU_otos_is_benne_van(self, qml_app):
        """#1766: a felvételen mért `eMenuView::` készlet."""
        window, _controller, _engine = qml_app
        texts = _menu_item_texts(_child(window, "menuViewFolderView"))
        # ⚠️ #2152: a `_menu_item_texts` mnemonik NÉLKÜL adja a feliratokat
        for hosszu in ("Sort by Creation Date", "Sort by Recent Changes",
                       "Sort by Size", "Sort by Name", "Reverse sort"):
            assert hosszu in texts, f"hiányzik a Nézet-készletből: {hosszu}"

    def test_a_menusavban_csak_egy_helyen_marad_a_folderSort(self):
        """A `Mappa ▸ Sort By` négy szempontja + a megfordítás — és semmi
        más. Forrásszintű őr: a duplikálás pont így csúszott be."""
        # #2152: az `&` a MNEMONIK jelölése, nem a felirat tartalma.
        source = _MENU_QML.read_text(encoding="utf-8").replace("&", "")
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

    def test_a_valtas_utan_a_kijelolt_mappa_latszik_a_faban(
        self, qml_app, qt_app
    ):
        """MÉRT hiba volt: fa-módra váltva a hasáb EGYETLEN, összecsukott
        sorra („Sajátgép") zsugorodott, és a kijelölt mappa sehol nem
        látszott.

        Az ok: a `revealPath()` csak a `selectedPath` VÁLTOZÁSÁRA futott,
        a nézetmód-váltásra nem — a nyitott ágak halmaza pedig induláskor
        üres, és a `flatten()` a virtuális gyökeret sem tekinti nyitottnak.
        A fanézet eddig menüből elérhetetlen volt, ezért ezt még senki nem
        láthatta; a spec 6. pontja („a váltás megőrzi a görgetést") N sorról
        1 sorra esve nem teljesülne.
        """
        window, controller, _engine = qml_app
        kijelolt = controller.currentFolder
        assert kijelolt, "a fixture nem választott ki mappát — nincs mit mérni"

        _trigger(window, "menuViewTreeView")
        qt_app.processEvents()

        sorok = _rendered_tree_paths(window)
        assert kijelolt in sorok, (
            "a fanézetre váltás után a kijelölt mappa nem látszik a fában; "
            f"kirajzolt sorok: {sorted(sorok)}"
        )

    def test_a_valtas_nem_zsugoritja_ossze_a_hasabot(self, qml_app, qt_app):
        """A lapos listában látott mappák a fában is elérhetők maradnak —
        a váltás nem eshet vissza egyetlen összecsukott sorra."""
        window, _controller, _engine = qml_app
        lapos_sorok = _child(window, "folderListView").property("count")

        _trigger(window, "menuViewTreeView")
        qt_app.processEvents()

        sorok = _rendered_tree_paths(window)
        # a gyökérsoron felül legalább annyi mappasor, ahányat a lapos
        # lista mutatott (a fában a köztes szintek is sorok, tehát több)
        assert len(sorok) > lapos_sorok, (
            f"a fa {len(sorok)} sorra zsugorodott, a lapos lista "
            f"{lapos_sorok} sort mutatott"
        )

    def test_az_egyszeru_tetele_visszavalt(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        _trigger(window, "menuViewTreeView")
        qt_app.processEvents()
        # a KÖZBENSŐ állapotot is állítjuk: e nélkül a teszt akkor is zöld
        # maradna, ha a fa-módra váltás egyáltalán nem történt volna meg
        # (mutációval mérve) — a végállapot ugyanis mindkét esetben lapos
        assert _child(window, "folderHierarchyList").property("visible") is True
        assert _rendered_tree_paths(window) != set()

        _trigger(window, "menuViewFlatFolderView")
        qt_app.processEvents()

        assert _child(window, "folderListView").property("visible") is True
        assert _child(window, "folderHierarchyList").property("visible") is False
        assert _rendered_tree_paths(window) == set(), (
            "lapos módban a fa egyetlen sora sem rajzolódhat ki"
        )
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
        szinteket, tehát a KIRAJZOLT fa rövidebb lesz.

        A `folderHierarchyList.count` NEM elég: az a modellből jön, és
        mutációval mérve akkor is helyes maradt, amikor a fa egyáltalán nem
        látszott (visszaégetett `treeViewMode: false`). Ezért a kirajzolt
        sorokat és a lista láthatóságát is állítjuk.
        """
        window, _controller, engine = qml_app
        hier = _hierarchy(engine)
        _trigger(window, "menuViewTreeView")
        hier.expandAll()
        qt_app.processEvents()
        assert _child(window, "folderHierarchyList").property("visible") is True
        elotte = _rendered_tree_paths(window)

        _trigger(window, "menuViewSimplifiedTreeView")
        qt_app.processEvents()
        utana = _rendered_tree_paths(window)

        assert len(elotte) > 1, (
            "a mért fa túl sekély ahhoz, hogy legyen mit összevonni"
        )
        assert len(utana) < len(elotte), (
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
        assert _child(window, "folderHierarchyList").property("visible") is True
        elotte = _rendered_tree_paths(window)

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
        utana = _rendered_tree_paths(window)
        assert len(elotte) > 1
        assert len(utana) < len(elotte)

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
