#!/usr/bin/env python3
"""Mérőszett (#685) — EGYETLEN mappa, EGYETLEN export, minden effekt.

Célja nem a felfedezés, hanem a **tényfelvétel**: melyik effekt működik,
melyik működik rosszul, és melyikre kell még kutatás. Ezért minden effektre
kevés, de jól választott eset kerül bele (alapérték + szélsőértékek), egyetlen
kombinált alapképen, hogy a tónus, a szín és az élesség/zaj ugyanazon a képen
mérhető legyen.

A szett a `docs/specs/filterdesc-registry.md` **kanonikus írásmódját** hozza
(pl. `Vignette`, `PicnikGrain`), mert az eredeti Picasa a saját alakját várja;
kisbetűs kulcsnévvel néma „nem történt semmi" jönne, és azt tévesen
„nem működik"-nek olvasnánk.

Minden generált lánc átmegy a saját `parse_filters`-ünkön, mielőtt az ini-be
kerül — elírt lánc miatt nem kaphatunk hamis verdiktet.

Használat:

    python3 tools/golden/make_validation_kit.py <kimenet_mappa>
"""
from __future__ import annotations

import csv
import math
import re
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from picasapy.ini.filters import parse_filters  # noqa: E402
from picasapy.render.registry import FILTER_REGISTRY  # noqa: E402

REGISTRY_DOC = (
    Path(__file__).resolve().parents[2] / "docs/specs/filterdesc-registry.md"
)

#: Nem renderelő bejegyzések: nem effektek, nincs mit mérni rajtuk.
SKIP = frozenset(
    {
        "save", "crop", "crop64", "rot", "redeye", "retouch", "picnik",
        "moviestart", "movieend", "debug", "rainbow",
    }
)

#: Ahol a regiszter felső határa végtelen, ott képarányhoz kötött érték jön.
INF_MAX = {
    "border": {2: 40.0, 3: 60.0},
    "focalzoom": {1: 200.0},
    "picnikfocalpixelate": {1: 200.0},
    "roundededges": {0: 60.0},
}

#: Alfa + jól látható meleg narancs — a semleges fehérnél árulkodóbb.
COLOR_HEX = "ffcc6633"

CHART_W, CHART_H = 960, 640


def canonical_names() -> dict[str, str]:
    """Kulcs -> a Picasa saját írásmódja, a specifikáció táblájából."""
    text = REGISTRY_DOC.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for match in re.finditer(r"^\| `([A-Za-z_0-9]+)` \|", text, re.M):
        found.setdefault(match.group(1).casefold(), match.group(1))
    return found


