"""A bal hasáb mért maradékai — #757 (1. és 3. pont).

A 2026-08-15-i mérő kör három, számokkal alátámasztott hibát hagyott a
hasábon (a P1/P2 tételek a #730–#732-ben már bementek):

1. **Az „Új album” súgó mindig ott van.** Az eredeti Picasa ezt a mondatot
   az ÜRES albumlistán mutatta; nálunk állandó, és 230 képpontos hasábon
   58 képpontot — 2,6 mappasornyi helyet — vesz el.
3. **Az exportált mappa sora album-nézetben is kijelöltnek látszik.** A
   `pane.selectedAlbumToken === ""` őr, amit a mappalista sora és a
   gyűjtemény-mappa sora is használ, ebből az egy sorból kimaradt — album
   megnyitásakor két sor látszik egyszerre kijelöltnek.

A 2. pont (menüfeliratok, mnemonikok) külön fájlban méri magát
(`test_menu_labels_757.py`), a 4. (tegezés/magázás) fordítási kör.

Miért kirajzolva: mindkét hiba GEOMETRIA és SZÍN kérdése — a meglévő
tesztek pont azért nem kapták el, mert a szöveg/tétel LÉTÉT állították, a
feltételét nem.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView

try:
    from PySide6.QtTest import QTest

    _QTTEST_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    QTest = None
    _QTTEST_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTTEST_VAN,
    reason=(
        "a PySide6.QtTest modul hiányzik ezen a gépen. Debian/Ubuntu alatt "
        "így pótolható: sudo apt install python3-pyside6.qttest"
    ),
)

_KEEPALIVE: list[object] = []

#: A mért hasábszélesség — a #757 1. pontja EZEN a szélességen mért 58 px-et.
_HASAB_SZELESSEG = 230


@pytest.fixture
def render_pane(qt_app):
    """Kirajzolt `QQuickView` a FolderPane-nel, controller nélkül (#305)."""
    import picasapy.app.application as app_module

    def _render(**properties):
        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", None)
        url = QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        )
        component = QQmlComponent(engine, url)
        pane = component.createWithInitialProperties(properties)
        errors = [error.toString() for error in component.errors()]
        assert errors == [], errors
        assert pane is not None

        view = QQuickView(engine, None)
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        view.setContent(url, component, pane)
        view.resize(_HASAB_SZELESSEG, 800)
        view.show()
        QTest.qWaitForWindowExposed(view)
        QTest.qWait(80)
        qt_app.processEvents()

        _KEEPALIVE.extend((engine, component, view, pane))
        return view, pane

    return _render


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _repeater_item(pane, repeater_name, index):
    """A `Repeater` index. delegate-példánya (a `findChild` nem látja)."""
    repeater = _child(pane, repeater_name)
    item = QMetaObject.invokeMethod(
        repeater,
        "itemAt",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(QQuickItem),
        Q_ARG(int, index),
    )
    assert item is not None, f"{repeater_name}[{index}] nem jött létre"
    return item


def _albums(count):
    return [
        {"token": f"album{i}", "name": f"Album {i}", "count": i + 1}
        for i in range(count)
    ]


class TestAzUjAlbumSugoCsakUresListan:
    """#757/1 — a súgó a felfedezhetőséget szolgálja, nem a díszítést."""

    def test_ures_albumlistan_lathato(self, render_pane):
        """Az eredeti Picasa ÜRES albumlistáján állt ott ez a mondat."""
        _view, pane = render_pane(albumsModel=[])

        sugo = _child(pane, "albumDropHintText")
        assert sugo.property("visible") is True
        assert "album" in sugo.property("text").lower()

    def test_elso_album_utan_eltunik(self, render_pane, qt_app):
        _view, pane = render_pane(albumsModel=_albums(1))

        sugo = _child(pane, "albumDropHintText")
        assert sugo.property("visible") is False, (
            "az „Új album” súgó az albumok mellett is helyet foglal (#757/1)"
        )

    def test_a_megsporolt_hely_a_sugo_teljes_magassaga(self, render_pane, qt_app):
        """A #757 a hasáb szélessége szerint 42–58 px-et mért. A pontos
        számot nem égetjük be (betűméret- és témafüggő), a KÖVETELMÉNYT
        viszont igen: az elrejtés a súgó TELJES magasságát felszabadítja, és
        az több egy mappasornál — vagyis valódi nyereség, nem kozmetika."""
        _view, ures = render_pane(albumsModel=[])
        _view2, teli = render_pane(albumsModel=_albums(1))

        sugo_magassag = _child(ures, "albumDropHintText").property("height")
        nyereseg = (
            _child(ures, "starredItem").property("y")
            - _child(teli, "starredItem").property("y")
        )

        assert abs(nyereseg - sugo_magassag) < 1.0, (
            f"a súgó {sugo_magassag:.0f} px magas, de csak {nyereseg:.0f} px "
            "szabadult fel — #757/1"
        )
        assert nyereseg > ures.property("rowHeight"), (
            f"a felszabadult {nyereseg:.0f} px egy mappasornál "
            f"({ures.property('rowHeight')} px) sem több — #757/1"
        )

    def test_csukott_gyujtemenyben_sem_latszik(self, render_pane, qt_app):
        """A korábbi feltétel (`!albumsCollapsed`) nem veszhet el."""
        _view, pane = render_pane(albumsModel=[], albumsCollapsed=True)

        assert _child(pane, "albumDropHintText").property("visible") is False


class TestAzExportaltMappaSoraAlbumNezetben:
    """#757/3 — album megnyitásakor csak az album sora legyen kiemelve."""

    EXPORTED = [{"path": "/export/nyar", "name": "nyar"}]

    def test_mappa_nezetben_ki_van_jelolve(self, render_pane, qt_app):
        """Ellenpróba: a kiemelés attól még működik."""
        _view, pane = render_pane(
            exportedFolders=self.EXPORTED,
            projectsCollapsed=False,
            selectedPath="/export/nyar",
        )

        sor = _repeater_item(pane, "exportedFolderRepeater", 0)
        assert sor.property("color").alpha() > 0, (
            "mappa-nézetben az exportált mappa sorának kijelöltnek kell lennie"
        )

    def test_album_nezetben_nincs_kiemelve(self, render_pane, qt_app):
        _view, pane = render_pane(
            exportedFolders=self.EXPORTED,
            projectsCollapsed=False,
            selectedPath="/export/nyar",
            selectedAlbumToken="album0",
            albumsModel=_albums(1),
        )

        sor = _repeater_item(pane, "exportedFolderRepeater", 0)
        assert sor.property("color").alpha() == 0, (
            "album-nézetben az exportált mappa sora is kijelöltnek látszik — "
            "hiányzik a `selectedAlbumToken === \"\"` őr (#757/3)"
        )
