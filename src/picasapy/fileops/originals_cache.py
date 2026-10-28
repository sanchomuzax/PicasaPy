"""A kísérő-mappák névlistájának gyorstára egy kötegelt művelet alatt (#1452).

A `picasapy.fileops.originals` szétbontott része: a gyorstár és a könyvelő
segédei. A publikus nevek (`listing_cache`) a `originals`-ból is elérhetők.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

#: A kísérő-mappák neveinek gyorstára EGY kötegelt művelet idejére (#1452).
#:
#: `None`, amíg senki nem nyitott `listing_cache()` hatókört - ilyenkor
#: minden olvasás friss listázás, pontosan úgy, mint korábban. A
#: `ContextVar` (és nem modulszintű dict) azért kell, mert a felület a
#: kötegelt műveleteket munkaszálon is futtathatja: minden szál SAJÁT,
#: üres kontextussal indul, tehát nem örökli meg egy másik szál félkész
#: gyorstárát.
_LISTINGS: ContextVar[dict[str, list[str]] | None] = ContextVar(
    "picasapy_originals_listings", default=None
)


@contextmanager
def listing_cache() -> Iterator[None]:
    """A kísérő-mappákat MAPPÁNKÉNT EGYSZER listázza a hatókörön belül (#1452).

    Mit old meg: a kötegelt áthelyezés képenként KÉT teljes
    könyvtárlistázást végzett - egyet a célmappa eredeti-mappáira
    (`originals_slot_free`), egyet a forráséira (`plan_original_moves`).
    500 képnél ez 999 listázás volt. A gyűjtemény NAS-on van, mért
    napló-korláttal (#1146), ahol egy listázás drága.

    Hogyan marad PONTOS: a gyorstár nem „elévül", hanem KÖNYVELT. Ez a
    modul minden saját mozgatását/másolását/törlését azonnal átvezeti a
    tárolt névlistán (`_moved`, `_copied`, `_discarded`,
    `_remove_if_empty`), tehát a hatókörön belül a listák együtt mozognak
    a lemezzel. Amit a modul NEM ír - a `.picasa.ini` és a `.bak` párja -,
    az a keresésben sem vesz részt: a pillanatkép-minta a kép
    törzsnevével kezdődik (`<név>.<N><kiterjesztés>`), a foglaltság-
    vizsgálat pedig a konkrét névre `exists()`-tel kérdez, nem a listából.

    Egy PÁRHUZAMOS író (a futó Picasa) közbeírását a hatókörön belül nem
    látjuk - de a művelet enélkül is versenyzik vele, és a tényleges
    ütközést a `_reject_unsafe_targets` közvetlenül a mozgatás előtt
    ellenőrzi, friss `exists()`-tel.

    A hatókört a kötegelt út nyitja (`fileops/batch.py`); az egyfájlos
    utak nélküle futnak, ott nincs mit megtakarítani.
    """
    token = _LISTINGS.set({})
    try:
        yield
    finally:
        _LISTINGS.reset(token)


def _read_names(directory: Path) -> list[str]:
    """A könyvtár bejegyzéseinek NEVE; üres lista, ha nem olvasható.

    `os.scandir`, nem `iterdir()`: ugyanaz a rendszerhívás, de nem
    gyártunk `Path`-t minden bejegyzéshez - a 250 000 fájlos gyűjteményben
    ez a kötegelt úton mérhető."""
    try:
        with os.scandir(directory) as entries:
            return [entry.name for entry in entries]
    except OSError:
        return []


def _entry_names(directory: Path) -> tuple[str, ...]:
    """A könyvtár bejegyzés-nevei, a `listing_cache()` hatókörén belül
    mappánként EGYETLEN listázásból (#1452)."""
    cache = _LISTINGS.get()
    if cache is None:
        return tuple(_read_names(directory))
    key = str(directory)
    names = cache.get(key)
    if names is None:
        names = _read_names(directory)
        cache[key] = names
    return tuple(names)


def _cache_added(directory: Path, name: str) -> None:
    """Új név a mappában - a gyorstár együtt mozog a lemezzel."""
    cache = _LISTINGS.get()
    if cache is None:
        return
    names = cache.get(str(directory))
    if names is not None and name not in names:
        names.append(name)


def _cache_removed(directory: Path, name: str) -> None:
    """Eltűnt név a mappában."""
    cache = _LISTINGS.get()
    if cache is None:
        return
    names = cache.get(str(directory))
    if names is not None and name in names:
        names.remove(name)


def _cache_unknown(directory: Path) -> None:
    """A mappa tartalma bizonytalanná vált (félbemaradt írás) - a következő
    kérdésre ismét listázzunk. Az elfelejtés SOSEM ad rossz választ, csak
    egy listázásba kerül."""
    cache = _LISTINGS.get()
    if cache is not None:
        cache.pop(str(directory), None)
