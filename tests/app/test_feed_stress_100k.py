"""#142: 100k-s stresszteszt a VALÓDI MVP-rácson — csak kérésre fut.

A research-plan 1. pontjának QML-rétegű fele: 100 000 szintetikus fotóval
tölti a valódi feedet (LightboxFeed), és azt ellenőrzi, hogy a csoporton
belüli virtualizálás mellett a példányosított cellaszám KORLÁTOS marad,
mély görgetés után is. Mellékhatásként kiírja az időket és a memóriát —
ezekből készül a docs/benchmarks/feed-100k-stressz.md.

Alapból SKIP (perc nagyságrendű futás lenne minden CI-körben):

    PICASAPY_STRESS=1 QT_QPA_PLATFORM=offscreen \
        timeout 300 python3 -m pytest tests/app/test_feed_stress_100k.py -q -s
"""

import os
import resource
import time

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from picasapy.index import PhotoRecord

pytestmark = pytest.mark.skipif(
    os.environ.get("PICASAPY_STRESS") != "1",
    reason="stresszteszt — csak PICASAPY_STRESS=1 esetén fut (#142)",
)

STRESS_COUNT = 100_000


def _settle(qt_app, rounds: int = 6) -> None:
    for _ in range(rounds):
        qt_app.processEvents()


def _synthetic_records(count: int, folder: str) -> tuple:
    """Szintetikus rekordok fájl nélkül (a test_qml_feed_virtualization
    mintája) — minden 10. képen filters= lánc a lusta parse teszteléséhez."""
    return tuple(
        PhotoRecord(
            id=i + 1,
            folder_path=folder,
            name=f"IMG_{i:06d}.jpg",
            kind="photo",
            size=1000,
            mtime_ns=1,
            star=False,
            caption=None,
            keywords=None,
            rotate_steps=0,
            filters="enhance=1;" if i % 10 == 0 else None,
            taken_at=None,
            orientation=1,
            width=8,
            height=6,
        )
        for i in range(count)
    )


def _cell_count(grid) -> int:
    """Példányosított rács-cellák a vizuális fán (ld. virtualizációs teszt)."""

    def walk(item) -> int:
        total = 1 if item.objectName() == "feedCell" else 0
        return total + sum(walk(child) for child in item.childItems())

    return walk(grid.property("contentItem"))


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


class TestFeedStress100k:
    def test_100k_feed_bounded_and_scrollable(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        rss0 = _rss_mb()

        t0 = time.perf_counter()
        records = _synthetic_records(STRESS_COUNT, str(lib / "nagy-mappa"))
        t_build = time.perf_counter() - t0

        controller._view_mode = ("folder", str(lib))
        t0 = time.perf_counter()
        controller._show(records)
        _settle(qt_app)
        t_show = time.perf_counter() - t0

        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        QMetaObject.invokeMethod(grid, "forceLayout")
        _settle(qt_app)

        assert controller.photos.rowCount() == STRESS_COUNT
        cells_top = _cell_count(grid)
        assert 0 < cells_top < 400, f"korlátlan példányszám fent: {cells_top}"

        # mély görgetés a csoport közepére, majd az aljára
        t0 = time.perf_counter()
        for target in (STRESS_COUNT // 2 // 6, (STRESS_COUNT - 10) // 6):
            QMetaObject.invokeMethod(
                grid, "scrollToRow", Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", target),
            )
            QMetaObject.invokeMethod(grid, "forceLayout")
            _settle(qt_app)
        t_scroll = time.perf_counter() - t0
        cells_deep = _cell_count(grid)
        assert 0 < cells_deep < 400, f"korlátlan példányszám lent: {cells_deep}"

        # mappaváltás-gyorsút: azonos feedre a set_photos no-op (#142)
        t0 = time.perf_counter()
        controller._show(records)
        _settle(qt_app)
        t_reshow = time.perf_counter() - t0

        rss1 = _rss_mb()
        print(
            "\n== #142 stressz-jelentés (100k szintetikus fotó) ==\n"
            f"rekord-építés:        {t_build:7.2f} s\n"
            f"_show (első betöltés): {t_show:7.2f} s\n"
            f"mély görgetés (2 ugrás):{t_scroll:6.2f} s\n"
            f"_show (változatlan):   {t_reshow:7.2f} s\n"
            f"cellaszám fent/lent:   {cells_top} / {cells_deep}\n"
            f"RSS: {rss0:.0f} MB → {rss1:.0f} MB (delta {rss1 - rss0:+.0f} MB)"
        )
