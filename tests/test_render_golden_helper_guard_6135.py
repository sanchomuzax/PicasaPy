"""A képpontos QML-golden tesztek közös betű- és szövegsegédet használnak."""

from __future__ import annotations

import ast
import re
from pathlib import Path


_QML_TESTS = Path(__file__).parent / "app" / "qml_functional"
_KOTELEZO_TESZTEK = (
    "test_tray_bar_render_6050.py",
    "test_folder_pane_render_6019.py",
    "test_create_dialogs_render_6051.py",
    "test_unnamed_faces_view_rendered_6077.py",
    "test_main_toolbar_components_6103.py",
)
#: A rögzített betűre még át nem állt teszt -> a jegy, amely átállítja.
#: A közös szövegsegédet ezek is kötelesek használni.
_BETU_ATALLAS_HATRA = {"test_tray_bar_render_6050.py": "#6148"}


def _pixel_golden_tesztek() -> list[tuple[Path, str]]:
    """A saját golden könyvtárból képet olvasó, pixeleket hasonlító tesztek."""
    talalatok = []
    for fajl in sorted(_QML_TESTS.glob("test_*.py")):
        forras = fajl.read_text(encoding="utf-8")
        sajat_golden = (
            "Path(__file__).parent" in forras
            and re.search(r"['\"]golden['\"]", forras)
        )
        kepet_rogzit = "grabWindow(" in forras or "grabToImage(" in forras
        pixelt_hasonlit = any(
            jel in forras
            for jel in (
                "np.any(",
                "np.count_nonzero(",
                "np.array_equal(",
                ".pixel(",
                ".pixelColor(",
            )
        )
        if sajat_golden and kepet_rogzit and pixelt_hasonlit:
            talalatok.append((fajl, forras))
    return talalatok


def test_minden_golden_render_teszt_kozos_segedet_hasznal():
    pixel_goldenek = _pixel_golden_tesztek()
    talalat_nevek = {fajl.name for fajl, _forras in pixel_goldenek}
    hianyzo_celok = sorted(set(_KOTELEZO_TESZTEK) - talalat_nevek)
    assert not hianyzo_celok, (
        "A kötelező képpontos golden-tesztek eltűntek vagy már nem felismerhetők: "
        + ", ".join(hianyzo_celok)
    )

    hianyos = []
    for fajl, forras in pixel_goldenek:
        fa = ast.parse(forras, filename=str(fajl))
        helper_nevek = {
            nev.asname or nev.name
            for csomopont in ast.walk(fa)
            if isinstance(csomopont, ast.ImportFrom)
            and csomopont.module == "tests.support.render_test_helpers"
            for nev in csomopont.names
            if nev.name == "is_text_item"
        }
        helper_hasznalat = any(
            isinstance(csomopont, ast.Call)
            and isinstance(csomopont.func, ast.Name)
            and csomopont.func.id in helper_nevek
            for csomopont in ast.walk(fa)
        )
        rogzitett_betu_fixture = any(
            isinstance(csomopont, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(
                argument.arg == "rogzitett_betu"
                for argument in [
                    *csomopont.args.posonlyargs,
                    *csomopont.args.args,
                    *csomopont.args.kwonlyargs,
                ]
            )
            for csomopont in ast.walk(fa)
        )
        betu_rendben = rogzitett_betu_fixture or fajl.name in _BETU_ATALLAS_HATRA
        if not helper_nevek or not helper_hasznalat or not betu_rendben:
            hianyos.append(fajl.name)

    assert not hianyos, (
        "A golden-képet összevető teszt közös is_text_item segédet és "
        "rogzitett_betu fixture-t köteles használni: " + ", ".join(hianyos)
    )
