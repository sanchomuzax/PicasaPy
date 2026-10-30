"""A kollázsvezérlő bontása őrizze meg az API-t és a forrásszöveget (#6254)."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from picasapy.app import collage_controller
from picasapy.app.controller import AppController


_GYOKER = Path(__file__).resolve().parents[1]
_APP = _GYOKER / "src" / "picasapy" / "app"
_UJ_MODULOK = (
    "collage_controller_state.py",
    "collage_controller_settings.py",
)

# A bontás előtti collage_controller.py CollageMixin-metódusainak forráslenyomata.
# A lenyomat a dekorátortól a függvény utolsó soráig vett UTF-8 bájtokra készül.
_EREDETI_FORRAS_SHA256 = {
    "_apply_source_album_fields": "c329adc8af796077d4a7ff6b2bced17d30594adc19ca5ce5081c3a4a91722716",
    "_apply_zero_spacing_shadow_rule": "e683b6a7839236d9a71fc3de88d6d664671f82be33445896693cd6d0ef51bf07",
    "_capabilities": "cf2a98943a8be74683ab23cb37b0e0ec9b90a31c3b758e128d45e7b6fcce75f8",
    "_current_sources": "8c1c70f9a8506ebe10af7ff885d5f7ef33c365880fe1d5824cc12366e80ab89c",
    "_ensure_collage_panel": "63039c9cc64889fc37f4181d005ca8688935b3e15addbd112290ae3e025293dd",
    "_nodes": "0a2ca8c5419bb15f78077c5e2a3a3d50dc984d6564ebd181ce0b72e4f85bd7bb",
    "_relayout": "a0a6689b1a5db44e3f52f248f6d1ce863cb6d383f79e71383ece048210161330",
    "_relayout_for_page_shape": "662ab2158e6ac46e936d02f8cf7ddf88d15844343d1d064039b424ecf38936ab",
    "_rng": "6b4c904d3ad488231a07b26b8b4a666bdbeb0b68a182e98e16b8af98580ff6d1",
    "_screen_ratio": "ebe78247be0c53d0ded715fdf1b7a0a370ec07e47e14e9ce104dcc9fcff25ffc",
    "_set_dirty": "8ad35d6e0b8e7a268e41937fb6412f3d5b7f09199755985206d92ee7642edc79",
    "_set_frame_center": "a7c973719e1ce4f469854ee465ce5e856e562b113c95fdeecbcedf7275b7a1e0",
    "_set_nodes": "81a3f33517f12661b95561b36f4f4c153eb8e1732931d07e759e42d1ba3e52cd",
    "_sources_from_rows": "27329e3d1fce1734db8f2e6a1cb70938cfe32b25b6eee4d2a2b0d11d258d0c04",
    "_title_from_sources": "e29e5e43a4e37a34e158034ee19322bab4a6b557068cb44feaeeb757d4766422",
    "closeCollage": "359a71e2a85c8f161b7e0c79df46fb034782163c2430681b773f0259a71473a2",
    "collageAngleCaption": "3d9ec3e984da8bdd0ab6ccfe2f2ce5ccb4b8e958e7624893c9f3050fe9948411",
    "collageBaseNodeWidth": "15e093b2dab88966a1a2ebeeea63f79e747a41006ca1093aec19a33216d40058",
    "collageBorder": "4f6785bf78e4df642b1f7d8e4df5b6f05533e82050aff74f3ce324a2a87b88d0",
    "collageCapabilities": "f7c5c77969f82ca9b9bb11f88dcc7a510851dd1cd074f727b0ac7617514f69f0",
    "collageCaptions": "f52b2bfb061276dbd52e801e723375578b66125d4485d358061662e326467512",
    "collageClipCount": "e9cc453e77eb8c19231cb7f113f670ad30e078611bdad7b988a997a8b13492ea",
    "collageDirty": "3ac03311a413c608f41919bd345e7a76ce3a46d38861a08a5d756b30c939a2df",
    "collageFormatKey": "ee11661d989a53bca0995b9784cc413feef737a8d0c3bc9de9e8d37a61954fc2",
    "collageFrameCenter": "15ee09856cccfd7e59ea11bdf1bb0d09beea25de1d6192a73a71216e86fed281",
    "collageGroupRect": "08a49e1138472c03573596ba47d40467bc6e53253808332568b97ec6ffefeec5",
    "collageNodes": "f2fea40198e5024ca18f240281a70e00f384058ef626259f1909b7af7e98a8a6",
    "collageOpen": "45c621beab05d4e4cf157029abb4740b39bea883e65e8d0fc12bdc9aed7a3acd",
    "collageOrientation": "eff5b45d418d9623688985ce1cfd964fac0b74530353ddd94defbb7579ed2ccc",
    "collagePageRatio": "989584d72248c1270467efbd1584f3b29ef4559b0784b1a43a810228bebcd883",
    "collageScaleCaption": "fdf63022fd79e4647f19e3b02a359f2839501c84fed41104a6d323e275555b1b",
    "collageSelection": "09c0f2127dee37800fb8eaed1a20fb93fd87cc53b8497b5b9a5d0209326b6e60",
    "collageShadows": "ffa617f7962950feef811855bfb630e1f59e32465de849a838c86a56fa4cc7f0",
    "collageSpacing": "49ef859e17abc0aa7e3211f6492dd07fa54db138e4238d7de624b669702bc98f",
    "collageTheme": "9af446989f1cbc8497eaae17711f16c35f72b701d75916d1d39482d85cc8a71c",
    "openCollage": "b5d219aaab3edab68eec34249597fcce88d2063736fe2cd4877285f8941fdf54",
    "setCollageBorder": "9245a03a4ae909d493d888d115a0babcb97e7215dc09234a0868db5c64a87b9f",
    "setCollageCaptions": "c6066538362767da92598842fda39d950ff381b50a56ac6712fc0c4a774a8cae",
    "setCollageFormat": "00b45c3d1324872bd7711c2e2030bd7dd710cd6681dad701874d893d911f3499",
    "setCollageOrientation": "489cc3f225d4235a2612c540cd3986973f39ea611412357cdf36a3f3d6cba02f",
    "setCollageShadows": "79212bb5013663ac50a02bf9c9fd8def24eae05875113d156254bbe08baf2baf",
    "setCollageSpacing": "f80083f2b3d084ea080c6e5e959302e0e4711e6f0ba1b490b44c9762010d4db6",
    "setCollageTheme": "23c93a5fd07fb883670705bee4d715e1ac6dcb9db054152d00277b9c3a50897a",
}

_REGI_NYILVANOS_NEVEK = {
    "BACKGROUND_MODES",
    "BORDER_THEMES",
    "COLLAGE_OUTPUT_DIR_KEY",
    "COLLAGE_THEMES",
    "CONTACTSHEET",
    "CollageBackgroundMixin",
    "CollageCanvasMixin",
    "CollageMixin",
    "CollageNode",
    "CollageNodeModel",
    "CollageSaveMixin",
    "CollageShadowMixin",
    "FALLBACK_SCREEN_RATIO",
    "MULTIEXP",
    "MsvcRandom",
    "NOBORDER",
    "ORIENTATIONS",
    "Path",
    "Property",
    "QColor",
    "QGuiApplication",
    "QObject",
    "Sequence",
    "Signal",
    "Slot",
    "WHITEBORDER",
    "album_fields_of",
    "annotations",
    "canvas",
    "capabilities_for",
    "capability_map",
    "common_source_folder_name",
    "group_bounds",
    "initial_node_width",
    "is_known_format",
    "layout",
    "page_ratio",
    "prefs",
    "selected_indices",
    "threading",
    "with_selection",
}

_QT_META_SHA256 = "234829d6617512fabb776cc33f50b751cceff8973ef60fd81381161f538ae25d"
_QT_META_METHODS = 79
_QT_META_PROPERTIES = 23


def _method_source_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    paths = [_APP / "collage_controller.py", *(_APP / name for name in _UJ_MODULOK)]
    for path in paths:
        raw = path.read_bytes()
        lines = raw.splitlines(keepends=True)
        tree = ast.parse(raw.decode("utf-8"), filename=str(path))
        for cls in tree.body:
            if not isinstance(cls, ast.ClassDef):
                continue
            for node in cls.body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
                digest = hashlib.sha256(b"".join(lines[start - 1 : node.end_lineno])).hexdigest()
                assert node.name not in hashes, f"többszörös kollázsmetódus: {node.name}"
                hashes[node.name] = digest
    return hashes


def _as_text(value) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return bytes(value).decode()


def _qt_collage_meta_rows() -> list[str]:
    names = {
        name
        for cls in collage_controller.CollageMixin.__mro__
        if cls is not object
        for name in cls.__dict__
        if not name.startswith("_")
    }
    meta = AppController.staticMetaObject
    rows = []
    for index in range(meta.methodCount()):
        method = meta.method(index)
        if _as_text(method.name()) in names:
            # A típusnevek PySide-verziónként másképp íródnak (helyben 6.8, a
            # CI-n újabb), ezért a lenyomat a metódus fajtáját, nevét és
            # paraméterszámát rögzíti.
            rows.append(
                "M:"
                f"{method.methodType().name}:"
                f"{_as_text(method.name())}:"
                f"{method.parameterCount()}"
            )
    for index in range(meta.propertyCount()):
        prop = meta.property(index)
        name = _as_text(prop.name())
        if name not in names:
            continue
        notify = _as_text(prop.notifySignal().name()) if prop.hasNotifySignal() else ""
        # Az isWritable a csak olvasható tulajdonságra is PySide-verziónként
        # mást ad (6.8: 1, újabb: 0), ezért nem része a lenyomatnak.
        rows.append(f"P:{name}:{notify}:{int(prop.isConstant())}")
    return sorted(rows)


def test_a_regi_importut_es_minden_nyilvanos_nevet_megtartja() -> None:
    hianyzo = sorted(nev for nev in _REGI_NYILVANOS_NEVEK if not hasattr(collage_controller, nev))
    assert not hianyzo, f"hiányzó régi collage_controller nevek: {hianyzo}"
    aktualis_nyilvanos = {nev for nev in vars(collage_controller) if not nev.startswith("_")}
    assert aktualis_nyilvanos == _REGI_NYILVANOS_NEVEK, (
        "a collage_controller nyilvános nevei megváltoztak: "
        f"hiányzó={sorted(_REGI_NYILVANOS_NEVEK - aktualis_nyilvanos)}, "
        f"új={sorted(aktualis_nyilvanos - _REGI_NYILVANOS_NEVEK)}"
    )
    assert collage_controller.__all__ == [
        "BACKGROUND_MODES",
        "COLLAGE_OUTPUT_DIR_KEY",
        "CollageMixin",
    ]


def test_a_bontott_metodusok_forrasszovege_bajtra_azonos() -> None:
    actual = _method_source_hashes()
    missing = sorted(set(_EREDETI_FORRAS_SHA256) - actual.keys())
    extra = sorted(actual.keys() - _EREDETI_FORRAS_SHA256.keys())
    changed = sorted(
        name
        for name, expected in _EREDETI_FORRAS_SHA256.items()
        if actual.get(name) != expected
    )
    assert not missing and not extra and not changed, (
        f"hiányzó metódusok: {missing}; új metódusok: {extra}; "
        f"eltérő forráshash: {changed}"
    )


def test_a_kontroller_modulok_400_sor_alatt_maradnak() -> None:
    paths = [_APP / "collage_controller.py", *(_APP / name for name in _UJ_MODULOK)]
    missing = [path.name for path in paths if not path.is_file()]
    assert not missing, f"hiányzó bontott modul(ok): {missing}"
    sizes = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in paths
    }
    too_long = {name: count for name, count in sizes.items() if count >= 400}
    assert not too_long, f"a kollázsvezérlő moduljai elérték a 400 soros határt: {too_long}"


def test_a_qt_metaobjektum_kollazs_felulet_valtozatlan() -> None:
    rows = _qt_collage_meta_rows()
    digest = hashlib.sha256("\n".join(rows).encode()).hexdigest()
    methods = sum(row.startswith("M:") for row in rows)
    properties = sum(row.startswith("P:") for row in rows)
    assert (digest, methods, properties) == (
        _QT_META_SHA256,
        _QT_META_METHODS,
        _QT_META_PROPERTIES,
    ), f"a Qt-metaobjektum felülete eltér: {rows}"


def test_az_appcontroller_mixinek_sorrendje_valtozatlan() -> None:
    mro = [cls.__name__ for cls in AppController.__mro__]
    # A #6252 a CreateMixin alá saját mixineket tett, ezért a három osztály
    # már nem szomszédos az MRO-ban; a relatív sorrendjük az állítás.
    sorrend = [mro.index(nev) for nev in ("CreateMixin", "PosterMixin", "CollageMixin")]
    assert sorrend == sorted(sorrend), f"az AppController MRO-sorrendje megváltozott: {mro}"
