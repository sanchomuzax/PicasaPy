"""A lasszó: üres területről indul, metszést mér, és ismeri a Shiftet (#1148).

## Az eredeti — bizonyíték

`docs/specs/picasa-eger-es-kijeloles.md` 4/e és #897:

- a lasszó **üres területre** való lenyomásra indul (`0x00719d4b`), és
  induláskor **pillanatfelvételt** ment minden elem kijelöltségéről
  (`[elem+0x5c]`, `0x00719d80`–`0x00719d94`);
- a már kijelölt elemre módosító nélkül lenyomva a kijelölés **nem
  szűkül** (`0x00719d22`) — ez teszi lehetővé a többelemű kijelölés
  együttes húzását (nálunk: #455 fogd-és-vidd);
- az elemenkénti teszt **metszés**, nem tartalmazás, **szigorúan
  pozitív** metszet-területtel (`0x0071bc90`,
  `0x0071bef7`–`0x0071bf25`);
- a hatókör a jelenlegi mappa csomópontja — a lasszó **nem lép át**
  mappahatárt (#1145, #1219).

## Amit ez a fájl mér

A geometriát (metszés) és a módosítókat közvetlen hívással — ott a
számítás a tárgy —, a HÚZÁST viszont **valódi egéreseménnyel**: a #1148
épp azt jelentette, hogy a lasszó telített rácson nem indul el.
"""

from pathlib import Path

from PySide6.QtCore import (
    Q_ARG,
    QEvent,
    QMetaObject,
    QObject,
    QPointF,
    Qt,
)
from PySide6.QtGui import QMouseEvent, QPointingDevice

from support.jpeg_factory import make_jpeg

_ORA = [1000]


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


