"""#2653 — a #985 kettébontott őrei: se lefedettség, se izoláció ne vesszen.

## Miért van erre őr

A #985 mind a 34 esetét egyetlen fájl vitte, tesztenként friss `qml_app`
alkalmazással. MÉRVE (2026-09-07, RPi5, `MemoryMax=2400M`):

    egy fájl, 34 teszt   →  94 mp,  csúcs 2233 MiB  (a plafon 93%-a)
    ugyanaz 1600 MiB-os plafonnal → 18 perc alatt sem ért a 19. tesztig

A plafonhoz érve a kernel visszanyerésbe fordul, és a futásidő
sokszorosára nő — ezt látta a jegy 640 másodpercként. A javítás a fájl
kettébontása:

    állapotmentes őrök, EGY közös app  →  15 teszt,  4,8 mp,  393 MiB
    állapotot író tesztek, appal/teszt →  19 teszt, 41,2 mp, 1128 MiB

Ez az őr azt a két dolgot tartja, ami a bontásból némán elveszhet:

1. **a 34 eset megvan** — egy „gyorsítás", ami tesztet töröl, nem
   gyorsítás, hanem lefedettség-vesztés;
2. **az állapotmentes fájl állapotmentes marad** — a közös, modul-szintű
   app mellé betett lapnyitás vagy fülváltás a SZOMSZÉD teszteket rontaná
   el, méghozzá a futási sorrendtől függően, tehát ingadozva.
"""

from __future__ import annotations

import ast
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[2]
_QML = _GYOKER / "tests" / "app" / "qml_functional"

#: A bontás előtti fájl esetszáma. Ez a szám a #985 elfogadási
#: feltételének terjedelme — csökkennie csak jegyben indokolt döntéssel
#: szabad, és akkor is itt, láthatóan.
OSSZES_ESET = 34

ALLAPOTMENTES = _QML / "test_collage_panel_wiring_985_allapotmentes.py"
ALLAPOTIRO = _QML / "test_collage_panel_wiring_985.py"

#: Segédek, amelyek TARTÓS állapotot írnak a közös alkalmazásba: lapot
#: nyitnak, fület váltanak, kattintanak. Ezek a közös appot használó
#: fájlban nem szerepelhetnek.
ALLAPOTIRO_SEGEDEK = (
    "_kollazs_lapot_nyit",
    "_konyvtar_fulre",
    "_kollazs_fulre",
    "_fulre_kattint_amig_valt",
    "_kattints",
    "_tolts_fel",
)


def _esetszam(fajl: Path) -> int:
    """A fájlban gyűjthető tesztesetek száma, paraméterezéssel együtt."""
    fa = ast.parse(fajl.read_text(encoding="utf-8"))
    osszes = 0
    for csomopont in ast.walk(fa):
        if not isinstance(csomopont, ast.FunctionDef):
            continue
        if not csomopont.name.startswith("test_"):
            continue
        szorzo = 1
        for dekorator in csomopont.decorator_list:
            if not isinstance(dekorator, ast.Call):
                continue
            nev = ast.unparse(dekorator.func)
            if not nev.endswith("parametrize"):
                continue
            # a második argumentum az eseteket felsoroló lista
            esetek = dekorator.args[1]
            assert isinstance(esetek, (ast.List, ast.Tuple)), (
                f"{fajl.name}: a {csomopont.name} parametrize-listája nem "
                "sorolható meg statikusan — az őr így nem tud számolni"
            )
            szorzo *= len(esetek.elts)
        osszes += szorzo
    return osszes


def test_a_ket_fajl_egyutt_hozza_a_985_osszes_eseteet() -> None:
    """A bontás nem törölhetett esetet — 15 + 19 = 34."""
    a = _esetszam(ALLAPOTMENTES)
    b = _esetszam(ALLAPOTIRO)
    assert a + b == OSSZES_ESET, (
        f"a #985 két fájlja együtt {a} + {b} = {a + b} esetet hoz, nem "
        f"{OSSZES_ESET}-et — a bontás lefedettséget vesztett"
    )


def test_az_allapotmentes_fajl_nem_ir_allapotot() -> None:
    """A közös, modul-szintű app mellé nem kerülhet állapotot író teszt."""
    szoveg = ALLAPOTMENTES.read_text(encoding="utf-8")
    # a modul saját docstringje NEVESÍTI a segédeket — azt nem mérjük
    fa = ast.parse(szoveg)
    torzs = "\n".join(
        ast.unparse(csomopont) for csomopont in fa.body
        if not (isinstance(csomopont, ast.Expr)
                and isinstance(csomopont.value, ast.Constant))
    )
    talalt = [seged for seged in ALLAPOTIRO_SEGEDEK if seged in torzs]
    assert not talalt, (
        f"{ALLAPOTMENTES.name}: állapotot író segéd(ek) a közös appot "
        f"használó fájlban: {', '.join(talalt)}. Ezek a szomszéd teszteket "
        "rontják el, sorrendfüggően — a helyük a "
        f"{ALLAPOTIRO.name}."
    )


def test_az_allapotmentes_fajl_MODUL_szintu_appot_hasznal() -> None:
    """A gyorsítás lelke a közös app — ha visszaesik függvény-scope-ra, a
    fájl megint 15 alkalmazást épít, és a mérés hazudik."""
    fa = ast.parse(ALLAPOTMENTES.read_text(encoding="utf-8"))
    for csomopont in fa.body:
        if isinstance(csomopont, ast.FunctionDef) and csomopont.name == "qml_app":
            # az `ast.unparse` egyszeres idézőjelre normalizál
            dekoratorok = [
                ast.unparse(d).replace("'", '"')
                for d in csomopont.decorator_list
            ]
            assert any('scope="module"' in d for d in dekoratorok), (
                "a qml_app felülírása nem modul-szintű — a fájl "
                "tesztenként új alkalmazást épít"
            )
            return
    raise AssertionError(
        f"{ALLAPOTMENTES.name}: nincs saját `qml_app` fixture — a fájl a "
        "függvény-scope-ú alapértelmezést kapja"
    )
