"""Az „Összes szerkesztés visszavonása" tétel engedélyezése (#7017).

EGY helyen számolódik a Kép menü, a helyi menük és a néző menüje számára: az
eredeti Picasa 3.9 szerkesztettségi állapotából, nem a `hasEdits` jelzőből
(az a kék visszahajtás-jelölőt és a Mentés-tételeket vezérli, és a tükrözést
vagy az elforgatást nem számolja).

Az eredeti állapotbájtja (`0x004296a0`):

| feltétel (ebben a sorrendben)             | állapot |
|-------------------------------------------|---------|
| nem üres `filters` (a vágás crop64-je a láncban lakik) | `1` |
| `rotate(n)`, `n mod 4 != 0`               | `2`     |
| `flipped > 0`                             | `1`     |
| különben                                  | `0`     |

A kijelölés sorrendjében az első nem nulla állapotú képnél megáll a vizsgálat
(`0x005cb1a0`: `0x20`, ha az állapot `2` volt: `0x40`). A menütétel akkor él,
ha van `0x20` és nincs `0x40` bit (`0x0056f393-0x0056f402`), vagyis ha az első
nem nulla állapot `1`. Csak elforgatott képnél, szerkesztetlen képnél és üres
kijelölésnél a tétel szürke.

Az eredeti állapotfüggvényének `+0xe4` tagját (a `0x0042af00` tömb, a
film-szerkesztés) ez a szelet kihagyja: nálunk nincs megfelelője.
"""

from __future__ import annotations

from collections.abc import Iterable

UNEDITED = 0
EDITED = 1
ROTATED_ONLY = 2


def edit_state(photo) -> int:
    """A kép szerkesztettségi állapota: `UNEDITED`, `EDITED` vagy `ROTATED_ONLY`.

    Elnézően olvas: a kollázs-sáv rekord-hasonmásai nem ismerik a
    `flip_flags` mezőt, és a `0` a helyes rájuk (ld. `PhotoRecord.flip_flags`).
    """
    if (photo.filters or "").strip():
        return EDITED
    if int(photo.rotate_steps or 0) % 4 != 0:
        return ROTATED_ONLY
    if int(getattr(photo, "flip_flags", 0) or 0) > 0:
        return EDITED
    return UNEDITED


def undo_all_edits_enabled(photos: Iterable) -> bool:
    """Él-e az „Összes szerkesztés visszavonása" a kijelölt képekre.

    A `photos` a kijelölés sorrendjében jön; az első nem nulla állapotú kép
    dönt. Üres kijelölésre, és ha minden kép szerkesztetlen: `False`.
    """
    for photo in photos:
        state = edit_state(photo)
        if state != UNEDITED:
            return state == EDITED
    return False
