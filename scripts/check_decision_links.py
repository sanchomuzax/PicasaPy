#!/usr/bin/env python3
"""A döntés ↔ kód kötés kétirányú őre — #1623.

**A hibaosztály.** A `docs/decisions/` lapjai NORMATÍV döntéseket rögzítenek
(mit határoztunk el), a `src/` pedig megvalósítja őket. A kettő között ma
semmi kötés nincs, és a döntés **csendben elmozdulhat a kód alól**. Két
megtörtént esetünk van rá:

- **#650** — a fájl saját kommentje leírta a helyes viselkedést, a kód nem
  valósította meg, és az átnézés a kommentet olvasta;
- **#616 ↔ #422** — egy javítás visszahozta a kifejezetten ELVETETT
  görgethető keretet, mert senki nem tudott a #422-ről; a tesztje ráadásul a
  HIBÁT rögzítette szerződésként.

Ez a szkript a `scripts/check_protected_features.py` általánosítása: ott a
`SAJÁT FUNKCIÓ` jelölés jegyzéke és a kód van kétirányban összevetve, itt a
döntési lapok `## Kötés` szakasza és a fa.

**Négy ellenőrzés:**

1. *minden lapnak van kötése* — a `## Kötés` szakasz megléte és a három mező
   (`Státusz`, `Megvalósítja`, `Őrzi`) kitöltöttsége;
2. *jegyzék → valóság* — a `Megvalósítja`/`Őrzi` alatt megnevezett útvonal
   létezik. Az elárvult hivatkozás hamis biztonságérzetet ad;
3. *valóság → jegyzék* — a fában hivatkozott `docs/decisions/*.md` létezik;
4. *a #616-osztály* — `VISSZAVONVA` státuszú döntéshez **nem tartozhat** élő
   `Megvalósítja`. Ha mégis, egy elvetett döntés tért vissza a kódba.

**Amit szándékosan NEM ellenőrzünk — szemantikai megfelelést.** Hogy a
megnevezett modul TÉNYLEG azt csinálja-e, amit a döntés mond, se generálni,
se kézzel vezetni nem lehet megbízhatóan; a #650 épp azt mutatja, hogy a
szöveges állítás eltérhet a kódtól. Ez az őr **jelölt éleket** ellenőriz,
nem garanciát ad.

**A `tests/` a 3. irányból KI VAN VÉVE.** A tesztek jogosan tartalmaznak
kitalált fájlneveket paraméterlistákban — a
`tests/scripts/test_kiadas_szukseges_1319.py:58` például egy nem létező
`docs/decisions/0012-valami.md`-t ad át mintaadatként. Ezt leletnek venni
hamis pozitív lenne.

Használat::

    python scripts/check_decision_links.py

Kilépési kód: 0 ha nincs eltérés, 1 ha van, 2 ha a bemenet hibás.
"""
from __future__ import annotations

import pathlib
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

#: A döntési lapok mappája — a normatív döntések egyetlen helye.
_DONTESEK = "docs/decisions"

#: A 3. irányban átvizsgált fák. A `tests/` KIMARAD (ld. a docstringet).
_FORRAS_FAK = ("src", "scripts", "docs")

#: Ezek a fájlok A KONVENCIÓRÓL beszélnek példákkal, nem egy konkrét döntésre
#: hivatkoznak — ugyanaz a kivétel, mint a `check_protected_features.py`
#: `EXCLUDED` listája. Kihagyásuk nélkül az őr a saját docstringjét jelezné.
_KIVETT = ("scripts/check_decision_links.py",
           "tests/tools/test_check_decision_links_1623.py")

#: Az élő és a visszavont döntés — a 4. ellenőrzés ezen a különbségen áll.
_ELO = "ELFOGADVA"
_VISSZAVONT = "VISSZAVONVA"
_STATUSZOK = (_ELO, _VISSZAVONT)

#: A „nincs ilyen” kitöltések. Ezek ÉRVÉNYES értékek: az információ, hogy egy
#: döntésnek nincs megvalósítása vagy nincs őre, önmagában is érték.
_NINCS = {"nincs megvalósítva", "nincs őr", "nincs"}

