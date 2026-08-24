"""A Shift+nyíl EGYESÉVEL bővít, és a kiindulópont is lép (#892, #1222).

## Az eltérés, amit ez a fájl mér

| | eredeti Picasa | PicasaPy a javítás előtt |
|---|---|---|
| Shift+nyíl | egyesével bővít, a léptetés töve is lép | horgony↔cél TARTOMÁNY, újraszámolva |

A kettő a leggyakoribb esetben (egy irányba bővítek) ugyanazt adja — a
különbség **irányváltáskor** látszik: a tartomány zsugorodik, az eredeti
viszont nem zsugorít, hanem a másik irányba bővít tovább.

## Az eredeti — bizonyíték

A léptető mag `0x00717eb0` (két argumentum: irány, „cseréld a kijelölést").
A két hívója (`0x00717260` / `0x007172a0`) a második argumentumot a
Shift állapotából **negálva** adja (`0x0071728c` `sete al`): cserélj =
NINCS Shift. A magban:

- `0x00718029`: a horgony (`[this+0x390]`) indexe + irány;
- `0x00718031`: ha túlfut → határkezelés (`0x00717d10`), nem fordul át;
- `0x0071805c`: **Shift esetén a leszedő ág KIMARAD** — a régiek maradnak;
- `0x007180d6`: az új elem kijelölődik (`[elem+0x5d] = 1`);
- `0x007180da`: a horgony a friss elemre íródik — **a tő is lép**.

Nincs tehát „tartomány", csak halmozás. Teljes levezetés:
`docs/specs/picasa-eger-es-kijeloles.md` 4/c.

⚠️ **EGÉRREL** a Shift továbbra is TARTOMÁNYT jelöl a horgonytól
(`0x0071bb34`) — az a #897 útvonala, azt ez a fájl nem érinti.

## Miért VALÓDI billentyűesemény

A #1200 és a #1148 is azért maradt zöld egy használhatatlan funkció
fölött, mert a teszt a kezelőfüggvényt hívta közvetlenül. A kattintás
időbélyege és a láthatóra görgetés is kötelező (a #1219 mérése): enélkül
a szintetikus lenyomásból dupla kattintás lesz, vagy a cella kicsúszik az
ablakból — a teszt pedig **némán zöld marad**.
"""

from pathlib import Path

from PySide6.QtCore import Q_ARG, QEvent, QMetaObject, QObject, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPointingDevice

from support.jpeg_factory import make_jpeg

#: a szintetikus események időbélyege — enélkül a Qt dupla kattintást lát
_ORA = [1000]

#: a mérőmappa képszáma — elég hosszú ahhoz, hogy az irányváltás UTÁN is
#: maradjon hely a másik irányba bővítésre
DARAB = 6


