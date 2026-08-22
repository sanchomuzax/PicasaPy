"""A kijelölés-bővítés sem lép át mappahatáron (#1219).

## Miért

A #1145 a *parancsokat* (Ctrl+A, invertálás, csillagosok) szorította a
jelenlegi mappára — a **kattintás- és billentyűkezelés viszont maradt**:
Shift+kattintás és Shift+nyíl továbbra is átnyúlt a szomszéd mappába.

## Az eredeti — bizonyíték

A feed konténere (`0x0076a390`, `CMultiAlbumNode` vtábla 33. rés) mindig
pontosan EGY albumsor kijelölés-csomópontját éri el, tehát a
tartomány-mag (`0x00716ae0`) és a nyilas léptetés (`0x00717eb0`)
fizikailag sem tud mappahatárt átlépni. A mappa végén MEGÁLL: a
`0x00718031` `cmp/jbe` ELŐJEL NÉLKÜLI (a −1-re csökkenő index ugyanide
fut), a határ-ág pedig `0x00717e76`-nál `[this+0x2e0] = 0xFFFFFFFF`, azaz
törli a jelölőt és NEM jelöl ki újat — nem lép át és nem fordul át.

⚠️ A jegy harmadik állítása („a lasszó több mappa képeit is befogja")
TÉVES: a lasszó eleve csoportonkénti (`groupCol.modelData.start/count`).
Az itteni lasszó-teszt ezért **megőrző** — nem javítást mér.
"""

from PySide6.QtCore import Q_ARG, QEvent, QMetaObject, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPointingDevice

