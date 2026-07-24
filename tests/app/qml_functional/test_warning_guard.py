"""A QML-figyelmeztetés-őr osztályozójának tesztje (#309).

Az őr (a `conftest.py` `qml_warnings` autouse fixture-e) csak a
QML-SZKRIPTHIBÁKRA hasalhat el — a platformfüggő Qt-környezeti zajra nem.
A tényleges üzenet-minták VALÓDI futásokból származnak: a #305-ös esetek a
linuxos tesztfutás kimenetéből, a zaj-minták a v0.4.66 windows-latest
CI-lábának naplójából.

Miért az osztályozót teszteljük, és nem egy „idézzünk elő élő null-hibát"
tesztet? Mert az autouse fixture magára a tesztre is vonatkozik: egy
szándékosan hibát okozó QML-kötés a saját tesztjét buktatná el, nem a
vizsgált viselkedést igazolná.
"""

from __future__ import annotations

import pytest

from support.qml_warning_filter import is_qml_script_error

# A #305-ös hibaosztály — ezeknek TOVÁBBRA IS buktatniuk kell a tesztet.
SZKRIPTHIBAK = [
    "file:///…/Main.qml:287: TypeError: Cannot read property "
    "'hasEffectsClipboard' of null",
    "file:///…/TrayBar.qml:60: TypeError: Cannot read property "
    "'statusText' of null",
    "file:///…/LightboxFeed.qml:423: ReferenceError: photos is not defined",
    "file:///…/PicasaMenuBar.qml:154: Unable to assign [undefined] to bool",
    "file:///…/PhotoViewer.qml:12: TypeError: controller.viewerInfo "
    "is not a function",
]

# Platformfüggő környezeti zaj — ezek NEM buktathatják a tesztet.
KORNYEZETI_ZAJ = [
    "QFontDatabase: Cannot find font directory "
    "C:/hostedtoolcache/windows/Python/3.12.10/x64/Lib/site-packages/PySide6/lib/fonts",
    "OpenThemeData() failed for theme 0 (BUTTON). (The handle is invalid.)",
    "file:///…/PicasaButton.qml:15:17: QML QQuickRectangle: The current style "
    "does not support customization of this control (property: \"contentItem\"). "
    "Please customize a non-native style (such as Basic, Fusion, Material, etc).",
    "QQuickWindow: Failed to create OpenGL context",
]


@pytest.mark.parametrize("uzenet", SZKRIPTHIBAK)
def test_szkripthiba_buktat(uzenet):
    assert is_qml_script_error(uzenet)


@pytest.mark.parametrize("uzenet", KORNYEZETI_ZAJ)
def test_kornyezeti_zaj_nem_buktat(uzenet):
    assert not is_qml_script_error(uzenet)
