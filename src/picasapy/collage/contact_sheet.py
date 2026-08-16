"""Az Indexkép (`contactsheet`) fejlécének méretei (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.4.

Az Indexkép magyar leírása az eredetiben: „Miniatűr tájékoztató jellegű
fejléccel." A fejléc **két sorból** áll — a felső a `collage/contactsheet/title`,
az alsó a `.../subtitle` erőforrásból, a `CContactSheetTheme::subtitle_format`
mintája szerint. A bélyegképek a fejléc alatt rácsba kerülnek (a rács
`regular_grid`, a térköz `rects`).

A címsor betűmérete:

```c
f = (panelOldalarany > 1.0f) ? 1.0f : 0.75f;
betumeret = round(f * 0.04f * lapMagassag);
```

Jobbról-balra író nyelveken a fejléc tükröződik (`DAT_00d678d4`) — ezt a
`mirror_header()` adja vissza, hogy a rajzoló ne találgasson.

> ⚠️ Ami a specben NINCS meg, ezért itt sem találjuk ki: a két fejlécsor
> közti sorköz és a fejléc teljes magassága. A rajzoló rétegnek ezt egyelőre
> saját tipográfiai döntésként kell megadnia; a betűméret viszont az eredetié.
"""

from __future__ import annotations

from .fitting import picasa_round

# A címsor betűmérete a lap magasságának ekkora hányada.
CONTACT_SHEET_TITLE_RATIO = 0.04

# Keskeny (nem fekvő) panelen ennyivel kisebb a címsor.
NARROW_PANEL_FACTOR = 0.75


def header_font_size(page_height: int, panel_aspect: float) -> int:
    """Az indexkép címsorának betűmérete képpontban.

    `panel_aspect` a megjelenítő PANEL oldalaránya (szélesség/magasság) —
    nem a lapé. A feltétel szigorú `>`, tehát a pontosan négyzetes panel is
    a kisebbik, 0,75-ös ágra esik."""
    if page_height < 1:
        raise ValueError(f"Érvénytelen lapmagasság: {page_height}")
    if panel_aspect <= 0.0:
        raise ValueError(f"Érvénytelen paneloldalarány: {panel_aspect}")
    factor = 1.0 if panel_aspect > 1.0 else NARROW_PANEL_FACTOR
    return picasa_round(factor * CONTACT_SHEET_TITLE_RATIO * page_height)


def mirror_header(right_to_left: bool) -> bool:
    """Igaz, ha a fejlécet tükrözni kell (jobbról-balra író nyelvek)."""
    return bool(right_to_left)


__all__ = [
    "CONTACT_SHEET_TITLE_RATIO",
    "NARROW_PANEL_FACTOR",
    "header_font_size",
    "mirror_header",
]