from support.jpeg_factory import make_jpeg


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _ket_mappas_feed(qml_app, qt_app):
    """A `qml_app` könyvtára alá két almappa — két feed-csoport."""
    from pathlib import Path

    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    for mappa, darab in (("alma", 3), ("korte", 3)):
        (lib / mappa).mkdir(exist_ok=True)
        for i in range(darab):
            make_jpeg(lib / mappa / f"{mappa}{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    csoportok = controller.feedGroups
    assert len(csoportok) >= 2, f"kevés csoport: {[c['name'] for c in csoportok]}"
    return window, controller, csoportok


def _kijelolt(window) -> list[int]:
    """A `selectedIndexes` PYTHON-listaként — a QML `QJSValue`-t ad."""
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return sorted(int(i) for i in (ertek or []))


def _bejar(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _bejar(gyerek)


def _indexkep(window, sor):
    """A `sor`-hoz tartozó indexkép-cella (ThumbDelegate) a valódi fában."""
    for elem in _bejar(window.contentItem()):
        if elem.objectName() == "thumbMouseArea":
            cella = elem.parentItem()
            if cella is not None and cella.property("index") == sor:
                return elem
    return None


#: a szintetikus kattintások időbélyege — ld. a `_kattints` figyelmeztetését
_ORA = [1000]


def _gorgesd_lathatora(window, qt_app, sor):
    """A sor indexképének KÖZÉPPONTJA ablak-koordinátában, láthatóra
    görgetve.

    ⚠️ A feed a kattintás után a kijelölt sorhoz igazít, ezért a
    következő cél könnyen kicsúszik az ablakból (mérve: a 4. sor
    középpontja y=−1-re került). A kikattintott esemény ilyenkor NEM ér
    el egyetlen indexképet sem, és a teszt a korábbi kijelölést látva
    némán zöld marad."""
    grid = _grid(window)

    def _kozeppont():
        terulet = _indexkep(window, sor)
        assert terulet is not None, f"a(z) {sor}. sor indexképe nem található"
        return terulet.mapToScene(
            QPointF(terulet.width() / 2, terulet.height() / 2)
        )

    def _belul(pont):
        # ⚠️ margóval: a görgetés közbeni köztes állapotban a cella széle
        # már benne van az ablakban, a közepe viszont még arrébb csúszik —
        # margó nélkül a kattintás a szomszéd cellára esne (flaky teszt).
        return (
            8 <= pont.y() <= window.height() - 8
            and 8 <= pont.x() <= window.width() - 8
        )

    elozo = None
    for kor in range(40):
        kozep = _kozeppont()
        # akkor fogadjuk el, ha látható ÉS már nem mozog
        if _belul(kozep) and elozo is not None and abs(kozep.y() - elozo) < 0.5:
            return kozep
        elozo = kozep.y()
        if kor % 8 == 0:
            QMetaObject.invokeMethod(
                grid,
                "scrollToRow",
                Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", sor),
            )
        qt_app.processEvents()
    raise AssertionError(f"a(z) {sor}. sor indexképe nem görgethető láthatóra")


def _kattints(window, qt_app, sor, mods=Qt.KeyboardModifier.NoModifier):
    """VALÓDI egéresemény az indexképre — nem a `handleThumbClick` hívása.

    A #1148 és a #1200 is azért maradt zöld egy használhatatlan funkció
    fölött, mert a teszt a kezelőfüggvényt hívta közvetlenül.

    ⚠️ Az IDŐBÉLYEG kötelező. Enélkül minden szintetikus esemény `0`
    ezredmásodpercen áll, a Qt a második lenyomást DUPLA KATTINTÁSNAK
    veszi, megnyílik a néző, és onnantól minden további kattintás a néző
    fölé megy — a teszt pedig némán zöld marad, mert az első kattintás
    kijelölése ottmarad. (Mérve: az első kattintás után se a sima, se a
    Ctrl-os, se a Shiftes kattintás nem változtatott a kijelölésen.)"""
    kozep = _gorgesd_lathatora(window, qt_app, sor)
    for tipus in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        _ORA[0] += 1000
        esemeny = QMouseEvent(
            tipus,
            kozep,
            kozep,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton
            if tipus == QEvent.Type.MouseButtonPress
            else Qt.MouseButton.NoButton,
            mods,
            QPointingDevice.primaryPointingDevice(),
        )
        esemeny.setTimestamp(_ORA[0])
        qt_app.sendEvent(window, esemeny)
    qt_app.processEvents()
    assert not window.property("viewerOpen"), (
        "a szintetikus kattintásból dupla kattintás lett (néző nyílt meg)"
    )


def _grid(window):
    from PySide6.QtCore import QObject

    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None, "a photoGrid nem található"
    return grid


def _nyil_le_shifttel(window, qt_app):
    """VALÓDI billentyűesemény a rácsra — nem az `extendSelection` hívása.

    A #1200 tanulsága: a közvetlen függvényhívás akkor is zöld marad, ha a
    funkciót a felhasználó el sem tudja sütni."""
    grid = _grid(window)
    grid.setProperty("focus", True)
    QMetaObject.invokeMethod(grid, "forceActiveFocus", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    esemeny = QKeyEvent(
        QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier
    )
    qt_app.sendEvent(window, esemeny)
    qt_app.processEvents()


class TestShiftKattintas:
    def test_a_tartomany_a_horgony_mappajaban_marad(self, qml_app, qt_app):
        """⚠️ A jegy magja: eddig átnyúlt a következő mappa képeire."""
        window, _controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        elso, masodik = csoportok[0], csoportok[1]
        elso_utolso = int(elso["start"]) + int(elso["count"]) - 1
        masodik_utolso = int(masodik["start"]) + int(masodik["count"]) - 1

        _kattints(window, qt_app, elso_utolso)
        _kattints(
            window, qt_app, masodik_utolso, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == [elso_utolso], (
            "a Shift+kattintás átnyúlt a szomszéd mappába"
        )

    def test_a_mappan_belul_tovabbra_is_bovit(self, qml_app, qt_app):
        """A szorítás nem ronthatja el a mappán belüli tartományt."""
        window, _controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        elso = csoportok[0]
        start, count = int(elso["start"]), int(elso["count"])

        _kattints(window, qt_app, start)
        _kattints(
            window, qt_app, start + count - 1, Qt.KeyboardModifier.ShiftModifier
        )

        assert _kijelolt(window) == list(range(start, start + count))


class TestShiftNyil:
    def test_a_mappa_aljan_megall(self, qml_app, qt_app):
        window, _controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        elso = csoportok[0]
        elso_utolso = int(elso["start"]) + int(elso["count"]) - 1

        _kattints(window, qt_app, elso_utolso)
        _nyil_le_shifttel(window, qt_app)

        assert _kijelolt(window) == [elso_utolso], (
            "a Shift+lefelé nyíl átlépett a szomszéd mappába"
        )


class TestLasszo:
    """MEGŐRZŐ teszt — a lasszó eleve csoportonkénti, ne romoljon el.

    A húzás a csoport saját folyamában indul, és a `applyLasso` a csoport
    `start`/`count` értékeit kapja: az egész képernyőt átfogó téglalap sem
    hozhat vissza másik mappából sort."""

    def test_a_lasszo_csak_a_sajat_csoportjabol_valogat(self, qml_app, qt_app):
        from PySide6.QtCore import Q_RETURN_ARG

        window, _controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        grid = _grid(window)
        elso = csoportok[0]
        start, count = int(elso["start"]), int(elso["count"])

        eredmeny = QMetaObject.invokeMethod(
            grid,
            "lassoIndexes",
            Qt.ConnectionType.DirectConnection,
            Q_RETURN_ARG("QVariant"),
            Q_ARG("QVariant", start),
            Q_ARG("QVariant", count),
            Q_ARG("QVariant", 1000),
            Q_ARG("QVariant", -5000.0),
            Q_ARG("QVariant", -5000.0),
            Q_ARG("QVariant", 5000.0),
            Q_ARG("QVariant", 5000.0),
        )
        if hasattr(eredmeny, "toVariant"):
            eredmeny = eredmeny.toVariant()
        sorok = sorted(int(i) for i in (eredmeny or []))
        assert sorok, "a mindent átfogó lasszó egy sort sem fogott be"
        assert sorok == list(range(start, start + count))
