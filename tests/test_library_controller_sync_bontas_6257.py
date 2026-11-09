"""A könyvtárszinkron bontása őrizze meg a forrást és a régi felületet."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


_GYOKER = Path(__file__).resolve().parents[1]
_APP = _GYOKER / "src" / "picasapy" / "app"

# #6440: a dirty-worker két függvénye a háttérmunka-jegy és a munkanév miatt
# változott. #6696: a rescan és a worker a hálózati gyökérre szűrt időzítést
# kezeli; a többi lenyomat változatlan.
# #6698: a rescan, a worker és a dirty-adag a háttérprioritás és a kötegelt
# albumtakarítás miatt változott.
_MOZGATOTT_FORRASOK = {
    # #6476: szándékos változás, a változatlan mappa célzott szinkronja kimarad
    ("library_controller_sync_dirty.py", "_LibrarySyncDirtyMixin", "_on_folders_dirty"):
        "38dccd48ba10eeb0817cbd760a789ed50c65d0abd232bad81114f669af5870e0",
    ("library_controller_sync_sweep.py", "_LibrarySyncSweepMixin", "_root_for_folder"):
        "f5afe5e6920a3047137f970df48e26bd2eeec92e67c8b544b126859d86d66efd",
    ("library_controller_sync_sweep.py", "_LibrarySyncSweepMixin", "_poll_current_folder"):
        "f5bfba83bc9be104e360305f62562ca79816cdfae78965cab55309b81375025f",
    (
        "library_controller_sync_sweep.py",
        "_LibrarySyncSweepMixin",
        "_projekt_kimeneti_mappak",
    ): "17b6715a632027495cc7a9e37e7f2d2ce3166fe2cfd95bc320ff055d838c7494",
    (
        "library_controller_sync_sweep.py",
        "_LibrarySyncSweepMixin",
        "_projekt_kimenet_felmeres",
    ): "bca51628d1fc889ee30820a77da095659e0f7f6e0fa7af6aa04253d926834383",
    ("library_controller_sync_sweep.py", "_LibrarySyncSweepMixin", "_sweep_candidates"):
        "86847b9a272748e9fb430fd8f783816a38e8f0fef89d96f1f23a54a4aa7e3778",
    ("library_controller_sync_sweep.py", "_LibrarySyncSweepMixin", "_stale_feed_folders"):
        "0601d410bcca2cd082900df88b0f8edad2e0af553f2027d7e48582c1312a8209",
    ("library_controller_sync_rescan.py", "_LibrarySyncRescanMixin", "rescan"):
        "2f1d5760ed225142b887b30c65b70d8bc5f4a352dd7fdecd78694a2634d0b02b",
    ("library_controller_sync_rescan.py", "_LibrarySyncRescanMixin", "_sync_worker"):
        "0d8b4c19b48d127012deca61a38f3dc39712cdc8107001b0d28aab88c3a28ce8",
    (
        "library_controller_sync_dirty.py",
        "_LibrarySyncDirtyMixin",
        "_flush_pending_dirty",
    ): "7dc1a0a72d68dab3d1980fb825db9d06e89e1b10ae7b2bfe91b88244e980ced9",
    (
        "library_controller_sync_dirty.py",
        "_LibrarySyncDirtyMixin",
        "_retry_locked_dirty_folders",
    ): "6bb679a2b69e86708bbde6386d78b5f756e30058b6b93941bda53546aa209fe0",
}

_REGI_NYILVANOS_NEVEK = {
    "DirectoryChange",
    "Path",
    "Slot",
    "annotations",
    "folder_scan_stamps",
    "get_app_busy_registry",
    "importlib",
    "next_sweep_batch",
    "open_index",
    "remove_folder_tree",
    "sqlite3",
    "stale_folders",
    "stat",
    "sys",
}

_QT_META_SHA256 = "92878aa84259e05f2e131b8647839f7404a58c83f54c47d908901cfe5d410188"
_MIXIN_SORREND = (
    "LibraryMixin",
    "_LibraryActivityMixin",
    "_LibraryFoldersMixin",
    "_LibrarySyncMixin",
    "_LibrarySyncDirtyMixin",
    "_LibrarySyncSweepMixin",
    "_LibrarySyncRescanMixin",
    "_LibraryResyncMixin",
)


def _fuggveny_forras_hash(fajl: Path, osztalynev: str, fuggvenynev: str) -> str:
    nyers = fajl.read_bytes().replace(b"\r\n", b"\n")  # windowsos checkout: CRLF (#6260)
    sorok = nyers.splitlines(keepends=True)
    fa = ast.parse(nyers.decode("utf-8"), filename=str(fajl))
    osztalyok = [
        node
        for node in fa.body
        if isinstance(node, ast.ClassDef) and node.name == osztalynev
    ]
    assert len(osztalyok) == 1, f"{fajl.name}:{osztalynev} hiányzik vagy többszörös"
    fuggvenyek = [
        node
        for node in osztalyok[0].body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == fuggvenynev
    ]
    assert len(fuggvenyek) == 1, f"{fajl.name}:{osztalynev}.{fuggvenynev} hiányzik vagy többszörös"
    fuggveny = fuggvenyek[0]
    kezdo_sor = min([fuggveny.lineno, *(d.lineno for d in fuggveny.decorator_list)])
    return hashlib.sha256(b"".join(sorok[kezdo_sor - 1 : fuggveny.end_lineno])).hexdigest()


def _qt_meta_lenyomat() -> str:
    from picasapy.app.controller import AppController

    from picasapy.app import library_controller_sync as facade

    # Csak a szinkron-mixincsalád saját tagjai: a teljes AppController
    # lenyomatát bármelyik másik mixin új tagja eltörné.
    nevek = {
        nev
        for cls in facade._LibrarySyncMixin.__mro__
        if cls is not object
        for nev in cls.__dict__
    }
    meta = AppController.staticMetaObject
    methods = []
    for index in range(meta.methodCount()):
        method = meta.method(index)
        if bytes(method.name()).decode("utf-8") not in nevek:
            continue
        kind = method.methodType()
        methods.append(
            (
                kind.name if hasattr(kind, "name") else str(kind),
                bytes(method.name()).decode("utf-8"),
                method.parameterCount(),
            )
        )
    properties = []
    for index in range(meta.propertyCount()):
        prop = meta.property(index)
        if prop.name() not in nevek:
            continue
        notify = prop.notifySignal()
        signal = bytes(notify.name()).decode("utf-8") if notify.isValid() else ""
        properties.append((prop.name(), signal, prop.isConstant()))
    # A mixinek felbontásakor a Qt metódustáblájának indexei átrendeződhetnek;
    # a felületet a tagok (nem a belső sorszámuk) alkotják.
    payload = json.dumps(
        {"methods": sorted(methods), "properties": sorted(properties)},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_a_regi_importutvonal_es_a_nyilvanos_nevek_megmaradnak() -> None:
    from picasapy.app import library_controller_sync as facade

    hianyzok = sorted(nev for nev in _REGI_NYILVANOS_NEVEK if not hasattr(facade, nev))
    assert not hianyzok, f"hiányzó régi szinkronnév: {hianyzok}"
    assert {nev for nev in vars(facade) if not nev.startswith("_")} == _REGI_NYILVANOS_NEVEK
    assert hasattr(facade._LibrarySyncMixin, "_on_folders_dirty")
    assert hasattr(facade._LibrarySyncMixin, "rescan")


def test_a_mozgatott_fuggvenyek_forrasszovege_bajtra_azonos() -> None:
    tenyleges = {
        (fajlnev, osztalynev, fuggvenynev): _fuggveny_forras_hash(
            _APP / fajlnev, osztalynev, fuggvenynev
        )
        for fajlnev, osztalynev, fuggvenynev in _MOZGATOTT_FORRASOK
    }
    assert tenyleges == _MOZGATOTT_FORRASOK, "a mozgatott függvények forrásszövege megváltozott"


def test_a_bontott_modulok_400_sor_alatt_maradnak() -> None:
    fajlok = (
        _APP / "library_controller_sync.py",
        _APP / "library_controller_sync_dirty.py",
        _APP / "library_controller_sync_sweep.py",
        _APP / "library_controller_sync_rescan.py",
    )
    hianyzok = [fajl.name for fajl in fajlok if not fajl.is_file()]
    assert not hianyzok, f"hiányzó szinkronmodul(ok): {hianyzok}"
    tulhosszuak = {
        fajl.name: len(fajl.read_text(encoding="utf-8").splitlines())
        for fajl in fajlok
        if len(fajl.read_text(encoding="utf-8").splitlines()) >= 400
    }
    assert not tulhosszuak, f"a bontott modul elérte a 400 soros határt: {tulhosszuak}"


def test_a_qt_metaobjektum_es_a_mixinek_sorrendje_valtozatlan() -> None:
    from picasapy.app.controller import AppController

    sorrend = tuple(
        cls.__name__
        for cls in AppController.__mro__
        if cls.__name__ in set(_MIXIN_SORREND)
    )
    assert sorrend == _MIXIN_SORREND
    assert _qt_meta_lenyomat() == _QT_META_SHA256
