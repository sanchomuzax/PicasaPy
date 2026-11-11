"""A paritás-felvevő lépéssora: JSON bemenet, ellenőrzött lépésekké alakítva (#6845).

A lépésfajták az eredeti Picasát vezérlő Colab-végrehajtó szókincsét követik
(kijelölés, ctrl-/shift-kattintás, jobb klikk, menüpont, gépelés, billentyű,
várakozás), de koordináta helyett rácsindexet és objectName-et használnak:

    {"kijelol": <rácsindex>}
    {"kijelol_mod": [<rácsindex>, "ctrl"|"shift"]}
    {"jobbklikk": <rácsindex>}
    {"jobbklikk_mappa": "<mappanév>"}
    {"menupont": "<objectName>"}
    {"fomenu": "<menü>", "menupont": "<tétel objectName>"}
    {"gepel": "<szöveg>"}
    {"billentyu": "Return"|"Escape"|"ctrl+a"|...}
    {"var": <másodperc>}

Az értelmező Qt nélkül fut: az érvénytelen lépés a felvétel indulása ELŐTT
érthető hibát ad, a lépés sorszámával.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LEPESFAJTAK = (
    "kijelol",
    "kijelol_mod",
    "jobbklikk",
    "jobbklikk_mappa",
    "menupont",
    "gepel",
    "billentyu",
    "var",
)
MODOSITOK = ("ctrl", "shift")
MAX_VARAKOZAS_MP = 600.0
MAX_SZOVEG_HOSSZ = 2000

_BILLENTYU_MODOSITOK = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "shift": "shift",
    "alt": "alt",
    "meta": "meta",
}
_MODOSITO_SORREND = ("ctrl", "shift", "alt", "meta")
_BILLENTYU_ALIASOK = {
    "enter": "return",
    "esc": "escape",
    "del": "delete",
    "pgup": "pageup",
    "pgdn": "pagedown",
    "ins": "insert",
}
_NEVES_BILLENTYUK = frozenset(
    {
        "return",
        "escape",
        "tab",
        "backtab",
        "backspace",
        "delete",
        "insert",
        "space",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
        "pageup",
        "pagedown",
    }
)
_FUNKCIOBILLENTYUK = frozenset(f"f{szam}" for szam in range(1, 13))
_EGY_KARAKTERES = frozenset("abcdefghijklmnopqrstuvwxyz0123456789")


class LepesHiba(ValueError):
    """Érvénytelen lépéssor vagy lépés; az üzenet a felhasználónak szól."""


@dataclass(frozen=True)
class Lepes:
    """Egy ellenőrzött lépés; csak a fajtájához tartozó mezők kitöltöttek."""

    fajta: str
    eredeti: str
    racsindex: int | None = None
    modosito: str | None = None
    mappanev: str | None = None
    objektumnev: str | None = None
    fomenu: str | None = None
    szoveg: str | None = None
    billentyu: str | None = None
    masodperc: float | None = None


def betolt(forras: str) -> tuple[Lepes, ...]:
    """A lépéssort JSON-szövegből vagy JSON-fájlból olvassa be."""
    szoveg = forras.strip()
    if not szoveg.startswith(("[", "{")):
        fajl = Path(forras)
        if not fajl.is_file():
            raise LepesHiba(
                f"Nincs ilyen lépéssor-fájl, és a bemenet nem JSON: {forras}"
            )
        try:
            szoveg = fajl.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as hiba:
            raise LepesHiba(f"A lépéssor-fájl nem olvasható: {forras} ({hiba})") from hiba
    try:
        adat = json.loads(szoveg)
    except json.JSONDecodeError as hiba:
        raise LepesHiba(f"A lépéssor érvénytelen JSON: {hiba}") from hiba
    return ertelmez(adat)


def ertelmez(adat: object) -> tuple[Lepes, ...]:
    """A betöltött JSON-értéket lépések sorává alakítja, vagy `LepesHiba`-t dob."""
    if not isinstance(adat, Sequence) or isinstance(adat, (str, bytes)):
        raise LepesHiba("A lépéssor legyen JSON-lista (a lépések tömbje).")
    if not adat:
        raise LepesHiba("A lépéssor üres: legalább egy lépés kell.")
    return tuple(_lepes(sorszam, nyers) for sorszam, nyers in enumerate(adat, start=1))


def _hiba(sorszam: int, uzenet: str) -> LepesHiba:
    return LepesHiba(f"A {sorszam}. lépés érvénytelen: {uzenet}")


def _lepes(sorszam: int, nyers: object) -> Lepes:
    if not isinstance(nyers, dict):
        raise _hiba(sorszam, "a lépés JSON-objektum legyen, pl. {\"kijelol\": 3}.")
    kulcsok = [kulcs for kulcs in nyers if kulcs != "fomenu"]
    ismeretlenek = [kulcs for kulcs in kulcsok if kulcs not in LEPESFAJTAK]
    if ismeretlenek:
        raise _hiba(
            sorszam,
            f"ismeretlen lépésfajta: {ismeretlenek[0]!r}. "
            f"Érvényes fajták: {', '.join(LEPESFAJTAK)}.",
        )
    if not kulcsok and "fomenu" in nyers:
        raise _hiba(sorszam, "a fomenu csak a menupont mellett állhat.")
    if len(kulcsok) != 1:
        raise _hiba(
            sorszam,
            "egy lépés egyetlen fajtát tartalmazhat "
            f"(talált: {', '.join(kulcsok) or 'semmit'}).",
        )
    fajta = kulcsok[0]
    if "fomenu" in nyers and fajta != "menupont":
        raise _hiba(sorszam, "a fomenu csak a menupont mellett állhat.")
    eredeti = json.dumps(nyers, ensure_ascii=False, sort_keys=True)
    return _mezok(sorszam, fajta, nyers, eredeti)


def _mezok(sorszam: int, fajta: str, nyers: dict[str, Any], eredeti: str) -> Lepes:
    ertek = nyers[fajta]
    if fajta in ("kijelol", "jobbklikk"):
        return Lepes(fajta, eredeti, racsindex=_index(sorszam, fajta, ertek))
    if fajta == "kijelol_mod":
        return _kijelol_mod(sorszam, ertek, eredeti)
    if fajta == "jobbklikk_mappa":
        return Lepes(fajta, eredeti, mappanev=_szoveg(sorszam, fajta, ertek))
    if fajta == "menupont":
        fomenu = None
        if "fomenu" in nyers:
            fomenu = _szoveg(sorszam, "fomenu", nyers["fomenu"])
        return Lepes(
            fajta,
            eredeti,
            objektumnev=_szoveg(sorszam, fajta, ertek),
            fomenu=fomenu,
        )
    if fajta == "gepel":
        return Lepes(fajta, eredeti, szoveg=_gepelt_szoveg(sorszam, ertek))
    if fajta == "billentyu":
        return Lepes(fajta, eredeti, billentyu=_billentyu(sorszam, ertek))
    return Lepes(fajta, eredeti, masodperc=_masodperc(sorszam, ertek))


def _index(sorszam: int, mezo: str, ertek: object) -> int:
    if isinstance(ertek, bool) or not isinstance(ertek, int) or ertek < 0:
        raise _hiba(
            sorszam,
            f"a {mezo} értéke nemnegatív egész rácsindex legyen (kapott: {ertek!r}).",
        )
    return ertek


def _kijelol_mod(sorszam: int, ertek: object, eredeti: str) -> Lepes:
    if not isinstance(ertek, (list, tuple)) or len(ertek) != 2:
        raise _hiba(
            sorszam,
            'a kijelol_mod értéke [rácsindex, "ctrl"|"shift"] legyen '
            f"(kapott: {ertek!r}).",
        )
    index = _index(sorszam, "kijelol_mod", ertek[0])
    modosito = ertek[1].strip().lower() if isinstance(ertek[1], str) else None
    if modosito not in MODOSITOK:
        raise _hiba(
            sorszam,
            f"a kijelol_mod módosítója {' vagy '.join(MODOSITOK)} lehet "
            f"(kapott: {ertek[1]!r}).",
        )
    return Lepes("kijelol_mod", eredeti, racsindex=index, modosito=modosito)


def _szoveg(sorszam: int, mezo: str, ertek: object) -> str:
    if not isinstance(ertek, str) or not ertek.strip():
        raise _hiba(
            sorszam, f"a {mezo} értéke nem üres szöveg legyen (kapott: {ertek!r})."
        )
    return ertek.strip()


def _gepelt_szoveg(sorszam: int, ertek: object) -> str:
    # A gépelt szöveg szóközei és sorvégei jelentésesek: nem vágjuk le.
    if not isinstance(ertek, str) or not ertek:
        raise _hiba(sorszam, f"a gepel értéke nem üres szöveg legyen (kapott: {ertek!r}).")
    if len(ertek) > MAX_SZOVEG_HOSSZ:
        raise _hiba(sorszam, f"a gepel szövege legfeljebb {MAX_SZOVEG_HOSSZ} karakter.")
    return ertek


def _billentyu(sorszam: int, ertek: object) -> str:
    """Egységes alak: kisbetűs, rögzített módosító-sorrendű `ctrl+shift+o`."""
    if not isinstance(ertek, str) or not ertek.strip():
        raise _hiba(
            sorszam, f"a billentyu értéke nem üres szöveg legyen (kapott: {ertek!r})."
        )
    tagok = [tag.strip().lower() for tag in ertek.strip().split("+")]
    modositok = set()
    for tag in tagok[:-1]:
        modosito = _BILLENTYU_MODOSITOK.get(tag)
        if modosito is None:
            raise _hiba(
                sorszam,
                f"a billentyu {ertek!r} alakjában ismeretlen módosító: {tag!r} "
                f"(ctrl, shift, alt, meta).",
            )
        modositok.add(modosito)
    gomb = _BILLENTYU_ALIASOK.get(tagok[-1], tagok[-1])
    if not (
        gomb in _NEVES_BILLENTYUK
        or gomb in _FUNKCIOBILLENTYUK
        or gomb in _EGY_KARAKTERES
    ):
        raise _hiba(
            sorszam,
            f"a billentyu {ertek!r} alakjában ismeretlen billentyű: {tagok[-1]!r}. "
            "Elfogadott: betű, számjegy, F1-F12, Return, Escape, Tab, Backspace, "
            "Delete, Space, nyilak, Home, End, PageUp, PageDown.",
        )
    rendezett = [mod for mod in _MODOSITO_SORREND if mod in modositok]
    return "+".join([*rendezett, gomb])


def _masodperc(sorszam: int, ertek: object) -> float:
    if (
        isinstance(ertek, bool)
        or not isinstance(ertek, (int, float))
        or not math.isfinite(ertek)
        or ertek < 0
        or ertek > MAX_VARAKOZAS_MP
    ):
        raise _hiba(
            sorszam,
            f"a var értéke 0 és {MAX_VARAKOZAS_MP:g} közötti másodperc legyen "
            f"(kapott: {ertek!r}).",
        )
    return float(ertek)
