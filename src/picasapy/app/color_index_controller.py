"""A színkeresés gyorsítótárának HÁTTÉR-FELTÖLTÉSE (#1500) — az
`AppController`-be kevert szelet (`ColorIndexMixin`).

## Miért kellett

A `color:`/`szín:` keresés (#383) magja és osztályozója kész volt (a
#1480 a bináriskból mért hue-hisztogramra cserélte a besorolást), a
`search_photos()` helyesen kérdezte a `photo_colors` táblát — de a táblát
feltöltő `index.backfill_colors()`-nak **nem volt éles hívója**: csak a
tesztek hívták. A keresősávba írt `szín:kék` ezért MINDIG nulla találatot
adott, néma, üres találati listával. Ez a modul a hiányzó hívó.

## Mikor fut

**Lustán, a színkeresés pillanatában** — nem indításkor. A #1480 mérése
szerint egy kép besorolása **81 ms**; egy 50 000 képes gyűjteményen ez
több mint egy óra processzoridő. Ezt SEMMIKÉPP nem szabad ráterhelni arra
a felhasználóra, aki soha nem használ színkeresést. Aki viszont beírja,
hogy `szín:kék`, az épp most kérte el ezt az adatot — ott a munka
indokolt.

## Hogyan fut

- **Háttérszálon**, a `BackgroundWorkerMixin._start_background`-on át
  (#430/#438/#999): így a lebontás (teszt-fixture, kilépés) bevárja, és a
  #505 alsó kék sávja is magától megjelenik.
- **Kötegelve**: a `backfill_colors` `_KOTEG_MERET` képenként commitol, a
  megszakított futás munkája nem vész el.
- **Megszakíthatóan**: `cancelColorIndex()` — kép-kötegek határán áll meg.
- **Haladásjelzéssel**: a `colorIndexProgress(kész, összes)` jelzésre a
  tájékoztató sáv számai élőben frissülnek, a futás egészét pedig a #505
  alsó kék sávja mutatja (ez a projekt bevett válasza a hosszú
  háttérmunkára). KÜLÖN százalék-property SZÁNDÉKOSAN nincs: a
  `FaceScanController.scanPercent`-nek van hova kötődnie (a „Névtelenek"
  albumsor), ennek nem lenne — a bekötetlen property épp az a néma,
  hatástalan felület, amit a #1473 óta kerülünk.
- **A végén magától frissül** a még mindig futó színkeresés
  (`_refresh_after_color_index`) — a felhasználótól nem várható el, hogy
  percekkel később újra begépelje ugyanazt.

## A némaság megszüntetése

A „0 találat" és a „még nem számoltuk ki" **két különböző dolog**, és a
jegy előtt összemosódott. Hiányos gyorsítótárral futó színkeresésnél a
`colorIndexIncomplete(kész, összes)` jelzés megy ki; a `Main.qml` ebből a
borostyán tájékoztató sávot rajzolja (nem hibát — nem hiba).

A szöveget PYTHON adja (`colorIndexNoticeText`), nem a QML (a #1473
mintája): a mondat számokat és többes számot kezel, a felület csak
megjeleníti — ugyanazt a szövegforrást használja a felbukkanó sáv és a
futás közbeni frissítése is. A `self.tr()`
FUTÁSIDŐBEN az `AppController` kontextusát használja (a példány osztálya,
nem a lexikai `ColorIndexMixin`) — ezért a `.ts`-ben az `AppController`
kontextus alatt van a fordítása, és a
`test_i18n_completeness._KNOWN_CONTEXT_FORWARDING_EXCEPTIONS` táblájában
szerepel a továbbítás.
"""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import Signal, Slot

from picasapy.index import backfill_colors, color_index_progress, open_index
from picasapy.index.search_color import parse_color_terms

from .worker_thread import BackgroundWorkerMixin

logger = logging.getLogger(__name__)

#: Ennyi kép egy körben. A `backfill_colors` körönként commitol, tehát ez
#: egyben a megszakítás szemcsézettsége és a haladásjelzés lépésköze is.
#: 25 kép × 81 ms ≈ 2 s — elég sűrű ahhoz, hogy a százalék mozogjon és a
#: megszakítás azonnalinak érződjön, elég ritka ahhoz, hogy a commitok
#: költsége ne uralja a futást.
_KOTEG_MERET = 25

