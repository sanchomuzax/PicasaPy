#!/usr/bin/env python3
"""Mérőszett 3. kör (#643, #685) — a lánc-megszakadás megerősítése.

A #643 kutatói köre a natív kódból már **megfejtette**, hogy egy hibás
bejegyzés nem csak önmagát viszi: a bejáró (`0x00907740`) az első hibánál
kilép a ciklusból, tehát a lánc **hátralévő része sem fut le**. Ez a kör ezt
**méréssel erősíti meg** — és megkülönbözteti a két esetet, amit egyelemű
lánccal nem lehetett szétválasztani.

Minden pár EGY változóban tér el a saját alapesetétől. A `bw` azért jó
jelzőeffekt, mert a mérőkép szürke sávjait nem, a színfoltokat viszont
látványosan megváltoztatja — vagyis egyértelműen látszik, lefutott-e.

Használat:

    python3 tools/golden/make_validation_kit3.py <kimenet_mappa>
"""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from picasapy.ini.filters import parse_filters  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_validation_kit import build_chart  # noqa: E402

#: (fájlnév, lánc, mit dönt el)
CASES: tuple[tuple[str, str, str], ...] = (
    (
        "A_alapeset.jpg",
        "sepia=1;bw=1;",
        "kétlépéses lánc kontrollja: mindkettőnek le kell futnia",
    ),
    (
        "B_ismeretlen_elol.jpg",
        "nincsilyen=1;bw=1;",
        "ismeretlen ELSŐ tag — átjön-e a bw? ha NEM, a lánc megszakad",
    ),
    (
        "C_ismeretlen_hatul.jpg",
        "sepia=1;nincsilyen=1;",
        "ismeretlen UTOLSÓ tag — az előtte lévő sepia megmarad-e?",
    ),
    (
        "D_rossz_parameterszam.jpg",
        "grain2=1,0.500000;bw=1;",
        "rossz paraméterszám — ugyanaz-e a viselkedés, mint az ismeretlen névnél",
    ),
    (
        "E_nincs_egyenlosegjel.jpg",
        "sepia;bw=1;",
        "'=' nélküli tag — a natív kód szerint ez is hibaág (return -1)",
    ),
    (
        "F_csak_bw.jpg",
        "bw=1;",
        "referencia: a bw önmagában, hogy legyen mihez hasonlítani",
    ),
    (
        "G_csak_sepia.jpg",
        "sepia=1;",
        "referencia: a sepia önmagában",
    ),
)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "export").mkdir()

    chart = build_chart()
    ini: list[str] = []
    rows: list[dict[str, str]] = []

    for name, chain, question in CASES:
        # A szándékosan hibás láncok egy részét a SAJÁT parszerünk is elutasítja
        # (pl. a `=` nélküli tagot). Ez nem baj — sőt, eredmény: rögzítjük, és a
        # kiértékelésnél tudni fogjuk, hogy ott a mi oldalunk is elhasal.
        try:
            parse_filters(chain)
            accepted = "elfogadja"
        except ValueError as error:
            accepted = f"ELUTASÍTJA: {error}"
        cv2.imwrite(str(out / name), chart, [cv2.IMWRITE_JPEG_QUALITY, 97])
        ini.append(f"[{name}]\nfilters={chain}\n")
        rows.append(
            {
                "fajl": name,
                "lanc": chain,
                "kerdes": question,
                "sajat_parszer": accepted,
            }
        )

    (out / ".picasa.ini").write_text("\n".join(ini), encoding="utf-8")
    with (out / "fedettseg.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["fajl", "lanc", "kerdes", "sajat_parszer"]
        )
        writer.writeheader()
        writer.writerows(rows)

    (out / "OLVASS-EL.txt").write_text(
        "MÉRŐSZETT — 3. kör (hét kép)\n"
        "=============================\n\n"
        "Ugyanaz a menet, mint eddig:\n"
        "1. Picasa -> Eszközök -> Mappakezelő -> ez a mappa ->\n"
        "   \"Egyszeri átvizsgálás\".\n"
        "2. Ctrl+A, majd Exportálás: eredeti méret, maximális minőség,\n"
        "   az \"export\" almappába.\n\n"
        "Ebben a körben SZÁNDÉKOSAN van néhány hibás beállítás. Az a kérdés,\n"
        "hogy egy hibás sor csak magát rontja-e el, vagy a mögötte lévőket is.\n\n"
        "Ezért itt a VÁLTOZATLAN kép a legfontosabb eredmény: ha valamelyik\n"
        "képen nem történik semmi, azt ne javítsd, ne állítsd át, és ne hagyd\n"
        "ki az exportból.\n",
        encoding="utf-8",
    )

    print(f"3. kör kész: {out} — {len(rows)} kép")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
