"""A főablak könyvtári kijelöléskezelése önálló QML-komponens (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_COMPONENT = _QML / "PicasaPy/MainLibrarySelectionState.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_kijeloleskezelo_regisztralt_es_800_sor_alatti():
    assert _COMPONENT.is_file(), "hiányzik a MainLibrarySelectionState.qml"
    component = _COMPONENT.read_text(encoding="utf-8")
    assert len(component.splitlines()) < 800
    assert "MainLibrarySelectionState 1.0 MainLibrarySelectionState.qml" in (
        _QMLDIR.read_text(encoding="utf-8")
    )
    assert re.search(
        r"MainLibrarySelectionState\s*\{\s*id:\s*mainLibrarySelectionState",
        _MAIN.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    for name in (
        "hostWindow",
        "hostController",
        "hostPhotoViewer",
        "hostMainDialogs",
        "hostPhotoContextMenu",
        "hostFolderPane",
        "hostScreensaverAlbumConfirmLoader",
        "hostFaceScanDialog",
        "hostFaceScanController",
    ):
        assert re.search(rf"required\s+property\s+var\s+{name}\b", component)
    assert 'hostController: typeof controller !== "undefined" ? controller : null' in (
        _MAIN.read_text(encoding="utf-8")
    )
    assert 'hostFaceScanController: typeof faceScanController !== "undefined"' in (
        _MAIN.read_text(encoding="utf-8")
    )
    assert re.search(r"property alias _lastFolder:\s*mainLibrarySelectionState\._lastFolder", _MAIN.read_text(encoding="utf-8"))


def test_a_foablak_megtartja_a_kijeloles_neveit_es_a_forditasi_kontextust():
    main = _MAIN.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")

    for name in (
        "selectedRows",
        "vanMentetlenSzerkesztes",
        "photoActionRows",
        "prepareRenameSelection",
        "photoActionIndex",
        "photoActionPaths",
        "newAlbumFolderPath",
        "addPhotosToScreensaver",
        "requestAddToScreensaver",
        "addTagToRows",
        "selectedPaths",
        "resetFacesForPaths",
        "openPhotoContextMenu",
        "splitFolderHere",
        "handleThumbClick",
        "_folderOfRow",
        "_selectionInFolder",
        "clearSelection",
        "_currentGroup",
        "_groupRows",
        "selectAll",
        "invertSelection",
        "selectStarred",
    ):
        assert re.search(rf"function\s+{name}\s*\(", main), (
            f"a Main.qml-beli nyilvános függvény eltűnt: {name}"
        )
        assert re.search(rf"function\s+{name}\s*\(", component), (
            f"hiányzik a komponensből a kijelölési művelet: {name}"
        )

    assert 'qsTr("Added %1 pictures to Screensaver.")' in main
    assert 'qsTr("Added %1 pictures to Screensaver.")' not in component
