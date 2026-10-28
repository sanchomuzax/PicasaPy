"""Őr (#6085): függvény nem adhat vissza helyi QImage pufferére mutató
numpy-nézetet.

A `np.frombuffer(kep.constBits())` nem másol: ha a `kep` a függvényen belül
jött létre (például `convertToFormat()`-tal), a függvény végén felszabadul, és
a visszaadott tömb felszabadított memóriára mutat. Windowson ez
hozzáférés-megsértéssel összeomlik, máshol csendben hamis képpontokat ad.
A helyes alak a `.copy()` a visszaadott tömbön, vagy `bytes(...)` a
puffer köré.
"""

from __future__ import annotations

import ast
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_KONYVTARAK = ("src", "tests", "scripts")
_PUFFER = {"constBits", "bits"}


def _puffer_nezet_forrasa(csomopont: ast.AST) -> str | None:
    """A `np.frombuffer(<név>.constBits(), ...)` hívás képváltozójának neve."""
    if not (
        isinstance(csomopont, ast.Call)
        and isinstance(csomopont.func, ast.Attribute)
        and csomopont.func.attr == "frombuffer"
        and csomopont.args
    ):
        return None
    elso = csomopont.args[0]
    if (
        isinstance(elso, ast.Call)
        and isinstance(elso.func, ast.Attribute)
        and elso.func.attr in _PUFFER
        and isinstance(elso.func.value, ast.Name)
    ):
        return elso.func.value.id
    return None


def _masolatra_vegzodik(kifejezes: ast.AST) -> bool:
    return (
        isinstance(kifejezes, ast.Call)
        and isinstance(kifejezes.func, ast.Attribute)
        and kifejezes.func.attr in {"copy", "tobytes", "tolist"}
    )


def _nevek(kifejezes: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(kifejezes) if isinstance(n, ast.Name)}


def _fuggveny_hibai(fuggveny: ast.FunctionDef) -> list[int]:
    helyi_kepek: set[str] = set()
    nezetek: set[str] = set()
    for csomopont in ast.walk(fuggveny):
        if isinstance(csomopont, ast.Assign):
            celok = {c.id for c in csomopont.targets if isinstance(c, ast.Name)}
            helyi_kepek |= celok
            forras = next(
                (
                    f
                    for f in map(_puffer_nezet_forrasa, ast.walk(csomopont.value))
                    if f
                ),
                None,
            )
            if forras and not _masolatra_vegzodik(csomopont.value):
                nezetek |= celok
    hibak = []
    for csomopont in ast.walk(fuggveny):
        if not isinstance(csomopont, ast.Return) or csomopont.value is None:
            continue
        ertek = csomopont.value
        if _masolatra_vegzodik(ertek):
            continue
        kozvetlen = {
            f for f in map(_puffer_nezet_forrasa, ast.walk(ertek)) if f
        }
        if (kozvetlen & helyi_kepek) or (_nevek(ertek) & nezetek):
            hibak.append(csomopont.lineno)
    return hibak


def _leletek() -> list[str]:
    leletek = []
    for konyvtar in _KONYVTARAK:
        for fajl in sorted((_GYOKER / konyvtar).rglob("*.py")):
            szoveg = fajl.read_text(encoding="utf-8")
            if "frombuffer" not in szoveg:
                continue
            fa = ast.parse(szoveg)
            for csomopont in ast.walk(fa):
                if isinstance(csomopont, ast.FunctionDef):
                    leletek += [
                        f"{fajl.relative_to(_GYOKER)}:{sor}"
                        for sor in _fuggveny_hibai(csomopont)
                    ]
    return leletek


def test_nincs_felszabadulo_kepre_mutato_visszaadott_nezet() -> None:
    assert _leletek() == []


def test_az_or_megfogja_a_hibas_mintat() -> None:
    hibas = ast.parse(
        "def f(kep):\n"
        "    rgba = kep.convertToFormat(1)\n"
        "    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)\n"
        "    return adat.reshape(2, 2)\n"
    ).body[0]
    jo = ast.parse(
        "def f(kep):\n"
        "    rgba = kep.convertToFormat(1)\n"
        "    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)\n"
        "    return adat.reshape(2, 2).copy()\n"
    ).body[0]
    assert _fuggveny_hibai(hibas) == [4]
    assert _fuggveny_hibai(jo) == []
