"""Az Indexkép (`contactsheet`) fejlécének tartalma és méretei (#431/#1273).

Forrás: `docs/specs/picasa-create-features.md` 1.9.4.

Az Indexkép magyar leírása az eredetiben: „Miniatűr tájékoztató jellegű
fejléccel." A fejléc **két sorból** áll — a felső az album címe, az alsó a
képszám és az album dátuma a `CContactSheetTheme::subtitle_format` mintája
szerint. A `collage/contactsheet/title` és `.../subtitle` a két rajzolt
szövegcsomópont neve, nem fordítási kulcs. A bélyegképek a fejléc alatt,
margós-hézagos rácsba kerülnek.

A címsor betűmérete:

```c
f = (panelOldalarany > 1.0f) ? 1.0f : 0.75f;
betumeret = round(f * 0.04f * lapMagassag);
```

Jobbról-balra író nyelveken a fejléc tükröződik (`DAT_00d678d4`) — ezt a
`mirror_header()` adja vissza, hogy a rajzoló ne találgasson.

> ⚠️ Ami továbbra sincs azonosítva: a pontos betűcsalád. A tartalom, a két
> betűméret, a sorok helye, a 15%-os fejléctér és az adaptív szín a
> dekompilált rajzolóból és az `AI6` képből igazolt.
"""

from __future__ import annotations

from .fitting import picasa_round

# A címsor betűmérete a lap magasságának ekkora hányada.
CONTACT_SHEET_TITLE_RATIO = 0.04

# Keskeny (nem fekvő) panelen ennyivel kisebb a címsor.
NARROW_PANEL_FACTOR = 0.75

# A dekompilált `CContactSheetTheme` a képeket a lap 15%-ánál kezdi. A cím
# ezen belül 45%-nál, az alcím pedig még `f * 4,5%`-kal lejjebb indul.
CONTACT_SHEET_HEADER_RATIO = 0.15
CONTACT_SHEET_LEFT_RATIO = 0.06
CONTACT_SHEET_TITLE_TOP_RATIO = CONTACT_SHEET_HEADER_RATIO * 0.45
CONTACT_SHEET_SUBTITLE_OFFSET_RATIO = 0.045
CONTACT_SHEET_SUBTITLE_SIZE_RATIO = 0.02


def header_lines(album_title: str, album_date: str, count: int) -> tuple[str, str]:
    """Az eredeti Indexkép két fejlécsora.

    A valódi ``AI6.cxf`` ``albumTitle=AI`` és ``albumDate=2023. november``
    mezőiből az ``AI6.jpg`` pontosan ``AI`` / ``9 kép, 2023. november``
    sorokat rajzol. A második sor mintája a honosított
    ``CContactSheetTheme::subtitle_format`` (``%1$d kép, %2$s``).

    Hiányzó dátumnál nem hagyunk lógó vesszőt. Ez hibatűrés a saját, régi
    projektjeinkhez; a tizenkét mért Picasa-projekt mind hordoz dátumot.
    """
    if count < 0:
        raise ValueError(f"A képek száma nem lehet negatív: {count}")
    title = str(album_title or "").strip()
    date = str(album_date or "").strip()
    subtitle = f"{count} kép"
    if date:
        subtitle += f", {date}"
    return title, subtitle


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
    "CONTACT_SHEET_HEADER_RATIO",
    "CONTACT_SHEET_LEFT_RATIO",
    "CONTACT_SHEET_SUBTITLE_OFFSET_RATIO",
    "CONTACT_SHEET_SUBTITLE_SIZE_RATIO",
    "CONTACT_SHEET_TITLE_TOP_RATIO",
    "CONTACT_SHEET_TITLE_RATIO",
    "NARROW_PANEL_FACTOR",
    "header_lines",
    "header_font_size",
    "mirror_header",
]
