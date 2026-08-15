#!/usr/bin/env python3
"""A #687-ben bekötött PONTONKÉNTI szűrők mért görbéinek kivonatolása.

A forrás a #685 mérőszettje: egyetlen mérőkép, effektenként 2–3 csúszkaállás,
és a valódi Picasa 3.9 exportja mindegyikről. A szett képei nem kerülhetnek a
publikus repóba — ez a szkript a képpárokból **együttes hisztogramot** épít,
és csak a GÖRBÉT menti ki (a `scripts/extract_finetune_reference.py` mintája
szerint):

    minden bemeneti szintre (0..255), csatornánként:
        count[v]    — hány képpont volt ezen a szinten (a szett minden
                      esetében UGYANAZ a mérőkép, ezért egyszer tároljuk)
        mean_out[v] — mi lett belőlük átlagosan a Picasa kimenetében

Ebből a fotó nem áll össze vissza, a pontonkénti modellek hibája viszont
kiszámolható — így a kalibráció bekerülhet a publikus tesztkészletbe, és a
konstansok (a `gamma` kitevőjének iránya, a `colortemp` két skálája) nem
csúszhatnak el észrevétlenül.

**Csak pontonkénti eset kerülhet ide.** A `backlight`/`triple*` Derítőfénye a
képpont világosságával súlyoz, tehát nem írja le egyetlen LUT — kivéve a
`triple2` alsó állását, ahol a Derítőfény 0. Az `autocontrast` szintén
kimarad: az ő LUT-ja a forráskép hisztogramjából jön, ami nincs meg a
publikus repóban.

Futtatás (a tulajdonos gépén, ahol a mérőszett megvan):

    python3 scripts/extract_native_filter_reference.py \
        --kit "/mnt/nas/My Pictures/PicasaPy meroszett" \
        --out tests/support/native_filter_reference/measured_luts_687.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import NamedTuple

import numpy as np
from PIL import Image


class Case(NamedTuple):
    """Egy mérési eset: melyik szűrő, milyen csúszkaállásokkal, melyik fájl."""

    name: str
    filter_key: str
    params: tuple[float, ...]
    file: str


#: A pontonkénti mérőesetek. A `params` a mi handlereink csúszka-sorrendjében
#: áll (ld. `picasapy.render.chain_native_handlers`).
CASES: tuple[Case, ...] = (
    Case("contrast_alap", "contrast", (0.1,), "contrast__alap.jpg"),
    Case("contrast_max", "contrast", (0.5,), "contrast__max.jpg"),
    Case("contrast_min", "contrast", (-0.5,), "contrast__min.jpg"),
    Case("gamma_alap", "gamma", (0.1618,), "gamma__alap.jpg"),
    Case("gamma_max", "gamma", (1.0,), "gamma__max.jpg"),
    Case("gamma_min", "gamma", (-1.0,), "gamma__min.jpg"),
    Case("colortemp_alap", "colortemp", (0.125, 0.5), "colortemp__alap.jpg"),
    Case("colortemp_max", "colortemp", (0.5, 1.0), "colortemp__max.jpg"),
    Case("colortemp_min", "colortemp", (-0.5, 0.0), "colortemp__min.jpg"),
    # a Derítőfény itt 0, ezért ez az eset is pontonkénti
    Case("triple2_min", "triple2", (0.0, 0.0, 0.0), "triple2__min.jpg"),
)


def _load(path: Path) -> np.ndarray:
    with Image.open(path) as handle:
        return np.asarray(handle.convert("RGB"))


def _channel_curve(
    source: np.ndarray, target: np.ndarray
) -> tuple[list[float], float]:
    """Egy csatorna együttes hisztogramjából a mért görbe és a JPEG-zaj."""
    flat_in = source.reshape(-1)
    flat_out = target.reshape(-1).astype(np.float64)
    counts = np.bincount(flat_in, minlength=256).astype(np.int64)
    sums = np.bincount(flat_in, weights=flat_out, minlength=256)
    with np.errstate(invalid="ignore", divide="ignore"):
        means = np.where(counts > 0, sums / np.maximum(counts, 1), 0.0)
    noise = float(np.abs(flat_out - means[flat_in]).mean())
    return [round(float(value), 2) for value in means], round(noise, 4)


def _source_counts(source: np.ndarray) -> list[list[int]]:
    return [
        np.bincount(source[..., index].reshape(-1), minlength=256).tolist()
        for index in range(3)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "tests/support/native_filter_reference/measured_luts_687.json"
        ),
    )
    args = parser.parse_args()
    export = args.kit / "export"
    if not export.is_dir():
        raise SystemExit(f"Nincs meg a mérőszett exportja: {export}")

    reference: np.ndarray | None = None
    cases = []
    for case in CASES:
        source = _load(args.kit / case.file)
        target = _load(export / case.file)
        if source.shape != target.shape:
            raise ValueError(f"{case.name}: eltérő méret {source.shape} vs {target.shape}")
        if reference is None:
            reference = source
        elif not np.array_equal(reference, source):
            raise ValueError(
                f"{case.name}: a szett mérőképe eltér a többiétől — a közös "
                "darabszám-tábla nem használható"
            )
        channels = []
        for index in range(3):
            means, noise = _channel_curve(source[..., index], target[..., index])
            channels.append({"mean_out": means, "noise": noise})
        cases.append(
            {
                "name": case.name,
                "filter_key": case.filter_key,
                "params": list(case.params),
                "channels": channels,
            }
        )

    assert reference is not None
    payload = {
        "issue": 687,
        "leiras": (
            "A #687-ben bekötött pontonkénti natív szűrők MÉRT görbéi a #685 "
            "mérőszettjéből (valódi Picasa 3.9-export), együttes "
            "hisztogrammal desztillálva. Előállító: "
            "scripts/extract_native_filter_reference.py"
        ),
        "pixels": int(reference.shape[0] * reference.shape[1]),
        "source_counts": _source_counts(reference),
        "cases": cases,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"{len(cases)} eset kiírva ide: {args.out}")


if __name__ == "__main__":
    main()
