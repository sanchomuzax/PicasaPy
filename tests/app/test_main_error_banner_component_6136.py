"""A főablak hibasávja önálló QML-komponensben marad (#6136)."""

from pathlib import Path
import re


_ROOT = Path(__file__).resolve().parents[2]
_QML = _ROOT / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_PERIPHERAL_LAYERS = _QML / "PicasaPy/MainWindowPeripheralLayers.qml"
_COMPONENT = _QML / "PicasaPy/MainErrorBanner.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_hibasav_komponens_kisebb_800_sornal():
    assert _COMPONENT.is_file(), "hiányzik a MainErrorBanner.qml"
    assert len(_COMPONENT.read_text(encoding="utf-8").splitlines()) < 800


def test_a_hibasav_megtartja_a_neveket_es_a_gazda_atadasat():
    main = _MAIN.read_text(encoding="utf-8")
    peripheral = _PERIPHERAL_LAYERS.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")

    assert re.search(
        r"MainErrorBanner\s*\{\s*id:\s*mainErrorBanner", peripheral, re.DOTALL
    )
    assert 'objectName: "errorBanner"' in component
    assert "property alias errorBanner:" in main
    assert "mainWindowPeripheralLayers.exportErrorBanner" in main
    assert "property alias errorBannerText:" in main
    assert "mainWindowPeripheralLayers.exportErrorBannerText" in main
    assert "hostController: layers.hostController" in peripheral
    assert re.search(
        r"MainWindowPeripheralLayers\s*\{[^}]*hostController:\s*"
        r"typeof\s+controller\s*!==\s*\"undefined\"", main, re.DOTALL
    )
    assert re.search(r"required\s+property\s+var\s+hostController\b", component)
    assert re.search(r"required\s+property\s+var\s+hostTestLogDialog\b", component)
    assert re.search(r"required\s+property\s+var\s+hostBrokenPhotoDialog\b", component)
    assert re.search(
        r"required\s+property\s+var\s+hostBrokenPhotoBatchTimer\b", component
    )
    assert not re.search(r"Rectangle\s*\{\s*id:\s*errorBanner\b", main)


def test_a_hibasav_regisztralt_a_qml_modulban():
    qmldir = _QMLDIR.read_text(encoding="utf-8")
    assert "MainErrorBanner 1.0 MainErrorBanner.qml" in qmldir
