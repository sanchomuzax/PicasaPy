"""Az átnevezett vagy törölt figyelt mappa rendezése (#6751).

A #1560 védelme az eltűnt figyelt gyökér indexsorait megtartja, mert a
hiány önmagában nem bizonyítja, hogy a mappa tényleg megszűnt: így néz ki
a kihúzott meghajtó is. A különbséget a gyökér SZÜLŐMAPPÁJA adja meg: ha a
szülő megvan, olvasható és nem üres, a tároló jelen van, tehát a mappát a
felhasználó nevezte át vagy törölte (a tulajdonos esete: az Intézőben
átnevezett `202611-a`, amely dőlten bent maradt).

Ilyenkor:

* ha a régi mappa képei egy testvérmappában vannak, amelyet még semmi nem
  figyel, a program követi az új nevet (a #1542 meglévő útja, sorvesztés
  nélkül);
* ha a testvért már figyeli a program (a tulajdonos esete), a régi név
  kikerül a figyeltek közül, ahogy a Mappakezelőből kivett mappa: a képek
  az új név alatt megvannak.

Ha a képek nincsenek egy testvérmappában (máshová helyezték át, vagy
törölték), a #1560 védelme változatlanul érvényes.

Ha a szülő sincs meg vagy olvashatatlan (lecsatolt meghajtó, hálózati
megosztás), semmi nem változik: a #1560 védelme érvényes marad.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtCore import QMetaObject, Qt, Slot

from picasapy.index import open_index
from picasapy.index.sync_folders import watched_root_missing
from picasapy.halozati_ut import halozati_gyoker

logger = logging.getLogger(__name__)


def szulo_jelen_van(gyoker: str | Path) -> bool:
    """Igaz, ha az eltűnt gyökér szülőmappája megvan, olvasható és nem üres.

    Az üres szülő gyanús (lecsatolt csatolási pont), az olvashatatlan pedig
    elérhetetlen tárolót jelent; egyiknél sem döntünk törlésről."""
    szulo = Path(gyoker).parent
    if szulo == Path(gyoker):
        return False
    try:
        with os.scandir(szulo) as bejegyzesek:
            return next(iter(bejegyzesek), None) is not None
    except OSError:
        return False


def indexelt_fajlnevek(conn, mappa: str) -> frozenset[str]:
    """Az index szerint a mappában (közvetlenül) álló fájlok nevei."""
    sorok = conn.execute(
        "SELECT p.name FROM photos p JOIN folders f ON f.id = p.folder_id "
        "WHERE f.path = ?",
        (mappa,),
    )
    return frozenset(nev for (nev,) in sorok)


def atnevezett_testver(gyoker: str | Path, nevek: frozenset[str]) -> str | None:
    """A szülő azon testvérmappája, amelyben a régi mappa összes képe áll.

    Csak egyértelmű egyezést fogad el: üres névhalmaznál, vagy ha több
    testvér is egyezik, nincs követés."""
    if not nevek:
        return None
    regi = Path(gyoker)
    talalatok = []
    try:
        with os.scandir(regi.parent) as bejegyzesek:
            for bejegyzes in bejegyzesek:
                if not bejegyzes.is_dir(follow_symlinks=False):
                    continue
                try:
                    with os.scandir(bejegyzes.path) as fajlok:
                        tartalom = {f.name for f in fajlok if f.is_file()}
                except OSError:
                    continue
                if nevek <= tartalom:
                    talalatok.append(str(regi.parent / bejegyzes.name))
    except OSError:
        return None
    return talalatok[0] if len(talalatok) == 1 else None


def atnevezett_gyoker(conn, gyoker: str | Path) -> bool:
    """Igaz, ha az eltűnt figyelt gyökeret a #6751 szabálya szerint átnevezték.

    A szinkronmunkás ezt nem jelenti hibának (#6762): a szinkron végén a
    rendező követi az új nevet, a hibasáv pedig téves riasztás volna."""
    if Path(gyoker).is_dir() or not szulo_jelen_van(gyoker):
        return False
    return atnevezett_testver(gyoker, indexelt_fajlnevek(conn, str(gyoker))) is not None


class _LibraryEltuntGyokerMixin:
    @Slot()
    def _eltunt_gyokerek_rendezese(self) -> None:
        """A szinkron végén háttérben vizsgálja az eltűnt figyelt gyökereket."""
        if getattr(self, "_missing_root_check_running", False):
            return
        roots = tuple(self._roots)
        if not any(halozati_gyoker(root) is not None for root in roots):
            # Helyi lemezen megtartjuk a korábbi közvetlen útvonalat; a
            # hálózati `stat()`-ok az alábbi workerben futnak.
            results = []
            for gyoker in roots:
                if not watched_root_missing(gyoker) or not szulo_jelen_van(gyoker):
                    continue
                with open_index(self._db_path) as conn:
                    nevek = indexelt_fajlnevek(conn, gyoker)
                uj = atnevezett_testver(gyoker, nevek)
                if uj is not None:
                    results.append((gyoker, uj))
            self._missing_root_results = results
            self._apply_missing_root_results()
            return
        self._missing_root_check_running = True

        def worker() -> None:
            results = []
            for gyoker in roots:
                if not watched_root_missing(gyoker) or not szulo_jelen_van(gyoker):
                    continue
                with open_index(self._db_path) as conn:
                    nevek = indexelt_fajlnevek(conn, gyoker)
                uj = atnevezett_testver(gyoker, nevek)
                if uj is not None:
                    results.append((gyoker, uj))
            self._missing_root_results = results
            QMetaObject.invokeMethod(
                self,
                "_apply_missing_root_results",
                Qt.ConnectionType.QueuedConnection,
            )

        def on_error(error: Exception) -> None:
            self._missing_root_check_running = False
            logger.warning("A figyelt gyökerek háttérellenőrzése hibára futott: %s", error)

        self._start_background(
            worker,
            name="picasapy-watched-root-check",
            on_error=on_error,
        )

    @Slot()
    def _apply_missing_root_results(self) -> None:
        """A háttérben készített gyökér-rendezést biztonságosan alkalmazza."""
        self._missing_root_check_running = False
        results = getattr(self, "_missing_root_results", ())
        self._missing_root_results = ()
        for gyoker, uj in results:
            if gyoker not in self._roots:
                continue
            if self._find_root(uj) is None:
                if self._kovesd_a_gyoker_athelyezeset(gyoker, uj):
                    logger.info(
                        "#6751: az átnevezett figyelt mappa követve: %s -> %s",
                        gyoker,
                        uj,
                    )
                continue
            logger.info(
                "#6751: a figyelt mappát átnevezték egy már figyelt mappára (%s); "
                "a régi név kikerül a figyeltek közül: %s",
                uj,
                gyoker,
            )
            self.removeWatchedFolder(gyoker)