def _feed(qml_app, qt_app, darab=6):
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    (lib / "sok").mkdir(exist_ok=True)
    for i in range(darab):
        make_jpeg(lib / "sok" / f"k{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    return window, controller


def _grid(window):
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None
    return grid


def _kijelolt(window):
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return sorted(int(i) for i in (ertek or []))


def _lasszo_indexek(grid, start, count, flow_w, x1, y1, x2, y2):
    from PySide6.QtCore import Q_RETURN_ARG

    eredmeny = QMetaObject.invokeMethod(
        grid, "lassoIndexes", Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG("QVariant"),
        Q_ARG("QVariant", start), Q_ARG("QVariant", count),
        Q_ARG("QVariant", flow_w),
        Q_ARG("QVariant", float(x1)), Q_ARG("QVariant", float(y1)),
        Q_ARG("QVariant", float(x2)), Q_ARG("QVariant", float(y2)),
    )
    if hasattr(eredmeny, "toVariant"):
        eredmeny = eredmeny.toVariant()
    return sorted(int(i) for i in (eredmeny or []))


class TestMetszes:
    """`0x0071bc90`: az elemteszt METSZÉS, szigorúan pozitív területtel."""

    def test_a_keretet_epphogy_atfedo_kep_bekerul(self, qml_app, qt_app):
        window, _controller = _feed(qml_app, qt_app)
        grid = _grid(window)
        cw = float(grid.property("cellWidth"))
        ch = float(grid.property("cellHeight"))

        # a keret átlóg a MÁSODIK cellába egy képpontnyit
        talalat = _lasszo_indexek(grid, 0, 6, cw * 3, 1, 1, cw + 1, ch / 2)

        assert 0 in talalat and 1 in talalat

    def test_a_nulla_teruletu_erintes_nem_szamit(self, qml_app, qt_app):
        """A cellahatárra pontosan illeszkedő keret a SZOMSZÉDOT nem
        fogja be — a metszet területe nulla."""
        window, _controller = _feed(qml_app, qt_app)
        grid = _grid(window)
        cw = float(grid.property("cellWidth"))
        ch = float(grid.property("cellHeight"))

        talalat = _lasszo_indexek(grid, 0, 6, cw * 3, 1, 1, cw, ch / 2)

        assert talalat == [0], f"a szomszéd cella is bekerült: {talalat}"

    def test_a_csoporton_kivulre_nem_lep(self, qml_app, qt_app):
        """#1219: a hatókör a mappacsoport — a `count`-on túl nincs sor."""
        window, _controller = _feed(qml_app, qt_app)
        grid = _grid(window)
        cw = float(grid.property("cellWidth"))
        ch = float(grid.property("cellHeight"))

        talalat = _lasszo_indexek(grid, 0, 3, cw * 3, 0, 0, cw * 3, ch * 5)

        assert max(talalat) <= 2


class TestModositok:
    """Shift = hozzáfűz, Ctrl = a PILLANATFELVÉTELHEZ képest vált (#897)."""

    @staticmethod
    def _alkalmaz(qt_app, grid, start, count, flow_w, x1, y1, x2, y2, mods=0):
        QMetaObject.invokeMethod(
            grid, "applyLasso", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", start), Q_ARG("QVariant", count),
            Q_ARG("QVariant", flow_w),
            Q_ARG("QVariant", float(x1)), Q_ARG("QVariant", float(y1)),
            Q_ARG("QVariant", float(x2)), Q_ARG("QVariant", float(y2)),
            Q_ARG("QVariant", int(mods)),
        )
        qt_app.processEvents()

    @staticmethod
    def _pillanatfelvetel(qt_app, grid):
        QMetaObject.invokeMethod(
            grid, "beginLasso", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

    def test_shift_hozzafuz(self, qml_app, qt_app):
        window, _controller = _feed(qml_app, qt_app)
        grid = _grid(window)
        cw = float(grid.property("cellWidth"))
        ch = float(grid.property("cellHeight"))
        window.setProperty("selectedIndexes", [4])
        window.setProperty("selectedIndex", 4)
        qt_app.processEvents()
        self._pillanatfelvetel(qt_app, grid)

        self._alkalmaz(
            qt_app, grid, 0, 6, cw * 3, 1, 1, cw + 1, ch / 2,
            int(Qt.KeyboardModifier.ShiftModifier.value),
        )

        assert _kijelolt(window) == [0, 1, 4]

    def test_ctrl_a_pillanatfelvetelhez_kepest_valt(self, qml_app, qt_app):
        """Húzás közben visszafelé is módosít: a keretbe eső elemek a
        felvételkori állapotukhoz képest fordulnak."""
        window, _controller = _feed(qml_app, qt_app)
        grid = _grid(window)
        cw = float(grid.property("cellWidth"))
        ch = float(grid.property("cellHeight"))
        window.setProperty("selectedIndexes", [0, 4])
        window.setProperty("selectedIndex", 4)
        qt_app.processEvents()
        self._pillanatfelvetel(qt_app, grid)

        # a keret a 0. és az 1. cellát fogja: a 0 KIESIK (volt), az 1 BEKERÜL
        self._alkalmaz(
            qt_app, grid, 0, 6, cw * 3, 1, 1, cw + 1, ch / 2,
            int(Qt.KeyboardModifier.ControlModifier.value),
        )

        assert _kijelolt(window) == [1, 4]

    def test_modosito_nelkul_lecsereli(self, qml_app, qt_app):
        window, _controller = _feed(qml_app, qt_app)
        grid = _grid(window)
        cw = float(grid.property("cellWidth"))
        ch = float(grid.property("cellHeight"))
        window.setProperty("selectedIndexes", [4])
        qt_app.processEvents()
        self._pillanatfelvetel(qt_app, grid)

        self._alkalmaz(qt_app, grid, 0, 6, cw * 3, 1, 1, cw + 1, ch / 2)

        assert _kijelolt(window) == [0, 1]


class TestUresTerulet:
    """A lasszó VALÓDI húzásból, a képfolyam üres részéről indulva."""

    @staticmethod
    def _huzas(window, qt_app, kezdet: QPointF, veg: QPointF):
        eszkoz = QPointingDevice.primaryPointingDevice()
        lepesek = [
            (QEvent.Type.MouseButtonPress, kezdet,
             Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton),
            (QEvent.Type.MouseMove, QPointF((kezdet.x() + veg.x()) / 2,
                                            (kezdet.y() + veg.y()) / 2),
             Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton),
            (QEvent.Type.MouseMove, veg,
             Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton),
            (QEvent.Type.MouseButtonRelease, veg,
             Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton),
        ]
        for tipus, pont, gomb, gombok in lepesek:
            _ORA[0] += 200
            esemeny = QMouseEvent(
                tipus, pont, pont, gomb, gombok,
                Qt.KeyboardModifier.NoModifier, eszkoz,
            )
            esemeny.setTimestamp(_ORA[0])
            qt_app.sendEvent(window, esemeny)
            qt_app.processEvents()

    def _cella(self, window, sor):
        for elem in _bejar(window.contentItem()):
            if elem.objectName() == "thumbMouseArea":
                cella = elem.parentItem()
                if cella is not None and cella.property("index") == sor:
                    return elem
        return None

    @staticmethod
    def _ures_pont(window, grid):
        """Egy pont a képfolyamon BELÜL, de cellán KÍVÜL.

        Nem geometriai feltevésből számoljuk (az oszlopszám a futtató
        ablakméretétől függ — a CI-n más, mint itt), hanem méréssel: a
        lasszó saját `MouseArea`-jának téglalapját pásztázzuk, és az első
        olyan pontot adjuk vissza, amit egyetlen cella sem takar."""
        terulet = None
        for elem in _bejar(window.contentItem()):
            if elem.objectName() == "feedFlowLasso":
                terulet = elem
                break
        if terulet is None:
            return None
        cellak = [
            e.parentItem()
            for e in _bejar(window.contentItem())
            if e.objectName() == "thumbMouseArea" and e.parentItem() is not None
        ]
        lepes = 12
        y = terulet.height() / 2
        x = terulet.width() - lepes
        while x > 0:
            pont = terulet.mapToScene(QPointF(x, y))
            if not (0 <= pont.x() <= window.width()
                    and 0 <= pont.y() <= window.height()):
                x -= lepes
                continue
            takart = False
            for cella in cellak:
                sarok = cella.mapToScene(QPointF(0, 0))
                if (sarok.x() <= pont.x() <= sarok.x() + cella.width()
                        and sarok.y() <= pont.y() <= sarok.y() + cella.height()):
                    takart = True
                    break
            if not takart:
                return pont
            x -= lepes
        return None

    def test_ures_reszrol_indulva_kijelol(self, qml_app, qt_app):
        """⚠️ A jegy magja: telített rácson eddig sehonnan nem indult
        lasszó — kijelölt képről fogd-és-vidd lesz (#455, ez helyes), üres
        területen viszont NEM VOLT kezelő."""
        window, _controller = _feed(qml_app, qt_app, darab=3)
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()
        grid = _grid(window)

        ures = self._ures_pont(window, grid)
        assert ures is not None, "nem található cellával nem takart pont a folyamon"
        cel = self._cella(window, 0)
        assert cel is not None
        kozep = cel.mapToScene(QPointF(cel.width() / 2, cel.height() / 2))

        self._huzas(window, qt_app, ures, kozep)

        assert 0 in _kijelolt(window), (
            "az üres területről indított húzás nem jelölte ki a keretbe "
            f"eső képet: {_kijelolt(window)}"
        )
