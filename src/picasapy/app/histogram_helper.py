"""RGB-hisztogram számítás a szerkesztő-előnézet aktuális képéhez (#25).

A hisztogram a filters-lánccal renderelt ELŐNÉZETI képből számol (nem a
forrásfájlból) — így csúszka-húzás közben is a ténylegesen látott képet
tükrözi. A számítás numpy-vektorizált (np.bincount csatornánként); nagy
képeknél stride-mintavétellel korlátozott a költség, hogy a GUI-szálon
futva se akaszthassa a nézőt (#25 — "ésszerű ritkítás")."""

from __future__ import annotations

import numpy as np

BUCKET_COUNT = 256
# e pixelszám fölött ritkítunk (stride-mintavétel) — a hisztogram ALAKJA
# nagyjából változatlan marad, a számítási idő viszont felülről korlátos
_MAX_SAMPLED_PIXELS = 500_000

# FONTOS (#232): a vödör-listák LISTÁK, nem tuple-ök. A PySide6 a Python
# `list`-et JS-tömbbé alakítja (van `.length`, indexelhető), a `tuple`-t
# viszont olyan objektummá, amin QML-ben `Array.isArray(...)` HAMIS és a
# `.length`/`[i]` nem működik — emiatt a HistogramBox (Canvas és Repeater
# egyaránt) sosem látott adatot, és üresen maradt a görbe (#25/#228 valódi
# gyökéroka). Listával a QML-oldali `histogramData.r[i]` helyesen működik.
EMPTY_HISTOGRAM: dict[str, list[float]] = {
    "r": [0.0] * BUCKET_COUNT,
    "g": [0.0] * BUCKET_COUNT,
    "b": [0.0] * BUCKET_COUNT,
}


def compute_rgb_histogram(
    rgb_array: np.ndarray | None, buckets: int = BUCKET_COUNT
) -> dict[str, list[float]]:
    """RGB uint8 (H, W, 3) tömbből normalizált (0..1) hisztogram csatornánként.

    A `buckets` a 256 intenzitásérték összevonása (256-nak osztójának kell
    lennie); a normalizálás CSATORNÁNKÉNT a saját csúcsértékére történik
    (a Picasa és a legtöbb hisztogram-nézet mintája) — így mindhárom görbe
    kitölti a doboz magasságát, egymástól függetlenül összehasonlítható
    alakkal. Üres/None tömbre, illetve csupa-nulla (fekete) képre mindhárom
    csatorna nulla lista — QML-oldalon ez üres/lapos görbeként jelenik meg."""
    if buckets <= 0 or 256 % buckets != 0:
        raise ValueError(f"A vödörszámnak a 256 osztójának kell lennie: {buckets}")
    if rgb_array is None or rgb_array.size == 0:
        return _empty(buckets)
    if rgb_array.ndim != 3 or rgb_array.shape[2] != 3:
        raise ValueError(f"RGB (H, W, 3) tömb várt, kaptunk: {rgb_array.shape}")

    sample = _subsample(rgb_array)
    fold = 256 // buckets
    raw_counts: dict[str, np.ndarray] = {}
    for index, channel in enumerate(("r", "g", "b")):
        values = np.ascontiguousarray(sample[:, :, index]).reshape(-1)
        hist = np.bincount(values, minlength=256).astype(np.float64)
        if fold > 1:
            hist = hist.reshape(buckets, fold).sum(axis=1)
        raw_counts[channel] = hist

    result = {}
    for channel, hist in raw_counts.items():
        peak = hist.max()
        # lista (nem tuple) — ld. a modul tetején a #232-es magyarázatot
        result[channel] = (
            (hist / peak).tolist() if peak > 0 else [0.0] * len(hist)
        )
    return result


def _empty(buckets: int) -> dict[str, list[float]]:
    return {"r": [0.0] * buckets, "g": [0.0] * buckets, "b": [0.0] * buckets}


def _subsample(rgb_array: np.ndarray) -> np.ndarray:
    """Stride-mintavétel, ha a pixelszám a küszöb fölött van."""
    height, width = rgb_array.shape[:2]
    pixel_count = height * width
    if pixel_count <= _MAX_SAMPLED_PIXELS:
        return rgb_array
    stride = int(np.ceil((pixel_count / _MAX_SAMPLED_PIXELS) ** 0.5))
    return rgb_array[::stride, ::stride]
