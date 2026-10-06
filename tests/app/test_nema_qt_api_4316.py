"""#4316: a Pythonból használt segédtagok ne legyenek fölöslegesen Qt API-k."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


_GYOKER = Path(__file__).resolve().parents[2]
_TAGOK = {
    "src/picasapy/app/effects_controller.py": {
        "canUndoPasteEffects",
        "copyEffects",
        "hasEffectsClipboard",
        "undoPasteEffects",
    },
    "src/picasapy/app/collage_controller.py": {"collageFrameCenter"},
    "src/picasapy/app/create_controller.py": {"collageSeed"},
    "src/picasapy/app/collage_save.py": {"collageTitle", "setCollageSavedPath"},
    "src/picasapy/app/tray_controller.py": {"expandFolderInTray"},
    "src/picasapy/app/geo_controller.py": {"locationOfRow"},
    "src/picasapy/app/fileops_controller.py": {"movePhoto"},
    "src/picasapy/app/controller.py": {"setFolderDescription"},
}

_NEMA_JELZESEK = {
    "src/picasapy/app/effects_controller.py": {"effectsClipboardChanged"},
    "src/picasapy/app/collage_controller.py": {"collageFrameCenterChanged"},
    "src/picasapy/app/create_controller.py": {"collageSeedChanged"},
    "src/picasapy/app/collage_save.py": {"collageTitleChanged"},
}


def _qt_tagelt_fuggvenyek(forras: Path) -> set[str]:
    fa = ast.parse(forras.read_text(encoding="utf-8"))
    talalatok = set()
    for csomopont in ast.walk(fa):
        if not isinstance(csomopont, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for diszito in csomopont.decorator_list:
            nev = diszito.func.id if isinstance(diszito, ast.Call) else None
            if isinstance(diszito, ast.Name):
                nev = diszito.id
            if nev in {"Property", "Slot"}:
                talalatok.add(csomopont.name)
    return talalatok


def _qt_jelzesek(forras: Path) -> set[str]:
    fa = ast.parse(forras.read_text(encoding="utf-8"))
    return {
        csomopont.targets[0].id
        for csomopont in ast.walk(fa)
        if isinstance(csomopont, ast.Assign)
        and csomopont.targets
        and isinstance(csomopont.targets[0], ast.Name)
        and isinstance(csomopont.value, ast.Call)
        and isinstance(csomopont.value.func, ast.Name)
        and csomopont.value.func.id == "Signal"
    }


@pytest.mark.parametrize(
    ("modul", "nevek"),
    _TAGOK.items(),
    ids=lambda ertek: ertek if isinstance(ertek, str) else None,
)
def test_a_nem_qml_tagok_nincsenek_qt_api_kent_kiteve(modul, nevek):
    """A Python segédút megmarad, de a 12 elárvult Qt-dekorátor nem."""
    qt_tageltek = _qt_tagelt_fuggvenyek(_GYOKER / modul)
    assert not nevek & qt_tageltek, (
        f"a {modul} még Qt/QML API-ként teszi közzé ezeket: "
        f"{sorted(nevek & qt_tageltek)}"
    )


@pytest.mark.parametrize(
    ("modul", "nevek"),
    _NEMA_JELZESEK.items(),
    ids=lambda ertek: ertek if isinstance(ertek, str) else None,
)
def test_a_kikerult_propertykhez_nem_marad_nema_qt_jelzes(modul, nevek):
    """A Qt property notify jelzéseit együtt kell kivenni a propertyvel."""
    qt_jelzesek = _qt_jelzesek(_GYOKER / modul)
    assert not nevek & qt_jelzesek, (
        f"a {modul} még nem fogadott Qt-jelzést tesz közzé: "
        f"{sorted(nevek & qt_jelzesek)}"
    )
