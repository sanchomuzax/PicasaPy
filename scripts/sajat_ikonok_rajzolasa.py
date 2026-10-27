#!/usr/bin/env python3
"""A PicasaPy saját rajzolású raszteres képeinek előállítója (#6068).

Két kép készül innen, hogy a forrásuk a repóban ellenőrizhető legyen, és
egyik se az eredeti Picasa erőforrásaiból származzon:

- ``straighten_grid.png``: a Kiegyenesítés 44×44-es rácscsempéje (#3924).
  Szaggatott, 1 képpontos fehér vonal (3 képpont vonal, 2 képpont szünet)
  jobbra-lefelé eltolt, 1 képpontos sötét árnyékkal;
- ``loading_icon.png``: a Helyek térképének betöltésjelzője (#5275), egy
  hajtogatott térkép tűvel, 64×52-ben.

Használat:
    python scripts/sajat_ikonok_rajzolasa.py [célmappa]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ALAP_CEL = Path(__file__).resolve().parents[1] / "src/picasapy/app/assets/tools"

CSEMPE = 44
VONAL = 41
VONAL_SZIN = (255, 255, 255, 128)
ARNYEK_SZIN = (0, 0, 0, 77)
SZAKASZ = 5
LATHATO = 3
KEZDET = VONAL + 1


def _szaggatott(i: int, eltolas: int) -> bool:
    """Igaz, ha az i-edik képpont a szaggatott vonal látható részére esik.

    A 44 nem osztható 5-tel, ezért a szaggatás a csempe szélén körbefut: a
    minta a kereszteződés utáni képponttól indul, így a csempék illesztésénél
    a vonal folytonos ritmusú marad.
    """
    return ((i - KEZDET - eltolas) % CSEMPE) % SZAKASZ < LATHATO


def racscsempe() -> Image.Image:
    """A Kiegyenesítés rácscsempéje: egy függőleges és egy vízszintes vonal."""
    kep = Image.new("RGBA", (CSEMPE, CSEMPE), (0, 0, 0, 0))
    px = kep.load()
    # Előbb az árnyék (egy képponttal jobbra-lefelé), utána a vonal, hogy a
    # kereszteződésben a fehér maradjon felül.
    for i in range(CSEMPE):
        if _szaggatott(i, 1):
            px[VONAL + 1, i] = ARNYEK_SZIN
            px[i, VONAL + 1] = ARNYEK_SZIN
    for i in range(CSEMPE):
        if _szaggatott(i, 0):
            px[VONAL, i] = VONAL_SZIN
            px[i, VONAL] = VONAL_SZIN
    return kep


NAGYITAS = 4
IKON = (64, 52)


def _p(pontok: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(x * NAGYITAS, y * NAGYITAS) for x, y in pontok]


def terkep_ikon() -> Image.Image:
    """Hajtogatott, háromrészes térkép egy piros tűvel, 64×52-ben."""
    w, h = IKON
    nagy = Image.new("RGBA", (w * NAGYITAS, h * NAGYITAS), (0, 0, 0, 0))
    rajz = ImageDraw.Draw(nagy)
    # A három hajtás: bal és jobb panel feljebb, a középső lejjebb ül.
    panelek = [
        ([(1, 6), (21, 1), (21, 46), (1, 51)], (126, 184, 92, 255)),
        ([(21, 1), (43, 7), (43, 51), (21, 46)], (246, 206, 92, 255)),
        ([(43, 7), (63, 1), (63, 46), (43, 51)], (92, 156, 220, 255)),
    ]
    for pontok, szin in panelek:
        rajz.polygon(_p(pontok), fill=szin, outline=(255, 255, 255, 255),
                     width=2 * NAGYITAS // 2)
    # A középső panel árnyékos hajtása mélységet ad.
    rajz.polygon(_p([(21, 1), (25, 2.1), (25, 47.1), (21, 46)]),
                 fill=(214, 172, 66, 255))
    # Folyó a jobb panelen és út a bal paneltől a középsőig.
    rajz.line(_p([(46, 14), (50, 24), (47, 34), (55, 46)]),
              fill=(60, 116, 190, 255), width=2 * NAGYITAS)
    rajz.line(_p([(6, 38), (14, 30), (24, 32), (34, 22), (41, 26)]),
              fill=(255, 255, 255, 255), width=2 * NAGYITAS)
    # A tű: kör fejjel és lefelé keskenyedő szárral.
    tu_x, tu_y = 32, 30
    rajz.polygon(_p([(tu_x - 4, tu_y - 8), (tu_x + 4, tu_y - 8), (tu_x, tu_y + 4)]),
                 fill=(208, 36, 36, 255))
    rajz.ellipse(_p([(tu_x - 6, tu_y - 18), (tu_x + 6, tu_y - 6)]),
                 fill=(224, 48, 44, 255), outline=(150, 20, 20, 255),
                 width=NAGYITAS)
    rajz.ellipse(_p([(tu_x - 2, tu_y - 14), (tu_x + 2, tu_y - 10)]),
                 fill=(255, 255, 255, 255))
    return nagy.resize(IKON, Image.Resampling.LANCZOS)


def main(argv: list[str]) -> int:
    cel = Path(argv[1]) if len(argv) > 1 else ALAP_CEL
    cel.mkdir(parents=True, exist_ok=True)
    racscsempe().save(cel / "straighten_grid.png", optimize=True)
    terkep_ikon().save(cel / "loading_icon.png", optimize=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
