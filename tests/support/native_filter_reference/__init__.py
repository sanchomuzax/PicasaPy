"""A #687-ben bekötött pontonkénti natív szűrők MÉRT görbéi (#685-ös szett).

A `measured_luts_687.json` a #685 mérőszettjéből készült
(`scripts/extract_native_filter_reference.py`): szűrőnként és
csúszkaállásonként a bemeneti szintek átlagos KIMENETI szintje a valódi
Picasa 3.9 exportjában, csatornánként. A mérőkép maga nem kerül a publikus
repóba — egy átlaggörbéből kép nem áll össze —, a pontonkénti modellek hibája
viszont pontosan kiszámolható belőle.

Mivel a szett minden esete UGYANARRÓL a mérőképről készült, a szintenkénti
darabszám (a hibaszámítás súlya) egyszer, a fájl tetején szerepel.

A használat mintája a `tests/render/test_native_reference_687.py`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import numpy as np

_DATA_PATH = Path(__file__).with_name("measured_luts_687.json")


class MeasuredCase(NamedTuple):
    """Egy mérési eset: melyik szűrő, milyen csúszkákkal, mit mértünk."""

    name: str
    filter_key: str
    params: tuple[float, ...]
    #: szintenkénti darabszám csatornánként (a hibaszámítás súlya)
    counts: tuple[np.ndarray, np.ndarray, np.ndarray]
    #: szintenkénti átlagos kimeneti szint csatornánként
    mean_out: tuple[np.ndarray, np.ndarray, np.ndarray]
    #: a mérés saját JPEG-zaja csatornánként — a tűrés alsó korlátja
    noise: tuple[float, float, float]

    def weighted_error(self, model_luts: tuple[np.ndarray, ...]) -> float:
        """A modell hibája a MÉRT görbéhez képest, szintenkénti súlyozással.

        `model_luts` a három csatorna 256 elemű LUT-ja. A visszaadott szám a
        csatornákra átlagolt, darabszámmal súlyozott abszolút eltérés a
        0..255-ös skálán.
        """
        errors = []
        for counts, measured, lut in zip(
            self.counts, self.mean_out, model_luts, strict=True
        ):
            total = float(counts.sum())
            if total <= 0.0:
                continue
            deviation = np.abs(np.asarray(lut, dtype=np.float64) - measured)
            errors.append(float((deviation * counts).sum() / total))
        return float(np.mean(errors)) if errors else 0.0

    @property
    def noise_floor(self) -> float:
        """A szett saját JPEG-zaja — ennél pontosabb modell nem mérhető."""
        return float(np.mean(self.noise))


@lru_cache(maxsize=1)
def measured_cases() -> tuple[MeasuredCase, ...]:
    """A mérési esetek betöltése (a JSON egyszer olvasódik be)."""
    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    counts = tuple(
        np.asarray(channel, dtype=np.int64) for channel in payload["source_counts"]
    )
    cases = []
    for entry in payload["cases"]:
        channels = entry["channels"]
        cases.append(
            MeasuredCase(
                name=str(entry["name"]),
                filter_key=str(entry["filter_key"]),
                params=tuple(float(value) for value in entry["params"]),
                counts=counts,  # type: ignore[arg-type]
                mean_out=tuple(  # type: ignore[arg-type]
                    np.asarray(channel["mean_out"], dtype=np.float64)
                    for channel in channels
                ),
                noise=tuple(float(channel["noise"]) for channel in channels),  # type: ignore[arg-type]
            )
        )
    return tuple(cases)


def case_by_name(name: str) -> MeasuredCase:
    """Egy mérési eset a neve alapján."""
    for case in measured_cases():
        if case.name == name:
            return case
    raise KeyError(f"Nincs ilyen mérési eset: {name!r}")


def pointwise_luts(image_op) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Egy PONTONKÉNTI képművelet három csatorna-LUT-ja.

    A műveletet egy 0..255-ös rámpára futtatja, és a kimenetből olvassa ki a
    leképezést — így a modell és a mérés ugyanabban az alakban áll össze.
    """
    ramp = np.repeat(
        np.arange(256, dtype=np.uint8).reshape(1, 256, 1), 3, axis=2
    )
    result = image_op(ramp)
    return tuple(  # type: ignore[return-value]
        result[0, :, channel].astype(np.float64) for channel in range(3)
    )


__all__ = ["MeasuredCase", "case_by_name", "measured_cases", "pointwise_luts"]
