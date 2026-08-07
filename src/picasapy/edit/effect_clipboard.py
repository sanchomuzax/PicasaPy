"""„Az összes effektus másolása/beillesztése" — a `filters=` lánc átvitele
képek között (#426, Picasa `ID_EDIT_COPYALLEFFECTS`/`ID_EDIT_PASTEALLEFFECTS`).

Ez a modul KIZÁRÓLAG tiszta logikát tartalmaz (nincs fájl-I/O, nincs Qt-
függés): a `filters=` lánc szűrését és a beillesztendő értéket adja vissza.
Az alkalmazás-szintű vágólap ÁLLAPOTA (mit másoltunk utoljára) és a
mappánkénti kötegelt ini-írás a vezérlő-oldalon van
(`picasapy.app.photo_ops_controller.EffectClipboardMixin`).

## Mit NEM viszünk át — és honnan jön ez a szabály

A Picasa a "Copy All Effects" művelethez a `crop64`/`crop` (kép-specifikus
geometria), `redeye`/`retouch` (kép-specifikus RÉGIÓ), valamint a
`moviestart`/`movieend` (klip-specifikus vágópont) bejegyzéseket NEM viszi
át — ezek nem "hangulat", hanem az adott képhez kötött adat.

A hivatalos forrás a `filterdesc.xml` szűrő-regiszter (Picasa
3.9.141.259), amelyet a `docs/specs/filterdesc-registry.md` tár fel: a
regiszter minden szűrőhöz tárol egy `mode` attribútumot (`history` = nem
képi művelet, csak az előzményben él) és egy `persist` jelzőt (régió-adatot
őriz). A `docs/specs/filterdesc-registry.md` "2. A teljes regiszter"
táblázata szerint:

* `mode="history"`: `save`, `crop64`, `crop`, `redeye`, `retouch`,
  `picnik`, `rot`
* `persist` jelző: `redeye`, `retouch`, `picnik` (a fentiek részhalmaza)

A `_FILTER_REGISTRY` lenti táblázata ezt a két oszlopot (mode, persist)
tükrözi, VERBATIM átvéve a specifikáció táblázatából — futásidőben a
`filterdesc.xml` maga NEM érhető el (a `research/` fa, ahonnan a
specifikáció készült, nincs benne ebben a repóban, és nincs hozzá
regiszter-olvasó kód sem a `tools/picasa/` alatt). Emiatt ez egy kódba
zárt, TESZTELT pillanatkép, nem futásidejű XML-olvasás — ha egyszer a
runtime `filterdesc.xml` és egy hozzá tartozó olvasó elérhetővé válik, ezt
a táblázatot azzal kell felváltani/ellenőrizni.

A `mode="history"`/`persist` szabály MECHANIKUSAN kiadja a `crop64`/`crop`/
`redeye`/`retouch` négyest (plusz a nem-effekt `save`/`rot`/`picnik`
bejegyzéseket, amelyeket szintén ártalmatlan kizárni: ezek sosem
"hangulat"-effektek, csak könyvelési/history-bejegyzések). A
`moviestart`/`movieend` viszont a jelenleg kinyert táblázatban
`mode="oneclick"`-ként szerepel, flag nélkül — a specifikáció 1.2
szakasza (History módú szűrők felsorolása) sem említi őket. Ez a
specifikáció-kivonat hiányossága: a `moviestart`/`movieend` a Picasa
mozgófilm-eszközének klip-specifikus kezdő-/végpontja, ugyanolyan
kép-/klip-kötött adat, mint a `redeye`/`retouch` régiói — ezért a #426
jegy kifejezetten kizárja őket. Mivel ezt a jelenleg elérhető
`mode`/`persist` oszlopokból nem lehet levezetni, ez a két név egy
explicit, dokumentált KIEGÉSZÍTÉS (`_MANUAL_EXCLUSIONS`) a mechanikus
szabály fölött — ha a teljes `filterdesc.xml` egyszer futásidőben
elérhető lesz, ellenőrizendő, hogy van-e rájuk saját, eddig fel nem
tárt jelző, és ha igen, a kiegészítés törölhető.
"""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.ini.filters import parse_filters, serialize_filters


