"""A csomagolt windowsos PicasaPy indulási ideje és ablakikonja (#6344, #6345).

## Miért kell

A tulajdonos szerint a telepítővel feltett program **sokkal lassabban**
indul, mint ugyanaz a verzió a Pythonos indítóval (#6344), és futás közben
**nincs ikonja** (#6345). A CI eddig csak azt nézte, hogy a csomagolt
program elindul-e, azt nem, hogy mennyi idő alatt, és milyen ikonnal.

Ez a szkript ugyanazon a gépen, ugyanabban a lépésben futtatja egymás
mellett a forrásból, a PyInstaller-mappából és a telepített programból
indított változatot, így a KÜLÖNBSÉGÜK a lelet, nem a futó gép sebessége.

## Két mód

    python csomag_meres.py ido --futtato forras=@python,picasapy \
        --futtato csomagolt=dist/PicasaPy/PicasaPy.exe

Futtatónként két egymást követő indítás (hideg, majd meleg) ugyanazzal a
profillal. Az indulási szakaszokat a program saját hibanaplójából olvassa
(`errorlog.txt`, a `StartupProgressLog` jelzései), és a folyamat indítása
előtti időbélyeghez méri. Így a PyInstaller-indító és a modulbetöltés ideje
is látszik.

    python csomag_meres.py ikon --futtato telepitett=C:/.../PicasaPy.exe

VALÓDI ablakkal indít (nem `offscreen`), és amíg a program fut, a folyamat
látható felső szintű ablakaitól lekérdezi a Windows ikonját
(`WM_GETICON`, illetve az ablakosztály ikonja). A tálca és az Alt+Tab ezt
mutatja. `--szigoru` mellett bukik, ha egyik ablaknak sincs ikonja.

## Valósághű indulás (#6355)

    python csomag_meres.py ido --futtato csomagolt=dist/PicasaPy/PicasaPy.exe \
        --kepek 2000 --halozati-export "\\\\192.0.2.1\\picasa\\export" --hatar-mp 5

Üres könyvtáron a csomagolt program 4-5 s alatt indul, a tulajdonos gépén
viszont 30-40 s alatt: az idő az ADATTAL nő. Ez a mód ezért sok képpel
(`--kepek`, mappánként 50) és egy elérhetetlen hálózati exportcéllal
(`--halozati-export`, a tulajdonos NAS-ának mintájára) indít. A
`192.0.2.0/24` dokumentációs címtartomány: oda soha semmi nem válaszol, a
Windows tehát kivárja a hálózati időkorlátot. `--hatar-mp` mellett bukik,
ha a főablak bármelyik indításnál ennél később jelenik meg.

`--indulo-hatar-ms 1000` bekapcsolja a valódi Windows-ablakos mérést is: a
naplójelzésből kiszámolja a külön indulóablak megjelenési idejét, a képernyőből
pedig ellenőrzi a splash ténylegesen kirajzolt, szöveg nélküli alsó sávját.
Alapértelmezésben ez a kapu ki van kapcsolva.

Ez CI-eszköz, nem termékkód: a csomag nem tartalmazza.
"""

from __future__ import annotations

import argparse
# A kiemelt függvények globális nevei a régi modulon keresztüli monkeypatch-ekhez kellenek.
import base64  # noqa: F401
import hashlib  # noqa: F401
import json  # noqa: F401
import os  # noqa: F401
import re  # noqa: F401
import shutil  # noqa: F401
import subprocess  # noqa: F401
import sys
import tempfile
import time  # noqa: F401
from datetime import datetime  # noqa: F401
from pathlib import Path
import zipfile  # noqa: F401

# A szkript közvetlen futtatásakor ez a könyvtár már a sys.path elején van;
# tesztből betöltve is tegyük elérhetővé a mellette lévő kis segédmodult.
_MERES_MODULOK = str(Path(__file__).resolve().parent)
if _MERES_MODULOK not in sys.path:
    sys.path.insert(0, _MERES_MODULOK)

#: a program saját sikerjelzése a hibanaplóban (`_StartupSmokeProbe`)
# Az indulásmérés modul melegíti elő a profilt a melegitsd_qml_cache hívással;
# a frissítési modul az indulás utáni frissitesi_indulasi_kapu ellenőrzést végzi.
import types as _types  # noqa: E402

import csomag_meres_kozos as _kozos  # noqa: E402
import csomag_meres_ido as _ido_modul  # noqa: E402
import csomag_meres_windows as _windows_modul  # noqa: E402
import csomag_meres_frissites as _frissites_modul  # noqa: E402
from csomag_meres_kozos import _futtatok  # noqa: E402
from csomag_meres_ido import ido  # noqa: E402
from csomag_meres_windows import ikon  # noqa: E402
from csomag_meres_frissites import frissites  # noqa: E402


def _tegye_elerhetove(modul) -> None:
    """A régi modulneveket megtartja, és a monkeypatch-elt globálisokat használja."""
    for nev in modul.__all__:
        ertek = getattr(modul, nev)
        if isinstance(ertek, _types.FunctionType):
            regi = ertek
            ertek = _types.FunctionType(
                regi.__code__, globals(), nev, regi.__defaults__, regi.__closure__
            )
            ertek.__kwdefaults__ = regi.__kwdefaults__
            ertek.__annotations__ = regi.__annotations__
            ertek.__dict__.update(regi.__dict__)
            ertek.__doc__ = regi.__doc__
            ertek.__module__ = regi.__module__
            ertek.__qualname__ = regi.__qualname__
        globals()[nev] = ertek


for _modul in (_kozos, _ido_modul, _windows_modul, _frissites_modul):
    _tegye_elerhetove(_modul)


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ertelmezo.add_argument("mod", choices=("ido", "ikon", "frissites"))
    ertelmezo.add_argument("--futtato", action="append", required=True)
    ertelmezo.add_argument("--inditasok", type=int, default=2)
    ertelmezo.add_argument("--szigoru", action="store_true")
    ertelmezo.add_argument("--elvart-verzio", default=None)
    ertelmezo.add_argument("--munka", type=Path, default=None)
    ertelmezo.add_argument("--kepek", type=int, default=0)
    ertelmezo.add_argument("--halozati-export", action="append", default=None)
    ertelmezo.add_argument("--hatar-mp", type=float, default=None)
    ertelmezo.add_argument("--indulo-hatar-ms", type=float, default=None)
    ertelmezo.add_argument("--kepernyokep-mappa", type=Path, default=None)
    args = ertelmezo.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    munka = args.munka or Path(tempfile.mkdtemp(prefix="picasapy-csomag-meres-"))
    futtatok = _futtatok(args.futtato)
    if args.mod == "ido":
        return ido(
            futtatok,
            args.inditasok,
            munka,
            args.elvart_verzio,
            kepek=args.kepek,
            halozati_export=args.halozati_export,
            hatar_mp=args.hatar_mp,
            indulo_hatar_ms=args.indulo_hatar_ms,
        )
    if args.mod == "frissites":
        return frissites(
            futtatok,
            munka,
            args.elvart_verzio,
            args.kepernyokep_mappa,
        )
    return ikon(futtatok, munka, args.szigoru)

if __name__ == "__main__":
    sys.exit(main())
