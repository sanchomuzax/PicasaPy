"""A Picasa mintaképes hasonlóságkereső jellemzői és rangsora (#5744).

Az eredeti előállítás helper-szintű képleteit a
`docs/specs/picasa-kereses-modok.md` írja le. A dekódolt BGR képpontokat
használjuk; az ICC/gamma út a specifikációban is nyitott.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import numpy as np

from picasapy.cvimage import dekodolj_forrast
from picasapy.resample import lanczos4_kicsinyites

RGB565Feature: TypeAlias = tuple[int, ...]
HistogramFeature: TypeAlias = tuple[int, ...]
EdgeFeature: TypeAlias = tuple[float, ...]
SimilarityFeatures: TypeAlias = tuple[
    RGB565Feature, HistogramFeature, EdgeFeature
]

DEFAULT_RANK_MAX = 1000
_DESCRIPTOR_SIZES = (56, 32, 16, 8)


@dataclass(frozen=True)
class SimilarityCandidate:
    """Egy fotó jellemzői és rangsoroláshoz használt helyi ideje."""

    key: str
    features: SimilarityFeatures
    time_value: float


def _validate_shape(image: np.ndarray, *, minimum: int) -> None:
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("A hasonlósági jellemzőhöz legalább három csatorna kell.")
    if image.shape[0] < minimum or image.shape[1] < minimum:
        raise ValueError(f"A jellemző bemenete legalább {minimum}×{minimum} képpont.")


def rgb565_feature(image: np.ndarray) -> RGB565Feature:
    """A 8×8 BGR leíró sorfolytonos, kerekítés nélküli RGB565 alakja."""
    _validate_shape(image, minimum=8)
    bgr = image[:8, :8, :3].astype(np.uint16, copy=False)
    blue, green, red = bgr[..., 0], bgr[..., 1], bgr[..., 2]
    values = ((red >> 3) << 11) | ((green >> 2) << 5) | (blue >> 3)
    return tuple(int(value) for value in values.ravel())


def histogram_feature(image: np.ndarray) -> HistogramFeature:
    """A 6×6×6 súlyozott hisztogram 216 normalizált bájtja."""
    _validate_shape(image, minimum=1)
    pixels = image[..., :3].reshape(-1, 3).astype(np.int32, copy=False)
    blue, green, red = pixels[:, 0], pixels[:, 1], pixels[:, 2]

    t0, t1, t2 = 5 * blue, 5 * green, 5 * red
    i0, i1, i2 = t0 >> 8, t1 >> 8, t2 >> 8
    f0, f1, f2 = t0 & 255, t1 & 255, t2 & 255
    c0, c1, c2 = 256 - f0, 256 - f1, 256 - f2
    base = 36 * i2 + 6 * i1 + i0

    target_bins = np.stack(
        (
            base,
            base + 1,
            base + 6,
            base + 7,
            base + 36,
            base + 37,
            base + 36,
            base + 37,
        ),
        axis=1,
    )
    additions = np.stack(
        (
            c2 * c1 * c0,
            c2 * c1 * f0,
            c2 * f1 * c0,
            c2 * f1 * f0,
            f2 * c1 * c0,
            f2 * c1 * f0,
            f2 * f1 * c0,
            f2 * f1 * f0,
        ),
        axis=1,
    ).astype(np.float32, copy=False)

    histogram = np.zeros(216, dtype=np.float32)
    np.add.at(histogram, target_bins.ravel(), additions.ravel())
    maximum = float(histogram.max(initial=0.0))
    denominator = 0.001 if maximum <= 0.001 else math.sqrt(maximum)
    scale = float(np.float32(255.99 / denominator))
    return tuple(
        min(255, max(0, math.trunc(math.sqrt(float(value)) * scale)))
        for value in histogram
    )


def edge_features(image: np.ndarray) -> tuple[float, float]:
    """A descriptor X/Y második különbségének két float32 skalárja."""
    _validate_shape(image, minimum=1)
    pixels = image[..., :3].astype(np.int32, copy=False)
    height, width = pixels.shape[:2]

    if width > 2:
        dx = 2 * pixels[:, 1:-1, :] - pixels[:, :-2, :] - pixels[:, 2:, :]
        sx = int(np.sum(dx.astype(np.int64) ** 2, dtype=np.int64))
        x_value = math.sqrt(sx / ((width - 2) * height * 786432))
    else:
        x_value = 0.0
    if height > 2:
        dy = 2 * pixels[1:-1, :, :] - pixels[:-2, :, :] - pixels[2:, :, :]
        sy = int(np.sum(dy.astype(np.int64) ** 2, dtype=np.int64))
        y_value = math.sqrt(sy / (width * (height - 2) * 786432))
    else:
        y_value = 0.0
    return float(np.float32(x_value)), float(np.float32(y_value))


def _halve_box(image: np.ndarray) -> np.ndarray:
    """A Picasa 2×2 box-előfelezése: egész osztás, lefelé kerekítés."""
    height, width = image.shape[:2]
    half_height, half_width = height // 2, width // 2
    cropped = image[: 2 * half_height, : 2 * half_width, :3]
    blocks = cropped.astype(np.uint16).reshape(
        half_height, 2, half_width, 2, 3
    )
    totals = blocks.sum(axis=(1, 3), dtype=np.uint16)
    return (totals // 4).astype(np.uint8)


def _resample_lanczos4(image: np.ndarray, size: int) -> np.ndarray:
    reduced = image[..., :3]
    while reduced.shape[0] >= 2 * size and reduced.shape[1] >= 2 * size:
        reduced = _halve_box(reduced)
    return lanczos4_kicsinyites(reduced, size, size)


def extract_similarity_features(image: np.ndarray) -> SimilarityFeatures:
    """Egy dekódolt sRGB/BGR képből előállítja mindhárom rekordjellemzőt."""
    leirok = {
        size: _resample_lanczos4(image, size) for size in _DESCRIPTOR_SIZES
    }
    rgb565 = rgb565_feature(leirok[8])
    histogram = histogram_feature(leirok[56])
    edges = tuple(
        value
        for size in _DESCRIPTOR_SIZES
        for value in edge_features(leirok[size])
    )
    return rgb565, histogram, edges


def decode_similarity_features(path: Path) -> SimilarityFeatures | None:
    """Fájlból dekódol és jellemzőket számít; hibás képhez `None` jár."""
    image = dekodolj_forrast(path)
    if image is None:
        return None
    return extract_similarity_features(image)


def rgb565_distance(a: RGB565Feature, b: RGB565Feature) -> float:
    """A 64 RGB565 szó csatornánkénti négyzetes távolságának átlaga."""
    if len(a) != 64 or len(b) != 64:
        raise ValueError("Az RGB565 jellemző pontosan 64 szót tartalmaz.")
    total = 0
    for first, second in zip(a, b, strict=True):
        red = ((first >> 11) & 31) - ((second >> 11) & 31)
        green = ((first >> 5) & 63) - ((second >> 5) & 63)
        blue = (first & 31) - (second & 31)
        total += red * red + green * green + blue * blue
    return total / 64


def histogram_distance(a: HistogramFeature, b: HistogramFeature) -> float:
    """A súlyozott 216 bájtos vektor átlagos négyzetes távolsága."""
    if len(a) != 216 or len(b) != 216:
        raise ValueError("A hisztogramjellemző pontosan 216 bájtot tartalmaz.")
    total = 0
    for index, (first, second) in enumerate(zip(a, b, strict=True)):
        red, green, blue = index // 36, (index // 6) % 6, index % 6
        weight = max(red, green, blue) - min(red, green, blue) + 1
        delta = first - second
        total += weight * delta * delta
    return total / 216


def edge_distance(a: EdgeFeature, b: EdgeFeature) -> float:
    """A nyolc float leíró normalizálatlan négyzetes távolsága."""
    if len(a) != 8 or len(b) != 8:
        raise ValueError("Az éljellemző pontosan nyolc floatot tartalmaz.")
    return sum(
        (first - second) ** 2 for first, second in zip(a, b, strict=True)
    )


def _distances(
    sample: SimilarityFeatures, candidate: SimilarityFeatures
) -> tuple[float, float, float]:
    return (
        rgb565_distance(sample[0], candidate[0]),
        histogram_distance(sample[1], candidate[1]),
        edge_distance(sample[2], candidate[2]),
    )


def similarity_rank_sums(
    sample: SimilarityFeatures,
    candidates: tuple[SimilarityCandidate, ...]
    | list[SimilarityCandidate],
) -> tuple[tuple[str, int], ...]:
    """A három külön rendezés rangpozícióinak összege, növekvő sorrendben."""
    if not candidates:
        return ()
    distances = [_distances(sample, candidate.features) for candidate in candidates]
    ranks = [[0] * len(candidates) for _ in range(3)]
    for component in range(3):
        order = sorted(
            range(len(candidates)), key=lambda index: distances[index][component]
        )
        for rank, index in enumerate(order):
            ranks[component][index] = rank
    totals = [
        sum(ranks[component][i] for component in range(3))
        for i in range(len(candidates))
    ]
    order = sorted(range(len(candidates)), key=lambda index: totals[index])
    return tuple((candidates[index].key, totals[index]) for index in order)


def final_rank_key(r_sim: int, r_time: int) -> int:
    """A Picasa végső kulcsa: `r_sim + 2 × r_time`."""
    return int(r_sim) + 2 * int(r_time)


def rank_similarity_candidates(
    sample: SimilarityFeatures,
    sample_time: float,
    candidates: tuple[SimilarityCandidate, ...] | list[SimilarityCandidate],
    rank_max: int = DEFAULT_RANK_MAX,
) -> tuple[str, ...]:
    """Összerangol, időranggal újrarendez és `RankMax` szerint levág."""
    if not candidates:
        return ()
    similarity_order = similarity_rank_sums(sample, candidates)
    r_sim = {key: rank for rank, (key, _rank_sum) in enumerate(similarity_order)}
    time_order = sorted(
        range(len(candidates)),
        key=lambda index: abs(candidates[index].time_value - sample_time),
    )
    r_time = {
        candidates[index].key: rank for rank, index in enumerate(time_order)
    }
    input_position = {
        candidate.key: index for index, candidate in enumerate(candidates)
    }
    ordered_keys = sorted(
        (candidate.key for candidate in candidates),
        key=lambda key: (final_rank_key(r_sim[key], r_time[key]), input_position[key]),
    )
    return tuple(ordered_keys[: max(0, int(rank_max))])


def pack_similarity_features(
    features: SimilarityFeatures,
) -> tuple[bytes, bytes, bytes]:
    """A három cache-mező little-endian SQLite BLOB alakja."""
    rgb565, histogram, edges = features
    if len(rgb565) != 64 or len(histogram) != 216 or len(edges) != 8:
        raise ValueError("A hasonlósági jellemzők mérete eltér a 380 bájtos rekordtól.")
    return (
        struct.pack("<64H", *rgb565),
        bytes(histogram),
        struct.pack("<8f", *edges),
    )


def unpack_similarity_features(
    rgb565: bytes, histogram: bytes, edges: bytes
) -> SimilarityFeatures:
    """SQLite BLOB-okból visszaállítja a keresőmag bemenetét."""
    return (
        struct.unpack("<64H", rgb565),
        tuple(histogram),
        struct.unpack("<8f", edges),
    )
