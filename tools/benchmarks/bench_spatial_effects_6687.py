#!/usr/bin/env python3
"""Measure the eight spatial effects from issue #6687 on one fixed image.

Run from any directory, for example:
    python tools/benchmarks/bench_spatial_effects_6687.py --width 2560 --height 1707 --runs 3

The default input is a committed test fixture, resized with Pillow BICUBIC so
the benchmark does not depend on a machine-local photo or network mount.
"""

from __future__ import annotations

import argparse
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "tests/fixtures/golden_colab/forras.jpg"
sys.path.insert(0, str(ROOT / "src"))


def _effects() -> tuple[tuple[str, Callable[[np.ndarray], np.ndarray]], ...]:
    from picasapy.render import effects, glimmer_artistic, glimmer_creative, glimmer_frames, glimmer_tone
    from picasapy.render.color import apply_grain
    from picasapy.render.native_grain import grain_seed

    return (
        ("Holga", lambda image: glimmer_creative.apply_holga(image, 70.0, 30.0, 0.0)),
        ("radblur", lambda image: effects.apply_radblur(image, 0.5, 0.5, 0.0, 0.0)),
        ("LocalContrast", lambda image: glimmer_tone.apply_local_contrast(image, 15.0, 1.5)),
        ("PencilSketch", lambda image: glimmer_creative.apply_pencil_sketch(image, 2.0, 100.0, 0.0)),
        ("glow2", lambda image: effects.apply_glow(image, 0.65, 3.0)),
        ("Pixelate", lambda image: glimmer_artistic.apply_pixelate(image, 20.0, 0.0, 9)),
        ("grain2", lambda image: apply_grain(image, seed=grain_seed(0))),
        ("DropShadow", lambda image: glimmer_frames.apply_drop_shadow(image)),
    )


def _load_image(path: Path, width: int, height: int) -> np.ndarray:
    with Image.open(path) as source:
        image = source.convert("RGB")
        resized = image.resize((width, height), Image.Resampling.BICUBIC)
        return np.asarray(resized, dtype=np.uint8).copy()


def _system_line() -> str:
    try:
        load = ", ".join(f"{value:.2f}" for value in os.getloadavg())
    except (AttributeError, OSError):
        load = "nem érhető el"
    cpu = platform.processor() or platform.machine()
    return f"Gép: {platform.node()} / {cpu}; logikai CPU: {os.cpu_count()}; load 1/5/15: {load}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="RGB-forráskép")
    parser.add_argument("--width", type=int, default=2560, help="kimeneti kép szélessége")
    parser.add_argument("--height", type=int, default=1707, help="kimeneti kép magassága")
    parser.add_argument("--runs", type=int, default=3, help="mért hívások száma effektenként")
    parser.add_argument("--warmups", type=int, default=0, help="nem mért bemelegítő hívások effektenként")
    args = parser.parse_args()
    if args.width < 1 or args.height < 1 or args.runs < 1 or args.warmups < 0:
        parser.error("a width, height és runs pozitív, a warmups nemnegatív legyen")
    if not args.source.is_file():
        parser.error(f"a forráskép nem található: {args.source}")

    image = _load_image(args.source, args.width, args.height)
    print(f"Forrás: {args.source}")
    print(f"Méret: {image.shape[1]}×{image.shape[0]} RGB uint8; futás: {args.runs}; bemelegítés: {args.warmups}")
    print(_system_line())
    print("\n| Effekt | Futások (ms) | Medián (ms) |")
    print("|---|---:|---:|")
    for name, effect in _effects():
        for _ in range(args.warmups):
            effect(image.copy())
        samples = []
        for _ in range(args.runs):
            input_image = image.copy()
            started = time.perf_counter()
            effect(input_image)
            samples.append((time.perf_counter() - started) * 1000.0)
        rendered = ", ".join(f"{sample:.1f}" for sample in samples)
        print(f"| {name} | {rendered} | {statistics.median(samples):.1f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
