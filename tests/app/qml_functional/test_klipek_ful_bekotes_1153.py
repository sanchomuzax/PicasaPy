"""A „Klipek" fül BEKÖTÉSE a valódi alkalmazásban (#1153).

## Miért a `Main.qml`-ben mérünk

A fül saját tesztje (`test_collage_clips_tab_949.py`) a panelt
**mesterséges burokban** építi fel, és a `librarySelection`-t KÉZZEL
állítja be:

```python
panel.setProperty("librarySelection", [0, 1])
```

Ez azt méri, hogy a panel jól viselkedik, ha megkapja a könyvtár
kijelölését — azt NEM, hogy meg is kapja. A tulajdonos épp az ellenkezőjét
jelentette (v0.8.27): „nem lehet másik képet hozzáadni, ami nincsen még a
szettben."

Ez a fájl a VALÓDI láncot állítja: `Main.qml` → `window.selectedIndexes`
→ `CollagePanel.librarySelection` → `CollageClipsTab` → `addClips`.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _keres(window, nev: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    return window.findChild(QObject, nev)


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _kattints(window, item: QQuickItem) -> None:
    """VALÓDI kattintás a vezérlőre — nem a slot közvetlen hívása.

    ⚠️ A közvetlen `controller.addClips(...)` hívás akkor is zöld, ha a
    gomb kattinthatatlan (takarja valami, tiltott, nincs bekötve az
    `onClicked`). Épp az a hibaosztály, amit ez a fájl keres."""
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    QTest.qWait(50)


@pytest.fixture
def kollazs(qml_app, qt_app):
    """Kollázs nyitva, EGY képpel (a könyvtár 0. sorával)."""
    window, controller, _engine = qml_app
    assert _var(qt_app, lambda: controller.photos.rowCount() >= 2), (
        "a fixture könyvtára üres"
    )
    # ⚠️ A VALÓDI belépési pont a `Main.qml` `openCollageTab()`-ja: az nem
    # csak megnyitja a kollázst, hanem AKTIVÁLJA is a lapot. A csupasz
    # `controller.openCollage(...)` hívása után a panel `visible=False`
    # marad (a lap a Könyvtáron áll), a gombok mégis megtalálhatók és
    # engedélyezettek — így a közvetlen slot-hívásra épülő teszt zöld
    # volna egy olyan felületen, amit a felhasználó el sem ér.
    window.setProperty("selectedIndexes", [0])
    qt_app.processEvents()
    QMetaObject.invokeMethod(window, "openCollageTab")
    assert _var(qt_app, lambda: controller.property("collageOpen") is True)
    fulgomb = _keres(window, "collageClipsTabButton")
    assert fulgomb is not None, "a Klipek fül gombja nincs a jelenetben"
    assert _var(qt_app, fulgomb.isVisible), (
        "a Kollázs-panel nem látszik — a lap nem lett aktív"
    )
    window.setProperty("selectedIndexes", [])
    qt_app.processEvents()
    # A felhasználó a KLIPEK fülön áll, amikor felvesz — a panel viszont a
    # Beállítások lapján nyílik. Fülváltás nélkül a kattintás máshova esne,
    # miközben a gomb a jelenetben MEGVAN és engedélyezett: pont ez a
    # hibaosztály visz félre (a scene-graph nem a láthatóság).
    _kattints(window, fulgomb)
    assert _var(
        qt_app,
        lambda: (_keres(window, "collageAddClips") or fulgomb).isVisible(),
    ), "a Klipek lap nem jött elő"
    window.setProperty("selectedIndexes", [])
    qt_app.processEvents()
    return window, controller


class TestAKonyvtarKijeloleseEljutAFulig:
    def test_a_plusz_gomb_a_konyvtar_kijelolesetol_lesz_aktiv(
        self, kollazs, qt_app
    ):
        """A `Main.qml` kötése: `librarySelection: window.selectedIndexes`."""
        window, _controller = kollazs
        gomb = _keres(window, "collageAddClips")
        assert gomb is not None, "a felvevő gomb nincs a kirajzolt jelenetben"
        assert gomb.property("enabled") is False, (
            "kijelölés nélkül a felvevő gombnak tiltottnak kell lennie"
        )

        window.setProperty("selectedIndexes", [1])

        assert _var(qt_app, lambda: gomb.property("enabled") is True), (
            "a felvevő gomb tiltott maradt, pedig a könyvtárban van kijelölés "
            "— a Main.qml kötése nem jut el a fülig"
        )

    def test_a_felvetel_bekeruli_a_konyvtar_kepet(self, kollazs, qt_app):
        """A tulajdonos tünete: nem lehet másik képet hozzáadni (#1153)."""
        window, controller = kollazs
        elotte = controller.collageNodes.rowCount()
        window.setProperty("selectedIndexes", [1])
        gomb = _keres(window, "collageAddClips")
        assert _var(qt_app, lambda: gomb.property("enabled") is True)

        _kattints(window, gomb)

        assert _var(
            qt_app, lambda: controller.collageNodes.rowCount() == elotte + 1
        ), "a kollázs nem nőtt — a könyvtárból felvett kép nem került be"

    def test_a_klip_lista_ujra_rajzolodik_a_felvetel_utan(self, kollazs, qt_app):
        """A másik tünet: nem frissülnek az indexképek (#1153).

        #1276: a lista a VÁLASZTHATÓ képeket mutatja, ezért a felvétel
        UTÁN a felvett kép csempéje ELTŰNIK (felhasználtá vált) — korábban
        itt új csempe megjelenését vártuk. Az állítás tárgya ugyanaz
        maradt: a lista újrarajzolódik a felvételre. Csak az irány más.

        A lánc a VALÓDI alkalmazásé: a könyvtár kijelölése a tálcába kerül
        (`syncSelection`), onnan a lapra; a „+" a kollázsra teszi és
        felhasználtnak jelöli."""
        window, controller = kollazs

        def csempek() -> int:
            n = 0
            while _keres(window, f"collageClip{n}") is not None:
                n += 1
            return n

        elotte = controller.collageNodes.rowCount()
        window.setProperty("selectedIndexes", [1])
        gomb = _keres(window, "collageAddClips")
        assert _var(qt_app, lambda: gomb.property("enabled") is True)
        # A kijelölés a tálcába kerül, tehát VÁLASZTHATÓKÉNT megjelenik.
        assert _var(qt_app, lambda: csempek() == 1), (
            "a könyvtárban kijelölt kép nem jelent meg a választhatók közt"
        )

        _kattints(window, gomb)

        assert _var(
            qt_app, lambda: controller.collageNodes.rowCount() == elotte + 1
        )
        assert _var(qt_app, lambda: csempek() == 0), (
            "a felvett kép csempéje ottmaradt a választhatók listáján"
        )
        assert controller.trayUnusedCount == 0
