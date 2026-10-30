"""A renderműveletek bontása őrizze meg a régi API-t és az AST-ket (#6242)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from picasapy.render import ops


_GYOKER = Path(__file__).resolve().parents[1]
_RENDER = _GYOKER / "src" / "picasapy" / "render"
_UJ_MODULOK = (
    "ops_geometry.py",
    "ops_levels_analysis.py",
    "ops_levels.py",
    "ops_redeye.py",
)

# A bontás előtti ops.py 24 függvényének/osztályának forrásszöveg-lenyomata
# (a dekorátoroktól a záró sorig). Az ast.dump Python-verziónként eltér
# (helyben 3.13, a CI-n 3.12), a forrás szövege nem; a bontás bájtra azonos.
_EREDETI_AST_SHA256 = {
    "_rect_to_pixels": "31bd6a73ec7150988fc2a5ac3319dde76d4e49a32228b3535521b62c8ba10fbc",
    "apply_crop": "2b4e10ea76a565092c061d25154263ed0eb383ee82d204f4dcc308afc8551d20",
    "tilt_scale": "4ae0e3bb8c51cc4831a065ccec86a1b4e1073b799634642194115e6692d8be9a",
    "tilt_matrix": "4e318245d110848b38a90ac27bdd526bab5b03f2f8a2c91f6863cb8559fb316b",
    "apply_tilt": "08d048b4c6857bd4eeba724a26a37b8cb3e204487efe9e7d6f3e54c1a7cd7453",
    "_levels_clip_threshold": "6f0ea37d82eab40b2d996f80f7d6f37a5be69993bb4b38e53d8d66fae2c72df0",
    "_channel_histograms": "0b86fa89217ac0408af32aafe6d4714c3fb55740928fc61b4001120d4bb09e18",
    "_native_clip_points": "8adf98046520c9eda470fb5e9c45258e4e4959eddbe72b04c3dece152c0f94fc",
    "_native_levels_lut": "433d4d7d396def4beb09780717dd1b0ad07964fd73e9691ab9f8e72514cfe6b9",
    "_union_black_white_point": "65e126ef5cab343f94ba20fc21f62e0bc964abacba2182b31c21c5c5bf5a0da1",
    "apply_autolight": "2202af29603b7da7bf693fe0f170d0d6027e13d011253cd8c0fd2c8f314d6417",
    "_analysis_region": "b7dc84344dd79f4c510e92f2e8526e95570b6dc0709af2c59c379472754c990c",
    "_channel_black_white_points": "6baf8e6e6ecaf100dc4d444e40a1047a4552a1b35ceae09bae4e82e406ec4bf6",
    "autocolor_gains": "f21696913c68e6ff2ad27c846c8229904567f3ff8d14b47319472edddacdedca",
    "apply_autocolor": "c6388409c3cef414878341ed035010be28557f2db06dde860c71dc10d419f9d1",
    "_blend_clip_points": "2ef1b229151f0db666efcf21e6ba54288a7cf7fe31c19df6ae47bc30d9e29b9b",
    "apply_channel_levels_stretch": "bc204e5a54fd338459f45c27a10ca818d5356dc10130dfb6d47eee53ee6c017b",
    "apply_enhance": "fd11f32ffe995afae1947c52301b1445146c36bdb09aa1768fe48ea5e97017d5",
    "apply_autocontrast": "78ccce24de7e658b5f379f9513448dd22404710b8eef6e4a670610e7138d3774",
    "apply_redeye": "cb624d1a2ecfd0ecba6b7c635bb8bb2b73ca01a309bf1d3d45a7fb3574f01030",
    "_redeye_pixel_mask": "6b9ed011bdf73d09bced9785412cac8015c8ebcbe9650f5282bcf9243a585857",
    "_eye_circle_mask": "97a6adc0f4362c0056ca7c70555c50b72892d64f716e1f8d067564af915f8775",
    "_eye_red_pixel_mask": "878fa1268882e377411cad9e8d96986474637927672d3c86af9184f26382fa02",
    "count_redeye_spots": "766b64a56cc22010854e485ffb230339dc70928ff8a60c744a02715d4297be5c",
}

_EREDETI_NYILVANOS_NEVEK = {
    "annotations",
    "Rect64",
    "apply_autocolor",
    "apply_autocolor_matrix",
    "apply_autocontrast",
    "apply_autolight",
    "apply_channel_levels_stretch",
    "apply_channel_luts",
    "apply_crop",
    "apply_enhance",
    "apply_lut",
    "apply_redeye",
    "apply_tilt",
    "autocolor_gains",
    "autocolor_matrix_16_16",
    "count_redeye_spots",
    "cv2",
    "estimate_illuminant",
    "fixpontos_bilinearis",
    "lut_ramp",
    "math",
    "np",
    "tilt_matrix",
    "tilt_scale",
    "validate_image",
}


def _forras_sha256(forras: str, node: ast.AST) -> str:
    sorok = forras.splitlines()
    eleje = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno])
    return hashlib.sha256("\n".join(sorok[eleje - 1 : node.end_lineno]).encode()).hexdigest()


def _fuggveny_ast_kivonat() -> dict[str, str]:
    lenyomatok: dict[str, str] = {}
    fajlok = (_RENDER / "ops.py", *(_RENDER / nev for nev in _UJ_MODULOK))
    for fajl in fajlok:
        if not fajl.is_file():
            continue
        forras = fajl.read_text(encoding="utf-8")
        fa = ast.parse(forras, filename=str(fajl))
        for node in fa.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert node.name not in lenyomatok, f"többszörös definíció: {node.name}"
                lenyomatok[node.name] = _forras_sha256(forras, node)
    return lenyomatok


def test_a_bontas_elotti_fuggvenyek_ast_je_valtozatlan() -> None:
    aktualis = _fuggveny_ast_kivonat()
    assert aktualis == _EREDETI_AST_SHA256, (
        "a függvények/osztályok AST-je megváltozott vagy hiányzik: "
        f"{sorted(set(aktualis) ^ set(_EREDETI_AST_SHA256))}; "
        f"eltérő lenyomat: {sorted(n for n in aktualis.keys() & _EREDETI_AST_SHA256.keys() if aktualis[n] != _EREDETI_AST_SHA256[n])}"
    )


def test_az_ops_homlokzat_megtartja_a_regi_neveket() -> None:
    for nev in _EREDETI_NYILVANOS_NEVEK | set(_EREDETI_AST_SHA256):
        assert hasattr(ops, nev), f"hiányzó régi ops-név: {nev}"
    assert {nev for nev in vars(ops) if not nev.startswith("_")} == _EREDETI_NYILVANOS_NEVEK


def test_a_modulok_es_a_homlokzat_400_sor_alatt_maradnak() -> None:
    fajlok = (_RENDER / "ops.py", *(_RENDER / nev for nev in _UJ_MODULOK))
    hianyzik = [fajl.name for fajl in fajlok if not fajl.is_file()]
    assert not hianyzik, f"hiányzó bontott modul(ok): {hianyzik}"
    tulhosszuak = {
        fajl.name: len(fajl.read_text(encoding="utf-8").splitlines())
        for fajl in fajlok
        if len(fajl.read_text(encoding="utf-8").splitlines()) >= 400
    }
    assert not tulhosszuak, f"a bontás moduljai elérték a 400 soros határt: {tulhosszuak}"


def test_a_histogram_patchpontok_tovabbra_is_az_ops_nevtereben_elnek() -> None:
    assert ops._channel_histograms.__globals__ is vars(ops)
    assert "_HISZTOGRAM_SAV_KEPPONT" in vars(ops)
    assert "cv2" in vars(ops)
