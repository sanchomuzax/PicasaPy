"""Python-forrásblokk kivágása MÉRT határok mentén (#2540).

## Miért kell KÜLÖN mérő

A `qml_blokk.py` a `{ … }` párosításra épül — Python-forráson ez nem
értelmes: ott a blokk határát a **behúzás** adja, és egy `{` a
szótár-literálban is előfordul. A QML-mérőt Python-forrásra ráhúzni néma
mellémérés lenne, ezért a blokkhatárt itt az `ast` adja meg: a horgonyt
tartalmazó LEGBELSŐ függvény (vagy osztály) törzse.

## A hibaosztály, ami ellen szól (#2540)

Több vezérlő-őr így dolgozott:

```python
kezd = _CTL.index("def worker()")
blokk = _CTL[kezd : kezd + 700]      # ⚠️ rögzített ablak
```

A `700` nem a függvény határa, csak egy szám, ami az íráskor épp elég
volt. Amint a függvény **indoklást** kap — pontosan azt, amit a projekt
megkövetel —, a mért sorok kicsúsznak az ablakból, és az őr olyasmit
jelent hiányzónak, ami ott van a kódban. A másik irányban ugyanez a szám
BELELÓG a szomszéd függvénybe, tehát egy tagadó állítás
(`assert "replace(" not in blokk`) a szomszéd kódjától bukhat.

## A szabály

Az ablak legyen a függvény VALÓDI törzse. A kommenteket és a
dokumentációs sztringeket előbb kivágjuk: egy kommentbe írt sor nem
elégítheti ki az őrt, és egy hosszú indoklás sem szoríthatja ki a mért
sorokat.
"""

from __future__ import annotations

import ast
import io
import tokenize

_BLOKK_CSOMOPONTOK = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _kifeheritve(szoveg: str) -> str:
    """A szöveget szóközökre cseréli, a sortöréseket megtartva.

    Így a forrás HOSSZA és a sorszámozása változatlan marad — az `ast`
    által adott sor/oszlop koordináták a kifehérített szövegre is
    érvényesek.
    """
    return "".join("\n" if jel == "\n" else " " for jel in szoveg)


def _sor_kezdetek(forras: str) -> list[int]:
    """Az egyes sorok kezdő karakter-eltolása (1-alapú sorszámhoz)."""
    kezdetek = [0, 0]
    for i, jel in enumerate(forras):
        if jel == "\n":
            kezdetek.append(i + 1)
    return kezdetek


def _eltolas(kezdetek: list[int], sor: int, oszlop: int) -> int:
    """A `sor`:`oszlop` (ast-koordináta) karakter-eltolása."""
    return kezdetek[sor] + oszlop


def kommentek_nelkul(forras: str) -> str:
    """A Python-kommenteket és a dokumentációs sztringeket kifehéríti.

    A visszaadott szöveg **ugyanolyan hosszú**, mint a bemenet (a kivágott
    részek helyén szóköz áll), tehát a sorszámok és az eltolások
    megmaradnak.

    A `#` a sztringen belül NEM komment (`"a # b"` érintetlen marad) — ezt
    a `tokenize` intézi, nem szövegkeresés.

    :raises AssertionError: ha a forrás nem elemezhető Python.
    """
    try:
        fa = ast.parse(forras)
    except SyntaxError as hiba:  # pragma: no cover - elrontott forrás
        raise AssertionError(f"a forrás nem elemezhető Python: {hiba}") from hiba

    darabok = list(forras)
    kezdetek = _sor_kezdetek(forras)

    # 1) kommentek — tokenize szerint, nem szövegkereséssel
    try:
        tokenek = tokenize.generate_tokens(io.StringIO(forras).readline)
        for token in tokenek:
            if token.type != tokenize.COMMENT:
                continue
            tol = _eltolas(kezdetek, token.start[0], token.start[1])
            ig = _eltolas(kezdetek, token.end[0], token.end[1])
            darabok[tol:ig] = _kifeheritve(forras[tol:ig])
    except tokenize.TokenError as hiba:  # pragma: no cover
        raise AssertionError(f"a forrás nem tokenizálható: {hiba}") from hiba

    # 2) dokumentációs sztringek — a modul, az osztályok és a függvények
    #    első utasítása, ha az sztring-literál
    for csomopont in ast.walk(fa):
        if not isinstance(csomopont, (ast.Module, *_BLOKK_CSOMOPONTOK)):
            continue
        torzs = getattr(csomopont, "body", None)
        if not torzs:
            continue
        elso = torzs[0]
        if not (
            isinstance(elso, ast.Expr)
            and isinstance(elso.value, ast.Constant)
            and isinstance(elso.value.value, str)
        ):
            continue
        tol = _eltolas(kezdetek, elso.lineno, elso.col_offset)
        ig = _eltolas(kezdetek, elso.end_lineno, elso.end_col_offset)
        darabok[tol:ig] = _kifeheritve(forras[tol:ig])

    return "".join(darabok)


def fuggveny_torzs(forras: str, horgony: str) -> str:
    """A `horgony`-t tartalmazó LEGBELSŐ függvény (vagy osztály) forrása.

    A kommenteket és a docstringeket előbb kivágjuk — így egy kommentbe
    írt sor sem elégítheti ki az őrt, és egy hosszú indoklás sem
    szoríthatja ki a mért sorokat. A kivágás a `def` sorától a törzs
    utolsó soráig tart, tehát a szomszéd függvény NEM lóg bele: a tagadó
    állítások (`assert "x" not in blokk`) is értelmesek maradnak.

    :raises AssertionError: ha a horgony nincs meg (kommenten kívül), vagy
        nem áll függvényben/osztályban.
    """
    tiszta = kommentek_nelkul(forras)
    hely = tiszta.find(horgony)
    assert hely >= 0, (
        f"a horgony nincs meg a forrásban (kommenten és docstringen "
        f"kívül): {horgony!r}"
    )

    kezdetek = _sor_kezdetek(forras)
    fa = ast.parse(forras)

    talalat = None
    for csomopont in ast.walk(fa):
        if not isinstance(csomopont, _BLOKK_CSOMOPONTOK):
            continue
        # a `def`/`class` sorától (a díszítők NÉLKÜL) a törzs végéig
        tol = _eltolas(kezdetek, csomopont.lineno, csomopont.col_offset)
        ig = _eltolas(
            kezdetek, csomopont.end_lineno, csomopont.end_col_offset
        )
        if not tol <= hely < ig:
            continue
        # a LEGBELSŐ: a legkésőbb kezdődő befoglaló
        if talalat is None or tol > talalat[0]:
            talalat = (tol, ig)

    assert talalat is not None, (
        f"a horgony nem függvényben/osztályban áll: {horgony!r}"
    )
    return tiszta[talalat[0]:talalat[1]]
