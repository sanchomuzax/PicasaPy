"""Az album-műveletek bontása őrizze meg a forrást és a Qt-felületet (#6273)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from PySide6.QtCore import QMetaMethod

from picasapy.app import photo_ops_album_mixin
from picasapy.app.controller import AppController


_APP = Path(__file__).resolve().parents[1] / "src" / "picasapy" / "app"
_MODULOK = (
    "photo_ops_album_mixin.py",
    "photo_ops_album_membership_mixin.py",
    "photo_ops_album_order_mixin.py",
    "photo_ops_album_properties_mixin.py",
    "photo_ops_album_actions_mixin.py",
)

_EREDETI_NYILVANOS_NEVEK = {
    "ALBUM_SECTION_PREFIX",
    "AlbumOrderWriteError",
    "PICASA_INI_NAME",
    "Path",
    "PhotoOpsAlbumMixin",
    "QCoreApplication",
    "QGuiApplication",
    "Qt",
    "SORT_MODES",
    "STAR_ALBUM_TOKEN",
    "Signal",
    "Slot",
    "album_photos",
    "albums_of",
    "annotations",
    "ensure_album",
    "formatting",
    "load_existing",
    "mappa_prioritasai",
    "mentsd_a_prioritasokat",
    "new_places",
    "open_index",
    "photos_in_folder",
    "photos_with_keyword",
    "secrets",
    "sorted_album",
    "update_document",
    "with_album",
    "with_album_fields",
    "without_album",
    "without_album_everywhere",
    "write_album_places",
}

# A bontás előtti photo_ops_album_mixin.py 22 metódusának LF-normalizált,
# UTF-8 forrásszöveg-lenyomata a dekorátortól a metódus záró soráig.
_EREDETI_FORRAS_SHA256 = {
    # #6281: az index-beli üres album kezelése (két új segéd, öt módosult metódus)
    "_fuggo_ures_album": "6d9fede6f567d5ddf6572d46ebceaf988e921360b2d338255710c353a6a14516",
    "_fuggo_ures_album_frissit": "a72813e92efdf9aa77224f89f05090af1886465f321cd643117bbc0a859d5860",
    "addRowsToAlbum": "79097cd609e59098501f9d323e629a39943e92d68c0148688b0b507453f1298e",
    "removeRowsFromAlbum": "6ece39f95ddb1d0fc0a5590d3c256139b2b5937e55210112a1a4402f7e025be1",
    "deleteAlbum": "82152426a235bc13e9dc864f9e7253362ebe481eaf18870b66854da553ae5ffa",
    "sortAlbum": "d037c31c30de643224579a7f939e1d26c2c266416472cb22cb9802e961637869",
    "sortAlbumBy": "4f7d5e4f254cb6991799344c0821f7572eb5d6e1ca901733a85be4f21b61911a",
    "reorderAlbumPhotos": "43ca046e9e47d948a784028d53e11b4f15d994026992dd18dc88e4720e6084bd",
    "sortFolderBy": "4c0095361c4b7230d800016553b39e0b3aa675b4830f16bfd3e297689139c59b",
    "albumProperties": "d7738cb831684847ff9c8f4a830d1587d0501baa317f1c06e431158e26514b49",
    "albumMusicFile": "45c71583aea327de21a32a58b0cf2d13ddc81f05f70131edbabd0e48cd747a73",
    "albumMusicTrackUrls": "4e0196cf9587690fd6fd89f2f92c161669abd38f4ff0dc5a0704553a2a1f9d99",
    "editAlbumProperties": "bdea3581ac51e62e42f0dd58cd78840cef66879a93ac976d14adf2526752829a",
    "editAlbumMusic": "777d8ae03eff326af0309dad4171d5cbacfff36ce8581e51431bbc0fccbfe14f",
    "_album_dokumentumok": "93229cf8ec334fca93d3d22d80fc1dfe077badfc8df952be25162eef0d612045",
    "createAlbum": "ef0c45d043b67bb6714deea959268ab0c4eb89ab3c84bf0cdadbd732d54a9a3a",
    "createAlbumWithProperties": "e7f9f61ae2a5fb48dcb264eb2a1c21ce4b81ed9f07b7359fb15828bf78e0ce57",
    "createEmptyAlbum": "c96d70e3e9bf57c6380655b3ea833da02ef9749d30dc5c963de1a9965456b165",
    "_albumot_keszit": "1c690d2f14511d1ade16ab7a024c6143f6624a1b6d7ca29c340e9e324c40b0ac",
    "setPhotoAsDesktopBackground": "fc86c3c32a894726152a71d252afc31cf41585c8a6f8dd355c019781237d327b",
    "showTagAsAlbum": "c405fb498f23de04a08fa0e0823c0db73d202816144b04b9ba358912c9c8c11f",
    "_mentheto_kereses": "37253d12bb90209f8755612ff0c43eb487b42a916bdea0c1f7fa189031ba2ef5",
    "saveSearchAsAlbum": "e02cfc7553506ceff3a4a755478d9c763d458947592b45cde69ae7523d00c6ca",
    "_write_album_batch": "c7847d0a326db08d05de0c3e46761edeea02fa0264c2b369a2c2b4686a43d77d",
}

_QT_METHODS = (
    ("signal", "albumWriteFailed", 1),
    ("slot", "addRowsToAlbum", 2),
    ("slot", "removeRowsFromAlbum", 2),
    ("slot", "deleteAlbum", 1),
    ("slot", "sortAlbum", 2),
    ("slot", "reorderAlbumPhotos", 2),
    ("slot", "sortFolderBy", 2),
    ("slot", "albumProperties", 1),
    ("slot", "editAlbumProperties", 5),
    ("slot", "editAlbumMusic", 3),
    ("slot", "createAlbum", 2),
    ("slot", "createAlbumWithProperties", 7),
    ("slot", "createEmptyAlbum", 7),
    ("slot", "setPhotoAsDesktopBackground", 1),
    ("slot", "showTagAsAlbum", 1),
    ("slot", "saveSearchAsAlbum", 0),
)
_QT_PROPERTIES: tuple[tuple[str, str, bool], ...] = ()


def _mozgatott_forras_hashok() -> dict[str, str]:
    lenyomatok: dict[str, str] = {}
    for utvonal in _APP.glob("photo_ops_album*.py"):
        nyers = utvonal.read_bytes().replace(b"\r\n", b"\n")
        sorok = nyers.splitlines(keepends=True)
        fa = ast.parse(nyers.decode("utf-8"), filename=str(utvonal))
        for osztaly in fa.body:
            if not isinstance(osztaly, ast.ClassDef):
                continue
            if not osztaly.name.startswith("PhotoOpsAlbum"):
                continue
            for tag in osztaly.body:
                if not isinstance(tag, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                assert tag.name not in lenyomatok, f"többszörös metódus: {tag.name}"
                kezdo_sor = min(
                    [tag.lineno, *(decorator.lineno for decorator in tag.decorator_list)]
                )
                reszlet = b"".join(sorok[kezdo_sor - 1 : tag.end_lineno])
                lenyomatok[tag.name] = hashlib.sha256(reszlet).hexdigest()
    return lenyomatok


def _album_mixin_qt_property_nevek() -> set[str]:
    nevek: set[str] = set()
    for utvonal in _APP.glob("photo_ops_album*.py"):
        fa = ast.parse(utvonal.read_text(encoding="utf-8"), filename=str(utvonal))
        for osztaly in fa.body:
            if not isinstance(osztaly, ast.ClassDef):
                continue
            if not osztaly.name.startswith("PhotoOpsAlbum"):
                continue
            for tag in osztaly.body:
                if isinstance(tag, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(
                        isinstance(dekorator, ast.Call)
                        and isinstance(dekorator.func, ast.Name)
                        and dekorator.func.id == "Property"
                        for dekorator in tag.decorator_list
                    ):
                        nevek.add(tag.name)
                elif isinstance(tag, ast.Assign):
                    if (
                        isinstance(tag.value, ast.Call)
                        and isinstance(tag.value.func, ast.Name)
                        and tag.value.func.id == "Property"
                    ):
                        nevek.update(
                            target.id
                            for target in tag.targets
                            if isinstance(target, ast.Name)
                        )
    return nevek


def test_a_homlokzat_megtartja_a_regi_nyilvanos_neveket() -> None:
    aktualis = {nev for nev in vars(photo_ops_album_mixin) if not nev.startswith("_")}
    assert aktualis == _EREDETI_NYILVANOS_NEVEK
    assert all(hasattr(photo_ops_album_mixin, nev) for nev in _EREDETI_NYILVANOS_NEVEK)


def test_a_metodusok_forrasszovege_bajtra_azonos() -> None:
    aktualis = _mozgatott_forras_hashok()
    assert aktualis == _EREDETI_FORRAS_SHA256, (
        f"hiányzó vagy új metódus: {sorted(set(aktualis) ^ set(_EREDETI_FORRAS_SHA256))}; "
        "eltérő forráshash: "
        f"{sorted(nev for nev in aktualis.keys() & _EREDETI_FORRAS_SHA256.keys() if aktualis[nev] != _EREDETI_FORRAS_SHA256[nev])}"
    )


def test_az_uj_modulok_400_sor_alatt_maradnak() -> None:
    hianyzik = [nev for nev in _MODULOK if not (_APP / nev).is_file()]
    assert not hianyzik, f"hiányzó bontott modul(ok): {hianyzik}"
    meretek = {
        nev: len((_APP / nev).read_text(encoding="utf-8").splitlines())
        for nev in _MODULOK
    }
    assert all(sor < 400 for sor in meretek.values()), (
        f"400 soros határt elérő modul: {meretek}"
    )


def test_az_album_mixin_qt_metaobjektuma_valtozatlan() -> None:
    meta = AppController.staticMetaObject
    vart_tulajdonsagnevek = {nev for nev, _, _ in _QT_PROPERTIES}
    assert _album_mixin_qt_property_nevek() == vart_tulajdonsagnevek

    sajat_nevek = {nev for _, nev, _ in _QT_METHODS}
    tenyleges_metodusok = []
    for index in range(meta.methodOffset(), meta.methodCount()):
        method = meta.method(index)
        nev = bytes(method.name()).decode("utf-8")
        if nev not in sajat_nevek:
            continue
        tipus = method.methodType()
        if tipus == QMetaMethod.MethodType.Signal:
            fajta = "signal"
        elif tipus == QMetaMethod.MethodType.Slot:
            fajta = "slot"
        else:
            fajta = "method"
        tenyleges_metodusok.append((fajta, nev, method.parameterCount()))
    assert sorted(tenyleges_metodusok) == sorted(_QT_METHODS)

    tenyleges_tulajdonsagok = []
    for index in range(meta.propertyOffset(), meta.propertyCount()):
        prop = meta.property(index)
        nev = prop.name()
        if nev not in vart_tulajdonsagnevek:
            continue
        notify = prop.notifySignal()
        notify_nev = bytes(notify.name()).decode("utf-8") if notify.isValid() else ""
        tenyleges_tulajdonsagok.append((nev, notify_nev, prop.isConstant()))
    assert tuple(tenyleges_tulajdonsagok) == _QT_PROPERTIES


def test_az_album_reszmixinek_a_regi_mixinhelyen_maradnak() -> None:
    mro = [cls.__name__ for cls in AppController.__mro__]
    vart = (
        "PhotoOpsAlbumMixin",
        "PhotoOpsAlbumMembershipMixin",
        "PhotoOpsAlbumOrderMixin",
        "PhotoOpsAlbumPropertiesMixin",
        "PhotoOpsAlbumActionsMixin",
        "PhotoOpsXmpMixin",
    )
    poziciok = [mro.index(nev) for nev in vart if nev in mro]
    assert len(poziciok) == len(vart), f"hiányzó albummixin vagy megváltozott MRO: {mro}"
    assert poziciok == sorted(poziciok), f"megváltozott albummixin MRO: {mro}"
