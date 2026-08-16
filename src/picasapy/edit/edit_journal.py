"""Szerkesztés-napló: a saját `filters=` írásaink tartós nyilvántartása (#644).

**Miért kell.** A `.picasa.ini` a projekt igazságforrása, és a szerkesztési
lánc MÁS SEHOL nem él. A párhuzamosan futó eredeti Picasa viszont nem
kulcsonként fésül: a fotó rekordját a saját adatbázisából írja ki egészben,
és amit a rekordja nem tartalmaz — a mi láncunkat —, azt elhagyja. A
felhasználó munkája így **figyelmeztetés nélkül megsemmisül**, a belőle épülő
visszavonás-veremmel együtt.

A napló ezt nem akadályozza meg (azt csak a #643 megoldása tudná), de három
dolgot lehetővé tesz:

1. **észlelés** — látjuk, hogy a láncunk eltűnt, nem csak elszenvedjük;
2. **figyelmeztetés** — meg tudjuk mondani, MELYIK kép szerkesztése veszett;
3. **helyreállítás** — a lánc visszaírható.

**A napló nem a fotó mappájába ír.** Egy külső program azt is felülírhatja —
a `.picasa.ini.bak` épp ezért nem elég: az a MI írásunk előtti állapot, és a
következő mentésünk felülírja.

Ez a modul tiszta függvényeket és egy egyszerű JSON-tárolót ad; hogy mikor
fut az észlelés, az a hívóé.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini.filters import parse_filters
from picasapy.ioutil import write_atomic


def naplo_kulcs(path: str | Path) -> str:
    """A napló EGYETLEN kulcsképzési szabálya (#699).

    Az író (`record_saved_chain`) és az olvasó oldal (`detect_lost_edits`,
    a vezérlő `full_path()`-a) ugyanezt hívja. Ha a két oldal máshogy
    képezné, a `detect_lost_edits` **némán soha nem találna egyezést**, és a
    védelem csendben hatástalan maradna — ami rosszabb, mint egy hangos hiba.

    Windowson ez nem elméleti: a `full_path()` visszaperjelre normalizál
    (`\\k\\a.jpg`), miközben a mentési út előreperjeles alakot adhat át
    (`/k/a.jpg`). A `Path` normalizálása a két alakot azonosra hozza — ezt a
    windows-CI-láb fogta meg (#699 utókövetés).
    """
    return str(Path(path))


@dataclass(frozen=True)
class JournalEntry:
    """Egy kép utoljára ÁLTALUNK mentett szerkesztési lánca."""

    #: a kép abszolút útvonala
    path: str
    #: a `filters=` érték, ahogy kiírtuk
    chain: str
    #: ISO-időbélyeg — a hívó adja (a modul nem olvas órát, hogy tesztelhető
    #: maradjon)
    saved_at: str


def record_saved_chains(
    journal: dict[str, JournalEntry],
    items: "Iterable[tuple[str, str]]",
    *,
    saved_at: str,
) -> dict[str, JournalEntry]:
    """Több kép láncának felvétele EGY menetben (immutábilis: új szótár).

    #750: a csoportos effekt és a kötegelt beillesztés több száz képet ír
    egyszerre. Ha a napló képenként töltődne be és íródna ki, a védelem a
    köteg szűk keresztmetszete lenne (N teljes JSON-olvasás + -írás). Ez a
    függvény a KÖTEG egészét egyetlen szótár-másolaton vezeti át; a hívó
    egyszer olvas és egyszer ír.

    Args:
        items: `(útvonal, lánc)` párok. Ugyanarra az útvonalra több pár is
            jöhet — a KÉSŐBBI nyer, ahogy az egyenkénti hívásoknál is.
        saved_at: közös időbélyeg (a modul nem olvas órát, ld. `JournalEntry`).

    **Üres lánc törli a bejegyzést:** ha a felhasználó maga vonta vissza az
    összes szerkesztést, nincs mit védeni — különben egy szándékos törlésre
    is riasztanánk.
    """
    frissitett = dict(journal)
    for path, chain in items:
        kulcs = naplo_kulcs(path)
        if not (chain or "").strip():
            frissitett.pop(kulcs, None)
            continue
        frissitett[kulcs] = JournalEntry(
            path=kulcs, chain=chain, saved_at=saved_at
        )
    return frissitett


def record_saved_chain(
    journal: dict[str, JournalEntry],
    path: str,
    chain: str,
    *,
    saved_at: str,
) -> dict[str, JournalEntry]:
    """A most kiírt lánc felvétele a naplóba (immutábilis: új szótár).

    Az egy-elemű eset a `record_saved_chains`-re megy vissza, hogy a
    kulcsképzés és az „üres lánc = törlés" szabály EGY helyen éljen — két
    változat előbb-utóbb szétcsúszna, és a #699 tanulsága szerint az ilyen
    csúszás NÉMÁN üti ki a védelmet.
    """
    return record_saved_chains(journal, ((path, chain),), saved_at=saved_at)


def _op_kulcsok(chain: str) -> set[tuple[str, tuple[str, ...]]]:
    """A lánc műveletei összehasonlítható alakban.

    Halmazként nézzük, mert a Picasa a saját rekordjából MÁS SORRENDBEN is
    kiírhatja a láncot — attól a mi effektünk még megvan.
    """
    if not chain.strip():
        return set()
    return {(op.name.casefold(), op.params) for op in parse_filters(chain)}


def detect_lost_edits(
    journal: dict[str, JournalEntry], current_chains: dict[str, str]
) -> tuple[JournalEntry, ...]:
    """A naplózott láncok közül melyik veszett el a mostani ini-állapotban.

    Args:
        journal: a naplónk.
        current_chains: a MOST beolvasott `filters=` értékek képenként. Csak
            az itt szereplő képekről nyilatkozunk — egy be nem olvasott mappa
            nem jelent veszteséget.

    Veszteség akkor van, ha a naplózott lánc **bármelyik** művelete hiányzik
    a mostaniból. A hozzáfűzés NEM veszteség: ha a Picasa a mi láncunk MELLÉ
    írt, a miénk megvan, és a jegy kikötése szerint az ilyen — minket nem
    érintő — változás nem zajonghat.

    A találatok útvonal szerint rendezettek, hogy a felhasználónak mutatott
    lista ne ugráljon futásonként.
    """
    veszteseg = []
    for path, entry in journal.items():
        if path not in current_chains:
            continue
        sajat = _op_kulcsok(entry.chain)
        if not sajat:
            continue
        if not sajat.issubset(_op_kulcsok(current_chains[path])):
            veszteseg.append(entry)
    return tuple(sorted(veszteseg, key=lambda e: e.path))


def load_journal(path: str | Path) -> dict[str, JournalEntry]:
    """A napló betöltése; hiányzó vagy sérült fájlnál üres napló.

    Egy sérült napló nem omlaszthatja el a programot — legfeljebb a védelmet
    veszítjük el, a fotókat nem.
    """
    target = Path(path)
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    eredmeny: dict[str, JournalEntry] = {}
    for kulcs, ertek in raw.items():
        if not isinstance(kulcs, str) or not isinstance(ertek, dict):
            continue
        chain = ertek.get("chain")
        saved_at = ertek.get("saved_at")
        if not isinstance(chain, str) or not isinstance(saved_at, str):
            continue
        eredmeny[kulcs] = JournalEntry(path=kulcs, chain=chain, saved_at=saved_at)
    return eredmeny


def save_journal(journal: dict[str, JournalEntry], path: str | Path) -> None:
    """A napló ATOMIKUS kiírása (a könyvtárat is létrehozva).

    #750: a naplót mostantól HÁTTÉRSZÁL is írja (a csoportos effekt), miközben
    a GUI-szál olvashatja (`_check_external_overwrites`). A korábbi
    `write_text` a célfájlt csonkolva kezdte írni, tehát az olvasó egy
    félkész JSON-t is elkaphatott volna — a `load_journal` az ilyet
    (helyesen) üres naplónak veszi, vagyis a védelem CSENDBEN elveszne.
    A temp fájl + csere ezt a rést zárja: az olvasó vagy a régi, vagy az új
    teljes tartalmat látja.
    """
    target = Path(path)
    payload = json.dumps(
        {
            kulcs: {"chain": entry.chain, "saved_at": entry.saved_at}
            for kulcs, entry in sorted(journal.items())
        },
        ensure_ascii=False,
        indent=1,
    )
    write_atomic(target, payload.encode("utf-8"), make_parents=True)


__all__ = [
    "JournalEntry",
    "detect_lost_edits",
    "load_journal",
    "naplo_kulcs",
    "record_saved_chain",
    "record_saved_chains",
    "save_journal",
]
