"""Az Ajándék CD (#3503) — az AppController szelete.

A kiadás-panel Ajándék-CD üzemmódja a **képtálca** elemeiből dolgozik
(`publish/giftcdtext`: „A program a fent pipával kijelölt elemeket másolja
az ajándék CD-re"), ugyanúgy, mint a tálca alatti többi kimenet (#455). A
munka háttérszálon fut: nagy tálcánál az átméretezés és a lemezkép-írás
percekig is eltarthat.

A lemezkép összeállítása a `picasapy.burn.ajandek_cd` magé; ez a modul csak
a tálcát olvassa, a honosított mappanevet adja, és jelez a felületnek.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Signal, Slot

from picasapy.burn.ajandek_cd import ajandek_cd_lemezkep

from .export_controller import _export_item
from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)


class AjandekCdMixin(BackgroundWorkerMixin):
    """„Létrehozás ▸ Ajándék CD készítése…" — a lemezkép háttérszála."""

    #: (a kész lemezkép útja — üres, ha nem készült; rákerült elemek;
    #: sikertelen elemek)
    ajandekCdKesz = Signal(str, int, int)

    @Slot(result=str)
    def ajandekCdAlapHely(self) -> str:  # noqa: N802 — QML-slot-stílus
        """A lemezkép-mentés kiinduló mappája: a felhasználó Képek mappája."""
        return QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )

    @Slot(int, str, str)
    def ajandekCdIrasa(  # noqa: N802 — QML-slot-stílus
        self, meret_index: int, cd_nev: str, cel: str
    ) -> None:
        """A tálca elemeiből lemezkép a `cel` útra (URL vagy helyi út).

        A tálca rekordjait a FŐSZÁLON olvassuk ki (a modell nem szálbiztos),
        a lemezkép a háttérszálon készül."""
        felold = getattr(self, "_tray_records", None)
        tetelek = tuple(_export_item(r) for r in felold()) if felold else ()
        cel_ut = Path(to_local_path(cel))
        if cel_ut.suffix.lower() != ".iso":
            cel_ut = cel_ut.with_name(cel_ut.name + ".iso")
        # a mappanév HONOSÍTOTT (`il_BurnPanel::picfolder`, spec 4.)
        kepek_mappa = self.tr("Pictures")
        self._start_background(
            self._ajandek_cd_hattereben,
            args=(tetelek, cel_ut, int(meret_index), str(cd_nev), kepek_mappa),
            name="ajandek-cd",
        )

    def _ajandek_cd_hattereben(
        self, tetelek, cel: Path, meret_index: int, cd_nev: str,
        kepek_mappa: str,
    ) -> None:
        try:
            eredmeny = ajandek_cd_lemezkep(
                tetelek, cel, meret_index=meret_index, cd_nev=cd_nev,
                kepek_mappa=kepek_mappa,
            )
        except (OSError, ValueError) as hiba:
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
