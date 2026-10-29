"""Az ImportSourceDialog QML-bontásának szerződésőrei (#6083)."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import picasapy.app


_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_TS = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
_COMPONENTS = (
    "ImportSourcePickerPanel",
    "ImportSourcePreview",
    "ImportSourceDestinationPanel",
)
_BASELINE_QSTR_COUNT = 52
_BASELINE_QSTR_SHA256 = (
    "5212e2af231a128f36745603810696b8cffc8e775cfe7e55004f15ec6f8096a4"
)
_BASELINE_OBJECT_NAMES = {
    "importRotateLeft:",
    "importRotateRight:",
    "importSourceAfterDeleteAllRadio",
    "importSourceAfterDeleteCopiedRadio",
    "importSourceAfterLeaveRadio",
    "importSourceAutoExcludeCheckBox",
    "importSourceBusyIndicator",
    "importSourceChooseDestButton",
    "importSourceChooseFilesItem",
    "importSourceChooseFolderItem",
    "importSourceChooseMenu",
    "importSourceChooseSourceButton",
    "importSourceCloseButton",
    "importSourceCountText",
    "importSourceDestPathText",
    "importSourceDialog",
    "importSourceDuplicateCountText",
    "importSourceEmptyText",
    "importSourceErrorText",
    "importSourceExcludeAllButton",
    "importSourceFilesDialog",
    "importSourceFolderDialog",
    "importSourceFolderMenu",
    "importSourceFromMenu",
    "importSourceIncludeAllButton",
    "importSourceManualNameField",
    "importSourceManualTipText",
    "importSourceMediaFilterBox",
    "importSourceMountedSourcesBox",
    "importSourceNamingByDateRadio",
    "importSourceNamingManualRadio",
    "importSourceNamingTodayRadio",
    "importSourceNextButton",
    "importSourceOnlineOptionsMenu",
    "importSourceOptionsButton",
    "importSourcePathText",
    "importSourcePreviewGrid",
    "importSourcePreviousButton",
    "importSourceProgressFill",
    "importSourceProgressText",
    "importSourceRecentBox",
    "importSourceRecentDestBox",
    "importSourceResizeBox",
    "importSourceResultText",
    "importSourceStartButton",
    "importSourceSyncStarredOnlyCheckBox",
    "importSourceThumb:",
    "importSourceToggle:",
    "importSourceToggleLabel:",
    "importSourceUploadCheckBox",
    "importStar:",
}


def _qml_strings(text: str) -> set[str]:
    sources = set()
    for match in re.finditer(r"\bqsTr\(", text):
        start = match.end()
        depth = 0
        quoted = False
        escaped = False
        end = start
        for position, char in enumerate(text[start:], start):
            end = position
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char == "," and depth == 0:
                break
        first_argument = text[start:end]
        pieces = re.findall(r'"((?:\\.|[^"\\])*)"', first_argument)
        if pieces:
            sources.add("".join(json.loads(f'"{piece}"') for piece in pieces))
    return sources


def test_a_parbeszed_komponensei_onallo_fajlok_es_betoltheto_tipusok():
    host = (_QML / "ImportSourceDialog.qml").read_text(encoding="utf-8")
    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")

    for component in _COMPONENTS:
        assert (_QML / f"{component}.qml").is_file(), (
            f"hiányzik az önálló QML-komponens: {component}.qml"
        )
        assert f"internal {component} {component}.qml" in qmldir
        assert re.search(rf"\b{component}\s*\{{", host), (
            f"a fő párbeszéd nem használja a {component} komponenst"
        )


def test_a_parbeszed_egyetlen_qml_resze_sem_hosszabb_800_sornal():
    fajlok = [_QML / "ImportSourceDialog.qml"] + [
        _QML / f"{component}.qml" for component in _COMPONENTS
    ]
    hosszak = {
        fajl.name: len(fajl.read_text(encoding="utf-8").splitlines())
        for fajl in fajlok
        if fajl.is_file()
    }

    assert len(hosszak) == len(fajlok), f"hiányzó komponensfájl: {hosszak}"
    assert all(hossz <= 800 for hossz in hosszak.values()), (
        f"a 800 soros határ fölötti QML-fájlok: {hosszak}"
    )


def test_a_meglevo_objectname_ertekek_valtozatlanul_megmaradnak():
    fajlok = [_QML / "ImportSourceDialog.qml"] + [
        _QML / f"{component}.qml" for component in _COMPONENTS
    ]
    forrasok = "\n".join(
        fajl.read_text(encoding="utf-8")
        for fajl in fajlok
        if fajl.is_file()
    )
    object_names = set(
        re.findall(r'objectName\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', forrasok)
    )

    assert _BASELINE_OBJECT_NAMES <= object_names, (
        "eltűnt objectName érték(ek): "
        f"{sorted(_BASELINE_OBJECT_NAMES - object_names)}"
    )


def test_a_meglevo_qstr_feliratok_valtozatlanul_megmaradnak():
    fajlok = [_QML / "ImportSourceDialog.qml"] + [
        _QML / f"{component}.qml" for component in _COMPONENTS
    ]
    forrasok = set().union(*(
        _qml_strings(fajl.read_text(encoding="utf-8"))
        for fajl in fajlok
        if fajl.is_file()
    ))
    lenyomat = hashlib.sha256(
        "\n".join(sorted(forrasok)).encode("utf-8")
    ).hexdigest()

    assert len(forrasok) == _BASELINE_QSTR_COUNT, (
        f"a qsTr-feliratok száma megváltozott: {len(forrasok)}"
    )
    assert lenyomat == _BASELINE_QSTR_SHA256, (
        "egy meglévő qsTr-felirat megváltozott vagy eltűnt"
    )


def test_a_qstr_forditasok_az_uj_qml_kontekstusokban_maradnak():
    translation_root = ET.parse(_TS).getroot()
    contexts = {
        context.findtext("name"): context
        for context in translation_root.findall("context")
    }

    for component in _COMPONENTS:
        assert component in contexts, f"hiányzik a .ts kontextus: {component}"
        qml = (_QML / f"{component}.qml").read_text(encoding="utf-8")
        translated_sources = {
            message.findtext("source") or ""
            for message in contexts[component].findall("message")
        }
        assert _qml_strings(qml) <= translated_sources, (
            f"{component}: hiányzó magyar fordítási források: "
            f"{sorted(_qml_strings(qml) - translated_sources)}"
        )


def test_a_parbeszed_gyokerenek_meglevo_qml_feluletetuletei_megmaradnak():
    host = (_QML / "ImportSourceDialog.qml").read_text(encoding="utf-8")
    api = (
        "id: importSourceWindow",
        'objectName: "importSourceDialog"',
        "property string sourceFolder:",
        "property var sourceFiles:",
        "readonly property bool hasSource:",
        "property string destFolder:",
        "property string namingMode:",
        "property string manualFolderName:",
        "property string afterCopying:",
        "property var previewItems:",
        "property int previewCount:",
        "property int selectedPreviewIndex:",
        "function formatSpeed(",
        "function open()",
        "function stepPreview(",
        "function scanCurrentSource()",
        "function useSelectedFiles(",
        "function runImportNow()",
        "function requestImport()",
    )

    assert all(signature in host for signature in api), (
        "eltűnt vagy átneveződött meglévő párbeszédfelületi elem"
    )


def test_a_panelek_neve_nem_parbeszed() -> None:
    """A főmenü-bejáró a típusnévben lévő `dialog` szóról ismeri fel a nyitott
    párbeszédet; egy ilyen nevű, mindig látható panelt bezáratlan ablaknak
    vélne, és mindegyikre kivárná a teljes időkorlátot."""
    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
    for nev in ("ImportSourcePickerPanel", "ImportSourcePreview", "ImportSourceDestinationPanel"):
        assert f"internal {nev} {nev}.qml" in qmldir
    assert "internal ImportSourceDialog" not in qmldir
