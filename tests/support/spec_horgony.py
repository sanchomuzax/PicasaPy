"""A spec-lapok horgony-előírásának (22.4) ellenőrzése — a #2182 őre.

⚠️ **Ez a modul a privát mérő VISELKEDÉSÉT tükrözi**, nem egy önálló ízlést.
A `picasapy-agent` repó `eszkozok/ui_lefedettseg.py`-ja szakaszonként keres
bizonyítékot, és horgony nélkül a **teljes szakaszt** átugorja. Az őr állítása
ezért így hangzik: *ezt a szakaszt a mérő át fogja ugrani, tehát az itt leírt
elemek »feltáratlan«-ként fognak a kutatói körök munkalistájára kerülni.*

Ebből következik, hogy a lenti minták és a szakaszolás **nem térhetnek el** a
mérőétől. Ha ott változnak, itt is át kell vezetni — a két helyet a
`docs/specs/binaris-regeszet-modszertan.md` 22.4–22.5 köti össze. A mérő a
privát repóban él, ezért nem importálható; a másolás tudatos, és ezek a
tesztek cserébe semmit nem igényelnek a privát repóból.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[2]
SPEC_DIR = GYOKER / "docs" / "specs"
MEGFELELTETES = SPEC_DIR / "ui-lefedettseg-megfeleltetes.csv"
ISMERT_UT = Path(__file__).with_name("spec_horgony_ismert_sertesek.json")

#: A mérő mintái, szó szerint. A `0x00…` szűkítés SZÁNDÉKOS: a Picasa kódcímei
#: `0x00xxxxxx` alakúak, az ARGB színkonstansok `0xFF…`/`0xAA…` — egy szín ne
#: igazoljon semmit. (A mérő saját megjegyzése ugyanezt mondja.)
CIM_MINTA = re.compile(r"0x00[0-9A-Fa-f]{6}\b")
FAJL_SOR_MINTA = re.compile(r"[\w./-]+\.(?:py|qml|cpp|h|tre|yt|ini)\s*:\s*\d+")

#: Generált lapok: nem a spec-író írja őket, a 22.4 rájuk értelmetlen.
GENERALT_LAPOK = frozenset({"ui-lefedettseg.md", "menu-lefedettseg.md"})


@dataclass(frozen=True)
class Sertes:
    """Egy szakasz, amely elemet dokumentál, de a mérő át fogja ugrani."""

    lap: str
    cim: str
    elemek: tuple[str, ...]

    def kulcs(self) -> tuple[str, str]:
        return (self.lap, self.cim)


def panelnevek(ut: Path | None = None) -> frozenset[str]:
    """A 74 ismert panelnév a publikus megfeleltetés-táblából.

    Miért innen, és nem mintából: a puszta `szó/szó` alak ártatlan
    útvonalakra is illeszkedne (`docs/specs`, `src/picasapy`). A panelnév
    ismerete teszi a felismerést pontossá — és a tábla épségét amúgy is
    őrzi a #707 tesztje.
    """
    cel = ut or MEGFELELTETES
    with cel.open(encoding="utf-8", newline="") as fh:
        return frozenset(s["panel"] for s in csv.DictReader(fh) if s["panel"])


def szakaszok(szoveg: str) -> list[str]:
    """Markdown-címsorok mentén szakaszol — a mérővel AZONOS módon.

    A `#`-kezdetű sor akkor is új szakaszt nyit, ha kódblokkban áll. Ez a
    mérő viselkedése, és itt épp ezért helyes: az őr azt jelzi előre, hol
    fog a mérő szakaszhatárt látni.
    """
    darabok: list[str] = []
    aktualis: list[str] = []
    for sor in szoveg.splitlines():
        if sor.startswith("#"):
            if aktualis:
                darabok.append("\n".join(aktualis))
            aktualis = [sor]
        else:
            aktualis.append(sor)
    if aktualis:
        darabok.append("\n".join(aktualis))
    return darabok


def _elem_minta(panelek: frozenset[str] | set[str]) -> re.Pattern[str]:
    return re.compile(r"\b(?:%s)/[A-Za-z0-9_]+" % "|".join(map(re.escape, sorted(panelek))))


def _tablasor(sor: str) -> bool:
    """Igaz a tábla ADATSORAIRA (a fejléc-elválasztó `|---|` nem az)."""
    csupasz = sor.strip()
    return (
        csupasz.startswith("|")
        and csupasz.endswith("|")
        and bool(set(csupasz) - set("|-: "))
    )


def horgony_van(szakasz: str) -> bool:
    return bool(CIM_MINTA.search(szakasz) or FAJL_SOR_MINTA.search(szakasz))


def sertesek(spec_dir: Path, panelek: frozenset[str] | set[str]) -> list[Sertes]:
    """Horgony nélküli szakaszok, amelyek TÁBLÁBAN dokumentálnak elemet.

    A táblasorra szűkítés hatókör-döntés, nem kényelem: a 22.4 harmadik
    pontja épp a táblába sorolt vezérlőkről szól, és a mért kár is
    elemtáblákban keletkezett. A folyó szövegben említett elemnév nem
    dokumentáció — az őrizetlenül hagyása tudatos (a különbség mérve:
    150 szakasz 40 lapon a tág, 58 szakasz 30 lapon a szűk olvasat).
    """
    minta = _elem_minta(panelek)
    talalt: list[Sertes] = []
    for lap in sorted(spec_dir.glob("*.md")):
        if lap.name in GENERALT_LAPOK:
            continue
        for szakasz in szakaszok(lap.read_text(encoding="utf-8")):
            elemek = sorted({m.group(0) for sor in szakasz.splitlines() if _tablasor(sor)
                             for m in minta.finditer(sor)})
            if not elemek or horgony_van(szakasz):
                continue
            sorok = szakasz.splitlines()
            talalt.append(Sertes(lap.name, sorok[0].strip(), tuple(elemek)))
    return talalt


def ismert_sertesek(ut: Path | None = None) -> frozenset[tuple[str, str]]:
    """A bevezetéskor már fennálló, jegyre kötött sértések kulcsai."""
    cel = ut or ISMERT_UT
    if not cel.exists():
        return frozenset()
    try:
        adat = json.loads(cel.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as hiba:
        raise ValueError(f"az ismert-sértés lista nem olvasható: {cel}") from hiba
    return frozenset((b["lap"], b["cim"]) for b in adat.get("sertesek", []))


def jelentes(tetelek: list[Sertes]) -> str:
    """Emberi olvasásra: MELYIK lap MELYIK szakasza, és mi vész el benne."""
    if not tetelek:
        return "nincs horgony nélküli elemtábla"
    sorok = []
    for s in sorted(tetelek, key=lambda t: (t.lap, t.cim)):
        mit = ", ".join(s.elemek[:4]) + ("…" if len(s.elemek) > 4 else "")
        sorok.append(f"  {s.lap} :: {s.cim}\n      {len(s.elemek)} elem: {mit}")
    sorok.append(
        "\n  Javítás: tedd a szakaszba a bizonyíték horgonyát — `0x00…` kódcímet"
        "\n  vagy `fájl.tre:sor` / `respack.yt:sor` hivatkozást (22.4)."
    )
    return "\n".join(sorok)
