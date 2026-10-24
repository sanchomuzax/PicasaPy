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

A #5744 a dHash/Hamming keresőt a Picasa három jellemzőjére és rangsorára
cseréli. Az új `photo_similarity` cache útvonal + mtime + méret kulcsú; a
`photo_hashes.dhash` megmarad a duplikátumkeresés és az átmenet számára.

⚠️ Az eredeti adatbázisának HELYE ÉS FORMÁTUMA nincs kimérve (a jegy is
így mondja); a tárolás a mi döntésünk. Amit átvettünk, az a VISELKEDÉS: az
egyszeri építés, a róla szóló jelzés, és a külön néven megjelenő eredmény.
"""

from __future__ import annotations

import datetime as _datetime
import logging
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.dedup.similarity import (
    DEFAULT_RANK_MAX,
    SimilarityCandidate,
    decode_similarity_features,
    rank_similarity_candidates,
)
from picasapy.index import open_index
from picasapy.index.hashes import HashKey
from picasapy.index.photo_date import photo_date
from picasapy.index.similarity_features import (
    load_similarity_features,
    save_similarity_features,
)

_log = logging.getLogger(__name__)

_FEATURE_FLUSH_SIZE = 100


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
        hiányzó jellemzőket, ami nagy könyvtárnál percekig tarthat. A
        felület a `similarityUpdating`-ból tudja, hogy dolgozunk."""
        self._ensure_similarity_wired()
        photos = self._photos.photos
        if not 0 <= int(row) < len(photos):
            return
        minta = photos[int(row)]
        minta_ut = str(Path(minta.folder_path) / minta.name)
        # A QSettings-példányt ne olvasson egyszerre a GUI- és a háttérszál.
        rank_max = _rank_max(self._get_settings())

        def worker() -> None:
            try:
                talalatok = self._similar_records(minta_ut, rank_max=rank_max)
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

    def _similar_records(self, minta_ut: str, *, rank_max: int | None = None):
        """A mintához hasonló fotó-rekordok (a mintát is beleértve).

        A Picasa három jellemzőjét a külön cache-ből vesszük; a hiányzókat
        kiszámoljuk és el is tesszük — ettől lesz „legközelebb gyors"."""
        from picasapy.index.queries import all_photos

        self._ensure_similarity_wired()
        with open_index(self._db_path) as conn:
            rekordok = all_photos(conn)
            kulcsok: dict[str, HashKey] = {}
            for rekord in rekordok:
                ut = str(Path(rekord.folder_path) / rekord.name)
                kulcsok[ut] = (ut, rekord.mtime_ns, rekord.size)
            tarolt = load_similarity_features(conn, list(kulcsok.values()))

            hianyzo = [ut for ut, k in kulcsok.items() if k not in tarolt]
            # A jelzés CSAK akkor megy ki, ha tényleg van mit építeni —
            # különben minden keresésnél felvillanna egy hazug „épül".
            if hianyzo:
                self._set_similarity_updating(True)

            uj = []
            ertekek = {
                ut: tarolt[k] for ut, k in kulcsok.items() if k in tarolt
            }
            for ut in hianyzo:
                jellemzok = decode_similarity_features(Path(ut))
                if jellemzok is None:
                    continue
                ertekek[ut] = jellemzok
                uj.append((*kulcsok[ut], jellemzok))
                if len(uj) >= _FEATURE_FLUSH_SIZE:
                    save_similarity_features(conn, uj)
                    conn.commit()
                    uj.clear()
            if uj:
                save_similarity_features(conn, uj)
                conn.commit()

            minta_jellemzok = ertekek.get(minta_ut)
            if minta_jellemzok is None:
                return ()
            rekordok_uton = {
                str(Path(rekord.folder_path) / rekord.name): rekord
                for rekord in rekordok
            }
            candidates = tuple(
                SimilarityCandidate(ut, ertekek[ut], _photo_time_value(rekord))
                for ut, rekord in rekordok_uton.items()
                if ut in ertekek
            )
            if rank_max is None:
                rank_max = _rank_max(self._get_settings())
            sorrend = rank_similarity_candidates(
                minta_jellemzok,
                _photo_time_value(rekordok_uton[minta_ut]),
                candidates,
                rank_max,
            )
            return tuple(rekordok_uton[ut] for ut in sorrend)

    def _on_similarity_ready(self, records, minta_ut: str) -> None:
        """A GUI-szálon: a találatok megjelenítése külön nézetként."""
        self._ensure_similarity_wired()
        self._similarity_sample = minta_ut
        self.similarityUpdatingChanged.emit()
        # Külön nézet-mód, nem a rács szűrése: a `_refresh_view` így vissza
        # tudja állítani, és a `clearFilter` is kivezet belőle.
        self._view_mode = ("similar", minta_ut)
        self._show_filtered(records, 0.0)


def _photo_time_value(record) -> float:
    """A felvételi dátumot, majd a befagyasztott helyi fájlidőt adja.

    A Picasa a FILETIME-ot helyi SYSTEMTIME-ra, majd double-ordinalra alakítja.
    A dokumentált rang a különbségek sorrendjét használja, ezért a lineáris
    másodperc-skála ugyanazt a rangot adja, mint az ordinal napja.
    """
    try:
        value = _datetime.datetime.fromisoformat(photo_date(record))
        if value.tzinfo is not None:
            value = value.astimezone().replace(tzinfo=None)
        return _ordinal_time_value(value)
    except (OSError, ValueError, OverflowError):
        try:
            fallback = _datetime.datetime.fromtimestamp(
                record.sort_mtime_ns / 1_000_000_000
            )
        except (OSError, ValueError, OverflowError):
            # A romlott indexidejű rekord a használható dátumok mögé kerül.
            return float(_datetime.datetime.max.toordinal() * 86400)
        return _ordinal_time_value(fallback)


def _ordinal_time_value(value: _datetime.datetime) -> float:
    """Helyi naptári nap és napszak lineáris, ordinal-kompatibilis skálán."""
    return float(
        value.toordinal() * 86400
        + value.hour * 3600
        + value.minute * 60
        + value.second
        + value.microsecond / 1_000_000
    )


def _rank_max(settings) -> int:
    """A `Preferences/RankMax` értéke, hiányában az eredeti 1000-es alap."""
    try:
        return max(0, int(settings.value("Preferences/RankMax", DEFAULT_RANK_MAX)))
    except (TypeError, ValueError):
        return DEFAULT_RANK_MAX
