"""A kollázs-vászon műveletei (#431).

Forrás: a jegy index-köre (a szerkesztőpanel 19 parancsa, a menü-erőforrás
`ID_COLLAGE_*` tételei) és a `docs/specs/picasa-create-features.md` 1.4.

Minden művelet **tiszta függvény**: a bemeneti sorozatot sosem írja, új
sorozatot ad vissza. Így ugyanaz a kód szolgálja ki a felületet, a
visszavonást és a `.cxf` mentését.

**A rétegsorrend iránya:** a lista sorrende a RAJZOLÁSI sorrend — a `.cxf`
is ebben sorolja a csomópontokat —, tehát az **utolsó elem van legfelül**.
Ezért a „Legfelülre helyezés" a lista végére visz.

**A `snap_*` négy parancs a négy fő irányra**, nem 30 fokos óralap-rács.
Ezt két független forrás igazolja: a buboréksúgók („Align rotation to
straight up / 90 CW / 180 CW / 270 CW") és a menü-erőforrás („0 fok",
„90 fok", „180 fok", „270 fok"). Az elforgatás egyébként szabad — ez a négy
csak „bepattintó" gomb.

**A két véletlenszerűsítő KÜLÖN parancs**, ahogy az eredetiben is:
`rand_order` („Képek összekeverése") a SORRENDET keveri — ez itt van;
`rand_placement` („Képek szétszórása") az elrendezést sorsolja újra — az a
`pile` / `packing` dolga.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import TypeVar

from .fitting import fisher_yates, picasa_round

T = TypeVar("T")

# A négy „bepattintó" parancs és a hozzájuk tartozó szög fokban.
#
# ⚠️ #921: a `snap_9` a binárisban **−90,0** fok, NEM 270. Rajzban a kettő
# ugyanaz, TÁROLÁSBAN nem: a `.cxf`-be `−1,570796` kerül `4,712389` helyett,
# tehát a windowsos Picasával való oda-vissza olvasás elcsúszna.
#
# A helyi menü „270 fok" felirata (`Rotate::ID_COLLAGE_ALIGN_270`) a
# MEGJELENÍTETT szöveg, nem a tárolt érték — a kettőt nem szabad
# összekeverni. A címek:
#
# | parancs | érték | cím |
# |---|---:|---|
# | `snap_12` | `0.0` (`fldz`) | `0x0082e0e9` |
# | `snap_3` | `+90.0f` | `0xcf4370`, `0x0082e163` |
# | `snap_6` | `+180.0f` | `0xcf409c`, `0x0082e1e1` |
# | `snap_9` | **`−90.0f`** | `0xcf50d0`, `0x0082e25f` |
SNAP_COMMANDS = {
    "snap_12": 0.0,  # „Align rotation to straight up"
    "snap_3": 90.0,  # „Align rotation to 90 CW"
    "snap_6": 180.0,  # „Align rotation to 180 CW"
    "snap_9": -90.0,  # „Align rotation to 270 CW" — a TÁROLT érték −90
}


def _checked(items: Sequence[T], indices: Iterable[int]) -> list[int]:
    selection = list(indices)
    for index in selection:
        if not 0 <= index < len(items):
            raise ValueError(
                f"Érvénytelen kép-index: {index} (0…{len(items) - 1})"
            )
    return selection


# --- Rétegsorrend -----------------------------------------------------------


def move_to_top(items: Sequence[T], indices: Iterable[int]) -> tuple[T, ...]:
    """A kijelöltek legfelülre (a lista végére), egymás relatív sorrendjében."""
    selection = sorted(set(_checked(items, indices)))
    if not selection:
        return tuple(items)
    moved = [items[i] for i in selection]
    rest = [item for i, item in enumerate(items) if i not in set(selection)]
    return tuple([*rest, *moved])


def move_to_bottom(items: Sequence[T], indices: Iterable[int]) -> tuple[T, ...]:
    """A kijelöltek legalulra (a lista elejére)."""
    selection = sorted(set(_checked(items, indices)))
    if not selection:
        return tuple(items)
    moved = [items[i] for i in selection]
    rest = [item for i, item in enumerate(items) if i not in set(selection)]
    return tuple([*moved, *rest])


def _step(
    items: Sequence[T], indices: Iterable[int], *, upward: bool
) -> tuple[T, ...]:
    """Egy lépés fel vagy le. A kijelölteket a szélükről kezdve mozgatjuk,
    hogy egy összefüggő blokk együtt csússzon, ne torlódjon egymásra."""
    selection = set(_checked(items, indices))
    if not selection:
        return tuple(items)
    result = list(items)
    current = set(selection)
    order = sorted(selection, reverse=upward)
    for index in order:
        target = index + 1 if upward else index - 1
        if not 0 <= target < len(result) or target in current:
            continue
        result[index], result[target] = result[target], result[index]
        current.discard(index)
        current.add(target)
    return tuple(result)


def move_up(items: Sequence[T], indices: Iterable[int]) -> tuple[T, ...]:
    """Egy réteggel feljebb (a lista vége felé)."""
    return _step(items, indices, upward=True)


def move_down(items: Sequence[T], indices: Iterable[int]) -> tuple[T, ...]:
    """Egy réteggel lejjebb (a lista eleje felé)."""
    return _step(items, indices, upward=False)


def remove_at(items: Sequence[T], indices: Iterable[int]) -> tuple[T, ...]:
    """A kijelöltek kivétele a kollázsból (`ID_COLLAGE_REMOVE`, Del).

    Minden kép eltávolítható — a mentés ilyenkor „Mentés mellőzve"
    üzenettel áll meg, de a művelet maga megengedett."""
    selection = set(_checked(items, indices))
    return tuple(item for i, item in enumerate(items) if i not in selection)


# --- Forgatás ---------------------------------------------------------------


def snap_theta(command: str) -> float:
    """A bepattintó parancshoz tartozó szög **radiánban** (a `.cxf` így tárol)."""
    if command not in SNAP_COMMANDS:
        raise ValueError(
            f"Ismeretlen forgatás-igazító parancs: {command!r} "
            f"(várt: {tuple(SNAP_COMMANDS)})"
        )
    return math.radians(SNAP_COMMANDS[command])


def angle_caption_degrees(theta: float) -> int:
    """A húzás közben kiírt szög (`collage::angle_format` = „Szög: %d").

    A `theta` radiánban van; a felület `*180/π`-vel váltja fokra.

    ⚠️ #921: a Picasa a kiírás ELŐTT **negálja** a szöget (`fchs`,
    `0x00868944`–`0x00868947`). Vagyis a felhasználó az óramutató járásával
    EGYEZŐ forgatásnál pozitív számot lát, miközben a belső szög negatív —
    nálunk eddig előjelhelyesen ment ki, tehát ellenkező előjelű számot
    mutattunk.
    """
    return picasa_round(-math.degrees(theta))


def scale_caption_percent(scale: float, base_scale: float) -> int:
    """A húzás közben kiírt méretarány (`collage::scale_format` =
    „Méretarány: %d%%")."""
    if base_scale <= 0.0:
        raise ValueError(f"Érvénytelen alapméret: {base_scale}")
    return picasa_round(scale / base_scale * 100.0)


# --- Képek összekeverése ----------------------------------------------------


def shuffle_order(items: Sequence[T], rng) -> tuple[T, ...]:
    """A képek SORRENDJÉNEK keverése (`rand_order`).

    Nem tévesztendő össze a „Képek szétszórása" (`rand_placement`)
    paranccsal, ami az elrendezést sorsolja újra."""
    return tuple(fisher_yates(items, rng))


__all__ = [
    "SNAP_COMMANDS",
    "angle_caption_degrees",
    "move_down",
    "move_to_bottom",
    "move_to_top",
    "move_up",
    "remove_at",
    "scale_caption_percent",
    "shuffle_order",
    "snap_theta",
]
