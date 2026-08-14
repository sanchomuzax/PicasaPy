"""Külső felülírás észlelése és helyreállítása — controller-szelet (#644).

A párhuzamosan futó eredeti Picasa a fotó rekordját a saját adatbázisából
írja ki egészben a `.picasa.ini`-be; amit a rekordja nem tartalmaz — a mi
`filters=` láncunkat —, azt elhagyja. Mivel a lánc máshol nem él, a
felhasználó munkája **figyelmeztetés nélkül megsemmisül**.

Ez a szelet a `picasapy.edit.edit_journal` tiszta rétegére ül:

- **felvétel** minden saját mentésnél (`recordSavedChain`),
- **észlelés** a nézet feltöltésekor — ott, ahol minden nézetmód átmegy,
- **jelzés** a felületnek (`editsOverwritten`), képenként egyszer,
- **helyreállítás** (`restoreOverwrittenEdit`): a naplózott lánc visszaírása.

A napló az adatbázis mellett él, NEM a fotó mappájában: egy külső program azt
is felülírhatja. Ugyanezért nem elég a `.picasa.ini.bak` sem — az a MI
írásunk előtti állapot, és a következő mentésünk felülírja.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.edit.edit_journal import (
    detect_lost_edits,
    load_journal,
    record_saved_chain,
    save_journal,
)
from picasapy.ini.io import update_document

#: A napló fájlneve az adatgyökérben (az index-SQLite mellett).
JOURNAL_FILENAME = "edit-journal.json"


class EditJournalMixin:
    """A saját szerkesztések védelme külső felülírás ellen (#644)."""

    #: `[{path, name, chain}]` — a felület ebből mutat figyelmeztetést. Csak
    #: az ÚJ (még nem jelzett) veszteségek kerülnek bele.
    editsOverwritten = Signal(list)

    def _journal_file(self) -> Path:
        return Path(self._db_path).parent / JOURNAL_FILENAME

    def _load_journal(self):
        return load_journal(self._journal_file())

    def recordSavedChain(self, image_path: str, chain: str) -> None:  # noqa: N802
        """A most kiírt lánc naplózása — a mentési út hívja.

        Üres láncnál a bejegyzés törlődik: ha a felhasználó MAGA vonta vissza
        a szerkesztéseit, nincs mit védeni."""
        journal = record_saved_chain(
            self._load_journal(),
            str(image_path),
            chain or "",
            saved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        save_journal(journal, self._journal_file())

    def _check_external_overwrites(self, records) -> None:
        """A nézetbe került képek láncainak összevetése a naplóval.

        Képenként **egyszer** jelzünk (ugyanarra a veszteségre nem szólunk
        újra minden nézetfrissítésnél) — a jelzés a helyreállításig vagy a
        program újraindításáig érvényes.
        """
        journal = self._load_journal()
        if not journal:
            return
        current = {str(r.path): (r.filters or "") for r in records}
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
        entry = self._load_journal().get(str(image_path))
        if entry is None or not entry.chain.strip():
            return False
        target = Path(image_path)
        ini_path = target.parent / ".picasa.ini"

        def mutate(document):
            return document.with_value(target.name, "filters", entry.chain)

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
