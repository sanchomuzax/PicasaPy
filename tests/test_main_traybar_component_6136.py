"""A főablak alsó sávjának bekötése külön komponensben marad (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[1] / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_COMPONENT = _QML / "PicasaPy/MainTrayBar.qml"
_TRAY_BAR = _QML / "PicasaPy/TrayBar.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_talca_foablaki_bekotese_kulon_800_sornal_rovidebb_komponens():
    assert _COMPONENT.is_file(), "hiányzik a MainTrayBar.qml komponens"
    assert len(_COMPONENT.read_text(encoding="utf-8").splitlines()) < 800
    assert "MainTrayBar 1.0 MainTrayBar.qml" in (
        _QMLDIR.read_text(encoding="utf-8")
    )


def test_a_foablak_a_megorzott_nevekkel_es_gazdaatadassal_koti_be_a_talcat():
    main = _MAIN.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")
    tray_bar = _TRAY_BAR.read_text(encoding="utf-8")

    assert re.search(r"MainTrayBar\s*\{\s*id:\s*trayBar", main, re.DOTALL)
    for name in (
        "hostWindow",
        "hostController",
        "hostPhotoViewer",
        "hostExportDialogs",
        "hostCreateDialogs",
        "hostFileOpsDialogs",
        "hostFileOpsController",
        "hostDocumentTabStrip",
    ):
        assert re.search(
            rf"required\s+property\s+var\s+{name}\b", component
        ), f"hiányzik a kötelező gazda-property: {name}"
        assert re.search(rf"\b{name}:\s*", main), (
            f"a főablak nem adja át a gazdát: {name}"
        )

    assert re.search(r'objectName:\s*"trayBar"', component)
    assert re.search(r"^TrayBar\s*\{", component, re.MULTILINE)
    assert "readonly property real requiredWidth" in tray_bar
    assert "readonly property int starTargetRow" in tray_bar
    assert "readonly property var keyboardShortcutSequences" in tray_bar
    assert "function kapcsoldACsillagot()" in tray_bar

    for signal in (
        "onPhotosDroppedOnTray",
        "onConfigureButtonsContextMenuRequested",
        "onZoomFitRequested",
        "onZoomActualRequested",
        "onZoomValueRequested",
        "onExportRequested",
        "onViewAndEditRequested",
        "onTrayRotateRightRequested",
        "onTrayRotateLeftRequested",
        "onTrayLocateRequested",
        "onTrayPropertiesRequested",
        "onPrintRequested",
        "onCollageRequested",
        "onMovieRequested",
        "onBackToCollageRequested",
        "onBackToMovieMakerRequested",
        "onEmailRequested",
        "onAddSelectedToScreensaverRequested",
        "onStarSelectedPhotosRequested",
        "onNewAlbumWithSelectionRequested",
    ):
        assert signal in component, f"hiányzik a tálca jelzésbekötése: {signal}"


def test_a_talca_vezerloje_ugyanugy_vedett_a_hianyzokontekstustol():
    main = _MAIN.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")
    assert 'hostFileOpsController: typeof fileOpsController !== "undefined"' in main
    assert "hostFileOpsController.revealPhoto(ut)" in component
