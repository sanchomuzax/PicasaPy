"""Az Ajándék CD (#3503, #7315): az AppController szelete.

A kiadás-panel alapforrása a jelenlegi mappa; a felhasználó a panelen
választhatja helyette a képtálcát. A munka háttérszálon fut: a mappa összes
fájljának átméretezése és a lemezkép-írás percekig is eltarthat.

A lemezkép összeállítása a `picasapy.burn.ajandek_cd` magé; ez a modul csak
a panel által választott mappát vagy tálcát olvassa, a honosított mappanevet
adja, és jelez a felületnek.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QUrl, Signal, Slot

from picasapy.burn.ajandek_cd import ajandek_cd_lemezkep
from picasapy.paths import path_key

from .export_controller import _export_item
from .formatting import to_file_url, to_local_path
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)


class AjandekCdMixin(BackgroundWorkerMixin):
    """„Létrehozás ▸ Ajándék CD készítése…" — a lemezkép háttérszála."""

    #: (a kész lemezkép útja — üres, ha nem készült; rákerült elemek;
    #: sikertelen elemek)
    ajandekCdKesz = Signal(str, int, int)

    def _ajandek_cd_mappa_rekordok(self, mappa: str) -> tuple:
        """A megadott mappa képei a már betöltött könyvtárfeedből."""
        if not mappa:
            return ()
        cel = path_key(mappa)
        if not cel:
            return ()
        photos = getattr(getattr(self, "_photos", None), "photos", ())
        return tuple(
            rekord for rekord in photos
            if path_key(rekord.folder_path) == cel
        )

    @Slot(result=int)
    def ajandekCdAktualisMappaDarab(self) -> int:  # noqa: N802
        """A jelenlegi mappa lemezképre választható fájljainak száma."""
        return len(self._ajandek_cd_mappa_rekordok(self.currentFolder))

    @Slot(result=QUrl)
    def ajandekCdAlapHely(self) -> QUrl:  # noqa: N802 — QML-slot-stílus
        """A lemezkép-mentés kiinduló mappája: a felhasználó Képek mappája,
        URL-ként — kézzel fűzött `"file://" + út` Windowson érvénytelen
        (#1009)."""
        return to_file_url(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.PicturesLocation
            )
        )

    @Slot(int, str, str, str, bool, bool)
    def ajandekCdIrasaForrassal(  # noqa: N802 - QML-slot-stílus
        self,
        meret_index: int,
        cd_nev: str,
        cel: str,
        mappa_ut: str,
        mappa_kivalasztva: bool,
        diavetito_engedelyezve: bool,
    ) -> None:
        """A panelen kiválasztott mappából vagy képtálcából készít lemezképet."""
        if mappa_kivalasztva:
            rekordok = self._ajandek_cd_mappa_rekordok(mappa_ut)
        else:
            felold = getattr(self, "_tray_records", None)
            rekordok = tuple(felold()) if felold else ()
        tetelek = tuple(_export_item(r) for r in rekordok)
        self._ajandek_cd_indit(
            tetelek, meret_index, cd_nev, cel, bool(diavetito_engedelyezve)
        )

    def _ajandek_cd_indit(
        self, tetelek, meret_index: int, cd_nev: str, cel: str,
        diavetito_engedelyezve: bool,
    ) -> None:
        """Közös háttérmunka-indítás a tálca és a mappaforrás számára."""
        cel_ut = Path(to_local_path(cel))
        if cel_ut.suffix.lower() != ".iso":
            cel_ut = cel_ut.with_name(cel_ut.name + ".iso")
        # a mappanév HONOSÍTOTT (`il_BurnPanel::picfolder`, spec 4.)
        kepek_mappa = self.tr("Pictures")
        self._start_background(
            self._ajandek_cd_hattereben,
            args=(
                tetelek, cel_ut, int(meret_index), str(cd_nev), kepek_mappa,
                bool(diavetito_engedelyezve),
            ),
            name="ajandek-cd",
        )

    def _ajandek_cd_hattereben(
        self, tetelek, cel: Path, meret_index: int, cd_nev: str,
        kepek_mappa: str, convert_non_jpeg: bool,
    ) -> None:
        try:
            eredmeny = ajandek_cd_lemezkep(
                tetelek, cel, meret_index=meret_index, cd_nev=cd_nev,
                kepek_mappa=kepek_mappa,
                convert_non_jpeg=convert_non_jpeg,
            )
        except Exception as hiba:  # noqa: BLE001 — a felület nem ragadhat „dolgozik" állapotban
            # BÁRMILYEN hiba után jelezni kell: a panel a jelzésig nem
            # engedi újra a „Lemezre írás"-t, és a felhasználó egyik
            # visszajelzést sem kapná
            _log.warning("az Ajándék CD lemezképe nem készült el: %s", hiba)
            self.ajandekCdKesz.emit("", 0, len(tetelek))
            return
        for forras, ok in zip(eredmeny.hibas, eredmeny.okok, strict=False):
            _log.warning("kimaradt az Ajándék CD-ről: %s (%s)", forras, ok)
        self.ajandekCdKesz.emit(
            str(eredmeny.lemezkep) if eredmeny.lemezkep else "",
            eredmeny.darab,
            len(eredmeny.hibas),
        )
