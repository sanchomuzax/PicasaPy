"""A törlés gyorsbillentyűje felület szerint válik szét (#1418).

## Az eredeti — bizonyíték

`docs/specs/picasa-gyorsbillentyuk.md` 4. szakasza (a helyi menük
`0x00a6aee0` rekordjai, a #1154 mérése): "A törlés billentyűje
felület-függő... rácsban/nézőben `Ctrl+Delete`, a menüsávban `Delete`. A
`cmd` azonos (`0x9c9a`), tehát egy parancs, két belépő."

## Nálunk — a MAI állapot (ELŐBB felmérve, aztán javítva)

Két KÜLÖN Shortcut-forrás létezik, nem csak az, amit ez a jegy eredetileg
feltételezett:

- `PicasaMenuBar.qml` `shortcutDeleteFromDisk` — bare `Delete`, a rács
  kontextusában él (`!viewerOpen && kijelölés`). Ez a menüsáv útja —
  HELYES, változatlan.
- `Main.qml` `shortcutDeleteFromDiskGrid` (**TILOS fájl ehhez a
  jegyhez**) — `Ctrl+Delete`, ugyanabban a rács-kontextusban. Ez MÁR
  #422 óta helyesen létezik — a jegy kiindulási feltevése ("a rácsban
  nincs élő Ctrl+Delete") téves volt, ezt a mai kód felmérése cáfolta.
- `Main.qml` `shortcutDeleteFromDiskViewer` (**szintén tiltott fájl**) —
  bare `Delete`, a nézőben. EZ VOLT a tényleges hiba: a #422-es, korábbi
  (spec 3.) feltevés szerint kötve, amit a friss #1154-mérés (spec 4.)
  felülírt — a helyes érték `Ctrl+Delete` volna, akárcsak a rácsban. Az
  ÚJ `Ctrl+Delete` bekötés (ez a jegy) a `PhotoViewer.qml`
  `Keys.onPressed`-jébe került, mert a `Main.qml`-hez NEM szabad
  nyúlnom — a puszta `Delete` a nézőben ezért ISMERT, dokumentált
  maradvány-hibaként MEGMARAD, amíg az integrátor a Main.qml egysoros
  javítását el nem végzi.

## A teszt

⚠️ Valódi billentyűesemény megy az ablakra (a #1417 mintája) — nem a
kezelő közvetlen hívása; a #1148/#1200 pont ettől a rövidítéstől maradt
zöld egy hatástalan funkció fölött.

⚠️ Kísérletileg igazolt csapda (ne ismételd meg): egy `Keys.
onShortcutOverride`-dal próbáltuk elfogni a rácsbeli puszta Delete-et —
ez a teszt-környezetben (és feltehetően élesben is) NEM állítja meg a
`Shortcut{}` window-szintű aktiválását, csak hamis biztonságérzetet adna
egy VISSZAFORDÍTHATATLAN művelethez. Ezért ide nem került ilyen kód.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QMetaObject, QObject, Qt
from PySide6.QtGui import QKeyEvent
from support.qml_halasztott import epitsd_fel_ha_fileops


def _gyerek(window, nev):
    epitsd_fel_ha_fileops(window, nev)  # #1612: halasztott párbeszédek
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _fokusz(elem, qt_app):
    elem.setProperty("focus", True)
    QMetaObject.invokeMethod(
        elem, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _billentyu(window, qt_app, key, mods=Qt.KeyboardModifier.NoModifier):
    qt_app.sendEvent(window, QKeyEvent(QEvent.Type.KeyPress, key, mods))
    qt_app.processEvents()


def _lista(ertek):
    """QJSValue → Python lista (a `test_search.py` mintája)."""
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return list(ertek)


class TestRacsCtrlDeleteMarMukodott:
    """Regresszió: a rács Ctrl+Delete-je (Main.qml `shortcutDeleteFrom-
    DiskGrid`, #422 óta) NEM romolhatott el ennek a jegynek a nyomán."""

    def test_ctrl_delete_megerositest_nyit_a_racsban(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        _fokusz(_gyerek(window, "photoGrid"), qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is False

        _billentyu(
            window, qt_app, Qt.Key.Key_Delete,
            Qt.KeyboardModifier.ControlModifier,
        )

        assert confirm.property("visible") is True, (
            "a rácsban a Ctrl+Delete-nek törlést kellene kérdeznie"
        )


class TestNezobenMostMarCtrlDeleteTorol:
    """#1418 tényleges javítása: a néző (OneUp) Ctrl+Delete-je eddig
    egyáltalán nem volt élő billentyű — mostantól az."""

    def _nezo(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = _gyerek(window, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        _fokusz(viewer, qt_app)
        return viewer

    def test_ctrl_delete_torol_a_nezoben(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        self._nezo(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is False

        _billentyu(
            window, qt_app, Qt.Key.Key_Delete,
            Qt.KeyboardModifier.ControlModifier,
        )

        assert confirm.property("visible") is True, (
            "a nézőben a Ctrl+Delete-nek törlést kellene kérdeznie — "
            "ez volt a #1418 tényleges hiánya"
        )
        vart = Path(controller.watchedFolders[0]) / "a.jpg"
        # `Path`-ként hasonlítunk: a felület `/`-t fűz, a Windows `\`-t
        # várna — a kettő ugyanaz a fájl, a nyers szövegegyezés nem az
        assert [Path(p) for p in _lista(confirm.property("paths"))] == [vart]

    def test_kijeloletlen_kepnel_a_ctrl_delete_nem_csinal_semmit(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        viewer = self._nezo(window, qt_app)
        viewer.setProperty("currentIndex", -1)
        qt_app.processEvents()
        confirm = _gyerek(window, "deleteConfirmDialog")

        _billentyu(
            window, qt_app, Qt.Key.Key_Delete,
            Qt.KeyboardModifier.ControlModifier,
        )

        assert confirm.property("visible") is False


class TestANezobenAPusztaDeleteNemTorol:
    """A nézőben (jobbklikk-menüs felület) CSAK a `Ctrl+Delete` töröl.

    A #1154 mérése szerint a `0x9c9a` parancs felület szerint válik szét:
    menüsávban puszta `Delete`, helyi menükben `Ctrl+Delete`. A néző az
    utóbbi családba tartozik.

    ⚠️ Ez **ellenkező irányú őr**: nem azt állítja, hogy a helyes billentyű
    működik (arra külön teszt van), hanem hogy a HELYTELEN **nem** — a
    korábbi `Delete`-kötés (a #422 azóta felülírt feltevése) így nem tud
    csendben visszatérni. A törlés visszafordíthatatlan, ezért kell mindkét
    irány."""

    def test_a_puszta_delete_nem_torol_a_nezoben(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        window.setProperty("viewerOpen", True)
        viewer = _gyerek(window, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        _fokusz(viewer, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")

        _billentyu(window, qt_app, Qt.Key.Key_Delete)

        assert confirm.property("visible") is False, (
            "a nézőben a puszta Delete törölni akart — a #422-es, felülírt "
            "kötés tért vissza (a helyes itt: Ctrl+Delete)"
        )
