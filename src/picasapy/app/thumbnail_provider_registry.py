"""A provider fotóregiszterének kezelése és indexből való feloldása."""

from __future__ import annotations

import logging

from picasapy.index import PhotoRecord, open_index, photo_by_id

_log = logging.getLogger("picasapy.app.thumbnail_provider")


def _register_photos(provider, photos: tuple[PhotoRecord, ...]) -> None:
    """#142: a regisztráció csak a (immutábilis) rekordokat jegyzi meg —
    a filters= lánc parse-a LUSTA, először requestImage-kor fut (és az
    eredmény lánconként cache-elődik), így 50k fotó regisztrálása is
    olcsó marad."""
    updated = {str(photo.id): photo for photo in photos}
    with provider._registry_lock:
        provider._registry = updated


def _register_additional_photos(provider, photos: tuple[PhotoRecord, ...]) -> None:
    """#23: fotók hozzáadása a MEGLÉVŐ regisztráció mellé (nem cseréli
    le, ellentétben a `register_photos`-szal) — az Import forrásból
    előnézete így nem takarja el a fő könyvtár épp regisztrált
    bélyegképeit, amíg az Import-dialógus nyitva van. A hívó felelőssége
    (ld. `import_source_controller.py`) ütközésmentes, saját id-
    tartományt használni (pl. negatív id-k), hogy sose írjon felül
    valódi könyvtárbeli fotót.

    FOGLALT (negatív) id-tartományok — az egyszerre nyitva lévő
    dialógusok se üssék egymást:
      * `-1`-től lefelé: Import forrásból előnézet
        (`import_source_controller._preview_photo_record`);
      * `-1_000_000`-tól lefelé: duplikátum-kereső találatok
        (`dedup_controller.DEDUP_THUMB_ID_BASE`, #298);
      * `-8_000_000_000_000_000` körül: parancssoros gyorsnézegető
        (#5762; a kiszámítható QML-számábrázolási tartományban).
    Új hívó ide vegyen fel magának új sávot."""
    extra = {str(photo.id): photo for photo in photos}
    with provider._registry_lock:
        provider._registry = {**provider._registry, **extra}


def _photo_record(provider, photo_id: str) -> PhotoRecord | None:
    """A regisztrált fotó rekordja (#338 effekt-bélyegképek): a
    szerkesztőpanel effekt-gombjainak bélyegkép-providere (
    `effect_thumbnails.py`) ebből olvassa ki az útvonalat — nem kell
    neki saját, párhuzamos fotó-regisztrációt vezetnie."""
    return provider._registry.get(str(photo_id))


def _unregister_additional_photos(provider, ids: tuple[str, ...]) -> None:
    """A `register_additional_photos`-szal felvett bejegyzések
    eltávolítása (pl. új szkennelés előtt vagy a dialógus zárásakor) —
    a valódi könyvtár bejegyzéseit nem érinti."""
    if not ids:
        return
    excluded = set(ids)
    with provider._registry_lock:
        provider._registry = {
            key: value
            for key, value in provider._registry.items()
            if key not in excluded
        }


def _photo_for_render(provider, photo_id: str) -> PhotoRecord | None:
    """Az album-regisztrációból, majd szükség esetén az indexből old fel.

    A `requestImageResponse` pool-szálán fut, ezért az indexkapcsolatot
    helyben nyitja meg és zárja le; SQLite-kapcsolatot nem oszt meg a Qt
    szálai között. Az indexből talált rekordot immutábilis szótárcserével
    jegyzi meg a következő kéréshez.
    """
    key = photo_id.split("?", 1)[0]
    photo = provider._registry.get(key)
    if photo is not None or provider._index_path is None:
        return photo
    try:
        index_id = int(key)
    except ValueError:
        return None

    with open_index(provider._index_path) as conn:
        photo = photo_by_id(conn, index_id)
    if photo is None:
        return None

    with provider._registry_lock:
        # Egy közben érkezett album-regisztráció vagy másik feloldó
        # friss rekordja elsőbbséget élvezzen.
        current = provider._registry
        existing = current.get(key)
        if existing is not None:
            return existing
        provider._registry = {**current, key: photo}
    return photo
