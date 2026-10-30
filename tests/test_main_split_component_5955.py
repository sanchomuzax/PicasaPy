"""#5955: a fő osztott nézet külön QML-komponensben él."""

from pathlib import Path
import re


_GYOKER = Path(__file__).resolve().parents[1]
_MAIN = _GYOKER / "src/picasapy/app/qml/Main.qml"
_WORKSPACE = _GYOKER / "src/picasapy/app/qml/PicasaPy/MainWindowWorkspace.qml"
_MENU_BAR = _GYOKER / "src/picasapy/app/qml/PicasaPy/MainMenuBar.qml"
_QML_DIR = _GYOKER / "src/picasapy/app/qml"
_QMLDIR = _GYOKER / "src/picasapy/app/qml/PicasaPy/qmldir"


def test_main_split_inline_marad_a_kepazonossaghoz():
    main = _MAIN.read_text(encoding="utf-8")
    workspace = _WORKSPACE.read_text(encoding="utf-8")
    qmldir = _QMLDIR.read_text(encoding="utf-8")

    assert re.search(r"^    SplitView\s*\{\n        id: mainSplit", workspace, re.MULTILINE)
    assert 'objectName: "mainSplit"' in workspace
    assert "MainWindowWorkspace {" in main
    assert not re.search(r"^MainSplit\s", qmldir, re.MULTILINE)
    assert not (_QML_DIR / "PicasaPy/MainSplit.qml").exists()


def test_foablak_menubar_kulon_komponensben_marad_a_neveivel():
    main = _MAIN.read_text(encoding="utf-8")
    component = _MENU_BAR.read_text(encoding="utf-8") if _MENU_BAR.exists() else ""
    qmldir = _QMLDIR.read_text(encoding="utf-8")
    main_family = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            _QML_DIR / "Main.qml",
            *sorted((_QML_DIR / "PicasaPy").glob("Main*.qml")),
        )
    )

    assert re.search(
        r"^    menuBar: MainMenuBar\s*\{\s*id: picasaMenuBar",
        main,
        re.MULTILINE,
    )
    assert "id: picasaMenuBar" in main
    assert _MENU_BAR.is_file()
    assert len(component.splitlines()) < 800
    assert "MainMenuBar 1.0 MainMenuBar.qml" in qmldir
    for name in (
        "hostWindow",
        "hostController",
        "hostToolbar",
        "hostPhotoViewer",
        "hostFileOpsController",
    ):
        assert re.search(rf"required\s+property\s+var\s+{name}\b", component)
        assert re.search(rf"\b{name}\s*:\s*", main)
    assert "onTimelineRequested: hostWindow.toggleTimeline()" in main_family
    assert "onLanguageConfirmRequested" in main_family
