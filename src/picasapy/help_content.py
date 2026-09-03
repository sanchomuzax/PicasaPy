"""A felhasználói súgó tartalmának elérése — net nélkül, telepítve is (#2054).

A súgó szövege a **csomagfa alatt** él (`src/picasapy/help/`), nem a
`docs/` alatt. Ez nem ízlés kérdése: a telepíthető csomagba kizárólag a
`src/picasapy` fa alól kerül be bármi

* `MANIFEST.in` — `graft src/picasapy`
* `pyproject.toml` — `[tool.setuptools.packages.find] where = ["src"]`

…tehát a `docs/help/` alatt hagyva a súgó **git-másolatból működne,
telepített csomagból nem**, és ez némán, csak a felhasználónál derülne
ki. Ugyanaz az osztály, ami a #646-ban 40 fájlt vitt el észrevétlenül
(forrásból minden működött, ezért hónapokig nem tűnt fel).

A `graft` miatt a mappa **magától** bekerül a csomagba, és a
`scripts/check_package_contents.py` őre azonnal jelez, ha kiesne — a
`.md` nem szerepel a kihagyott kiterjesztések közt.

## Amit ez a modul NEM csinál

Nem jelenít meg és nem formáz: nyers Markdown-szöveget ad vissza. A
megjelenítés a felület dolga.
"""

from __future__ import annotations

import re
from pathlib import Path

#: A súgó főoldala — a tartalomjegyzék.
FOOLDAL = "index.md"

#: Egy keresési találat körüli szövegkörnyezet fél-hossza karakterben.
_RESZLET_SUGAR = 60

#: A találatok felső korlátja. Egy gyakori szó (pl. „a") különben
#: több száz sort adna, és a lista használhatatlan lenne.
_MAX_TALALAT = 200

#: A rejtett, GÉPI állományok: a frissítő naplója és feladatlapja. Ezek
#: nem a felhasználónak szólnak, tehát a fejezetlistából kimaradnak.
_REJTETT_ELOTAG = "."


def sugo_mappa() -> Path:
    """A súgó mappája a csomagon belül."""
    return Path(__file__).parent / "help"


def fejezetek() -> list[str]:
    """A fejezetek a súgó mappájához képesti útvonalként, a FŐOLDALLAL elöl.

    A főoldal a tartalomjegyzék, ezért nem ábécérendben áll: az nyílik
    meg elsőként, tehát az első helye rögzített.
    """
    mappa = sugo_mappa()
    if not mappa.is_dir():
        return []
    nevek = sorted(
        ut.relative_to(mappa).as_posix()
        for ut in mappa.rglob("*.md")
        if not ut.name.startswith(_REJTETT_ELOTAG)
    )
    if FOOLDAL in nevek:
        nevek.remove(FOOLDAL)
        nevek.insert(0, FOOLDAL)
    return nevek


def _feloldott(nev: str) -> Path | None:
    """A fejezetnév biztonságos feloldása a súgó mappáján BELÜL.

    A fejezetnév a felületről jön (`helpTopic` tulajdonság, keresési
    találat), tehát nem megbízható bemenet: útvonal-bejárással
    (`../../`) ki lehetne lépni a csomagból. A feloldás után ezért
    ellenőrizzük, hogy tényleg a mappán belül maradtunk.
    """
    mappa = sugo_mappa().resolve()
    try:
        jelolt = (mappa / nev).resolve()
        jelolt.relative_to(mappa)
    except (ValueError, OSError):
        return None
    return jelolt if jelolt.is_file() else None


def fejezet_szovege(nev: str) -> str | None:
    """Egy fejezet nyers Markdown-szövege; ismeretlen névre `None`."""
    ut = _feloldott(nev)
    if ut is None:
        return None
    try:
        return ut.read_text(encoding="utf-8")
    except OSError:
        return None


def kereses(kifejezes: str) -> list[dict[str, str]]:
    """Szöveges keresés a súgóban.

    Args:
        kifejezes: a keresett szöveg; a kis- és nagybetű közömbös.

    Returns:
        Találatonként `{"fejezet": …, "cim": …, "reszlet": …}` szótárak.
        A `cim` a fejezet első `#` címsora, hogy a lista olvasható legyen
        a fájlnév ismerete nélkül is.
    """
    minta = (kifejezes or "").strip().casefold()
    if not minta:
        return []

    talalatok: list[dict[str, str]] = []
    for nev in fejezetek():
        szoveg = fejezet_szovege(nev) or ""
        cim = _cim(szoveg) or nev
        kicsi = szoveg.casefold()
        kezdet = 0
        while len(talalatok) < _MAX_TALALAT:
            hely = kicsi.find(minta, kezdet)
            if hely < 0:
                break
            talalatok.append(
                {
                    "fejezet": nev,
                    "cim": cim,
                    "reszlet": _reszlet(szoveg, hely, len(minta)),
                }
            )
            kezdet = hely + len(minta)
        if len(talalatok) >= _MAX_TALALAT:
            break
    return talalatok


def _cim(szoveg: str) -> str | None:
    """A fejezet első `#` címsora."""
    for sor in szoveg.splitlines():
        if sor.startswith("# "):
            return sor[2:].strip()
    return None


def _reszlet(szoveg: str, hely: int, hossz: int) -> str:
    """A találat körüli szövegkörnyezet, egyetlen sorba simítva."""
    eleje = max(0, hely - _RESZLET_SUGAR)
    vege = min(len(szoveg), hely + hossz + _RESZLET_SUGAR)
    darab = re.sub(r"\s+", " ", szoveg[eleje:vege]).strip()
    if eleje > 0:
        darab = "…" + darab
    if vege < len(szoveg):
        darab = darab + "…"
    return darab


__all__ = [
    "FOOLDAL",
    "fejezet_szovege",
    "fejezetek",
    "kereses",
    "sugo_mappa",
]
