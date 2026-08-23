"""A `filters=` szűrőnevek KANONIKUS alakja és paraméterszám-korlátja (#695).

Ez a modul az **író oldal** igazságforrása. Mérve (#685, ld.
`docs/specs/picasa-ini-format.md`, „A `filters=` lánc beolvasása SZIGORÚ"):
az eredeti Picasa a lánc szűrőneveit **bájtra pontosan** illeszti, és a
nem egyező bejegyzést **némán elejti** — nincs hiba, nincs jelzés, a
szerkesztés egyszerűen nem történik meg:

| lánc | hatás |
|---|---|
| `tint=1,79.842102,ffff;` | lefut |
| `Tint=` / `TINT=` / `tInT=` | **néma elejtés** |
| `Vignette=1,35,1.4,0,00000000;` | lefut |
| `vignette=` / `VIGNETTE=` | **néma elejtés** |

Ezért **mindkét irányban a kanonikus alak számít**:

- **íráskor** kizárólag a kanonikus alak mehet ki;
- **olvasáskor** a nem egyező írásmódú, de FELISMERT nevű bejegyzés
  ugyanúgy elesik, ahogy az eredetiben (#1141). Korábban itt casefold
  illesztés állt („legyünk megengedők"), és ettől a PicasaPy olyan
  szerkesztést mutatott, amit a Picasa a felhasználó gépén nem hajt végre
  — a néma eltérés a mi oldalunkon keletkezett.

Az ISMERETLEN nevet továbbra sem bántjuk: változatlanul megy vissza a
láncba (round-trip elv).

A kanonikus alakok forrása a `docs/specs/filterdesc-registry.md` 2.
szakasza — a Picasa saját `filterdesc.xml`-jéből átvezetett, 84 bejegyzésű
regiszter. Itt semmit nem „javítunk ki" és nem találunk ki: ami ott nincs
benne, az ismeretlen névnek számít, és **változatlanul** megy vissza a
láncba (round-trip elv).

## A paraméterszám

Ugyanez a hibaosztály a paraméterek száma: mérve `grain2=1;` lefut,
`grain2=1,0.500000;` **néma elejtés**. A mérés iránya azonban FONTOS és
aszimmetrikus:

- a **fölösleges** paraméter bizonyítottan megöli a bejegyzést;
- a **hiányzó** paraméter viszont nem: `unsharp=1` mérten azonos az
  `unsharp2=1,0.600000`-val (`edit_controller.py` `_CATALOGUE` megjegyzése),
  azaz az elhagyott paraméter az alapértékére esik vissza;
- a **záró üres mező** (`grain=1,;`) szintén tolerált.

Ezért a `MAX_PARAM_COUNTS` **felső korlát**, nem elvárt darabszám — pontosan
azt tiltja, amit a mérés néma elejtésként kimutatott. Egy szigorúbb
(egyenlőséget követelő) szabály olyan láncokat is hibának minősítene,
amelyekről tudjuk, hogy az eredetiben lefutnak.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

#: A `filterdesc-registry.md` 2. szakaszának 84 szűrője, **pontosan abban az
#: írásmódban**, ahogyan az eredeti Picasa várja. A sorrend a
#: dokumentum táblázatának sorrendje (nem ábécé) — így a két lista
#: szemre összevethető marad.
CANONICAL_FILTER_NAMES: tuple[str, ...] = (
    # history (nem képi műveletek)
    "save",
    "crop64",
    "crop",
    "redeye",
    "retouch",
    "picnik",
    "rot",
    # natív szűrők
    "debug",
    "triple",
    "triple2",
    "triple3",
    "finetune",
    "finetune2",
    "colorfix",
    "autobacklight",
    "autolight",
    "autocolor",
    "bw",
    "enhance",
    "warm",
    "grain",
    "grain2",
    "sepia",
    "unsharp",
    "unsharp2",
    "autocontrast",
    "tilt",
    "rainbow",
    "radblur",
    "radsat",
    "linblur",
    "ansel",
    "tint",
    "dir_tint",
    "radtint",
    "glow",
    "glow2",
    "sat",
    "colortemp",
    "shadow",
    "blur",
    "contrast",
    "gamma",
    "backlight",
    "fill",
    "whitept",
    "dir_sat",
    "dir_brite",
    "dir_sharp",
    "focalpixelate",
    # Glimmer (Picnik-örökös) effektek
    "Boost",
    "Border",
    "Cinemascope",
    "Comicize",
    "CrossProcess",
    "DropShadow",
    "PicnikFocalPixelate",
    "FocalZoom",
    "PicnikGrain",
    "HDR",
    "HeatMap",
    "Holga",
    "Invert",
    "IR",
    "LocalContrast",
    "Lomo",
    "Matte",
    "MuseumMatte",
    "Neon",
    "NightVision",
    "Orton",
    "PencilSketch",
    "Pixelate",
    "Polaroid",
    "QuantizePalette",
    "ReanimatedEyeColor",
    "RoundedEdges",
    "Sixties",
    "Soften",
    "PicnikTint",
    "TwoTone",
    "Vignette",
    # film-jelölők
    "moviestart",
    "movieend",
)

_CANONICAL_BY_CASEFOLD: Mapping[str, str] = MappingProxyType(
    {name.casefold(): name for name in CANONICAL_FILTER_NAMES}
)

#: A lánc-paraméterek MAXIMÁLIS száma az engedélyező `1` flag UTÁN. Fölötte
#: az eredeti Picasa némán elejti a bejegyzést (#685). Csak azok a szűrők
#: szerepelnek itt, amelyeknél a darabszám a regiszterből egyértelműen
#: levezethető — a többinél nem validálunk (ld. a modul alján a hiánylistát).
#:
#: (a) VALÓDI `.picasa.ini`-mintából (`filterdesc-registry.md` 3. és 4.1,
#:     illetve a `tests/ini/test_filters.py` #190/#347 mintái):
_SAMPLED_PARAM_COUNTS: Mapping[str, int] = {
    "finetune2": 5,  # 1,fill,highlights,shadows,szín,hőmérséklet
    "radblur": 4,  # 1,x,y,Size,Amount
    "dir_tint": 5,  # 1,x,y,Feather,Shade,szín
    "radtint": 4,  # 1,x,y,Feather,szín
    "glow2": 2,  # 1,Intensity,Radius
    "tint": 2,  # 1,Color Preservation,szín
    "ansel": 1,  # 1,szín
    "grain2": 0,  # mérve: egyetlen fölös paraméter megöli
    "sepia": 0,  # mérve: `sepia=1;` lefut, paramétere nincs
    "Vignette": 4,  # 1,Blur,Strength,Fade,szín
    "MuseumMatte": 4,
    "TwoTone": 5,
    "Holga": 3,
    "QuantizePalette": 3,
    "Sixties": 3,
    "Border": 6,
    "DropShadow": 6,
    "Cinemascope": 1,  # Letterbox jelölő
    "FocalZoom": 6,  # 1,x,y,Impact,Radius,Hardness,Fade
    "Boost": 1,
    "Soften": 2,
    "Pixelate": 3,
    "PencilSketch": 3,
    "Neon": 2,  # 1,Fade,szín
    "Comicize": 3,
    "Polaroid": 2,
    "IR": 1,
    "Lomo": 2,
    "HDR": 3,
    "Orton": 3,
    "HeatMap": 2,
    "CrossProcess": 1,
    "Invert": 0,
    "NightVision": 3,
}

#: (b) A `filterdesc-registry.md` 2. szakaszának csúszka-oszlopából, a 3.
#:     szakasz kimondott POZÍCIÓ-szabályával: „`puck` kurzoros szűrőnél a
#:     fókuszpont (x, y) megy elöl, utána a csúszkák `id` sorrendben, a
#:     színparaméter a végén". Tehát darabszám = 2·(van-e puck) + csúszkák
#:     száma + 1·(van-e szín).
_DERIVED_PARAM_COUNTS: Mapping[str, int] = {
    "debug": 3,  # puck + Size
    "triple": 3,
    "triple2": 3,
    "triple3": 3,
    "finetune": 5,  # 4 csúszka + colorcircle (a finetune2-vel azonos alak)
    "unsharp": 1,
    "unsharp2": 1,
    "tilt": 2,  # a 2. csúszka letiltott, de v1-kompat miatt megmaradt
    "rainbow": 1,
    "radsat": 4,  # puck + Size + Sharpness
    "linblur": 3,  # puck + Amount
    "glow": 2,
    "sat": 1,
    "colortemp": 2,
    "shadow": 3,
    "blur": 1,
    "contrast": 1,
    "gamma": 1,
    "backlight": 1,
    "fill": 1,
    "dir_sat": 4,  # puck + 2 csúszka
    "dir_brite": 4,
    "dir_sharp": 4,
    "focalpixelate": 6,  # puck + 4 csúszka (örökölt, a 3.9-ben halott)
    "LocalContrast": 2,
    "Matte": 4,
    "RoundedEdges": 2,
    "PicnikGrain": 2,
    # paraméter nélküli egykattintásos javítások (`mode="oneclick"`,
    # csúszka-oszlop üres)
    "autobacklight": 0,
    "autolight": 0,
    "autocolor": 0,
    "autocontrast": 0,
    "bw": 0,
    "enhance": 0,
    "warm": 0,
    "grain": 0,
    "moviestart": 0,
    "movieend": 0,
}

#: Amire SZÁNDÉKOSAN nincs korlát — itt a regiszterből nem derül ki a
#: darabszám, és találgatni tilos (a téves korlát valódi szerkesztést
#: utasítana vissza):
#:
#: - `save`, `crop64`, `crop`, `rot`: `history` módú, csúszka nélküli
#:   bejegyzések, amelyek mégis hordoznak adatot (a `crop64` a rect64 hexet);
#: - `redeye`, `retouch`, `picnik`: `persist` jelzős, RÉGIÓ-adatot őrző
#:   bejegyzések — a `redeye`/`retouch` nálunk ráadásul saját, változó
#:   hosszú PicasaPy-kiterjesztés (ld. `picasapy.ini.redeye`/`retouch`);
#: - `colorfix`, `whitept`: rejtett „Choose White Point" csúszka + külön
#:   `colorcircle` — nem dönthető el, hogy ez egy vagy két mező a láncban;
#: - `PicnikFocalPixelate`: a `filterdesc-registry.md` 4.1 kimondja, hogy
#:   „a `PicnikFocalPixelate`-ra nincs valós mintánk";
#: - `PicnikTint`, `ReanimatedEyeColor`: festhető maszkos effektek — nem
#:   igazolt, hogy a maszk foglal-e lánc-paramétert.
UNKNOWN_PARAM_COUNT_FILTERS: frozenset[str] = frozenset(
    {
        "save",
        "crop64",
        "crop",
        "rot",
        "redeye",
        "retouch",
        "picnik",
        "colorfix",
        "whitept",
        "PicnikFocalPixelate",
        "PicnikTint",
        "ReanimatedEyeColor",
    }
)

MAX_PARAM_COUNTS: Mapping[str, int] = MappingProxyType(
    {**_SAMPLED_PARAM_COUNTS, **_DERIVED_PARAM_COUNTS}
)

#: #711 — a `desat`: a `CDesaturateFilter` saját, Picasa 2-korabeli
#: ini-kulcsa. Szándékosan NEM tagja a `CANONICAL_FILTER_NAMES`/
#: `MAX_PARAM_COUNTS` pároshoz — azok a `filterdesc-registry.md` 2.
#: szakaszának 84 szűrőjét tükrözik VERBATIM (ld. a modul docsztringjét és
#: `tests/ini/test_filter_registry_695.py::TestRegiszterTeljesseg`), a
#: `desat` viszont bizonyítottan NINCS abban a táblában — külön, hardcode-olt
#: ágon kezeli a natív névfeloldás (`FUN_008f9fe0`, ld.
#: `docs/specs/picasa-ini-format.md`, „A `desat`" szakasz). Ezért egy
#: KÜLÖN, kis rétegben él: a kanonikus alak és a paraméterszám a normál
#: 84-es regiszter után, EZT is megnézi.
_LEGACY_ALIAS_MAX_PARAM_COUNTS: Mapping[str, int] = MappingProxyType({"desat": 3})
_LEGACY_ALIAS_BY_CASEFOLD: Mapping[str, str] = MappingProxyType(
    {name.casefold(): name for name in _LEGACY_ALIAS_MAX_PARAM_COUNTS}
)


class FilterWriteError(ValueError):
    """A `filters=` láncba írás visszautasítása — a bejegyzést az eredeti
    Picasa némán elejtené (#695)."""


def canonical_filter_name(name: str) -> str | None:
    """A szűrő kanonikus (Picasa által várt) írásmódja.

    Args:
        name: Bármilyen írásmódú szűrőnév a láncból.

    Returns:
        A kanonikus alak, vagy `None`, ha a név nincs a regiszterben (idegen
        vagy jövőbeli szűrő — ilyet nem alakítunk át). A `desat` (#711) a
        84-es táblán KÍVÜLI, dokumentált kivétel — ld.
        `_LEGACY_ALIAS_BY_CASEFOLD`.
    """
    folded = name.casefold()
    return _CANONICAL_BY_CASEFOLD.get(folded) or _LEGACY_ALIAS_BY_CASEFOLD.get(folded)


def is_exact_filter_name(name: str) -> bool:
    """A név PONTOSAN a kanonikus (regiszterbeli) alak-e (#1141).

    Az eredeti Picasa lánc-bejárója kis-nagybetű-érzékeny: hat mért képen
    (`merokit-2` export) a `Tint` / `TINT` / `tInT` / `vignette` /
    `VIGNETTE` / `Sepia` alak NEM futott le, a kanonikus `tint` /
    `Vignette` / `sepia` igen. A három család mintázata más, tehát tényleg
    a regiszterbeli alakhoz kell illeszteni.

    A régi (`_LEGACY_ALIAS_BY_CASEFOLD`) nevek a SAJÁT írásmódjukkal
    fogadhatók el — azok is valódi Picasa-alakok.
    """
    return name in CANONICAL_FILTER_NAMES or name in _LEGACY_ALIAS_BY_CASEFOLD


def canonicalize_filter_name(name: str) -> str:
    """A kanonikus alak, ismeretlen névnél maga a kapott név (round-trip)."""
    return canonical_filter_name(name) or name


def effective_param_count(params: tuple[str, ...]) -> int:
    """A flag utáni ÉRDEMI paraméterek száma egy lánc-tag mezőiből.

    A `params[0]` az engedélyező flag, ezt nem számoljuk. A ZÁRÓ ÜRES mező
    (`grain=1,;`) mérten tolerált (ld. a modul docstringjét), ezért az sem
    paraméter.

    Args:
        params: A tag `,` mentén tagolt mezői, a flaggel együtt.

    Returns:
        Az érdemi paraméterek száma.
    """
    rest = list(params[1:])
    while rest and rest[-1] == "":
        rest.pop()
    return len(rest)


def max_param_count(name: str) -> int | None:
    """A szűrő megengedett legnagyobb paraméterszáma a flag után.

    Args:
        name: Bármilyen írásmódú szűrőnév.

    Returns:
        A felső korlát, vagy `None`, ha a regiszterből nem vezethető le
        (ilyenkor nem validálunk — ld. `UNKNOWN_PARAM_COUNT_FILTERS`).
    """
    canonical = canonical_filter_name(name)
    if canonical is None:
        return None
    if canonical in _LEGACY_ALIAS_MAX_PARAM_COUNTS:
        return _LEGACY_ALIAS_MAX_PARAM_COUNTS[canonical]
    return MAX_PARAM_COUNTS.get(canonical)
