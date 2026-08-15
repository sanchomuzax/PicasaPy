#!/usr/bin/env python3
"""A mérőszett kiértékelése (#685): mi működik, mi rosszul, mi sehogy.

A `make_validation_kit.py` szettjéhez tartozik. Minden exportált képre két
kérdést tesz fel:

1. **Csinált-e bármit a Picasa?** (export vs. az érintetlen mérőkép)
2. **Ugyanazt csináltuk-e mi is?** (export vs. a mi renderünk)

A kettőből jön a verdikt. A leglényegesebb az a két eset, amit egy sima
ΔE-szám elrejtene:

* `NEM_IMPLEMENTALT` — a Picasa változtatott, mi nem nyúltunk a képhez;
* `FOLOSLEGES` — a Picasa nem csinált semmit, mi viszont igen.

Futtatás:

    python3 tools/golden/analyze_validation_kit.py <szett_mappa> [--json r.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from picasapy.ini.filters import parse_filters  # noqa: E402
from picasapy.render.chain import apply_filters  # noqa: E402

from compare_render import _read_rgb, delta_e_cie76, ssim  # noqa: E402

#: Amin belül „nem történt semmi" — JPEG-újratömörítés ennyit simán mozdít.
NOOP_DE = 1.0
#: Pixelhűnek tekintett egyezés a Picasa-exporttal.
MATCH_DE = 2.0
#: E fölött a modellünk érdemben mást csinál.
WRONG_DE = 6.0


def load(path: Path) -> np.ndarray | None:
    """RGB uint8 — a renderer RGB-ben dolgozik, a cv2 viszont BGR-t ad.

    Ez nem stílus kérdése: BGR-t átadva a csatornánkénti LUT-ok (warm, sepia)
    felcserélt csatornára futnak, és a mérés pixelpontos effektet is
    „rossz"-nak minősít.
    """
    payload = path.read_bytes() if path.is_file() else None
    if payload is None:
        return None
    try:
        return _read_rgb(path)
    except ValueError:
        return None


def mean_de(first: np.ndarray, second: np.ndarray) -> float:
    if first.shape != second.shape:
        second = cv2.resize(
            second, (first.shape[1], first.shape[0]), interpolation=cv2.INTER_AREA
        )
    return float(delta_e_cie76(first, second).mean())


def classify(de_base: float, de_ours: float, ours_de_base: float) -> str:
    picasa_acted = de_base > NOOP_DE
    we_acted = ours_de_base > NOOP_DE
    if not picasa_acted and not we_acted:
        return "MINDKETTO_TETLEN"
    if picasa_acted and not we_acted:
        return "NEM_IMPLEMENTALT"
    if not picasa_acted and we_acted:
        return "FOLOSLEGES"
    if de_ours <= MATCH_DE:
        return "JO"
    if de_ours <= WRONG_DE:
        return "KOZELITO"
    return "ROSSZ"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", type=Path)
    parser.add_argument("--export", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    kit: Path = args.kit
    export: Path = args.export or (kit / "export")
    with (kit / "fedettseg.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    results = []
    for row in rows:
        source = load(kit / row["fajl"])
        golden = load(export / row["fajl"])
        if source is None or golden is None:
            results.append({**row, "verdikt": "HIANYZO_EXPORT"})
            continue

        try:
            report = apply_filters(source, parse_filters(row["lanc"]))
            ours = report.image
        except Exception as error:  # noqa: BLE001 — a hiba maga az eredmény
            results.append(
                {**row, "verdikt": "RENDER_HIBA", "hiba": str(error)[:200]}
            )
            continue

        results.append(
            {
                **row,
                "verdikt": classify(
                    mean_de(source, golden), mean_de(golden, ours),
                    mean_de(source, ours),
                ),
                "de_picasa_vs_eredeti": round(mean_de(source, golden), 3),
                "de_mienk_vs_picasa": round(mean_de(golden, ours), 3),
                "de_mienk_vs_eredeti": round(mean_de(source, ours), 3),
                "ssim": round(ssim(golden, ours), 4)
                if golden.shape == ours.shape else None,
                "meret_elter": golden.shape != ours.shape,
            }
        )

    order = [
        "HIANYZO_EXPORT", "RENDER_HIBA", "NEM_IMPLEMENTALT", "ROSSZ",
        "FOLOSLEGES", "KOZELITO", "MINDKETTO_TETLEN", "JO",
    ]
    counts = {name: 0 for name in order}
    for row in results:
        counts[row["verdikt"]] = counts.get(row["verdikt"], 0) + 1

    print(f"{len(results)} eset\n")
    for name in order:
        if counts.get(name):
            print(f"  {name:20s} {counts[name]:4d}")
    print()
    for name in ("HIANYZO_EXPORT", "RENDER_HIBA", "NEM_IMPLEMENTALT", "ROSSZ",
                 "FOLOSLEGES"):
        bad = [row for row in results if row["verdikt"] == name]
        if not bad:
            continue
        print(f"--- {name} ---")
        for row in bad:
            extra = row.get("hiba") or (
                f"Picasa Δ={row.get('de_picasa_vs_eredeti')} "
                f"mi Δ={row.get('de_mienk_vs_eredeti')} "
                f"eltérés={row.get('de_mienk_vs_picasa')}"
            )
            print(f"  {row['fajl']:42s} {extra}")
        print()

    if args.json:
        args.json.write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
