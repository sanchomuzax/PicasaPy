"""Közös segédosztály a HÁTTÉRSZÁLAS controllerekhez (#438) — a #430-ban
feltárt SIGSEGV-osztály általános megoldása.

GYÖKÉROK (#430, minimál-repróval igazolva): a `threading.Thread(...,
daemon=True)` háttérszálról emitált Qt-jelzés SIGSEGV-vel öli meg a
processzt, ha a küldő QObject közben megsemmisül (pl. a teszt véget ér →
GC), miközben a szál még emitál. A daemon-szál felett az interpreter NEM
várakozik leépléskor, ezért ez a versenyhelyzet bármikor bekövetkezhet —
normál futásban mikroszekundumos az ablak, coverage-tracing alatt viszont
nagyságrendekkel tágabb, ezért csak alkalomszerűen, a CI-ben jelentkezik.

A #430 a `WebExportController`-t javította: nyilvántartott `self._worker`
+ `waitForExport(timeout_s)`/`exportRunning()`, a teszt-fixture
teardownjában bevárva, AMÍG A CONTROLLER MÉG ÉL. Ez a modul UGYANEZT a
mintát adja mixinként, hogy a többi controllerban ne kilencszer másolva
éljen (#438 1. pont).

`BackgroundWorkerMixin` — HALMAZ-alapú nyilvántartás (nem egyetlen
`_worker`-mező): több controllernél (pl. `LibraryMixin`, `PhotoOpsMixin`)
egyszerre TÖBB háttérszál is futhat (különböző mappák/fotók egymástól
függetlenül) — a halmaz ezt is helyesen fedi, az egyetlen-szálas eset
(pl. `DiscoveryController`) speciális esete csupán legfeljebb egy elemű
halmaznak.

#505: `_start_background` MINDEN hívása automatikusan bejelentkezik az
alkalmazás-szintű `AppBusyRegistry`-be (`busy_registry.py`) — az alsó kék
sáv animációja ezért MINDEN, ezen a mixinen át indított háttérmunkánál
magától megjelenik (a jelenlegieknél ÉS a jövőbelieknél is), anélkül hogy
az egyes controllereknek külön be kellene jelentkezniük. A bejelentkezés
`try`/`finally`-vel párosított — hibával leálló munka is lezárja a
bejegyzést, különben a csík örökre pörögne."""

from __future__ import annotations

import threading
import time
import weakref
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from .busy_registry import get_app_busy_registry

#: **FOLYAMAT-SZINTŰ szál-nyilvántartás (#988/#999).** A példányonkénti
#: `_bg_workers` halmaz mellett minden `_start_background` ide is
#: bejelentkezik. Ok: a lebontásért felelős fél (teszt-fixture,
#: alkalmazás-kilépés) eddig **kézzel felsorolta**, mely controllereket vár
#: be — és a lista elcsúszott. A `qml_functional/conftest.py` öt controllert
#: várt be, miközben a fixture ennél többet hozott létre (`EditController`,
#: `FaceScanController`), a két `QThreadPool`-os szolgáltatót pedig
#: egyáltalán nem. Ebből lett két, véletlenszerűen pirosló CI-bukás.
#:
#: Ez a halmaz azért folyamat-szintű, hogy **ne lehessen elfelejteni**: aki
#: a mixinen át indít szálat, automatikusan fedve van, a jövőbeli
#: controllerek is.
_ALL_WORKERS: set[threading.Thread] = set()
_ALL_WORKERS_LOCK = threading.Lock()


@runtime_checkable
class PoolOwner(Protocol):
    """Saját `QThreadPool`-t tartó objektum (bélyegkép-szolgáltatók)."""

    def wait_for_done(self, msecs: int = ...) -> bool: ...


#: A `QThreadPool`-t tartó szolgáltatók — GYENGE hivatkozással, hogy a
#: nyilvántartás ne tartsa életben őket (a tesztek sok példányt hoznak
#: létre). A `QRunnable`-ök ugyanúgy Qt-objektumokat érnek el, mint a
#: daemon-szálak, tehát ugyanaz a #430-as osztály fenyegeti őket.
_POOL_OWNERS: "weakref.WeakSet[PoolOwner]" = weakref.WeakSet()


def register_pool_owner(owner: PoolOwner) -> None:
    """Bejelentkezés a folyamat-szintű bevárásba (`wait_for_done`-nal).

    A `QThreadPool`-t tartó osztályok a `__init__`-jükben hívják — így a
    `wait_for_all_background_workers` rájuk is vár, anélkül hogy bárkinek
    fel kellene sorolnia őket."""
    _POOL_OWNERS.add(owner)


def running_background_workers() -> tuple[str, ...]:
    """A még futó, nyilvántartott háttérszálak nevei (hibaüzenethez)."""
    with _ALL_WORKERS_LOCK:
        return tuple(w.name or "<névtelen>" for w in _ALL_WORKERS if w.is_alive())


