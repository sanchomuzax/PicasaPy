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
import sys
import tempfile
from pathlib import Path

# A szkript közvetlen futtatásakor ez a könyvtár már a sys.path elején van;
# tesztből betöltve is tegyük elérhetővé a mellette lévő kis segédmodult.
_MERES_MODULOK = str(Path(__file__).resolve().parent)
if _MERES_MODULOK not in sys.path:
    sys.path.insert(0, _MERES_MODULOK)

# Az indulásmérés a melegitsd_qml_cache hívással készíti elő a profilt;
# a frissítési mérés a frissitesi_indulasi_kapu ellenőrzést végzi.
# A régi közvetlen hívásokhoz a modulnevek újraexportként megmaradnak; a
# függvényobjektumok a saját moduljuk globális névterét használják.
from csomag_meres_kozos import (  # noqa: E402
    _BEALLITAS_KULCS,
    _EXPORT_ERTEK,
    _HelyiKiadasszerver,
    _IDOKORLAT_MP,
    _INDULOABLAK,
    _KEP_MAPPANKENT,
    _SIKER,
    _SOR,
    _futtatok,
    _keszits_frissitesi_zip,
    _platform,
    _resz,
    _sha256_fajl,
)
from csomag_meres_ido import (  # noqa: E402
    _bevar,
    _egy_inditas,
    _exportcelok_beallitasa,
    _exportcelok_visszaallitasa,
    _ido_futtato,
    _indulo_jelentes,
    _jelentes,
    _kepekkel_tolt,
    _naplo_sorai,
    _profil,
    foablak_mp,
    hatar_hiba,
    ido,
    indulo_hatar_hiba,
    indulo_kozepertek_hiba,
    induloablak_ms,
)
from csomag_meres_windows import (  # noqa: E402
    _ablakikonok,
    _splash_ablak,
    _induloablak_kepe,
    _kepernyokep,
    _renderelt_indulokep_ellenorzese,
    ikon,
)
from csomag_meres_frissites import (  # noqa: E402
    _NYUGALOM_MP,
    _about_menu,
    _about_verzio_latszik,
    _csatolt_folyamatok_leallitasa,
    _diagnosztika,
    _eloterbe_hoz,
    _elso_inditasi_kerdes_lezarasa,
    _falido,
    _frissites_utana_indulasi_kapu,
    _help_menu,
    _kepernyokep_mentese,
    _kilepes_diagnosztika,
    _kovetkezo_verzio,
    _lathato_koordinataval,
    _objektum,
    _stabil_kattintas,
    _szunet,
    _uj_folyamat_diagnosztika,
    _valodi_eger_kattintas,
    _varjon_diagnosztikara,
    frissites,
)

__all__ = (
    "_BEALLITAS_KULCS",
    "_EXPORT_ERTEK",
    "_HelyiKiadasszerver",
    "_IDOKORLAT_MP",
    "_INDULOABLAK",
    "_KEP_MAPPANKENT",
    "_NYUGALOM_MP",
    "_SIKER",
    "_SOR",
    "_about_menu",
    "_about_verzio_latszik",
    "_ablakikonok",
    "_splash_ablak",
    "_bevar",
    "_csatolt_folyamatok_leallitasa",
    "_diagnosztika",
    "_egy_inditas",
    "_eloterbe_hoz",
    "_elso_inditasi_kerdes_lezarasa",
    "_exportcelok_beallitasa",
    "_exportcelok_visszaallitasa",
    "_falido",
    "_frissites_utana_indulasi_kapu",
    "_futtatok",
    "_help_menu",
    "_ido_futtato",
    "_indulo_jelentes",
    "_induloablak_kepe",
    "_jelentes",
    "_kepernyokep",
    "_kepernyokep_mentese",
    "_kepekkel_tolt",
    "_keszits_frissitesi_zip",
    "_kilepes_diagnosztika",
    "_kovetkezo_verzio",
    "_lathato_koordinataval",
    "_naplo_sorai",
    "_objektum",
    "_platform",
    "_profil",
    "_renderelt_indulokep_ellenorzese",
    "_resz",
    "_sha256_fajl",
    "_stabil_kattintas",
    "_szunet",
    "_uj_folyamat_diagnosztika",
    "_valodi_eger_kattintas",
    "_varjon_diagnosztikara",
    "foablak_mp",
    "frissites",
    "hatar_hiba",
    "ido",
    "ikon",
    "indulo_hatar_hiba",
    "indulo_kozepertek_hiba",
    "induloablak_ms",
    "main",
)


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
