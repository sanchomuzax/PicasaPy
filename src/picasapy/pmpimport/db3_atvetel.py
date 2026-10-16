"""A db3 adatainak átvétele a `.picasa.ini`-be — kulcsszó, hely, ARC (#2336/#3184).

## Miért kell

Az OLVASÓ oldal a #2342 óta kész: az `importer.iter_photo_records` behozza a
`tags`, `lat` és `long` oszlopokat, és a geotag tényleges jelzője a
`geoview` üressége (képenkénti egyezésre mérve a tulajdonos adatmappáján:
219/219). A **fogyasztó** hiányzott — a tulajdonos szava a jegyen:

> „Az adat ma nem az importon vész el, hanem azon, hogy nincs fogyasztója."

A `.picasa.ini` az igazságforrás (7. rögzített döntés), és az eredeti Picasa
is oda írja a `keywords=` és `geotag=` kulcsot, tehát az átvétel oda megy.

## A SZABÁLY: csak a hiányzót pótoljuk

Ugyanaz az „A" szabály, ami a #3002 arcátvételét vezeti: ahol a fotónak már
van értéke, ahhoz **hozzá sem nyúlunk**. Ha ott már áll adat, azt vagy a
felhasználó, vagy az eredeti Picasa írta — az import nem tudja, melyik a
frissebb, tehát nem is dönthet helyette. Így az átvétel **soha nem ír felül
meglévő adatot**, tehát nem ronthat el semmit.

A két adatfajta **külön** dől el: a meglévő `keywords=` nem akadálya annak,
hogy a hiányzó `geotag=` bekerüljön.

## Két réteg

1. **Tiszta átalakítás** (`kulcsszavakat_atvesz`, `helyet_atvesz`) — egy
   `IniDocument`-ből egy másikat ad, ahogy az `arcatvetel`-ben is.
2. **Futtató** (`rekordokat_atvesz`) — a beolvasott rekordokat mappánként
   csoportosítja, és az `ini.io.update_document`-en át írja ki. Enélkül a
   modul „polcon álló" kód maradna: a #3002 arcátvétele pontosan így állt,
   és az adat ugyanúgy nem ért oda.

## Miért EZ a neve (#3184)

A #2336 óta a modul nem csak kulcsszót és helyet visz: az **arcok** átvétele
(`arcatvetel.arcokat_atvesz`) ugyanebbe a ciklusba került, mert egy mappára
EGY írás jár. A régi `kulcsszo_hely_atvetel` név ezt már nem írta le — a
futtató a db3 → `.picasa.ini` átvétel közös helye.

## Ami ebben a modulban NINCS benne

A db3 beolvasása (`importer.iter_photo_records` dolga).

## #4591: a videó módosított dátuma

⚠️ Új függőség: a `pmpimport` az `index/` csomagot is használja (a videódátum
az indexbe megy, `index/atvett_datum.py`) — eddig csak az `ini/`-t.

A `videodatumokat_atvesz` a nem-JPEG rekordok Picasában módosított
dátumát (az 1. FILETIME, ha eltér a 2.-tól) a `photos.taken_at_override`-ba
írja az `index/` API-n át; a `.picasa.ini` és a fájl érintetlen. Az
indexben még nem szereplő fotó kimarad.

⚠️ **A futtatónak MA sincs hívója a felületről**: a `rekordokat_atvesz`-t
semmi nem szólítja meg a `src/` alatt — az a **#3132** (a db3-import
felhasználói kiváltója). Amíg az nincs meg, az adat a felhasználónál nem
mozdul; ez a modul viszont készen áll rá.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from picasapy.index.atvett_datum import atvett_datumokat_beir
from picasapy.index.database import open_index
from picasapy.ini.album_order import places_of_section, with_album_places
from picasapy.ini.albums import parse_album_refs
from picasapy.ini.document import IniDocument
from picasapy.ini.io import load_or_empty, update_document
from picasapy.ini.priority import prioritassal
from picasapy.metadata.gps import format_geotag
from picasapy.pmpimport.arcatvetel import arcokat_atvesz, atveendo_arcok
from picasapy.pmpimport.importer import PhotoRecord
from picasapy.pmpimport.videodatum import atveendo_datum
from picasapy.scanner.walker import PICASA_INI_NAME

_log = logging.getLogger(__name__)

#: a `.picasa.ini` kulcsai, amikbe az átvétel ír
_KULCSSZO_KULCS = "keywords"
_GEOTAG_KULCS = "geotag"
#: #3184: az arcok kulcsa — az `arcatvetel` írja, itt csak a „már van
#: adat" vizsgálatához kell
_ARC_KULCS = "faces"


def atveendo_kulcsszavak(kulcsszavak: tuple[str, ...]) -> tuple[str, ...]:
    """A ténylegesen átveendő kulcsszavak: trimmelve, üresek és
    ismétlődések nélkül, az ELSŐ előfordulás sorrendjében.

    A `.picasa.ini` `keywords=` kulcsa vesszővel elválasztott lista, tehát
    az üres elem ott két egymás melletti vesszőként jelenne meg — a Picasa
    ilyet nem ír.
    """
    eredmeny: list[str] = []
    for nyers in kulcsszavak:
        szo = (nyers or "").strip()
        if szo and szo not in eredmeny:
            eredmeny.append(szo)
    return tuple(eredmeny)


def _van_erteke(document: IniDocument, photo_name: str, kulcs: str) -> bool:
    """Van-e a fotónak NEM ÜRES értéke a megadott kulcson.

    Az üres érték (`keywords=`) nem „meglévő adat": azt pótoljuk.
    """
    szakasz = document.section(photo_name)
    if szakasz is None:
        return False
    return bool((szakasz.get(kulcs) or "").strip())


def kulcsszavakat_atvesz(
    document: IniDocument, photo_name: str, kulcsszavak: tuple[str, ...]
) -> IniDocument:
    """A db3 kulcsszavainak átvétele EGY fotóra, az „A" szabály szerint.

    Érintetlenül adja vissza a dokumentumot, ha nincs átveendő kulcsszó,
    vagy ha a fotónak **már van** nem üres `keywords=` kulcsa.
    """
    atveendo = atveendo_kulcsszavak(kulcsszavak)
    if not atveendo:
        return document
    if _van_erteke(document, photo_name, _KULCSSZO_KULCS):
        # ⛔ az „A" szabály lelke: meglévő adathoz hozzá sem nyúlunk
        return document
    return document.with_value(photo_name, _KULCSSZO_KULCS, ",".join(atveendo))


def helyet_atvesz(
    document: IniDocument,
    photo_name: str,
    latitude: float | None,
    longitude: float | None,
) -> IniDocument:
    """A db3 helyadatának átvétele EGY fotóra, az „A" szabály szerint.

    Érintetlenül adja vissza a dokumentumot, ha bármelyik koordináta
    hiányzik, ha az érték értelmetlen (a `GeoPoint` validálása szerint),
    vagy ha a fotónak **már van** nem üres `geotag=` kulcsa.

    ⚠️ A `0,0` koordinátát KIÍRJA: a hamis nullákat már az olvasó oldal
    kiszűrte a `geoview` üressége alapján, tehát ami idáig eljut, valódi
    hely (a jegy 2. tulajdonosi észrevétele).
    """
    if latitude is None or longitude is None:
        return document
    if _van_erteke(document, photo_name, _GEOTAG_KULCS):
        return document
    try:
        ertek = format_geotag(latitude, longitude)
    except (ValueError, TypeError):
        # sérült adat `None`-t ér, nem kivételt (#301 elve)
        return document
    return document.with_value(photo_name, _GEOTAG_KULCS, ertek)


@dataclass(frozen=True)
class AtvetelJelentes:
    """Mit végzett az átvétel — a hívó ebből jelent a felhasználónak."""

    #: hány `.picasa.ini`-t érintettünk
    mappak: int = 0
    #: #4889/#4900: kézi mappa- vagy albumsorrendbe vett képek száma
    sorrend: int = 0
    #: hány fotóra írtunk `keywords=` kulcsot
    kulcsszo: int = 0
    #: hány fotóra írtunk `geotag=` kulcsot
    hely: int = 0
    #: #3184: hány fotóra írtunk `faces=` kulcsot (az arcátvétel hívója)
    arc: int = 0
    #: hány fotón volt db3-adat, de az ini-ben már állt érték (nem nyúltunk hozzá)
    kihagyott: int = 0
    #: #4889/#4900: a wordhash-listák nem fájl vagy fel nem oldható sorai
    wordhash_kihagyott: int = 0
    #: #4591: hány videó (nem-JPEG) módosított dátumát vettük át az indexbe
    #: (`taken_at_override`) — külön számolva, nem az ini-kulcsok között
    videodatum: int = 0
    #: #4591: hány videódátum-átvétel bukott az indexen (zárolt/hibás index);
    #: az ini-átvételt ez nem érinti
    videodatum_hiba: int = 0

    def __add__(self, masik: "AtvetelJelentes") -> "AtvetelJelentes":
        return AtvetelJelentes(
            mappak=self.mappak + masik.mappak,
            sorrend=self.sorrend + masik.sorrend,
            kulcsszo=self.kulcsszo + masik.kulcsszo,
            hely=self.hely + masik.hely,
            arc=self.arc + masik.arc,
            kihagyott=self.kihagyott + masik.kihagyott,
            wordhash_kihagyott=(
                self.wordhash_kihagyott + masik.wordhash_kihagyott
            ),
            videodatum=self.videodatum + masik.videodatum,
            videodatum_hiba=self.videodatum_hiba + masik.videodatum_hiba,
        )


def mappa_atvetel(
    document: IniDocument,
    rekordok: tuple[PhotoRecord, ...],
    *,
    eligible_album_tokens: frozenset[str] | None = None,
) -> tuple[IniDocument, AtvetelJelentes]:
    """EGY mappa átvétele — tiszta függvény, a jelentéssel együtt.

    A jelentés a dokumentum ELŐTTI állapotából számol, tehát az
    `update_document` újrajátszásakor is a ténylegesen kiírt állapotot írja
    le.
    """
    eredmeny = document
    kulcsszo = hely = arc = sorrend = kihagyott = 0
    for rekord in rekordok:
        nev = Path(rekord.local_path).name
        volt_kulcsszo = bool(atveendo_kulcsszavak(rekord.tags)) and _van_erteke(
            eredmeny, nev, _KULCSSZO_KULCS
        )
        van_hely = rekord.latitude is not None and rekord.longitude is not None
        volt_hely = van_hely and _van_erteke(eredmeny, nev, _GEOTAG_KULCS)
        #: #3184: az arc ugyanebben a ciklusban megy ki — egy mappa EGY írás.
        #: A „már van adat" itt is az „A" szabály szerint dönt (a
        #: `faces=` kulcs jelenléte), ugyanúgy, mint a másik két fajtánál.
        volt_arc = bool(atveendo_arcok(rekord.faces)) and _van_erteke(
            eredmeny, nev, _ARC_KULCS
        )

        elotte = eredmeny
        eredmeny = kulcsszavakat_atvesz(eredmeny, nev, rekord.tags)
        irt_kulcsszo = eredmeny is not elotte
        elotte = eredmeny
        eredmeny = helyet_atvesz(
            eredmeny, nev, rekord.latitude, rekord.longitude
        )
        irt_hely = eredmeny is not elotte
        elotte = eredmeny
        eredmeny = arcokat_atvesz(eredmeny, nev, rekord.faces)
        irt_arc = eredmeny is not elotte

        kulcsszo += int(irt_kulcsszo)
        hely += int(irt_hely)
        arc += int(irt_arc)
        kihagyott += int(volt_kulcsszo or volt_hely or volt_arc)

    feldolgozott_nevek: set[str] = set()
    van_meglevo_mappasorrend = any(
        section.get("priority") is not None for section in eredmeny.file_sections()
    )
    if not van_meglevo_mappasorrend:
        for rekord in rekordok:
            if rekord.manual_priority is None:
                continue
            nev = Path(rekord.local_path).name
            if nev in feldolgozott_nevek:
                continue
            feldolgozott_nevek.add(nev)
            eredmeny = prioritassal(eredmeny, nev, rekord.manual_priority)
            sorrend += 1

    meglevo_albumok = {
        token
        for section in eredmeny.file_sections()
        for token in places_of_section(section)
    }
    uj_albumhelyek: dict[str, dict[str, float]] = {}
    for rekord in rekordok:
        nev = Path(rekord.local_path).name
        section = eredmeny.section(nev)
        if section is None:
            continue
        tagsagok = set(parse_album_refs(section.get("albums") or ""))
        for token, place in rekord.manual_album_places:
            if token in meglevo_albumok:
                continue
            if eligible_album_tokens is not None and token not in eligible_album_tokens:
                continue
            if token in tagsagok:
                uj_albumhelyek.setdefault(token, {})[nev] = place

    for token, places in uj_albumhelyek.items():
        eredmeny = with_album_places(eredmeny, token, places)
        for nev in places:
            if nev not in feldolgozott_nevek:
                feldolgozott_nevek.add(nev)
                sorrend += 1

    return eredmeny, AtvetelJelentes(
        mappak=0,
        kulcsszo=kulcsszo,
        hely=hely,
        arc=arc,
        sorrend=sorrend,
        kihagyott=kihagyott,
    )


def _mappankent(
    rekordok: Iterable[PhotoRecord],
) -> dict[Path, tuple[PhotoRecord, ...]]:
    """A rekordok mappánként, a beolvasási sorrendet megtartva."""
    csoportok: dict[Path, list[PhotoRecord]] = {}
    for rekord in rekordok:
        csoportok.setdefault(Path(rekord.local_path).parent, []).append(rekord)
    return {mappa: tuple(tetelek) for mappa, tetelek in csoportok.items()}


def _mutato(
    tetelek: tuple[PhotoRecord, ...],
    doboz: list[AtvetelJelentes],
    eligible_album_tokens: frozenset[str],
) -> "Callable[[IniDocument], IniDocument]":
    """Az `update_document` `mutate`-je EGY mappára, a jelentést gyűjtve.

    Külön gyárban, nem a cikluson belüli lezárásban: a hurokváltozóra
    hivatkozó belső függvény késői kötést kapna (`ruff` B023).
    """

    def _mutate(dokumentum: IniDocument) -> IniDocument:
        uj_dok, jelentes = mappa_atvetel(
            dokumentum,
            tetelek,
            eligible_album_tokens=eligible_album_tokens,
        )
        doboz.append(jelentes)
        return uj_dok

    return _mutate


def videodatumokat_atvesz(
    rekordok: Iterable[PhotoRecord], index_path: Path
) -> AtvetelJelentes:
    """#4591: a Picasában módosított videódátumok az indexbe.

    Csak a nem-JPEG, eltérő FILETIME-ú rekordok (`videodatum.atveendo_datum`);
    az `index/` API-n át, a meglévő `taken_at_override`-ot nem írja felül.
    Az index hibája (zárolt, sérült, újabb séma) NEM dobódik tovább: a
    jelentés `videodatum_hiba` mezője számolja, hogy az ini-átvétel ne
    vesszen el miatta.
    """
    tetelek = [
        (str(Path(r.local_path).parent), Path(r.local_path).name, datum)
        for r in rekordok
        if (datum := atveendo_datum(r)) is not None
    ]
    if not tetelek:
        return AtvetelJelentes()
    try:
        with open_index(index_path) as conn:
            return AtvetelJelentes(videodatum=atvett_datumokat_beir(conn, tetelek))
    except (sqlite3.Error, RuntimeError) as hiba:
        _log.warning(
            "A videódátumok átvétele az indexbe nem sikerült (%d tétel): %s",
            len(tetelek),
            hiba,
        )
        return AtvetelJelentes(videodatum_hiba=len(tetelek))


def rekordokat_atvesz(
    rekordok: Iterable[PhotoRecord],
    *,
    backup: bool = True,
) -> AtvetelJelentes:
    """A beolvasott db3-rekordok kulcsszavainak és helyadatának kiírása.

    Mappánként EGY `.picasa.ini`-t nyit az útvonalanként szerializált,
    best-effort konkurenciakezelésű `update_document` útján (a NAS-mappát a
    futó eredeti Picasa is írhatja).

    ⚠️ A mappát nem hozzuk létre: ha a helyi útvonal nem létezik (a remap
    másik gépre mutat), a mappa kimarad — az import CSAK OLVAS a db3-ból, a
    fotók mellé viszont nem talál ki könyvtárat.
    """
    csoportok = _mappankent(rekordok)
    albumtokenek = {
        token
        for tetelek in csoportok.values()
        for rekord in tetelek
        for token, _place in rekord.manual_album_places
    }
    meglevo_albumtokenek: set[str] = set()
    if albumtokenek:
        for mappa in csoportok:
            if not mappa.is_dir():
                continue
            document = load_or_empty(mappa / PICASA_INI_NAME)
            meglevo_albumtokenek.update(
                token
                for section in document.file_sections()
                for token in places_of_section(section)
            )
    eligible_album_tokens = frozenset(albumtokenek - meglevo_albumtokenek)

    osszes = AtvetelJelentes()
    for mappa, tetelek in csoportok.items():
        if not mappa.is_dir():
            continue
        ut = mappa / PICASA_INI_NAME
        # Száraz futás: ha nincs mit írni, HOZZÁ SEM NYÚLUNK a fájlhoz.
        # Enélkül az `update_document` változatlan tartalmat is kimentene,
        # ami üres `.picasa.ini`-t hozna létre és képfájl-mtime-ot érintene.
        _, proba = mappa_atvetel(
            load_or_empty(ut),
            tetelek,
            eligible_album_tokens=eligible_album_tokens,
        )
        if not (proba.kulcsszo or proba.hely or proba.arc or proba.sorrend):
            osszes = osszes + AtvetelJelentes(kihagyott=proba.kihagyott)
            continue

        # az `update_document` újrajátszhatja a `mutate`-et; a jelentést a
        # NYERTES futás hagyja itt (minden futás hozzáfűz) — ezért az utolsó
        doboz: list[AtvetelJelentes] = []
        update_document(
            ut,
            _mutato(tetelek, doboz, eligible_album_tokens),
            backup=backup,
        )
        vegso = doboz[-1]
        osszes = osszes + AtvetelJelentes(
            mappak=1,
            kulcsszo=vegso.kulcsszo,
            hely=vegso.hely,
            arc=vegso.arc,
            sorrend=vegso.sorrend,
            kihagyott=vegso.kihagyott,
        )
    return osszes


__all__ = [
    "AtvetelJelentes",
    "atveendo_kulcsszavak",
    "helyet_atvesz",
    "kulcsszavakat_atvesz",
    "mappa_atvetel",
    "rekordokat_atvesz",
    "videodatumokat_atvesz",
]
