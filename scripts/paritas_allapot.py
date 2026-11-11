"""A paritás-felvevő állapotkivonata: lemez, bal hasáb, rács, kijelölés, nyitott rétegek (#6845).

Az útvonalak a teszt-könyvtárhoz képest, előreperjeles alakban szerepelnek,
hogy két futás (és az eredeti Picasa mért állapota) összevethető legyen,
függetlenül az ideiglenes mappa nevétől.

A lépésenkénti kivonat (`pillanatkep`) olcsó; a teljes (`teljes`) a lemezfát is
bejárja, ezért csak a futás végén készül.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import paritas_qt as qt
else:
    from . import paritas_qt as qt

from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem

MAX_INI_BAJT = 65536
MAX_RACS_NEV = 500
_BELSO_ELOTAGOK = ("index.db", "settings.ini", "thumbs", "kollazs", "utlevel")


def relativ(gyoker: Path, ut: object) -> str:
    """A `gyoker` alatti útvonal előreperjeles relatív alakja; kívüli útvonal változatlan."""
    szoveg = str(ut)
    if not szoveg:
        return ""
    for alap in (gyoker, gyoker.resolve()):
        try:
            return Path(szoveg).relative_to(alap).as_posix()
        except ValueError:
            continue
    return Path(szoveg).as_posix()


# --- lemez ------------------------------------------------------------------------------


def _fajl_adatai(gyoker: Path, ut: Path) -> dict[str, Any]:
    statusz = ut.stat()
    return {
        "ut": ut.relative_to(gyoker).as_posix(),
        "meret": statusz.st_size,
        "mtime": int(statusz.st_mtime),
        "sha1": hashlib.sha1(ut.read_bytes(), usedforsecurity=False).hexdigest(),
    }


def fa(gyoker: Path) -> dict[str, Any]:
    """A könyvtárfa minden mappája és fájla, a `.picasa.ini` szövegével együtt."""
    mappak: list[str] = []
    fajlok: list[dict[str, Any]] = []
    ini: dict[str, str] = {}
    for ut in sorted(gyoker.rglob("*")):
        if ut.is_dir():
            mappak.append(ut.relative_to(gyoker).as_posix())
        elif ut.is_file():
            fajlok.append(_fajl_adatai(gyoker, ut))
            if ut.name == ".picasa.ini":
                szoveg = ut.read_text(encoding="utf-8", errors="replace")
                ini[ut.relative_to(gyoker).as_posix()] = szoveg[:MAX_INI_BAJT]
    return {"mappak": mappak, "fajlok": fajlok, "ini": ini}


def kivul_maradt(munka: Path, konyvtar: Path) -> list[str]:
    """A munkamappa bejegyzései a könyvtáron és az app belső fájljain kívül.

    Egy rossz helyre (a könyvtárfán kívülre) tett mappa vagy fájl itt látszik."""
    maradek: list[str] = []
    for ut in sorted(munka.rglob("*")):
        elso = ut.relative_to(munka).parts[0]
        if elso == konyvtar.name or elso.startswith(_BELSO_ELOTAGOK):
            continue
        maradek.append(ut.relative_to(munka).as_posix())
    return maradek


def lemez(munka: Path, konyvtar: Path) -> dict[str, Any]:
    return {**fa(konyvtar), "kivul": kivul_maradt(munka, konyvtar)}


# --- bal hasáb, rács, kijelölés ---------------------------------------------------------


def _szerepek(modell: Any, sor: int) -> dict[str, Any]:
    index = modell.index(sor, 0)
    return {
        bytes(nev).decode("utf-8"): modell.data(index, szerep)
        for szerep, nev in modell.roleNames().items()
    }


def bal_hasab(gyoker: Path, vezerlo: Any, ablak: Any) -> dict[str, Any]:
    """A bal hasáb mappalistája a modellből, és a ténylegesen látszó sorok."""
    modell = vezerlo.folders
    sorok = []
    for sor in range(modell.rowCount()):
        adat = _szerepek(modell, sor)
        sorok.append(
            {
                "nev": str(adat.get("name", "")),
                "ut": relativ(gyoker, adat.get("path", "")),
                "darab": int(adat.get("count") or 0),
                "fajta": str(adat.get("kind", "")),
            }
        )
    lathato = [
        {"nev": Path(str(elem.property("folderPath"))).name,
         "ut": relativ(gyoker, elem.property("folderPath"))}
        for elem in qt.vizualis_bejaras(ablak.contentItem())
        if elem.objectName() == "folderRowMouse"
        and qt.lathato_e(elem)
        and str(elem.property("folderPath"))
    ]
    return {"modell": sorok, "lathato_sorok": lathato}


def racs(gyoker: Path, vezerlo: Any) -> dict[str, Any]:
    """A rács aktuális mappája, elemszáma és (korlátig) az elemek fájlnevei sorrendben."""
    darab = int(vezerlo.photos.rowCount())
    nevek = [
        Path(str(vezerlo.photos.filePathAt(sor))).name
        for sor in range(min(darab, MAX_RACS_NEV))
    ]
    return {
        "aktualis_mappa": relativ(gyoker, vezerlo.currentFolder),
        "elemszam": darab,
        "fajlnevek": nevek,
        "album": str(vezerlo.currentAlbumToken),
        "szemely": str(vezerlo.currentPersonName),
    }


def _indexlista(ertek: Any) -> list[int]:
    nyers = ertek.toVariant() if hasattr(ertek, "toVariant") else ertek
    return sorted(int(elem) for elem in (nyers or []))


def kijeloles(vezerlo: Any, ablak: Any) -> dict[str, Any]:
    indexek = _indexlista(ablak.property("selectedIndexes"))
    return {
        "indexek": indexek,
        "fo_index": int(ablak.property("selectedIndex")),
        "fajlnevek": [
            Path(str(vezerlo.photos.filePathAt(index))).name for index in indexek
        ],
    }


# --- nyitott rétegek -----------------------------------------------------------------------


def _tipusnev(objektum: QObject) -> str:
    return objektum.metaObject().className().split("_QML", 1)[0]


def nyitott_retegek(ablak: Any) -> list[dict[str, str]]:
    """A nyitott popupok, menük és párbeszédek (a nevetleneket is, típussal)."""
    retegek = []
    for objektum in ablak.findChildren(QObject):
        if isinstance(objektum, QQuickItem):
            continue
        megnyitva = objektum.property("opened") is True
        lathato_parbeszed = (
            objektum.property("visible") is True
            and bool(objektum.objectName())
            and "Dialog" in _tipusnev(objektum)
        )
        if megnyitva or lathato_parbeszed:
            retegek.append(
                {"objectName": objektum.objectName(), "tipus": _tipusnev(objektum)}
            )
    return retegek


def masik_ablakok(fo_ablak: Any) -> list[dict[str, Any]]:
    """A főablakon kívüli látható ablakok (felugró menük, külön ablakos párbeszédek)."""
    ablakok = []
    for ablak in QGuiApplication.topLevelWindows():
        if not ablak.isVisible() or qt.azonos(ablak, fo_ablak):
            continue
        keret = ablak.geometry()
        ablakok.append(
            {
                "objectName": ablak.objectName(),
                "cim": ablak.title(),
                "x": keret.x(),
                "y": keret.y(),
                "szelesseg": keret.width(),
                "magassag": keret.height(),
            }
        )
    return ablakok


# --- összeállítás --------------------------------------------------------------------------


def pillanatkep(gyoker: Path, vezerlo: Any, ablak: Any) -> dict[str, Any]:
    """Lépésenkénti, olcsó kivonat: kijelölés, aktuális mappa, elemszám, nyitott rétegek."""
    return {
        "kijeloles": kijeloles(vezerlo, ablak)["indexek"],
        "aktualis_mappa": relativ(gyoker, vezerlo.currentFolder),
        "elemszam": int(vezerlo.photos.rowCount()),
        "nyitott_parbeszedek": _nevek(nyitott_retegek(ablak)),
    }


def _nevek(retegek: list[dict[str, str]]) -> list[str]:
    return sorted(reteg["objectName"] for reteg in retegek if reteg["objectName"])


def teljes(
    munka: Path, konyvtar: Path, vezerlo: Any, ablak: Any
) -> dict[str, Any]:
    """A futás végi teljes állapot: lemez, bal hasáb, rács, kijelölés, nyitott rétegek."""
    retegek = nyitott_retegek(ablak)
    return {
        "lemez": lemez(munka, konyvtar),
        "bal_hasab": bal_hasab(konyvtar, vezerlo, ablak),
        "racs": racs(konyvtar, vezerlo),
        "kijeloles": kijeloles(vezerlo, ablak),
        "nyitott_parbeszedek": _nevek(retegek),
        "nyitott_retegek": retegek,
        "masik_ablakok": masik_ablakok(ablak),
    }
