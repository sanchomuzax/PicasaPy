"""Alkalmazás-szintű, laza csatolású busy-nyilvántartás (#505).

**A probléma**: a `LibraryMixin.isWorking`/`busyChanged` (#70) csak a
szinkron/indexelés és a bélyegkép-betöltés állapotát könyvelte — minden
más háttérmunka (kötegelt effekt, export, webexport, import-forrás,
duplikátum-keresés, arc-szkennelés, adatbázis-áthelyezés) NÉMÁN futott: az
alsó kék sáv animációja nem jelezte, hogy a program dolgozik. A #504-es
hibánál (percekig számoló, akkor még főszálas Lomo/Holga-effekt) éppen ez
a némaság tette megkülönböztethetetlenné a lassúságot a befagyástól.

**A megoldás**: EGYETLEN, folyamat-szintű számláló (`AppBusyRegistry`),
amihez BÁRMELY controller csatlakozhat — `begin()`-nel jelenti be, hogy
munka indult, `end()`-del, hogy véget ért —, anélkül hogy a controllerek
egymásra vagy egy közös ősosztályra (`AppController`) hivatkoznának. A
`get_app_busy_registry()` egy modul-szintű, lusta-inicializált szingleton
példányt ad — ez a laza csatolás: az importáló controller csak ezt a
függvényt hívja, semmi mást.

A `BackgroundWorkerMixin._start_background` (`worker_thread.py`) MINDEN
hívását automatikusan bekapcsolja ebbe a nyilvántartásba — így minden,
`_start_background`-on át indított háttérmunka (a jelenlegiek ÉS a
jövőbeliek is) megkapja az animációt, anélkül hogy a controllernek
külön be kellene jelentkeznie (ld. a `worker_thread.py` docstringjét).

**Küszöb + minimális láthatóság** (a jegy kifejezett kérése — ne
villogjon): ld. a `SHOW_DELAY_MS`/`MIN_VISIBLE_MS` konstansok mellett.

**Szál-biztonság**: a `begin()`/`end()` bármely szálról hívható (a
háttérszálak worker-függvénye is hívja, ld. `worker_thread.py`). Mindkettő
csak egy Qt-jelzést emitál (`_beginRequested`/`_endRequested`) — a TÉNYLEGES
számlálás/időzítés a jelzésre kötött belső slotban fut, ami a regisztrátum
SAJÁT szálán (a regisztrátum létrehozásának szálán, jellemzően a GUI-szálon)
hívódik: a Qt az `AutoConnection`-t szál-határon átmenő hívásnál
automatikusan `QueuedConnection`-né alakítja (ugyanez a minta, mint a
`LibraryMixin.syncProgress` workerből jövő jelzésénél). Emiatt nincs
szükség Lock-ra — csak a GUI-szál nyúl a `_active`/`_visible`/időzítő
állapothoz."""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

#: Küszöb (ms): rövid műveletnél NE villanjon fel a csík. Néhány száz
#: ezredmásodperces munka (egy gyors sync-tick, egy pár képes köteg) a
#: felhasználó számára nem érződik "lassúnak" — a csík felvillanása ilyenkor
#: inkább zajként hatna, mint tájékoztatásként. 300 ms a szokásos UI-
#: válaszidő-küszöb (Nielsen: ez alatt a felhasználó a rendszert
#: "azonnalinak" érzékeli, efölött viszont már várakozásnak) — ha a munka
#: ennél tovább tart, a csík megjelenése hasznos infó, nem zaj.
SHOW_DELAY_MS = 300

#: Minimális láthatóság (ms): ha a csík egyszer megjelent, maradjon
#: látható legalább ennyi ideig, MÉG AKKOR IS, ha a munka közben véget ér.
#: Enélkül egy éppen a küszöb fölött induló, de gyorsan befejeződő munka
#: egy pillanatra felvillanna, majd eltűnne (villogás) — ez ugyanolyan
#: zavaró lenne, mint a némaság. 500 ms elég rövid ahhoz, hogy egy valóban
#: gyors, utólag mégis lassúra sikeredő munka ne tűnjön "beragadtnak", de
#: elég hosszú ahhoz, hogy egyetlen villanás helyett folyamatos, észlelhető
#: benyomást keltsen.
MIN_VISIBLE_MS = 500


