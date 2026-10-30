"""Az EditSession bontása őrizze meg az API-t és a forrásszöveget (#6247)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from picasapy.edit import session

_GYOKER = Path(__file__).resolve().parents[1]
_EDIT = _GYOKER / "src" / "picasapy" / "edit"
_MODULOK = ("session_core.py", "session_effects.py", "session_regions.py")

# A #6247 előtti session.py forrásából vett SHA-256-ok, dekorátortól a záró
# sorig. Az AST csak a sorok megkeresésére szolgál, ast.dump nincs használva.
_MOZGATOTT_FORRASOK = {
    "class:FinetuneValues": "3b578948c924d90830869715330c72512794b525a30295eeaed2714bd01d8d4b",
    "function:_finetune_float": "2323de0410c89bbc4a0d100bad6b840d3ccfa9f067f83a7f250be99a23f70d79",
    "function:_new_op": "dde68fbe9c3c56abf9b138e6dfaec1881e881e66a1c6fc5d5ea9e621dcb79da9",
    "method:_with_single_layer": "a12e5ce03fd473cc691955290f974f021fc36f0624705714ebc216e8c8215735",
    "method:append_crop": "63d4bf26c9db8a105702727041aa766b9d4889222584674268fea40c53326475",
    "method:append_effect": "f7a8cf067e5d7f5da99f107283e2542cb2b968802c05e5e129aa04c15b056308",
    "method:apply": "cbdca7c8cdfaa52915e3108637fc3424564c561e2e4cf98e409b1b90b76ee018",
    "method:clear_crop": "92a529ae3ebb9a172edfa7d047f9d3ed31b531c771687573e98d4a48f2d3c219",
    "method:clear_finetune": "13b1283dca764cabd8877eb8d666829bdb0fe7b5cfded236dba21a8271813481",
    "method:clear_redeye": "ab25bf283d15cfbcbc8fa81a74543a1082ecda66126681cbfb1b3347b5e01e52",
    "method:clear_retouch": "03c9bf8e1e68a408e9249b520fcd2e0a271bde3efe31a7a748fb871607d0f2b1",
    "method:clear_tilt": "bec13be1170bb6c291c621414a61eca6ad7c2daa237c05831185567a0d5b9ec0",
    "method:copy_effects": "9724c22720fc29807d1087cef03bcd735097972742e496ab5c42b3916036001f",
    "method:crop": "5896933ef520bf3f2314a80e6914005c22a077a0aebcdbf96ba0a57c4ecacbc3",
    "method:finetune_values": "070940f2e00adf7bec61c0f1f3d5334906bd1e1bc594e601617dc2e19c25d49c",
    "method:from_value": "be9131bc0ce99160202e7d90fe66631fdfcc2b8b4e4e1bd69e22ccb6f9283f09",
    "method:gpu_finetune_prefix": "ceac8389f014b55801f5f72619c1db4ebec17d85922098514189fa4d51901cd6",
    "method:has": "5f6a6322e625d81478b13f21fe09e34d6cea2e44070d14c77fa0a008cc79e95b",
    "method:has_finetune": "7c3de77a4da8b8b28829b29f151e5a53800ce03c54254193b201da44e7ad2321",
    "method:is_empty": "e46902765464fca5e663bec7a53f2f80f34b882471d6d5f8e48b6cc4b4beaa72",
    "method:last_is": "5aad2d0eab693a86c5c23803d9a7379e783fa310a9c9de7c0e29a03c2cd01982",
    "method:paste_effects": "874784b157aa6f4a2dba7256c4cb50665346b63622f2e7505c5288d673a326ea",
    "method:redeye_detection_ops": "284d38f6cee87f11559060241538442233cbac9b2f715f9147316324ba73a6fb",
    "method:redeye_post_detection_ops": "3aba72090dc2d9cb201f58d80020918a1fddf29c1b69addbfb278747824850e1",
    "method:redeye_regions": "dc12ef2bfcfa6cf8da85c11918b543bab5aa57f05df38c7f55e49d5fb7f4e75f",
    "method:retouch_patches": "81844334671ac864675b6450347f1c6256de438f0e3ed03af2a9d7dc1c9cc54f",
    "method:retouch_regions": "e8a8b8661e6135fc7880e2f5a8de1091c3e428e2fb6ea17b5e99fd59745877d5",
    "method:set_finetune": "f250c8ac2000b1e105408399017963a219e4ae66ebc259e1cd6a653988a06514",
    "method:set_redeye_regions": "4d2dc8597e65dd3ec2220b02b02e35ad46ce4c93522b533c1dc9f07f78db19d4",
    "method:set_retouch_patches": "71dd48cdb9d854d9b7f01fa6cb5a800501b826825c2cbd1cd54436c2815e90a8",
    "method:set_retouch_regions": "97a114fdc67965b42a0b61a8decdad4dbdf4a485c4931cbb8bdba3f653321087",
    "method:set_tilt": "6d59aebf9db1f12be4f634df71d07047b9551e0cad7205486d9eddc50a91e724",
    "method:tilt_param": "7fc4c8df779688ecda03b360cb4beb2211c4123c71de466442bf4bebe96d7532",
    "method:to_value": "0b720aebfb77be3820cf757e8bdf2837b41aa176d3b3809e2910bddb79013cb8",
    "method:toggle": "017290ae6494afaf7626a9a30c1d519a247ff7d11629e6fd99398764e695de4b",
}

_REGI_NYILVANOS_NEVEK = {
    "parse_retouch_regions",
    "dataclass",
    "build_retouch_op",
    "encode_rect64",
    "FilterOp",
    "EditSession",
    "serialize_filters",
    "canonicalize_op",
    "validate_op_for_write",
    "parse_retouch_patches",
    "annotations",
    "parse_redeye_regions",
    "RETOUCH_FILTER_NAME",
    "decode_rect64",
    "REDEYE_FILTER_NAME",
    "Rect64",
    "Callable",
    "build_redeye_op",
    "EyeCircle64",
    "RetouchPatch",
    "parse_filters",
    "build_retouch_patches_op",
    "FinetuneValues",
}


def _lenyomat(forras: bytes, node: ast.AST) -> str:
    sorok = forras.splitlines(keepends=True)
    kezdo = min(
        [node.lineno, *(dekorator.lineno for dekorator in getattr(node, "decorator_list", []))]
    )
    return hashlib.sha256(b"".join(sorok[kezdo - 1 : node.end_lineno])).hexdigest()


def _forraslenyomatok() -> dict[str, str]:
    eredmeny: dict[str, str] = {}
    fajlok = (_EDIT / "session.py", *(_EDIT / nev for nev in _MODULOK))
    for fajl in fajlok:
        forras = fajl.read_bytes().replace(b"\r\n", b"\n")  # windowsos checkout: CRLF (#6260)
        fa = ast.parse(forras.decode("utf-8"), filename=str(fajl))
        for csomopont in fa.body:
            if isinstance(csomopont, ast.ClassDef):
                if csomopont.name == "FinetuneValues":
                    eredmeny[f"class:{csomopont.name}"] = _lenyomat(forras, csomopont)
                for tag in csomopont.body:
                    if isinstance(tag, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        kulcs = f"method:{tag.name}"
                        assert kulcs not in eredmeny, f"többszörös definíció: {kulcs}"
                        eredmeny[kulcs] = _lenyomat(forras, tag)
            elif isinstance(csomopont, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kulcs = f"function:{csomopont.name}"
                assert kulcs not in eredmeny, f"többszörös definíció: {kulcs}"
                eredmeny[kulcs] = _lenyomat(forras, csomopont)
    return eredmeny


def test_a_session_bontasa_megorizza_a_regi_homlokzatot_es_forrast() -> None:
    hianyzok = [nev for nev in _MODULOK if not (_EDIT / nev).is_file()]
    assert not hianyzok, f"hiányzó bontott modul(ok): {hianyzok}"

    for fajl in (_EDIT / "session.py", *(_EDIT / nev for nev in _MODULOK)):
        sorok = len(fajl.read_text(encoding="utf-8").splitlines())
        assert sorok < 400, f"{fajl.name} elérte a 400 soros határt: {sorok}"

    aktualis = _forraslenyomatok()
    assert aktualis == _MOZGATOTT_FORRASOK, (
        "a bontott függvények/metódusok forrásszövege megváltozott vagy hiányzik: "
        f"hiány/többlet={sorted(set(aktualis) ^ set(_MOZGATOTT_FORRASOK))}; "
        f"eltérő hash={sorted(k for k in aktualis.keys() & _MOZGATOTT_FORRASOK.keys() if aktualis[k] != _MOZGATOTT_FORRASOK[k])}"
    )

    regi_nevek = {nev for nev in vars(session) if not nev.startswith("_")}
    assert regi_nevek == _REGI_NYILVANOS_NEVEK, (
        f"a session homlokzat nyilvános nevei változtak: "
        f"hiányzik={sorted(_REGI_NYILVANOS_NEVEK - regi_nevek)}; "
        f"új={sorted(regi_nevek - _REGI_NYILVANOS_NEVEK)}"
    )
