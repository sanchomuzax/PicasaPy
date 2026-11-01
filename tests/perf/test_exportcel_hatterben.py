"""Az exportcélok ellenőrzése nem tartja vissza az indítóképernyőt.

A tulajdonos gépén (2026-11-01) az „Exportmappák ellenőrzése” percekig futott
a NAS-on lévő exportmappákon, és az indítóképernyő addig nem tűnt el. A lépés
ezért a könyvtár első szinkronja után, külön munkacsoportban fut.
"""

from __future__ import annotations

import ast
import inspect

from picasapy.app import application


def _run_fa() -> ast.AST:
    return ast.parse(inspect.getsource(application.run))


def _fuggveny(fa: ast.AST, nev: str) -> ast.FunctionDef:
    return next(
        node for node in ast.walk(fa)
        if isinstance(node, ast.FunctionDef) and node.name == nev
    )


def _enqueue_kulcsok(fa: ast.AST, munkacsoport: str) -> list[str]:
    hivasok = [
        node for node in ast.walk(fa)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "enqueue"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == munkacsoport
    ]
    return [
        kw.value.value
        for hivas in hivasok
        for step in ast.walk(hivas)
        if isinstance(step, ast.Call)
        and isinstance(step.func, ast.Name)
        and step.func.id == "StartupMaintenanceStep"
        for kw in step.keywords
        if kw.arg == "key" and isinstance(kw.value, ast.Constant)
    ]


def test_az_exportcelok_nem_az_inditokepernyot_visszatarto_csoportban_vannak():
    fa = _run_fa()
    assert "exported_folders" not in _enqueue_kulcsok(fa, "initial")
    assert _enqueue_kulcsok(fa, "exported") == ["exported_folders"]


def test_az_exportcel_csoport_a_szinkron_vegere_indul():
    fa = _run_fa()
    hatterben = _fuggveny(fa, "_exportcelok_hatterben")
    assert _enqueue_kulcsok(hatterben, "exported") == ["exported_folders"]
    forras = ast.unparse(fa)
    assert "syncFinished.connect(_exportcelok_hatterben" in forras


def test_az_exportcel_csoport_vege_frissiti_a_nezeteket():
    befejezes = _fuggveny(_run_fa(), "_maintenance_batch_finished")
    forras = ast.unparse(befejezes)
    assert "'exported'" in forras or '"exported"' in forras
    assert "syncFinished.emit()" in forras
