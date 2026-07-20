"""#142: a rács-feed csoporton belüli virtualizálása.

Egy nagy (több ezer képes) mappa láthatóvá válásakor NEM példányosulhat
minden cella — csak a látótér-közeli rácssorok delegate-jei élnek, így a
memória- és thumbnail-terhelés korlátos marad (RPi5, 50k+ fotós könyvtár).
A cellák szintetikus PhotoRecord-okkal készülnek (fájl nélkül): a teszt a
példányszámot méri, nem a képbetöltést.
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

from picasapy.index import PhotoRecord


def _settle(qt_app, rounds: int = 6) -> None:
    for _ in range(rounds):
        qt_app.processEvents()


def synthetic_records(count: int, folder: str) -> tuple:
    """`count` darab szintetikus fotó-rekord egyetlen mappában."""
    return tuple(
        PhotoRecord(
            id=i + 1,
            folder_path=folder,
            name=f"IMG_{i:05d}.jpg",
            kind="photo",
            size=1000,
            mtime_ns=1,
            star=False,
            caption=None,
            keywords=None,
            rotate_steps=0,
            filters=None,
            taken_at=None,
            orientation=1,
            width=8,
            height=6,
        )
        for i in range(count)
    )


@pytest.fixture
def big_feed_app(qml_app, qt_app):
    """A közös qml_app kiegészítve egy 3000 képes szintetikus mappával."""
    window, controller, lib, engine = qml_app
    records = synthetic_records(3000, str(lib / "nagy-mappa"))
    controller._view_mode = ("folder", str(lib))
    controller._show(records)
    _settle(qt_app)
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None, "photoGrid nem található"
    QMetaObject.invokeMethod(grid, "forceLayout")
    _settle(qt_app)
    return window, controller, grid


def _cell_count(grid) -> int:
    """A példányosított rács-cellák száma a VIZUÁLIS fán — a Repeater-
    delegate-ek nem QObject-gyermekei a rácsnak, a findChildren nem
    látná őket (ld. a test_qml_hidden contentItem-bejárás mintáját)."""

    def walk(item) -> int:
        total = 1 if item.objectName() == "feedCell" else 0
        return total + sum(walk(child) for child in item.childItems())

    return walk(grid.property("contentItem"))


class TestFeedVirtualization:
    def test_cell_count_is_bounded_for_big_group(self, big_feed_app, qt_app):
        window, controller, grid = big_feed_app
        assert controller.photos.rowCount() == 3000
        cells = _cell_count(grid)
        assert cells > 0, "a látótér celláinak példányosulniuk kell"
        # látótér (~800 px / ~160 px-es sorok ≈ 5 sor) + pufferek — bőven
        # elég 400 cella; a virtualizálatlan változat 3000-et hozna létre
        assert cells < 400, f"túl sok példányosított cella: {cells}"

    def test_scrolled_window_follows_viewport(self, big_feed_app, qt_app):
        from PySide6.QtCore import Q_ARG

        window, controller, grid = big_feed_app
        # görgetés mélyre a csoportban — a cellaszám korlátos marad, és a
        # látótér-közeli sorok cellái léteznek (scrollToRow működik)
        QMetaObject.invokeMethod(
            grid, "scrollToRow", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 1500),
        )
        QMetaObject.invokeMethod(grid, "forceLayout")
        _settle(qt_app)
        cells = _cell_count(grid)
        assert 0 < cells < 400, f"görgetés után is korlátos: {cells}"

    def test_selected_set_drives_cell_highlight(self, big_feed_app, qt_app):
        # #142: a cellák kijelölés-kötése set-alapú (O(1) lookup) — a
        # window.selectedSet a selectedIndexes-ből épül, és a látható
        # cella `selected` állapota követi
        window, controller, grid = big_feed_app
        window.setProperty("selectedIndexes", [0, 2])
        window.setProperty("selectedIndex", 2)
        _settle(qt_app)
        selected_set = window.property("selectedSet")
        if hasattr(selected_set, "toVariant"):
            selected_set = selected_set.toVariant()
        assert selected_set.get("0") or selected_set.get(0)

        def find_cells(item, out):
            if item.objectName() == "feedCell":
                out.append(item)
            for child in item.childItems():
                find_cells(child, out)
            return out

        cells = find_cells(grid.property("contentItem"), [])
        by_row = {c.property("row"): c for c in cells}
        assert by_row[0].childItems()[0].property("selected") is True
        assert by_row[1].childItems()[0].property("selected") is False
        assert by_row[2].childItems()[0].property("selected") is True

    def test_selection_navigation_still_works(self, big_feed_app, qt_app):
        from PySide6.QtCore import Q_ARG

        window, controller, grid = big_feed_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        QMetaObject.invokeMethod(
            grid, "moveSelection", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "down"),
        )
        _settle(qt_app)
        assert window.property("selectedIndex") == grid.property("columns")
