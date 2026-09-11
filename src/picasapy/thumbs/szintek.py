"""A bélyegkép-gyorsítótár SZINTJEI (#598).

Az eredeti Picasa **négy** bélyegkép-tárat tartott, nem egyet:
`thumbs2.db` · `thumbs.db` · `bigthumbs.db` · `previews.db`. A méretek a
tulajdonos 2025-12-24-i Picasa-mentéséből **mérve** vannak
(`docs/specs/pmp-database.md`, több ezer elemű minta, két független
mintavételi ponton):

| szint | fájl | leghosszabb oldal |
|---|---|---:|
| apró („pinky", `m_pinkyThumbs`) | `thumbs2.db` | **72 px** |
| normál (`m_thumbs`) | `thumbs.db` | **144 px** |
| nagy (`m_bigThumbs`) | `bigthumbs.db` | **288 px** |
| előnézet (`m_previewThumbs`) | `previews.db` | **640 px** |

A szabály: **a hosszabb oldal fixen kötött, a képarány megmarad** — a három
bélyegkép-szint pontosan duplázódik (72 → 144 → 288), tehát a kisebb a
nagyobbikból felezéssel előáll.

## Miért NEM vesszük át mind a négyet

Mert nálunk **más a felső vég**, és ezt megmértük.

1. **288 px-re nincs fogyasztónk.** A rács legnagyobb fokozata 256 px
   (`application._GRID_MAX_THUMB_PX`), és a cache-méret ennek a
   képernyő-DPR-rel szorzott értéke — tehát a rács MA SEM nagyít, minden
   fokozat kicsinyítéssel áll elő. A tálca 81 px-es, a kollázs-klipek
   62 px-esek, az idővonal a rács fokozatát követi.
2. **A 288-as szint a felső fokozatokon LASSABB nálunk**, mert nagyobb
   JPEG-et kell dekódolni a 256-osnál. Egy cella előállítása (dekódolás +
   kicsinyítés, medián 200 körből, a legjobb három futásból):

   | rács-fokozat | a 256-os szintről | a 288-asról |
   |---:|---:|---:|
   | 176 px | 679 µs | 790 µs |
   | 256 px | 225 µs | 1060 µs |

3. **A 640-es előnézet nekünk visszalépés lenne.** A nézőben a képet a
   FÁJLBÓL töltjük (`sourceSize.width: 2560`), tehát élesebb, mint az
   eredeti 640 px-es előnézete. Az a szint 2008-ban a lassú
   JPEG-dekódolás megkerülése volt, nem képkvalitás.

## Amit ÁTVESZÜNK — és amit nyer vele

A két kicsi szintet (72, 144), a felső helyére pedig a saját rács-maximum
kerül. A nyereség ugyanazon a mérésen:

| rács-fokozat | ma (256-ról) | rétegzetten | nyereség |
|---:|---:|---:|---:|
| 64 px | 1010 µs | 72 px: 87 µs | **91%** |
| 96 px | 2085 µs | 144 px: 201 µs | **90%** |
| 128 px | 2347 µs | 144 px: 321 µs | **86%** |
| 144 px | 612 µs | 144 px: 77 µs | **87%** |

⚠️ A mérés a GÉPI költséget adja (dekódolás + kicsinyítés), nem a látható
gördülést: a Qt URL szerint gyorstárazza a kész képet, tehát a nyereség az
ELSŐ megjelenítéskor és a gyorstár kiürülése után jelentkezik.
"""

from __future__ import annotations

#: `thumbs2.db` — `m_pinkyThumbs`
PINKY = 72
#: `thumbs.db` — `m_thumbs`
NORMAL = 144
#: `bigthumbs.db` — `m_bigThumbs` (mérve, nálunk nem használt, ld. fent)
NAGY = 288
#: `previews.db` — `m_previewThumbs` (mérve, nálunk nem használt)
ELONEZET = 640

#: Az eredeti négy szint, a mérés sorrendjében — dokumentációs érték.
PICASA_SZINTEK = (PINKY, NORMAL, NAGY, ELONEZET)

#: Amit mi tartunk: a két kicsi szint, fölötte a hívó felső szintje.
KIS_SZINTEK = (PINKY, NORMAL)


def szintek(teto: int) -> tuple[int, ...]:
    """A tár szintjei növő sorrendben, `teto` a legnagyobb (a rács maximuma).

    A `teto` alatti kis szintek maradnak benne; egy `teto`-nél nem kisebb
    kis szint kimarad, különben két szint ugyanazt a képet tárolná."""
    if teto <= 0:
        raise ValueError(f"Érvénytelen felső szint: {teto}")
    return (*(px for px in KIS_SZINTEK if px < teto), teto)


def szint_cellahoz(cella_px: int, teto: int) -> int:
    """A legkisebb szint, amiből a `cella_px` oldalú cella még KICSINYÍTÉSSEL
    áll elő — nagyítás sosem (az homályos lenne).

    A cellánál nem kisebb szintek közül a legkisebbet adja; ha egyik sem
    elég nagy, a `teto`-t."""
    if cella_px <= 0:
        raise ValueError(f"Érvénytelen cellaméret: {cella_px}")
    for px in szintek(teto):
        if px >= cella_px:
            return px
    return teto


__all__ = [
    "ELONEZET",
    "KIS_SZINTEK",
    "NAGY",
    "NORMAL",
    "PICASA_SZINTEK",
    "PINKY",
    "szint_cellahoz",
    "szintek",
]
