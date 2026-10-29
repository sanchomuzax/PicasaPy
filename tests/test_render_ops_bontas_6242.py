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

# A bontás előtti ops.py 24 függvényének/osztályának AST-lenyomata.
# Az attribútumok (sor- és oszlopszám) kimaradnak; a teljes kifejezésfa,
# dekorátorok, annotációk, alapértékek és törzsek részei az összevetésnek.
_EREDETI_AST_SHA256 = {
    "_rect_to_pixels": "2e06bb5e609e63b41d50337ef689ed6075b5be26eecf035ded14f396909cae1a",
    "apply_crop": "e4ce60b6592c52b474286ee331705615e7b87d207a1c67ed7f5dd9c413d83677",
    "tilt_scale": "47a551a28edb858d8df4892b2da2c6f30d4953bfe2406e7a96b15c9f42e1bc2f",
    "tilt_matrix": "19c0061c5b74083e2eac9e12d1200f5a265b3bf8f7a5cd5950168478c074e3e6",
    "apply_tilt": "08c59e5f23bc548bcfb1373232f330ad9e094ecd465452b8aeac31e09226038e",
    "_levels_clip_threshold": "f29941f32b8c6d9ee98ce2baaf5abd054dcb721199ab63ebee50b2dfbc3487f3",
    "_channel_histograms": "8d2a357f2e4b13e5ccef27aaaba1872da85c70e2efa0c10c9d2e1a2e1f6691c5",
    "_native_clip_points": "eb034f64214dc5801547f92403830e1654af66896226463fed8de2bfe176b314",
    "_native_levels_lut": "9d6b4719ef503ea03988f3ef6eed2e617b554fcb272eb0a128706327b130c0b5",
    "_union_black_white_point": "63e0f83fb33212ae71df3e029144bd47391f7e7bf4f87c914b239ec0a7d59d25",
    "apply_autolight": "35b7ca6fcfebdaa3eff4f703640c4ac8878605e0c415fd11bc82a515977e8a7f",
    "_analysis_region": "6688e7061645691bee7726054efc43af58a1fe06df30fb6c2e92f711ce9e6eb7",
    "_channel_black_white_points": "ced90449491ad04cbe889ab0f5064ac3d974e7ed53f336ea9e67d5960611c172",
    "autocolor_gains": "4162337ddb0e11f32b02c978f77fedfc0c38b74c06187807ee4962b28bf55bef",
    "apply_autocolor": "20147077baca400f1f0103bd021c47602536e46c505dcb241ab16c56c333befe",
    "_blend_clip_points": "55ac7404125dc69f59bee9b26a48873dc54bd9f0b7719eeccc2a9c182b193546",
    "apply_channel_levels_stretch": "497d6c560d092f8004bc7b0aca196d12fd30a66a1d79c092b80286dafda3ecaf",
    "apply_enhance": "47d903c5438e037e13db98ab59ba48e665a3f9bc3f8cef4e9288071f1ee0ab2d",
    "apply_autocontrast": "cb6f44056a0b23b79ac7be800df9026c2b1630d48ffc124e519fba360d623046",
    "apply_redeye": "50f53974c9e051babc3f34ff414fccac3f6206b58ef0cf410e9e8213a2b081d2",
    "_redeye_pixel_mask": "731061242ada5cb4dcd7f8d0780788ca780d54a82faa2a0d6236100dee064318",
    "_eye_circle_mask": "15df3f31a23c627cae97c6fdc5df6e25e8a15dfd0ca02942bb6698266144bb19",
    "_eye_red_pixel_mask": "36e0f49ff25b72b3e5f516817e3cf696498675eb74fd389a49b2e2b3d3bceab3",
    "count_redeye_spots": "580e03ff85e5a8a597f0f1297ade607a618372add01ecda99dfd63aa790724b4",
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


def _ast_sha256(node: ast.AST) -> str:
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def _fuggveny_ast_kivonat() -> dict[str, str]:
    lenyomatok: dict[str, str] = {}
    fajlok = (_RENDER / "ops.py", *(_RENDER / nev for nev in _UJ_MODULOK))
    for fajl in fajlok:
        if not fajl.is_file():
            continue
        fa = ast.parse(fajl.read_text(encoding="utf-8"), filename=str(fajl))
        for node in fa.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert node.name not in lenyomatok, f"többszörös definíció: {node.name}"
                lenyomatok[node.name] = _ast_sha256(node)
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
