"""Home / End / PageUp / PageDown a rácsban (#1147).

## Az eredeti — bizonyíték

Teljes levezetés: `docs/specs/picasa-eger-es-kijeloles.md` 12. A `CThumbUI`
billentyűkezelője (`0x005c24c0`) a `VK_HOME`/`VK_END`/`VK_PRIOR`/`VK_NEXT`
kódokat a `CMultiAlbumNode` felületére osztja (`+0x84` = `0x0076a390`
Home, `+0x88` = `0x0076a400` End). A nem-Ctrl ág a JELENLEGI mappa
kijelölés-csomópontján dolgozik (`[esi+0x2e0]` → `[+0x300]` →
`[+0x2b4]`), a Shiftet pedig a mag választja szét (`0x00718930`):

- Shift nélkül: minden kijelölés le (`0x718a50`), majd egy lépés — üres
  kijelölésnél a léptető mag (`0x00717eb0`) az elemlista ELSŐ (`+1`) vagy
  UTOLSÓ (`−1`) elemét veszi, ezért „ugrás" lesz belőle;
- Shifttel: tartomány a horgonytól (`[edi+0x390]`) a lista végéig
  (`0x716ae0`), horgony nélkül pedig MINDENT kijelöl (`0x716f40`).

A Ctrl-ág görget: Home a könyvtár elejére (`0x76a2f0`), End az UTOLSÓ
albumhoz (`[eax+0x2c0]` lista, darabszám `−1`, `0x768470`).

## A teszt

⚠️ **Valódi billentyűesemény** megy a `photoGrid`-re — a #1148 és a #1200
is azért maradt zöld egy használhatatlan funkció fölött, mert a teszt a
kezelőfüggvényt hívta közvetlenül.
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QMetaObject, QObject, Qt
from PySide6.QtGui import QKeyEvent

from support.jpeg_factory import make_jpeg


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _ket_mappas_feed(qml_app, qt_app):
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    for mappa, darab in (("alma", 4), ("korte", 4)):
        (lib / mappa).mkdir(exist_ok=True)
        for i in range(darab):
            make_jpeg(lib / mappa / f"{mappa}{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    csoportok = controller.feedGroups
    assert len(csoportok) >= 2
    return window, controller, csoportok


def _grid(window):
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None, "a photoGrid nem található"
    return grid


def _billentyu(window, qt_app, key, mods=Qt.KeyboardModifier.NoModifier):
    grid = _grid(window)
    grid.setProperty("focus", True)
    QMetaObject.invokeMethod(
        grid, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    qt_app.sendEvent(window, QKeyEvent(QEvent.Type.KeyPress, key, mods))
    qt_app.processEvents()


def _kijelolt(window):
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return sorted(int(i) for i in (ertek or []))


def _allj(window, qt_app, sor):
    """Kiindulás: egy sor kijelölve, a horgony ugyanoda állítva."""
    window.setProperty("selectedIndexes", [sor])
    window.setProperty("selectedIndex", sor)
    _grid(window).setProperty("selectionAnchor", sor)
    qt_app.processEvents()


def _masodik_csoport(csoportok):
    cs = csoportok[1]
    start = int(cs["start"])
    return start, start + int(cs["count"]) - 1


class TestHomeEnd:
    def test_home_a_mappa_elso_kepere_szukit(self, qml_app, qt_app):
        window, _c, csoportok = _ket_mappas_feed(qml_app, qt_app)
        start, utolso = _masodik_csoport(csoportok)
        _allj(window, qt_app, utolso)

        _billentyu(window, qt_app, Qt.Key.Key_Home)

        assert _kijelolt(window) == [start]
        assert window.property("selectedIndex") == start

    def test_end_a_mappa_utolso_kepere_szukit(self, qml_app, qt_app):
        window, _c, csoportok = _ket_mappas_feed(qml_app, qt_app)
        start, utolso = _masodik_csoport(csoportok)
        _allj(window, qt_app, start)

        _billentyu(window, qt_app, Qt.Key.Key_End)

        assert _kijelolt(window) == [utolso]
        assert window.property("selectedIndex") == utolso

    def test_shift_end_a_horgonytol_a_mappa_vegeig(self, qml_app, qt_app):
        window, _c, csoportok = _ket_mappas_feed(qml_app, qt_app)
        start, utolso = _masodik_csoport(csoportok)
        _allj(window, qt_app, start + 1)

        _billentyu(
            window, qt_app, Qt.Key.Key_End, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == list(range(start + 1, utolso + 1))

    def test_shift_home_a_horgonytol_a_mappa_elejeig(self, qml_app, qt_app):
        window, _c, csoportok = _ket_mappas_feed(qml_app, qt_app)
        start, utolso = _masodik_csoport(csoportok)
        _allj(window, qt_app, utolso - 1)

        _billentyu(
            window, qt_app, Qt.Key.Key_Home, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == list(range(start, utolso))

    def test_shift_end_horgony_nelkul_az_egesz_mappat(self, qml_app, qt_app):
        """Az eredetiben ilyenkor a mag a `0x716f40`-re fut: MINDENT
        kijelöl — a jelenlegi mappa csomópontjában."""
        window, controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        start, utolso = _masodik_csoport(csoportok)
        controller.selectFolder(csoportok[1]["path"])
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        _grid(window).setProperty("selectionAnchor", -1)
        qt_app.processEvents()

        _billentyu(
            window, qt_app, Qt.Key.Key_End, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == list(range(start, utolso + 1))

    def test_a_mappahataron_nem_ler_at(self, qml_app, qt_app):
        """#1145/#1219: a hatókör a jelenlegi mappacsoport."""
        window, _c, csoportok = _ket_mappas_feed(qml_app, qt_app)
        start, utolso = _masodik_csoport(csoportok)
        _allj(window, qt_app, start)

        _billentyu(
            window, qt_app, Qt.Key.Key_End, Qt.KeyboardModifier.ShiftModifier
        )

        assert max(_kijelolt(window)) <= utolso
        assert min(_kijelolt(window)) >= start


