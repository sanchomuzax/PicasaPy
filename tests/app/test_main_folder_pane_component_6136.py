"""A főablak bal mappahasábja önálló, bekötött QML-komponens (#6136)."""

from __future__ import annotations

import re
from pathlib import Path


_QML_DIR = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML_DIR / "Main.qml"
_COMPONENT = _QML_DIR / "PicasaPy/MainFolderPane.qml"
_WORKSPACE = _QML_DIR / "PicasaPy/MainLibraryWorkspace.qml"
_QMLDIR = _QML_DIR / "PicasaPy/qmldir"


def test_a_mappahasab_onallo_800_sor_alatti_komponens():
    assert _COMPONENT.is_file(), "hiányzik a MainFolderPane.qml"
    assert len(_COMPONENT.read_text(encoding="utf-8").splitlines()) < 800


def test_a_mappahasab_a_gazdaobjektumokat_kotelezoen_kapja():
    assert _COMPONENT.is_file(), "hiányzik a MainFolderPane.qml"
    for nev in (
        "hostWindow",
        "hostController",
        "hostToolbar",
        "hostBackupHost",
        "hostFileOpsDialogs",
        "hostCollectionPasswordDialog",
        "hostFileOpsController",
        "hostFaceScanController",
        "hostFolderHierarchyController",
    ):
        assert re.search(
            rf"required\s+property\s+var\s+{nev}\b",
            _COMPONENT.read_text(encoding="utf-8"),
        ), f"hiányzó kötelező gazdatulajdonság: {nev}"


def test_a_foablak_megtartja_a_mappahasab_nevet_es_a_bekotest():
    main = _MAIN.read_text(encoding="utf-8")
    workspace = _WORKSPACE.read_text(encoding="utf-8")
    assert re.search(
        r"MainLibraryWorkspace\s*\{\s*id:\s*mainLibraryWorkspace",
        main,
    ), "a munkaterületi komponens bekötése hiányzik"
    assert re.search(
        r"MainFolderPane\s*\{\s*id:\s*_folderPane\s*objectName:\s*\"folderPane\"",
        workspace,
    ), "a folderPane azonosítója vagy objectName-je megváltozott"
    assert "property alias folderPane: mainLibraryWorkspace.folderPane" in main
    assert not re.search(r"(?<!Main)FolderPane\s*\{", workspace), (
        "a FolderPane példány inline maradt"
    )
    for binding in (
        "hostWindow: root.hostWindow",
        "hostController: root.hostController",
        "hostToolbar: root.hostToolbar",
        "hostBackupHost: root.hostBackupHost",
        "hostFileOpsDialogs: root.hostFileOpsDialogs",
        "hostCollectionPasswordDialog: root.hostCollectionPasswordDialog",
    ):
        assert binding in workspace, f"hiányzó munkaterületi bekötés: {binding}"
    for binding in (
        "hostWindow: window",
        "hostController: controller",
        "hostToolbar: toolbar",
        "hostBackupHost: backupHost",
        "hostFileOpsDialogs: fileOpsDialogs",
        "hostCollectionPasswordDialog: collectionPasswordDialog",
    ):
        assert binding in main, f"hiányzó főablak-bekötés: {binding}"


def test_a_mappahasab_regisztralt_a_qml_modulban():
    qmldir = _QMLDIR.read_text(encoding="utf-8")
    assert "MainFolderPane 1.0 MainFolderPane.qml" in qmldir
