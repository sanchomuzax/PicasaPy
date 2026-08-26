"""A `color:`/`szín:` keresőtoken kiválogatása egy szabadszavas keresésből
(#383) — a Picasa `color:blue`-jának megfelelője, magyarul `szín:kék` is.

A tokeneket a `picasapy.color.resolve_color_alias` ismeri fel (10 szín,
angolul és magyarul); a nem felismert `color:xyz`/`szín:xyz` szó — hogy a
felhasználó ne veszítsen el keresési szöveget egy elgépelt színnév miatt —
egyszerűen a szabadszavas maradékban marad, mintha sima szó lenne."""

from __future__ import annotations

from picasapy.color import resolve_color_alias

# Az ékezet nélküli "szin:" alak is elfogadott — sok billentyűzeten/
# bevitelen kényelmetlen az í.
_COLOR_PREFIXES = ("color:", "szín:", "szin:")


def parse_color_terms(query: str) -> tuple[str, tuple[str, ...]]:
    """A `query` szétbontása: `(maradék_szabadszöveg, talált_színtokenek)`.

    Több `color:`/`szín:` token esetén a színek EGYMÁSSAL VAGY (OR)
    kapcsolatban állnak — a maradék szöveggel viszont ÉS (a meglévő
    FTS-keresés szemantikájával összhangban). Egy képnek egy hue-vödre
    van, tehát két KÜLÖNBÖZŐ színnév ÉS-elve sosem adna találatot; az
    akromatikus kép viszont egyszerre illeszkedik a `black`, `white` és
    `gray` tokenre (#1480)."""
    remaining: list[str] = []
    colors: list[str] = []
    for token in query.split():
        folded = token.casefold()
        prefix = next((p for p in _COLOR_PREFIXES if folded.startswith(p)), None)
        if prefix is None:
            remaining.append(token)
            continue
        canonical = resolve_color_alias(token[len(prefix) :])
        if canonical is None:
            remaining.append(token)  # ismeretlen szín — marad szabadszöveg
        else:
            colors.append(canonical)
    return " ".join(remaining), tuple(colors)
