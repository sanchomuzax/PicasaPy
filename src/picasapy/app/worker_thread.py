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
halmaznak."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any


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
        korlátlanul hosszú futás alatt sok hívással."""
        workers = self._bg_worker_set()

        def _run() -> None:
            try:
                target(*args, **(kwargs or {}))
            finally:
                workers.discard(thread)

        thread = threading.Thread(target=_run, name=name, daemon=True)
        workers.add(thread)
        thread.start()
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
