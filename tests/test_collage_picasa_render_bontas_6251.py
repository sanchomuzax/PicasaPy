"""A Picasa-kollázs renderelőjének bontása őrizze meg az API-t és a forrást."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import picasapy.collage.picasa_render as picasa_render


_GYOKER = Path(__file__).resolve().parents[1]
_COLLAGE = _GYOKER / "src" / "picasapy" / "collage"
_UJ_MODULOK = (
    "picasa_render_settings.py",
    "picasa_render_placement.py",
    "picasa_render_make.py",
)
_MOZGATOTT = {
    "PicasaCollageSettings": "picasa_render_settings.py",
    "_canvas": "picasa_render_settings.py",
    "shadow_for_settings": "picasa_render_settings.py",
    "_aspects": "picasa_render_placement.py",
    "layout_nodes_for_aspects": "picasa_render_placement.py",
    "layout_nodes": "picasa_render_placement.py",
    "_multiexp_node": "picasa_render_placement.py",
    "make_picasa_collage": "picasa_render_make.py",
}

# Az eredeti picasa_render.py függvényeinek és osztályának UTF-8 forrásbájtjai
# a dekorátortól (ha volt) a záró sorig. A hash nem Python AST-formátumfüggő.
_EREDETI_FORRAS_SHA256 = {
    "PicasaCollageSettings": "63d8781d3cf9f81f4eb007acd3065e39ac6988b3f444e637aaa940f1481c13c0",
    "_canvas": "bea6576c81e69ba9a10c3021418e275cc433bd50369e04034798cc23c99003c1",
    "shadow_for_settings": "d021f0a232af7fbd0d848e4cdd7c14e8cddfdd3c1d94fde7783e037de6ba8060",
    "_aspects": "d536720fccfbd598a0f3cb15e26fa951fc60f4a233ea52b86202d72c4f51f052",
    "render_nodes": "8405742f1e4a350ce429e967dd77be56345e7ac60b4e8da67f852c7cac472768",
    "_draw_contact_header": "7ca831f9fc4e5ed60cc0d9e7084c3fb045bd50573ad55b1b5976779914e8280d",
    "layout_nodes_for_aspects": "0b85b5e09b4c7c5475d5505a4498dee7a08c7e9de3f61dee6bdb4c1e37e42011",
    "layout_nodes": "6d9f23cb2a33554512b1f26077933e777960c3853358854a1bccda6e4e279ff1",
    "_multiexp_node": "2a2e59d7eff5d30bec0287366b1c87129e0f764c4117666a7dd762d0974e6aba",
    "make_picasa_collage": "8ef3b799d937dfa361e4c6d10900b1fda1eee89547ae77e434cc2f4318fbc03b",
}

_REGI_NYILVANOS_NEVEK = {
    "BACKGROUND_DIM_ALPHA",
    "BACKGROUND_DIM_FACTOR",
    "BORDER_THEMES",
    "COLLAGE_THEMES",
    "CONTACTSHEET",
    "CollageNode",
    "CollageReport",
    "FRAMEGRID",
    "Image",
    "ImageDraw",
    "MULTIEXP",
    "MsvcRandom",
    "NOBORDER",
    "PICTUREGRID",
    "PICTUREPILE",
    "POLAROID_CSEMPE_ARANY",
    "POLAROID_HEIGHT_RATIO",
    "POLAROID_WIDTH_RATIO",
    "Path",
    "PicasaCollageSettings",
    "REGULARGRID",
    "SHEET_UNITS",
    "Sequence",
    "ShadowParams",
    "THEME_CAPABILITIES",
    "annotations",
    "blend_multi_exposure",
    "border_growth",
    "contact_sheet_cell_scale",
    "cv2",
    "dataclass",
    "draw_nodes",
    "fit_to_frame",
    "layout_nodes",
    "layout_nodes_for_aspects",
    "logger",
    "logging",
    "make_picasa_collage",
    "np",
    "outer_box",
    "pack",
    "pack_with_center",
    "photo_box",
    "picasa_round",
    "pixels_to_sheet",
    "regular_grid_rects",
    "regular_grid_shape",
    "render_nodes",
    "shadow_for_settings",
    "shadow_params",
    "sheet_to_pixels",
}
_REGI_ALL = [
    "SHEET_UNITS",
    "CollageNode",
    "PicasaCollageSettings",
    "border_growth",
    "contact_sheet_cell_scale",
    "layout_nodes",
    "layout_nodes_for_aspects",
    "make_picasa_collage",
    "outer_box",
    "photo_box",
    "pixels_to_sheet",
    "render_nodes",
    "shadow_for_settings",
    "sheet_to_pixels",
]


def _forraslenyomatok() -> dict[str, str]:
    lenyomatok: dict[str, str] = {}
    fajlok = (_COLLAGE / "picasa_render.py", *(_COLLAGE / n for n in _UJ_MODULOK))
    for fajl in fajlok:
        if not fajl.is_file():
            continue
        nyers = fajl.read_bytes()
        sorok = nyers.splitlines(keepends=True)
        fa = ast.parse(nyers.decode("utf-8"), filename=str(fajl))
        for node in fa.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name not in _EREDETI_FORRAS_SHA256:
                continue
            assert node.name not in lenyomatok, f"többszörös definíció: {node.name}"
            kezdo = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            reszlet = b"".join(sorok[kezdo - 1 : node.end_lineno])
            lenyomatok[node.name] = hashlib.sha256(reszlet).hexdigest()
    return lenyomatok


def test_a_bontas_megorizza_az_api_t_a_forrast_es_a_patchpontot(monkeypatch) -> None:
    hianyzo = [nev for nev in _UJ_MODULOK if not (_COLLAGE / nev).is_file()]
    assert not hianyzo, f"hiányzó bontott modul(ok): {hianyzo}"

    sorok = {
        nev: len((_COLLAGE / nev).read_text(encoding="utf-8").splitlines())
        for nev in _UJ_MODULOK
    }
    tul_hosszu = {nev: db for nev, db in sorok.items() if db >= 400}
    assert not tul_hosszu, f"a bontott modulok elérték a 400 soros határt: {tul_hosszu}"

    nevek = {nev for nev in vars(picasa_render) if not nev.startswith("_")}
    assert nevek == _REGI_NYILVANOS_NEVEK, (
        f"megváltozott a régi nyilvános névtér: hiányzik={sorted(_REGI_NYILVANOS_NEVEK - nevek)}, "
        f"többlet={sorted(nevek - _REGI_NYILVANOS_NEVEK)}"
    )
    assert picasa_render.__all__ == _REGI_ALL

    for nev, modul in _MOZGATOTT.items():
        nyers = (_COLLAGE / modul).read_bytes()
        fa = ast.parse(nyers.decode("utf-8"), filename=modul)
        assert any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == nev
            for node in fa.body
        ), f"{nev} nem a kijelölt új modulba került ({modul})"

    aktualis = _forraslenyomatok()
    assert aktualis == _EREDETI_FORRAS_SHA256, (
        "a bontás előtti függvény/osztály forrása megváltozott vagy hiányzik: "
        f"hiányzik={sorted(set(_EREDETI_FORRAS_SHA256) - set(aktualis))}; "
        f"eltérő={[n for n in aktualis.keys() & _EREDETI_FORRAS_SHA256.keys() if aktualis[n] != _EREDETI_FORRAS_SHA256[n]]}"
    )

    hivasok: list[int] = []
    monkeypatch.setattr(
        picasa_render,
        "_draw_contact_header",
        lambda _canvas, _settings, count=0: hivasok.append(count),
    )
    picasa_render.render_nodes(
        [],
        picasa_render.PicasaCollageSettings(
            theme=picasa_render.CONTACTSHEET, width=32, height=32
        ),
    )
    assert hivasok == [0], "a render_nodes nem a régi modul patchpontján át hívta a fejlécet"
