"""A mentés-készlet bélyege a `.picasa.ini`-ben (#7292).

Az eredeti Picasa a "mentetlen" döntést nem a képfájlon, hanem a kép
`.picasa.ini`-szakaszának két kulcsán hozza (`docs/specs/biztonsagi-mentes.md`
9.2, döntés `0x0065d010`):

* a sima `backuphash`: minden metaadat-szerkesztés (felirat, forgatás,
  kulcsszó ...) új értékre írja;
* a `BKTag <készletnév>-backuphash`: a mentés írja, a sima kulcs akkori
  értékével.

Egyenlő a kettő: a kép naprakész ebben a készletben. Eltér vagy hiányzik:
mentendő. A `0xFFFF` készletkulcs "sosem mentendő".

Az `.ini` KIZÁRÓLAG az `ini` csomag API-ján át íródik (sáv-invariáns).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from picasapy.ini import (
    IniConflictError,
    IniDocument,
    IniSaveError,
    backuphash_for_local_datetime,
    ini_source_path,
    load_document,
    update_document,
)
from picasapy.ini.names import INI_NAME

_log = logging.getLogger(__name__)

#: A készletkulcs előtagja és utótagja: `BKTag <készletnév>-backuphash`.
_ELOTAG = "BKTag "
_UTOTAG = "-backuphash"
_SIMA_KULCS = "backuphash"

#: A 16 bites bélyeg két különleges értéke: a 0 "soha nem mentett", a
#: 0xFFFF "sosem mentendő" (`0x0065e750`, `0x0065e75c`).
SOHA_NEM_MENTETT = 0
SOSEM_MENTENDO = 0xFFFF


def keszlet_kulcs(keszlet_nev: str) -> str:
    """A készlet társkulcsa a kép szakaszában (`0x00429d1c`)."""
    return f"{_ELOTAG}{keszlet_nev}{_UTOTAG}"


@dataclass(frozen=True)
class Belyeg:
    """Egy kép két kulcsa; a hiányzó vagy érthetetlen érték 0."""

    sima: int
    keszlet: int


def _ertek(szoveg: str | None) -> int:
    """A kulcs értéke 16 bitesre szűkítve (ahogy az eredeti olvasója)."""
    if szoveg is None:
        return SOHA_NEM_MENTETT
    try:
        return int(szoveg.strip()) & 0xFFFF
    except ValueError:
        return SOHA_NEM_MENTETT


def _iras_celja(mappa: Path) -> Path | None:
    """A mappa `.picasa.ini`-je, vagy `None`, ha csak a régi `Picasa.ini` van.

    A régi fájl SOHA nem írási cél (#4839): hozzá bélyeget nem írunk, és
    mellé sem hozunk létre `.picasa.ini`-t, mert az archívumba másolt ini
    bájtra azonos kell maradjon. Az olvasás is ide tartozik: ami sosem
    íródik, arról nem is döntünk."""
    cel = mappa / INI_NAME
    forras = ini_source_path(cel)
    if forras is not None and forras != cel:
        return None
    return cel


class BelyegOlvaso:
    """A tervezéshez: mappánként egyszer olvassa be az ini-t."""

    def __init__(self, keszlet_nev: str) -> None:
        self._kulcs = keszlet_kulcs(keszlet_nev)
        self._mappak: dict[Path, IniDocument | None] = {}

    def _dokumentum(self, mappa: Path) -> IniDocument | None:
        if mappa not in self._mappak:
            self._mappak[mappa] = self._betolt(mappa)
        return self._mappak[mappa]

    @staticmethod
    def _betolt(mappa: Path) -> IniDocument | None:
        cel = _iras_celja(mappa)
        if cel is None or ini_source_path(cel) is None:
            return None
        try:
            return load_document(cel)
        except OSError as hiba:
            # olvashatatlan ini: a döntés a nyilvántartásra esik vissza
            _log.warning("a(z) %s nem olvasható a mentés tervezésekor: %s", cel, hiba)
            return None

    def belyeg(self, fajl: Path) -> Belyeg | None:
        """A fájl két kulcsa; `None`, ha nincs ini, amiből dönteni lehetne.

        Ini van, de a fájlnak nincs szakasza: két nulla (soha nem mentett)."""
        dokumentum = self._dokumentum(fajl.parent)
        if dokumentum is None:
            return None
        szakasz = dokumentum.section(fajl.name)
        if szakasz is None:
            return Belyeg(SOHA_NEM_MENTETT, SOHA_NEM_MENTETT)
        return Belyeg(
            sima=_ertek(szakasz.get(_SIMA_KULCS)),
            keszlet=_ertek(szakasz.get(self._kulcs)),
        )


def mentendo(
    belyeg: Belyeg | None, *, nyilvantartva_valtozatlanul: bool, nyilvantartva: bool
) -> bool | None:
    """A bélyegből hozott döntés: `True` mentendő, `False` kihagyandó,
    `None` ha a bélyeg nem dönt (nincs ini), és a nyilvántartás marad.

    `nyilvantartva_valtozatlanul`: a nyilvántartásban van, és a méret/mtime
    egyezik. `nyilvantartva`: a nyilvántartásban van egyáltalán."""
    if belyeg is None:
        return None
    if belyeg.keszlet == SOSEM_MENTENDO:
        return False
    if belyeg.keszlet == SOHA_NEM_MENTETT:
        # Az eredetiben ez mindig mentendő. Nálunk a nyilvántartás ELŐTTI
        # változat nem írt bélyeget: a szerkesztetlen (sima kulcs nélküli),
        # változatlanul nyilvántartott kép már el van mentve. Ha a sima
        # kulcs megvan, nem tudható, a mentés előtt vagy után szerkesztették.
        return not (nyilvantartva_valtozatlanul and belyeg.sima == SOHA_NEM_MENTETT)
    if belyeg.keszlet != belyeg.sima:
        return True
    # naprakész a bélyeg szerint; a kívülről módosított fájlt a
    # (méret, mtime) még elkapja, ahogy a nyilvántartás szerint is
    return nyilvantartva and not nyilvantartva_valtozatlanul


def _ervenyes(lenyomat: int) -> int:
    """Az új bélyeg nem lehet 0 és 0xFFFF: azok különleges jelentésűek."""
    return 1 if lenyomat in (SOHA_NEM_MENTETT, SOSEM_MENTENDO) else lenyomat


def _belyegezve(
    dokumentum: IniDocument, fajl_nev: str, kulcs: str, mikor: datetime
) -> IniDocument:
    szakasz = dokumentum.section(fajl_nev)
    sima = _ertek(None if szakasz is None else szakasz.get(_SIMA_KULCS))
    if sima in (SOHA_NEM_MENTETT, SOSEM_MENTENDO):
        sima = _ervenyes(backuphash_for_local_datetime(mikor))
        dokumentum = dokumentum.with_value(fajl_nev, _SIMA_KULCS, str(sima))
    return dokumentum.with_value(fajl_nev, kulcs, str(sima))


def belyegezd(
    keszlet_nev: str,
    forrasok: Iterable[Path],
    *,
    most: datetime | None = None,
) -> None:
    """A sikeresen mentett fájlok szakaszába a készlet-bélyeg (`0x00429cf0`).

    A sima `backuphash` marad, ha van; hiányzó vagy 0 esetén új bélyeg
    készül az aktuális időből (#5810 képlet), és a készletkulcs UGYANAZT az
    értéket kapja. Mappánként egy írás; a hibás mappa nem állítja meg a
    többit (írásvédett forrás, hálózati megosztás): a naplóba kerül, és a
    fájl a nyilvántartás döntésére esik vissza."""
    kulcs = keszlet_kulcs(keszlet_nev)
    mikor = datetime.now() if most is None else most
    mappankent: dict[Path, list[str]] = {}
    for forras in forrasok:
        mappankent.setdefault(Path(forras).parent, []).append(Path(forras).name)
    for mappa, nevek in sorted(mappankent.items()):
        cel = _iras_celja(mappa)
        if cel is None:
            continue

        def _mutalj(dokumentum: IniDocument, nevek=nevek) -> IniDocument:
            for nev in nevek:
                dokumentum = _belyegezve(dokumentum, nev, kulcs, mikor)
            return dokumentum

        try:
            # `backup=False`: gépi könyvelés, mappánként egy `.bak` zaj lenne.
            # `touch=False`: a bélyeg nem szerkesztés, a képfájl mtime-ja a
            # nyilvántartás döntésének része, és az eredeti képet sem írjuk át
            update_document(cel, _mutalj, backup=False, touch=False)
        except (OSError, IniSaveError, IniConflictError) as hiba:
            _log.warning("a mentési bélyeg nem írható a(z) %s fájlba: %s", cel, hiba)


def nevezd_at_a_belyegeket(
    forrasok: Iterable[Path], regi_nev: str, uj_nev: str
) -> None:
    """A készlet átnevezése: a régi nevű kulcs minden képszakaszban az új
    nevűvé válik (`0x00473fd5`, `0x0047402f`), értéke változatlan.

    Csak azokat a mappákat érinti, amelyeket a készlet mentett (a
    nyilvántartás forrásai)."""
    regi_kulcs, uj_kulcs = keszlet_kulcs(regi_nev), keszlet_kulcs(uj_nev)
    if regi_kulcs == uj_kulcs:
        return
    mappak = sorted({Path(forras).parent for forras in forrasok})
    for mappa in mappak:
        cel = _iras_celja(mappa)
        if cel is None or ini_source_path(cel) is None:
            continue
        try:
            update_document(
                cel,
                lambda dokumentum: _atnevezve(dokumentum, regi_kulcs, uj_kulcs),
                backup=False,
                touch=False,
            )
        except (OSError, IniSaveError, IniConflictError) as hiba:
            _log.warning("a mentési bélyeg nem nevezhető át a(z) %s fájlban: %s", cel, hiba)


def _atnevezve(dokumentum: IniDocument, regi_kulcs: str, uj_kulcs: str) -> IniDocument:
    for szakasz in dokumentum.file_sections():
        ertek = szakasz.get(regi_kulcs)
        if ertek is None:
            continue
        # előbb az új, aztán a régi törlése: a szakasz közben sosem ürül ki
        dokumentum = dokumentum.with_value(szakasz.name, uj_kulcs, ertek)
        dokumentum = dokumentum.with_removed(szakasz.name, regi_kulcs)
    return dokumentum