class TestGorgetoBillentyuk:
    """Ctrl+Home / Ctrl+End / PageUp / PageDown — görget, de a kijelölést
    NEM változtatja."""

    def _kijeloles_valtozatlan(self, window, qt_app, key, mods):
        _allj(window, qt_app, 1)
        elotte = _kijelolt(window)
        _billentyu(window, qt_app, key, mods)
        assert _kijelolt(window) == elotte, (
            f"a(z) {key} megváltoztatta a kijelölést"
        )

    def test_ctrl_home_nem_valtoztat_kijelolest(self, qml_app, qt_app):
        window, _c, _cs = _ket_mappas_feed(qml_app, qt_app)
        self._kijeloles_valtozatlan(
            window, qt_app, Qt.Key.Key_Home, Qt.KeyboardModifier.ControlModifier
        )

    def test_ctrl_end_nem_valtoztat_kijelolest(self, qml_app, qt_app):
        window, _c, _cs = _ket_mappas_feed(qml_app, qt_app)
        self._kijeloles_valtozatlan(
            window, qt_app, Qt.Key.Key_End, Qt.KeyboardModifier.ControlModifier
        )

    def test_pagedown_gorget_de_nem_jelol(self, qml_app, qt_app):
        window, _c, _cs = _ket_mappas_feed(qml_app, qt_app)
        self._kijeloles_valtozatlan(
            window, qt_app, Qt.Key.Key_PageDown, Qt.KeyboardModifier.NoModifier
        )

    def test_pageup_gorget_de_nem_jelol(self, qml_app, qt_app):
        window, _c, _cs = _ket_mappas_feed(qml_app, qt_app)
        self._kijeloles_valtozatlan(
            window, qt_app, Qt.Key.Key_PageUp, Qt.KeyboardModifier.NoModifier
        )

    def test_ctrl_home_a_feed_elejere_gorget(self, qml_app, qt_app):
        window, _c, _cs = _ket_mappas_feed(qml_app, qt_app)
        grid = _grid(window)
        grid.setProperty("contentY", 300)
        qt_app.processEvents()

        _billentyu(
            window, qt_app, Qt.Key.Key_Home, Qt.KeyboardModifier.ControlModifier
        )

        assert float(grid.property("contentY")) <= float(
            grid.property("originY")
        ) + 1, "a Ctrl+Home nem görgetett a feed elejére"