def build_chart() -> np.ndarray:
    """Kombinált mérőkép: rámpa + színfoltok + finom részlet, egy képen."""
    img = np.zeros((CHART_H, CHART_W, 3), np.uint8)

    # 1. sáv: szürke rámpa (tónusgörbe, fill, contrast, gamma…)
    ramp = np.linspace(0, 255, CHART_W).astype(np.uint8)
    img[0:160] = np.tile(ramp, (160, 1))[..., None]

    # 2. sáv: színfoltok (telítettség, színezés, színhő…)
    patches = [
        (200, 40, 40), (40, 180, 60), (40, 60, 200), (220, 200, 40),
        (200, 40, 190), (40, 200, 210), (235, 235, 235), (25, 25, 25),
        (225, 180, 150), (150, 110, 80), (120, 120, 120), (180, 180, 180),
    ]
    step = CHART_W // len(patches)
    for i, (red, green, blue) in enumerate(patches):
        img[160:320, i * step:(i + 1) * step] = (blue, green, red)

    # 3. sáv: finom részlet (élesítés, elmosás, szemcse, glow…)
    detail = np.zeros((160, CHART_W), np.uint8)
    for x in range(CHART_W):
        period = 2 + (x * 22) // CHART_W
        detail[:, x] = 235 if (x // period) % 2 == 0 else 25
    img[320:480] = detail[..., None]

    # 4. sáv: lágy átmenetek + élek (vignetta, sugaras/irányított család)
    yy, xx = np.mgrid[0:160, 0:CHART_W]
    radial = 255 - np.hypot(
        (xx - CHART_W / 2) / (CHART_W / 2), (yy - 80) / 80
    ) * 160
    img[480:640] = np.clip(radial, 0, 255).astype(np.uint8)[..., None]
    img[480:640, CHART_W // 2 - 3:CHART_W // 2 + 3] = 255
    return img


def slider_values(key: str, spec) -> list[tuple[str, list[float]]]:
    """Esetek: alapérték, felső szélsőérték, és ha értelmes, alsó is."""
    if not spec.sliders:
        return [("alap", [])]

    def bounded(index: int, value: float) -> float:
        if math.isinf(value):
            return INF_MAX.get(key, {}).get(index, 50.0)
        return value

    lows, defaults, highs = [], [], []
    for slider in spec.sliders:
        low = bounded(slider.index, slider.minimum)
        high = bounded(slider.index, slider.maximum)
        mid = slider.default
        if mid is None:
            mid = (low + high) / 2
        lows.append(low)
        defaults.append(mid)
        highs.append(high)

    cases = [("alap", defaults), ("max", highs)]
    if any(low < 0 for low in lows) or lows != defaults:
        cases.append(("min", lows))
    return cases


HEX_SLOT = re.compile(r"^[0-9a-fA-F]{8}$")

#: Ahol a doksi/tesztek VALÓDI Picasa-láncot őriznek, azt a sablont követjük —
#: a paraméterek számát és a nem-csúszka rekeszeket (szín, jelölőnégyzet) is.
#: Erre azért van szükség, mert a Glimmer-effektek a `FILTER_REGISTRY`-ben
#: nyilvántartott csúszkákon FELÜL is hordoznak rekeszeket: a `Border` például
#: hatot vár (`20,5,0,00000000,00ffffff,0`), nem négyet. Regiszterből generálva
#: néma „nem történt semmi" jönne, amit tévesen „nem működik"-nek olvasnánk.
KNOWN_CHAINS = "docs/specs", "tests", "tools"


def harvest_templates(repo_root: Path) -> dict[str, list[str]]:
    """Kulcs -> valódi lánc paraméterlistája a leghosszabb talált mintából."""
    pattern = re.compile(r"\b([A-Za-z_][A-Za-z_0-9]*)=1((?:,[0-9a-fA-F.eE+-]+)*);")
    best: dict[str, list[str]] = {}
    for folder in KNOWN_CHAINS:
        for path in (repo_root / folder).rglob("*"):
            if not path.is_file() or path.suffix not in (".md", ".py", ".txt", ".ini"):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in pattern.finditer(text):
                params = [p for p in match.group(2).split(",") if p]
                key = match.group(1).casefold()
                if key not in best or len(params) > len(best[key]):
                    best[key] = params
    return best


def chain_for(
    key: str, wire: str, spec, values: list[float], template: list[str] | None
) -> tuple[str, str]:
    """A lánc és a megbízhatósága (`mintabol` vagy `regiszterbol`)."""
    if template is not None:
        params = list(template)
        numeric = [i for i, p in enumerate(params) if not HEX_SLOT.match(p)]
        if spec.has_puck and len(numeric) >= 2:
            params[numeric[0]] = "0.500000"
            params[numeric[1]] = "0.500000"
            numeric = numeric[2:]
        for slot, value in zip(numeric, values):
            # A jelölőnégyzet-rekeszek egészként szerializálódnak — ne törjük el.
            params[slot] = (
                str(int(value)) if "." not in params[slot] else f"{value:.6f}"
            )
        return f"{wire}=1,{','.join(params)};", "mintabol"

    params = ["1"]
    if spec.has_puck:
        params += ["0.500000", "0.500000"]
    params += [f"{value:.6f}" for value in values]
    if spec.color_kind != "none":
        params.append(COLOR_HEX)
    return f"{wire}={','.join(params)};", "regiszterbol"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    wire_names = canonical_names()
    templates = harvest_templates(Path(__file__).resolve().parents[2])
    chart = build_chart()
    base = out / "_alapkep.png"
    cv2.imwrite(str(base), chart)

    ini_lines: list[str] = []
    coverage: list[dict[str, str]] = []
    invalid: list[str] = []

    for key, spec in sorted(FILTER_REGISTRY.items()):
        if key in SKIP:
            continue
        wire = wire_names.get(key, key)
        seen: set[str] = set()
        for case, values in slider_values(key, spec):
            chain, confidence = chain_for(
                key, wire, spec, values, templates.get(key)
            )
            try:
                parse_filters(chain)
            except ValueError as error:  # a saját parszerünk elutasítja
                invalid.append(f"{key}/{case}: {chain} -> {error}")
                continue
            if chain in seen:
                continue  # rejtett csúszkánál az esetek egybeeshetnek
            seen.add(chain)
            name = f"{key}__{case}.jpg"
            cv2.imwrite(
                str(out / name), chart, [cv2.IMWRITE_JPEG_QUALITY, 97]
            )
            ini_lines.append(f"[{name}]\nfilters={chain}\n")
            coverage.append(
                {
                    "effekt": key,
                    "picasa_nev": wire,
                    "eset": case,
                    "fajl": name,
                    "lanc": chain,
                    "megbizhatosag": confidence,
                    "csuszkak": " | ".join(
                        f"{s.label}={v:.6f}"
                        for s, v in zip(spec.sliders, values)
                    ),
                }
            )

    # A `tint` négyjegyű színe (#679): két kép, ami CSAK a jegyek számában tér el.
    for case, hexval in (("hex4", "ffff"), ("hex8", "0000ffff")):
        name = f"tint__{case}.jpg"
        chain = f"Tint=1,79.842102,{hexval};"
        parse_filters(chain)
        cv2.imwrite(str(out / name), chart, [cv2.IMWRITE_JPEG_QUALITY, 97])
        ini_lines.append(f"[{name}]\nfilters={chain}\n")
        coverage.append(
            {
                "effekt": "tint",
                "picasa_nev": "Tint",
                "eset": case,
                "fajl": name,
                "lanc": chain,
                "megbizhatosag": "mintabol",
                "csuszkak": "#679: azonos szin, elteroszamu hex jegy",
            }
        )

    base.unlink()
    (out / ".picasa.ini").write_text("\n".join(ini_lines), encoding="utf-8")

    with (out / "fedettseg.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "effekt", "picasa_nev", "eset", "fajl", "lanc",
                "megbizhatosag", "csuszkak",
            ],
        )
        writer.writeheader()
        writer.writerows(coverage)

    (out / "OLVASS-EL.txt").write_text(
        "MÉRŐSZETT — egyetlen exportálás\n"
        "================================\n\n"
        f"Ebben a mappában {len(coverage)} kép van. Mindegyik ugyanaz a\n"
        "mérőkép, de mindegyikre más beállítás van beírva. A Picasa ezeket\n"
        "magától felismeri, amikor megnyitod a mappát.\n\n"
        "Mit kell csinálni:\n\n"
        "1. Nyisd meg a Picasát.\n"
        "2. Mappa hozzáadása: Eszközök -> Mappakezelő -> keresd meg ezt a\n"
        "   mappát -> \"Egyszeri átvizsgálás\".\n"
        "3. Várd meg, amíg a képek megjelennek. A bélyegképeken már látszania\n"
        "   kell a hatásoknak — ha valamelyik kép változatlan, az is\n"
        "   eredmény, ne javítsd.\n"
        "4. Kattints a mappára, majd Ctrl+A (mindet kijelöli).\n"
        "5. Exportálás gomb. Beállítás: eredeti méret, maximális minőség.\n"
        "6. Az exportált mappát másold vissza ide a NAS-ra.\n\n"
        "Ne nevezd át a fájlokat — a nevük mondja meg, melyik beállítás volt.\n"
        "Ha egy képnél a Picasa hibát jelez, hagyd ki és menj tovább.\n",
        encoding="utf-8",
    )

    print(f"Mérőszett kész: {out}")
    generated = sum(1 for row in coverage if row["megbizhatosag"] == "regiszterbol")
    print(f"  kép: {len(coverage)}   effekt: "
          f"{len({row['effekt'] for row in coverage})}")
    print(f"  valódi mintából: {len(coverage) - generated}   "
          f"regiszterből generált: {generated}")
    if invalid:
        print(f"  FIGYELEM, kihagyott lánc ({len(invalid)}):")
        for line in invalid:
            print(f"    {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
