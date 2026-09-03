#!/usr/bin/env python3
"""#2111: `subprocess.run(text=True)` KÖTELEZŐEN `encoding=`-gel.

## Miért kapu ez

A `text=True` (és a `universal_newlines=True`) a gyerekfolyamat kimenetét a
**locale-kódolással** dekódolja. Linuxon ez UTF-8, **Windowson `cp1252`** — a
saját őr-szkriptjeink viszont magyarul írnak, és a kimenetüket kifejezetten
UTF-8-ra állítják (`folyam.reconfigure(encoding="utf-8")`). A hívó oldal tehát
UTF-8-at kap, és cp1252-vel próbálja olvasni:

```
File "C:\\...\\Lib\\encodings\\cp1252.py", line 23, in decode
UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 6
```

Éles eset: a `main` CI-je **minden kód-merge után** pirosra ment a
windows-lábon (`ci.yml` 33711692677, windows 1/4), és a piros main
e-mail-értesítést küld a tulajdonosnak.

Ez a #2077 `posix_or.py`-jának testvére: ott a KIÍRÁS kódolása volt a hiba
(`UnicodeEncodeError`), itt a BEOLVASÁSÉ (`UnicodeDecodeError`).

## Amit az őr követel

```python
subprocess.run(..., text=True, encoding="utf-8", errors="replace")
```

Az `errors="replace"` nem kötelező (a hívó dönthet szigorúbban), az
`encoding=` viszont igen: enélkül a viselkedés **platformfüggő**, és a
fejlesztői gépen soha nem jön elő.

## Amit NEM néz

A `text=` nélküli (bájtos) hívásokat — ott nincs dekódolás, tehát nincs mit
elrontani.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
#: A vizsgált fák. A `src/` szándékosan NINCS köztük: a termék kódja ma nem
#: indít gyerekfolyamatot szöveges módban; ha egyszer fog, ide kell venni.
FAK = ("tests", "scripts")

#: A szöveges módot bekapcsoló kulcsszavak.
SZOVEGES = ("text", "universal_newlines")


def _subprocess_hivas(csomopont: ast.Call) -> str | None:
    """A hívott `subprocess` függvény neve, ha ez egy ilyen hívás."""
    fv = csomopont.func
    if isinstance(fv, ast.Attribute) and isinstance(fv.value, ast.Name):
        if fv.value.id == "subprocess" and fv.attr in {
            "run",
            "check_output",
            "Popen",
        }:
            return f"subprocess.{fv.attr}"
    return None


def _szoveges_mod(csomopont: ast.Call) -> bool:
    for kw in csomopont.keywords:
        if kw.arg in SZOVEGES and isinstance(kw.value, ast.Constant):
            if kw.value.value is True:
                return True
    return False


def _van_kodolas(csomopont: ast.Call) -> bool:
    return any(kw.arg == "encoding" for kw in csomopont.keywords)


def _utf8_kimenet() -> None:
    """A saját kiírásunk se bukjon el a Windows-konzolon (#2077)."""
    for folyam in (sys.stdout, sys.stderr):
        try:
            folyam.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def leletek(gyoker: Path | None = None) -> list[str]:
    """A leletek listája. `gyoker` megadásával EGY tetszőleges fát vizsgál —
    így az őr foga ellenőrizhető anélkül, hogy a próba a repó fájljait
    piszkálná (a párhuzamosan futó tesztek különben a vetett fájlokat
    látnák)."""
    talalatok: list[str] = []
    fak = [gyoker] if gyoker is not None else [GYOKER / nev for nev in FAK]
    alap = gyoker if gyoker is not None else GYOKER
    for fa in fak:
        for fajl in sorted(fa.rglob("*.py")):
            try:
                fa = ast.parse(fajl.read_text(encoding="utf-8"), filename=str(fajl))
            except SyntaxError as hiba:
                talalatok.append(f"{fajl.relative_to(alap)}: nem elemezhető ({hiba})")
                continue
            for cs in ast.walk(fa):
                if not isinstance(cs, ast.Call):
                    continue
                nev = _subprocess_hivas(cs)
                if nev is None or not _szoveges_mod(cs) or _van_kodolas(cs):
                    continue
                talalatok.append(
                    f"{fajl.relative_to(alap)}:{cs.lineno}: {nev}(…, text=True) "
                    'KÓDOLÁS NÉLKÜL — Windowson cp1252-vel dekódol. Add meg: '
                    'encoding="utf-8", errors="replace"'
                )
    return talalatok


def main(argv: list[str] | None = None) -> int:
    _utf8_kimenet()
    ervek = sys.argv[1:] if argv is None else argv
    hibak = leletek(Path(ervek[0]).resolve() if ervek else None)
    if hibak:
        print("Kódolás-őr: szöveges gyerekfolyamat megadott kódolás nélkül:")
        for h in hibak:
            print(f"  {h}")
        return 1
    print(
        "✅ a tests/ és a scripts/ minden szöveges `subprocess` hívása "
        "megadja a kódolást"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