@dataclass(frozen=True)
class _FilterFlags:
    """Egy szűrő `filterdesc.xml`-beli `mode`/`persist` jelzője."""

    mode: str
    persist: bool = False


# forrás: docs/specs/filterdesc-registry.md, "2. A teljes regiszter"
# táblázata (Picasa 3.9.141.259 `filterdesc.xml`-ből kinyerve, 2026-08-06) —
# csak a `mode`/`persist` oszlopok, verbatim. Lásd a modul docstringjét.
_FILTER_REGISTRY: dict[str, _FilterFlags] = {
    "save": _FilterFlags("history"),
    "crop64": _FilterFlags("history"),
    "crop": _FilterFlags("history"),
    "redeye": _FilterFlags("history", persist=True),
    "retouch": _FilterFlags("history", persist=True),
    "picnik": _FilterFlags("history", persist=True),
    "rot": _FilterFlags("history"),
    "debug": _FilterFlags("effect"),
    "triple": _FilterFlags("soft"),
    "triple2": _FilterFlags("soft"),
    "triple3": _FilterFlags("soft"),
    "finetune": _FilterFlags("soft"),
    "finetune2": _FilterFlags("soft"),
    "colorfix": _FilterFlags("soft"),
    "autobacklight": _FilterFlags("oneclick"),
    "autolight": _FilterFlags("oneclick"),
    "autocolor": _FilterFlags("oneclick"),
    "bw": _FilterFlags("oneclick"),
    "enhance": _FilterFlags("oneclick"),
    "warm": _FilterFlags("oneclick"),
    "grain": _FilterFlags("oneclick"),
    "grain2": _FilterFlags("oneclick"),
    "sepia": _FilterFlags("oneclick"),
    "unsharp": _FilterFlags("effect"),
    "unsharp2": _FilterFlags("effect"),
    "autocontrast": _FilterFlags("oneclick"),
    "tilt": _FilterFlags("tool"),
    "rainbow": _FilterFlags("tool"),
    "radblur": _FilterFlags("effect"),
    "radsat": _FilterFlags("effect"),
    "linblur": _FilterFlags("effect"),
    "ansel": _FilterFlags("effect"),
    "tint": _FilterFlags("effect"),
    "dir_tint": _FilterFlags("effect"),
    "radtint": _FilterFlags("effect"),
    "glow": _FilterFlags("effect"),
    "glow2": _FilterFlags("effect"),
    "sat": _FilterFlags("effect"),
    "colortemp": _FilterFlags("effect"),
    "shadow": _FilterFlags("effect"),
    "blur": _FilterFlags("effect"),
    "contrast": _FilterFlags("effect"),
    "gamma": _FilterFlags("effect"),
    "backlight": _FilterFlags("effect"),
    "fill": _FilterFlags("soft"),
    "whitept": _FilterFlags("effect"),
    "dir_sat": _FilterFlags("effect"),
    "dir_brite": _FilterFlags("effect"),
    "dir_sharp": _FilterFlags("effect"),
    "focalpixelate": _FilterFlags("effect"),
    "Boost": _FilterFlags("effect"),
    "Border": _FilterFlags("effect"),
    "Cinemascope": _FilterFlags("effect"),
    "Comicize": _FilterFlags("effect"),
    "CrossProcess": _FilterFlags("effect"),
    "DropShadow": _FilterFlags("effect"),
    "PicnikFocalPixelate": _FilterFlags("effect"),
    "FocalZoom": _FilterFlags("effect"),
    "PicnikGrain": _FilterFlags("effect"),
    "HDR": _FilterFlags("effect"),
    "HeatMap": _FilterFlags("effect"),
    "Holga": _FilterFlags("effect"),
    "Invert": _FilterFlags("effect"),
    "IR": _FilterFlags("effect"),
    "LocalContrast": _FilterFlags("effect"),
    "Lomo": _FilterFlags("effect"),
    "Matte": _FilterFlags("effect"),
    "MuseumMatte": _FilterFlags("effect"),
    "Neon": _FilterFlags("effect"),
    "NightVision": _FilterFlags("effect"),
    "Orton": _FilterFlags("effect"),
    "PencilSketch": _FilterFlags("effect"),
    "Pixelate": _FilterFlags("effect"),
    "Polaroid": _FilterFlags("effect"),
    "QuantizePalette": _FilterFlags("effect"),
    "ReanimatedEyeColor": _FilterFlags("effect"),
    "RoundedEdges": _FilterFlags("effect"),
    "Sixties": _FilterFlags("effect"),
    "Soften": _FilterFlags("effect"),
    "PicnikTint": _FilterFlags("effect"),
    "TwoTone": _FilterFlags("effect"),
    "Vignette": _FilterFlags("effect"),
    "moviestart": _FilterFlags("oneclick"),
    "movieend": _FilterFlags("oneclick"),
}

