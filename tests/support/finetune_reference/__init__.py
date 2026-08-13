"""A Finomhangolás-csúszkák MÉRT görbéi a valódi Picasa 3.9 kimenetéből (#551).

A `measured_luts.json` a privát `sanchomuzax/picasapy-agent` repó
referencia-képpárjaiból készült (`scripts/extract_finetune_reference.py`):
csúszkaállásonként és csatornánként a bemeneti szintek darabszáma és az
átlagos kimeneti szint. A fotók maguk nem kerülnek a publikus repóba — egy
átlaggörbéből kép nem áll össze —, a pontonkénti modellek hibája viszont
pontosan kiszámolható belőle.

A használat mintája a `tests/render/test_tone_reference_551.py`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import numpy as np

_DATA_PATH = Path(__file__).with_name("measured_luts.json")


class MeasuredCurve(NamedTuple):
    """Egy mérési eset egy csatornájának görbéje."""

    #: szintenkénti képpont-darabszám (súly a hibaszámításhoz)
    counts: np.ndarray
    #: szintenkénti átlagos kimeneti szint
    mean_out: np.ndarray
    #: a kimenetek átlagos abszolút eltérése a saját szintátlaguktól —
    #: gyakorlatilag a JPEG-tömörítés zajszintje, a tűrés alsó korlátja
    noise: float


class MeasuredCase(NamedTuple):
    """Egy mérési eset: melyik vezérlő, milyen paraméterrel, mit mértünk."""

    name: str
    control: str
    param: float
    pixels: int
    channels: tuple[MeasuredCurve, MeasuredCurve, MeasuredCurve]
    #: A szín-varázspálcánál a forrásképből BECSÜLT viszonyítási szín (a
    #: kivonatoláskor rögzítve, mert a fotó nincs a publikus repóban);
    #: a többi vezérlőnél `None`.
    neutral: tuple[int, int, int] | None = None

    def weighted_error(self, model_luts: tuple[np.ndarray, ...]) -> float:
        """A modell hibája a MÉRT görbéhez képest, szintenkénti súlyozással.

        `model_luts` a három csatorna 256 elemű LUT-ja. A visszaadott szám a
        csatornákra átlagolt, darabszámmal súlyozott abszolút eltérés a
        0..255-ös skálán — ugyanaz a mérőszám, amivel a #551 modelljei
        eredetileg is illesztve lettek.
        """
        errors = []
        for curve, lut in zip(self.channels, model_luts, strict=True):
            total = float(curve.counts.sum())
            if total <= 0.0:
                continue
            deviation = np.abs(np.asarray(lut, dtype=np.float64) - curve.mean_out)
            errors.append(float((deviation * curve.counts).sum() / total))
        return float(np.mean(errors)) if errors else 0.0

    @property
    def noise_floor(self) -> float:
        """A készlet saját JPEG-zaja — ennél pontosabb modell nem mérhető."""
        return float(np.mean([curve.noise for curve in self.channels]))


@lru_cache(maxsize=1)
def measured_cases() -> tuple[MeasuredCase, ...]:
    """A mérési esetek betöltése (a JSON egyszer olvasódik be)."""
    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    cases = []
    for entry in payload["cases"]:
        curves = tuple(
            MeasuredCurve(
                counts=np.asarray(channel["counts"], dtype=np.int64),
                mean_out=np.asarray(channel["mean_out"], dtype=np.float64),
                noise=float(channel["noise"]),
            )
            for channel in entry["channels"]
        )
        raw_neutral = entry.get("estimated_neutral")
        cases.append(
            MeasuredCase(
                name=str(entry["name"]),
                control=str(entry["control"]),
                param=float(entry["param"]),
                pixels=int(entry["pixels"]),
                channels=curves,  # type: ignore[arg-type]
                neutral=(
                    None
                    if raw_neutral is None
                    else (
                        int(raw_neutral[0]),
                        int(raw_neutral[1]),
                        int(raw_neutral[2]),
                    )
                ),
            )
        )
    return tuple(cases)


def case_by_name(name: str) -> MeasuredCase:
    """Egy mérési eset a neve alapján."""
    for case in measured_cases():
        if case.name == name:
            return case
    raise KeyError(f"Nincs ilyen mérési eset: {name!r}")


__all__ = ["MeasuredCase", "MeasuredCurve", "case_by_name", "measured_cases"]
