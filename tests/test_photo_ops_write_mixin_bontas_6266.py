"""A fotóíró mixin bontása őrizze meg a régi API-t és a Qt-felületet (#6266)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from PySide6.QtCore import QMetaMethod

from picasapy.app import photo_ops_write_mixin
from picasapy.app.controller import AppController


_APP = Path(__file__).resolve().parents[1] / "src" / "picasapy" / "app"
_UJ_MODULOK = (
    "photo_ops_write_core_mixin.py",
    "photo_ops_write_text_mixin.py",
)

_EREDETI_NYILVANOS_NEVEK = {
    "PICASA_INI_NAME",
    "Path",
    "PhotoOpsWriteMixin",
    "Property",
    "Signal",
    "Slot",
    "annotations",
    "formatting",
    "load_or_empty",
    "open_index",
    "parse_text",
    "photo_by_id",
    "replace",
    "search_photos",
    "update_document",
    "update_document_ujraprobalva",
    "update_photo_fields",
    "with_backuphash",
    "write_iptc_caption",
}

# A 6266 előtti photo_ops_write_mixin.py 32 metódusának LF-normalizált,
# UTF-8 forrásszöveg-lenyomata a dekorátortól a metódus záró soráig.
_EREDETI_FORRAS_SHA256 = {
    "hoverPreviewFileUrlAt": "d7c0de8636133f4907cea69506cfdf3ebe872ab72eefaf579b7254fdeef64522",
    "_ensure_broken_photo_wired": "09144552bde330597f10079da85ba2da1bd3fbab91261a38d8f11ca2babe34d3",
    "_on_broken_image_detected": "5fdb0ede327c8be82efdbafba63b07f74a29c305f1a990dad2a5740625c2b67e",
    "hidePhotosByIds": "3b5efdb19b4deb5697ecf074ea3063c806034aef348b0cda7c29dc77ed1d6aaa",
    "_ensure_photo_ops_wired": "fbf1aed565f3353df68897a6ccbaa008a3dbff3440354d87343d14164be86359",
    "_on_photo_field_updated": "5c8304b31371e16bffde0b33c0283ce62de9ee376e7e55a9221ca12f82555c1a",
    "_on_photo_write_aborted": "168446a6cb84c5df26d342d6af7da212575124585dda89c4ad101ee7d15475d0",
    "jelentsdAzIrasiHibat": "57428491224f07804ebc7b728858bb4b609516f5d75c8942025d773e7d89564f",
    "_on_photo_write_failed": "00b6e8a4a02d81334ad496dffbd2d0da8f76098bc8245911e637b929379e71e8",
    "_run_photo_write": "58c3b4176a38f675bdcf1b8e533b12fc48dbc2cfe1f1fe942376b11a31517935",
    "_run_photo_writes": "4889d5ad6db6ff50db6280f464e3d7ffe143058fbdbbfb4736df3e8db64f85bd",
    "_refresh_if_star_filtered": "dfeb8f6caa803a13df0a8143c05014c51d7fbc8b735b02f910e01c2e6485a218",
    "_refresh_if_dropped_from_search": "ad1944a77a9db8677d34b47aaafb4712f749a0af1ed18f745382aba4425dcd27",
    "toggleStar": "4b3e698bf19d889dff8da1f79f833d9b3398aeb5a1e48cc82b11cf09c42c4ebe",
    "_ensure_caption_clipboard": "466fb7f0d772d64c96ec1ce0c3392195cca96cbd8411c5688612e064bb08a5ed",
    "setCaptionClipboardText": "740759dadd2a208bde414f43a755f0f66f1a653046e65b3e16ff266fc376e9a2",
    "captionClipboardText": "f392c4239a38836794e8afbff912f4d3bc5cbd5c2e5de5583f6f900408566611",
    "copyCaptionText": "124a22594e8bbfc2389de5e78d4a1455af27032b50a8efdebc0bb7d5570c7e5d",
    "pasteCaptionText": "15b492f0b356509d8d8fa19733320c35f01227fc121cb373abd0911edcab224d",
    "_write_caption_text": "955a1ce28854f4f31a7d8159e09682ea756e274d7e3dc281b31587a707d4e5ab",
    "_ensure_text_layer_clipboard": "6919ff5b531eaf9a7364df911c9080f87c4266e9eafb797f37d4718e10c197da",
    "_text_layer_value": "0abc20b5221931b3a192da9f95cd857356fda6d8bb57baee93ade5c645d6b779",
    "hasTextLayerInSelection": "8f98039c96fdbe2955d9fe1fff7793ddfa3fa882763e8502bd0fba6523eaad56",
    "hasTextLayerClipboard": "6e5ebd70ccacfba6d240550e091f4a2e8cff51f45645a75ef453cf111f1bf7b4",
    "copyTextLayer": "2bef7ea47fcd15e5f74d0169b566c242c8e1a687a9c04d188362bd5a6a817320",
    "pasteTextLayer": "a4db5b62d4af83939deaaccc3ee456e59f3f068484c13f34fd0fb49cd564a6a9",
    "confirmCaptionPaste": "a93ac0f9bb9f55ab8993e50e1572d34e1cc8eded49c28bb5c6000726fc2ae858",
    "cancelCaptionPaste": "f34c1e292d0fdfc6aaf3b1bf37c879eae4b7df711383dcbf0ac22cb821b5f1ba",
    "setCaption": "2e812d2b2050a8e291261d7a7948de920d18df7876c5c1e1f8f6de83db9f85aa",
    "_felirat_iras": "1e0dc54288eb28c25c825b4ccb6bdc80f6771512a914ed8d882302461fa8099d",
    "_rows_to_photos": "6a75f2ea77f949673fdcede4a1709c0cb9d47e89e9d764e81b8b044bf3ef06d6",
    "_apply_batch": "8d1de968774f1e04ec43314db9d607f50f7a18d8095517d9628d9afcdb6b2f6c",
}

_QT_METHODS = (
    ("signal", "_photoFieldUpdated", 3),
    ("signal", "_photoWriteAborted", 1),
    ("signal", "photoOpFailed", 1),
    ("signal", "textLayerClipboardChanged", 0),
    ("signal", "captionPasteConfirmationRequested", 0),
    ("signal", "brokenPhotosDetected", 1),
    ("slot", "hoverPreviewFileUrlAt", 1),
    ("slot", "_on_broken_image_detected", 1),
    ("slot", "hidePhotosByIds", 1),
    ("slot", "_on_photo_field_updated", 3),
    ("slot", "_on_photo_write_aborted", 1),
    ("slot", "_on_photo_write_failed", 1),
    ("slot", "toggleStar", 1),
    ("slot", "hasTextLayerInSelection", 1),
    ("slot", "copyTextLayer", 1),
    ("slot", "pasteTextLayer", 1),
    ("slot", "confirmCaptionPaste", 0),
    ("slot", "cancelCaptionPaste", 0),
    ("slot", "setCaption", 2),
)
_QT_PROPERTIES = (("hasTextLayerClipboard", "textLayerClipboardChanged", False),)


def _fuggveny_hash(forras: bytes, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    sorok = forras.splitlines(keepends=True)
    kezdo_sor = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    reszlet = b"".join(sorok[kezdo_sor - 1 : node.end_lineno])
    return hashlib.sha256(reszlet).hexdigest()


def _mozgatott_forras_hashok() -> dict[str, str]:
    lenyomatok: dict[str, str] = {}
    for utvonal in _APP.glob("photo_ops_write*.py"):
        nyers = utvonal.read_bytes().replace(b"\r\n", b"\n")
        fa = ast.parse(nyers.decode("utf-8"), filename=str(utvonal))
        for osztaly in fa.body:
            if not isinstance(osztaly, ast.ClassDef):
                continue
            for tag in osztaly.body:
                if not isinstance(tag, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                assert tag.name not in lenyomatok, f"többszörös metódus: {tag.name}"
                lenyomatok[tag.name] = _fuggveny_hash(nyers, tag)
    return lenyomatok


def test_a_homlokzat_megtartja_a_regi_nyilvanos_neveket() -> None:
    aktualis = {nev for nev in vars(photo_ops_write_mixin) if not nev.startswith("_")}
    assert aktualis == _EREDETI_NYILVANOS_NEVEK
    assert photo_ops_write_mixin.PhotoOpsWriteMixin is not None


def test_a_metodusok_forrasszovege_bajtra_azonos() -> None:
    aktualis = _mozgatott_forras_hashok()
    assert aktualis == _EREDETI_FORRAS_SHA256, (
        f"hiányzó vagy új metódus: {sorted(set(aktualis) ^ set(_EREDETI_FORRAS_SHA256))}; "
        "eltérő forráshash: "
        f"{sorted(nev for nev in aktualis.keys() & _EREDETI_FORRAS_SHA256.keys() if aktualis[nev] != _EREDETI_FORRAS_SHA256[nev])}"
    )


def test_az_uj_modulok_400_sor_alatt_maradnak() -> None:
    hianyzik = [nev for nev in _UJ_MODULOK if not (_APP / nev).is_file()]
    assert not hianyzik, f"hiányzó bontott modul(ok): {hianyzik}"
    meretek = {
        nev: len((_APP / nev).read_text(encoding="utf-8").splitlines())
        for nev in _UJ_MODULOK
    }
    assert all(sor < 400 for sor in meretek.values()), f"400 soros határt elérő modul: {meretek}"


def test_a_fotoiro_mixin_qt_metaobjektuma_valtozatlan() -> None:
    meta = AppController.staticMetaObject
    sajat_nevek = {nev for _, nev, _ in _QT_METHODS}
    tenyleges_metodusok = []
    for index in range(meta.methodOffset(), meta.methodCount()):
        method = meta.method(index)
        nev = bytes(method.name()).decode("utf-8")
        if nev in sajat_nevek:
            tipus = method.methodType()
            if tipus == QMetaMethod.MethodType.Signal:
                fajta = "signal"
            elif tipus == QMetaMethod.MethodType.Slot:
                fajta = "slot"
            else:
                fajta = "method"
            tenyleges_metodusok.append((fajta, nev, method.parameterCount()))
    # a metaobjektum-index sorrendje nem része a felületnek
    assert sorted(tenyleges_metodusok) == sorted(_QT_METHODS)

    tenyleges_tulajdonsagok = []
    for index in range(meta.propertyOffset(), meta.propertyCount()):
        prop = meta.property(index)
        nev = prop.name()
        if nev == "hasTextLayerClipboard":
            notify = prop.notifySignal()
            notify_nev = bytes(notify.name()).decode("utf-8") if notify.isValid() else ""
            tenyleges_tulajdonsagok.append((nev, notify_nev, prop.isConstant()))
    assert tuple(tenyleges_tulajdonsagok) == _QT_PROPERTIES


def test_az_uj_mixinreszek_a_regi_fotomuvelet_savban_maradnak() -> None:
    mro = [cls.__name__ for cls in AppController.__mro__]
    vart = (
        "PhotoOpsWriteMixin",
        "PhotoOpsWriteCoreMixin",
        "PhotoOpsWriteTextMixin",
        "PhotoOpsRenameMixin",
        "PhotoOpsAlbumMixin",
        "PhotoOpsXmpMixin",
        "PhotoOpsTransformMixin",
        "PhotoOpsEffectClipboardMixin",
        "BatchEffectMixin",
    )
    poziciok = [mro.index(nev) for nev in vart if nev in mro]
    assert len(poziciok) == len(vart), f"hiányzó vagy áthelyezett mixin: {mro}"
    assert poziciok == sorted(poziciok), f"megváltozott mixinek sorrendje: {mro}"
