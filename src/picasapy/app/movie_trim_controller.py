"""A videó vágáspontjainak MENTÉSE — az AppController szelete (#1838).

Az eredeti Picasa videó-vezérlősávján `setin` / `setout` / `reset_trim` áll
(kezelő: `0x005952d0`), és a vágáspontok a `.picasa.ini` **`filters=`**
láncába kerülnek `moviestart` / `movieend` néven. A formátum mérve van
(`ini/movie_trim.py`): 64 bites kisbetűs hex, 100 ns-os DirectShow
`REFERENCE_TIME`.

Ez a modul a lánc **visszaírását** végzi. Az olvasás
(`models.movieTrimAt`) és a lejátszás-szorítás (`VideoPlayerView.qml`) a
jegy korábbi köreiben elkészült.

## Három szerződés, amit ez a szelet őriz

1. **A lánc többi tokenje érintetlen.** Egy Picasából örökölt `.picasa.ini`-t
   nem mi írtunk; amit nem értünk, azt megőrizzük. A csere a token HELYÉN
   történik (`ini.movie_trim.filters_with_trim`), a sorrend nem rendeződik át.
2. **A `-1` nem nulla.** A hiányzó token azt jelenti, hogy azon az oldalon
   nincs vágás — a nulla pontra állított kezdés MÁS. A `movieTrimAt` is ezt a
   megállapodást használja, a kettő párban áll.
3. **Az írás bukása nem néma** (#2506). A kivétel a gazda hibacsatornáján
   megy ki, és a modell-sort CSAK sikeres írás után frissítjük — különben a
   felület mentettnek mutatná, ami a lemezre nem jutott el.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.ini import update_document
from picasapy.ini.movie_trim import (
    MovieTrim,
    filters_with_trim,
    ms_to_ticks,
    ticks_to_ms,
    trim_from_filters,
)
from picasapy.scanner import PICASA_INI_NAME

#: Amit írási hibaként kezelünk. A `PermissionError`/`IsADirectoryError` az
#: `OSError` alatt van, tehát nem kell külön felvenni.
_WRITE_ERRORS = (OSError,)


def _tick(ms: int, orzott: int | None) -> int | None:
    """Ezredmásodperc → 100 ns-os tick; a negatív érték „nincs vágás".

    ⚠️ **Ha a felhasználó nem mozdította azt az oldalt, a MEGŐRZÖTT tick megy
    vissza, bitre.** A tárolt egység 100 ns, a felület egysége ezredmásodperc
    — a kettő között a visszaváltás VESZTESÉGES: a Picasából örökölt
    `moviestart=80252d` 8 398 125 tick = 839,8125 ms, amiből 839 ms-on át
    visszaszámolva 8 390 000 lenne. Az ms-egyezést ezért megőrzésnek
    olvassuk: amihez a felület nem nyúlt, azt nem írjuk át.
    """
    if ms is None or ms < 0:
        return None
    ms = int(ms)
    if orzott is not None and ticks_to_ms(orzott) == ms:
        return orzott
    return ms_to_ticks(ms)


class MovieTrimMixin:
    """`setMovieTrim` / `resetMovieTrim` — a `setin`/`setout`/`reset_trim` párja.

    ⚠️ SZÁNDÉKOSAN nincs „elmentve" jelzés. A felület a modellből olvassa a
    vágást, és az `update_photo` `revision`-lépése már újraértékelteti a
    kötéseket — egy külön jelzés bekötetlen maradna, azt pedig a
    `scripts/check_dead_signals.py` (helyesen) visszautasítja.
    """

    @Slot(int, int, int)
    def setMovieTrim(self, row: int, start_ms: int, end_ms: int) -> None:
        """A sor vágáspontjainak mentése (`-1` = nincs vágás azon az oldalon).

        Amelyik oldal ms-ban EGYEZIK a tárolttal, ott a megőrzött 100 ns-os
        érték megy vissza bitre — ld. a `_tick` figyelmeztetését.
        """
        felvetel = self._vago_sor(row)
        if felvetel is None:
            return
        orzott = trim_from_filters(felvetel.filters or "")
        self._irjd_a_vagast(
            row,
            MovieTrim(
                start=_tick(start_ms, orzott.start),
                end=_tick(end_ms, orzott.end),
            ),
        )

    @Slot(int)
    def resetMovieTrim(self, row: int) -> None:
        """A vágás visszaállítása — mindkét token kikerül a láncból.

        A lánc TÖBBI tokenje megmarad: a `reset_trim` az eredetiben sem
        törli a videó egyéb szerkesztését.
        """
        self._irjd_a_vagast(row, MovieTrim(start=None, end=None))

    # -- belső ------------------------------------------------------------

    def _irjd_a_vagast(self, row: int, trim: MovieTrim) -> None:
        felvetel = self._vago_sor(row)
        if felvetel is None:
            return
        ini_path = Path(felvetel.folder_path) / PICASA_INI_NAME
        uj_lanc = filters_with_trim(felvetel.filters or "", trim)

        # #137: ütközésbiztos írás — a párhuzamosan futó eredeti Picasa
        # módosítása nem veszhet el (a mutate tiszta, újrajátszható).
        def mutate(document):
            if uj_lanc:
                return document.with_value(felvetel.name, "filters", uj_lanc)
            return document.with_removed(felvetel.name, "filters")

        try:
            update_document(ini_path, mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.jelentsdAzIrasiHibat(error)
            return

        # A modell-sort CSAK a sikeres írás után frissítjük (#2497 tanulsága).
        self.photos.update_photo(felvetel.id, replace(felvetel, filters=uj_lanc or None))

    def _vago_sor(self, row: int):
        """A sor felvétele, ha az egyáltalán vágható — különben `None`.

        A vágás videó-fogalom: fotóra hívva NEM nyúlunk az inihez. Így egy
        elszállt QML-kötés sem tud egy fényképhez `moviestart`-ot írni.
        """
        modell = getattr(self, "photos", None)
        if modell is None:
            return None
        felvetelek = getattr(modell, "_photos", ())
        if not 0 <= row < len(felvetelek):
            return None
        felvetel = felvetelek[row]
        if felvetel.kind != "video" or not felvetel.folder_path:
            return None
        return felvetel
