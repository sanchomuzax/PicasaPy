"""A mentés-üzemmód képrács-szűrője (#3751) — az `AppController` szelete.

Az eredeti „Képek biztonsági mentése" módjában a `backuptext2` szerint
„a Picasa most azokat a FÁJLOKAT jeleníti meg, amelyekről korábban nem
készült biztonsági másolat" — a jobb oldali rács is, nem csak a bal hasáb
mappalistája (#3681). A szűrés FÁJL szerinti: egy részben elmentett mappából
csak a még el nem mentett képek maradnak.

A szűrő a `photos`/`feedGroups` páros ELŐÁLLÍTÁSAKOR hat (`_show`), a
rejtett képek és a bezárt gyűjtemények mintájára — így a sorindexek, a
csoportok `start`/`count`-ja, a billentyűs navigáció, a Ctrl+A és a néző
lapozása egyszerre a szűrt listára mutat. A szűrő a nézetmódtól független:
a háttér-szinkron utáni újratöltés is megtartja.

A lista forrása a `BackupController.mentetlenMappakLekerese` eredménye
(soronként az `utak`); a felületen a `BackupHost` kapcsolja.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index.queries import full_path


def _normalt(ut: str) -> str:
    return os.path.normpath(str(ut))


class MentesRacsSzuroMixin:
    """A rács szűkítése a kiválasztott készlet még el nem mentett fájljaira."""

    #: A szűrő bekapcsolt, új fájllistát kapott, vagy kikapcsolt. Az első
    #: kettőnél a `feedChanged` ELŐTT, kikapcsoláskor UTÁNA megy ki — a rács
    #: ebből tudja, mikor tegye el a mentés előtti görgetési helyzetét, mikor
    #: induljon a szűrt tartalom tetejéről, és mikor álljon vissza.
    backupFilterChanged = Signal()

    def _mentes_szuro_utak(self) -> frozenset[str] | None:
        return getattr(self, "_mentes_racs_utak", None)

    @Property(bool, notify=backupFilterChanged)
    def backupFilterActive(self) -> bool:  # noqa: N802 — QML-konvenció
        """Szűkíti-e most a rácsot a mentés-üzemmód."""
        return self._mentes_szuro_utak() is not None

    @Slot("QVariantList")
    def setBackupFilter(self, utak) -> None:  # noqa: N802
        """A rács a megadott fájlokra szűkül (teljes útvonalak).

        Üres lista = üres rács: a kiválasztott készletben minden fájlról van
        már másolat, vagy nincs kiválasztott készlet. Az azonos listára nem
        rajzolunk újra."""
        uj = frozenset(_normalt(ut) for ut in (utak or ()))
        elozo = self._mentes_szuro_utak()
        if elozo == uj:
            return
        self._mentes_racs_utak = uj
        self.backupFilterChanged.emit()
        self._mentes_ujrarajzol()

    @Slot()
    def clearBackupFilter(self) -> None:  # noqa: N802
        """Vissza a teljes rácshoz (a mentés-panel bezárásakor)."""
        if self._mentes_szuro_utak() is None:
            return
        self._mentes_racs_utak = None
        self._mentes_ujrarajzol()
        self.backupFilterChanged.emit()

    def _mentes_szurt(self, records):
        """A `_show` közös pontja: a szűrő aktív állapotában csak a még el
        nem mentett fájlok maradnak."""
        utak = self._mentes_szuro_utak()
        if utak is None:
            return records
        return tuple(r for r in records if _normalt(full_path(r)) in utak)

    def _mentes_ujrarajzol(self) -> None:
        """Az aktuális nézet újra, a szűrő új állapotával.

        A mappa-nézet mappa nélkül üres feed (`_show(())`) — azon nincs mit
        szűrni; minden más mód a `_refresh_view` saját ágán töltődik újra."""
        self._refresh_view()
