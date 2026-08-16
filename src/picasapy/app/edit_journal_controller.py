"""Külső felülírás észlelése és helyreállítása — controller-szelet (#644).

A párhuzamosan futó eredeti Picasa a fotó rekordját a saját adatbázisából
írja ki egészben a `.picasa.ini`-be; amit a rekordja nem tartalmaz — a mi
`filters=` láncunkat —, azt elhagyja. Mivel a lánc máshol nem él, a
felhasználó munkája **figyelmeztetés nélkül megsemmisül**.

Ez a szelet a `picasapy.edit.edit_journal` tiszta rétegére ül:

- **felvétel** minden saját mentésnél (`recordSavedChain`) és minden
  kötegelt írásnál (`recordSavedChains`, #750 — a szerkesztőn kívül a
  csoportos effekt, a két effekt-beillesztés és a lemezre mentés is ide
  jelent, különben azokon az utakon se észlelés, se helyreállítás nincs),
- **észlelés** a nézet feltöltésekor — ott, ahol minden nézetmód átmegy,
- **jelzés** a felületnek (`editsOverwritten`), képenként egyszer,
- **helyreállítás** (`restoreOverwrittenEdit`): a naplózott lánc visszaírása.

A napló az adatbázis mellett él, NEM a fotó mappájában: egy külső program azt
is felülírhatja. Ugyanezért nem elég a `.picasa.ini.bak` sem — az a MI
írásunk előtti állapot, és a következő mentésünk felülírja.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.edit.edit_journal import (
    detect_lost_edits,
    naplo_kulcs,
    load_journal,
    record_saved_chains,
    save_journal,
)
from picasapy.index.queries import PhotoRecord, full_path
from picasapy.ini.io import update_document

#: A napló fájlneve az adatgyökérben (az index-SQLite mellett).
JOURNAL_FILENAME = "edit-journal.json"

#: A napló olvasás-módosítás-írás körét védő zár (#750).
#:
#: A csoportos effekt HÁTTÉRSZÁLON ír (`batch_effect_controller`), a
#: szerkesztő mentése és a beillesztések a GUI-szálon — zár nélkül két
#: párhuzamos kör közül a később kiíró felülcsapná a másik bejegyzését, és a
#: védelem NÉMÁN veszne el egy képre. Modul-szintű (nem példány-szintű),
#: mert a lusta példány-inicializálás maga is versenyhelyzet lenne; a
#: programban egyetlen napló van, tehát nincs mit finomabban szemcsézni.
#:
#: ÚJRABELÉPHETŐ (`RLock`), mert a `recordSavedChains` a zár alatt hívja a
#: `_load_journal`-t, ami maga is felveszi — sima `Lock` itt önzárat okozna.
_JOURNAL_LOCK = threading.RLock()


class EditJournalMixin:
    """A saját szerkesztések védelme külső felülírás ellen (#644)."""

    #: `[{path, name, chain}]` — a felület ebből mutat figyelmeztetést. Csak
    #: az ÚJ (még nem jelzett) veszteségek kerülnek bele.
    editsOverwritten = Signal(list)

    def _journal_file(self) -> Path:
        return Path(self._db_path).parent / JOURNAL_FILENAME

    def _journal_stamp(self):
        """A naplófájl azonosító pecsétje (`mtime_ns`, méret) — hiánynál None."""
        try:
            adat = self._journal_file().stat()
        except OSError:
            return None
        return (adat.st_mtime_ns, adat.st_size)

    def _load_journal(self):
        """A napló betöltése, MEMÓRIÁBAN gyorsítótárazva (#750).

        Az észlelés (`_check_external_overwrites`) MINDEN nézetfrissítésnél
        lefut — mappaváltásnál, minden fotóművelet után. A #644-es körben ez
        ártalmatlan volt, mert a naplót csak a szerkesztő egyenkénti mentései
        táplálták. A #750-nel viszont a kötegelt írók is jelentenek, így egy
        nagy gyűjteményen a napló tízezres nagyságrendűre nő, és minden
        beolvasás a GUI-szálon fizetne: mérve (RPi5, 2026-08-16) 10 000
        bejegyzésnél 50 ms, 50 000-nél 490 ms — utóbbi már látható akadás
        minden egyes mappaváltásnál.

        A pecsét (`mtime_ns` + méret) változásáig a memóriabeli példányt
        adjuk vissza. A naplót MI írjuk (atomikus cserével, ami új pecsétet
        ad), és a hívók sosem mutálják a kapott szótárat — a tiszta réteg
        minden művelete új szótárat ad —, ezért a közös példány kiadása
        biztonságos.
        """
        pecset = self._journal_stamp()
        with _JOURNAL_LOCK:
            gyorsitotar = getattr(self, "_journal_cache", None)
            if gyorsitotar is not None and gyorsitotar[0] == pecset:
                return gyorsitotar[1]
            journal = load_journal(self._journal_file())
            self._journal_cache = (pecset, journal)
            return journal

    def recordSavedChain(self, image_path: str, chain: str) -> None:  # noqa: N802
        """A most kiírt lánc naplózása — a mentési út hívja.

        Üres láncnál a bejegyzés törlődik: ha a felhasználó MAGA vonta vissza
        a szerkesztéseit, nincs mit védeni."""
        self.recordSavedChains(((str(image_path), chain or ""),))

    def recordSavedChains(  # noqa: N802 — QML-stílusú név, mint a párja
        self, items: "Iterable[tuple[str, str]]"
    ) -> None:
        """Egy KÖTEG kiírt lánc naplózása — egyetlen olvasás + írás (#750).

        A csoportos effekt, a „Paste All Effects" és „Az összes effektus
        beillesztése" mappánként több tucat/több száz képet ír. Ezek a hívók
        a mappájuk kész bejegyzéseit adják át egyben, hogy a napló ne váljon
        a köteg szűk keresztmetszetévé: a költség a MAPPÁK számával nő, nem a
        képekével.

        Mérve (RPi5, 2026-08-16, 1000 képes mappa): kötegelve 9,8 ms, míg
        képenkénti olvasás+írással 626 ms — és ez utóbbi NÉGYZETESEN romlik,
        mert a napló minden lépésben újra beolvasódik (5000 képnél már
        ~3,4 s a 0,05 s helyett).

        Args:
            items: `(kép útvonala, kiírt lánc)` párok. Üres lánc (törölt
                `filters=`) a bejegyzést törli.
        """
        parok = tuple(items)
        if not parok:
            return
        # A zár a teljes olvasás-módosítás-írás kört fedi: ez a kör az, ami
        # két íróval versenyezve bejegyzést veszítene (ld. `_JOURNAL_LOCK`).
        with _JOURNAL_LOCK:
            journal = record_saved_chains(
                self._load_journal(),
                parok,
                saved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            save_journal(journal, self._journal_file())
            # A frissen kiírt állapot AZONNAL a gyorsítótárba: így a soron
            # következő nézetfrissítés (a kötegelt írók mindegyike hív
            # `_refresh_view()`-t) nem olvassa vissza a most írt fájlt.
            self._journal_cache = (self._journal_stamp(), journal)

    def _check_external_overwrites(
        self, records: "Sequence[PhotoRecord]"
    ) -> None:
        """A nézetbe került képek láncainak összevetése a naplóval.

        Képenként **egyszer** jelzünk (ugyanarra a veszteségre nem szólunk
        újra minden nézetfrissítésnél) — a jelzés a helyreállításig vagy a
        program újraindításáig érvényes.
        """
        journal = self._load_journal()
        if not journal:
            return
        # #699: a rekord `index.queries.PhotoRecord` — NINCS `path` mezője.
        # A kulcsot a KÖZÖS `full_path()` képzi, ugyanazzal a szabállyal,
        # amivel a napló írója (`recordSavedChain`) dolgozik. Harmadik
        # útvonal-szabály írása némán kiütné a védelmet.
        current = {naplo_kulcs(full_path(r)): (r.filters or "") for r in records}
        lost = detect_lost_edits(journal, current)
        if not lost:
            return
        reported = getattr(self, "_reported_overwrites", None)
        if reported is None:
            reported = set()
            self._reported_overwrites = reported
        friss = [
            entry for entry in lost if (entry.path, entry.chain) not in reported
        ]
        if not friss:
            return
        for entry in friss:
            reported.add((entry.path, entry.chain))
        self.editsOverwritten.emit(
            [
                {
                    "path": entry.path,
                    "name": Path(entry.path).name,
                    "chain": entry.chain,
                }
                for entry in friss
            ]
        )

    @Slot(str, result=bool)
    def restoreOverwrittenEdit(self, image_path: str) -> bool:
        """A naplózott lánc visszaírása a `.picasa.ini`-be.

        Igaz, ha sikerült. A művelet a `filters=` kulcsot állítja vissza; a
        képfájlt nem érinti (a lánc nem beégetett szerkesztés).
        """
        # #699: a helyreállítás is a KÖZÖS kulcsszabállyal keres
        entry = self._load_journal().get(naplo_kulcs(image_path))
        if entry is None or not entry.chain.strip():
            return False
        target = Path(image_path)
        ini_path = target.parent / ".picasa.ini"

        def mutate(document):
            # #643: a naplóból ÁTVITT lánc (korábban már kiírtuk) —
            # a visszatöltés nem szerzőség, ezért `carried`.
            return document.with_value(
                target.name, "filters", entry.chain, carried=True
            )

        try:
            update_document(ini_path, mutate, backup=True)
        except OSError:
            return False
        # a helyreállítás után ugyanarra a veszteségre már nem szólunk
        reported = getattr(self, "_reported_overwrites", None)
        if reported is not None:
            reported.discard((entry.path, entry.chain))
        self._refresh_view()
        return True


__all__ = ["JOURNAL_FILENAME", "EditJournalMixin"]
