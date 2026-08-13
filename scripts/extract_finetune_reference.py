#!/usr/bin/env python3
"""A Finomhangolás-csúszkák MÉRT LUT-jainak kivonatolása (#551).

A referencia-képpárok (eredeti + a valódi Picasa 3.9 kimenete) a privát
`sanchomuzax/picasapy-agent` repóban élnek, fotók — a publikus repóba nem
kerülhetnek. Ez a szkript a képpárokból **együttes hisztogramot** épít, és
abból csak a GÖRBÉT menti ki:

    minden bemeneti szintre (0..255), csatornánként:
        count[v]    — hány képpont volt ezen a szinten
        mean_out[v] — mi lett belőlük átlagosan

Ez a fotó tartalmát nem őrzi meg (egy szintből visszafelé nem áll össze kép),
viszont a pontonkénti (LUT-jellegű) modellek hibája belőle **ingyen**
kiszámolható — így a mérés bekerülhet a publikus tesztkészletbe.

A Derítőfény szándékosan hiányzik: az nem pontonkénti művelet (a natív mag a
képpont világosságával súlyoz, ld. #575), ezért egyetlen LUT nem írja le.

Futtatás (a tulajdonos gépén, ahol a privát repó megvan):

    python3 scripts/extract_finetune_reference.py \
        --ref ~/picasapy-agent/referencia \
        --out tests/support/finetune_reference/measured_luts.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterator, NamedTuple

import numpy as np
from PIL import Image

from picasapy.render.tone import estimate_neutral_color


class Case(NamedTuple):
    """Egy mérési eset: melyik vezérlő, milyen paraméterrel, melyik képpár."""

    name: str
    control: str
    param: float
    source: str
    target: str


#: A mérési esetek. A `param` a mi modellünk paramétere abban a mértékben,
#: ahogy a `picasapy.render.tone` várja (a csúszkaállás átszámítva).
CASES: tuple[Case, ...] = (
    # Kiemelések / Árnyékok: a `filterdesc.xml` szerint [0..0.48]; a „mid"
    # csúszkaállás a mérésből 0,24-nek adódott.
    Case("kiemelesek_mid", "highlights", 0.24,
         "finomhangolas/original.jpg", "finomhangolas/kiemelések mid.jpg"),
    Case("kiemelesek_max", "highlights", 0.48,
         "finomhangolas/original.jpg", "finomhangolas/kiemelések max.jpg"),
    Case("arnyekok_mid", "shadows", 0.24,
         "finomhangolas/original.jpg", "finomhangolas/árnyékok mid.jpg"),
    Case("arnyekok_max", "shadows", 0.48,
         "finomhangolas/original.jpg", "finomhangolas/árnyékok max.jpg"),
    # Színhőmérséklet: a csúszka 0..100%-a, az 50% a semleges kiindulás.
    Case("szinho_0", "temperature", -1.0,
         "szinhomerseklet/percent 50.jpg", "szinhomerseklet/percent 0.jpg"),
    Case("szinho_10", "temperature", -0.8,
         "szinhomerseklet/percent 50.jpg", "szinhomerseklet/percent 10.jpg"),
    Case("szinho_25", "temperature", -0.5,
         "szinhomerseklet/percent 50.jpg", "szinhomerseklet/percent 25.jpg"),
    Case("szinho_75", "temperature", 0.5,
         "szinhomerseklet/percent 50.jpg", "szinhomerseklet/percent 75.jpg"),
    Case("szinho_90", "temperature", 0.8,
         "szinhomerseklet/percent 50.jpg", "szinhomerseklet/percent 90.jpg"),
    Case("szinho_100", "temperature", 1.0,
         "szinhomerseklet/percent 50.jpg", "szinhomerseklet/percent 100.jpg"),
    # Szín-varázspálca: a p4 semleges színt a program választja (a `param`
    # itt nem használt — a modell a forrásképből becsüli).
    Case("szinpalca", "color_wand", 0.0,
         "varazspalcak/original.jpg", "varazspalcak/egy gombnyomásos javítás a színhez.jpg"),
)


def _load(path: Path) -> np.ndarray:
    with Image.open(path) as handle:
        return np.asarray(handle.convert("RGB"))


def _channel_curve(
    source: np.ndarray, target: np.ndarray
) -> tuple[list[int], list[float], float]:
    """Egy csatorna együttes hisztogramjából a mért görbe.

    Visszaad: szintenkénti darabszám, szintenkénti átlagos kimenet, és a
    JPEG-zaj szintje (a kimenetek átlagos abszolút szórása a saját szintjük
    átlaga körül) — ez utóbbi a tűrés értelmezéséhez kell.
    """
    flat_in = source.reshape(-1)
    flat_out = target.reshape(-1).astype(np.float64)
    counts = np.bincount(flat_in, minlength=256).astype(np.int64)
    sums = np.bincount(flat_in, weights=flat_out, minlength=256)
    with np.errstate(invalid="ignore", divide="ignore"):
        means = np.where(counts > 0, sums / np.maximum(counts, 1), 0.0)
    noise = float(np.abs(flat_out - means[flat_in]).mean())
    return (
        counts.tolist(),
        [round(float(value), 2) for value in means],
        round(noise, 4),
    )


def _iter_cases(ref_root: Path) -> Iterator[dict[str, object]]:
    for case in CASES:
        source_path = ref_root / case.source
        target_path = ref_root / case.target
        if not source_path.exists() or not target_path.exists():
            raise FileNotFoundError(
                f"Hiányzó referencia-kép a(z) {case.name!r} esethez: "
                f"{source_path if not source_path.exists() else target_path}"
            )
        source = _load(source_path)
        target = _load(target_path)
        if source.shape != target.shape:
            raise ValueError(
                f"A(z) {case.name!r} képpár mérete eltér: "
                f"{source.shape} vs {target.shape}"
            )
        channels = []
        for index in range(3):
            counts, means, noise = _channel_curve(
                source[..., index], target[..., index]
            )
            channels.append({"counts": counts, "mean_out": means, "noise": noise})
        entry: dict[str, object] = {
            "name": case.name,
            "control": case.control,
            "param": case.param,
            "source": case.source,
            "target": case.target,
            "pixels": int(source.shape[0] * source.shape[1]),
            "channels": channels,
        }
        if case.control == "color_wand":
            # A szín-varázspálca a viszonyítási színt a FORRÁSKÉPBŐL becsüli,
            # az pedig nincs meg a publikus repóban. A becslés eredményét
            # ezért ide mentjük — így a teszt a pálca teljes hatásláncát
            # (becsült szín → csatorna-erősítés) veti össze a méréssel.
            entry["estimated_neutral"] = list(estimate_neutral_color(source))
        yield entry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref",
        type=Path,
        default=Path.home() / "picasapy-agent" / "referencia",
        help="a privát repó referencia-mappája",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("tests/support/finetune_reference/measured_luts.json"),
        help="a kimeneti JSON útvonala",
    )
    args = parser.parse_args()

    if not args.ref.is_dir():
        raise SystemExit(
            f"Nincs meg a referencia-mappa: {args.ref}\n"
            "Ehhez a privát sanchomuzax/picasapy-agent repó klónja kell."
        )

    payload = {
        "issue": 551,
        "leiras": (
            "A Finomhangolás pontonkénti vezérlőinek MÉRT görbéi a valódi "
            "Picasa 3.9 kimenetéből, együttes hisztogrammal desztillálva. "
            "Előállító: scripts/extract_finetune_reference.py"
        ),
        "cases": list(_iter_cases(args.ref)),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"{len(payload['cases'])} eset kiírva ide: {args.out}")


if __name__ == "__main__":
    main()
