"""Mintakép-alapú hasonlóság-keresés — „keress ehhez hasonlót" (#1833).

Az eredeti Picasa keresésének második rétegében (`searchoptions`) a
másodpéldány-keresés MELLETT ül egy mintakép-alapú hasonlóság-keresés:
kiválasztasz EGY képet, és a program megmutatja a hozzá hasonlókat. Nálunk
eddig csak az előbbi volt meg (`dedup/`, `DedupDialog.qml`), ami más
kérdésre felel: „mely képek duplikátumai EGYMÁSNAK?".

## Amit a bináris elárul

* **`similarthumb`** — a minta-bélyegkép; **`loadsim`/`clearsim`** — a
  minta betöltése és törlése.
* **„Updating similarity database (will be fast next time)"**
  (`CSimSearch::updating`, `0x007ead60`) — hasonlósági adatbázis, ami az
  ELSŐ használatkor épül fel, és a program meg is mondja, hogy ez egyszeri
  lassulás.
* **„Similarity Search Results"** (`CAlbumState::SimSearchResults`,
  `0x004ad4e0`) — az eredmény külön néven jelenik meg.

## Amit a MI oldalunk ad hozzá

A motor megvolt: a `dedup/phash.py` dHash-e és a Hamming-távolság ugyanaz
a matematika, a `photo_hashes` tábla pedig már ma is tárolja a
kiszámított értékeket (útvonal + mtime + méret kulccsal). A „hasonlósági
adatbázis" nálunk tehát NEM új tároló — ez a meglévő gyorstár —, és az
első keresés azért lassabb, mert még nincs benne minden kép.

⚠️ Az eredeti adatbázisának HELYE ÉS FORMÁTUMA nincs kimérve (a jegy is
így mondja); a tárolás a mi döntésünk. Amit átvettünk, az a VISELKEDÉS: az
egyszeri építés, a róla szóló jelzés, és a külön néven megjelenő eredmény.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.dedup.phash import compute_dhash, hamming_distance
from picasapy.index import open_index
from picasapy.index.hashes import HashKey, load_dhashes, save_dhashes

_log = logging.getLogger(__name__)

#: A hasonlóság küszöbe dHash-bitekben (Hamming-távolság).
#:
#: ⚠️ SAJÁT DÖNTÉS, nem mért érték: az eredeti küszöbét a bináris nem
#: árulja el. A `dedup/similar.py` mai, másodpéldányokra hangolt küszöbe
#: 10; a „hasonló" lazább kérdés, mint a „duplikátum", ezért ennél
#: bővebbre vesszük. 14 bit a 64-ből ~22% eltérést enged — a gyakorlatban
#: ez fogja meg az újrakeretezett, kissé más expozíciójú vagy utólag
#: vágott változatokat, anélkül hogy a teljes könyvtárat visszaadná.
HASONLOSAG_KUSZOB = 14

#: Hány kiszámított hash után írunk az indexbe. A `dedup_controller`
#: azonos nevű állandójának mintája: egy hosszú keresés így nem egyetlen,
#: hatalmas tranzakcióban ír.
_HASH_FLUSH_SIZE = 200


class SimilarityMixin:
    """„Keress ehhez hasonlót" — a vezérlő hasonlóság-kereső szelete."""

    #: A hasonlósági adatbázis épül-e ÉPPEN. A felület ebből ad
    #: visszajelzést; a jegy külön kiköti, hogy üres várakozás TILOS
    #: (#1798 „hazudó állapot" tanulsága).
    similarityUpdatingChanged = Signal()

    #: A háttérszálról érkező eredmény — a Qt a GUI-szálra sorolja
    #: (a `PhotoOpsMixin._photoFieldUpdated` mintája).
    _similarityReady = Signal(object, str)

    def _ensure_similarity_wired(self) -> None:
        """Lusta, egyszeri állapot-inicializálás (a `TrayMixin` mintája) —
        a `controller.py` (forró fájl) `__init__`-jét nem kell módosítani."""
        if getattr(self, "_similarity_wired", False):
            return
        self._similarity_wired = True
        self._similarity_updating = False
        self._similarity_sample = ""
        self._similarityReady.connect(self._on_similarity_ready)

    # -- lekérdezések a felület felé --------------------------------------

    @Property(bool, notify=similarityUpdatingChanged)
    def similarityUpdating(self) -> bool:  # noqa: N802 — QML-konvenció
        """Épül-e éppen a hasonlósági adatbázis (`CSimSearch::updating`)."""
        self._ensure_similarity_wired()
        return self._similarity_updating

    @Property(str, notify=similarityUpdatingChanged)
    def similaritySample(self) -> str:  # noqa: N802 — QML-konvenció
        """A minta képe (`similarthumb`), vagy üres — a `clearsim` után."""
        self._ensure_similarity_wired()
        return self._similarity_sample

    # -- műveletek --------------------------------------------------------

    @Slot(int)
    def showSimilarTo(self, row: int) -> None:  # noqa: N802 — QML-konvenció
        """„Keress ehhez hasonlót" a rács `row`. képére (`loadsim`).

        A munka HÁTTÉRSZÁLON fut: az első keresés végigszámolja a még
        hiányzó dHash-eket, ami nagy könyvtárnál percekig tarthat. A
        felület a `similarityUpdating`-ból tudja, hogy dolgozunk."""
        self._ensure_similarity_wired()
        photos = self._photos.photos
        if not 0 <= int(row) < len(photos):
            return
        minta = photos[int(row)]
        minta_ut = str(Path(minta.folder_path) / minta.name)

        def worker() -> None:
            try:
                talalatok = self._similar_records(minta_ut)
            except Exception:  # pragma: no cover — a szál nem halhat némán
                _log.exception("hasonlóság-keresés: a háttérmunka elbukott")
                talalatok = ()
            finally:
                # ⚠️ `finally`: kivételnél sem ragadhat be a jelzés — a jegy
                # ezt külön kiköti.
                self._set_similarity_updating(False)
            self._similarityReady.emit(talalatok, minta_ut)

        self._start_background(worker, name="picasapy-similarity")

    @Slot()
    def clearSimilarity(self) -> None:  # noqa: N802 — QML-konvenció
        """A minta törlése (`clearsim`) — a nézet visszaáll."""
        self._ensure_similarity_wired()
        if not self._similarity_sample:
            return
        self._similarity_sample = ""
        self.similarityUpdatingChanged.emit()
        self.clearFilter()

    # -- belső ------------------------------------------------------------

    def _set_similarity_updating(self, value: bool) -> None:
        # A szelet BÁRMELYIK belépőjén át elérhető (a `_refresh_view` a
        # `_similar_records`-ot közvetlenül hívja), ezért az őr itt is kell.
        self._ensure_similarity_wired()
        if self._similarity_updating == value:
            return
        self._similarity_updating = value
        self.similarityUpdatingChanged.emit()

    def _similar_records(self, minta_ut: str):
        """A mintához hasonló fotó-rekordok (a mintát is beleértve).

        A dHash-eket a MEGLÉVŐ `photo_hashes` gyorstárból vesszük; a
        hiányzókat kiszámoljuk és el is tesszük — ettől lesz „legközelebb
        gyors"."""
        from picasapy.index.queries import all_photos

        self._ensure_similarity_wired()
        with open_index(self._db_path) as conn:
            rekordok = all_photos(conn)
            kulcsok: dict[str, HashKey] = {}
            for rekord in rekordok:
                ut = str(Path(rekord.folder_path) / rekord.name)
                kulcsok[ut] = (ut, rekord.mtime_ns, rekord.size)
            tarolt = load_dhashes(conn, list(kulcsok.values()))

            hianyzo = [ut for ut, k in kulcsok.items() if k not in tarolt]
            # A jelzés CSAK akkor megy ki, ha tényleg van mit építeni —
            # különben minden keresésnél felvillanna egy hazug „épül".
            if hianyzo:
                self._set_similarity_updating(True)

            uj: list[tuple[str, int, int, int]] = []
            ertekek: dict[str, int] = {
                ut: tarolt[k] for ut, k in kulcsok.items() if k in tarolt
            }
            for ut in hianyzo:
                ertek = compute_dhash(Path(ut))
                if ertek is None:
                    continue
                ertekek[ut] = ertek
                uj.append((*kulcsok[ut], ertek))
                if len(uj) >= _HASH_FLUSH_SIZE:
                    save_dhashes(conn, uj)
                    conn.commit()
                    uj.clear()
            if uj:
                save_dhashes(conn, uj)
                conn.commit()

            minta_hash = ertekek.get(minta_ut)
            if minta_hash is None:
                return ()
            hasonlo = {
                ut
                for ut, ertek in ertekek.items()
                if hamming_distance(ertek, minta_hash) <= HASONLOSAG_KUSZOB
            }
            return tuple(
                rekord
                for rekord in rekordok
                if str(Path(rekord.folder_path) / rekord.name) in hasonlo
            )

    def _on_similarity_ready(self, records, minta_ut: str) -> None:
        """A GUI-szálon: a találatok megjelenítése külön nézetként."""
        self._ensure_similarity_wired()
        self._similarity_sample = minta_ut
        self.similarityUpdatingChanged.emit()
        # Külön nézet-mód, nem a rács szűrése: a `_refresh_view` így vissza
        # tudja állítani, és a `clearFilter` is kivezet belőle.
        self._view_mode = ("similar", minta_ut)
        self._show_filtered(records, 0.0)
