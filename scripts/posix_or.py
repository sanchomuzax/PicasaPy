#!/usr/bin/env python3
"""#2077: MODULSZINTEN nem hívható POSIX-only `os`-függvény a tesztekben.

## Miért kapu ez, és nem ajánlás

A `skipif` dekorátor kifejezése az **importáláskor** fut le. Ha abban egy
Windowson nem létező `os`-függvény áll, nem egy teszt bukik el, hanem a
**teljes gyűjtés** — és vele az egész részfutás.

Éles eset (`ci.yml` 33690975023, windows 1/4):

```
ERROR collecting tests/scanner/test_hibas_bejegyzesek_1998.py
    @pytest.mark.skipif(os.getuid() == 0, reason="root mindent olvashat")
E   AttributeError: module 'os' has no attribute 'getuid'
!!! Interrupted: 1 error during collection !!!
```

A windows-láb nem blokkol, ezért ez némán élt — és a `tests --ignore=tests/app`
részfutás EGÉSZE elveszett vele.

## Amit az őr ENGED

1. **A függvényen/fixture-ön BELÜLI hívást** — ott a `skipif` már
   megvédte, a kód csak akkor fut, ha a teszt egyáltalán elindul.
2. **A RÖVIDZÁRRAL védett modulszintű hívást.** A projektben ez a bevált,
   helyes alak, és az őr nem büntetheti:

   ```python
   pytestmark = pytest.mark.skipif(
       sys.platform.startswith("win")
       or (hasattr(os, "geteuid") and os.geteuid() == 0),
       reason="…",
   )
   ```

   Windowson a `sys.platform.startswith("win")` igaz → a `or` rövidre zár;
   ha nem, a `hasattr` hamis → az `and` zár rövidre. A hívás sosem fut le.

⚠️ Ezért az őr azt nézi, hogy a hívást tartalmazó **utasításban** ott
van-e a védelem (`hasattr(os, "<ugyanaz a név>")` vagy `sys.platform`-os
Windows-vizsgálat). Ez szándékosan megengedő: a cél a VÉDTELEN alak
kiszűrése, nem a stílus egységesítése.

## A helyes alak

```python
@pytest.mark.skipif(
    not hasattr(os, "getuid") or os.getuid() == 0,
    reason="Windowson nincs os.getuid, root alatt pedig minden olvasható",
)
```

A `hasattr` **rövidzár**: Windowson a második tag már le sem fut.
"""

from __future__ import annotations

import ast
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
TESZTEK = GYOKER / "tests"

#: Az `os` azon függvényei, amelyek a CPython Windows-építésében NINCSENEK.
#: Csak olyat veszünk fel, aminek a hiánya `AttributeError`-t ad — a
#: „létezik, de mást csinál" eset nem ide tartozik (az a #1217 hatóköre).
POSIX_ONLY = frozenset(
    {
        "getuid",
        "geteuid",
        "getgid",
        "getegid",
        "getlogin",
        "uname",
        "fork",
        "getpgrp",
        "setuid",
        "setgid",
    }
)


def _modulszintu_hivasok(fa: ast.Module) -> list[tuple[int, str]]:
    """A modul- és osztálytörzsben (dekorátorokat is beleértve) álló
    `os.<posix>` hívások — a függvénytörzseket NEM járjuk be."""
    talalatok: list[tuple[int, str]] = []

    def bejar(csomopontok) -> None:
        for cs in csomopontok:
            if isinstance(cs, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # a törzs futásidejű, de a DEKORÁTOROK modulszintűek
                for dek in cs.decorator_list:
                    talalatok.extend(_hivasok(dek))
                continue
            if isinstance(cs, ast.ClassDef):
                for dek in cs.decorator_list:
                    talalatok.extend(_hivasok(dek))
                bejar(cs.body)
                continue
            talalatok.extend(_hivasok(cs))

    bejar(fa.body)
    return talalatok


def _vedelmek(csomopont: ast.AST) -> tuple[set[str], bool]:
    """Az utasításban található védelmek: mely `os`-nevekre van `hasattr`,
    és van-e `sys.platform`-alapú Windows-vizsgálat."""
    nevek: set[str] = set()
    platform = False
    for cs in ast.walk(csomopont):
        if isinstance(cs, ast.Call):
            fv = cs.func
            if isinstance(fv, ast.Name) and fv.id == "hasattr" and len(cs.args) == 2:
                cel, attr = cs.args
                if (
                    isinstance(cel, ast.Name)
                    and cel.id == "os"
                    and isinstance(attr, ast.Constant)
                    and isinstance(attr.value, str)
                ):
                    nevek.add(attr.value)
        if isinstance(cs, ast.Attribute) and cs.attr == "platform":
            if isinstance(cs.value, ast.Name) and cs.value.id == "sys":
                platform = True
    return nevek, platform


def _hivasok(csomopont: ast.AST) -> list[tuple[int, str]]:
    vedett_nevek, platform_vedett = _vedelmek(csomopont)
    ki: list[tuple[int, str]] = []
    for cs in ast.walk(csomopont):
        if not isinstance(cs, ast.Call):
            continue
        fv = cs.func
        if (
            isinstance(fv, ast.Attribute)
            and isinstance(fv.value, ast.Name)
            and fv.value.id == "os"
            and fv.attr in POSIX_ONLY
            and fv.attr not in vedett_nevek
            and not platform_vedett
        ):
            ki.append((cs.lineno, f"os.{fv.attr}()"))
    return ki


def main() -> int:
    hibak: list[str] = []
    fajlok = sorted(TESZTEK.rglob("*.py"))
    for fajl in fajlok:
        try:
            fa = ast.parse(fajl.read_text(encoding="utf-8"), filename=str(fajl))
        except SyntaxError as hiba:
            hibak.append(f"{fajl.relative_to(GYOKER)}: nem elemezhető ({hiba})")
            continue
        for sor, nev in _modulszintu_hivasok(fa):
            hibak.append(
                f"{fajl.relative_to(GYOKER)}:{sor}: MODULSZINTŰ {nev} — "
                "Windowson elszáll a GYŰJTÉS. Helyette: "
                'not hasattr(os, "…") or os.…()'
            )
    if hibak:
        print("POSIX-őr: modulszintű, Windowson hiányzó os-hívás:")
        for h in hibak:
            print(f"  {h}")
        return 1
    print(
        f"✅ {len(fajlok)} tesztfájl, {len(POSIX_ONLY)} figyelt os-függvény — "
        "modulszinten egy sem hívódik"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