def _bejar(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _bejar(gyerek)


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _feed(qml_app, qt_app):
    """`DARAB` kép az „adag” mappában; a csoport ELSŐ sorindexét is adja."""
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    (lib / "adag").mkdir(exist_ok=True)
    for i in range(DARAB):
        make_jpeg(lib / "adag" / f"k{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    csoport = next(
        (cs for cs in controller.feedGroups if cs["name"] == "adag"), None
    )
    assert csoport is not None, "az „adag” csoport nem jött létre"
    assert int(csoport["count"]) == DARAB
    return window, controller, int(csoport["start"])


def _grid(window):
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None, "a photoGrid nem található"
    return grid


def _kijelolt(window) -> list[int]:
    """A `selectedIndexes` PYTHON-listaként — a QML `QJSValue`-t ad."""
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return sorted(int(i) for i in (ertek or []))


def _indexkep(window, sor):
    for elem in _bejar(window.contentItem()):
        if elem.objectName() == "thumbMouseArea":
            cella = elem.parentItem()
            if cella is not None and cella.property("index") == sor:
                return elem
    return None


def _kozeppont(window, sor):
    terulet = _indexkep(window, sor)
    assert terulet is not None, f"a(z) {sor}. sor indexképe nem található"
    return terulet.mapToScene(
        QPointF(terulet.width() / 2, terulet.height() / 2)
    )


def _gorgesd_lathatora(window, qt_app, sor):
    """A sor indexképének középpontja, láthatóra görgetve és megállapodva.

    ⚠️ A `scrollToRow` a `contentY`-t nem vágja a görgethető tartományra,
    ezért minden mérés előtt visszaigazítjuk a nézetet a határaira (#897
    mérése) — a szintetikus lenyomás így ugyanazt látja, mint a mérés."""
    grid = _grid(window)

    def _belul(pont):
        return (
            8 <= pont.y() <= window.height() - 8
            and 8 <= pont.x() <= window.width() - 8
        )

    elozo = None
    for kor in range(40):
        QMetaObject.invokeMethod(
            grid, "returnToBounds", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        kozep = _kozeppont(window, sor)
        if _belul(kozep) and elozo is not None and abs(kozep.y() - elozo) < 0.5:
            return kozep
        elozo = kozep.y()
        if kor % 8 == 0:
            QMetaObject.invokeMethod(
                grid, "scrollToRow", Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", sor),
            )
        qt_app.processEvents()
    raise AssertionError(f"a(z) {sor}. sor indexképe nem görgethető láthatóra")


def _kattints(window, qt_app, sor, mods=Qt.KeyboardModifier.NoModifier):
    """VALÓDI egéresemény az indexképre — nem a `handleThumbClick` hívása."""
    kozep = _gorgesd_lathatora(window, qt_app, sor)
    for tipus, gombok in (
        (QEvent.Type.MouseButtonPress, Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseButtonRelease, Qt.MouseButton.NoButton),
    ):
        _ORA[0] += 1000
        esemeny = QMouseEvent(
            tipus, kozep, kozep, Qt.MouseButton.LeftButton, gombok, mods,
            QPointingDevice.primaryPointingDevice(),
        )
        esemeny.setTimestamp(_ORA[0])
        qt_app.sendEvent(window, esemeny)
    qt_app.processEvents()
    assert not window.property("viewerOpen"), (
        "a szintetikus kattintásból dupla kattintás lett (néző nyílt meg)"
    )


def _nyil(window, qt_app, kulcs, mods=Qt.KeyboardModifier.ShiftModifier):
    """VALÓDI billentyűesemény a rácsra — nem az `extendSelection` hívása."""
    grid = _grid(window)
    grid.setProperty("focus", True)
    QMetaObject.invokeMethod(
        grid, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    qt_app.sendEvent(window, QKeyEvent(QEvent.Type.KeyPress, kulcs, mods))
    qt_app.processEvents()


def _kurzor(window) -> int:
    return int(window.property("selectedIndex"))


class TestEgyesevelBovit:
    """`0x0071805c`: Shift esetén a leszedő ág kimarad — a régiek maradnak."""

    def test_ket_lepes_utan_harom_kijelolt(self, qml_app, qt_app):
        """A #892 nevesített tesztje: 1. képre kattintás → Shift+jobb ×2 →
        az 1., 2. és 3. kép MIND kijelölt (nem csak az 1. és a 3.)."""
        window, _controller, start = _feed(qml_app, qt_app)

        _kattints(window, qt_app, start)
        _nyil(window, qt_app, Qt.Key.Key_Right)
        _nyil(window, qt_app, Qt.Key.Key_Right)

        assert _kijelolt(window) == [start, start + 1, start + 2]
        assert _kurzor(window) == start + 2

    def test_a_lepes_tove_a_friss_elem(self, qml_app, qt_app):
        """`0x007180da`: minden lépés a LEGUTÓBB kijelölt elemtől indul —
        ezért halad a kurzor egyesével, nem ugrik vissza a kiindulóra."""
        window, _controller, start = _feed(qml_app, qt_app)

        _kattints(window, qt_app, start + 1)
        for lepes in range(1, 4):
            _nyil(window, qt_app, Qt.Key.Key_Right)
            assert _kurzor(window) == start + 1 + lepes


class TestIranyvaltas:
    """A TÉNYLEGES különbség a régi (Intéző-féle) viselkedéshez képest.

    E nélkül a két őr nélkül a fájl a RÉGI kódra is zöld lenne: a
    tartomány-kijelölés is „bővít", amíg egy irányba megyünk."""

    def test_a_visszafele_lepes_nem_zsugorit(self, qml_app, qt_app):
        """⚠️ A jegy magja. A tartomány-szemantika itt visszavette volna a
        3. képet; az eredeti csak visszasétál a már kijelölteken."""
        window, _controller, start = _feed(qml_app, qt_app)

        _kattints(window, qt_app, start + 2)
        _nyil(window, qt_app, Qt.Key.Key_Right)
        _nyil(window, qt_app, Qt.Key.Key_Left)

        assert _kijelolt(window) == [start + 2, start + 3], (
            "az irányváltás ZSUGORÍTOTT — ez a régi, Intéző-féle tartomány"
        )
        assert _kurzor(window) == start + 2

    def test_az_iranyvaltas_a_masik_iranyba_bovit(self, qml_app, qt_app):
        """A már kijelölteken visszasétálva a léptetés TOVÁBB bővít."""
        window, _controller, start = _feed(qml_app, qt_app)

        _kattints(window, qt_app, start + 2)
        _nyil(window, qt_app, Qt.Key.Key_Right)   # + start+3
        _nyil(window, qt_app, Qt.Key.Key_Left)    # vissza start+2-re
        _nyil(window, qt_app, Qt.Key.Key_Left)    # + start+1

        assert _kijelolt(window) == [start + 1, start + 2, start + 3], (
            "az irányváltás után nem bővített a másik irányba"
        )
        assert _kurzor(window) == start + 1


class TestMappahatar:
    """MEGŐRZŐ őr (#1219): a bővítés a mappacsoportban marad."""

    def test_a_csoport_vegen_megall(self, qml_app, qt_app):
        window, _controller, start = _feed(qml_app, qt_app)
        utolso = start + DARAB - 1

        _kattints(window, qt_app, utolso)
        _nyil(window, qt_app, Qt.Key.Key_Right)

        assert _kijelolt(window) == [utolso], (
            "a Shift+jobb átlépett a szomszéd mappába"
        )
        assert _kurzor(window) == utolso

    def test_a_csoport_elejen_megall(self, qml_app, qt_app):
        window, _controller, start = _feed(qml_app, qt_app)

        _kattints(window, qt_app, start)
        _nyil(window, qt_app, Qt.Key.Key_Left)

        assert _kijelolt(window) == [start]
        assert _kurzor(window) == start


class TestHorgonyKetSzerepe:
    """A horgony két szerepét nálunk két mező viszi (spec 15.6).

    Az eredetiben a `[this+0x390]` a nyilas léptetés töve ÉS a
    Shift-KATTINTÁS tartományának töve; a nyíl lépteti, a kattintás nem.
    Nálunk a léptetésé a kurzor (lép), a kattintásé a `selectionAnchor`
    (marad, #897). A LÁTHATÓ eredmény ugyanaz, mert az eredeti
    tartomány-magja (`0x00716ae0`) csak KIJELÖL — a tartományon kívül már
    kijelölteket nem szedi le. Ez az őr azt a végeredményt rögzíti."""

    def test_a_nyilas_bovites_utani_shift_kattintas_mindent_megtart(
        self, qml_app, qt_app
    ):
        window, _controller, start = _feed(qml_app, qt_app)
        grid = _grid(window)

        _kattints(window, qt_app, start)
        _nyil(window, qt_app, Qt.Key.Key_Right)
        _nyil(window, qt_app, Qt.Key.Key_Right)
        _kattints(
            window, qt_app, start + 4, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == [start + k for k in range(5)], (
            "a nyíllal megkezdett kijelölés eleje leesett a Shift-kattintáskor"
        )
        assert int(grid.property("selectionAnchor")) == start, (
            "a Shift+nyíl elmozdította a KATTINTÁS horgonyát (#897)"
        )
