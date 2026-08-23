"""Minden platformfüggő ág legyen HELYETTESÍTHETŐ (#1217).

## A minta, ami egyetlen napon NÉGYSZER bukott

| jegy | a teszt feltevése | a windows-lábon |
|---|---|---|
| #1076 | `XDG_CONFIG_HOME` adja a konfig-mappát | a natív `%APPDATA%`-n bukott |
| #1182 | `$XDG_DATA_HOME/Trash` a lomtár | a natív Lomtáron bukott |
| #1206 | a `/` a negyedik gyökér | a valódi meghajtókon bukott |
| #1167 | a „teljes gép" a home-könyvtár | a valódi meghajtókon bukott |

**Mind a négyben a TERMÉK volt helyes, és a TESZT bukott** — ráadásul úgy,
hogy a bukás a natív (helyes) viselkedést mutatta hibának.

## A szabály

> Ha egy teszt állítása egy platformra igaz, a teszt MONDJA KI, melyikre.

Ehhez a terméknek adnia kell egy fogantyút: a platform-lekérdezés legyen
**modulszintű, helyettesíthető** — vagy `_platform()` függvény, vagy
nevesített `platform=` paraméter. Aki közvetlenül a `sys.platform`-ot
olvassa egy elágazásban, azt a teszt csak a saját gépén tudja állítani.

⚠️ **A `skipif` nem megoldás:** a kihagyott teszt a másik platformon NEM
mér semmit. A rögzítéssel mindkét lábon fut, és azt méri, amit állít.
"""

from __future__ import annotations

import ast
import pathlib

FORRAS = pathlib.Path(__file__).resolve().parents[1] / "src" / "picasapy"

#: Ahol a `sys.platform` olvasása RENDBEN van: maga a fogantyú, illetve a
#: nevesített paraméter alapértéke.
_ENGEDETT_FUGGVENYEK = {"_platform"}


def _platform_olvasasok(fa: ast.AST) -> list[ast.Attribute]:
    """A `sys.platform` attribútum-olvasások a fában."""
    return [
        csomopont
        for csomopont in ast.walk(fa)
        if isinstance(csomopont, ast.Attribute)
        and csomopont.attr == "platform"
        and isinstance(csomopont.value, ast.Name)
        and csomopont.value.id == "sys"
    ]


def _van_platform_parameter(fuggveny) -> bool:
    """Van-e `platform` nevű paramétere — az is szabályos fogantyú.

    Az `application.py` ezt használja: `platform: str | None = None`, majd
    `sys.platform if platform is None else platform`. A teszt így ki tudja
    mondani, melyik platformot méri — a hívásban."""
    argok = fuggveny.args
    nevek = {
        a.arg
        for a in [*argok.posonlyargs, *argok.args, *argok.kwonlyargs]
    }
    return "platform" in nevek


def _fuggveny_torzsek(fa: ast.AST) -> dict[int, tuple[str, bool]]:
    """Sorszám → (az őt tartalmazó függvény neve, van-e platform-paramétere).

    A legbelső nyer."""
    hova: dict[int, tuple[str, bool]] = {}
    for csomopont in ast.walk(fa):
        if isinstance(csomopont, ast.FunctionDef | ast.AsyncFunctionDef):
            adat = (csomopont.name, _van_platform_parameter(csomopont))
            for sor in range(csomopont.lineno, (csomopont.end_lineno or 0) + 1):
                hova[sor] = adat
    return hova


def test_a_sys_platform_csak_a_fogantyuban_es_alapertekben_all():
    """Elágazásban közvetlen `sys.platform` nem lehet."""
    vetok: list[str] = []
    for ut in sorted(FORRAS.rglob("*.py")):
        fa = ast.parse(ut.read_text(encoding="utf-8"), filename=str(ut))
        hova = _fuggveny_torzsek(fa)
        # a nevesített paraméterek alapértékei (pl. `platform=sys.platform`)
        alapertekek = {
            id(ertek)
            for csomopont in ast.walk(fa)
            if isinstance(csomopont, ast.FunctionDef | ast.AsyncFunctionDef)
            for ertek in [*csomopont.args.defaults, *csomopont.args.kw_defaults]
            if ertek is not None
        }
        for olvasas in _platform_olvasasok(fa):
            if id(olvasas) in alapertekek:
                continue
            nev, van_parameter = hova.get(olvasas.lineno, ("<modul>", False))
            if nev in _ENGEDETT_FUGGVENYEK or van_parameter:
                continue
            vetok.append(
                f"{ut.relative_to(FORRAS.parents[1])}:{olvasas.lineno} ({nev})"
            )

    assert not vetok, (
        "közvetlen `sys.platform` olvasás elágazásban — a teszt így nem "
        "tudja kimondani, melyik platformot méri (#1217):\n  "
        + "\n  ".join(vetok)
    )


def test_a_fogantyu_neve_egyseges():
    """Ahol van fogantyú, ott `_platform` a neve — ne legyen három név."""
    nevek: set[str] = set()
    for ut in sorted(FORRAS.rglob("*.py")):
        fa = ast.parse(ut.read_text(encoding="utf-8"), filename=str(ut))
        for csomopont in ast.walk(fa):
            if not isinstance(csomopont, ast.FunctionDef):
                continue
            if _platform_olvasasok(csomopont) and not _van_platform_parameter(
                csomopont
            ):
                nevek.add(csomopont.name)

    assert nevek <= _ENGEDETT_FUGGVENYEK, (
        f"a platform-fogantyú több néven él: {sorted(nevek)}"
    )
