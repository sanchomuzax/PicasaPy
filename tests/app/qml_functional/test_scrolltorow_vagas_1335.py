"""A `scrollToRow` a görgethető tartományra vág — a rács nem ugrik (#1335).

## A lelet

A `LightboxFeed.scrollToRow` a `contentY`-t **nem vágta** a Flickable
görgethető tartományára, a `wheelStep` ezzel szemben igen. A nézet így
tartományon KÍVÜLI `contentY`-nál ragadt, és a Flickable csak a
**következő egérlenyomásra** rántotta vissza: a rács a kattintás
pillanatában megugrott, a kattintás/húzás pedig a közben elcsúszott képre
esett (mérve a #897 tesztkörnyezetében: `contentY` 101, miközben a
görgethető maximum 0 volt; egy indexkép középpontja y=175-ről 276-ra
ugrott, a húzásból néma, üres kijelölés lett).

## Amit ez a fájl mér

1. a vágást magát (`contentY` a maximumon áll),
2. a hiba LÉNYEGÉT: a vágás után a következő egérlenyomás **nem** mozdítja
   el a rácsot — a kattintás oda esik, ahová a felhasználó célzott,
3. az ellenkező irányú őrt: a vágás nem akadályozza a VALÓDI görgetést
   olyan feednél, ami nem fér a látótérbe (#1045 tanulsága),
4. a horgony-visszaállást (`restoreAnchor`): a javítás közben MÉRTÜK, hogy
   ugyanez a hiba onnan is előáll (`contentY` 277 ott, ahol a maximum 0) —
   a `scrollToRow` vágása egymagában nem zárta ki a tünetet.
"""

from pathlib import Path

import pytest
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

#: a szintetikus események időbélyege — enélkül a Qt dupla kattintást lát
_ORA = [1000]


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(300):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _feed(qml_app, qt_app, darab):
    """`darab` kép a „sok” mappában; visszaadja a csoport ELSŐ sorindexét is."""
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    (lib / "sok").mkdir(exist_ok=True)
    for i in range(darab):
        make_jpeg(lib / "sok" / f"k{i:03d}.jpg", size=(80, 60))
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


def _hatarok(grid):
    """A görgethető tartomány `(min, max)` határa content-koordinátában."""
    origin = float(grid.property("originY"))
    return origin, origin + max(
        0.0,
        float(grid.property("contentHeight")) - float(grid.property("height")),
    )


def _scroll(grid, qt_app, sor) -> None:
    QMetaObject.invokeMethod(
        grid, "scrollToRow", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", sor),
    )
    qt_app.processEvents()


def _wheel(grid, qt_app, delta) -> None:
    QMetaObject.invokeMethod(
        grid, "wheelStep", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", delta),
    )
    qt_app.processEvents()


