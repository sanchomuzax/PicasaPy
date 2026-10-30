"""A projektlapok állapota és navigációja önálló QML-komponens (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_COMPONENT = _QML / "PicasaPy/MainProjectTabs.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"

_PROPERTY_NAMES = (
    "collageTabId",
    "movieMakerTabId",
    "movieMakerTabOpen",
    "documentTabsBottom",
    "activeDocumentTabId",
    "movieMakerActive",
    "backToMovieMakerPrompted",
    "openProjectTabs",
    "libraryFrameVisible",
    "slideshowRunning",
    "backToCollagePrompted",
)
_FUNCTION_NAMES = (
    "collageSourceRows",
    "openCollageFromRows",
    "openMovieFromRows",
    "openMovieMakerTab",
    "openMovieClipCollector",
    "returnToMovieMaker",
    "closeMovieMakerTab",
    "openCollageTab",
    "openSavedMovie",
    "openSavedCollage",
    "locateSavedCollage",
    "folderOfPath",
    "openCollageNodeInEditor",
)


def test_a_projektlap_allapot_regisztralt_800_sor_alatti_komponens():
    assert _COMPONENT.is_file(), "hiányzik a MainProjectTabs.qml"
    assert len(_COMPONENT.read_text(encoding="utf-8").splitlines()) < 800
    assert "MainProjectTabs 1.0 MainProjectTabs.qml" in (
        _QMLDIR.read_text(encoding="utf-8")
    )


def test_a_foablak_megtartja_a_projektlapok_neveit_es_fuggvenyeit():
    main = _MAIN.read_text(encoding="utf-8")
    assert re.search(r"MainProjectTabs\s*\{\s*id:\s*mainProjectTabs", main, re.DOTALL)
    for name in _PROPERTY_NAMES:
        assert re.search(rf"\b{name}\b", main), f"eltűnt a publikus tulajdonság: {name}"
        assert f"mainProjectTabs.{name}" in main
    for name in _FUNCTION_NAMES:
        assert re.search(rf"function\s+{name}\s*\(", main), (
            f"eltűnt a publikus függvény: {name}"
        )
        assert f"mainProjectTabs.{name}(" in main


def test_a_komponens_kotelezoen_kapja_a_gazdaobjektumokat_es_a_forditott_cimeket():
    component = _COMPONENT.read_text(encoding="utf-8")
    main = _MAIN.read_text(encoding="utf-8")
    for name in (
        "hostWindow",
        "hostController",
        "hostDocumentTabStrip",
        "hostSlideshow",
        "hostCreateDialogs",
        "collageTitle",
        "movieMakerTitle",
    ):
        assert re.search(rf"required\s+property\s+var\s+{name}\b", component), (
            f"hiányzó kötelező tulajdonság: {name}"
        )
    assert 'collageTitle: qsTr("Collage")' in main
    assert 'movieMakerTitle: qsTr("Movie Maker")' in main
    assert "qsTr(" not in component, "a fordítási kontextusnak Main.qml-ben kell maradnia"
    for name in _PROPERTY_NAMES:
        assert re.search(rf"\bproperty\s+\w+\s+{name}\b", component), (
            f"hiányzó komponens-tulajdonság: {name}"
        )
    for name in _FUNCTION_NAMES:
        assert re.search(rf"function\s+{name}\s*\(", component), (
            f"hiányzó komponens-függvény: {name}"
        )
