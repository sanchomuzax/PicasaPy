"""#4532 — a szűrősáv végén nem maradhat működés nélküli, gombnak látszó jel.

Az eredeti szűrőkereső elemei: csillag, mozgófilm, webalbum, arc, geo. A
`▤` jel a mozgófilm-gomb mellett állt kezelő nélkül; most a sávból kikerül.
A teszt valódi egérkattintásokkal megy végig a maradék szűrőkön, és
ellenőrzi, hogy a sávban nincs látható `▤` jel.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

HALOTT_JEL = "▤"


def _item(window, object_name: str) -> QQuickItem:
    item = window.findChild(QQuickItem, object_name)
    assert item is not None, f"a(z) {object_name} QML-elem nem található"
    return item


def _kattintas(window, item: QQuickItem, qt_app) -> None:
    """Valódi kattintás a felépült QML-elem aktuális közepére."""
    point = item.mapToScene(
        QPointF(float(item.width()) / 2, float(item.height()) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _bejar(item):
    for child in item.childItems():
        yield child
        yield from _bejar(child)


def _lathato_halott_jelek(window) -> list[QQuickItem]:
    """A szűrősáv látható szövegelemei, amelyeken a halott jel áll.

    A nézetváltó (`toolbarFlatViewButton`) ugyanezt a glifet használja, de
    működő gomb, ezért a vizsgálat a `searchgroup` sávra szűkül.
    """
    sav = _item(window, "searchgroup")
    return [
        item
        for item in _bejar(sav)
        if item.property("text") == HALOTT_JEL and item.isVisible()
    ]


def test_szurosavban_nincs_halott_jel_minden_ablakmagassagon(qml_app, qt_app):
    window, controller, _engine = qml_app
    assert controller.photos.photos

    # A geo-gomb csak meglévő helyjelölő mellett kattintható.
    controller.setGeotagRows([0], 47.4979, 19.0402)
    assert controller.geoMarkerCount > 0

    # Az ablakmagasságot ±5 px-re állítjuk, hogy a sáv scene-koordinátái
    # a helyi elrendezéstől függetlenül is valódi kattintásnak feleljenek meg.
    alap_magassag = int(window.height())
    hibak: list[str] = []

    for delta in (-5, 0, 5):
        window.resize(int(window.width()), alap_magassag + delta)
        qt_app.processEvents()
        assert int(window.height()) == alap_magassag + delta

        jelek = _lathato_halott_jelek(window)
        if jelek:
            hibak.append(
                f"a szűrősávban látható, kezelő nélküli „{HALOTT_JEL}” jel maradt "
                f"({len(jelek)} db, ablakmagasság-eltérés: {delta}px)"
            )

        for object_name, mode in (
            ("starFilterButton", "starred"),
            ("movieFilter", "videos"),
            ("faceFilter", "faces"),
            ("geoFilter", "geo"),
        ):
            _kattintas(window, _item(window, object_name), qt_app)
            if controller.viewModeName != mode:
                hibak.append(
                    f"{object_name} kattintása után {controller.viewModeName!r}, "
                    f"nem {mode!r} nézet aktív (ablakmagasság-eltérés: {delta}px)"
                )

        controller.clearFilter()
        qt_app.processEvents()

    assert not hibak, "\n".join(hibak)
