"""A #6686 hat render-szűrőjének időmérése és cProfile-jelentése.

Alapértelmezésben 2560×1707-es, rögzített magú szintetikus RGB-képet mér,
három egymást követő hívással. A `--profile` minden szűrőhöz külön
cProfile-összesítést ír. A célgép méréséhez a `--check-target` kapcsoló a
mediánra alkalmazza a 300 ms-os küszöböt.
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

# A szkript a forrásfás munkakönyvtárból közvetlenül is futtatható.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from picasapy.render.color import apply_saturation  # noqa: E402
from picasapy.render.directional import apply_dir_brite  # noqa: E402
from picasapy.render.glimmer_tone import apply_twotone  # noqa: E402
from picasapy.render.ops import apply_autocolor  # noqa: E402
from picasapy.render.rainbow import apply_rainbow  # noqa: E402
from picasapy.render.tone import apply_finetune2  # noqa: E402

Filter = tuple[str, Callable[[], np.ndarray]]


def _synthetic_image(width: int, height: int) -> np.ndarray:
    """Nem semleges, teljes tartományú bemenet, reprodukálható színeloszlással."""
    rng = np.random.default_rng(6686)
    green = rng.integers(0, 256, (height, width), dtype=np.uint8)
    green_wide = green.astype(np.uint16)
    red = np.minimum(255, green_wide + 24).astype(np.uint8)
    blue = np.minimum(255, green_wide * 3 // 4 + 32).astype(np.uint8)
    image = np.stack((red, green, blue), axis=-1)
    noise = rng.integers(0, 16, (height, width, 3), dtype=np.uint8)
    return np.minimum(image.astype(np.uint16) + noise, 255).astype(np.uint8)


def _filters(image: np.ndarray) -> tuple[Filter, ...]:
    return (
        (
            "finetune2",
            lambda: apply_finetune2(
                image,
                fill=0.5,
                highlights=0.24,
                shadows=0.16,
                neutral=None,
                temperature=0.0,
            ),
        ),
        ("autocolor", lambda: apply_autocolor(image)),
        ("sat", lambda: apply_saturation(image, 0.5)),
        ("TwoTone", lambda: apply_twotone(image)),
        ("dir_brite", lambda: apply_dir_brite(image, 0.5, -0.35)),
        ("rainbow", lambda: apply_rainbow(image)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=2560)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--profile-limit", type=int, default=10)
    parser.add_argument("--target-ms", type=float, default=300.0)
    parser.add_argument("--check-target", action="store_true")
    args = parser.parse_args()

    if args.width < 1 or (args.height is not None and args.height < 1):
        parser.error("a kép mérete pozitív kell legyen")
    if args.repeats < 1:
        parser.error("a --repeats legalább 1 legyen")

    height = args.height or round(args.width * 2 / 3)
    image = _synthetic_image(args.width, height)
    print(f"Bemenet: {args.width}×{height} RGB uint8, mag=6686, ismétlés={args.repeats}")

    failures: list[tuple[str, float]] = []
    for name, operation in _filters(image):
        durations: list[float] = []
        for _ in range(args.repeats):
            start = time.perf_counter()
            result = operation()
            durations.append((time.perf_counter() - start) * 1000.0)
            if result.shape != image.shape or result.dtype != np.uint8:
                raise RuntimeError(f"{name}: hibás kimenet: {result.shape}, {result.dtype}")
            del result

        median_ms = float(np.median(durations))
        samples = "/".join(f"{duration:.1f}" for duration in durations)
        print(f"{name:10s} {samples} ms; medián={median_ms:.1f} ms")
        if median_ms > args.target_ms:
            failures.append((name, median_ms))

        if args.profile:
            profile = cProfile.Profile()
            profile.runcall(operation)
            print(f"cProfile – {name}:")
            pstats.Stats(profile).strip_dirs().sort_stats("cumtime").print_stats(args.profile_limit)

    if args.check_target and failures:
        details = ", ".join(f"{name}={duration:.1f} ms" for name, duration in failures)
        print(f"NEM FELEL MEG a {args.target_ms:.1f} ms-os küszöbnek: {details}")
        return 1
    if args.check_target:
        print(f"Mind a hat medián legfeljebb {args.target_ms:.1f} ms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
