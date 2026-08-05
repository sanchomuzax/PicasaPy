"""A `text=`/`textactive=` szöveg-overlay kulcsok parse/serialize-e (#148).

**ŐSZINTE ÁLLAPOT — nyitott kérdés:** a spec (`docs/specs/picasa-ini-format.md`)
egyetlen, RÖVIDÍTETT példát rögzít:

    text=1; 136;11;sample text;Aharoni;...

Ebből az első öt mező szerkezete (engedélyező flag; két szám; szöveg-tartalom;
betűtípus-név) egyértelműen kiolvasható, de:

- a `136`/`11` számpár **JELENTÉSE ismeretlen** — lehet pozíció (px vagy
  relatív koordináta más skálázással), betűméret+forgatás, vagy valami más;
  golden-minta (valódi Picasa `text=` export, tényleges kép mellett) NINCS
  hozzá, tehát ez a modul **nem** próbálja koordinátává/rendereléshez
  átalakítani — csak nyersen tárolja, típusosan;
- a lezáró `...` azt jelzi, hogy a mező-lista FOLYTATÓDIK, de a további mezők
  száma/jelentése szintén nem dokumentált.

Emiatt ez a modul egy **defenzív, típusos, de round-trip-korlátozott**
réteget ad: az ismert öt mezőt (`enabled`, `raw_x`, `raw_y`, `content`,
`font`) elemekre bontja, a fennmaradó (`...`) részt EGYBEN, nyers stringként
őrzi meg (`raw_tail`) — ha ez üres, a serialize sem ír utána pontosvesszőt.

**Round-trip garancia csak PicasaPy-eredetű értékekre**: ha ez a modul
maga építi a `text=` stringet (`serialize_text`), a `parse_text(serialize_text(x)) == x`
mindig igaz. Egy VALÓDI, máshonnan (Picasa) származó `text=` érték
bájt-pontos visszaírását ez a modul NEM garantálja (a szóközölés/mezőszám
bizonytalan) — ha egy ilyen sort a PicasaPy nem módosít, az ini generikus,
tartalom-agnosztikus sor-rétege (`picasapy.ini.document`) attól függetlenül
bitre pontosan megőrzi, mert azt a réteget sosem hívjuk erre a kulcsra,
amíg nem kell ténylegesen szerkeszteni.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Az ismert mezők száma a `text=` értékben (flag, x, y, content, font) —
#: ezen felül minden a `raw_tail`-be kerül, tagolatlanul.
_KNOWN_FIELD_COUNT = 5


@dataclass(frozen=True)
class TextOverlay:
    """A `text=` kulcs típusos alakja.

    `raw_x`/`raw_y`: a nyers (nem értelmezett) számpár — a jelentésük
    megerősítetlen, ld. modul-docsztring. `raw_tail`: minden a betűtípus-név
    UTÁN álló, tagolatlanul megőrzött rész (lehet üres string).
    """

    enabled: bool
    raw_x: int
    raw_y: int
    content: str
    font: str
    raw_tail: str = ""


def parse_text(value: str) -> TextOverlay:
    """A `text=` érték dekódolása.

    `ValueError`, ha az első öt mező (flag;x;y;tartalom;betűtípus) nem
    állítható elő — a hívó felelőssége, hogy ilyenkor a bejegyzést
    érintetlenül hagyja (ne írja felül a generikus round-trip réteget)."""
    parts = value.split(";", _KNOWN_FIELD_COUNT - 1)
    if len(parts) < _KNOWN_FIELD_COUNT:
        raise ValueError(f"Érvénytelen text= érték (túl kevés mező): {value!r}")
    flag_raw, x_raw, y_raw, content, rest = parts
    font, _sep, raw_tail = rest.partition(";")
    try:
        enabled = int(flag_raw.strip()) != 0
        raw_x = int(x_raw.strip())
        raw_y = int(y_raw.strip())
    except ValueError as error:
        raise ValueError(f"Érvénytelen text= érték (nem szám mező): {value!r}") from error
    return TextOverlay(
        enabled=enabled, raw_x=raw_x, raw_y=raw_y, content=content, font=font,
        raw_tail=raw_tail,
    )


def serialize_text(overlay: TextOverlay) -> str:
    """`TextOverlay` → `text=` érték. PicasaPy-eredetű overlay-re a
    `parse_text(serialize_text(overlay)) == overlay` mindig igaz."""
    flag = "1" if overlay.enabled else "0"
    tail = f";{overlay.raw_tail}" if overlay.raw_tail else ""
    return f"{flag};{overlay.raw_x};{overlay.raw_y};{overlay.content};{overlay.font}{tail}"


def parse_text_active(value: str) -> bool:
    """`textactive=` — feltételezett boolean jelző (a `hidden=yes`-hez
    hasonlóan a Picasa `0`/`1`-et használ a legtöbb boolean kulcsnál);
    élő ini-ben egyelőre validálatlan."""
    return value.strip() not in ("", "0")


def serialize_text_active(active: bool) -> str:
    return "1" if active else "0"
