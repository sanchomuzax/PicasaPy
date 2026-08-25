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
    """`darab` kép a „sok" mappában — ismételten hívható, a hiányzókat
    pótolja (az oszlopszám ismeretében pontos képszám kell)."""
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
    def _ures_pont(window, horgony):
        """Egy pont a képfolyamon BELÜL, de cellán KÍVÜL — MÉRÉSSEL.

        Nem geometriai feltevésből számoljuk (az oszlopszám a futtató
        ablakméretétől függ — a CI-n más, mint itt), hanem végigpásztázzuk
        a lasszó saját `MouseArea`-jának téglalapját, és az első olyan,
        ablakon belüli pontot adjuk vissza, amit egyetlen cella sem takar."""
        # ⚠️ A feedben TÖBB csoport van, mindegyiknek saját lasszó-területe.
        # Azt kell választani, amelyik a CÉLKÉPET tartalmazza — különben a
        # húzás két csoport között menne, és a keret a másik csoport
        # tartományára számolna (a lasszó csoporton belüli, #1219).
        terulet = None
        for elem in _bejar(window.contentItem()):
            if elem.objectName() != "feedFlowLasso":
                continue
            bal_felso = elem.mapToScene(QPointF(0, 0))
            if (bal_felso.x() <= horgony.x() <= bal_felso.x() + elem.width()
                    and bal_felso.y() <= horgony.y()
                    <= bal_felso.y() + elem.height()):
                terulet = elem
                break
        if terulet is None:
            return None
        cellak = [
            e.parentItem()
            for e in _bejar(window.contentItem())
            if e.objectName() == "thumbMouseArea" and e.parentItem() is not None
        ]
        # ⚠️ A GÖRGETŐSÁV is elnyeli az egérlenyomást, pedig „cellával nem
        # takart" pont. Ha a keresés oda esik, a húzás el sem indul, és a
        # bukás úgy néz ki, mintha a lasszó lenne hibás. A #587 (bal panel
        # 230 → 240) épp ilyen ponthoz sodorta a keresést: x = 1252 egy
        # 1280 széles ablakban. Ezért a sávot ugyanúgy kizárjuk, mint a
        # cellákat — MÉRÉSSEL, nem szélső margóval.
        kizart = list(cellak)
        kizart += [
            e for e in _bejar(window.contentItem())
            if e.objectName() == "feedScrollBar"
        ]
        keretek = []
        for cella in kizart:
            sarok = cella.mapToScene(QPointF(0, 0))
            keretek.append(
                (sarok.x(), sarok.y(),
                 sarok.x() + cella.width(), sarok.y() + cella.height())
            )
        lepes = 10
        y = lepes
        while y < terulet.height():
            x = lepes
            while x < terulet.width():
                pont = terulet.mapToScene(QPointF(x, y))
                if (0 <= pont.x() <= window.width()
                        and 0 <= pont.y() <= window.height()
                        and not any(
                            bx <= pont.x() <= jx and by <= pont.y() <= jy
                            for bx, by, jx, jy in keretek
                        )):
                    return pont
                x += lepes
            y += lepes
        return None

    def test_ures_reszrol_indulva_kijelol(self, qml_app, qt_app):
        """⚠️ A jegy magja: telített rácson eddig sehonnan nem indult
        lasszó — kijelölt képről fogd-és-vidd lesz (#455, ez helyes), üres
        területen viszont NEM VOLT kezelő.

        ⚠️ A csoport képszámát az OSZLOPSZÁMBÓL állítjuk be: ha a sor
        pontosan tele van, a képfolyamban EGYÁLTALÁN nincs üres pont, és a
        teszt a saját feltevésén bukna el, nem a terméken. (A CI ablaka
        keskenyebb, ott ez elő is jött.)"""
        window, controller = _feed(qml_app, qt_app, darab=3)
        oszlopok = int(_grid(window).property("columns") or 1)
        if oszlopok < 2:
            import pytest

            pytest.skip("egyoszlopos rács: nincs üres hely a folyamban")
        _feed(qml_app, qt_app, darab=oszlopok + 1)
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()
        grid = _grid(window)

        # ⚠️ Az újraolvasás után a feed elmozdulhat — a célt előbb
        # láthatóra görgetjük, és megvárjuk, amíg megáll (a #1219
        # tanulsága: a görgetés közbeni köztes állapot félrevisz).
        QMetaObject.invokeMethod(
            grid, "scrollToRow", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        elozo = None
        for _ in range(40):
            qt_app.processEvents()
            cel = self._cella(window, 0)
            if cel is None:
                continue
            kozep = cel.mapToScene(QPointF(cel.width() / 2, cel.height() / 2))
            if (elozo is not None and abs(kozep.y() - elozo) < 0.5
                    and 8 <= kozep.y() <= window.height() - 8):
                break
            elozo = kozep.y()
        cel = self._cella(window, 0)
        assert cel is not None
        kozep = cel.mapToScene(QPointF(cel.width() / 2, cel.height() / 2))
        assert 0 <= kozep.y() <= window.height(), "a célkép nem látszik"
        ures = self._ures_pont(window, kozep)
        assert ures is not None, "nem található cellával nem takart pont a folyamon"

        self._huzas(window, qt_app, ures, kozep)

        assert 0 in _kijelolt(window), (
            "az üres területről indított húzás nem jelölte ki a keretbe "
            f"eső képet: {_kijelolt(window)}"
        )