def _bejar(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _bejar(gyerek)


def _indexkep(window, sor):
    for elem in _bejar(window.contentItem()):
        if elem.objectName() == "thumbMouseArea":
            cella = elem.parentItem()
            if cella is not None and cella.property("index") == sor:
                return elem
    return None


def _kozeppont(window, sor):
    """A sor indexképének középpontja JELENET-koordinátában."""
    terulet = _indexkep(window, sor)
    assert terulet is not None, f"a(z) {sor}. sor indexképe nem található"
    return terulet.mapToScene(
        QPointF(terulet.width() / 2, terulet.height() / 2)
    )


def _lenyomas(window, qt_app, pont) -> None:
    """VALÓDI egérlenyomás — ez rántja vissza a Flickable-t a határaira."""
    _ORA[0] += 1000
    esemeny = QMouseEvent(
        QEvent.Type.MouseButtonPress, pont, pont,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPointingDevice.primaryPointingDevice(),
    )
    esemeny.setTimestamp(_ORA[0])
    qt_app.sendEvent(window, esemeny)
    qt_app.processEvents()


def _felengedes(window, qt_app, pont) -> None:
    _ORA[0] += 1000
    esemeny = QMouseEvent(
        QEvent.Type.MouseButtonRelease, pont, pont,
        Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        QPointingDevice.primaryPointingDevice(),
    )
    esemeny.setTimestamp(_ORA[0])
    qt_app.sendEvent(window, esemeny)
    qt_app.processEvents()


#: a mért eset: a tartalom BELEFÉR a látótérbe (a maximum 0), a nézet
#: mégis 101 képponttal lejjebb áll
_KIVUL = 101.0


@pytest.fixture
def _befero_feed(qml_app, qt_app):
    """Rövid feed (a tartalom belefér a látótérbe) + a mért kilógó `contentY`."""
    window, _controller, start = _feed(qml_app, qt_app, 6)
    grid = _grid(window)
    # ⚠️ A feed-csere `Qt.callLater`-t ütemez (horgony-visszaállás, #17/#173):
    # amíg az le nem fut, felülírja a nézet pozícióját. A mérés csak UTÁNA
    # állítható be.
    for _ in range(5):
        qt_app.processEvents()
    _also, felso = _hatarok(grid)
    if felso > 0.5:
        pytest.skip("a futtató ablakában a feed nem fér a látótérbe")
    grid.setProperty("contentY", _KIVUL)
    qt_app.processEvents()
    assert float(grid.property("contentY")) == pytest.approx(_KIVUL), (
        "a szonda nem tudta tartományon kívülre állítani a nézetet"
    )
    return window, grid, start


class TestVagas:
    """A `scrollToRow` ugyanúgy vág, mint a `wheelStep`."""

    def test_a_scrolltorow_a_maximumra_vag(self, _befero_feed, qt_app):
        """⚠️ A jegy magja: tartományon kívülről visszatér a maximumra."""
        _window, grid, start = _befero_feed

        _scroll(grid, qt_app, start)

        also, felso = _hatarok(grid)
        assert float(grid.property("contentY")) == pytest.approx(felso), (
            f"a scrollToRow a tartományon kívül hagyta a nézetet: "
            f"contentY={grid.property('contentY')}, "
            f"görgethető tartomány=[{also}, {felso}]"
        )

    def test_a_wheelstep_ugyanezt_teszi(self, _befero_feed, qt_app):
        """A viszonyítási pont: a `wheelStep` MA is helyesen vág."""
        _window, grid, _start = _befero_feed

        _wheel(grid, qt_app, 0)

        _also, felso = _hatarok(grid)
        assert float(grid.property("contentY")) == pytest.approx(felso)


class TestNemUgrikAKattintasra:
    """A hiba LÉNYEGE: a következő egérlenyomás nem mozdítja el a rácsot."""

    def test_a_lenyomas_nem_mozditja_el_a_racsot(self, _befero_feed, qt_app):
        """⚠️ A `contentY` értéke önmagában tünet; a felhasználó abból lát
        valamit, hogy a rács a kattintás pillanatában MEGUGRIK, és a
        kattintás a közben elcsúszott képre esik."""
        window, grid, start = _befero_feed
        _scroll(grid, qt_app, start)
        elotte_y = float(grid.property("contentY"))
        elotte_kozep = _kozeppont(window, start)

        _lenyomas(window, qt_app, elotte_kozep)
        utana_y = float(grid.property("contentY"))
        utana_kozep = _kozeppont(window, start)
        _felengedes(window, qt_app, utana_kozep)

        assert utana_y == pytest.approx(elotte_y), (
            f"a lenyomás elmozdította a rácsot: {elotte_y} → {utana_y}"
        )
        assert utana_kozep.y() == pytest.approx(elotte_kozep.y(), abs=0.5), (
            "a lenyomás alatt elcsúszott az indexkép — a kattintás nem oda "
            f"esik, ahová a felhasználó célzott: {elotte_kozep.y()} → "
            f"{utana_kozep.y()}"
        )


class TestAVagasNemAkadalyozAGorgetest:
    """Ellenkező irányú őr (#1045): a vágás nem tilthatja le a görgetést."""

    def test_hosszu_feednel_a_cel_sor_lathatova_valik(self, qml_app, qt_app):
        """A látótérnél HOSSZABB feed utolsó sorára görgetve a nézet
        valóban elmozdul, és a sor a látótérbe kerül."""
        window, _controller, start = _feed(qml_app, qt_app, 120)
        grid = _grid(window)
        _also, felso = _hatarok(grid)
        if felso <= 0.5:
            pytest.skip("a futtató ablakában 120 kép is belefér a látótérbe")
        utolso = start + 119

        _scroll(grid, qt_app, utolso)

        also, felso = _hatarok(grid)
        contenty = float(grid.property("contentY"))
        assert contenty > also + 0.5, (
            "a scrollToRow nem mozdult el a feed elejéről"
        )
        assert also - 0.5 <= contenty <= felso + 0.5, (
            f"contentY={contenty} a [{also}, {felso}] tartományon kívül"
        )
        assert _indexkep(window, utolso) is not None, (
            "az utolsó sor indexképe nem került a látótérbe"
        )


class TestHorgonyVisszaallas:
    """A `restoreAnchor` sem hagyhatja tartományon kívül a nézetet (#1335).

    A horgony a viewport tetején látszó mappacsoport útvonala; a
    visszaálláskor a nézet a csoport `y`-ára ugrik. A feed VÉGÉN álló
    csoportnál ez a `y` a görgethető maximum FÖLÖTT van, ha a tartalom
    belefér a látótérbe — mérve: `contentY` 277, maximum 0."""

    def test_az_utolso_csoportra_allitott_horgony_a_tartomanyban_marad(
        self, qml_app, qt_app
    ):
        window, controller, _start = _feed(qml_app, qt_app, 6)
        grid = _grid(window)
        for _ in range(5):
            qt_app.processEvents()
        _also, felso = _hatarok(grid)
        if felso > 0.5:
            pytest.skip("a futtató ablakában a feed nem fér a látótérbe")
        utolso = controller.feedGroups[-1]
        grid.setProperty("anchorPath", str(utolso["path"]))
        grid.setProperty("anchorOffset", 0.0)
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            grid, "restoreAnchor", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        also, felso = _hatarok(grid)
        contenty = float(grid.property("contentY"))
        assert also - 0.5 <= contenty <= felso + 0.5, (
            f"a horgony-visszaállás a tartományon kívül hagyta a nézetet: "
            f"contentY={contenty}, görgethető tartomány=[{also}, {felso}]"
        )
