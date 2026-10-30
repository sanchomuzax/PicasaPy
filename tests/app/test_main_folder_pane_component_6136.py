"""A főablak bal mappahasábja önálló, bekötött QML-komponens (#6136)."""

from __future__ import annotations

import re
from pathlib import Path


_QML_DIR = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML_DIR / "Main.qml"
_WORKSPACE = _QML_DIR / "PicasaPy/MainWindowWorkspace.qml"
_COMPONENT = _QML_DIR / "PicasaPy/MainFolderPane.qml"
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
        r"MainFolderPane\s*\{\s*id:\s*folderPane\s*objectName:\s*\"folderPane\"",
        workspace,
    ), "a folderPane azonosítója vagy objectName-je megváltozott"
    assert "MainWindowWorkspace {" in main
    assert not re.search(r"(?<!Main)FolderPane\s*\{", workspace), (
        "a FolderPane példány inline maradt"
    )
    for binding in (
        "hostWindow: workspace.hostWindow",
        "hostController: workspace.hostController",
        "hostToolbar: hostRefs.toolbar",
        "hostBackupHost: hostRefs.backupHost",
        "hostFileOpsDialogs: workspace.hostWindow.fileOpsDialogs",
        "hostCollectionPasswordDialog: workspace.hostWindow.collectionPasswordDialog",
    ):
        assert binding in workspace, f"hiányzó gazda-bekötés: {binding}"


def test_a_mappahasab_regisztralt_a_qml_modulban():
    qmldir = _QMLDIR.read_text(encoding="utf-8")
    assert "MainFolderPane 1.0 MainFolderPane.qml" in qmldir