_KOTES_SZAKASZ = re.compile(r"^##\s+Kötés\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
_MEZO = re.compile(r"^[-*]\s*\*\*(Státusz|Megvalósítja|Őrzi):\*\*\s*(.+?)\s*$", re.M)
_UTVONAL = re.compile(r"`([^`]+)`")
_HIVATKOZAS = re.compile(r"docs/decisions/([A-Za-z0-9._-]+\.md)")


class Kotes:
    """Egy döntési lap gépi kötése."""

    def __init__(self, lap: str, statusz: str, megvalositja: list[str], orzi: list[str]):
        self.lap = lap
        self.statusz = statusz
        self.megvalositja = megvalositja
        self.orzi = orzi


def _mezok(szoveg: str) -> dict[str, str]:
    szakasz = _KOTES_SZAKASZ.search(szoveg)
    if not szakasz:
        return {}
    return {n: e for n, e in _MEZO.findall(szakasz.group(1))}


def _utvonalak(ertek: str) -> list[str]:
    """A backtickbe zárt útvonalak. A »nincs …« kitöltés üres listát ad."""
    if ertek.strip().lower() in _NINCS:
        return []
    return [u.strip() for u in _UTVONAL.findall(ertek)]


def olvas_kotesek(base: pathlib.Path) -> tuple[list[Kotes], list[str]]:
    """A lapok kötései, és a hiányzó/hibás kötések hibalistája."""
    mappa = base / _DONTESEK
    if not mappa.is_dir():
        raise FileNotFoundError(f"nincs döntési mappa: {mappa}")

    kotesek: list[Kotes] = []
    hibak: list[str] = []
    for lap in sorted(mappa.glob("*.md")):
        rel = lap.relative_to(base).as_posix()
        mezok = _mezok(lap.read_text(encoding="utf-8"))
        if not mezok:
            hibak.append(f"{rel}: hiányzik a `## Kötés` szakasz")
            continue
        hianyzo = [m for m in ("Státusz", "Megvalósítja", "Őrzi") if m not in mezok]
        if hianyzo:
            hibak.append(f"{rel}: hiányzó mező a kötésben: {', '.join(hianyzo)}")
            continue
        statusz = mezok["Státusz"].strip().strip("*").strip()
        if statusz not in _STATUSZOK:
            hibak.append(
                f"{rel}: ismeretlen státusz {statusz!r} "
                f"(csak {' vagy '.join(_STATUSZOK)} lehet)"
            )
            continue
        kotesek.append(
            Kotes(rel, statusz, _utvonalak(mezok["Megvalósítja"]), _utvonalak(mezok["Őrzi"]))
        )
    if not kotesek and not hibak:
        raise ValueError(f"egyetlen döntési lapot sem találtam itt: {mappa}")
    return kotesek, hibak


def ellenoriz(base: pathlib.Path = _REPO_ROOT) -> list[str]:
    """Mind a négy irány. Üres lista = nincs eltérés."""
    kotesek, hibak = olvas_kotesek(base)

    for k in kotesek:
        # 2. irány — a jegyzékben megnevezett útvonal létezik.
        for mezo, utak in (("Megvalósítja", k.megvalositja), ("Őrzi", k.orzi)):
            for ut in utak:
                if not (base / ut).exists():
                    hibak.append(f"{k.lap}: a(z) `{ut}` ({mezo}) nem létezik")

        # 4. irány — visszavont döntéshez nem tartozhat élő megvalósítás.
        if k.statusz == _VISSZAVONT and k.megvalositja:
            hibak.append(
                f"{k.lap}: VISSZAVONVA státusz, mégis van megvalósítása "
                f"({', '.join('`' + u + '`' for u in k.megvalositja)}) — "
                f"egy elvetett döntés tért vissza a kódba (#616-osztály)"
            )

    # 3. irány — a fában hivatkozott döntési lap létezik.
    letezo = {pathlib.Path(k.lap).name for k in kotesek}
    for fa in _FORRAS_FAK:
        gyoker = base / fa
        if not gyoker.is_dir():
            continue
        for fajl in gyoker.rglob("*"):
            if not fajl.is_file() or fajl.suffix.lower() in {".png", ".jpg", ".qm", ".zip"}:
                continue
            if fajl.relative_to(base).as_posix() in _KIVETT:
                continue
            try:
                szoveg = fajl.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for nev in set(_HIVATKOZAS.findall(szoveg)):
                if nev not in letezo and not (base / _DONTESEK / nev).exists():
                    hibak.append(
                        f"{fajl.relative_to(base).as_posix()}: hivatkozik a "
                        f"`{_DONTESEK}/{nev}`-re, ami nem létezik"
                    )
    return sorted(set(hibak))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    base = pathlib.Path(argv[0]) if argv else _REPO_ROOT
    try:
        hibak = ellenoriz(base)
    except (FileNotFoundError, ValueError) as hiba:
        print(f"az ellenőrzés nem futott le: {hiba}", file=sys.stderr)
        return 2

    if not hibak:
        print("Döntés ↔ kód kötés: rendben, nincs eltérés.")
        return 0
    print(f"Döntés ↔ kód kötés — {len(hibak)} eltérés:\n")
    for h in hibak:
        print(f"  {h}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
