"""#5955: a főablak megjelenítési blokkjai önálló QML-komponensek."""

from pathlib import Path
import re


_GYOKER = Path(__file__).resolve().parents[1]
_MAIN = _GYOKER / "src/picasapy/app/qml/Main.qml"
_QMLDIR = _GYOKER / "src/picasapy/app/qml/PicasaPy/qmldir"
_QML = _GYOKER / "src/picasapy/app/qml/PicasaPy"


def test_a_fejlec_a_megorzo_nevvel_komponensbol_epul():
    main = _MAIN.read_text(encoding="utf-8")
    qmldir = _QMLDIR.read_text(encoding="utf-8")
    component = _QML / "MainWindowToolbar.qml"

    assert component.is_file(), "hiányzik a MainWindowToolbar.qml komponens"
    assert re.search(
        r"^MainWindowToolbar 1\.0 MainWindowToolbar\.qml$", qmldir, re.MULTILINE
    )
    assert re.search(
        r"header:\s*MainWindowToolbar\s*\{\s*id:\s*toolbar", main, re.DOTALL
    )
    assert 'objectName: "mainToolbar"' in component.read_text(encoding="utf-8")
