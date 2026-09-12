"""A mentés-készlet futtatása: terv, másolás, manifeszt (#440).

Két lépés, szándékosan külön:

1. **`tervezd_meg`** — mit KELL menteni: az új és a megváltozott fájlok.
   Semmit nem ír; a felület ebből tud darabszámot és becsült méretet
   mutatni, ahogy az eredeti is („Est. %d CDs or %d DVDs").
2. **`futtasd`** — a terv végrehajtása: másolás, a `.picasa.ini` kísérése,
   manifeszt, és a nyilvántartás frissítése.

## Miért megy a `.picasa.ini` a képekkel

A jegy 4. pontja: az eredeti is így tett, és ettől lesz a mentés
**önmagában teljes értékű archívum** — a címkék, a csillagok és a
szerkesztések a képek mellett maradnak.

## A manifeszt

Az eredeti a lemez gyökerére `files.txt`-et írt a másolt fájlokról.
Ugyanez a cél: a mentés a programunk nélkül is **olvasható és
ellenőrizhető** legyen. Soronként: relatív útvonal, méret, mtime.
"""

from __future__ import annotations

from collections.abc import Callable

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from picasapy.index.backup_sets import (
    elmentett_allapot,
    jegyezd_fel_a_futast,
    jegyezd_fel_az_elmentettet,
)
from picasapy.scanner import PICASA_INI_NAME

from .szuro import szurd_meg

#: Az eredeti a lemez gyökerére `files.txt`-et írt a másolt fájlokról.
MANIFESZT_NEVE = "files.txt"


@dataclass(frozen=True)
class TervezettFajl:
    """Egy mentendő fájl: honnan, hová, és miért került a tervbe."""

    forras: Path
    relativ: Path
    meret: int
    mtime_ns: int
    #: `"uj"` vagy `"valtozott"` — a felület ezt mutathatja meg.
    ok: str


@dataclass(frozen=True)
class Terv:
    """Amit a következő futás elvégezne."""

    fajlok: tuple[TervezettFajl, ...]
    #: A már elmentett, azóta változatlan fájlok száma — az eredeti
    #: üzenetének megfelelője: „Picasa is now showing the files you have
    #: not previously backed up."
    kihagyott: int

    @property
    def osszes_bajt(self) -> int:
        return sum(fajl.meret for fajl in self.fajlok)


def _relativ_ut(fajl: Path, gyokerek) -> Path:
    """A fájl útja a hozzá tartozó gyökérhez képest.

    Gyökér nélkül (vagy azon kívül) a fájl a saját mappanevével kerül be —
    az abszolút út sosem megy át a célra, mert egy `C:\\…` vagy `/home/…`
    kezdet a célmappából kilógna."""
    for gyoker in gyokerek:
        try:
            return fajl.relative_to(Path(gyoker))
        except ValueError:
            continue
    return Path(fajl.parent.name) / fajl.name


def tervezd_meg(conn, keszlet, fajlok, *, gyokerek=()) -> Terv:
    """Mit kell menteni: az ÚJ és a MEGVÁLTOZOTT fájlok (#440).

    A `fajlok` a jelöltek (az index vagy a bejárás adja); a készlet
    szűrője itt fut le rajtuk. A már elmentett, változatlan fájl kimarad —
    ez a készlet lényege.
    """
    nyilvantartas = elmentett_allapot(conn, keszlet.id)
    tervezett: list[TervezettFajl] = []
    kihagyott = 0
    for fajl in szurd_meg(fajlok, keszlet.szuro):
        try:
            allapot = fajl.stat()
        except OSError:
            # az eltűnt vagy olvashatatlan fájl nem dönti le a mentést
            continue
        korabbi = nyilvantartas.get(str(fajl))
        mostani = (allapot.st_size, allapot.st_mtime_ns)
        if korabbi == mostani:
            kihagyott += 1
            continue
        tervezett.append(
            TervezettFajl(
                forras=fajl,
                relativ=_relativ_ut(fajl, gyokerek),
                meret=allapot.st_size,
                mtime_ns=allapot.st_mtime_ns,
                ok="valtozott" if korabbi is not None else "uj",
            )
        )
    return Terv(tuple(tervezett), kihagyott)


