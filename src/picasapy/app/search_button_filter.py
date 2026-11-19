"""A keresőszöveg és a csillag-, arc-, geocímke-, filmgomb közös szűrője.

Az eredeti `0x0043f9a0` a keresőszöveg szavait és a gombok belső szójeleit
(`]star`, `]face`, `]geo`) EGY pozitív szólistában kapja, a találat a lista
minden szavának metszete (`0x0043fda4`, `0x00413290`): a szöveg és a gomb ÉS
kapcsolatban van. Itt ugyanez áll: a keresés találatait a bekapcsolt gomb
saját nézetének képeivel metsszük. A film gomb a meglévő `video_photos`
indexlekérdezésre épül (#7264).

A csillag-, arc- és geocímke-gomb eddigi állapota változatlan; a filmgomb
szintén a keresőszöveggel közös állapotot használ (#7264). Az online és a
másodpéldány gomb nem tartozik ehhez a gépezethez.

A kor-csúszka (#7255) ugyanígy a keresés állapotának része: a találat a
szöveg ÉS a `kor <= N nap` metszete (`intersect_with_age`), mérve az eredeti
Picasán (`picasa-colab-jobs` #748). Szöveg nélkül a csúszka önmagában
dátumszűrő a teljes könyvtáron (`photos_up_to_age`).
"""

from __future__ import annotations

from collections.abc import Callable

from picasapy.index import (
    geotagged_photos,
    photos_up_to_age,
    photos_with_faces,
    starred_photos,
    video_photos,
)

#: a keresőszöveggel kombinálható gombok; a névsor egyben a nézetmód-nevük
STAR = "starred"
FACES = "faces"
GEO = "geo"
VIDEOS = "videos"
BUTTON_FILTERS = (STAR, FACES, GEO, VIDEOS)

#: a keresés nézetmódjai (szöveges keresés, mappára szűkítve is)
SEARCH_MODES = ("search", "search-folder")

#: azok a nézetmódok, amelyekben a kor-csúszka állása érvényes marad (#7255):
#: a saját `age` nézet és a keresés; bármely más nézet betöltése törli
AGE_KEEPING_MODES = ("age", *SEARCH_MODES)

_BUTTON_QUERIES: dict[str, Callable] = {
    STAR: starred_photos,
    FACES: photos_with_faces,
    GEO: geotagged_photos,
    VIDEOS: video_photos,
}


def button_records(conn, button: str) -> tuple:
    """A gomb SAJÁT nézetének képei (a keresőszöveg nélküli találat)."""
    return _BUTTON_QUERIES[button](conn)


def intersect_with_button(conn, records, button: str) -> tuple:
    """A keresés találatai a bekapcsolt gomb képeivel metszve.

    Üres `button` esetén a találatok változatlanul maradnak. A metszet a
    találatok sorrendjét őrzi, a tagságot a kép azonosítója dönti el."""
    if not button:
        return tuple(records)
    members = {record.id for record in button_records(conn, button)}
    return tuple(record for record in records if record.id in members)


def intersect_with_age(conn, records, cutoff: str) -> tuple:
    """A keresés találatai a `cutoff` (ISO időpont) UTÁN készült képekkel metszve.

    A tagságot ugyanaz a lekérdezés adja, mint a szöveg nélküli kor-nézetet
    (`photos_up_to_age`), így a két út nem térhet el. A dátum NÉLKÜLI kép
    kimarad (kora nincs). A metszet a találatok sorrendjét őrzi."""
    members = {record.id for record in photos_up_to_age(conn, cutoff)}
    return tuple(record for record in records if record.id in members)
