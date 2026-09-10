"""A másodpéldány-keresés KERESÉSI MÓDKÉNT (#1398).

Az eredeti Picasa „Eszközök ▸ Kísérleti ▸ Show Duplicate Files"
(`eMenuTools::ID_DUPES`) parancsa **nem párbeszédet nyit**: a keresési sáv
rejtett `dupesearch` jelzőjét kapcsolja be, tehát ugyanolyan szűrt nézetbe
visz, mint a szöveges keresés. A módból a sáv `viewallbutton`-ja vezet ki
(felirata **„Back to View All"**, súgója „Exit Search Mode").

Mérve (#1398): a `dupesearch` elemet hat függvény hivatkozza, köztük a
főablak parancs-diszpécsere (`0x005cb990`); a `searchcontainer/` öt
szűrő-kapcsolója (`starsearch`, `facesearch`, `moviesearch`,
`geotagsearch`, `webview`) közt a másodpéldány-mód NINCS ott — azt
kizárólag a menüpont kapcsolja.

## Mit tekintünk másodpéldánynak

**A Picasa saját `originfast` kulcsát** (fej+farok MD5, 64 bit — #1481). Ez
MÉRT döntés, nem a mi választásunk: a `iCAcquireDupeCheckJob`
(`0x00513730`) a fájl `originfast`-ját számolja ki (`FUN_00a4d210`), és ezt
a 64 bites értéket keresi a másodpéldány-listában (`FUN_00436980`) — a
találat a dupe-jelölés (`docs/specs/picasa-kereses-modok.md`, 6. szakasz;
Ghidra-C, megerősített). Tehát NEM a fájlnév, NEM a `backuphash`, és nem
is a teljes tartalom-hash.

A kulcsokat az index gyorstára szolgálja ki (#1494,
`IndexFastKeySource`): a változatlan képek fájlvégeit a második keresés sem
olvassa be újra, és a teljes fájlt egyszer sem olvassuk végig — a kulcs
legfeljebb 33 672 bájtot lát fájlonként.

A perceptuálisan HASONLÓ képek szándékosan kimaradnak: az eredetiben a
hasonlóság-keresés öt eleme ki van kommentezve, tehát nem létezik — nálunk
külön funkció (`similarity_controller.py`, #1833), saját belépési ponttal.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index import open_index
from picasapy.index.fast_key_source import IndexFastKeySource

_log = logging.getLogger(__name__)

#: A nézet-mód neve (`_view_mode[0]`) — a felület ebből tudja, hogy a
#: `dupesearch` jelző be van kapcsolva.
DUPE_MOD = "dupes"


class DupeSearchMixin:
    """„Fájlok másodpéldányainak megjelenítése" — keresési mód, nem panel."""

    #: Fut-e ÉPPEN a keresés. A nagy könyvtár átvizsgálása másodpercekig
    #: tart, és üres várakozás TILOS (#1798) — a sáv ebből ad jelzést.
    dupeSearchChanged = Signal()

    #: A háttérszálról érkező eredmény; a Qt a GUI-szálra sorolja
    #: (a `SimilarityMixin._similarityReady` mintája).
    _dupesReady = Signal(object)

    def _ensure_dupe_search_wired(self) -> None:
        """Lusta, egyszeri állapot-inicializálás — a `controller.py` (forró
        fájl) `__init__`-jéhez így nem kell nyúlni."""
        if getattr(self, "_dupe_search_wired", False):
            return
        self._dupe_search_wired = True
        self._dupe_search_scanning = False
        self._dupesReady.connect(self._on_dupes_ready)

    # -- lekérdezések a felület felé --------------------------------------

    @Property(bool, notify=dupeSearchChanged)
    def dupeSearchScanning(self) -> bool:  # noqa: N802 — QML-konvenció
        """Fut-e éppen a másodpéldány-keresés."""
        self._ensure_dupe_search_wired()
        return self._dupe_search_scanning

    # -- műveletek --------------------------------------------------------

    @Slot()
    def showDuplicateFiles(self) -> None:  # noqa: N802 — QML-konvenció
        """Váltás a másodpéldány-MÓDBA (`ID_DUPES`).

        A munka HÁTTÉRSZÁLON fut: a teljes könyvtár átvizsgálása nagy
        gyűjteménynél hosszú, a felületet pedig nem blokkolhatja."""
        self._ensure_dupe_search_wired()
        self._set_dupe_scanning(True)

        def worker() -> None:
            try:
                rekordok = self._duplicate_records()
            except Exception:  # pragma: no cover — a szál nem halhat némán
                _log.exception("másodpéldány-keresés: a háttérmunka elbukott")
                rekordok = ()
            finally:
                # ⚠️ `finally`: kivételnél sem ragadhat be a jelzés.
                self._set_dupe_scanning(False)
            self._dupesReady.emit(rekordok)

        self._start_background(worker, name="picasapy-dupes")

    # -- belső ------------------------------------------------------------

    def _set_dupe_scanning(self, value: bool) -> None:
        self._ensure_dupe_search_wired()
        if self._dupe_search_scanning == value:
            return
        self._dupe_search_scanning = value
        self.dupeSearchChanged.emit()

    def _duplicate_records(self):
        """A könyvtár azon fotó-rekordjai, amelyeknek van másodpéldánya.

        A csoportosítás kulcsa a Picasa `originfast`-ja (ld. a modul
        docstringjét). Egy kulcshoz tartozó MINDEN kép bekerül (az
        „eredeti" is): a felhasználó épp azt akarja látni, mi kettőződött
        meg. A sorrend az indexé, hogy a rács mappánkénti csoportosítása
        változatlan maradjon."""
        from picasapy.index.queries import all_photos

        with open_index(self._db_path) as conn:
            rekordok = all_photos(conn)
            azonossagok = {
                str(Path(rekord.folder_path) / rekord.name): (
                    str(Path(rekord.folder_path) / rekord.name),
                    rekord.mtime_ns,
                    rekord.size,
                )
                for rekord in rekordok
            }
            kulcsforras = IndexFastKeySource(conn, azonossagok)
            kulcsok: dict[str, int] = {}
            try:
                for ut in azonossagok:
                    kulcs = kulcsforras(Path(ut))
                    if kulcs is not None:
                        kulcsok[ut] = kulcs
            finally:
                # a `flush()` maga commitol és maga nyeli el a saját
                # index-hibáit (#1494) — kész eredményt nem ronthat el
                kulcsforras.flush()
        darab: dict[int, int] = {}
        for kulcs in kulcsok.values():
            darab[kulcs] = darab.get(kulcs, 0) + 1
        return tuple(
            rekord
            for rekord in rekordok
            if darab.get(
                kulcsok.get(str(Path(rekord.folder_path) / rekord.name), -1), 0
            )
            > 1
        )

    def _on_dupes_ready(self, records) -> None:
        """A GUI-szálon: a találatok megjelenítése külön nézet-módként.

        Külön mód, nem egyszeri szűrés: így a `_refresh_view` vissza tudja
        állítani (#1830 tanulsága), a `clearFilter` pedig kivezet belőle."""
        self._ensure_dupe_search_wired()
        self._view_mode = (DUPE_MOD, "")
        self._show_filtered(records, 0.0)
