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
    # #506: a saját komponens tulajdonsága elfedi az alaposztály tagját
    # (pl. `palette` az Item/Control-on) — mindig kódhiba, mindig buktasson.
    "qt.qml.propertyCache.append: Member palette of the object "
    "TextColorSwatches overrides a member of the base object. Consider "
    "renaming it or adding final or override specifier",
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


# #2072: a QT SAJÁT QML-jéből érkező üzenetek — origó szerint kizárva.
#
# A mérés (`ci.yml` 33687325094, windows 1/4): a Qt Controls natív
# Windows-stílusának `Button.qml`-je négy `TypeError`-t ír ki minden
# gomb-példányosításkor. Az őr ezekre elhasalt, tehát Windowson MINDEN
# gombot példányosító teszt elbukott — és a nem-blokkoló windows-láb
# miatt ez elfedte a valódi, windows-specifikus hibákat is.
IDEGEN_EREDETU_ZAJ = [
    "qrc:/qt-project.org/imports/QtQuick/Controls/Windows/Button.qml:28:9: "
    "TypeError: Cannot read property 'height' of null",
    "qrc:/qt-project.org/imports/QtQuick/Controls/Windows/Button.qml:25:9: "
    "TypeError: Cannot read property 'x' of null",
    "qrc:/qt-project.org/imports/QtQuick/Controls/Fusion/CheckBox.qml:12: "
    "ReferenceError: control is not defined",
]


@pytest.mark.parametrize("uzenet", IDEGEN_EREDETU_ZAJ)
def test_a_qt_sajat_qml_je_NEM_buktat(uzenet):
    """Nem mi írtuk, nem is javíthatjuk — az őr ne hasaljon el rajta."""
    assert is_qml_script_error(uzenet) is False


@pytest.mark.parametrize(
    "uzenet",
    [
        "file:///home/x/PicasaPy/src/picasapy/app/qml/PicasaPy/Button.qml:28:9: "
        "TypeError: Cannot read property 'height' of null",
        "file:///…/PicasaPy/qml/Sajat.qml:25:9: "
        "TypeError: Cannot read property 'x' of null",
    ],
)
def test_a_MI_QML_UNK_ugyanolyan_uzenete_TOVABBRA_IS_buktat(uzenet):
    """A kapu nem tehet vakká.

    Fog: ha valaki az origó-szűrést a `TypeError` MINTA kivételére
    cseréli, ez a két eset átcsúszna — pedig szó szerint ugyanaz a
    hibaszöveg, csak a MI fájlunkból.
    """
    assert is_qml_script_error(uzenet) is True


def test_a_szures_nem_a_fajlnevre_hanem_az_EREDETRE_nez():
    """Egy `Button.qml` nevű SAJÁT fájl nem eshet ki a szűrőn."""
    sajat = (
        "file:///…/PicasaPy/qml/PicasaPy/Button.qml:1: "
        "TypeError: Cannot read property 'x' of null"
    )
    idegen = (
        "qrc:/qt-project.org/imports/QtQuick/Controls/Windows/Button.qml:1: "
        "TypeError: Cannot read property 'x' of null"
    )
    assert is_qml_script_error(sajat) is True
    assert is_qml_script_error(idegen) is False
