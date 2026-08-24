"""#1345 — az alsó műveletsor gombjai KIRAJZOLVA, képpontra mérve.

A `respack.yt` rétegfejlécei (`docs/specs/picasa-keptalca.md` 11.) az
eredeti kimeneti sávjának MINDEN gombjára ugyanazt adják: a gomb
**55 × 36**, a cellája **59 × 40**, azaz 2-2 képpont margó körben. Az
elválasztó a cellán belül **2 × 27**, vízszintesen középen, felülről 8
képpont behúzással.

Nálunk a mérés (2026-08-24, 1280 px-es ablak) ezt adta: E-mail 75 × 29,
Nyomtatás 65 × 29, Exportálás 75 × 29, Kollázs 30 × 42, Film 30 × 44,
Megosztás 30 × 44 — hét gomb, hat különböző méret.

Miért KIRAJZOLVA mérünk (a `test_editor_panel_rendered_651.py` mintája):
a gomb tényleges mérete a szülő elrendezéséből (RowLayout, `Layout.*`,
kompakt mód) áll elő, nem a komponens saját property-jéből. Izolált
komponensen olvasott `width` hamis biztonságot adna. A `Repeater`
delegáltjait ráadásul a `findChild` sem találja meg — innen a `_walk()`.

⚠️ HATÓKÖR: az eredeti kilenc gombjából nálunk **hat** létezik
(`pbutton`, `ebutton`, `folderbutton`, `sharewith`, `collage`, `movie`);
a `orderbutton` (Vásárlás), `blogger` és `morebutton` nálunk NINCS MEG —
ezek a `docs/specs/ui-lefedettseg.md` `outputlayout` hiánylistáján
szerepelnek, külön jegy tárgyai. A `webupload` (a zöld „Feltöltés a
Google Fotókba") NEM tartozik a mért kilenc közé: a respack a kimeneti
sáv kilenc rétegét adja, a webupload nincs köztük.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtQuick import QQuickItem, QQuickView


class FakeAppWindow(QObject):
    """A TrayBar `appWindow` felülete — csak amit a komponens olvas.

    A `tests/app/test_qml_tray_responsive.py` azonos nevű osztályának
    párja. Nem onnan importáljuk: a `tests/app` nem csomag (nincs
    `__init__.py`), tesztmodulból tesztmodult importálni pedig a
    `run_tests.py` fájlonkénti processzeiben törékeny lenne.
    """

    selectedIndexesChanged = Signal()
    selectedIndexChanged = Signal()
    viewerOpenChanged = Signal()
    thumbSizeChanged = Signal()

    def __init__(self, selected=()):
        super().__init__()
        self._selected_indexes = list(selected)
        self._selected_index = self._selected_indexes[0] if selected else -1
        self._viewer_open = False
        self._thumb_size = 100

    @Property(list, notify=selectedIndexesChanged)
    def selectedIndexes(self):
        return self._selected_indexes

    @Property(int, notify=selectedIndexChanged)
    def selectedIndex(self):
        return self._selected_index

    @Property(bool, notify=viewerOpenChanged)
    def viewerOpen(self):
        return self._viewer_open

    @Property(int, notify=thumbSizeChanged)
    def thumbSize(self):
        return self._thumb_size

    @Slot(result=bool)
    def rotateTargetsAllVideo(self):
        return False

#: A mért geometria (spec 11.) — egyetlen helyen, hogy a bukás
#: üzenetéből is látsszon, mihez képest mérünk.
GOMB_SZELESSEG = 55
GOMB_MAGASSAG = 36
CELLA_SZELESSEG = 59
CELLA_MAGASSAG = 40
ELVALASZTO_SZELESSEG = 2
ELVALASZTO_MAGASSAG = 27

#: A gombok az eredeti respack DEKLARÁCIÓS sorrendjében (spec 7.), a
#: nálunk hiányzó `orderbutton`/`blogger`/`morebutton` kihagyásával.
#: A név szerinti felsorolás a lényeg: a bukás megmondja, MELYIK rossz.
MUVELETGOMBOK = (
    ("pbutton", "trayPrintButton"),
    ("ebutton", "trayEmailButton"),
    ("folderbutton", "trayExportButton"),
    ("sharewith", "trayShareButton"),
    ("collage", "trayCollageButton"),
    ("movie", "trayMovieButton"),
)

#: Az ablakszélességek, amelyeken a méretnek TARTANIA kell magát. A jegy
#: FIX képpontot ír elő, tehát a gomb nem skálázódhat az ablakkal — és a
#: kompakt mód (#406) küszöbének két oldalán is ugyanakkora kell legyen.
ABLAKSZELESSEGEK = (900, 1000, 1280, 1600, 1920)

_KEEPALIVE: list[object] = []

_TRAY_QML = """
import QtQuick
import PicasaPy 1.0
Item {
    id: root
    property var win
    TrayBar {
        objectName: "tray"
        appWindow: root.win
        width: root.width
        anchors.bottom: parent.bottom
    }
}
"""


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása (ld. a #651-es teszt azonos nevű segédjét)."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _child(root: QQuickItem, name: str) -> QQuickItem:
    for item in _walk(root):
        if item.objectName() == name:
            return item
    found = root.findChild(QObject, name)
    assert found is not None, f"{name} nem található a kirajzolt fában"
    return found


def _cella(gomb: QQuickItem) -> QQuickItem:
    """A gombot befoglaló `TrayActionCell` — az ősláncban felfelé keresve.

    Nem a KÖZVETLEN szülőt kérdezzük: a cella egy belső, 55 × 36-os
    dobozba teszi a gombját (ott áll elő a 2-2 képpontos margó), tehát a
    `parentItem()` ezt a dobozt adná. A cellát a saját, mért geometriát
    kiíró `cellWidth` tulajdonságáról ismerjük fel.
    """
    csomopont = gomb.parentItem()
    while csomopont is not None and csomopont.property("cellWidth") is None:
        csomopont = csomopont.parentItem()
    assert csomopont is not None, (
        f"{gomb.objectName()} nincs `TrayActionCell`-ben — nincs mihez "
        "képest mérni a 2-2 képpontos margót"
    )
    return csomopont


def _tray(qt_app, width: int):
    """A TrayBar VALÓDI ablakban, adott szélességgel — a layout lefuttatva."""
    from PySide6.QtQml import QQmlComponent

    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.engine().rootContext().setContextProperty("controller", None)
    component = QQmlComponent(view.engine())
    component.setData(_TRAY_QML.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    window = FakeAppWindow(selected=(0, 1, 2))
    root.setProperty("win", window)
    root.setParentItem(view.contentItem())
    view.resize(width, 700)
    root.setWidth(width)
    root.setHeight(700)
    view.show()
    for _ in range(5):
        qt_app.processEvents()
    _KEEPALIVE.extend((view, root, window, component))
    return root


class TestMindenMuveletgomb55x36:
    """A jegy fő állítása: a hat meglévő műveletgomb MÉRETE azonos."""

    @pytest.mark.parametrize("szelesseg", ABLAKSZELESSEGEK)
    def test_a_gombok_pontosan_55x36_kepponton_allnak(self, qt_app, szelesseg):
        root = _tray(qt_app, szelesseg)

        mert = {}
        for respack_nev, object_name in MUVELETGOMBOK:
            gomb = _child(root, object_name)
            mert[respack_nev] = (round(gomb.width()), round(gomb.height()))

        elvart = {
            respack_nev: (GOMB_SZELESSEG, GOMB_MAGASSAG)
            for respack_nev, _ in MUVELETGOMBOK
        }
        assert mert == elvart, (
            f"{szelesseg} px-es ablakban a műveletgombok mérete nem "
            f"{GOMB_SZELESSEG}×{GOMB_MAGASSAG} (respack, spec 11.)"
        )

    def test_a_meret_nem_skalazodik_az_ablakkal(self, qt_app):
        """A jegy FIX képpontot ír elő — a széles ablak sem nyújthatja."""
        meretek = {}
        for szelesseg in ABLAKSZELESSEGEK:
            root = _tray(qt_app, szelesseg)
            meretek[szelesseg] = [
                (round(_child(root, name).width()),
                 round(_child(root, name).height()))
                for _, name in MUVELETGOMBOK
            ]

        elso = meretek[ABLAKSZELESSEGEK[0]]
        for szelesseg, ertek in meretek.items():
            assert ertek == elso, (
                f"a gombméretek {szelesseg} px-en eltérnek a "
                f"{ABLAKSZELESSEGEK[0]} px-en mértektől: {ertek} != {elso}"
            )


class TestA59x40esCella:
    """Minden gomb 59 × 40-es cellában ül, 2-2 képpont margóval."""

    @pytest.mark.parametrize("respack_nev,object_name", MUVELETGOMBOK)
    def test_a_cella_59x40_es_a_gomb_kozepen_all(
        self, qt_app, respack_nev, object_name
    ):
        root = _tray(qt_app, 1280)
        gomb = _child(root, object_name)

        cella = _cella(gomb)

        assert (round(cella.width()), round(cella.height())) == (
            CELLA_SZELESSEG,
            CELLA_MAGASSAG,
        ), (
            f"{respack_nev} cellája {cella.width():.0f}×{cella.height():.0f} "
            f"— a mért érték {CELLA_SZELESSEG}×{CELLA_MAGASSAG}"
        )

        bal_felso = gomb.mapToItem(cella, 0, 0)
        assert (round(bal_felso.x()), round(bal_felso.y())) == (2, 2), (
            f"{respack_nev} gombja a cellán belül "
            f"({bal_felso.x():.0f}, {bal_felso.y():.0f})-nál kezdődik — "
            "a mért érték (2, 2)"
        )


class TestAzElvalaszto:
    """A `outputlayout/separator`: 2 × 27, a cellán belül középen."""

    def test_van_elvalaszto_es_2x27(self, qt_app):
        root = _tray(qt_app, 1600)

        elvalasztok = [
            item
            for item in _walk(root)
            if item.objectName() == "trayActionSeparatorRule"
        ]
        assert elvalasztok, (
            "nincs egyetlen elválasztó sem a műveletsorban "
            "(`outputlayout/separator`, spec 11.)"
        )
        for rule in elvalasztok:
            assert (round(rule.width()), round(rule.height())) == (
                ELVALASZTO_SZELESSEG,
                ELVALASZTO_MAGASSAG,
            ), (
                f"az elválasztó {rule.width():.0f}×{rule.height():.0f} — "
                f"a mért érték {ELVALASZTO_SZELESSEG}×{ELVALASZTO_MAGASSAG}"
            )
            cella = rule.parentItem()
            bal_felso = rule.mapToItem(cella, 0, 0)
            assert round(bal_felso.x()) == 28, (
                f"az elválasztó x={bal_felso.x():.0f}-nál áll a cellában "
                "— a mért érték 28"
            )
            assert round(bal_felso.y()) == 8, (
                f"az elválasztó y={bal_felso.y():.0f}-nál áll a cellában "
                "— a mért érték 8 (felülről 8, alulról 5 behúzás)"
            )


class TestAGombokSorrendje:
    """A respack deklarációs sorrendje (spec 7.), a hiányzók kihagyásával."""

    def test_balrol_jobbra_a_respack_sorrendjeben_allnak(self, qt_app):
        root = _tray(qt_app, 1600)
        tray = _child(root, "tray")

        sorrend = [
            (respack_nev, _child(root, name).mapToItem(tray, 0, 0).x())
            for respack_nev, name in MUVELETGOMBOK
        ]
        mert_sorrend = [nev for nev, _ in sorted(sorrend, key=lambda p: p[1])]
        elvart_sorrend = [nev for nev, _ in MUVELETGOMBOK]

        assert mert_sorrend == elvart_sorrend, (
            "a műveletgombok sorrendje eltér a respack deklarációs "
            f"sorrendjétől: {mert_sorrend} != {elvart_sorrend}"
        )


class TestAValodiFoablakban:
    """Ugyanez a VALÓDI `Main.qml`-ben — a szülő elrendezésével együtt.

    A fenti tesztek önálló `TrayBar`-t töltenek egy `QQuickView`-ba. Ez a
    kör azt zárja ki, hogy a főablak elrendezése (a `Main.qml`
    oszlopa, a valódi controller és kijelölés) elmozdítsa a méretet.
    """

    def test_a_foablakban_is_55x36_minden_muveletgomb(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        for _ in range(3):
            qt_app.processEvents()

        mert = {}
        for respack_nev, object_name in MUVELETGOMBOK:
            gomb = window.findChild(QObject, object_name)
            assert gomb is not None, f"{object_name} nem található a főablakban"
            mert[respack_nev] = (
                round(float(gomb.property("width"))),
                round(float(gomb.property("height"))),
            )

        elvart = {
            respack_nev: (GOMB_SZELESSEG, GOMB_MAGASSAG)
            for respack_nev, _ in MUVELETGOMBOK
        }
        assert mert == elvart, (
            "a valódi főablakban a műveletgombok mérete nem "
            f"{GOMB_SZELESSEG}×{GOMB_MAGASSAG}"
        )
