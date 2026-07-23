"""#142: szintetikus feed-stresszmérés a Python-rétegen (50k–100k fotó).

A research-plan 1. pontjának („50k–100k elemes rács-stresszteszt és
memóriamérés") gépi, ismételhető fele. A QML-rétegű (valódi MVP-rácsos)
párja a `tests/app/test_feed_stress_100k.py` — azt így kell futtatni:

    PICASAPY_STRESS=1 QT_QPA_PLATFORM=offscreen \
        timeout 300 python3 -m pytest tests/app/test_feed_stress_100k.py -q -s

Ez a szkript a rács alatti Python-réteg költségeit méri 100k szintetikus
rekorddal (fájl-I/O nélkül):

  * PhotoGridModel.set_photos — teljes modell-reset költsége,
  * set_photos VÁLTOZATLAN tartalommal — a #142-es no-op gyorsút,
  * ThumbnailProvider.register_photos — a lusta filters-parse melletti
    regisztráció költsége,
  * memória: RSS-delta és tracemalloc-csúcs.

Futtatás (headless):

    QT_QPA_PLATFORM=offscreen python3 tools/benchmarks/bench_feed_100k.py \
        [--count 100000]

Az eredmények dokumentálása: docs/benchmarks/feed-100k-stressz.md.
"""

from __future__ import annotations

import argparse
import resource
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from PySide6.QtGui import QGuiApplication  # noqa: E402

from picasapy.index import PhotoRecord  # noqa: E402


def _records(count: int, folder: str) -> tuple:
    """`count` darab szintetikus fotó-rekord — minden 10. képen van
    filters= lánc, hogy a lusta parse valósághű terhet kapjon."""
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


def _rss_mb() -> float:
    """A folyamat aktuális RSS-csúcsa MB-ban (ru_maxrss: Linuxon kB)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100_000,
                        help="szintetikus fotók száma (alap: 100000)")
    args = parser.parse_args()

    app = QGuiApplication(sys.argv)  # noqa: F841 — Qt-objektumokhoz kell

    from picasapy.app.models import PhotoGridModel
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    print(f"== #142 feed-stresszmérés: {args.count} szintetikus fotó ==")
    rss_start = _rss_mb()
    tracemalloc.start()

    t0 = time.perf_counter()
    records = _records(args.count, "/konyvtar/nagy-mappa")
    t_build = time.perf_counter() - t0
    print(f"rekord-építés:                 {t_build:8.3f} s")

    model = PhotoGridModel()
    t0 = time.perf_counter()
    model.set_photos(records)
    t_set = time.perf_counter() - t0
    print(f"set_photos (első, teljes reset):{t_set:8.3f} s")

    t0 = time.perf_counter()
    model.set_photos(records)  # azonos tartalom → #142-es no-op ág
    t_noop = time.perf_counter() - t0
    print(f"set_photos (változatlan, no-op):{t_noop:8.3f} s")

    # A teljes ThumbnailProvider konstruktora lemez-cache-t és szálpoolt
    # nyitna — a register_photos méréséhez elég a csupasz példány, a
    # VALÓDI metódust hívjuk rajta (#142: a regisztráció lusta parse
    # mellett csak dict-építés, ezt bizonyítja a mérés).
    provider = ThumbnailProvider.__new__(ThumbnailProvider)
    t0 = time.perf_counter()
    ThumbnailProvider.register_photos(provider, records)
    t_reg = time.perf_counter() - t0
    print(f"register_photos (lusta parse): {t_reg:8.3f} s")

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_end = _rss_mb()
    print(f"tracemalloc-csúcs:             {peak / 1024 / 1024:8.1f} MB")
    print(f"RSS: {rss_start:.1f} MB → {rss_end:.1f} MB "
          f"(delta {rss_end - rss_start:+.1f} MB)")

    ok = t_noop < 0.01 and t_set < 5.0 and t_reg < 5.0
    print("VERDIKT:", "OK" if ok else "FIGYELEM — vizsgálandó regresszió")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
