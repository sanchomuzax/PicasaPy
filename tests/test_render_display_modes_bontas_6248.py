"""A megjelenítési módok modulbontásának szerkezeti őrei (#6248)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from picasapy.render import display_modes


_GYOKER = Path(__file__).resolve().parents[1]
_RENDER = _GYOKER / "src" / "picasapy" / "render"
_MODULOK = ("display_modes.py", "display_mode_pixels.py", "display_mode_dither.py")

# A régi display_modes.py minden nyilvános neve maradjon importálható.
_NYILVANOS_NEVEK = {
    "annotations",
    "cv2",
    "np",
    "OVERFLOW_MODE",
    "OVERFLOW_MARK_RGB",
    "PROJECTOR_MODE",
    "LCD_MODE",
    "LINEAR_GAMMA_MODE",
    "MAC_MODE",
    "MAC_GAMMA_SCREENSHOT_PAIR",
    "BW_MODE",
    "SEPIA_MODE",
    "LUMA_WEIGHTS_RGB",
    "SEPIA_LIGHTEN_MULTIPLIER",
    "SEPIA_BLEND_RGB",
    "PROJECTOR_MULTIPLIER",
    "LCD_MULTIPLIER",
    "MAC_GAMMA_LUT",
    "LINEAR_GAMMA_GAMMA",
    "LINEAR_GAMMA_LUT",
    "DITHER16_SEED",
    "PicasaDitherGenerator",
    "PIXEL_AFFECTING_MODES",
    "display_mode_changes_pixels",
    "apply_dither16",
    "mark_overflow",
    "darken",
    "apply_linear_gamma",
    "apply_mac_gamma",
    "luma",
    "apply_display_bw",
    "apply_display_sepia",
    "apply_display_mode",
}

# A bontás előtti függvények/osztály forrásszövegének SHA-256 lenyomata,
# a dekorátortól a záró sorig. AST-t csak a forrássorok megtalálására használ.
_FORRASHASH = {
    "PicasaDitherGenerator": "01f37addf0388e06a710d37072a39958fb9d1b1eeec32b0808e2f33780c064cd",
    "_luma_tabla": "1e81ce2d11944577b5018fa87bd455ad2fa65abc7ba5eb7ccd0f3a7e212dfe3a",
    "_szepia_tabla": "20ea3f3e60dd2496cfaccce8457342483dd003bc82ae2e08d0f5f5f55ab73da0",
    "display_mode_changes_pixels": "9757440b10b794d28e6fddef9a0e33c97daddd7f60d10a582d688d95c72db2b4",
    "apply_dither16": "c1c5318dad8ea196ba5469aca06d9a38a943241f134cdb351c22089dd29d3312",
    "mark_overflow": "f8f8a70b859a9eb22586b75fe933baaa8beb17f579dd2e798470045ba64b9991",
    "_rgb_kep_e": "00e22c7029cc379492209ade1695458cdec0aa0192389e25495a7cfe5dd23407",
    "_tablat_alkalmaz": "fbc5e7a5dd0d2d682440acaabb85662e398760461c2f66454bb2058ec9e1e476",
    "darken": "77d08d94e67f8885ecd78434843edd9ea498b371521005bfabea1be4bad5f97f",
    "apply_linear_gamma": "8667f34d8cac65f6cbcfdf737476c9a405a2dbbc639324ed00c100aab18f1984",
    "apply_mac_gamma": "f028837675be73dd9ab0baee428491dead2363e4aea7ade8e9edc3fc48b06680",
    "luma": "093f46a448f6a28e7767a4895d722f955e72556780435f8ed2395d4549affa76",
    "apply_display_bw": "562c9c45e53fbfcd87e948cce082d316f1f0c777f27e3ba9ce394c164de2da5f",
    "apply_display_sepia": "ab02800065c0a420c55907d294a92eebe42050dc8be2e97552057149b126f858",
    "apply_display_mode": "d968e460d6b747f4b98b2adff27a35c5c3c187e819696d06ad4b9af9abf6af3a",
}

_FORRASFAJL = {
    "PicasaDitherGenerator": "display_mode_dither.py",
    "apply_dither16": "display_mode_dither.py",
    "_luma_tabla": "display_mode_pixels.py",
    "_szepia_tabla": "display_mode_pixels.py",
    "display_mode_changes_pixels": "display_mode_pixels.py",
    "mark_overflow": "display_mode_pixels.py",
    "_rgb_kep_e": "display_mode_pixels.py",
    "_tablat_alkalmaz": "display_mode_pixels.py",
    "darken": "display_mode_pixels.py",
    "apply_linear_gamma": "display_mode_pixels.py",
    "apply_mac_gamma": "display_mode_pixels.py",
    "luma": "display_mode_pixels.py",
    "apply_display_bw": "display_mode_pixels.py",
    "apply_display_sepia": "display_mode_pixels.py",
    "apply_display_mode": "display_modes.py",
}


def _forras_sha256(fajl: Path, nev: str) -> str:
    forras = fajl.read_text(encoding="utf-8")
    sorok = forras.splitlines()
    fa = ast.parse(forras, filename=str(fajl))
    talalatok = [
        node
        for node in fa.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == nev
    ]
    assert len(talalatok) == 1, f"{fajl.name}:{nev} hiányzik vagy többszörös"
    node = talalatok[0]
    kezdet = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    reszlet = "\n".join(sorok[kezdet - 1 : node.end_lineno]).encode("utf-8")
    return hashlib.sha256(reszlet).hexdigest()


def test_a_regi_importutvonal_minden_nyilvanos_nevet_megtart():
    aktualis = {nev for nev in vars(display_modes) if not nev.startswith("_")}
    assert aktualis == _NYILVANOS_NEVEK, (
        f"a display_modes homlokzat nevei eltérnek: "
        f"hiányzik={sorted(_NYILVANOS_NEVEK - aktualis)}, "
        f"többlet={sorted(aktualis - _NYILVANOS_NEVEK)}"
    )


def test_a_felbontott_fuggvenyek_forrasszovege_bajtra_azonos():
    elteresek = {}
    rossz_helyen = {}
    for nev, vart_hash in _FORRASHASH.items():
        fajl = _RENDER / _FORRASFAJL[nev]
        kapott_hash = _forras_sha256(fajl, nev)
        if kapott_hash != vart_hash:
            elteresek[nev] = (vart_hash, kapott_hash)
        objektum = getattr(display_modes, nev)
        vart_modul = f"picasapy.render.{_FORRASFAJL[nev][:-3]}"
        if objektum.__module__ != vart_modul:
            rossz_helyen[nev] = (vart_modul, objektum.__module__)

    assert not elteresek, f"megváltozott forrásszöveg-hash: {elteresek}"
    assert not rossz_helyen, f"a függvény/osztály nincs a bontott modulban: {rossz_helyen}"


def test_a_homlokzat_es_a_reszmodulok_400_sor_alatt_maradnak():
    hianyzo = [nev for nev in _MODULOK if not (_RENDER / nev).is_file()]
    assert not hianyzo, f"hiányzó megjelenítési mód modulok: {hianyzo}"

    hosszu = {
        nev: len((_RENDER / nev).read_text(encoding="utf-8").splitlines())
        for nev in _MODULOK
        if len((_RENDER / nev).read_text(encoding="utf-8").splitlines()) >= 400
    }
    assert not hosszu, f"400 soros vagy hosszabb modul: {hosszu}"


def test_a_dispatcher_patchpontjai_a_regi_homlokzaton_maradnak():
    assert display_modes.apply_display_mode.__globals__ is vars(display_modes)
