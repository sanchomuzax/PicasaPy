"""#1436: a mappa TARTALMÁNAK rendezése — a `Folder::SortFolderBy` magja.

A „Mappa rendezésének alapja ▸" menü (spec: `ui-audit-context-menus.md`
6.3) a mappa KÉPEIT rendezi, nem a mappákat. A mappák egymáshoz
viszonyított sorrendje két MÁSIK beállításé: a rácsé a Mappa ▸ Rendezés
(`folderSort`, #321; #1454-ig tévesen a Nézet ▸ Mappanézet alatt is), a bal
hasábé a saját menüje (`paneSort`, #461/3).

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
    fájl BEFAGYASZTOTT (első látáskori) ideje.

    A Picasa is így datálja a képet: a felvételi dátum az elsődleges, és
    csak annak hiányában esik vissza a fájlidőre — így az EXIF nélküli
    képek (szkennelt lapok, letöltött rajzok) sem csúsznak egy kupacba a
    lista végére. Mindkét ág ISO-alakot ad, ezért összehasonlíthatók.

    **#2486 — a fájlidő nem az élő `mtime`.** A tartalék a
    `record.sort_mtime_ns`, vagyis az az idő, amit a mappa ELSŐ
    beolvasásakor láttunk, és amit az index azóta őriz. Az élő `mtime`-ot
    bármi átírhatja — mentés, szinkron, másolás, és a #2491 óta a saját
    ini-írásunk `photo_touch`-a is —, és a rács ettől átrendeződött. Az
    eredeti Picasa ugyanezt a dátumot a katalógusába fagyasztja a
    beolvasáskor, és a pásztázó soha nem frissíti
    (`docs/specs/pmp-database.md` 10.1/10.3–10.4); a döntés lapja:
    `docs/decisions/befagyasztott-fajlido.md`.

    A befagyasztott érték hiányában (v17 előtti index, kézzel épített
    rekord) a `sort_mtime_ns` az élő `mtime`-ot adja — a viselkedés
    ilyenkor a #2486 ELŐTTI, tehát az index eldobása nem ronthat el semmit.
    """
    if record.taken_at:
        return record.taken_at
    return datetime.fromtimestamp(
        record.sort_mtime_ns / 1_000_000_000
    ).isoformat()


#: #2496: a romlott fájlidejű rekord rendezési helye — a lista VÉGE.
#: Bármely valódi ISO-dátumnál nagyobb sztring; a `~` a nyomtatható
#: ASCII vége, tehát számjeggyel kezdődő dátum SOHA nem előzi meg.
_ROMLOTT_KULCS = "~"


def _datum_kulcs(record) -> str:
    """A dátum-rendezés kulcsa, a romlott fájlidőt is TÚLÉLVE (#2496).

    A `photo_date()` EXIF nélkül a fájl idejéből számol, és ez DOBHAT: a
    `datetime.fromtimestamp` egy romlott indexsorra kivételt ad (mérve:
    `mtime_ns = 10**26` → `OSError: [Errno 75] Value too large for defined
    data type`). Nyersen hívva egyetlen ilyen sor a rács rendezését — és
    vele a nézet felépítését — kivitte volna.

    **A romlott sor a lista VÉGÉRE kerül, NEM marad ki.** Ez SZÁNDÉKOSAN
    más, mint a fejléc útja (`formatting.photo_dates`), ami a rossz sort
    KIHAGYJA: ott egy szélsőértéket keresünk, és egyetlen romlott sor
    évekkel elhúzná a mappa dátumát. Itt viszont minden képnek helyet kell
    kapnia — a kihagyás ELTÜNTETNÉ a képet a rácsból, ami sokkal nagyobb
    kár, mint egy rossz helyre került sor. A másodlagos kulcs (fájlnév) a
    romlott sorokra is érvényes, tehát egymás közt sem futásfüggő a
    sorrendjük.
    """
    try:
        return photo_date(record)
    except (OSError, ValueError, OverflowError):
        return _ROMLOTT_KULCS


def _sort_key(sort_mode: str):
    """Rendezőkulcs egy mappa-blokkon belül."""
    if sort_mode == "date":
        return lambda r: (_datum_kulcs(r), r.name.casefold())
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
