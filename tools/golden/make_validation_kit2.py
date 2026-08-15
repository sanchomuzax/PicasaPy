#!/usr/bin/env python3
"""Mérőszett 2. kör (#685) — célzott kísérletek, nem újabb széles sweep.

Az 1. kör megmondta, mi működik. Ez a kör azt tisztázza, amit az 1. kör
**nem tudott eldönteni**, és minden csoportban EGYETLEN változót mozgat.
Ahol két dolgot változtatnánk egyszerre, ott a mérés nem dönt — az 1. körben
pont ezt rontottam el a `Tint=`/`tint=` párnál.

Csoportok:

* **nev** (#689) — csak a szűrőnév írásmódja változik, a paraméterek nem.
* **tintszin** (#679) — csak a hex jegyek száma változik, a szín nem.
* **halott** — az 1. körben az eredeti sem hatott rájuk; itt más
  paraméteralakot próbálunk, mielőtt „halott"-nak könyvelnénk őket.
* **auto** — az automatikák semleges mérőképen joggal tétlenek; itt kapnak
  olyan képet, amin VAN mit javítani (színöntet, szűk tónustartomány).
* **unsharp** — a beégetett 1,5-ös sugár ellenőrzése több erősségen.
* **szemcse** — a `grain2` rejtélye: az eredeti nem hatott, pedig létezik.

Használat:

    python3 tools/golden/make_validation_kit2.py <kimenet_mappa>
"""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from picasapy.ini.filters import parse_filters  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_validation_kit import build_chart  # noqa: E402

#: (csoport, kérdés, alapkép, lánc) — a kérdés a CSV-be kerül, hogy a
#: kiértékelés ne találgassa, mire válaszol az adott kép.
NEUTRAL, CAST = "semleges", "szinontet"


def cast_chart(chart: np.ndarray) -> np.ndarray:
    """Szűk tónustartomány + meleg színöntet: van mit javítani rajta."""
    narrowed = (chart.astype(np.float32) * 0.62 + 44.0)
    narrowed[..., 0] *= 0.88          # kék vissza
    narrowed[..., 2] *= 1.10          # piros fel  (BGR-tömb)
    return np.clip(narrowed, 0, 255).astype(np.uint8)


