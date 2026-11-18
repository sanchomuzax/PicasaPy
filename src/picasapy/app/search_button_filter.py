"""A keresőszöveg és a csillag-, arc-, geocímke-gomb közös szűrője (#7191).

Az eredeti `0x0043f9a0` a keresőszöveg szavait és a gombok belső szójeleit
(`]star`, `]face`, `]geo`) EGY pozitív szólistában kapja, a találat a lista
minden szavának metszete (`0x0043fda4`, `0x00413290`): a szöveg és a gomb ÉS
kapcsolatban van. Itt ugyanez áll: a keresés találatait a bekapcsolt gomb
saját nézetének képeivel metsszük.

A három gomb ma is kizárja egymást (egyszerre egy lehet bekapcsolva); a
film, az online és a másodpéldány gomb és a kor-csúszka nem ide tartozik, azok
a mai nézetmódjukban maradnak (E1b).
"""

from __future__ import annotations

from collections.abc import Callable

from picasapy.index import geotagged_photos, photos_with_faces, starred_photos

#: a keresőszöveggel kombinálható gombok; a névsor egyben a nézetmód-nevük
STAR = "starred"
FACES = "faces"
GEO = "geo"
BUTTON_FILTERS = (STAR, FACES, GEO)

#: a keresés nézetmódjai (szöveges keresés, mappára szűkítve is)
SEARCH_MODES = ("search", "search-folder")

_BUTTON_QUERIES: dict[str, Callable] = {
    STAR: starred_photos,
    FACES: photos_with_faces,
    GEO: geotagged_photos,
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
