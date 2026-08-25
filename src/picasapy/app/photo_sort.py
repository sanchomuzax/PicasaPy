"""#1436: a mappa TARTALMÁNAK rendezése — a `Folder::SortFolderBy` magja.

A „Mappa rendezésének alapja ▸" menü (spec: `ui-audit-context-menus.md`
6.3) a mappa KÉPEIT rendezi, nem a mappákat. A mappák egymáshoz
viszonyított sorrendje két MÁSIK beállításé: a rácsé a Nézet ▸ Mappanézet
(`folderSort`, #321), a bal hasábé a saját menüje (`paneSort`, #461/3).

Az itteni függvény ezért **mappa-blokkon belül** rendez: a rács a képeket
egymást követő, azonos mappájú futamokban rajzolja (a fejléceket ugyanezen
futamokból számolja a `formatting.build_feed_groups`), és pontosan egy ilyen
blokk a menü hatóköre. A futamhatárok NEM mozdulnak, csak a blokkon belüli
sorrend — így a mappák sorrendje garantáltan érintetlen marad.

Irány: az alapérték MINDHÁROM szempontnál NÖVEKVŐ — dátumnál a legrégebbi
elöl, a legújabb a VÉGÉN (a tulajdonos megfigyelése a Picasa 3-ról, #1436).
A „Fordított sorrend" fordítja meg.
"""

from __future__ import annotations

from datetime import datetime

# QSettings-kulcsok — a `view/` névtér a többi nézet-beállításé is
# (folderSort, paneSort, thumbCaption, showHidden).
FOLDER_PHOTO_SORT_KEY = "view/folderPhotoSort"
FOLDER_PHOTO_SORT_REVERSE_KEY = "view/folderPhotoSortReverse"

# A menü három szempontja (spec 6.3: Dátum · Név · Méret · Fordított
# sorrend) — a „legutóbbi változtatás" a BAL HASÁB menüjéé, ide nem való.
SORT_MODES = ("date", "name", "size")

# Az alapérték a fájlnév: ez volt a viselkedés a #1436 előtt is, tehát aki
# nem nyúl a menühöz, semmilyen változást nem lát.
DEFAULT_SORT_MODE = "name"

_TRUE_VALUES = (True, "true", "1")


def coerce_sort_mode(value) -> str:
    """Mentett beállítás → érvényes szempont; ismeretlen érték = fájlnév."""
    return value if value in SORT_MODES else DEFAULT_SORT_MODE


def coerce_reverse_flag(value) -> bool:
    """Mentett beállítás → bool (a QSettings bool-t és szöveget is adhat)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1")
    return value in _TRUE_VALUES


def photo_date(record) -> str:
    """A kép dátuma a rendezéshez: EXIF-felvételi dátum, ha van, egyébként a
    FÁJL ideje.

    A Picasa is így datálja a képet: a felvételi dátum az elsődleges, és
    csak annak hiányában esik vissza a fájlidőre — így az EXIF nélküli
    képek (szkennelt lapok, letöltött rajzok) sem csúsznak egy kupacba a
    lista végére. Mindkét ág ISO-alakot ad, ezért összehasonlíthatók.
    """
    if record.taken_at:
        return record.taken_at
    return datetime.fromtimestamp(record.mtime_ns / 1_000_000_000).isoformat()


def _sort_key(sort_mode: str):
    """Rendezőkulcs egy mappa-blokkon belül."""
    if sort_mode == "date":
        return lambda r: (photo_date(r), r.name.casefold())
    if sort_mode == "size":
        return lambda r: (r.size, r.name.casefold())
    return lambda r: r.name.casefold()


def sort_folder_blocks(records, sort_mode: str, reverse: bool = False) -> tuple:
    """A képek újrarendezése MAPPA-BLOKKONKÉNT (a blokkhatárok maradnak).

    Új sorozatot ad vissza, a bemenetet nem módosítja. Ismeretlen
    szempontnál a fájlnév-sorrend a visszaesés.
    """
    records = tuple(records)
    if not records:
        return records
    key = _sort_key(coerce_sort_mode(sort_mode))
    ordered: list = []
    block: list = []
    current: str | None = None
    for record in records:
        if record.folder_path != current:
            ordered.extend(sorted(block, key=key, reverse=reverse))
            block = []
            current = record.folder_path
        block.append(record)
    ordered.extend(sorted(block, key=key, reverse=reverse))
    return tuple(ordered)
