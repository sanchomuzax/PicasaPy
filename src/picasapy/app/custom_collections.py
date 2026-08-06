"""Felhasználói egyéni gyűjtemények (#320): a mappafa gyökerén a beépített
öt gyűjtemény (`collections.py`) mellett a felhasználó SAJÁT gyűjteményt is
létrehozhat, és mappákat sorolhat át bele — az eredeti Picasa mappakezelő-
viselkedése.

Tárolás: ugyanabban a QSettings-ben, ahol a gyűjtemények csukott állapota
él (`collections.py.collection_setting_key`) — egyetlen kulcs alatt, JSON-
szerializálva (a QSettings backendjei nem kezelnek egyformán listás/
struktúrált értéket, a JSON-string a legegyszerűbb, hordozható forma). Ez a
modul csak TISZTA függvényeket ad — a QSettings I/O-t a hívó (controller-
mixin) végzi, a `schema.py`-hoz (forró fájl, csak az integrátor módosítja)
nincs köze."""

from __future__ import annotations

import json
from dataclasses import dataclass

#: A felhasználói gyűjtemények listája ez alatt az EGY QSettings-kulcs alatt
#: él, JSON-szerializálva.
CUSTOM_COLLECTIONS_SETTING_KEY = "collections/custom"


@dataclass(frozen=True)
class CustomCollection:
    """Egy felhasználói gyűjtemény: név + a beleoszott mappák útvonalai."""

    name: str
    folders: tuple[str, ...] = ()


def parse_custom_collections(raw: str | None) -> tuple[CustomCollection, ...]:
    """A QSettings-ből olvasott nyers JSON-string feldolgozása.

    Hiányzó/sérült/érvénytelen bemenetnél üres tuple — egy hibás/sérült
    beállítás-fájl NEM omlaszthatja el az alkalmazást, legfeljebb a
    gyűjtemények tűnnek el (amíg a felhasználó újra létre nem hozza őket)."""
    if not raw:
        return ()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return ()
    if not isinstance(data, list):
        return ()
    result: list[CustomCollection] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        folders = item.get("folders")
        if not isinstance(folders, list):
            folders = []
        result.append(
            CustomCollection(
                name=name,
                folders=tuple(f for f in folders if isinstance(f, str)),
            )
        )
    return tuple(result)


def serialize_custom_collections(collections: tuple[CustomCollection, ...]) -> str:
    """A gyűjtemény-lista JSON-szerializálása a QSettings-be íráshoz."""
    return json.dumps(
        [{"name": c.name, "folders": list(c.folders)} for c in collections],
        ensure_ascii=False,
    )


def create_collection(
    collections: tuple[CustomCollection, ...], name: str
) -> tuple[CustomCollection, ...]:
    """Új, üres gyűjtemény hozzáadása.

    Üres/csak-szóköz nevet és kis-nagybetű-tűrő duplikátumot csendben
    elutasít (változatlan listát ad vissza) — a hívó UI a validációt már
    elvégzi (pl. az Ok gomb tiltásával), de a réteg saját magát is védi."""
    stripped = name.strip()
    if not stripped:
        return collections
    folded = stripped.casefold()
    if any(c.name.casefold() == folded for c in collections):
        return collections
    return collections + (CustomCollection(name=stripped),)


def rename_collection(
    collections: tuple[CustomCollection, ...], old_name: str, new_name: str
) -> tuple[CustomCollection, ...]:
    """Gyűjtemény átnevezése — a tagmappák megmaradnak. Üres új névnél vagy
    ütköző (más gyűjteményre eső, kis-nagybetű-tűrő) névnél nincs teendő."""
    stripped = new_name.strip()
    if not stripped:
        return collections
    folded = stripped.casefold()
    if any(
        c.name.casefold() == folded and c.name != old_name for c in collections
    ):
        return collections
    return tuple(
        CustomCollection(name=stripped, folders=c.folders)
        if c.name == old_name
        else c
        for c in collections
    )


def delete_collection(
    collections: tuple[CustomCollection, ...], name: str
) -> tuple[CustomCollection, ...]:
    """Gyűjtemény törlése — a benne volt mappák egyszerűen kikerülnek
    belőle (visszakerülnek az alap "Mappák" nézetbe), nem törlődnek."""
    return tuple(c for c in collections if c.name != name)


def move_folder_to_collection(
    collections: tuple[CustomCollection, ...], folder_path: str, target_name: str
) -> tuple[CustomCollection, ...]:
    """A mappa kivétele MINDEN gyűjteményből, majd (ha `target_name` egy
    létező gyűjteményt jelöl) beillesztése oda.

    Az eredeti Picasa mappakezelője is ezt csinálja: egy mappa legfeljebb
    egy egyéni gyűjteményben lehet tagja. Üres `target_name` (vagy nem
    létező gyűjtemény) esetén a mappa egyszerűen kikerül minden egyéni
    gyűjteményből — visszakerül az alap "Mappák" nézetbe."""
    without = tuple(
        CustomCollection(
            name=c.name,
            folders=tuple(f for f in c.folders if f != folder_path),
        )
        for c in collections
    )
    if not target_name:
        return without
    return tuple(
        CustomCollection(name=c.name, folders=c.folders + (folder_path,))
        if c.name == target_name and folder_path not in c.folders
        else c
        for c in without
    )
