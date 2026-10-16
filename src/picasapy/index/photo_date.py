"""A kép dátuma a rendezéshez — a rács és az album KÖZÖS kulcsa (#2486, #2496, #4599).

Az `app/photo_sort.py` és az `index/album_sort.py` is innen hívja: az `index/`
nem importálhat az `app/`-ból, ezért a logika itt él, és a mappa-rendezés
(`app/photo_sort.py`) ide vezet vissza.
"""

from __future__ import annotations

from datetime import datetime


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
ROMLOTT_KULCS = "~"


def datum_kulcs(record) -> str:
    """A dátum-rendezés kulcsa, a romlott fájlidőt is TÚLÉLVE (#2496).

    A `photo_date()` EXIF nélkül a fájl idejéből számol, és ez DOBHAT: a
    `datetime.fromtimestamp` egy romlott indexsorra kivételt ad (mérve:
    `mtime_ns = 10**26` → `OSError: [Errno 75] Value too large for defined
    data type`). Nyersen hívva egyetlen ilyen sor a rendezést — és vele a
    nézet felépítését — kivitte volna.

    **A romlott sor a lista VÉGÉRE kerül, NEM marad ki.** Ez SZÁNDÉKOSAN
    más, mint a fejléc útja (`app/formatting.photo_dates`), ami a rossz sort
    KIHAGYJA: ott egy szélsőértéket keresünk, és egyetlen romlott sor
    évekkel elhúzná a mappa dátumát. Itt viszont minden képnek helyet kell
    kapnia — a kihagyás ELTÜNTETNÉ a képet, ami sokkal nagyobb kár, mint egy
    rossz helyre került sor. A másodlagos kulcs (fájlnév) a romlott sorokra
    is érvényes, tehát egymás közt sem futásfüggő a sorrendjük.
    """
    try:
        return photo_date(record)
    except (OSError, ValueError, OverflowError):
        return ROMLOTT_KULCS
