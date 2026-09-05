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

#: A találatok felső korlátja — **fejezetekben**, nem előfordulásokban
#: (#2214). Előfordulásra számolva egyetlen bőbeszédű fejezet elvitte a
#: keretet, és a hátrébb lévő — akár relevánsabb — fejezetek ki sem
#: kerültek a listára. Fejezetből ma 28 van, tehát ez a korlát ma nem is
#: harap; akkor lép működésbe, ha a súgó sokszorosára nő.
_MAX_FEJEZET = 200

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


#: Sémák, amelyek NEM a súgó belső fejezetére mutatnak. Ma egyik sem
#: fordul elő a súgóban (mérve: 42 relatív hivatkozás, 0 külső) — a lista
#: azért van, hogy egy később bekerülő külső hivatkozás se oldódjon fel
#: némán fejezetnévvé.
_KULSO_SEMAK = ("http://", "https://", "mailto:", "ftp://", "file://")


def hivatkozas_celja(honnan: str, cel: str) -> str | None:
    """Egy Markdown-hivatkozás célja fejezetnévként — vagy `None`.

    A súgó lapjai egymásra **relatívan** hivatkoznak (`features/konyvtar.md`
    a gyökérből, `../index.md` egy almappából), ezért a feloldás a HIVATKOZÓ
    fejezet mappájához képest történik.

    Args:
        honnan: a hivatkozást tartalmazó fejezet neve (`fejezetek()` alakja).
        cel: a Markdown-hivatkozás nyers célja, horgonnyal együtt is.

    Returns:
        A cél fejezet neve a `fejezetek()` alakjában, vagy `None`, ha a cél
        külső, nem létező, vagy kilépne a súgó mappájából.
    """
    if not cel or not cel.strip():
        return None
    tiszta = cel.strip()
    if tiszta.lower().startswith(_KULSO_SEMAK):
        return None
    # `konyvtar.md#albumok` — a horgony a lapon belüli hely, a fejezet
    # attól még ugyanaz. A csak-horgony (`#szakasz`) viszont nem visz sehova.
    tiszta = tiszta.split("#", 1)[0]
    if not tiszta:
        return None

    mappa = sugo_mappa().resolve()
    szulo = (mappa / honnan).parent
    try:
        jelolt = (szulo / tiszta).resolve()
        viszonylagos = jelolt.relative_to(mappa)
    except (ValueError, OSError):
        return None
    if not jelolt.is_file():
        return None
    return viszonylagos.as_posix()


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
        **Fejezetenként legfeljebb egy** találat:
        `{"fejezet": …, "cim": …, "reszlet": …, "db": …}`. A `cim` a fejezet
        első `#` címsora (a fájlnév nem olvasható a felhasználónak), a
        `reszlet` az első előfordulás környezete, a `db` az előfordulások
        száma a lapon.
    """
    minta = (kifejezes or "").strip().casefold()
    if not minta:
        return []

    talalatok: list[dict[str, object]] = []
    for nev in fejezetek():
        if len(talalatok) >= _MAX_FEJEZET:
            break
        szoveg = fejezet_szovege(nev) or ""
        kicsi = szoveg.casefold()
        elso = kicsi.find(minta)
        if elso < 0:
            continue
        # A fejezet EGY sorral szerepel: a felhasználó a címet látja, és
        # ugyanaz a cím ötször egymás alatt semmit nem mond neki (#2214).
        # A részlet az ELSŐ előfordulás környezete, a `db` pedig megmondja,
        # hányszor fordul elő a lapon — így a sorok különböznek egymástól.
        talalatok.append(
            {
                "fejezet": nev,
                "cim": _cim(szoveg) or nev,
                "reszlet": _reszlet(szoveg, elso, len(minta)),
                "db": kicsi.count(minta),
            }
        )
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
