"""#6136: a főablaki diavetítés állapota a saját komponensében él."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parent.parent / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_WORKSPACE = _QML / "PicasaPy/MainWindowWorkspace.qml"
_COMMANDS = _QML / "PicasaPy/MainWindowCommands.qml"
_COMPONENT = _QML / "PicasaPy/MainSlideshow.qml"


def test_a_diavetites_eletciklusa_a_meglevo_fooldali_komponensben_van():
    component = _COMPONENT.read_text(encoding="utf-8")

    for name in (
        "hostWindow",
        "hostController",
        "hostPhotoViewer",
        "hostErrorBanner",
        "noScreensaverPicturesMessage",
    ):
        assert re.search(rf"required\s+property\s+\w+\s+{name}\b", component), (
            f"hiányzik a kötelező gazda-property: {name}"
        )

    for function in (
        "toggleViewerFullscreen",
        "startSlideshow",
        "startScreensaverPreview",
        "exitSlideshow",
    ):
        assert re.search(rf"function\s+{function}\s*\(", component), (
            f"a diavetítési komponens nem birtokolja a(z) {function} kezelőt"
        )
    assert re.search(
        r"property\s+int\s+visibilityBeforeViewerFullscreen\b", component
    )
    assert re.search(
        r"property\s+int\s+visibilityBeforeSlideshow\b", component
    )


def test_a_foablak_regi_nevei_atjarokent_megmaradnak():
    main = _MAIN.read_text(encoding="utf-8")
    commands = _COMMANDS.read_text(encoding="utf-8")

    for prop in (
        "visibilityBeforeViewerFullscreen",
        "visibilityBeforeSlideshow",
    ):
        assert re.search(
            rf"property\s+alias\s+{prop}:\s*"
            rf"mainWindowWorkspace\.export{prop[0].upper() + prop[1:]}",
            main,
        ), f"megváltozott a főablak látható property-neve: {prop}"

    for function in (
        "toggleViewerFullscreen",
        "startSlideshow",
        "startScreensaverPreview",
        "exitSlideshow",
    ):
        assert re.search(
            rf"function\s+{function}\s*\([^)]*\)\s*\{{\s*"
            rf"mainWindowCommands\.{function}\(",
            main,
            re.DOTALL,
        ), f"a főablak látható függvényneve nem őrzi a belépőt: {function}"
        assert re.search(
            rf"function\s+{function}\s*\([^)]*\)\s*\{{\s*"
            rf"hostRefs\.slideshow\.{function}\(",
            commands,
            re.DOTALL,
        ), f"a parancskomponens nem vezeti át a(z) {function} hívást"

    assert re.search(
        r"hostController:\s*typeof\s+controller\s*!==\s*\"undefined\"\s*"
        r"\?\s*controller\s*:\s*null",
        _MAIN.read_text(encoding="utf-8"),
    ), "a context controller átadása nem védi a tesztkörnyezetet"
    assert re.search(
        r"noScreensaverPicturesMessage:\s*qsTr\(",
        _WORKSPACE.read_text(encoding="utf-8"),
    ), (
        "a meglévő fordítási hívásnak a MainWindowWorkspace kontextusában kell maradnia"
    )
