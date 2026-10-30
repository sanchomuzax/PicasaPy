"""A főablak Időrend-ablaka önálló komponensben marad (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[1] / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_WORKSPACE = _QML / "PicasaPy/MainWindowWorkspace.qml"
_COMMANDS = _QML / "PicasaPy/MainWindowCommands.qml"
_COMPONENT = _QML / "PicasaPy/MainTimeline.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_az_idorend_ablaka_onallo_komponensben_marad_az_ablaknevek_megtartasaval():
    main = _MAIN.read_text(encoding="utf-8")
    workspace = _WORKSPACE.read_text(encoding="utf-8")
    commands = _COMMANDS.read_text(encoding="utf-8")
    assert _COMPONENT.is_file(), "hiányzik a MainTimeline.qml komponens"
    component = _COMPONENT.read_text(encoding="utf-8")
    qmldir = _QMLDIR.read_text(encoding="utf-8")

    assert len(component.splitlines()) < 800
    assert "MainTimeline 1.0 MainTimeline.qml" in qmldir
    assert re.search(r"MainTimeline\s*\{\s*id:\s*timelineView", workspace)
    assert "MainWindowWorkspace {" in main
    assert 'objectName: "timelineView"' in component
    assert re.search(r"^TimelineView\s*\{", component, re.MULTILINE)

    for name in (
        "timelineOpen",
        "timelineSlideshowActive",
        "timelineSlideshowModel",
    ):
        assert re.search(
            rf"property\s+alias\s+{name}:\s*mainWindowWorkspace\.export"
            rf"{name[0].upper() + name[1:]}",
            main,
        ), f"a Main.qml nem őrzi meg a(z) {name} nevet"

    for function in (
        "timelineCollectionForId",
        "selectTimelineCollection",
        "closeTimeline",
        "toggleTimeline",
        "startTimelineSlideshow",
    ):
        assert re.search(
            rf"function\s+{function}\s*\(", main
        ), f"a Main.qml nem őrzi meg a(z) {function} belépőt"
        assert re.search(
            rf"function\s+{function}\s*\([^)]*\)\s*\{{\s*"
            rf"(?:return\s+)?mainWindowCommands\.{function}\(",
            main,
            re.DOTALL,
        ), f"a Main.qml nem őrzi meg a(z) {function} belépőt"
        assert re.search(
            rf"function\s+{function}\s*\(", component
        ), f"a MainTimeline.qml nem tartalmazza a(z) {function} műveletet"

    for name in (
        "hostWindow",
        "hostController",
        "hostTimelineController",
        "hostToolbar",
        "hostSlideshow",
    ):
        assert re.search(
            rf"required\s+property\s+var\s+{name}\b", component
        ), f"hiányzik a kötelező gazda-property: {name}"
        assert re.search(rf"\b{name}:\s*", workspace), (
            f"a MainWindowWorkspace.qml nem adja át a gazdát: {name}"
        )

    assert "hostRefs.timelineView: mainWindowWorkspace.exportTimelineView" in commands or (
        "timelineView: mainWindowWorkspace.exportTimelineView" in main
    )

    assert not re.search(r"^\s*TimelineView\s*\{", main, re.MULTILINE)