def wait_for_all_background_workers(timeout_s: float = 30.0) -> bool:
    """MINDEN nyilvántartott háttérmunka bevárása — szálak és pool-ok.

    Egyetlen hívás, ami a folyamat összes `_start_background`-szálát és
    minden bejelentkezett `QThreadPool`-t bevár. A lebontásért felelős fél
    ezt hívja, **amíg a controllerek még élnek** (#430/#438) — így a
    bevárandók listája nem csúszhat el a valósághoz képest.

    `True`, ha a keretidőn belül minden leállt."""
    deadline = time.monotonic() + timeout_s
    mind_leallt = True
    with _ALL_WORKERS_LOCK:
        workers = tuple(_ALL_WORKERS)
    for worker in workers:
        worker.join(max(0.0, deadline - time.monotonic()))
        if worker.is_alive():
            mind_leallt = False
    for owner in tuple(_POOL_OWNERS):
        remaining_ms = int(max(0.0, deadline - time.monotonic()) * 1000)
        if not owner.wait_for_done(remaining_ms):
            mind_leallt = False
    return mind_leallt


class BackgroundWorkerMixin:
    """Daemon-szálak indítása nyilvántartással + determinista bevárás.

    Használat: a `threading.Thread(target=worker, daemon=True).start()`
    hívás helyett `self._start_background(worker)`. A leépítésért felelős
    fél (teszt-fixture teardownja, alkalmazás-kilépés) a controller még
    élő példányán hívja a `waitForBackgroundWorkers(timeout_s)`-t."""

    _bg_workers: set[threading.Thread]

    def _bg_worker_set(self) -> set[threading.Thread]:
        """Lusta inicializálás — a mixinnek nincs `__init__`-je (a #150
        mintája: nem kell az integrátor `__init__`-jét módosítani)."""
        try:
            return self._bg_workers
        except AttributeError:
            self._bg_workers = set()
            return self._bg_workers

    def _start_background(
        self,
        target: Callable[..., None],
        *,
        args: Sequence[Any] = (),
        kwargs: Mapping[str, Any] | None = None,
        name: str | None = None,
    ) -> threading.Thread:
        """Egy `target` HÁTTÉRSZÁLON indítása, nyilvántartva.

        A szál a saját végén automatikusan kikerül a nyilvántartásból —
        a halmaz mindig csak a TÉNYLEG futó szálakat tartalmazza, nem nő
        korlátlanul hosszú futás alatt sok hívással.

        #505: a busy-nyilvántartás bejelentkezése/kijelentkezése ITT, EGY
        helyen történik — a hívó controllernek nem kell külön hívnia. A
        `begin()` a hívó (jellemzően GUI-) szálon fut, MIELŐTT a szál
        elindulna; az `end()` a `finally`-ben — kivétellel leálló munkánál
        is, hogy a csík ne pörögjön örökre."""
        workers = self._bg_worker_set()
        registry = get_app_busy_registry()
        registry.begin()

        def _run() -> None:
            try:
                target(*args, **(kwargs or {}))
            finally:
                workers.discard(thread)
                # #988/#999: a folyamat-szintű nyilvántartásból is
                with _ALL_WORKERS_LOCK:
                    _ALL_WORKERS.discard(thread)
                registry.end()

        thread = threading.Thread(target=_run, name=name, daemon=True)
        workers.add(thread)
        with _ALL_WORKERS_LOCK:
            _ALL_WORKERS.add(thread)
        try:
            thread.start()
        except BaseException:
            # #550: ha a `start()` elbukik (pl. `RuntimeError: can't start new
            # thread`), a `_run` — és vele a `finally` ága — SOSEM fut le. A
            # `begin()` párját ilyenkor itt kell megadni, különben a kék csík
            # örökre pörögne, a halmazban pedig egy halott szál ragadna bent.
            workers.discard(thread)
            with _ALL_WORKERS_LOCK:
                _ALL_WORKERS.discard(thread)
            registry.end()
            raise
        return thread

    def backgroundWorkersRunning(self) -> bool:  # noqa: N802 — a webexport_controller QML-stílusú elnevezését követi
        """Fut-e éppen legalább egy nyilvántartott háttérszál?"""
        return any(worker.is_alive() for worker in self._bg_worker_set())

    def waitForBackgroundWorkers(self, timeout_s: float = 30.0) -> bool:  # noqa: N802
        """Megvárja az ÖSSZES nyilvántartott háttérszál leállását;
        `True`, ha mindegyik leállt (vagy nem is volt futó szál) a
        `timeout_s` teljes időkeretén belül.

        A szálak `daemon`-ok, ezért az interpreter leépítése nem várja meg
        őket: ha a processz úgy ér véget, hogy egy szál még Qt-jelzést
        emitál egy közben felszámolt objektumnak, a futás SIGSEGV-vel
        omlik össze (#430). Aki a controller élettartamát zárja (teszt-
        fixture, alkalmazás-kilépés), ezt hívja."""
        deadline = time.monotonic() + timeout_s
        all_joined = True
        for worker in tuple(self._bg_worker_set()):
            remaining = max(0.0, deadline - time.monotonic())
            worker.join(remaining)
            if worker.is_alive():
                all_joined = False
        return all_joined