class AppBusyRegistry(QObject):
    """Számláló-alapú busy-nyilvántartás, küszöbbel és minimális
    láthatósággal — ld. a modul docstringjét."""

    #: A LÁTHATÓ (küszöb + minimális láthatóság szerint szűrt) állapot
    #: változott — ERRE kötnek a controllerek `isWorking`-szerű
    #: property-i, NEM a nyers számlálóra.
    visibleChanged = Signal()

    # belső, szál-határon átmenő "kérés" jelzések (ld. modul docstring) —
    # a begin()/end() csak ezeket emitálja, a tényleges állapotváltás a
    # rájuk kötött _on_begin/_on_end slotban, a regisztrátum szálán fut.
    _beginRequested = Signal()
    _endRequested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._active = 0
        self._visible = False
        # a min-láthatósági időzítő lejártakor még mindig el kell-e
        # rejteni (mert az end() a min-ablakban érkezett)
        self._pending_hide = False
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._on_show_timeout)
        self._min_visible_timer = QTimer(self)
        self._min_visible_timer.setSingleShot(True)
        self._min_visible_timer.timeout.connect(self._on_min_visible_timeout)
        self._beginRequested.connect(self._on_begin)
        self._endRequested.connect(self._on_end)

    @property
    def visible(self) -> bool:
        """Látszódjon-e a busy-sáv MOST — a küszöb/minimális láthatóság
        alkalmazása UTÁN. A controllerek `isWorking`-je ezt olvassa."""
        return self._visible

    @property
    def activeCount(self) -> int:  # noqa: N802 — a projekt QML-stílusú property-neveihez igazítva
        """A nyers, még be nem fejezett munkák száma — csak diagnosztikának/
        teszteknek, a UI ezt NEM olvassa (a küszöbölt `visible`-t igen)."""
        return self._active

    def begin(self) -> None:
        """Egy háttérmunka indul. BÁRMELY szálról hívható."""
        self._beginRequested.emit()

    def end(self) -> None:
        """Egy háttérmunka véget ért — HIBÁVAL leálló munkánál is hívandó
        (a hívó felelőssége `try`/`finally`-ben zárni, ld.
        `BackgroundWorkerMixin._start_background`), különben a számláló
        soha nem éri el a nullát, és a csík örökre pörögne."""
        self._endRequested.emit()

    # -- belső: MINDIG a regisztrátum szálán fut (ld. modul docstring) ------

    def _on_begin(self) -> None:
        self._active += 1
        if self._active == 1 and not self._visible and not self._show_timer.isActive():
            self._show_timer.start(SHOW_DELAY_MS)

    def _on_end(self) -> None:
        self._active = max(0, self._active - 1)
        if self._active > 0:
            return
        self._show_timer.stop()
        if not self._visible:
            return
        if self._min_visible_timer.isActive():
            # a csík még a minimális láthatósági ablakban van — a tényleges
            # elrejtés a timer lejártára vár, hogy ne villanjon
            self._pending_hide = True
        else:
            self._hide()

    def _on_show_timeout(self) -> None:
        if self._active <= 0:
            return  # a munka a küszöb ideje alatt befejeződött — nincs villanás
        self._visible = True
        self._pending_hide = False
        self.visibleChanged.emit()
        self._min_visible_timer.start(MIN_VISIBLE_MS)

    def _on_min_visible_timeout(self) -> None:
        if self._pending_hide or self._active <= 0:
            self._hide()
        self._pending_hide = False

    def _hide(self) -> None:
        self._visible = False
        self._pending_hide = False
        self.visibleChanged.emit()


_registry: AppBusyRegistry | None = None


def get_app_busy_registry() -> AppBusyRegistry:
    """A folyamat EGYETLEN, lusta-inicializált busy-nyilvántartása.

    Ez a laza csatolás lényege (#505): bármely controller ezt a függvényt
    hívja — nincs szükség rá, hogy ismerje az `AppController`-t vagy más
    controllert."""
    global _registry
    if _registry is None:
        _registry = AppBusyRegistry()
    return _registry


#: A LECSERÉLT regisztrátum-példányok (#519/#430). Lásd `reset_app_busy_registry`.
_retired_registries: list[AppBusyRegistry] = []


def reset_app_busy_registry() -> None:
    """Csak teszteknek: friss példányt kényszerít a következő
    `get_app_busy_registry()` hívásra, hogy egyik teszt maradék állapota
    (aktív számláló, futó időzítő) ne szivárogjon át a következőbe.

    #519/#430: a régi példányt NEM engedjük felszabadulni. A `begin()`/
    `end()` szálhatáron át, SORBA ÁLLÍTVA (queued) érkezik — ha egy korábbi
    teszt háttérszála a csere után jelez, a jelzés egy már felszabadított
    QObject-nek szólna: az a Windowson `0xC0000005` (access violation),
    Linuxon SIGSEGV. A példányt ezért életben tartjuk (a memória
    elhanyagolható: csak a tesztfuttatásban keletkezik belőle több), és
    leállítjuk az időzítőit, hogy ne dolgozzon tovább.
    """
    global _registry
    if _registry is not None:
        _registry.blockSignals(True)
        _registry._show_timer.stop()
        _registry._min_visible_timer.stop()
        _retired_registries.append(_registry)
    _registry = None
