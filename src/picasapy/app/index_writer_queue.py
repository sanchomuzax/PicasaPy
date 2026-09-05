"""Index-írók sorosítása — egyszerre EGY író, néma kihagyás nélkül (#2389).

## Miért nem elég a futásjelző

A `library_controller` öt helyen indít index-írót. Hármat futásjelző véd
(`_sync_running`, `_dirty_running`, `_sweep_running`): ha épp fut egy író,
az újabb kérés egyszerűen **kimarad**. Az `addWatchedFolder` és a
`scanFolderOnce` viszont őrizetlen volt, tehát futó író mellé is indított
egy másodikat — ugyanaz az `sqlite3.OperationalError` → `syncFailed` tünet,
mint a #1440/#1456-ban.

A kézenfekvő javítás — „nézze ez a kettő is a jelzőket" — **rosszabb lenne
a mai hibánál.** A `rescan()` nyugodtan kihagyhat: az ötperces időzítő öt
perc múlva újrapróbál, és a felhasználó nem is kérte kimondottan. Ez a
kettő viszont közvetlen felhasználói művelet: ha a „Mappa hozzáadása"
némán kimarad, a mappa **nem kerül be a könyvtárba**, és erről semmilyen
jelzés nem születik. A mai hiba legalább hangos.

## Ezért sorosítás, nem kihagyás

A sor egyetlen író-szálon, beadási sorrendben futtatja a munkákat.
Egyszerre így is csak EGY író fut — de mindegyik le is fut. A hívó a
`submit` visszatérési értékéből tudja, hogy a munka azonnal indult-e vagy
várólistára került, és ennek megfelelően tud visszajelezni a
felhasználónak (se néma kihagyás, se néma késleltetés).

## Az „idegen" írókat is megvárja

A másik három belépési pont nem ezen a soron megy. Az `is_busy` visszahívás
ezért a saját jelzőiket kérdezi: amíg bármelyik fut, a sor nem kezd új
munkába. Ez rövid periódusú lekérdezés — a jelzők más szálon állnak át,
és nincs olyan esemény, amire itt rá lehetne kötni.

## A bukott munka nem állítja meg a sort

Ha egy író kivétellel áll le, a sor a következő munkával folytatja, a
kivételt pedig az `on_error` visszahívásnak adja át. Enélkül egyetlen
elszállt beolvasás az összes mögötte várakozó felhasználói kérést
elnyelné — épp azt a néma veszteséget okozva, ami ellen a sor készült.
"""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable

#: Az „idegen" írók lekérdezésének periódusa másodpercben. Elég sűrű ahhoz,
#: hogy a felhasználó ne érzékelje késleltetésnek, és elég ritka ahhoz, hogy
#: a várakozó szál ne terhelje a gépet.
DEFAULT_POLL_S = 0.05

_Munka = Callable[[], None]
_Indito = Callable[..., object]


class IndexWriterQueue:
    """Beadási sorrendben, EGY szálon futtatja az index-írókat."""

    def __init__(
        self,
        start_background: _Indito,
        *,
        is_busy: Callable[[], bool] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        poll_s: float = DEFAULT_POLL_S,
    ) -> None:
        if poll_s <= 0:
            raise ValueError("a lekérdezési periódus csak pozitív lehet")
        self._start_background = start_background
        self._is_busy = is_busy
        self._on_error = on_error
        self._poll_s = poll_s
        self._lock = threading.Lock()
        self._sor: deque[tuple[_Munka, str]] = deque()
        self._fut = False
        #: Akkor van beállítva, ha a sor üres ÉS nem fut munka.
        self._uresjarat = threading.Event()
        self._uresjarat.set()

    def submit(self, munka: _Munka, *, name: str = "picasapy-index-iro") -> bool:
        """Beadja a munkát. `True`, ha azonnal indul; `False`, ha várólistára
        került (a hívó ebből tudja, hogy visszajelzést kell adnia)."""
        with self._lock:
            azonnal = not self._fut
            self._sor.append((munka, name))
            self._uresjarat.clear()
            if self._fut:
                return False
            self._fut = True
        self._start_background(self._futtato, name=name)
        return azonnal

    def wait_idle(self, timeout_s: float) -> bool:
        """Megvárja, amíg a sor kiürül. `False` időtúllépéskor."""
        return self._uresjarat.wait(timeout_s)

    @property
    def pending(self) -> int:
        """A még el nem kezdett munkák száma."""
        with self._lock:
            return len(self._sor)

    def _futtato(self) -> None:
        """Az EGYETLEN író-szál törzse: kiüríti a sort, majd leáll."""
        try:
            while True:
                with self._lock:
                    if not self._sor:
                        self._fut = False
                        self._uresjarat.set()
                        return
                    munka, _name = self._sor.popleft()
                self._varj_az_idegen_irora()
                try:
                    munka()
                except BaseException as hiba:  # noqa: BLE001 — a sor nem állhat meg
                    self._jelentsd(hiba)
        except BaseException:  # noqa: BLE001 — a szál sosem hagyhatja beragadva
            with self._lock:
                self._fut = False
                if not self._sor:
                    self._uresjarat.set()
            raise

    def _varj_az_idegen_irora(self) -> None:
        """Amíg máshonnan indult író fut, nem kezdünk másodikat."""
        if self._is_busy is None:
            return
        while self._is_busy():
            if not self._uresjarat.wait(self._poll_s):
                continue

    def _jelentsd(self, hiba: BaseException) -> None:
        if self._on_error is None:
            return
        try:
            self._on_error(hiba)
        except BaseException:  # noqa: BLE001 — a hibajelzés hibája sem áll meg
            pass
