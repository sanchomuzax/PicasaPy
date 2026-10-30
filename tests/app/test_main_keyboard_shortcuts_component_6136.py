"""A főablak gyorsbillentyűi önálló QML-komponensben maradnak (#6136)."""

from collections import Counter
from pathlib import Path
import re


_QML_DIR = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML_DIR / "Main.qml"
_COMMANDS = _QML_DIR / "PicasaPy/MainWindowCommands.qml"
_COMPONENT = _QML_DIR / "PicasaPy/MainKeyboardShortcuts.qml"
_QMLDIR = _QML_DIR / "PicasaPy/qmldir"
_PUBLIC_OBJECT_NAMES = {
    "toggleRightDrawerShortcut",
    "searchShortcut",
    "searchF3Shortcut",
    "starToggleShortcut",
    "refreshCurrentFolderShortcut",
    "tagsPanelAltShortcut",
    "editViewShortcut",
    "dupeSearchShortcut",
    "findSimilarShortcut",
    "clearSimilarShortcut",
    "batchBwShortcut",
    "batchEnhanceShortcut",
    "helpShortcut",
    "helpContextShortcut",
    "shortcutCopyFiles",
    "shortcutCutFiles",
    "shortcutPasteFiles",
    "flipHorizontalShortcut",
    "flipVerticalShortcut",
    "viewerFullscreenShortcut",
    "shortcutDeleteFromDiskGrid",
    "shortcutDeleteFromDiskViewer",
    "openInEditorShortcut",
    "emailShortcut",
}
_SHORTCUT_SEQUENCES = Counter(
    (
        "Ctrl+0",
        "Ctrl+F",
        "F3",
        "F4",
        "F5",
        "Ctrl+K",
        "Ctrl+3",
        "Ctrl+F6",
        "Ctrl+F7",
        "Ctrl+F8",
        "Ctrl+Shift+B",
        "Ctrl+Shift+E",
        "F1",
        "Shift+F1",
        "Ctrl+A",
        "Ctrl+D",
        "Ctrl+I",
        "Ctrl+S",
        "Ctrl+C",
        "Ctrl+X",
        "Ctrl+V",
        "Ctrl+R",
        "Ctrl+Shift+R",
        "Ctrl+Shift+H",
        "Ctrl+Shift+V",
        "Ctrl+4",
        "Ctrl+T",
        "Alt+Return",
        "F11",
        "Ctrl+5",
        "F2",
        "Ctrl+Shift+S",
        "Ctrl+Delete",
        "Ctrl+Delete",
        "Ctrl+Shift+O",
        "Ctrl+E",
    )
)


def test_a_gyorsbillentyuk_komponense_regisztralt_es_800_sor_alatti():
    assert _COMPONENT.is_file(), "hiányzik a MainKeyboardShortcuts.qml"
    assert len(_COMPONENT.read_text(encoding="utf-8").splitlines()) < 800
    assert "MainKeyboardShortcuts 1.0 MainKeyboardShortcuts.qml" in (
        _QMLDIR.read_text(encoding="utf-8")
    )


def test_a_foablak_megtartja_a_neveket_es_a_kotelezo_gazdakapcsolatokat():
    main = _MAIN.read_text(encoding="utf-8")
    commands = _COMMANDS.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")

    assert re.search(
        r"MainKeyboardShortcuts\s*\{\s*id:\s*mainKeyboardShortcuts",
        commands,
        re.DOTALL,
    )
    assert re.search(
        r"property alias keyboardShortcutGroups:\s*"
        r"mainWindowCommands\.keyboardShortcutGroups",
        main,
    )
    for name in (
        "hostWindow",
        "hostController",
        "hostDocumentTabStrip",
        "hostExportDialogs",
        "hostFileOpsController",
        "hostFileOpsDialogs",
        "hostHelpDialog",
        "hostPhotoViewer",
        "hostPicasaMenuBar",
        "hostSaveDialogs",
        "hostSlideshow",
        "hostTrayBar",
    ):
        assert re.search(rf"required\s+property\s+var\s+{name}\b", component), (
            f"hiányzó kötelező gazdatulajdonság: {name}"
        )
        assert re.search(rf"\b{name}:\s*", commands), (
            f"a parancskomponens nem adja át a gazdát: {name}"
        )
    assert "readonly property var keyboardShortcutGroups" in component
    assert "hostFileOpsController.copyFilesToClipboard" in component
    assert "hostFileOpsController.cutFilesToClipboard" in component
    assert "fileOpsController." not in component
    assert _PUBLIC_OBJECT_NAMES <= set(
        re.findall(r'objectName:\s*"([^"]+)"', component)
    ), "egy vagy több QML-ből látható gyorsbillentyűnév eltűnt"
    sequences = Counter(
        re.findall(r'^\s*sequence:\s*"([^"]+)"', component, re.MULTILINE)
    )
    assert sequences == _SHORTCUT_SEQUENCES
