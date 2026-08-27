"""Tartós **tesztüzem** (#1654) — a KÖVETKEZŐ indulás naplózása.

## Miért kellett

Két mérőeszközünk van, és mindkettő pont az indulást véti el:

* `Súgó ▸ Performance Monitor` (#211) — csak MENETKÖZBEN kapcsolható be;
  mire a felhasználó eléri a menüt, az indulás rég lezajlott.
* `PICASAPY_STARTUP_TIMELINE=1` (#1601) — környezeti változó; a tulajdonos
  nem fejlesztő, nem állít env-et, és nem is szabad kérni tőle.

A #1653 (P0, 33 mp-es windowsos indulás) bizonyítéka épp ezért hiányzik.
A tesztüzem **tartós** kapcsoló: `QSettings`-ben él, túléli a kilépést, és
a következő indítás **az első ezredmásodperctől** naplóz.

## Ez a modul

Qt-mentes mag: a kapcsoló értelmezése, a parancssori kapcsoló leválasztása,
a napló összeállítása, és a NAS közös mappájába való átadás útvonalai.
A Qt-oldal (menü, vezérlő) a `picasapy.app.tesztuzem_controller`-ben él.

## ⚠️ Adatvédelem — a #211 szabálya érvényben marad

A napló NEM tartalmazhat teljes elérési utat, fájlnevet, felhasználónevet.
Ezt itt KÉT, egymástól független réteg biztosítja:

1. **Szerkezeti**: a könyvtár méretét a `konyvtar_merete()` kizárólag
   SZÁMOKBÓL számolja — nevet vagy útvonalat átadni sem lehet neki.
2. **Utolsó védvonal**: az `utvonalmentes()` a kész szövegből kiszűri az
   útvonalra és képfájlnévre emlékeztető tokeneket. Erre azért van szükség,
   mert a szakaszcímkék ma rögzített szövegek, de egy jövőbeli, futásidejű
   címke enélkül némán kiszivárogtatná a mappaszerkezetet.

## ⚠️ Semmilyen hálózati feltöltés

Az átadás **fájlmásolás** egy csatolt megosztásra. Nincs külső szolgáltatás,
nincs hitelesítés, nincs HTTP-kérés.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple

#: A tartós kapcsoló `QSettings`-kulcsa. A #211 diagnosztikájával egy
#: névtérben él, mert ugyanaz a célja: a támogatási kör kiszolgálása.
TESZTUZEM_BEALLITAS_KULCS = "diagnostics/tesztuzem"

#: A parancssori kapcsoló (#1654/2). Magyar, mert a felhasználó gépelné be
#: egy támogatási körben — de fejlesztői és CI-oldalon is ez a bejárat.
TESZTUZEM_KAPCSOLO = "--tesztuzem"

#: A közös mappa rögzített almappája — a fejlesztés innen olvassa ki.
NAPLO_ALMAPPA = "picasapy-naplo"

#: A NAS közös mappája az RPi5-ön (csatolási pont).
MEGOSZTAS_LINUX = "/mnt/nas"

#: Ugyanaz a megosztás Windowsról, UNC-alakban.
#:
#: ⚠️ GÉPNÉV, NEM IP-cím (#1668). A tulajdonos Tailscale-en át is eléri a
#: NAS-t; ott az IP-cím hálózatonként más, a gépnév viszont mindenhonnan
#: feloldódik. Beégetett IP-vel a napló otthonról működne, máshonnan nem.
MEGOSZTAS_WINDOWS = "//DS215j/lemez"

#: Az indulási napló fájlnév-előtagja a helyi gyorstárban (`default_log_dir`).
#: A `StartupTimeline.write()` ugyanezt használja — az „elküldés" ezért
#: találja meg a legutóbbi naplót.
INDULASI_NAPLO_ELOTAG = "indulas-"

#: A közös mappába kerülő fájl előtagja. Szándékosan MÁS, mint a helyié:
#: a megosztáson több gép naplói keverednek, ott a termék neve is kell.
ATADOTT_NAPLO_ELOTAG = "picasapy-indulas-"

#: Igaznak számító értékek. A `QSettings` INI-formátumban SZTRINGET ad
#: vissza (`"true"`), a natív tárolóból viszont `bool`-t — mindkettőt
#: ugyanúgy kell érteni, különben a mód platformfüggően „elfelejtődik".
_IGAZ_ERTEKEK = frozenset({"1", "true", "yes", "on", "igen", "be"})

#: Képfájl-kiterjesztések, amelyek PUSZTA fájlnévként (útvonal nélkül) is
#: kiszűrendők. ⚠️ A `.txt` SZÁNDÉKOSAN nincs benne: egy valódi szakaszcímke
#: említi (`figyelt gyökerek beolvasása (WatchedFolders.txt)`), és a kiszűrése
#: olvashatatlanná tenné a naplót — a `.txt` nem is árul el mappaszerkezetet.
_MEDIA_KITERJESZTESEK = (
    "jpg", "jpeg", "png", "gif", "bmp", "tif", "tiff", "webp", "heic",
    "heif", "raw", "cr2", "nef", "arw", "dng", "mp4", "mov", "avi", "mts",
)

_MEDIA_MINTA = re.compile(
    r"\.(?:" + "|".join(_MEDIA_KITERJESZTESEK) + r")\b", re.IGNORECASE
)

#: Windowsos meghajtó-előtag (`C:\`) — önmagában is útvonal-kezdet.
_MEGHAJTO_MINTA = re.compile(r"^[A-Za-z]:[\\/]")

#: A kiszűrt tokenek helyére kerülő jelölés. Nem törlés: a napló olvasója
#: lássa, hogy ott VOLT valami, csak nem adjuk ki.
UTVONAL_HELYETT = "‹útvonal eltávolítva›"


def ertek_igaz(ertek: Any) -> bool:
    """Igaznak számít-e a tárolt (vagy megadott) érték.

    Ismeretlen érték = kikapcsolva: egy elgépelt beállítás ne kezdjen el
    némán naplózni. Ez a függvény MINDEN indításkor lefut, kikapcsolt
    állapotban is — ezért csupa olcsó művelet, lemezhez nem nyúl."""
    if isinstance(ertek, bool):
        return ertek
    if ertek is None:
        return False
    return str(ertek).strip().casefold() in _IGAZ_ERTEKEK


def argv_tesztuzem(argv: Iterable[str]) -> bool:
    """Szerepel-e a `--tesztuzem` kapcsoló a parancssorban."""
    return TESZTUZEM_KAPCSOLO in tuple(argv)


def argv_kapcsolo_nelkul(argv: Iterable[str]) -> list[str]:
    """A parancssor a `--tesztuzem` kapcsoló NÉLKÜL — új listaként.

    ⚠️ Nem kozmetika: az `application._resolve_roots` MINDEN `argv[1:]`
    elemet figyelt gyökérnek vesz. Ha a kapcsoló bennmarad, a program egy
    `--tesztuzem` nevű mappát próbál indexelni, és a valódi gyökerek
    (`WatchedFolders.txt`) fel sem merülnek."""
    return [elem for elem in argv if elem != TESZTUZEM_KAPCSOLO]


def tesztuzem_bekapcsolva(settings: Any) -> bool:
    """A tartós beállításból olvasott állapot (`QSettings`-szerű objektum)."""
    return ertek_igaz(settings.value(TESZTUZEM_BEALLITAS_KULCS, False))


class KonyvtarMeret(NamedTuple):
    """A könyvtár mérete DARABSZÁMBAN — a #1653 fő gyanúja a méretfüggés.

    ⚠️ Szándékosan csak két szám. Nem `roots`, nem mappanév, nem útvonal:
    az adatvédelmi garancia így a TÍPUSBAN van, nem egy docstringben."""

    mappak: int
    kepek: int


def konyvtar_merete(kepszamok: Iterable[int]) -> KonyvtarMeret:
    """Mappa- és képdarabszám a mappánkénti képszámok sorozatából.

    A bemenet kizárólag SZÁMOK sorozata (az index `folders` táblájának
    `count` oszlopa) — nevet vagy útvonalat átadni sem lehet neki."""
    szamok = [int(darab) for darab in kepszamok]
    return KonyvtarMeret(mappak=len(szamok), kepek=sum(szamok))


def _utvonalszeru(token: str) -> bool:
    """Útvonalra vagy képfájlnévre emlékeztet-e a token."""
    if "/" in token or "\\" in token:
        return True
    if _MEGHAJTO_MINTA.match(token):
        return True
    return bool(_MEDIA_MINTA.search(token))


def utvonalmentes(szoveg: str) -> str:
    """A szövegből kiszűri az útvonal- és képfájlnév-szerű tokeneket.

    Token-szinten dolgozik (szóközzel elválasztott darabok), mert a
    mappanévben LEHET szóköz: a `Nyaralás 2019` két tokenre esik, és egy
    naiv, „egy-token-egy-út" szűrő a másodikat (`2019/IMG_1234.jpg`)
    bennhagyná. Így viszont mindkettő elbukik a saját jogán — az egyik a
    `/` miatt, a másik a kiterjesztés miatt —, a köztük álló, ártatlan
    szavak pedig együtt mennek a szomszédjukkal.

    ⚠️ Ez az utolsó védvonal, nem az egyetlen. A napló mezői eleve
    rögzített szövegek és számok; ez a szűrő azt fogja meg, ha valaki
    később futásidejű szöveget tesz egy szakaszcímkébe."""
    kimenet: list[str] = []
    for sor in szoveg.split("\n"):
        darabok = sor.split(" ")
        cserelt = [
            UTVONAL_HELYETT if darab and _utvonalszeru(darab) else darab
            for darab in darabok
        ]
        # az egymás melletti jelölések összevonása — egy szóközös útvonal
        # különben ötször ismételné ugyanazt
        tomoritett: list[str] = []
        for darab in cserelt:
            if (
                darab == UTVONAL_HELYETT
                and tomoritett
                and tomoritett[-1] == UTVONAL_HELYETT
            ):
                continue
            tomoritett.append(darab)
        kimenet.append(" ".join(tomoritett))
    return "\n".join(kimenet)


def naplo_szovege(
    *,
    idovonal_jelentes: str,
    fejlec: Mapping[str, Any],
    meret: KonyvtarMeret,
) -> str:
    """A tesztüzem naplójának teljes szövege (#1654/3).

    Három forrásból áll össze:

    * a `perf/logwriter.py` **session-fejléce** (verzió, platform,
      Python-/Qt-verzió, időbélyeg) — a #211 óta ez az azonosító réteg;
    * a #1601 **szakaszos indulási bontása**;
    * a könyvtár **mérete** darabszámban — a #1653 fő gyanúja a
      méretfüggés, enélkül a napló nem összevethető más gépekével.

    A kimenet átmegy az `utvonalmentes()` szűrőn."""
    sorok = [
        "PicasaPy — tesztüzem: indulási napló (#1654)",
        "",
        f"verzió:      {fejlec.get('app_version', 'ismeretlen')}",
        f"rendszer:    {fejlec.get('platform', 'ismeretlen')}",
        f"Python:      {fejlec.get('python_version', 'ismeretlen')}",
        f"Qt:          {fejlec.get('qt_version', 'ismeretlen')}",
        f"indulás:     {fejlec.get('started_at', 'ismeretlen')}",
        "",
        "A könyvtár mérete (a #1653 méretfüggés-gyanújához):",
        f"  indexelt mappák:  {meret.mappak}",
        f"  indexelt képek:   {meret.kepek}",
        "",
        "A napló SEMMILYEN elérési utat, fájlnevet és felhasználónevet",
        "nem tartalmaz — kizárólag darabszámokat és időket.",
        "",
        idovonal_jelentes,
    ]
    return utvonalmentes("\n".join(sorok))


def megosztas_gyokere(platform: str) -> Path:
    """A közös mappa gyökere a platform szerint.

    A `platform` a `sys.platform` értéke (a `_platform()` fogantyún át,
    ld. #1217) — így a linuxos teszt a windowsos ágat is ki tudja mondani."""
    if platform.startswith("win"):
        return Path(MEGOSZTAS_WINDOWS)
    return Path(MEGOSZTAS_LINUX)


def megosztas_elerheto(
    gyoker: Path,
    *,
    ismount: Callable[[str], bool] = os.path.ismount,
    unc: bool | None = None,
) -> bool:
    """Ténylegesen elérhető-e a megosztás.

    ⚠️ A puszta `is_dir()` NEM elég: a `/mnt/nas` Linuxon akkor is létező,
    üres könyvtár, ha a NAS nincs felcsatolva. Csatolás-ellenőrzés nélkül a
    napló némán a helyi lemezre kerülne, a felhasználó pedig azt hinné,
    hogy átadta — és a fejlesztés hiába várná.

    UNC-útvonalon (Windows) nincs mit csatolni: ott a létezés a mérce.

    ⚠️ #1668: Windowson egy HITELESÍTETLEN UNC-útvonalon az `is_dir()` nem
    `False`-t ad, hanem `OSError`-t dob (`WinError 1326` — „Helytelen a
    felhasználónév vagy a jelszó"). A tulajdonos gépén ez az első éles
    használatnál a felületre dobott kivételt, ahelyett hogy a „Mentés
    másként…" tartalék jutott volna szóhoz. Minden `OSError` (hitelesítés,
    időtúllépés, hálózat) ugyanazt jelenti nekünk: **nem elérhető**."""
    szoveg = str(gyoker)
    unc_e = unc if unc is not None else (szoveg.startswith(("//", "\\\\")))
    try:
        if not gyoker.is_dir():
            return False
        return True if unc_e else bool(ismount(szoveg))
    except OSError:
        return False


def naplo_celmappa(gyoker: Path) -> Path:
    """A megosztáson belüli, rögzített almappa."""
    return Path(gyoker) / NAPLO_ALMAPPA


def naplo_fajlneve(most: datetime) -> str:
    """Időbélyeges fájlnév a közös mappában."""
    return f"{ATADOTT_NAPLO_ELOTAG}{most.strftime('%Y%m%d-%H%M%S')}.txt"


def naplo_atadasa(*, forras: Path, celmappa: Path, most: datetime) -> Path:
    """A napló átmásolása a közös mappába; a cél útvonalát adja vissza.

    Fájlmásolás — se hálózati feltöltés, se külső szolgáltatás, se
    hitelesítés. Hibát (`OSError`) SZÁNDÉKOSAN feldob: ebből tudja a hívó,
    hogy a „Mentés másként…" tartalékot kell felajánlania. A néma
    sikertelenség itt a legrosszabb kimenet."""
    celmappa = Path(celmappa)
    celmappa.mkdir(parents=True, exist_ok=True)
    cel = celmappa / naplo_fajlneve(most)
    cel.write_text(Path(forras).read_text(encoding="utf-8"), encoding="utf-8")
    return cel


def legutobbi_indulasi_naplo(mappa: Path) -> Path | None:
    """A legfrissebb helyi indulási napló, vagy `None`.

    A fájlnevek időbélyege rendezhető (`indulas-ÉÉÉÉHHNN-óóppmm.txt`),
    ezért a névsorrend egyben időrend is — nem kell `stat`-olni."""
    mappa = Path(mappa)
    # #1668: ugyanaz a hibaosztály — a gyorstár is állhat hálózati profilon.
    try:
        if not mappa.is_dir():
            return None
        jeloltek = sorted(mappa.glob(f"{INDULASI_NAPLO_ELOTAG}*.txt"))
    except OSError:
        return None
    return jeloltek[-1] if jeloltek else None


def irj_indulasi_naplot(
    szoveg: str, mappa: Path, *, most: datetime | None = None
) -> Path | None:
    """A napló kiírása a helyi gyorstárba; hibánál `None`.

    Egy diagnosztika SOHA nem akadályozhatja az indulást — ezért nyeljük
    el az írási hibát (a `StartupTimeline.write()` ugyanígy tesz)."""
    most = most or datetime.now()
    cel = Path(mappa) / f"{INDULASI_NAPLO_ELOTAG}{most.strftime('%Y%m%d-%H%M%S')}.txt"
    try:
        cel.parent.mkdir(parents=True, exist_ok=True)
        cel.write_text(szoveg, encoding="utf-8")
    except OSError:
        return None
    return cel


__all__ = [
    "ATADOTT_NAPLO_ELOTAG",
    "INDULASI_NAPLO_ELOTAG",
    "MEGOSZTAS_LINUX",
    "MEGOSZTAS_WINDOWS",
    "NAPLO_ALMAPPA",
    "TESZTUZEM_BEALLITAS_KULCS",
    "TESZTUZEM_KAPCSOLO",
    "UTVONAL_HELYETT",
    "KonyvtarMeret",
    "argv_kapcsolo_nelkul",
    "argv_tesztuzem",
    "ertek_igaz",
    "irj_indulasi_naplot",
    "konyvtar_merete",
    "legutobbi_indulasi_naplo",
    "megosztas_elerheto",
    "megosztas_gyokere",
    "naplo_atadasa",
    "naplo_celmappa",
    "naplo_fajlneve",
    "naplo_szovege",
    "tesztuzem_bekapcsolva",
    "utvonalmentes",
]
