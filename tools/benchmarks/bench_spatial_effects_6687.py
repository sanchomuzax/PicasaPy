#!/usr/bin/env python3
"""Measure the eight spatial effects from issue #6687 on one fixed image.

Run from any directory, for example:
    python tools/benchmarks/bench_spatial_effects_6687.py --width 2560 --height 1707 --runs 3

The default input is a committed test fixture, resized with Pillow BICUBIC so
the benchmark does not depend on a machine-local photo or network mount.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "tests/fixtures/golden_colab/forras.jpg"
sys.path.insert(0, str(ROOT / "src"))
_WORKER_READY = "__SPATIAL_BENCH_WORKER_READY__"
_EFFECT_NAMES = (
    "Holga",
    "radblur",
    "LocalContrast",
    "PencilSketch",
    "glow2",
    "Pixelate",
    "grain2",
    "DropShadow",
)


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


def _uptime_line() -> str:
    try:
        result = subprocess.run(["uptime"], capture_output=True, text=True, check=False)
    except OSError:
        return "uptime: nem érhető el"
    return result.stdout.strip() or result.stderr.strip() or "uptime: nem érhető el"


def _measure(
    image: np.ndarray,
    effects: tuple[tuple[str, Callable[[np.ndarray], np.ndarray]], ...],
    runs: int,
    warmups: int,
) -> dict[str, dict[str, object]]:
    measured: dict[str, dict[str, object]] = {}
    for name, effect in effects:
        for _ in range(warmups):
            effect(image.copy())
        samples = []
        for _ in range(runs):
            input_image = image.copy()
            started = time.perf_counter()
            effect(input_image)
            samples.append((time.perf_counter() - started) * 1000.0)
        measured[name] = {
            "samples_ms": samples,
            "best_ms": min(samples),
            "median_ms": statistics.median(samples),
        }
    return measured


def _start_worker(
    code_root: Path,
    source: Path,
    effect: str,
    width: int,
    height: int,
):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--code-root",
        str(code_root),
        "--source",
        str(source),
        "--effect",
        effect,
        "--width",
        str(width),
        "--height",
        str(height),
        "--worker",
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    ready = process.stdout.readline().strip() if process.stdout else ""
    if ready != _WORKER_READY:
        stdout = process.stdout.read() if process.stdout else ""
        stderr = process.stderr.read() if process.stderr else ""
        raise RuntimeError(
            f"A {code_root} alatti {effect} mérőfolyamat nem indult el:\n{ready}\n{stdout}\n{stderr}"
        )
    return process


def _worker_request(process: subprocess.Popen[str], request: str) -> dict[str, object]:
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("A benchmark mérőfolyamatának csatornája nem érhető el.")
    process.stdin.write(request + "\n")
    process.stdin.flush()
    line = process.stdout.readline()
    if not line:
        stderr = process.stderr.read() if process.stderr else ""
        raise RuntimeError(f"A benchmark mérőfolyamata leállt: {stderr}")
    result = json.loads(line)
    if "error" in result:
        raise RuntimeError(f"A benchmark mérőfolyamata hibázott: {result['error']}")
    return result


def _stop_worker(process: subprocess.Popen[str]) -> None:
    if process.poll() is None and process.stdin is not None:
        process.stdin.write("quit\n")
        process.stdin.flush()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="RGB-forráskép")
    parser.add_argument("--width", type=int, default=2560, help="kimeneti kép szélessége")
    parser.add_argument("--height", type=int, default=1707, help="kimeneti kép magassága")
    parser.add_argument("--runs", type=int, default=3, help="mért hívások száma effektenként")
    parser.add_argument("--warmups", type=int, default=0, help="nem mért bemelegítő hívások effektenként")
    parser.add_argument("--effect", choices=_EFFECT_NAMES, help="csak ezt az effektet mérje")
    parser.add_argument(
        "--compare-root",
        type=Path,
        help="összehasonlító forrásfa; bemelegítés után mintánként váltja az előtte/utána mérést",
    )
    parser.add_argument("--code-root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.width < 1 or args.height < 1 or args.runs < 1 or args.warmups < 0:
        parser.error("a width, height és runs pozitív, a warmups nemnegatív legyen")
    args.code_root = args.code_root.resolve()
    sys.path.insert(0, str(args.code_root / "src"))
    source = args.source or (args.code_root / "tests/fixtures/golden_colab/forras.jpg")
    if not source.is_file():
        parser.error(f"a forráskép nem található: {source}")

    if args.compare_root:
        before_root = args.compare_root.resolve()
        if not (before_root / "src/picasapy").is_dir():
            parser.error(f"az összehasonlító kódfa nem található: {before_root}")
        names = (args.effect,) if args.effect else _EFFECT_NAMES
        print(f"Forráskép: {source}; méret: {args.width}×{args.height}; futás: {args.runs}; bemelegítés: {args.warmups}")
        print(_system_line())
        print("\n| Effekt | Előtte medián (ms) | Utána medián (ms) | Gyorsulás |")
        print("|---|---:|---:|---:|")
        for name in names:
            before_source = args.source or before_root / "tests/fixtures/golden_colab/forras.jpg"
            before_source = before_source.resolve()
            if not before_source.is_file():
                parser.error(f"az összehasonlító forráskép nem található: {before_source}")
            before_worker = _start_worker(
                before_root, before_source, name, args.width, args.height
            )
            after_worker = _start_worker(
                args.code_root, source.resolve(), name, args.width, args.height
            )
            try:
                for _ in range(args.warmups):
                    _worker_request(before_worker, "warmup")
                    _worker_request(after_worker, "warmup")
                before_samples = []
                after_samples = []
                print(f"# {name} — bemelegítés után; {_uptime_line()}")
                for run in range(args.runs):
                    print(f"# {name} — minta {run + 1}/{args.runs}; {_uptime_line()}")
                    if run % 2 == 0:
                        before_samples.append(float(_worker_request(before_worker, "run")["elapsed_ms"]))
                        after_samples.append(float(_worker_request(after_worker, "run")["elapsed_ms"]))
                    else:
                        after_samples.append(float(_worker_request(after_worker, "run")["elapsed_ms"]))
                        before_samples.append(float(_worker_request(before_worker, "run")["elapsed_ms"]))
                before_median = statistics.median(before_samples)
                after_median = statistics.median(after_samples)
                ratio = before_median / after_median
                print(
                    f"| {name} | {before_median:.1f} | {after_median:.1f} | {ratio:.2f}× |"
                )
            finally:
                _stop_worker(before_worker)
                _stop_worker(after_worker)
        return 0

    image = _load_image(source, args.width, args.height)
    effects = tuple(effect for effect in _effects() if args.effect is None or effect[0] == args.effect)
    if args.worker:
        if len(effects) != 1:
            parser.error("a mérőfolyamat pontosan egy effektet vár")
        effect = effects[0][1]
        print(_WORKER_READY, flush=True)
        for request in sys.stdin:
            operation = request.strip()
            if operation == "quit":
                break
            try:
                if operation == "warmup":
                    effect(image.copy())
                    response = {"warmed": True}
                elif operation == "run":
                    input_image = image.copy()
                    started = time.perf_counter()
                    effect(input_image)
                    response = {"elapsed_ms": (time.perf_counter() - started) * 1000.0}
                else:
                    raise ValueError(f"ismeretlen mérőparancs: {operation}")
            except Exception as exc:  # a szülőfolyamatban jelenik meg a részletes hiba
                response = {"error": f"{type(exc).__name__}: {exc}"}
            print(json.dumps(response, separators=(",", ":")), flush=True)
        return 0

    print(f"Méret: {image.shape[1]}×{image.shape[0]} RGB uint8; futás: {args.runs}; bemelegítés: {args.warmups}")
    print(_system_line())
    print(_uptime_line())
    measured = _measure(image, effects, args.runs, args.warmups)
    print("\n| Effekt | Futások (ms) | Legjobb (ms) | Medián (ms) |")
    print("|---|---:|---:|---:|")
    for name, result in measured.items():
        samples = ", ".join(f"{sample:.1f}" for sample in result["samples_ms"])
        print(f"| {name} | {samples} | {result['best_ms']:.1f} | {result['median_ms']:.1f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
