"""#5955: a fő osztott nézet külön QML-komponensben él."""

from pathlib import Path
import re


_GYOKER = Path(__file__).resolve().parents[1]
_MAIN = _GYOKER / "src/picasapy/app/qml/Main.qml"
_SPLIT = _GYOKER / "src/picasapy/app/qml/PicasaPy/MainSplit.qml"
_MENU_BAR = _GYOKER / "src/picasapy/app/qml/PicasaPy/MainMenuBar.qml"
_QMLDIR = _GYOKER / "src/picasapy/app/qml/PicasaPy/qmldir"


def test_main_split_inline_marad_a_kepazonossaghoz():
    main = _MAIN.read_text(encoding="utf-8")
    qmldir = _QMLDIR.read_text(encoding="utf-8")

    assert re.search(r"^    SplitView\s*\{\n        id: mainSplit", main, re.MULTILINE)
    assert 'objectName: "mainSplit"' in main
    assert not re.search(r"^MainSplit\s", qmldir, re.MULTILINE)
    assert not _SPLIT.exists()


def test_foablak_menubar_inline_marad_a_kepazonossaghoz():
    main = _MAIN.read_text(encoding="utf-8")
    qmldir = _QMLDIR.read_text(encoding="utf-8")

    assert re.search(
        r"^    menuBar: PicasaMenuBar\s*\{",
        main,
        re.MULTILINE,
    )
    assert "id: picasaMenuBar" in main
    assert not re.search(r"^MainMenuBar\s", qmldir, re.MULTILINE)
    assert not _MENU_BAR.exists()
