"""Az importforrás-vezérlő bontása őrizze meg a régi API-t és Qt-felületet."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from picasapy.app import import_source_controller as controller


_GYOKER = Path(__file__).resolve().parents[1]
_APP = _GYOKER / "src" / "picasapy" / "app"

_REGI_NYILVANOS_NEVEK = {
    "AFTER_COPY_DELETE_ALL",
    "AFTER_COPY_DELETE_COPIED",
    "AFTER_COPY_LEAVE",
    "ATMERETEZES_EREDETI",
    "ATMERETEZES_OPCIOK",
    "AUTOEXCLUDE_DEFAULT",
    "AUTOEXCLUDE_SETTINGS_KEY",
    "BackgroundWorkerMixin",
    "Callable",
    "DEFAULT_DESTINATION_SETTINGS_KEY",
    "INI_NAME",
    "ImportCandidate",
    "ImportSourceController",
    "ImportSourceControllerScanningMixin",
    "ImportSourceControllerStateMixin",
    "IndexFastKeySource",
    "MAX_RECENT_DESTINATIONS",
    "MAX_RECENT_SOURCES",
    "MEDIA_FILTER_PICTURES_AND_MOVIES",
    "NAMING_BY_DATE",
    "NAMING_MANUAL",
    "NAMING_TODAY",
    "Path",
    "PhotoRecord",
    "Property",
    "PurePosixPath",
    "PureWindowsPath",
    "QObject",
    "QSettings",
    "QStandardPaths",
    "QStorageInfo",
    "QUrl",
    "RECENT_DESTINATIONS_SETTINGS_KEY",
    "RECENT_SOURCES_SETTINGS_KEY",
    "RESIZE_SETTINGS_KEY",
    "Sequence",
    "Signal",
    "Slot",
    "WipeCardFacts",
    "all_photos",
    "annotations",
    "atmeretez_masolatot",
    "companions_of",
    "copy_photo",
    "ctypes",
    "current_display_mode_suffix",
    "destination_subpath_for_mode",
    "discover_linux_mounted_sources",
    "discover_mounted_sources",
    "discover_windows_mounted_sources",
    "duplicate_paths",
    "has_enough_free_space",
    "has_ini_source",
    "is_valid_folder_name",
    "load_or_empty",
    "media_kind_of",
    "open_index",
    "remove_original_ini_sections",
    "required_bytes_for",
    "scan_files",
    "scan_source_detailed",
    "sqlite3",
    "sys",
    "time",
    "to_file_url",
    "to_local_path",
    "update_document",
    "wintypes",
    "wipe_card_warning",
    "with_backuphash",
}

# A lenyomatok a bontás előtti modulból származnak. A sorokat CRLF->LF
# normalizálás után, a dekorátortól a záró sorig hash-eljük.
_MOZGATOTT_FORRASOK = {
    ("import_source_controller_sources.py", None, "_linux_media_mount_points"):
        "dfb286030238f084da1b2b02a43aa09d62c00fb8cacf5708ae9c1e049bbf1e67",
    ("import_source_controller_sources.py", None, "discover_linux_mounted_sources"):
        "da88c250904c4f87c0824983983e5e89f50e0c04d26452e09226241558b1a770",
    ("import_source_controller_sources.py", None, "_windows_drive_type"):
        "5d21fa32e7f44f18523c89ba157e0cde8ef8553f419e7ac9684da8d72608da9d",
    ("import_source_controller_sources.py", None, "_has_dcim_directory"):
        "bf5a4716d7dfe559ea5e0c255d1a856d85b0dd4a292317ccecb074cad4d02c61",
    ("import_source_controller_sources.py", None, "discover_windows_mounted_sources"):
        "c70e61c99b602c89eb46a89e390dd8481c9971be80a894899dff42146f359bb9",
    ("import_source_controller_sources.py", None, "discover_mounted_sources"):
        "82b84a5406657c4263c8a3ce6e6607e881c9463374287aaa52b50bdf536fa746",
    ("import_source_controller_sources.py", None, "_thumb_url"):
        "0cda4397cdd71773c04356c2674aa6e0c56c314cf360df8c03068db4c90d97f5",
    ("import_source_controller_sources.py", None, "_preview_photo_record"):
        "46edae1383012c527b5fc4128fd49a90e9d55ad718ffa0bbe68abf2559ebcc89",
    ("import_source_controller_sources.py", None, "_library_paths"):
        "65e597a32b14c57894adde054fb188e3974b37f8413798c9dece52e36df46b95",
    ("import_source_controller_sources.py", None, "_duplikatumok"):
        "96a23ad277faf88c9cc18c81b5b7214a73b8ab0b40ef085affd6c9a486f020d7",
    ("import_source_controller.py", "ImportSourceController", "runImport"):
        "82d5b6adf2ed4621227bc7a45a2df40c4138e29de2d02a89d433b8867e253cb0",
    ("import_source_controller_import.py", None, "_size_of"):
        "0f47e44e0fa4ebf543afb784d96deff0affcdde3b956de3794ce0311d3a76cb3",
    ("import_source_controller_import.py", None, "_mark_imported_ini"):
        "9df1bda8dee074017d5c94a1fba1e393d6c28fabf5f259d1536764247e9c0c46",
    ("import_source_controller_import.py", None, "_remove_source_file"):
        "4c07c883fd95ee64603ff5fa25d78a5c8d1ab0821fbb5d2dcee2746040ef4073",
}

_QML_METODUSOK = [
    (1, "sourceScanFinished", 2),
    (1, "sourceScanFailed", 1),
    (1, "selectionChanged", 1),
    (1, "importStarted", 1),
    (1, "importProgress", 2),
    (1, "importSpeed", 1),
    (1, "importFailedDetails", 1),
    (1, "importFinished", 2),
    (1, "autoExcludeChanged", 0),
    (1, "mediaFilterChanged", 0),
    (1, "mountedSourcesChanged", 0),
    (1, "recentSourcesChanged", 0),
    (1, "recentDestinationsChanged", 0),
    (1, "defaultDestinationChanged", 0),
    (1, "resizeLimitChanged", 0),
    (2, "scanSource", 2),
    (2, "scanSource", 1),
    (2, "scanFiles", 1),
    (2, "runImport", 4),
    (2, "refreshMountedSources", 0),
    (2, "setDefaultDestination", 1),
    (2, "setResizeLimit", 1),
    (2, "setMediaFilter", 1),
    (2, "setAutoExclude", 1),
    (2, "rotateFile", 2),
    (2, "toggleStar", 1),
    (2, "excludeFile", 1),
    (2, "includeFile", 1),
    (2, "excludeAll", 0),
    (2, "includeAll", 0),
    (2, "wipeCardWarning", 0),
    (2, "isValidFolderName", 1),
]

_QML_TULAJDONSAGOK = [
    ("autoExclude", "autoExcludeChanged", False),
    ("recentSources", "recentSourcesChanged", False),
    ("mountedSources", "mountedSourcesChanged", False),
    ("recentDestinations", "recentDestinationsChanged", False),
    ("defaultDestination", "defaultDestinationChanged", False),
    ("defaultDestinationUrl", "defaultDestinationChanged", False),
    ("resizeOptions", "resizeLimitChanged", False),
    ("resizeLimit", "resizeLimitChanged", False),
    ("mediaFilter", "mediaFilterChanged", False),
]


def _nev(ertek) -> str:
    return ertek if isinstance(ertek, str) else bytes(ertek).decode("utf-8")


def _forras_hash(fajlnev: str, osztalynev: str | None, nev: str) -> str:
    fajl = _APP / fajlnev
    nyers = fajl.read_bytes().replace(b"\r\n", b"\n")
    sorok = nyers.splitlines(keepends=True)
    fa = ast.parse(nyers.decode("utf-8"), filename=str(fajl))
    jeloltek: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for csomopont in fa.body:
        if osztalynev is None:
            if (
                isinstance(csomopont, (ast.FunctionDef, ast.AsyncFunctionDef))
                and csomopont.name == nev
            ):
                jeloltek.append(csomopont)
        elif isinstance(csomopont, ast.ClassDef) and csomopont.name == osztalynev:
            jeloltek.extend(
                elem
                for elem in csomopont.body
                if isinstance(elem, (ast.FunctionDef, ast.AsyncFunctionDef))
                and elem.name == nev
            )
    assert len(jeloltek) == 1, f"{fajlnev}:{osztalynev or '<modul>'}.{nev} hiányzik"
    fuggveny = jeloltek[0]
    kezdo_sor = min(
        [fuggveny.lineno, *(dekorator.lineno for dekorator in fuggveny.decorator_list)]
    )
    reszlet = b"".join(sorok[kezdo_sor - 1 : fuggveny.end_lineno])
    return hashlib.sha256(reszlet).hexdigest()


def test_a_homlokzat_megtartja_a_regi_neveket() -> None:
    aktualis = {nev for nev in vars(controller) if not nev.startswith("_")}
    assert aktualis == _REGI_NYILVANOS_NEVEK
    assert all(hasattr(controller, nev) for nev in _REGI_NYILVANOS_NEVEK)


def test_a_bontott_forrasok_bajtra_azonosak() -> None:
    hianyzo = []
    eltero = []
    for (fajlnev, osztalynev, nev), vart_hash in _MOZGATOTT_FORRASOK.items():
        fajl = _APP / fajlnev
        if not fajl.is_file():
            hianyzo.append(f"{fajlnev}:{nev}")
            continue
        if _forras_hash(fajlnev, osztalynev, nev) != vart_hash:
            eltero.append(f"{fajlnev}:{osztalynev or '<modul>'}.{nev}")
    assert not hianyzo, f"hiányzó bontott források: {hianyzo}"
    assert not eltero, f"a bontott függvények forrásszövege eltért: {eltero}"


def test_az_uj_modulok_400_sor_alatt_maradnak() -> None:
    fajlnevek = (
        "import_source_controller_sources.py",
        "import_source_controller_import.py",
        "import_source_controller_state.py",
        "import_source_controller_scanning.py",
    )
    hianyzo = [nev for nev in fajlnevek if not (_APP / nev).is_file()]
    assert not hianyzo, f"hiányzó modul(ok): {hianyzo}"
    tulhosszuak = {
        nev: len((_APP / nev).read_text(encoding="utf-8").splitlines())
        for nev in fajlnevek
        if len((_APP / nev).read_text(encoding="utf-8").splitlines()) >= 400
    }
    assert not tulhosszuak, f"400 soros határt elérő modul(ok): {tulhosszuak}"


def test_a_qml_metaobjektum_es_a_forditasi_osztalynev_valtozatlan() -> None:
    meta = controller.ImportSourceController.staticMetaObject
    metodusok = [
        (
            meta.method(index).methodType().value,
            _nev(meta.method(index).name()),
            meta.method(index).parameterCount(),
        )
        for index in range(meta.methodOffset(), meta.methodCount())
    ]
    tulajdonsagok = []
    for index in range(meta.propertyOffset(), meta.propertyCount()):
        prop = meta.property(index)
        notify = prop.notifySignal()
        tulajdonsagok.append(
            (
                _nev(prop.name()),
                _nev(notify.name()) if notify.isValid() else None,
                prop.isConstant(),
            )
        )

    assert _nev(meta.className()) == "ImportSourceController"
    assert metodusok == _QML_METODUSOK
    assert tulajdonsagok == _QML_TULAJDONSAGOK

    mro = [
        base.__name__
        for base in controller.ImportSourceController.__mro__
        if base.__name__
        in {
            "ImportSourceControllerStateMixin",
            "ImportSourceControllerScanningMixin",
            "BackgroundWorkerMixin",
        }
    ]
    assert mro == [
        "ImportSourceControllerStateMixin",
        "ImportSourceControllerScanningMixin",
        "BackgroundWorkerMixin",
    ]
