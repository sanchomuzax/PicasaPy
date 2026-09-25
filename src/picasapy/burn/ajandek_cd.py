"""Az Ajándék CD lemezképe (#3503).

## Mit ad ez a modul

A képtálca elemeiből egyetlen ISO 9660 + Joliet lemezképet — a mért
Ajándék-CD beállításokkal (`docs/specs/ajandek-cd-kimenet.md` 12.4):

| beállítás | érték | nálunk |
|---|---|---|
| mappanév | `il_BurnPanel::picfolder` („Képek") | a hívó adja, honosítva |
| `option_imagesizelimit` | a választott fokozat (0 · 640 · 800 · 1600) | `MERETEK` |
| `option_jpegquality` | 85 | `JPEG_MINOSEG` |
| `option_preservemovies` | 1 | a film bájthűen másolódik |
| `option_createhtml` | 0 | nincs HTML |
| `option_inifile` | nincs az ágon | nincs `.picasa.ini` a lemezen |

A képek átalakítását a közös export-mag végzi (a forgatás és a
szerkesztési lánc beleég, ahogy a rácson látszik); a nem-JPEG kép JPEG-gé
válik — az eredetiben ezt a `Preferences\\CDSlideshow` alapértéke (1)
kapcsolja be (`option_convertnonjpeg`, 11.2).

## Amit NEM ad

A fizikai lemezírást és a Windows-os tartozékokat (`autorun.inf`, vetítő,
telepítő — 6. szakasz): Linuxon a lemezkép a kimenet.
"""

from __future__ import annotations

import dataclasses
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from picasapy.burn.iso import iso_kiirasa
from picasapy.export import ExportItem, ExportSettings, export_photos

#: `0x0066f658`–`0x0066f670`: a méretválasztó négy fokozata (0 = eredeti)
MERETEK = (0, 640, 800, 1600)
#: `0x0066f7b3`: `option_jpegquality = 0x55`
JPEG_MINOSEG = 85
#: `publish/namelimitext`: „Legfeljebb 16 karakter"
CD_NEV_HOSSZ = 16


@dataclass(frozen=True)
class AjandekCdEredmeny:
    """A lemezkép útja (`None`, ha semmi nem került rá), a rákerült elemek
    száma és a sikertelen források."""

    lemezkep: Path | None
    darab: int
    hibas: tuple[Path, ...] = ()
    okok: tuple[str, ...] = ()


def kotetnev(cd_nev: str, cel: Path) -> str:
    """A lemez kötetneve: a CD neve legfeljebb 16 karakterrel; üres névnél
    a lemezkép fájlneve (a lemez így sem marad névtelen)."""
    nev = (cd_nev or "").strip() or Path(cel).stem
    return nev[:CD_NEV_HOSSZ]


def ajandek_cd_lemezkep(
    tetelek: Iterable[ExportItem],
    cel: Path,
    *,
    meret_index: int,
    cd_nev: str,
    kepek_mappa: str,
) -> AjandekCdEredmeny:
    """A tálca elemeiből az Ajándék CD lemezképe.

    Egy hibás elem nem állítja le a többit (az export-mag szerződése); ha
    egyetlen elem sem sikerül, lemezkép sem készül. A köztes fájlok a
    lemezkép MELLETT, ideiglenes mappában készülnek, és a végén törlődnek —
    a rendszer `/tmp`-je kicsi lehet (tmpfs), a cél-meghajtó nem."""
    if not 0 <= int(meret_index) < len(MERETEK):
        raise ValueError(f"Érvénytelen méretfokozat: {meret_index}")
    cel = Path(cel)
    meret = MERETEK[int(meret_index)]
    beallitas = ExportSettings(
        max_dimension=meret or None,
        jpeg_quality=JPEG_MINOSEG,
        movie_full=True,
    )
    # az Ajándék-CD ágon nincs `option_inifile`: a felirat és a címkék nem
    # kerülhetnek a lemezre egy `.picasa.ini`-ben
    tisztitott = tuple(
        dataclasses.replace(tetel, caption=None, keywords=None)
        for tetel in tetelek
    )
    if not tisztitott:
        return AjandekCdEredmeny(lemezkep=None, darab=0)
    cel.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".ajandek-cd-", dir=cel.parent
    ) as munka:
        jelentes = export_photos(tisztitott, Path(munka), beallitas)
        if not jelentes.exported:
            return AjandekCdEredmeny(
                lemezkep=None, darab=0,
                hibas=jelentes.failed, okok=jelentes.reasons,
            )
        # a kép előbb a munkamappába készül, és csak kész állapotban kerül
        # a helyére: egy írás közbeni hiba (tele lemez) nem hagy csonka
        # `.iso`-t, és nem teszi tönkre a korábbit (ugyanaz a kötet, tehát
        # a csere atomikus)
        kesz = Path(munka) / ".lemezkep.iso"
        iso_kiirasa(
            ((f"{kepek_mappa}/{ut.name}", ut) for ut in jelentes.exported),
            kesz,
            kotetnev=kotetnev(cd_nev, cel),
        )
        os.replace(kesz, cel)
    return AjandekCdEredmeny(
        lemezkep=cel,
        darab=len(jelentes.exported),
        hibas=jelentes.failed,
        okok=jelentes.reasons,
    )


__all__ = [
    "CD_NEV_HOSSZ",
    "JPEG_MINOSEG",
    "MERETEK",
    "AjandekCdEredmeny",
    "ajandek_cd_lemezkep",
    "kotetnev",
]
