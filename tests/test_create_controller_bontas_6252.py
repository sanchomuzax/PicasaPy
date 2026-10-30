"""A Létrehozás vezérlő bontása őrizze meg a régi API-t (#6252)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from picasapy.app import create_controller
from picasapy.app.controller import AppController


_GYOKER = Path(__file__).resolve().parents[1]
_FORRAS = _GYOKER / "src" / "picasapy" / "app"
_UJ_MODULOK = ("create_movie_mixin.py", "create_collage_mixin.py")

_REGI_NYILVANOS_NEVEK = frozenset(
    {
        "BORDER_THEMES",
        "COLLAGE_THEMES",
        "CollagePreviewProvider",
        "CreateMixin",
        "ElementTree",
        "MovieSettings",
        "MovieTransitionPreviewProvider",
        "MxfAtmenet",
        "MxfForras",
        "MxfProjekt",
        "MxfSzovegParam",
        "NOBORDER",
        "PICASA_INI_NAME",
        "Path",
        "PicasaCollageSettings",
        "PosterMixin",
        "Property",
        "QImageReader",
        "QUrl",
        "Signal",
        "Slot",
        "album_photos",
        "annotations",
        "coerce_ui_preference_flag",
        "collage_output",
        "collage_prefs",
        "discard_autosave",
        "export_movie",
        "film_zene_mappabol",
        "has_recoverable_draft",
        "load_or_empty",
        "logger",
        "logging",
        "make_picasa_collage",
        "math",
        "open_index",
        "project_from_nodes",
        "projekt_utvonal",
        "read_folder_music",
        "read_mxf",
        "recover_orphan_draft",
        "sqlite3",
        "to_local_path",
        "write_autosave",
        "write_collage",
        "write_mxf",
    }
)

# SHA-256 az eredeti dekorátortól a definíció záró soráig vett UTF-8 bájtokra.
# A definíciók a create_controller.py-ból kerültek ide átvételre a bontáskor.
_EREDETI_FORRAS_SHA256 = {
    "film_zene_mappabol": "8719975db859d37671c19977473a4f15d75e21fcf3143648e2eb7968d2aeea2e",
    "_movie_call": "c86f6b2837f23ce478ed8d2ce4428fac4b797aa6168379a2c4052f0429bee8b2",
    "_collage_call": "41a8be66e34fc15cc7da2ec25faa0af45b67f7d8da6f1688c822ed766c274303",
    "_write_movie_project": "8ff09596dd47a5e990c9c4cdc61127b5ee1c3bcef3e8033b2a6c2ae82c363cdb",
    "filmMusicForSources": "0f129ff391d2026c094ceb4f32b0f693a83d6407386fb89bb322b54f7f541378",
    "_sources_belong_to_album": "8c5628801781d170516cf8668dd4b25fb87f26e3fe977e5a53777b2141cbefb3",
    "_ensure_collage_wired": "7e42e28808116579372d185dc6d9f8fd948df264602223a473f1bbcb41463bb1",
    "movieResolutionIndex": "9899a5d80a8e322b2ccdd58f95b7165256858afbf35efc0fb56f798b0d03cffb",
    "faceMovieResolutionIndex": "b04037a359ad5cb6e2073cd287babffd8b7e4d869037a14fdbd9e2e31bc76c62",
    "setMovieResolutionIndex": "321b3195ea063953aef053495b96c143c4d3edc9984ce5bb554e42e85efe7a7f",
    "movieSlideDuration": "80be3251f622147c75551d4d17daff0f360b7f148bcc67067bb4a33705236cbc",
    "setMovieSlideDuration": "33a121218c78d76c54c66dfc623b82419701b416fbaa65b165d9de0836f1f2bd",
    "movieTransition": "90a7fbfcf6483140d97b65c2d2564136c2a26c729af18655703ade5023b775cb",
    "setMovieTransition": "465e1acb34762327818d921cd63c1c88463289c0197282b35618b6b879ac97b5",
    "movieVolume": "a19b0a65e4f183ac535edd49523bda2e75d8b95f1aa8e073689eff41e7deb386",
    "setMovieVolume": "c7f24637035e5ff1aef7a8b89d1ac3dd125a5b636f1c4badcad9d79742f33e16",
    "moviePreference": "925d0db1f8a7096626af365b56474007a1c5182944259da0f271321f7a8c7727",
    "setMoviePreference": "7ad50ce75794c03c64002925d0629cd123ea9e73b5434a1b459b188efbbbc722",
    "movieSourceUrls": "df313932720ec10e7d7fe6cef180ffd6909bdd4fdd5133cf5fe258a237dc3e64",
    "movieClipNames": "66c4916a32af97386972d6e3ef8f15ccd06d03f3a3351570c6eec9fb42066428",
    "selectedMovieSourceUrls": "11dd13e04aee945c634d1527764a43744e642ddc7cd213eb34d1829464a9c69e",
    "movie_transition_preview_provider": "89ee2322e884815ef2806692d2c7c5d09805490792278e36ac4e2199ed6f5a7e",
    "requestMovieTransitionPreview": "bd9ea71cda700f6bfa120504f894e73982d02aa51252c99b19fe1fdc581bcaaf",
    "prefetchMovieTransitionPreview": "375fe339dd68df758fa0b7e6de3abd92e7b03f4e8acd25863b33a4e998f81ba6",
    "moviePreviewImageSize": "fbb7762fb65b1bd2da482d473be6acd4cacd24ea8bd3dafa8795b95ee3c9fd87",
    "collage_preview_provider": "ff6601694dcc9787f29ec42511ca3d5908ad442fdf5435f73a03edfcd30d0356",
    "_collage_draft_dir": "4b01b8ff267bb40cd386ab5fa3bfdc2f55fd14f6ad7c1d3b7ab618d2ff582ebb",
    "_save_collage_draft": "3290bfeebc33c7b6a19e0423f14a5280c996b2934e99d2519381ff9d2d9468f8",
    "_drop_collage_draft": "51948b70dfcd325fab7d47f6d87231961d49c01c510cfafbb78dfd61cfec6223",
    "collageDraftAvailable": "68b0ffd20e81f6ee2c01b401baffd1827fa56ab1c4ebbc89884141df93763f65",
    "refreshCollageDraft": "9cda4fc2aa3e109971a2e2fb083e67dc2a7451499bdd5a3540e982c4f3596d12",
    "discardCollageDraft": "80fc0c966a49ae3bf7c921e1c6d1ae582595fcd672525392ffbfbe14f9c1f98b",
    "_selected_sources": "85705f4810437ff40267276a65ceb2f54e168b5fa164cf3fb1461fbd1091997c",
    "_tray_sources": "fd136cb426702bcfc1e0d994bb6fad6488cd108b3bcf5d3dfc9ccccad3ba555c",
    "_sources_for": "ac74392535c2b3918d6607cca1f7fba332f2f67281f235e0c4ada0aef5483eb2",
    "requestCollagePreview": "0c86d57127fd2c9fdfb4a707bb0f660bb1e2c62fc841a21de9600c9753c3df89",
    "shuffleCollage": "f9b52024b13838863ef4d96ea1f3e11cff01020f8f18d5b8a87146063cc9af1f",
    "collageSeed": "558beee71a629d579c140d6947d91cf08f5815cc48d5a8994e204884af8023f6",
    "makeCollage": "ed5f46f6f559044e99e4e7c095b527888c2156ee134c941e3adf69d8aa06830c",
    "_alapertelmezett_film_cel": "19c3ac9a73095bb7a92a2b6bab426d12f377420ff20b706dd0fa85cfbafae6d8",
    "_film_beallitas": "88dd3128f0e2859ed944a579470970f2ccb5cd423e2cfbbececcdc220f2da064",
    "_film_projekt": "d7e5ec63fc03b569e4a61f770969c14a9faa319c44ba1668244c7e2e657f4c59",
    "_film_projekt_utja": "08b6fb4629cb37d23a807533cb3b25b1ceac2ee278d9dd3d8b825fa52f55196f",
    "hasMovieProject": "e2e8da06e32800d9865c8a59aaf215f2ae1ee5f2ea6e856efa237ca2978f5976",
    "movieProject": "62282d481f1f58fca75c97cc704f55dceda2ec9685c3185f9d75f5e7078574e5",
    "exportMovie": "a8cdef85d6af3d23ed720f5948ce0d74b2230c84d8c6b25cc02a0d8e32dd622d",
}

_CREATE_METHODS = (
    ("collageDraftAvailableChanged()", "Signal", "void"),
    ("collageFailed(QString)", "Signal", "void"),
    # A kiinduló AppController metaobjektuma kétszer tartalmazza ezt a jelet.
    ("collageFailed(QString)", "Signal", "void"),
    ("collageFinished(QString,int,int,int)", "Signal", "void"),
    ("collagePreviewFailed(QString)", "Signal", "void"),
    ("collagePreviewReady(int)", "Signal", "void"),
    ("discardCollageDraft()", "Slot", "void"),
    ("exportMovie(QVariantList,QString,int,double)", "Slot", "void"),
    ("exportMovie(QVariantList,QString,int,double,int)", "Slot", "void"),
    ("exportMovie(QVariantList,QString,int,double,int,QString,double,QString,int)", "Slot", "void"),
    ("exportMovie(QVariantList,QString,int,double,int,QString,double,QString,int,QVariantList)", "Slot", "void"),
    ("exportMovie(QVariantList,QString,int,double,int,QString,double,QString,int,QVariantList,QVariantMap)", "Slot", "void"),
    ("filmMusicForSources(QVariantList)", "Slot", "QString"),
    ("hasMovieProject(QString)", "Slot", "bool"),
    ("makeCollage(QVariantList,QString,QString)", "Slot", "void"),
    ("makeCollage(QVariantList,QString,QString,QString)", "Slot", "void"),
    ("movieClipNames(QVariantList)", "Slot", "QVariantList"),
    ("movieFailed(QString)", "Signal", "void"),
    ("movieFinished(QString,int,int,int)", "Signal", "void"),
    ("moviePreference(QString)", "Slot", "bool"),
    ("moviePreferencesChanged()", "Signal", "void"),
    ("moviePreviewImageSize(QString)", "Slot", "QVariantList"),
    ("movieProgress(int,int)", "Signal", "void"),
    ("movieProject(QString)", "Slot", "QVariantMap"),
    ("movieSourceUrls(QVariantList)", "Slot", "QVariantList"),
    ("movieTransitionPreviewReady(QString,int)", "Signal", "void"),
    ("prefetchMovieTransitionPreview(QString,QString,int,int,bool,bool,bool,bool,int,int,double)", "Slot", "void"),
    ("refreshCollageDraft()", "Slot", "void"),
    ("requestCollagePreview(QVariantList,QString,QString)", "Slot", "void"),
    ("requestMovieTransitionPreview(QString,QString,QString,double,int,int,bool,bool,bool,QString,QString,bool,int,int,double)", "Slot", "int"),
    ("selectedMovieSourceUrls(QVariantList)", "Slot", "QVariantList"),
    ("setMoviePreference(QString,bool)", "Slot", "void"),
    ("setMovieResolutionIndex(int)", "Slot", "void"),
    ("setMovieSlideDuration(double)", "Slot", "void"),
    ("setMovieTransition(QString)", "Slot", "void"),
    ("setMovieVolume(int)", "Slot", "void"),
    ("shuffleCollage()", "Slot", "void"),
)
_CREATE_PROPERTIES = (
    ("collageDraftAvailable", "bool", "collageDraftAvailableChanged()"),
    ("faceMovieResolutionIndex", "int", "moviePreferencesChanged()"),
    ("movieResolutionIndex", "int", "moviePreferencesChanged()"),
    ("movieSlideDuration", "double", "moviePreferencesChanged()"),
    ("movieTransition", "QString", "moviePreferencesChanged()"),
    ("movieVolume", "int", "moviePreferencesChanged()"),
)


def _node_sha256(source: bytes, node: ast.AST) -> str:
    lines = source.splitlines(keepends=True)
    start = min(
        [node.lineno, *(decorator.lineno for decorator in getattr(node, "decorator_list", []))]
    )
    return hashlib.sha256(b"".join(lines[start - 1 : node.end_lineno])).hexdigest()


def _definicio_hashok() -> dict[str, set[str]]:
    hashes: dict[str, set[str]] = {}
    for filename in ("create_controller.py", *_UJ_MODULOK):
        fajl = _FORRAS / filename
        source = fajl.read_bytes().replace(b"\r\n", b"\n")  # windowsos checkout: CRLF (#6260)
        tree = ast.parse(source.decode("utf-8"), filename=str(fajl))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                hashes.setdefault(node.name, set()).add(_node_sha256(source, node))
            elif isinstance(node, ast.ClassDef):
                for member in node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        hashes.setdefault(member.name, set()).add(_node_sha256(source, member))
    return hashes


def _qml_meta_felulet():
    method_nevek = {signature.split("(", 1)[0] for signature, _, _ in _CREATE_METHODS}
    property_nevek = {name for name, _, _ in _CREATE_PROPERTIES}
    methods = []
    meta = AppController.staticMetaObject
    for index in range(meta.methodCount()):
        method = meta.method(index)
        signature = bytes(method.methodSignature()).decode("utf-8")
        if signature.split("(", 1)[0] in method_nevek:
            methods.append((signature, method.methodType().name, str(method.typeName())))
    properties = []
    for index in range(meta.propertyCount()):
        prop = meta.property(index)
        name = str(prop.name())
        if name in property_nevek:
            notify = (
                bytes(prop.notifySignal().methodSignature()).decode("utf-8")
                if prop.hasNotifySignal()
                else ""
            )
            properties.append((name, str(prop.typeName()), notify))
    return tuple(sorted(methods)), tuple(sorted(properties))


def test_a_regi_importut_minden_nyilvanos_nevet_megtartja() -> None:
    assert {name for name in vars(create_controller) if not name.startswith("_")} == _REGI_NYILVANOS_NEVEK


def test_a_bontott_fuggvenyek_forrasa_bajtra_azonos() -> None:
    aktualis = _definicio_hashok()
    elteresek = {
        name: sorted(aktualis.get(name, set()))
        for name, vart in _EREDETI_FORRAS_SHA256.items()
        if vart not in aktualis.get(name, set())
    }
    assert not elteresek, f"a bontott definíció forrásszövege eltért vagy hiányzik: {elteresek}"


def test_a_homlokzat_es_az_uj_modulok_400_sor_alatt_maradnak() -> None:
    fajlok = (_FORRAS / "create_controller.py", *(_FORRAS / nev for nev in _UJ_MODULOK))
    hianyzik = [fajl.name for fajl in fajlok if not fajl.is_file()]
    assert not hianyzik, f"hiányzó bontott modul(ok): {hianyzik}"
    sorok = {
        fajl.name: len(fajl.read_text(encoding="utf-8").splitlines())
        for fajl in fajlok
        if fajl.is_file()
    }
    assert all(db < 400 for db in sorok.values()), f"a 400 soros határt elérő modulok: {sorok}"


def test_a_create_qt_metaobjektum_felulet_valtozatlan() -> None:
    assert _qml_meta_felulet() == (
        tuple(sorted(_CREATE_METHODS)),
        tuple(sorted(_CREATE_PROPERTIES)),
    )
    mro = [cls.__name__ for cls in AppController.__mro__]
    index = mro.index("CreateMixin")
    assert mro[index - 1 : index + 4] == [
        "EditorControlsMixin",
        "CreateMixin",
        "_CreateMovieMixin",
        "_CreateCollageMixin",
        "PosterMixin",
    ]
