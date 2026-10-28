"""Forrásőrzők a főablak vetítési és néző komponenseihez (#5955)."""

from pathlib import Path
import re


_ROOT = Path(__file__).resolve().parents[1]
_MAIN = _ROOT / "src/picasapy/app/qml/Main.qml"
_QML_DIR = _ROOT / "src/picasapy/app/qml/PicasaPy/qmldir"
_COMPONENTS = {
    "MainWindowToolbar": ("MainWindowToolbar.qml", "mainToolbar"),
    "MainSlideshow": ("MainSlideshow.qml", "slideshowView"),
}


def test_felso_sav_vetites_es_nezo_onallo_komponensben_marad():
    main = _MAIN.read_text(encoding="utf-8")
    qmldir = _QML_DIR.read_text(encoding="utf-8")

    for type_name, (filename, object_name) in _COMPONENTS.items():
        component_path = _QML_DIR.parent / filename
        assert component_path.is_file(), f"hiányzik a {filename} komponens"
        source = component_path.read_text(encoding="utf-8")
        assert re.search(
            rf"^{type_name} 1\.0 {re.escape(filename)}$", qmldir, re.MULTILINE
        ), f"hiányzik a {type_name} qmldir-exportja"
        assert f'objectName: "{object_name}"' in source

    for old_type in ("MainToolbar", "SlideshowView"):
        assert not re.search(rf"\b{old_type}\s*\{{", main), (
            f"a {old_type} még inline a Main.qml-ben"
        )
    for component_type in _COMPONENTS:
        assert re.search(rf"\b{component_type}\s*\{{", main), (
            f"hiányzik a {component_type} példány a Main.qml-ből"
        )

    # A teljes nézőblokk a helyén marad: a komponensváltozat két állapotban
    # 29 képponttal tért el, az inline változat ott 0 eltérést adott.
    assert re.search(r"^    PhotoViewer\s*\{\n        id: photoViewer", main, re.MULTILINE)
