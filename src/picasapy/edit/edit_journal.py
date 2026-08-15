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
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini.filters import parse_filters


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


def record_saved_chain(
    journal: dict[str, JournalEntry],
    path: str,
    chain: str,
    *,
    saved_at: str,
) -> dict[str, JournalEntry]:
    """A most kiírt lánc felvétele a naplóba (immutábilis: új szótár).

    **Üres lánc törli a bejegyzést:** ha a felhasználó maga vonta vissza az
    összes szerkesztést, nincs mit védeni — különben egy szándékos törlésre
    is riasztanánk.
    """
    path = naplo_kulcs(path)
    frissitett = dict(journal)
    if not chain.strip():
        frissitett.pop(path, None)
        return frissitett
    frissitett[path] = JournalEntry(path=path, chain=chain, saved_at=saved_at)
    return frissitett


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
    """A napló kiírása (a könyvtárat is létrehozva)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                kulcs: {"chain": entry.chain, "saved_at": entry.saved_at}
                for kulcs, entry in sorted(journal.items())
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )


__all__ = [
    "JournalEntry",
    "detect_lost_edits",
    "load_journal",
    "record_saved_chain",
    "save_journal",
]
