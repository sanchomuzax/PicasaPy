"""#6016: a felső menük külön QML-fájlokban, változatlan fájlsorrendben."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml/PicasaPy"
_TS = Path(__file__).resolve().parents[2] / "src/picasapy/app/i18n/picasapy_hu.ts"
_MENU_COMPONENTS = (
    "PicasaFileMenu",
    "PicasaEditMenu",
    "PicasaViewMenu",
    "PicasaFolderMenu",
    "PicasaPictureMenu",
    "PicasaCreateMenu",
    "PicasaToolsMenu",
    "PicasaHelpMenu",
    "PicasaFolderViewMenu",
    "MainMenuBar",
)
_HOST_IDS = {
    "PicasaFileMenu": "menuFile",
    "PicasaEditMenu": "menuEdit",
    "PicasaViewMenu": "menuView",
    "PicasaFolderMenu": "menuFolder",
    "PicasaPictureMenu": "menuPicture",
    "PicasaHelpMenu": "menuHelp",
}


def test_a_felso_menuk_sorrendben_kulon_komponensek():
    host = (_QML / "PicasaMenuBar.qml").read_text(encoding="utf-8")
    poziciok = []
    for tipus in _MENU_COMPONENTS[:8]:
        fajl = _QML / f"{tipus}.qml"
        assert fajl.is_file(), f"hiányzik a menükomponens: {fajl.name}"
        host_id = _HOST_IDS.get(tipus)
        beallitas = (
            rf"\s*id\s*:\s*{host_id}" if host_id else ""
        ) + r"\s*bar\s*:\s*bar"
        talalat = re.search(rf"\b{tipus}\s*\{{{beallitas}", host)
        assert talalat, f"a {tipus} nincs a menüsávba kötve"
        poziciok.append(talalat.start())

    assert poziciok == sorted(poziciok), "a felső menük sorrendje megváltozott"
    assert (_QML / "PicasaFolderViewMenu.qml").is_file()
    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
    for tipus in _MENU_COMPONENTS:
        if tipus == "MainMenuBar":
            assert "MainMenuBar 1.0 MainMenuBar.qml" in qmldir
        else:
            assert f"internal {tipus} {tipus}.qml" in qmldir


def test_egyik_menufajl_sem_haladja_meg_a_800_sort():
    fajlok = [_QML / "PicasaMenuBar.qml"] + [
        _QML / f"{tipus}.qml" for tipus in _MENU_COMPONENTS
    ]
    tulhosszu = {
        fajl.name: len(fajl.read_text(encoding="utf-8").splitlines())
        for fajl in fajlok
        if fajl.is_file()
        and len(fajl.read_text(encoding="utf-8").splitlines()) > 800
    }
    assert not tulhosszu, f"a 800 soros határ fölötti fájlok: {tulhosszu}"


def test_a_forditasi_kontextusok_az_uj_qml_fajlnevek():
    root = ET.parse(_TS).getroot()
    contexts = {
        context.findtext("name"): context
        for context in root.findall("context")
    }
    missing = [tipus for tipus in _MENU_COMPONENTS if tipus not in contexts]
    assert not missing, f"hiányzó .ts fordítási kontextusok: {missing}"

    for tipus in _MENU_COMPONENTS:
        qml = (_QML / f"{tipus}.qml").read_text(encoding="utf-8")
        forditott_forrasok = {
            message.findtext("source") or ""
            for message in contexts[tipus].findall("message")
        }
        qml_forrasok = {
            json.loads(f'"{source}"')
            for source in re.findall(r'qsTr\("((?:\\.|[^"\\])*)"\)', qml)
        }
        assert qml_forrasok <= forditott_forrasok, (
            f"{tipus}: nincs fordítási rekord ezekhez: "
            f"{sorted(qml_forrasok - forditott_forrasok)}"
        )

    host = (_QML / "PicasaMenuBar.qml").read_text(encoding="utf-8")
    host_sources = {
        message.findtext("source") or ""
        for message in contexts["PicasaMenuBar"].findall("message")
    }
    host_qml_sources = {
        json.loads(f'"{source}"')
        for source in re.findall(r'qsTr\("((?:\\.|[^"\\])*)"\)', host)
    }
    assert host_qml_sources <= host_sources
