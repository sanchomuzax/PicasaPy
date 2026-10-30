"""A thumbnail-cache bontása nem változtathatja meg a forrást vagy API-t."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_FORRAS = _GYOKER / "src" / "picasapy" / "thumbs"

_REGI_NYILVANOS_NEVEK = {
    "FilterOp",
    "Path",
    "ThumbnailCache",
    "VIDEO_EXTENSIONS",
    "apply_filters",
    "cv2",
    "dekodol_nyerset",
    "elonezeti_arany",
    "hashlib",
    "hosszabb_el",
    "logging",
    "normalize_crop_ops",
    "np",
    "nyers_hosszabb_el",
    "nyers_utvonal",
    "open_video",
    "os",
    "prune_cache_dir",
    "prune_in_background",
    "read_image_bytes",
    "reduced_color_flag",
    "scale_down",
    "scale_down_picasa_mag",
    "serialize_filters",
    "subprocess",
    "sys",
    "szint_cellahoz",
    "szintek",
    "tempfile",
    "threading",
    "write_atomic",
}

# Az értékeket a bontás előtti cache.py forrásszövegéből számoltuk.
# A hash az eredeti dekorátortól (ha volt) a függvény záró soráig tartó
# UTF-8 bájtokat rögzíti; AST-t csak a forrássorok megkeresésére használ.
_MOZGATOTT_FORRASOK = {
    ("cache_storage.py", "_CacheStorageMixin", "__init__"):
        "34dc32867b361a762e927d0748289f0028c94a714375e3a06afba0239b89b654",
    ("cache_storage.py", "_CacheStorageMixin", "prune"):
        "31aa3ce9541519e614fb14a5c541cc94e878cfca648f9c07690a73d8f6a8f999",
    ("cache_storage.py", "_CacheStorageMixin", "levels"):
        "34cca3ce695481b57f87b411b2f940de7ef224060def5dd11b7522c1f884bc49",
    ("cache_storage.py", "_CacheStorageMixin", "level_for"):
        "10bd12c2b7b0a0bb1d7b6161035b9039bdb69ce8a4296d6199968b8e8ff9b1cf",
    ("cache_storage.py", "_CacheStorageMixin", "clear"):
        "362eaa58cde4a0a91944ce89ec84d8ffa7ef983c8de7f87ca2991073bbb7a5f7",
    ("cache_storage.py", "_CacheStorageMixin", "thumbnail_path"):
        "fe999039063f8df169caf2dc0c49bcebeaa6a4a9c2d816329bf639281343df53",
    ("cache_storage.py", "_CacheStorageMixin", "_write_atomic"):
        "ca11a5089310d58bd950f83db11c2230889589b42bcc6d74122b0edc92546310",
    ("cache_generation.py", "_CacheGenerationMixin", "get_or_create"):
        "40eccd18239ec51f6ad3355ced36f28dec0bb330cd34e42631229ecf69954979",
    ("cache_generation.py", "_CacheGenerationMixin", "_szint_forras"):
        "d7fda426a6c2be4e668411f2421d1e2866c345342c14d39d4c248d7ae8959154",
    ("cache_generation.py", "_CacheGenerationMixin", "_read_flag"):
        "7211f543ff7fb63a48e796c78672678b95b3ae128d1ccddff2cd9cea0bce5e11",
}


def _fuggveny_forras_hash(utvonal: Path, osztalynev: str | None, nev: str) -> str:
    nyers = utvonal.read_bytes()
    sorok = nyers.splitlines(keepends=True)
    fa = ast.parse(nyers.decode("utf-8"))
    jeloltek: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for csomopont in fa.body:
        if osztalynev is None:
            if isinstance(csomopont, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if csomopont.name == nev:
                    jeloltek.append(csomopont)
        elif isinstance(csomopont, ast.ClassDef) and csomopont.name == osztalynev:
            jeloltek.extend(
                elem
                for elem in csomopont.body
                if isinstance(elem, (ast.FunctionDef, ast.AsyncFunctionDef))
                and elem.name == nev
            )
    assert len(jeloltek) == 1, f"{utvonal.name}:{osztalynev}.{nev} hiányzik vagy többszörös"
    fuggveny = jeloltek[0]
    kezdo_sor = min(
        [fuggveny.lineno, *(decorator.lineno for decorator in fuggveny.decorator_list)]
    )
    reszlet = b"".join(sorok[kezdo_sor - 1 : fuggveny.end_lineno])
    return hashlib.sha256(reszlet).hexdigest()


def test_a_cache_bontasa_megorizza_az_api_t_es_a_forrasszoveget():
    for fajlnev in {
        "cache_generation.py",
        "cache_policy.py",
        "cache_storage.py",
    }:
        utvonal = _FORRAS / fajlnev
        assert utvonal.is_file(), f"hiányzó bontott modul: {utvonal.name}"
        assert len(utvonal.read_text(encoding="utf-8").splitlines()) < 400

    from picasapy.thumbs import ThumbnailCache
    from picasapy.thumbs import cache

    hianyzo = sorted(nev for nev in _REGI_NYILVANOS_NEVEK if not hasattr(cache, nev))
    assert not hianyzo, f"a cache homlokzatáról eltűntek ezek a nevek: {hianyzo}"
    assert set(cache.__all__) == _REGI_NYILVANOS_NEVEK
    assert cache.ThumbnailCache is ThumbnailCache
    assert cache.open_video is cache._open_video

    elteresek = []
    for (fajlnev, osztalynev, nev), vart_hash in _MOZGATOTT_FORRASOK.items():
        utvonal = _FORRAS / fajlnev
        tenyleges_hash = _fuggveny_forras_hash(utvonal, osztalynev, nev)
        if tenyleges_hash != vart_hash:
            elteresek.append(f"{fajlnev}:{osztalynev or '<modul>'}.{nev}")
    assert not elteresek, f"a bontott függvények forrásszövege változott: {elteresek}"
