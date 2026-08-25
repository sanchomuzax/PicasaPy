"""A rács kattintás- és lasszó-modellje: pillanatfelvétel, horgony, téglalap (#897).

## Az eredeti — bizonyíték

A #897 mind a négy eseményágat utasításszinten visszafejtette
(`0x00719c37` lenyomás, `0x00719ece` húzás, `0x00719df0` felengedés,
`0x0071bae0` kijelölés-átállító):

- a lasszó **indulásakor** a program minden elem kijelöltségét elmenti
  (`[elem+0x5c]`, `0x00719d80`–`0x00719d94`), és a húzás alatt **ehhez**
  viszonyít — ezért nem „villog" a kijelölés húzás közben, és ezért tud a
  Ctrl-lel húzott keret **vissza is venni**, ha visszahúzzák;
- **egérrel a Shift TARTOMÁNYT jelöl** a horgonytól (`[edi+0x390]`,
  `0x0071bb34`) a kattintott elemig — billentyűzettel viszont egyesével
  bővít és a horgonyt is lépteti (#892/#96); a két útvonal szándékosan
  külön kódban van;
- a keret téglalapja **normalizált**, és ha a két koordináta egyenlő,
  a program **+1**-et ad hozzá (`0x00719fd6`–`0x0071a012`) — a téglalap
  soha nem nulla méretű;
- már kijelölt elemre módosító nélkül **lenyomva** a kijelölés nem szűkül
  (`0x00719d22`), a szűkítés csak **felengedéskor** és csak húzás nélkül
  történik (`0x00719e1f`).

## Amit ez a fájl mér

A geometriát és a pillanatfelvétel-összefésülést közvetlen hívással (ott
a SZÁMÍTÁS a tárgy), a kattintás- és húzás-útvonalakat viszont **valódi
egér- és billentyűeseménnyel** — a #1148 és a #1200 is azért maradt zöld
egy használhatatlan funkció fölött, mert a teszt a kezelőfüggvényt hívta
közvetlenül.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QEvent,
    QMetaObject,
    QObject,
    QPointF,
    Qt,
)
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPointingDevice

from support.jpeg_factory import make_jpeg
from support.qml_focus import fokuszt_ad

#: a szintetikus események időbélyege — enélkül a Qt dupla kattintást lát
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
    """`darab` kép a „sok” mappában; visszaadja a csoport ELSŐ sorindexét is."""
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    (lib / "sok").mkdir(exist_ok=True)
    for i in range(darab):
        make_jpeg(lib / "sok" / f"k{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    csoport = next(
        (cs for cs in controller.feedGroups if cs["name"] == "sok"), None
    )
    assert csoport is not None, "a „sok” csoport nem jött létre"
    assert int(csoport["count"]) == darab
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
    """A sor indexképének középpontja JELENET-koordinátában (görgetés nélkül)."""
    terulet = _indexkep(window, sor)
    assert terulet is not None, f"a(z) {sor}. sor indexképe nem található"
    return terulet.mapToScene(
        QPointF(terulet.width() / 2, terulet.height() / 2)
    )


def _gorgesd_lathatora(window, qt_app, sor):
    """A sor indexképének KÖZÉPPONTJA ablak-koordinátában, láthatóra görgetve.

    ⚠️ A feed a kattintás után a kijelölt sorhoz igazít, ezért a következő
    cél könnyen kicsúszik az ablakból; margó nélkül a kattintás a szomszéd
    cellára esne (a #1219 tanulsága).

    (A #1335-ig itt egy `returnToBounds`-os megkerülés is állt: a
    `scrollToRow` nem vágta a `contentY`-t a görgethető tartományra, ezért
    a nézet érvénytelen helyre került, és a Flickable csak a KÖVETKEZŐ
    egérlenyomásra rántotta vissza. A #1335 a vágást a `LightboxFeed`-be
    tette — a megkerülés fölöslegessé vált, az őre a
    `test_scrolltorow_vagas_1335.py`.)"""
    grid = _grid(window)

    def _belul(pont):
        return (
            8 <= pont.y() <= window.height() - 8
            and 8 <= pont.x() <= window.width() - 8
        )

    elozo = None
    for kor in range(40):
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


def _egeresemeny(window, qt_app, tipus, pont, gomb, gombok, mods):
    _ORA[0] += 1000
    esemeny = QMouseEvent(
        tipus, pont, pont, gomb, gombok, mods,
        QPointingDevice.primaryPointingDevice(),
    )
    esemeny.setTimestamp(_ORA[0])
    qt_app.sendEvent(window, esemeny)
    qt_app.processEvents()


def _kattints(window, qt_app, sor, mods=Qt.KeyboardModifier.NoModifier):
    """VALÓDI egéresemény az indexképre — nem a `handleThumbClick` hívása."""
    kozep = _gorgesd_lathatora(window, qt_app, sor)
    _egeresemeny(
        window, qt_app, QEvent.Type.MouseButtonPress, kozep,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, mods,
    )
    _egeresemeny(
        window, qt_app, QEvent.Type.MouseButtonRelease, kozep,
        Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, mods,
    )
    assert not window.property("viewerOpen"), (
        "a szintetikus kattintásból dupla kattintás lett (néző nyílt meg)"
    )


def _nyil_shifttel(window, qt_app, kulcs):
    """VALÓDI billentyűesemény a rácsra — nem az `extendSelection` hívása."""
    fokuszt_ad(_grid(window), qt_app)
    qt_app.sendEvent(
        window,
        QKeyEvent(QEvent.Type.KeyPress, kulcs, Qt.KeyboardModifier.ShiftModifier),
    )
    qt_app.processEvents()


def _lasszo_indexek(grid, start, count, flow_w, x1, y1, x2, y2):
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


class TestHorgony:
    """`0x0071bb34`: EGÉRREL a Shift a HORGONYTÓL jelöl tartományt."""

    def test_a_shift_kattintas_a_horgonytol_jelol(self, qml_app, qt_app):
        """⚠️ A jegy magja.

        A horgonyt egy sima kattintás teszi le, a KURZORT viszont a
        Shift+nyíl elmozdítja róla. Az eredeti a horgonytól méri a
        tartományt (`[edi+0x390]`), nálunk a kurzortól ment — ezért a
        Shift+nyíllal már megkezdett kijelölés eleje leesett."""
        window, _controller, start = _feed(qml_app, qt_app)

        _kattints(window, qt_app, start + 1)          # horgony := start+1
        _nyil_shifttel(window, qt_app, Qt.Key.Key_Right)  # kurzor → start+2
        _kattints(
            window, qt_app, start + 4, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == [start + k for k in (1, 2, 3, 4)], (
            "a Shift+kattintás nem a horgonytól mérte a tartományt"
        )

    def test_az_otodikre_shift_kattintva_mind_az_ot_kijelolt(
        self, qml_app, qt_app
    ):
        """A jegy nevesített tesztje: az 1. képre kattintás, majd
        Shift-kattintás az 5.-re → mind az 5 kijelölt."""
        window, _controller, start = _feed(qml_app, qt_app)

        _kattints(window, qt_app, start)
        _kattints(
            window, qt_app, start + 4, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == [start + k for k in range(5)]

    def test_a_shift_kattintas_nem_lepteti_a_horgonyt(self, qml_app, qt_app):
        """A horgony a Shift-kattintás UTÁN is a kiindulóponton áll —
        különben a következő Shift-gesztus más tartományt adna."""
        window, _controller, start = _feed(qml_app, qt_app)
        grid = _grid(window)

        _kattints(window, qt_app, start + 1)
        _kattints(
            window, qt_app, start + 4, Qt.KeyboardModifier.ShiftModifier
        )

        assert int(grid.property("selectionAnchor")) == start + 1

    def test_horgony_nelkul_a_kattintott_kepre_szukit(self, qml_app, qt_app):
        """Dokumentált alapértelmezés: horgony híján a Shift-kattintás
        úgy viselkedik, mint a sima kattintás (és leteszi a horgonyt)."""
        window, _controller, start = _feed(qml_app, qt_app)
        grid = _grid(window)
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        grid.setProperty("selectionAnchor", -1)
        qt_app.processEvents()

        _kattints(
            window, qt_app, start + 3, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == [start + 3]
        assert int(grid.property("selectionAnchor")) == start + 3


class TestTeglalap:
    """`0x00719fd6`–`0x0071a012`: a keret normalizált és SOHA nem nulla méretű.

    A képfolyam szélességét a NÉVLEGES cellaméret háromszorosára állítjuk:
    így az oszlopszám biztosan 3, az osztás pedig maradék nélküli, tehát a
    `pitch` pontosan a névleges cellaszélesség. (A `cellWidth` a futtató
    ablakméretétől függ — abból nem jönne ki determinisztikus rács.)"""

    @staticmethod
    def _racs(window):
        grid = _grid(window)
        pitch = int(grid.property("nominalCellWidth"))
        return grid, pitch, float(grid.property("cellHeight"))

    def test_az_oszlophataron_futo_fuggoleges_huzas_kijelol(
        self, qml_app, qt_app
    ):
        """Pontosan az oszlophatáron végighúzott (nulla SZÉLES) keret: a
        +1 nélkül egyetlen cellát sem fog be — se balra, se jobbra."""
        window, _controller, _start = _feed(qml_app, qt_app)
        grid, pitch, ch = self._racs(window)

        talalat = _lasszo_indexek(
            grid, 0, 6, pitch * 3, pitch, ch * 0.25, pitch, ch * 0.75
        )

        assert talalat == [1], f"az oszlophatáron futó húzás eredménye: {talalat}"

    def test_a_sorhataron_futo_vizszintes_huzas_kijelol(self, qml_app, qt_app):
        """Pontosan a sorhatáron végighúzott (nulla MAGAS) keret."""
        window, _controller, _start = _feed(qml_app, qt_app)
        grid, pitch, ch = self._racs(window)

        talalat = _lasszo_indexek(
            grid, 0, 6, pitch * 3, pitch * 0.25, ch, pitch * 1.75, ch
        )

        assert talalat == [3, 4], f"a sorhatáron futó húzás eredménye: {talalat}"


class TestPillanatfelvetel:
    """`[elem+0x5c]`: a húzás a FELVÉTELKORI állapothoz viszonyít."""

    @staticmethod
    def _kezd(qt_app, grid):
        QMetaObject.invokeMethod(
            grid, "beginLasso", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

    @staticmethod
    def _frissit(qt_app, grid, start, count, flow_w, x1, y1, x2, y2, mods=0):
        """A húzás KÖZBENI frissítés — a felengedés (`applyLasso`) párja."""
        QMetaObject.invokeMethod(
            grid, "updateLasso", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", start), Q_ARG("QVariant", count),
            Q_ARG("QVariant", flow_w),
            Q_ARG("QVariant", float(x1)), Q_ARG("QVariant", float(y1)),
            Q_ARG("QVariant", float(x2)), Q_ARG("QVariant", float(y2)),
            Q_ARG("QVariant", int(mods)),
        )
        qt_app.processEvents()

    def test_ctrl_lasszo_visszahuzva_nem_hagy_ragadt_elemet(
        self, qml_app, qt_app
    ):
        """⚠️ A jegy nevesített tesztje: 3 kijelölt kép → Ctrl-lasszó egy
        4. fölé, majd VISSZA → megint 3 kijelölt kép.

        A 4 képes csoport rácsa (3 oszlop) az első sorban tele van, a
        másodikban egyetlen kép áll — a második sor HARMADIK helye üres,
        onnan indul és oda tér vissza a keret."""
        window, _controller, _start = _feed(qml_app, qt_app)
        grid = _grid(window)
        pitch = int(grid.property("nominalCellWidth"))
        ch = float(grid.property("cellHeight"))
        window.setProperty("selectedIndexes", [0, 1, 2])
        window.setProperty("selectedIndex", 2)
        qt_app.processEvents()
        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        ures_x, ures_y = pitch * 2.5, ch * 1.5

        self._kezd(qt_app, grid)
        # a keret a második sor egyetlen képére (3.) húzódik…
        self._frissit(
            qt_app, grid, 0, 4, pitch * 3,
            ures_x, ures_y, pitch * 0.5, ures_y, ctrl,
        )
        assert _kijelolt(window) == [0, 1, 2, 3], (
            "a húzás közben nem került be a keretbe eső kép"
        )
        # …majd visszahúzva már egyetlen képet sem fog be
        self._frissit(
            qt_app, grid, 0, 4, pitch * 3,
            ures_x, ures_y, ures_x, ures_y, ctrl,
        )

        assert _kijelolt(window) == [0, 1, 2], (
            "a visszahúzott keret »ragadt« elemet hagyott a kijelölésben"
        )

    def test_a_kijeloles_mar_huzas_kozben_frissul(self, qml_app, qt_app):
        """VALÓDI húzás: a kijelölés a FELENGEDÉS ELŐTT is követi a keretet.

        Az eredeti a húzás minden mozdulatánál újraszámol a
        pillanatfelvételből — nálunk a kijelölés csak felengedéskor
        változott, tehát a felhasználó vakon húzott."""
        window, _controller, start = _feed(qml_app, qt_app)
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()

        # ⚠️ MINDKÉT pontot a görgetés megállapodása UTÁN mérjük: a
        # `_gorgesd_lathatora` második hívása elmozdíthatná az elsőt.
        _gorgesd_lathatora(window, qt_app, start + 1)
        _gorgesd_lathatora(window, qt_app, start)
        kezdet = _kozeppont(window, start)
        veg = _kozeppont(window, start + 1)
        if abs(veg.y() - kezdet.y()) > 1:
            pytest.skip("egyoszlopos rács: nincs vízszintes húzás egy soron belül")

        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonPress, kezdet,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        assert _indexkep(window, start).property("pressed"), (
            "a lenyomás nem ért el az indexképig"
        )
        for arany in (0.5, 1.0):
            pont = QPointF(
                kezdet.x() + (veg.x() - kezdet.x()) * arany, kezdet.y()
            )
            _egeresemeny(
                window, qt_app, QEvent.Type.MouseMove, pont,
                Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
        kozben = _kijelolt(window)
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonRelease, veg,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )

        assert kozben == [start, start + 1], (
            f"felengedés ELŐTT a kijelölés: {kozben}"
        )


class TestLenyomasNemSzukit:
    """`0x00719d22` / `0x00719e1f`: a lenyomás nem szűkít, a felengedés igen.

    Megőrző tesztek: a #455 fogd-és-vidd ezt már megvalósította, de a
    viselkedés a jegy szerződésének része — őr nélkül némán elveszhetne."""

    def test_a_kijelolt_kepre_lenyomva_a_tobbes_kijeloles_megmarad(
        self, qml_app, qt_app
    ):
        window, _controller, start = _feed(qml_app, qt_app)
        window.setProperty("selectedIndexes", [start, start + 1, start + 2])
        window.setProperty("selectedIndex", start + 2)
        qt_app.processEvents()

        kozep = _gorgesd_lathatora(window, qt_app, start + 1)
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonPress, kozep,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        lenyomva = _kijelolt(window)
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonRelease, kozep,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )

        assert lenyomva == [start, start + 1, start + 2], (
            "a lenyomás egyetlen képre szűkítette a kijelölést — így a "
            "többelemű kijelölés nem húzható egyben"
        )

    def test_a_kijelolt_kepet_elhuzva_mind_a_harom_utazik(
        self, qml_app, qt_app
    ):
        """A jegy nevesített tesztje: 3 kijelölt kép, az egyikről indított
        húzás → mind a 3 marad kijelölve (a húzás a #455 fogd-és-vidd, nem
        lasszó), és nem szűkül egyre."""
        window, _controller, start = _feed(qml_app, qt_app)
        window.setProperty("selectedIndexes", [start, start + 1, start + 2])
        window.setProperty("selectedIndex", start + 2)
        qt_app.processEvents()

        kozep = _gorgesd_lathatora(window, qt_app, start + 1)
        terulet = _indexkep(window, start + 1)
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonPress, kozep,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseMove,
            QPointF(kozep.x() + 30, kozep.y() + 30),
            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        huzas_kozben = _kijelolt(window)
        huzas = terulet.property("dragging")
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonRelease,
            QPointF(kozep.x() + 30, kozep.y() + 30),
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )

        assert huzas, "kijelölt képről nem fogd-és-vidd, hanem lasszó indult"
        assert huzas_kozben == [start, start + 1, start + 2], (
            f"a húzás egyre szűkítette a kijelölést: {huzas_kozben}"
        )
        assert _kijelolt(window) == [start, start + 1, start + 2], (
            "a húzás vége szűkítette a kijelölést"
        )

    def test_felengedve_huzas_nelkul_egyre_szukul(self, qml_app, qt_app):
        window, _controller, start = _feed(qml_app, qt_app)
        window.setProperty("selectedIndexes", [start, start + 1, start + 2])
        window.setProperty("selectedIndex", start + 2)
        qt_app.processEvents()

        _kattints(window, qt_app, start + 1)

        assert _kijelolt(window) == [start + 1]