#: A háttérszál neve — a `running_background_workers()` hibaüzenetében ez
#: azonosítja, ha valami nem áll le.
_SZAL_NEV = "picasapy-szinindex"


class ColorIndexMixin(BackgroundWorkerMixin):
    """A `photo_colors` gyorsítótár feltöltése háttérben (#1500)."""

    #: (kész, összes) — a futó feltöltés haladása
    colorIndexProgress = Signal(int, int)
    #: (kész, összes) — a futás vége (befejezés, megszakítás vagy hiba után)
    colorIndexFinished = Signal(int, int)
    #: (kész, összes) — a színkeresés hiányos gyorsítótárral futott
    colorIndexIncomplete = Signal(int, int)

    # ---------------------------------------------------------------- állapot
    # A szelet LUSTÁN inicializálja magát (#150 mintája): a `controller.py`
    # — forró fájl — `__init__`-jéhez nem kell hozzányúlni.

    @property
    def _color_index_stop_event(self) -> threading.Event | None:
        return getattr(self, "_color_index_stop", None)

    # ------------------------------------------------------------- lekérdezés

    @Slot(result=bool)
    def colorIndexRunning(self) -> bool:  # noqa: N802 — QML-slot-stílus
        """Fut-e éppen a színgyorsítótár feltöltése?

        A FUTÁSJELZŐT kérdezi, nem a szál életjelét: a kapu (két egyidejű
        index-író elkerülése) ezen a jelzőn áll, tehát az őrnek is ezt
        kell látnia."""
        return bool(getattr(self, "_color_index_running", False))

    # ------------------------------------------------------------- vezérlés

    @Slot()
    def startColorIndex(self) -> None:  # noqa: N802 — QML-slot-stílus
        """A feltöltés elindítása háttérszálon; ha már fut, nem csinál semmit."""
        if self.colorIndexRunning():
            return
        self._ensure_color_index_wired()
        stop_event = threading.Event()
        self._color_index_stop = stop_event
        # A jelző a szálindítás ELŐTT áll be: minden hívó a GUI-szálon van
        # (QML-slot, illetve a keresés), tehát a beállítás és az ellenőrzés
        # között nincs másik hívó.
        self._color_index_running = True
        try:
            self._start_background(
                self._run_color_index, args=(stop_event,), name=_SZAL_NEV
            )
        except BaseException:
            # ⚠️ #550/#1435/#1440 mintája: a `thread.start()` elbukhat
            # (`RuntimeError: can't start new thread`), és akkor a worker —
            # vele a `finally` ága — SOSEM fut le. Beragadt jelzővel a
            # színkeresés a munkamenet végéig NÉMÁN soha többé nem töltené
            # fel a gyorsítótárat: a felhasználó minden további
            # `szín:kék`-re üres listát kapna, és semmi nem árulná el, hogy
            # egyetlen tranziens hiba miatt.
            self._color_index_running = False
            raise

    def _ensure_color_index_wired(self) -> None:
        """A záró jelzés bekötése — LUSTÁN, egyszer (a szelet nem nyúl a
        `controller.py` `__init__`-jéhez, ld. modul-docstring)."""
        if getattr(self, "_color_index_wired", False):
            return
        self._color_index_wired = True
        self.colorIndexFinished.connect(self._refresh_after_color_index)

    def _refresh_after_color_index(self, kesz: int, osszes: int) -> None:
        """A kész feltöltés után a FUTÓ színkeresés magától frissül.

        A tájékoztató sáv önmagában kevés lenne: a felhasználó beírta,
        hogy `szín:kék`, üres listát kapott, és nem várható el tőle, hogy
        percekkel később újra begépelje ugyanazt. A jelzés a munkásszálról
        QUEUED módon érkezik, tehát ez a metódus a GUI-szálon fut.

        CSAK akkor frissít, ha a felhasználó MÉG MINDIG ugyanazon a
        színkeresésen áll — ha közben továbblépett, a kész feltöltés nem
        ránthatja vissza az elhagyott találatokat."""
        mode, param = getattr(self, "_view_mode", ("", ""))
        if mode != "search" or not isinstance(param, str):
            return
        _, szinek = parse_color_terms(param)
        if not szinek:
            return
        # Az újrafuttatás NEM indít újabb feltöltést: a `_note_color_search`
        # kész gyorsítótárnál azonnal visszatér, tehát nincs körkörösség.
        self.search(param)

    @Slot()
    def cancelColorIndex(self) -> None:  # noqa: N802 — QML-slot-stílus
        """A folyamatban lévő feltöltés megszakítása köteg-határon.

        A már kiszámolt színek az indexben maradnak (a `backfill_colors`
        kötegenként commitol), tehát a következő indítás onnan folytatja."""
        stop_event = self._color_index_stop_event
        if stop_event is not None:
            stop_event.set()

    # -------------------------------------------------- a keresés belépője

    def _note_color_search(self, conn, query: str) -> None:
        """A `SearchMixin.search()` hívja MINDEN kereséskor.

        Színtoken nélküli keresésnél azonnal visszatér — a szöveges
        keresés nem indíthat 81 ms/képes háttérmunkát. Színtoken esetén
        megnézi, teljes-e a gyorsítótár; ha nem, JELEZ (hogy az üres
        találati lista ne legyen néma) és elindítja a feltöltést."""
        _, szinek = parse_color_terms(query)
        if not szinek:
            return
        kesz, osszes = color_index_progress(conn)
        if osszes == 0 or kesz >= osszes:
            return
        self.colorIndexIncomplete.emit(kesz, osszes)
        try:
            self.startColorIndex()
        except Exception:
            # A szálindítás bukása NEM teheti tönkre magát a keresést: a
            # szöveges találatoknak akkor is meg kell jönniük. A jelzőt a
            # `startColorIndex` már visszaállította, tehát a következő
            # keresés újra próbálkozhat.
            logger.warning(
                "#1500: a színgyorsítótár feltöltése nem indult el", exc_info=True
            )

    @Slot(int, int, result=str)
    def colorIndexNoticeText(self, kesz: int, osszes: int) -> str:  # noqa: N802
        """A borostyán tájékoztató sáv mondata — cselekvésre váltható.

        Nem elég közölni, hogy „hiányos": a felhasználónak azt kell
        megtudnia, MIÉRT üres a lista, és MIT tegyen (várjon, majd keressen
        újra)."""
        return self.tr(
            "Color search is still being prepared: {0} of {1} photos have been "
            "analyzed so far. Photos that have not been analyzed yet cannot "
            "show up in the results, but the list fills in on its own as soon "
            "as the preparation finishes."
        ).format(kesz, osszes)

    # ------------------------------------------------------------ háttérszál

    def _run_color_index(self, stop_event: threading.Event) -> None:
        """A háttérszál törzse: kötegenként hívja a feltöltést, amíg van
        teendő, a felhasználó meg nem szakítja, vagy hiba nem történik."""
        kesz = osszes = 0
        try:
            with open_index(self._db_path) as conn:
                kesz, osszes = color_index_progress(conn)
                self._emit_color_progress(kesz, osszes)
                while not stop_event.is_set():
                    if backfill_colors(conn, limit=_KOTEG_MERET) == 0:
                        break
                    kesz, osszes = color_index_progress(conn)
                    self._emit_color_progress(kesz, osszes)
        except Exception:
            # A daemon-szálról kiszökő kivétel csak tracebacket köpne a
            # stderr-re (#1435 mintája) — naplózzuk, a `finally` rendet rak.
            logger.exception("#1500: a színgyorsítótár feltöltése elhasalt")
        finally:
            self._color_index_running = False
            try:
                self.colorIndexFinished.emit(kesz, osszes)
            except RuntimeError:
                # leállás közben a C++ oldal már eltűnhetett
                logger.debug("#1500: a záró jelzés elmaradt", exc_info=True)

    def _emit_color_progress(self, kesz: int, osszes: int) -> None:
        """Haladás a felületnek — a látható tájékoztató sáv számai ebből
        frissülnek élőben.

        A `FaceScanController._emit_progress` (#449) mintája: a jelzés a
        munkásszálról megy, a Qt `AutoConnection`-je a GUI-szálon
        kézbesíti. A `RuntimeError` elnyelése ugyanaz a védelem, mint a
        záró jelzésnél: leállás közben a C++ oldal már eltűnhetett."""
        try:
            self.colorIndexProgress.emit(kesz, osszes)
        except RuntimeError:
            logger.debug("#1500: a haladásjelzés elmaradt", exc_info=True)
