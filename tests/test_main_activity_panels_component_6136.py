"""A főablak háttérmunka-jelzői külön komponensben maradnak (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parent.parent / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_PERIPHERAL_LAYERS = _QML / "PicasaPy/MainWindowPeripheralLayers.qml"
_COMPONENT = _QML / "PicasaPy/MainActivityPanels.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_folyamatjelzok_komponense_regisztralt_es_megorzott_nevekkel_kotott():
    assert _COMPONENT.is_file(), "hiányzik a MainActivityPanels.qml komponens"
    assert "MainActivityPanels 1.0 MainActivityPanels.qml" in (
        _QMLDIR.read_text(encoding="utf-8")
    )

    main = _MAIN.read_text(encoding="utf-8")
    peripheral = _PERIPHERAL_LAYERS.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")
    assert re.search(
        r"MainActivityPanels\s*\{\s*id:\s*activityPanels", peripheral, re.DOTALL
    )
    assert "MainWindowPeripheralLayers {" in main

    for name in ("hostController", "hostActivityCancelConfirm"):
        assert re.search(
            rf"required\s+property\s+var\s+{name}\b", component
        ), f"hiányzik a kötelező gazda-property: {name}"
        assert re.search(rf"\b{name}:\s*", peripheral), (
            f"a rétegkomponens nem adja át a gazdát: {name}"
        )

    for object_name in (
        "importProgressPanel",
        "activityBadge",
        "xmpFacesProgressPanel",
        "batchEditProgressPanel",
        "saveProgressPanel",
        "perfMonitorPanel",
    ):
        assert f'objectName: "{object_name}"' in component, (
            f"megváltozott vagy eltűnt a nyilvános objectName: {object_name}"
        )
