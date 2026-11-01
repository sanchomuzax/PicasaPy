"""#6392: a `src/picasapy/` minden nem-Python adatfájlja bekerül a windowsos csomagba.

A spec a csomagon belüli adatot mintákkal (`collect_data_files(includes=…)`)
és kifejezett mappákkal (`adatok = [...]`) gyűjti. A HTML-export sablonjai
(`webexport/templates/`, `.html`/`.tpl`/`.css`/`.svg`/`.xml`) egyik szabályba
sem estek bele, ezért a telepített programban üres volt a sablonlista. Ez az
őr minden adatfájlra megnézi, hogy valamelyik szabály lefedi-e.
"""

from __future__ import annotations

import ast
import fnmatch
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[2]
_CSOMAG = _GYOKER / "src" / "picasapy"
_SPEC = _GYOKER / "packaging" / "windows" / "picasapy.spec"


def _spec_szabalyok() -> tuple[list[str], list[str]]:
    """(includes-minták, kifejezetten felvett mappák a csomagon belül)."""
    fa = ast.parse(_SPEC.read_text(encoding="utf-8"))
    mintak: list[str] = []
    mappak: list[str] = []
    for csomopont in ast.walk(fa):
        if isinstance(csomopont, ast.Call) and getattr(csomopont.func, "id", "") == "collect_data_files":
            for kw in csomopont.keywords:
                if kw.arg == "includes":
                    mintak += [elem.value for elem in kw.value.elts]
        if isinstance(csomopont, ast.Tuple) and len(csomopont.elts) == 2:
            cel = csomopont.elts[1]
            if isinstance(cel, ast.Constant) and isinstance(cel.value, str) and cel.value.startswith("picasapy/"):
                mappak.append(cel.value.removeprefix("picasapy/"))
    return mintak, mappak


def _adatfajlok() -> list[str]:
    return sorted(
        p.relative_to(_CSOMAG).as_posix()
        for p in _CSOMAG.rglob("*")
        if p.is_file()
        and p.suffix not in {".py", ".pyc"}
        and "__pycache__" not in p.parts
        and not p.name.startswith(".")
    )


def test_az_or_talal_adatfajlt_es_szabalyt() -> None:
    mintak, mappak = _spec_szabalyok()
    assert mintak and mappak, "a spec szabályait nem sikerült kiolvasni: az őr vak"
    assert _adatfajlok(), "nincs adatfájl: az őr vak"


def test_minden_adatfajl_bekerul_a_csomagba() -> None:
    mintak, mappak = _spec_szabalyok()
    kimaradt = [
        fajl
        for fajl in _adatfajlok()
        if not any(fajl.startswith(mappa.rstrip("/") + "/") for mappa in mappak)
        and not any(fnmatch.fnmatch(fajl, minta) or fnmatch.fnmatch(fajl, minta.removeprefix("**/")) for minta in mintak)
    ]
    assert not kimaradt, (
        f"{len(kimaradt)} adatfájl kimaradna a windowsos csomagból "
        f"(#6392), pl.: {', '.join(kimaradt[:5])}"
    )


def test_a_html_sablonok_mappaja_a_csomagban_van() -> None:
    _mintak, mappak = _spec_szabalyok()
    assert "webexport/templates" in mappak
