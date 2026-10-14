"""Őr a tests/app várakozó-segédeinek korlátjára (#4970).

A feltételre váró helyi segédek (`_var*`, `_wait*` előtaggal) korlátja legalább
10 másodperc legyen, és a hívások se adjanak 10 másodperc alatti literált. Így a
windowsos CI lassú futásai nem adnak hamis bukást, és a szorzó
(`PICASAPY_TESZT_IDOSZORZO`) a helyi korlátokon is hat.

A még át nem írt fájlok a `KIVETEL` listán vannak. A lista csak csökkenhet:
ha egy fájl átíródott, a kivételt törölni kell (a stale bejegyzés bukik), és
új fájl nem kerülhet fel rá (`KIVETEL_PLAFON`).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

TESZT_GYOKER = Path(__file__).resolve().parent
TESZT_APP = TESZT_GYOKER / "app"

KORLAT_MP = 10.0
KORLAT_MS = 10_000.0

HELYI_PREFIX = re.compile(r"^_(var|wait)")
IDOS_NEV = re.compile(r"(masodperc|timeout|seconds|hatarido|lejarat|ezred|^ido$|^ms$|_ms$|_mp$|_s$|^s$)")
MS_NEV = re.compile(r"(^ms$|_ms$|ezred)")
# A pillanatnyi lista hossza (9 fájl); csak csökkenhet.
KIVETEL_PLAFON = 9
# Szándékosan a listán maradó fájlok: negatív ablakot („nem jelenik meg") vagy
# fix idejű várakozást (`lambda: False`) mérnek. Ezek a korlátját nem emelhetjük,
# különben a negatív állítás vagy a fix várakozás lassulna. A feltétel-várakozó
# segédjük már a közös var_feltetelre-t hívja.
KIVETEL: frozenset[str] = frozenset(
    {
        "tests/app/qml_functional/test_general_ui_settings_4449.py",  # negatív: `assert not _varj(..., 0.9)`
        "tests/app/qml_functional/test_kimeneti_tulcsordulas_2191.py",  # fix idő: `_var(lambda: False, 0.3)`
        "tests/app/qml_functional/test_mappa_borito_ikon_2215.py",  # fix idő: `_var(lambda: False, 1.0)` ×2
        "tests/app/qml_functional/test_nyomtatas_ablakmeret_4795.py",  # fix idő: `_var(lambda: False, 0.3)` ×2
        "tests/app/qml_functional/test_tulcsordulas_fuggoleges_4537.py",  # fix idő: `_var(lambda: False, 1.0)`
        "tests/app/test_exportcel_indexelese_1565.py",  # negatív: `assert not _var(..., 3.0)`
        "tests/app/test_kimenet_resync_1539.py",  # negatív: `assert not _var(..., 3.0)`
        "tests/app/test_mappa_athelyezes_resync_1538.py",  # fix idő: `_var(lambda: False, 0.5)`
        "tests/app/test_qml_splash.py",  # negatív: `assert not _wait_until(..., timeout_ms=600)`
    }
)


@dataclass(frozen=True)
class Helper:
    nev: str
    fajl: str
    sor: int
    idoparamok: tuple[tuple[int, str, bool, float | None], ...]  # (index, név, ms?, alap)


@dataclass(frozen=True)
class Eltres:
    fajl: str
    sor: int
    tipus: str  # "helyi" (a segéd alapértéke) vagy "hivas" (a hívás literálja)
    leiras: str


def _feltetel_tipusu(fn: ast.FunctionDef) -> bool:
    """Feltételre vár: a törzsében a paraméterét, egy belső függvényét, vagy a
    közös `var_feltetelre`-t hívja (a vékony burkoló is ilyen)."""
    hivhatok = {a.arg for a in fn.args.args}
    hivhatok |= {n.name for n in ast.walk(fn) if isinstance(n, ast.FunctionDef) and n is not fn}
    hivhatok.add("var_feltetelre")
    return any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in hivhatok
        for n in ast.walk(fn)
    )


def _szam(node: ast.AST | None) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    return None


def _helperek(fa: ast.Module, rel: str) -> list[Helper]:
    eredmeny = []
    for node in ast.walk(fa):
        if not (isinstance(node, ast.FunctionDef) and HELYI_PREFIX.match(node.name)):
            continue
        if not _feltetel_tipusu(node):
            continue
        args = node.args.args
        off = len(args) - len(node.args.defaults)
        idoparamok = []
        for i, a in enumerate(args):
            if not IDOS_NEV.search(a.arg):
                continue
            alap = _szam(node.args.defaults[i - off]) if i >= off else None
            idoparamok.append((i, a.arg, bool(MS_NEV.search(a.arg)), alap))
        if idoparamok:
            eredmeny.append(Helper(node.name, rel, node.lineno, tuple(idoparamok)))
    return eredmeny


def _korlat_alatt(ertek: float, ms: bool) -> bool:
    return ertek < (KORLAT_MS if ms else KORLAT_MP)


def _importok(fa: ast.Module, forrasok: set[str]) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    """A fájl importjai a vizsgált (`forrasok`) fájlokra képezve.

    Visszatér: (modul-aliasok: alias -> fájl, név-importok: alias -> (fájl, eredeti név)).
    A `tests/support` és más, nem vizsgált modul nem kerül be: a neve nem
    üteközhet a vizsgált helyi segédekkel."""
    modulok: dict[str, str] = {}
    nevek: dict[str, tuple[str, str]] = {}
    for node in ast.walk(fa):
        if not (isinstance(node, ast.ImportFrom) and node.module and node.level == 0):
            continue
        alap = node.module.replace(".", "/")
        for a in node.names:
            alias = a.asname or a.name
            if f"{alap}/{a.name}.py" in forrasok:
                modulok[alias] = f"{alap}/{a.name}.py"
            elif f"{alap}.py" in forrasok:
                nevek[alias] = (f"{alap}.py", a.name)
    return modulok, nevek


def _hivott_segedek(
    hivas: ast.Call,
    rel: str,
    helyi_nevek: set[str],
    modulok: dict[str, str],
    importalt: dict[str, tuple[str, str]],
    nevek: dict[str, list[Helper]],
) -> list[Helper]:
    """Melyik segédet hívja a hívás: a fájl saját definícióját, vagy az import szerintit.

    A nevek egyezése önmagában nem elég: két modul is adhat `_var`-t, és csak
    az számít, amelyiket a fájl ténylegesen importálja."""
    fn = hivas.func
    if isinstance(fn, ast.Name):
        if fn.id in helyi_nevek:
            return [h for h in nevek.get(fn.id, []) if h.fajl == rel]
        if fn.id in importalt:
            fajl, eredeti = importalt[fn.id]
            return [h for h in nevek.get(eredeti, []) if h.fajl == fajl]
        return []
    if isinstance(fn, ast.Attribute):
        if isinstance(fn.value, ast.Name) and fn.value.id in modulok:
            fajl = modulok[fn.value.id]
            return [h for h in nevek.get(fn.attr, []) if h.fajl == fajl]
        return [h for h in nevek.get(fn.attr, []) if h.fajl == rel]
    return []


def _eltresek(forrasok: dict[str, str]) -> list[Eltres]:
    """Minden forrásfájl (relatív út -> szöveg) sértését megadja, egyszer."""
    fak = {rel: ast.parse(szoveg) for rel, szoveg in forrasok.items()}
    helperek = [h for rel, fa in fak.items() for h in _helperek(fa, rel)]
    eredmeny: list[Eltres] = []
    for h in helperek:
        for _index, nev, ms, alap in h.idoparamok:
            if alap is not None and _korlat_alatt(alap, ms):
                eredmeny.append(Eltres(h.fajl, h.sor, "helyi", f"{h.nev}: {nev}={alap:g} (korlát {'ms' if ms else 's'})"))
    nevek: dict[str, list[Helper]] = {}
    for h in helperek:
        nevek.setdefault(h.nev, []).append(h)
    for rel, fa in fak.items():
        helyi_nevek = {n.name for n in ast.walk(fa) if isinstance(n, ast.FunctionDef)}
        modulok, importalt = _importok(fa, set(forrasok))
        for node in ast.walk(fa):
            if not isinstance(node, ast.Call):
                continue
            for h in _hivott_segedek(node, rel, helyi_nevek, modulok, importalt, nevek):
                eredmeny.extend(_hivas_eltresei(rel, node, h))
    egyedi: dict[tuple[str, int, str], Eltres] = {}
    for e in eredmeny:
        egyedi.setdefault((e.fajl, e.sor, e.tipus), e)
    return sorted(egyedi.values(), key=lambda e: (e.fajl, e.sor))


def _hivas_eltresei(rel: str, hivas: ast.Call, h: Helper) -> list[Eltres]:
    talalt = []
    for index, nev, ms, _alap in h.idoparamok:
        ertek = _szam(hivas.args[index]) if index < len(hivas.args) else None
        kulcsszo = next((kw for kw in hivas.keywords if kw.arg == nev), None)
        if kulcsszo is not None:
            ertek = _szam(kulcsszo.value)
        if ertek is not None and _korlat_alatt(ertek, ms):
            talalt.append(Eltres(rel, hivas.lineno, "hivas", f"{h.nev}({nev}={ertek:g}) (korlát {'ms' if ms else 's'})"))
    return talalt


def _beolvas() -> dict[str, str]:
    return {
        p.relative_to(TESZT_GYOKER.parent).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(TESZT_APP.rglob("*.py"))
    }


def test_a_helyi_segedek_korlata_legalabb_tiz_masodperc():
    eltresek = [e for e in _eltresek(_beolvas()) if e.tipus == "helyi" and e.fajl not in KIVETEL]
    assert not eltresek, "10 s alatti helyi várakozás:\n" + "\n".join(
        f"  {e.fajl}:{e.sor} {e.leiras}" for e in eltresek
    )


def test_a_hivasok_nem_adnak_tiz_masodperc_alatti_literalt():
    hivas_sertesek = [
        e for e in _eltresek(_beolvas()) if e.tipus == "hivas" and e.fajl not in KIVETEL
    ]
    assert not hivas_sertesek, "10 s alatti literál a várakozó hívásban:\n" + "\n".join(
        f"  {e.fajl}:{e.sor} {e.leiras}" for e in hivas_sertesek
    )


def test_kivetellista_csak_csokkenhet():
    alap = {e.fajl for e in _eltresek(_beolvas())}
    elavult = sorted(KIVETEL - alap)
    assert not elavult, "ezek már át vannak írva, töröld a KIVETEL-ből: " + ", ".join(elavult)
    print(f"\nKIVETEL hossza: {len(KIVETEL)} (plafon: {KIVETEL_PLAFON})")
    assert len(KIVETEL) <= KIVETEL_PLAFON, (
        f"a KIVETEL nőtt: {len(KIVETEL)} > {KIVETEL_PLAFON}; új fájl nem kerülhet fel"
    )


_ROSSZ = '''
def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    return feltetel()


def teszt(qt_app):
    _var(qt_app, lambda: True, 2.0)
'''

_JO = '''
def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return feltetel()


def _wait_ms(qt_app, ms):
    return ms


def teszt(qt_app):
    _var(qt_app, lambda: True, 10.0)
    _wait_ms(qt_app, 300)
'''


def test_az_or_maga_eszleli_a_rovid_korlatot():
    eltresek = _eltresek({"tests/app/minta.py": _ROSSZ})
    assert {(e.tipus, e.sor) for e in eltresek} == {("helyi", 2), ("hivas", 7)}


def test_az_or_nem_jelez_a_tiz_masodperces_korlatra_es_a_fix_varakozasra():
    assert _eltresek({"tests/app/minta.py": _JO}) == []


_BURKOLO = '''
from tests.support.varakozas import var_feltetelre


def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def teszt(qt_app):
    _var(qt_app, lambda: True, 2.0)
'''


def test_az_or_eszleli_a_kozos_segedet_hivo_burkolot():
    eltresek = _eltresek({"tests/app/minta.py": _BURKOLO})
    assert {(e.tipus, e.sor) for e in eltresek} == {("helyi", 5), ("hivas", 10)}


_SEGED = '''
def _var(qt_app, feltetel, ms: int = 10000) -> bool:
    return feltetel()
'''


def test_az_or_nem_keveri_a_masik_modul_azonos_nevu_segedjet():
    minta = {
        "tests/app/a_seged.py": _SEGED,
        "tests/app/b_teszt.py": (
            "from tests.support.collage_wiring_985 import _var\n\n\n"
            "def teszt(qt_app):\n    _var(qt_app, lambda: True, 30.0)\n"
        ),
    }
    assert _eltresek(minta) == []


def test_az_or_eszleli_az_importalt_segedet_rovid_literallal():
    minta = {
        "tests/app/a_seged.py": _SEGED,
        "tests/app/b_teszt.py": (
            "from tests.app.a_seged import _var\n\n\n"
            "def teszt(qt_app):\n    _var(qt_app, lambda: True, 3000)\n"
        ),
    }
    assert [(e.fajl, e.tipus) for e in _eltresek(minta)] == [("tests/app/b_teszt.py", "hivas")]


def test_az_or_eszleli_a_modul_aliason_at_hivott_segedet():
    minta = {
        "tests/app/a_seged.py": _SEGED,
        "tests/app/b_teszt.py": (
            "from tests.app import a_seged as _seg\n\n\n"
            "def teszt(qt_app):\n    _seg._var(qt_app, lambda: True, ms=3000)\n"
        ),
    }
    assert [(e.fajl, e.tipus) for e in _eltresek(minta)] == [("tests/app/b_teszt.py", "hivas")]