# Gépi szabály: history módú VAGY régió-adatot (persist) őrző szűrő nem
# vihető át képek között (docs/specs/filterdesc-registry.md 1.2/1.3 szakasz).
_MECHANICALLY_EXCLUDED: frozenset[str] = frozenset(
    name
    for name, flags in _FILTER_REGISTRY.items()
    if flags.mode == "history" or flags.persist
)

# Explicit kiegészítés a jelenlegi (csak mode/persist oszlopokat tartalmazó)
# regiszter-kivonat hiányossága miatt — ld. a modul docstringjét.
_MANUAL_EXCLUSIONS: frozenset[str] = frozenset({"moviestart", "movieend"})

#: A #426 "mit NE vigyen át" szabálya szerint kizárt szűrőnevek —
#: `mode="history"`/`persist="1"` a `filterdesc` regiszterből, plusz a
#: dokumentált `_MANUAL_EXCLUSIONS` kiegészítés.
EXCLUDED_FILTER_NAMES: frozenset[str] = _MECHANICALLY_EXCLUDED | _MANUAL_EXCLUSIONS

_EXCLUDED_FOLDED: frozenset[str] = frozenset(
    name.casefold() for name in EXCLUDED_FILTER_NAMES
)


def is_transferable(filter_name: str) -> bool:
    """Igaz, ha `filter_name` átvihető képek között (nincs az
    `EXCLUDED_FILTER_NAMES` halmazban, kis-nagybetű-tűrően)."""
    return filter_name.casefold() not in _EXCLUDED_FOLDED


def copy_all_effects(filters_value: str | None) -> str:
    """„Az összes effektus másolása": a `filters=` lánc vágólap-tartalma.

    A kép-/régióspecifikus bejegyzéseket (`EXCLUDED_FILTER_NAMES`) kihagyja,
    a maradékot az eredeti sorrendben, serializálva adja vissza — ez kerül
    az alkalmazás-szintű vágólapra.

    Args:
        filters_value: A forráskép nyers `filters=` értéke (`None`/üres
            string üres láncot jelent).

    Returns:
        A vágólapra teendő, már szűrt `filters=` érték (üres eredmény esetén
        üres string).
    """
    ops = parse_filters(filters_value or "")
    kept = tuple(op for op in ops if is_transferable(op.name))
    return serialize_filters(kept)


def paste_all_effects(clipboard_value: str) -> str:
    """„Az összes effektus beillesztése": a cél `filters=` értéke a
    beillesztés UTÁN.

    A vágólap tartalma a másoláskor MÁR szűrve lett (`copy_all_effects`),
    ezért a beillesztés a TELJES cél-láncot erre cseréli — a Picasa
    "felülírva a meglévő láncot" viselkedése (#426). Ha a cél képnek saját
    `crop64`/`redeye`/`retouch` bejegyzése volt, az is elvész: a #426 jegy
    kifejezetten teljes csere-műveletként írja le a beillesztést, nem
    rétegzést/összefésülést.

    Args:
        clipboard_value: Egy korábbi `copy_all_effects()` hívás eredménye.

    Returns:
        A célkép új `filters=` értéke (megegyezik `clipboard_value`-val —
        a függvény a szemantika dokumentálására és a jövőbeli
        finomításokra hagy egy nevesített csatlakozási pontot).
    """
    return clipboard_value