def cases() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []

    # --- nev (#689): CSAK az írásmód változik ---------------------------
    params = "1,79.842102,ffff"
    for label in ("tint", "Tint", "TINT", "tInT"):
        out.append(
            ("nev", "natív szűrő: számít-e a kis/nagybetű?", NEUTRAL,
             f"{label}={params};")
        )
    vig = "1,35.000000,1.400000,0.000000,00000000"
    for label in ("Vignette", "vignette", "VIGNETTE"):
        out.append(
            ("nev", "Glimmer-szűrő: számít-e a kis/nagybetű?", NEUTRAL,
             f"{label}={vig};")
        )
    for label in ("sepia", "Sepia"):
        out.append(
            ("nev", "paraméter nélküli szűrő írásmódja", NEUTRAL, f"{label}=1;")
        )

    # --- tintszin (#679): CSAK a hex jegyek száma változik --------------
    for hexval in ("ffff", "0000ffff", "00ffff", "000000ffff"):
        out.append(
            ("tintszin", "levágott vezető nullákról van szó?", NEUTRAL,
             f"tint=1,79.842102,{hexval};")
        )
    # kontroll: más szín, hogy lássuk, egyáltalán a színt olvassa-e onnan
    for hexval in ("ff0000", "00ff00", "0000ff"):
        out.append(
            ("tintszin", "kontroll: melyik csatorna melyik hex helyen áll",
             NEUTRAL, f"tint=1,79.842102,{hexval};")
        )

    # --- halott? más paraméteralakkal ----------------------------------
    dead = {
        "blur": ("blur=1;", "blur=1,0.500000;", "blur=1,2.000000;"),
        "colorfix": (
            "colorfix=1;", "colorfix=1,0.250000;",
            "colorfix=1,0.500000,0.500000,0.250000;",
        ),
        "whitept": (
            "whitept=1;", "whitept=1,ffffffff;",
            "whitept=1,0.500000,0.500000,ffc0c0c0;",
        ),
        "triple": ("triple=1;", "triple=1,0.300000,0.200000,0.400000;"),
        "focalpixelate": (
            "focalpixelate=1;",
            "focalpixelate=1,0.500000,0.500000,40.000000,1.000000,0.250000,0.000000;",
        ),
        "PicnikFocalPixelate": (
            "PicnikFocalPixelate=1,0.500000,0.500000,40.000000,60.000000,50.000000,0.000000;",
            "PicnikFocalPixelate=1,40.000000,60.000000,50.000000,0.000000;",
        ),
    }
    for name, chains in dead.items():
        for chain in chains:
            out.append(
                ("halott", f"{name}: tényleg nem csinál semmit?", NEUTRAL, chain)
            )

    # --- auto: olyan kép, amin VAN mit javítani ------------------------
    for chain in (
        "autocolor=1;", "autolight=1;", "autocontrast=1;", "enhance=1;",
        "autobacklight=1;", "backlight=1,0.500000;", "fill=1,0.400000;",
    ):
        out.append(
            ("auto", "színöntetes, szűk tónusú képen is tétlen?", CAST, chain)
        )
    out.append(("auto", "kontroll ugyanez semlegesen", NEUTRAL, "autocolor=1;"))

    # --- unsharp: a beégetett 1,5-ös sugár ellenőrzése -----------------
    for amount in ("0.200000", "0.600000", "1.000000"):
        out.append(
            ("unsharp", "a sugár tényleg fix 1,5, csak az erősség változik?",
             NEUTRAL, f"unsharp=1,{amount};")
        )
    for amount in ("1.500000", "3.000000"):
        out.append(
            ("unsharp", "unsharp2 felső tartománya ugyanaz a mag?", NEUTRAL,
             f"unsharp2=1,{amount};")
        )

    # --- szemcse: miért volt tétlen a grain2? --------------------------
    for chain in ("grain=1;", "grain2=1;", "grain2=1,0.500000;",
                  "PicnikGrain=1,30.000000,0;"):
        out.append(("szemcse", "melyik szemcse-alak hat egyáltalán?",
                    NEUTRAL, chain))
    out.append(
        ("szemcse", "kétszer egymás után: azonos-e a zajminta?", NEUTRAL,
         "grain=1;grain=1;")
    )
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "export").mkdir()

    charts = {NEUTRAL: build_chart()}
    charts[CAST] = cast_chart(charts[NEUTRAL])

    ini: list[str] = []
    coverage: list[dict[str, str]] = []
    counters: dict[str, int] = {}

    for group, question, chart_key, chain in cases():
        parse_filters(chain)  # elírt lánc miatt ne kapjunk hamis verdiktet
        counters[group] = counters.get(group, 0) + 1
        name = f"{group}_{counters[group]:02d}.jpg"
        cv2.imwrite(
            str(out / name), charts[chart_key], [cv2.IMWRITE_JPEG_QUALITY, 97]
        )
        ini.append(f"[{name}]\nfilters={chain}\n")
        coverage.append(
            {
                "csoport": group,
                "kerdes": question,
                "alapkep": chart_key,
                "fajl": name,
                "lanc": chain,
            }
        )

    (out / ".picasa.ini").write_text("\n".join(ini), encoding="utf-8")
    with (out / "fedettseg.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["csoport", "kerdes", "alapkep", "fajl", "lanc"]
        )
        writer.writeheader()
        writer.writerows(coverage)

    (out / "OLVASS-EL.txt").write_text(
        "MÉRŐSZETT — 2. kör\n"
        "===================\n\n"
        f"{len(coverage)} kép, ugyanaz a menet, mint az elsőnél.\n\n"
        "1. Picasa -> Eszközök -> Mappakezelő -> ez a mappa ->\n"
        "   \"Egyszeri átvizsgálás\".\n"
        "2. Ctrl+A, majd Exportálás: eredeti méret, maximális minőség,\n"
        "   az \"export\" almappába.\n\n"
        "Ez a kör kevés képből áll, de mindegyik egy konkrét kérdésre felel.\n"
        "Ezért fontos: ha egy kép VÁLTOZATLAN marad, az is válasz — ne\n"
        "javítsd, ne állítsd át, ne hagyd ki.\n\n"
        "Kétféle alapkép van benne: a semleges mérőkép, és egy szándékosan\n"
        "fakó, melegre húzott változat. Ez utóbbi az automatikus javításoké\n"
        "(Nagyítás, Fényerő, Színek) — azoknak kell legyen mit javítaniuk.\n",
        encoding="utf-8",
    )

    print(f"2. kör kész: {out} — {len(coverage)} kép")
    for group, count in sorted(counters.items()):
        print(f"  {group:10s} {count:3d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
