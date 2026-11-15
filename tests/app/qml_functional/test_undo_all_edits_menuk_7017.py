"""Az Összes szerkesztés visszavonása tétel szürkítése mindhárom menüben az
eredeti szerkesztettségi állapot szerint (#7017, a #7009 összevetése alapján).

Az eredeti képlet (`0x004296a0`, `0x005cb1a0`, `0x0056f393-0x0056f402`): a
kijelölés sorrendjében az első nem nulla állapotú kép dönt; szűrőláncos vagy
tükrözött kép állapota `1` (a tétel él), csak elforgatott képé `2` (szürke),
a szerkesztetlené `0`. Ha nincs nem nulla állapotú kép, a tétel szürke.

A tesztek a menüt TÉNYLEGESEN megnyitják (Kép menü: a menüsor fejlécére
kattintással; helyi menü: `openPhotoContextMenu`; néző: `openContextMenu`), és a
`MenuItem` `enabled` állapotát olvassák, nem a függvényt hívják.

Nem mért: a megerősítő párbeszéd és a törlés maga (ld. `test_undo_confirmations_465`
és `test_undo_all_edits_kulcsok_7017`).

rontás-kontroll: a `PicasaPictureMenu.qml` tételéről a `bar.undoAllEditsEnabled`
feltétel levétele -> test_kep_menu_az_eredeti_kepletet_koveti bukik; a
`MainPhotoContextMenu.qml` `canUndoAllEdits` kötésének visszaállítása a
`hasEdits`-re -> test_helyi_menu_az_eredeti_kepletet_koveti bukik; a
`PhotoViewerContextActions.qml` kötése `hasEdits`-re -> test_nezo_menu_... bukik.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre

# A rács név szerinti sorrendjében: 0_szurt, a_forgatott, b_szurt,
# c_tukrozott, d_sima. A szűrőláncos kép egyszer az elforgatott ELŐTT, egyszer
# UTÁNA áll, hogy mindkét irányú „első nem nulla" eset mérhető legyen.
_NEVEK = ("0_szurt.jpg", "a_forgatott.jpg", "b_szurt.jpg", "c_tukrozott.jpg", "d_sima.jpg")
_INI = (
    "[0_szurt.jpg]\nfilters=sat=1,-0.2;\n"
    "[a_forgatott.jpg]\nrotate=rotate(1)\n"
    "[b_szurt.jpg]\nfilters=sat=1,-0.2;\n"
    "[c_tukrozott.jpg]\nflipped=flipped(1)\n"
)

#: (kijelölt képek a rács sorrendjében, a tétel várt `enabled` állapota)
_ESETEK = (
    (("d_sima.jpg",), False),
    (("a_forgatott.jpg",), False),
    (("c_tukrozott.jpg",), True),
    (("b_szurt.jpg",), True),
    (("a_forgatott.jpg", "b_szurt.jpg"), False),
    (("0_szurt.jpg", "a_forgatott.jpg"), True),
    (("d_sima.jpg", "c_tukrozott.jpg"), True),
    (("d_sima.jpg", "a_forgatott.jpg"), False),
)

_KEEP: list = []


@pytest.fixture
def qml_app_7017(qt_app, tmp_path):
    def kepek(lib: Path) -> None:
        for nev in _NEVEK:
            make_jpeg(lib / nev, size=(320, 160))
        (lib / ".picasa.ini").write_text(_INI, encoding="utf-8")

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=kepek)


def _gyerek(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _sorok(controller, nevek) -> list[int]:
    index = {p.name: i for i, p in enumerate(controller.photos.photos)}
    assert set(_NEVEK) <= set(index), f"a rács nem tartalmazza a próbaképeket: {index}"
    return [index[nev] for nev in nevek]


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0])
    qt_app.processEvents()


def _var(qt_app, feltetel, uzenet, masodperc=10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _bezar(qt_app, menu) -> None:
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _kep_menu_megnyitasa(window, qt_app):
    """A Kép menü megnyitása a menüsor fejlécére kattintással."""
    menu_bar = window.property("menuBar")
    cimek = {"&Picture", "&Kép"}
    menu = next(
        elem for elem in menu_bar.findChildren(QObject)
        if elem.property("title") in cimek
    )
    fejlec = next(
        elem for elem in menu_bar.findChildren(QObject)
        if "MenuBarItem" in elem.metaObject().className()
        and elem.property("text") in cimek
    )
    assert isinstance(fejlec, QQuickItem)
    _KEEP.extend((menu_bar, menu, fejlec))
    kozep = fejlec.mapToScene(QPointF(fejlec.width() / 2, fejlec.height() / 2))
    QTest.mouseClick(
        fejlec.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    _var(qt_app, lambda: menu.property("opened") is True, "a Kép menü nem nyílt meg")
    return menu


def _helyi_menu_megnyitasa(window, qt_app, sor):
    racs = _gyerek(window, "photoGrid")
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", sor), Q_ARG("QVariant", racs),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    menu = _gyerek(window, "photoContextMenu")
    _var(qt_app, lambda: menu.property("visible") is True, "a helyi menü nem nyílt meg")
    return menu


def _nezo_menu_megnyitasa(window, qt_app, sor):
    window.setProperty("viewerOpen", True)
    nezo = _gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", sor)
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        nezo, "openContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    return _gyerek(window, "viewerContextMenu")


def _enabled(qt_app, window, nev) -> bool:
    """A tétel állapota a kötés lefutása után."""
    qt_app.processEvents()
    return _gyerek(window, nev).property("enabled") is True


def test_kep_menu_az_eredeti_kepletet_koveti(qml_app_7017, qt_app):
    window, controller, _engine = qml_app_7017
    hibak = []
    for nevek, vart in _ESETEK:
        _kijelol(window, qt_app, _sorok(controller, nevek))
        menu = _kep_menu_megnyitasa(window, qt_app)
        kapott = _enabled(qt_app, window, "menuPictureUndoAllEdits")
        _bezar(qt_app, menu)
        if kapott is not vart:
            hibak.append(f"{nevek}: várt {vart}, kapott {kapott}")
    assert not hibak, "Kép menü: " + "; ".join(hibak)


def test_helyi_menu_az_eredeti_kepletet_koveti(qml_app_7017, qt_app):
    window, controller, _engine = qml_app_7017
    hibak = []
    for nevek, vart in _ESETEK:
        sorok = _sorok(controller, nevek)
        _kijelol(window, qt_app, sorok)
        menu = _helyi_menu_megnyitasa(window, qt_app, sorok[0])
        kapott = _enabled(qt_app, window, "contextMenuUndoAllEdits")
        _bezar(qt_app, menu)
        if kapott is not vart:
            hibak.append(f"{nevek}: várt {vart}, kapott {kapott}")
    assert not hibak, "helyi menü: " + "; ".join(hibak)


def test_helyi_menu_nem_a_jobbklikkelt_sorra_szamol(qml_app_7017, qt_app):
    """A régi kötés a jobbklikkelt sor `hasEdits` mezőjét olvasta; az eredeti a
    KIJELÖLÉS első nem nulla állapotú képét nézi. Itt a jobbklikkelt sor a
    szűrőláncos `b_szurt`, de a kijelölés első nem nulla képe az elforgatott
    `a_forgatott`: a tétel szürke marad."""
    window, controller, _engine = qml_app_7017
    sorok = _sorok(controller, ("a_forgatott.jpg", "b_szurt.jpg"))
    _kijelol(window, qt_app, sorok)

    menu = _helyi_menu_megnyitasa(window, qt_app, sorok[1])

    assert _enabled(qt_app, window, "contextMenuUndoAllEdits") is False
    _bezar(qt_app, menu)


def test_nezo_menu_az_eredeti_kepletet_koveti(qml_app_7017, qt_app):
    window, controller, _engine = qml_app_7017
    hibak = []
    for nevek, vart in (e for e in _ESETEK if len(e[0]) == 1):
        sor = _sorok(controller, nevek)[0]
        menu = _nezo_menu_megnyitasa(window, qt_app, sor)
        kapott = _enabled(qt_app, window, "viewerMenuUndoAllEdits")
        _bezar(qt_app, menu)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        if kapott is not vart:
            hibak.append(f"{nevek}: várt {vart}, kapott {kapott}")
    assert not hibak, "néző menü: " + "; ".join(hibak)


def test_a_nezo_nyitott_kep_menu_a_nezett_kepre_szamol(qml_app_7017, qt_app):
    """Nézőben a Kép menü célpontja a nézett kép, nem a mögötte maradt kijelölés."""
    window, controller, _engine = qml_app_7017
    szurt, forgatott = _sorok(controller, ("b_szurt.jpg", "a_forgatott.jpg"))
    _kijelol(window, qt_app, [szurt])
    window.setProperty("viewerOpen", True)
    _gyerek(window, "photoViewer").setProperty("currentIndex", forgatott)
    qt_app.processEvents()

    menu = _kep_menu_megnyitasa(window, qt_app)

    assert _enabled(qt_app, window, "menuPictureUndoAllEdits") is False
    _bezar(qt_app, menu)
