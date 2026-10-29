"""Látható kérések és alacsony prioritású előtöltés ütemezése."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from .thumbnail_provider_constants import (
    _PREFETCH_QUEUE_CAPACITY,
    _PREFETCH_THUMB_PRIORITY,
    _VISIBLE_THUMB_PRIORITY,
)
from .thumbnail_provider_jobs import _PrefetchJob, _ThumbJob, _ThumbResponse

_log = logging.getLogger("picasapy.app.thumbnail_provider")


def _request_image_response(provider, photo_id: str, requested_size) -> _ThumbResponse:
    """Aszinkron belépési pont (a Qt a saját olvasószálán hívja): a
    munka a poolba kerül, a válasz azonnal visszamegy.

    A válasz #1457 óta bekerül a provider nyilvántartásába is, és csak
    a motor általi megszüntetéskor (`destroyed`) kerül ki onnan."""
    response = _ThumbResponse()
    token = next(provider._response_tokens)
    with provider._live_lock:
        provider._live_responses[token] = response
    # A kötés SZÁNDÉKOSAN nem zárja magába a választ (csak a tokent),
    # különben a nyilvántartás sosem ürülne. A `destroyed` átadja a
    # megszűnő objektumot is — azt eldobjuk (`*_`): ilyenkor a C++
    # oldal már érvénytelen, hozzányúlni tilos.
    response.destroyed.connect(
        lambda *_, token=token: provider._release_response(token)
    )
    provider._pool.start(
        _ThumbJob(provider, photo_id, response), _VISIBLE_THUMB_PRIORITY
    )
    return response


def _prefetch_images(provider, photo_ids: Iterable[str]) -> int:
    """A megadott bélyegkép-azonosítók alacsony prioritású előtöltése.

    A render-mag a már meglévő `ThumbnailCache`-t és a szűrt képek
    memóriatárát használja. A sorosított futás egy pool-helyet legfeljebb
    egy kép idejére foglal; a látható kérések közben a Qt magasabb
    prioritással előzik meg a sorban álló előtöltéseket.
    """
    uj_azonositok: list[str] = []
    prefix = "image://thumbs/"
    for value in photo_ids:
        photo_id = str(value or "").strip()
        if photo_id.startswith(prefix):
            photo_id = photo_id[len(prefix):]
        if photo_id:
            uj_azonositok.append(photo_id)
    if not uj_azonositok:
        return 0

    indit = False
    hozzaadott = 0
    with provider._prefetch_lock:
        uj_sor = []
        for photo_id in uj_azonositok:
            if photo_id in provider._prefetch_pending:
                continue
            provider._prefetch_pending.add(photo_id)
            uj_sor.append(photo_id)
        # A friss görgetési cél kerüljön a régebbi, még sorban álló
        # tartomány elé, de annak eredeti sorrendjét őrizze meg.
        for photo_id in reversed(uj_sor):
            provider._prefetch_queue.appendleft(photo_id)
        hozzaadott = len(uj_sor)
        queue_capacity = max(_PREFETCH_QUEUE_CAPACITY, hozzaadott)
        while len(provider._prefetch_queue) > queue_capacity:
            eldobott = provider._prefetch_queue.pop()
            provider._prefetch_pending.discard(eldobott)
        if provider._prefetch_queue and not provider._prefetch_scheduled:
            provider._prefetch_scheduled = True
            indit = True
    if indit:
        provider._pool.start(
            _PrefetchJob(provider), _PREFETCH_THUMB_PRIORITY
        )
    return hozzaadott


def _run_prefetch_job(provider) -> None:
    """Egy cache-felmelegítő munka; a következő csak a befejezés után indul."""
    with provider._prefetch_lock:
        if not provider._prefetch_queue:
            provider._prefetch_scheduled = False
            return
        photo_id = provider._prefetch_queue.popleft()
    try:
        # Előtöltéskor nincs képernyő-válasz és nem jelezzük a felületnek
        # látható betöltésként. A render-mag ugyanazokat a gyorsítótárakat
        # tölti, amelyeket a rendes requestImage is használ.
        image = provider._render(photo_id)
        if image.isNull():
            _log.debug("thumbnail előtöltése sikertelen: %s", photo_id)
    except Exception:  # noqa: BLE001 — háttérfeladat nem szakíthatja meg a görgetést
        _log.exception("thumbnail-előtöltési hiba: %s", photo_id)
    finally:
        with provider._prefetch_lock:
            provider._prefetch_pending.discard(photo_id)
            van_kovetkezo = bool(provider._prefetch_queue)
            if not van_kovetkezo:
                provider._prefetch_scheduled = False
        if van_kovetkezo:
            provider._pool.start(
                _PrefetchJob(provider), _PREFETCH_THUMB_PRIORITY
            )


def _release_response(provider, token: int) -> None:
    """A motor elpusztította a választ — elengedhetjük a hivatkozást."""
    with provider._live_lock:
        provider._live_responses.pop(token, None)


def _live_response_count(provider) -> int:
    """A nyilvántartott (a motor által még el nem engedett) válaszok
    száma — a #1457 őr-tesztek ebből látják, hogy a nyilvántartás
    ürül, azaz nem szivárog."""
    with provider._live_lock:
        return len(provider._live_responses)
