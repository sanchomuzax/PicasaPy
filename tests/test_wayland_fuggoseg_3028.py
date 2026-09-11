"""#3028: a Qt 6 wayland-bővítménye szerepel az EGYETLEN csomaglistában.

A lista a `packaging/qt-runtime-deps.txt`; a CI, a bootstrap és minden
telepítő ezt olvassa (`scripts/print_dependencies.py`). A tulajdonos gépén
a hiánya miatt nem indult el a program.

A tétel a `[csak-disztribucios]` szakaszba tartozik: a pip-es PySide6
kerék a saját bővítményeit hozza, a disztribúciós csomag viszont külön
csomagra bontja — és a CI a KÖTELEZŐ listát telepíti `apt-get install`-lal,
ahol egy fölös tétel az egész lépést elviszi (#1472).
"""

from __future__ import annotations

from pathlib import Path

_LISTA = Path(__file__).resolve().parents[1] / "packaging" / "qt-runtime-deps.txt"


def _szakaszok() -> tuple[list[str], list[str]]:
    kotelezo: list[str] = []
    disztros: list[str] = []
    cel = kotelezo
    for sor in _LISTA.read_text(encoding="utf-8").splitlines():
        sor = sor.strip()
        if sor.startswith("[csak-disztribucios]"):
            cel = disztros
            continue
        if not sor or sor.startswith("#"):
            continue
        cel.append(sor)
    return kotelezo, disztros


def test_a_wayland_bovitmeny_szerepel():
    _kotelezo, disztros = _szakaszok()
    assert "qt6-wayland" in disztros, (
        "wayland-asztalon enélkül el sem indul a program (#3028)"
    )


def test_NEM_a_kotelezo_szakaszban_van():
    """A CI ubuntu-futtatója pip-es PySide6-tal megy: ott fölös, és egy
    fölös tétel az egész `apt-get install` lépést elviszi (#1472)."""
    kotelezo, _disztros = _szakaszok()
    assert "qt6-wayland" not in kotelezo
