"""Fő szál-figyelő: hol áll a felület, amikor nem válaszol (#6349).

## Miért kell

A tulajdonos gépén a Main.qml betöltése 25–46 s (a CI-n 1,3–2 s), és
futás közben a felület homokórázik: a kilépési kérdés gombja sem
kattintható. A szakaszos idővonal (#1601) csak annyit mond, hogy a
`engine.load()` hívás lassú, azt nem, hogy MIRE vár — a CI-futón pedig
nem reprodukálható, mert ott nincs a gép saját könyvtára, hálózata és
hardvere.

## Hogyan

Egy háttérszál tizedmásodpercenként megnézi a fő szál Python-vermét
(`sys._current_frames`), de CSAK akkor, ha a fő szál nem válaszol:

- egy megnevezett szakaszban (`szakasz()`, pl. a Main.qml betöltése),
  ahol még nincs eseményhurok, tehát szívverés sem lehet;
- az eseményhurok indulása után akkor, ha a fő szál 200 ms-os
  szívverése egy másodpercnél régebbi.

A fagyás végén, ha az legalább `kuszob_s` hosszú volt, egy WARNING sor
kerül a hibanaplóba: meddig tartott, és a minták hány százaléka melyik
kódsorra esett. A sor csak fájlnevet, függvénynevet és sorszámot tartalmaz
— útvonalat, fotónevet nem (a napló személyes adatot nem tartalmazhat).

Ha a fő szál a Qt C++-kódjában vár (pl. egy bővítmény betöltésén), a
legbelső Python-keret az a hívás, ami a C++-ba vezetett (`engine.load`):
ez önmagában is lelet — azt mondja, hogy a várakozás nem a mi Python-
kódunkban van.

⛔ **Python-oldali Qt-üzenetkezelőt (`qInstallMessageHandler`) itt TILOS
telepíteni.** Kipróbáltuk (a Qt import-/bővítménynaplójának csendjeit akartuk
mérni a betöltés alatt): a QML-fordítás háttérszálon naplóz, a kezelőnek a
GIL kell, a fő szál pedig közben a háttérszálra vár — HOLTPONT. Mérve a
`scripts/qml_betoltes_bontas.py` gyermekfolyamatán: a kezelővel 180 s után
időtúllépés, nélküle 2,7 s. A minta-vevő szál ezzel szemben nem nyúl a Qt-hez.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

#: ennyi ideig tartó fagyás kerül a naplóba
KUSZOB_S = 2.0
#: mintavételi időköz
MINTAVETEL_S = 0.1
#: a szívverés időköze (a fő szálon), és az a kor, amitől „nem válaszol”
SZIVVERES_MS = 200
ELAVULT_S = 1.0
#: ennyi leggyakoribb kódsor kerül a naplósorba
LEGGYAKORIBB = 6


def _keret_kulcs(keret) -> str:
    """`fájlnév:függvény:sor` — útvonal nélkül."""
    kod = keret.f_code
    return f"{Path(kod.co_filename).name}:{kod.co_name}:{keret.f_lineno}"


def verem_kulcs(keret) -> str:
    """A legbelső keret, és ha az nem a mi kódunk, a legbelső saját keret.

    Így a napló egyszerre mutatja, MIBEN vár a szál (pl. `os.stat`), és
    hogy NÁLUNK melyik sor hívta (pl. `exportcelok.py:...`)."""
    legbelso = _keret_kulcs(keret)
    sajat = None
    while keret is not None:
        if "picasapy" in Path(keret.f_code.co_filename).parts:
            sajat = _keret_kulcs(keret)
            break
        keret = keret.f_back
    if sajat is None or sajat == legbelso:
        return legbelso
    return f"{legbelso} ← {sajat}"


class FoszalFigyelo:
    """Lásd a modul leírását. Egy példány folyamatonként elég."""

    def __init__(
        self,
        *,
        kuszob_s: float = KUSZOB_S,
        mintavetel_s: float = MINTAVETEL_S,
        log: logging.Logger | None = None,
    ) -> None:
        self._kuszob_s = kuszob_s
        self._mintavetel_s = mintavetel_s
        self._log = log or logger
        self._fo_szal = threading.main_thread().ident
        self._zar = threading.Lock()
        self._szakasz: str | None = None
        self._szivveres: float | None = None
        self._fagyas_kezdete: float | None = None
        self._mintak: Counter[str] = Counter()
        self._leall = threading.Event()
        self._szal: threading.Thread | None = None
        self._idozito = None

    # -- a fő szálról hívandó --------------------------------------------

    @contextmanager
    def szakasz(self, nev: str) -> Iterator[None]:
        """Egy blokkoló szakasz (eseményhurok nélkül) mintavételezése."""
        self._inditsd_a_szalat()
        with self._zar:
            self._szakasz = nev
            self._fagyas_kezdete = time.monotonic()
            self._mintak = Counter()
        try:
            yield
        finally:
            with self._zar:
                self._lezar(nev)
                self._szakasz = None

    def szivveres_inditasa(self, parent) -> None:
        """A fő szál szívverése (QTimer) — az eseményhurok indulása előtt hívandó."""
        from PySide6.QtCore import QTimer

        self._inditsd_a_szalat()
        self._szivveres = time.monotonic()
        self._idozito = QTimer(parent)
        self._idozito.setInterval(SZIVVERES_MS)
        self._idozito.timeout.connect(self._dobbanas)
        self._idozito.start()

    def leallitas(self) -> None:
        self._leall.set()
        if self._idozito is not None:
            try:
                self._idozito.stop()
            except RuntimeError:
                pass

    def _dobbanas(self) -> None:
        most = time.monotonic()
        with self._zar:
            self._szivveres = most
            if self._fagyas_kezdete is not None and self._szakasz is None:
                self._lezar("a felület nem válaszolt")

    # -- belső -------------------------------------------------------------

    def _inditsd_a_szalat(self) -> None:
        if self._szal is not None:
            return
        self._szal = threading.Thread(
            target=self._mintavevo, name="picasapy-foszal-figyelo", daemon=True
        )
        self._szal.start()

    def _mintavevo(self) -> None:
        while not self._leall.wait(self._mintavetel_s):
            try:
                self._egy_minta()
            except Exception:  # noqa: BLE001 — diagnosztika: soha nem dönthet
                return

    def _egy_minta(self) -> None:
        most = time.monotonic()
        with self._zar:
            fagy = self._szakasz is not None or (
                self._szivveres is not None and most - self._szivveres > ELAVULT_S
            )
            if not fagy:
                return
            if self._fagyas_kezdete is None:
                # a szívverés utolsó ütése óta áll — onnan számítjuk
                self._fagyas_kezdete = self._szivveres or most
                self._mintak = Counter()
        keret = sys._current_frames().get(self._fo_szal)
        if keret is None:
            return
        kulcs = verem_kulcs(keret)
        with self._zar:
            if self._fagyas_kezdete is not None:
                self._mintak[kulcs] += 1

    def _lezar(self, nev: str) -> bool:
        """A fagyás lezárása és naplózása — a zár alatt hívandó. Igaz, ha naplózott."""
        kezdet, mintak = self._fagyas_kezdete, self._mintak
        self._fagyas_kezdete, self._mintak = None, Counter()
        if kezdet is None:
            return False
        hossz = time.monotonic() - kezdet
        if hossz < self._kuszob_s:
            return False
        osszes = sum(mintak.values())
        if osszes:
            reszek = "; ".join(
                f"{darab * 100 // osszes}% {kulcs}"
                for kulcs, darab in mintak.most_common(LEGGYAKORIBB)
            )
        else:
            reszek = "nincs minta"
        self._log.warning(
            "#6349: a fő szál %.1f s-ig foglalt volt (%s); minták: %d — %s",
            hossz,
            nev,
            osszes,
            reszek,
        )
        return True


_figyelo: FoszalFigyelo | None = None


def foszal_figyelo() -> FoszalFigyelo:
    """A folyamat egyetlen figyelője (lusta létrehozás)."""
    global _figyelo
    if _figyelo is None:
        _figyelo = FoszalFigyelo()
    return _figyelo
