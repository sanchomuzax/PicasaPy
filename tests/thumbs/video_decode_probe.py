"""Párhuzamos videó-dekódolás próbája (#673) — KÜLÖN PROCESSZBEN futtatandó.

A `_decode_video_frame` több pool-szálból hívva SIGSEGV-vel viszi el az
EGÉSZ processzt, ha a sérült fájlon az OpenCV a GStreamer-háttérre esik
vissza. Egy in-process teszt ezért nem elég: a szegmentálási hiba a teljes
pytest-futást megölné (a #103-as tanulság mintája). A próba ezért itt fut,
a `test_video_decode_parallel.py` alprocesszként indítja.

Kimenet: `OK` + exit 0, vagy AssertionError / összeomlás + exit != 0.

Argumentumok: <munkakönyvtár> [szálak] [körök]
"""

import os
import sys
import threading
from pathlib import Path

_THREADS = 4
_ROUNDS = 12


def main(work_dir: Path, threads: int, rounds: int) -> None:
    from picasapy.thumbs.cache import _decode_video_frame

    # Szándékosan érvénytelen ("csonka") videó: az FFMPEG-háttér nem tudja
    # megnyitni, és pont ez váltja ki a GStreamerre való visszaesést.
    broken = work_dir / "serult.mp4"
    broken.write_bytes(b"\x00" * 64)

    results: list[object] = []
    results_lock = threading.Lock()

    def work() -> None:
        local = [_decode_video_frame(broken) for _ in range(rounds)]
        with results_lock:
            results.extend(local)

    workers = [threading.Thread(target=work) for _ in range(threads)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert len(results) == threads * rounds, (
        f"nem futott le minden hívás: {len(results)}"
    )
    assert all(frame is None for frame in results), (
        "a sérült videóból nem jöhet képkocka"
    )

    print("OK", flush=True)  # os._exit nem üríti a puffert — flush kell!
    # A GStreamer/FFMPEG háttérszálainak leépítése maga is deadlockra
    # hajlamos (#53-as osztály) — a processz itt lép ki, a takarítás az OS-é.
    os._exit(0)


if __name__ == "__main__":
    main(
        Path(sys.argv[1]),
        int(sys.argv[2]) if len(sys.argv) > 2 else _THREADS,
        int(sys.argv[3]) if len(sys.argv) > 3 else _ROUNDS,
    )