def _ird_ki_a_manifesztet(cel: Path, tetelek) -> Path:
    manifeszt = cel / MANIFESZT_NEVE
    sorok = [
        f"{tetel.relativ.as_posix()}\t{tetel.meret}\t{tetel.mtime_ns}"
        for tetel in tetelek
    ]
    korabbi = (
        manifeszt.read_text(encoding="utf-8").splitlines()
        if manifeszt.exists()
        else []
    )
    # a manifeszt a MENTÉS teljes tartalmát írja le, nem az utolsó futásét:
    # az inkrementális futás csak hozzáad, a régi sorokat megtartja
    ismert = {sor.split("\t", 1)[0] for sor in korabbi if sor.strip()}
    ujak = [sor for sor in sorok if sor.split("\t", 1)[0] not in ismert]
    manifeszt.write_text(
        "\n".join([*korabbi, *ujak]) + "\n" if (korabbi or ujak) else "",
        encoding="utf-8",
    )
    return manifeszt


def futtasd(
    conn,
    keszlet,
    terv: Terv,
    *,
    most: str | None = None,
    haladas: Callable[[tuple[int, int]], None] | None = None,
    megszakitva: Callable[[], bool] | None = None,
) -> tuple[Path, ...]:
    """A terv végrehajtása; a ténylegesen átmásolt fájlok célútjai.

    A nyilvántartásba CSAK a sikeresen átmásolt fájl kerül be — egy
    megszakadt mentés után a következő futás így pótolja a hiányzót.

    #3009: `haladas` fájlonként kapja a `(hányadik, hány)` párt — az
    eredeti is végig beszél („Copying (%d/%d) files"). A `megszakitva`
    minden fájl ELŐTT megkérdezi, folytassuk-e; a már átmásoltak
    bekerülnek a nyilvántartásba, tehát a megszakítás nem veszít el
    munkát, csak elhalasztja a maradékot.
    """
    cel = Path(keszlet.cel)
    cel.mkdir(parents=True, exist_ok=True)
    masoltak: list[Path] = []
    feljegyzendo: list[tuple[str, int, int]] = []
    ini_mappak: set[Path] = set()
    osszes = len(terv.fajlok)
    for index, tetel in enumerate(terv.fajlok, start=1):
        if megszakitva is not None and megszakitva():
            break
        celfajl = cel / tetel.relativ
        celfajl.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(tetel.forras, celfajl)
        except OSError:
            # a bukott fájl kimarad a nyilvántartásból, tehát a következő
            # futás újra megpróbálja
            continue
        masoltak.append(celfajl)
        feljegyzendo.append((str(tetel.forras), tetel.meret, tetel.mtime_ns))
        ini_mappak.add(tetel.forras.parent)
        if haladas is not None:
            haladas((index, osszes))

    for mappa in sorted(ini_mappak):
        ini = mappa / PICASA_INI_NAME
        if not ini.is_file():
            continue
        celmappa = (cel / _ini_relativ(mappa, terv)).parent
        celmappa.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(ini, celmappa / PICASA_INI_NAME)
        except OSError:
            continue

    _ird_ki_a_manifesztet(cel, [
        tetel for tetel in terv.fajlok
        if (cel / tetel.relativ) in set(masoltak)
    ])
    if feljegyzendo:
        jegyezd_fel_az_elmentettet(conn, keszlet.id, feljegyzendo)
    jegyezd_fel_a_futast(
        conn,
        keszlet.id,
        most or datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return tuple(masoltak)


def _ini_relativ(mappa: Path, terv: Terv) -> Path:
    """A mappához tartozó `.picasa.ini` helye a célon belül.

    A mappa relatív útját a benne lévő, MÁR tervezett fájl adja meg — így
    az ini pontosan a képei mellé kerül."""
    for tetel in terv.fajlok:
        if tetel.forras.parent == mappa:
            return tetel.relativ.parent / PICASA_INI_NAME
    return Path(mappa.name) / PICASA_INI_NAME
