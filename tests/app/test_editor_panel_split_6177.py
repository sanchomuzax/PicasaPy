"""A szerkesztőpanel komponensekre bontásának szerkezeti őre (#6177)."""

from pathlib import Path


GYOKER = Path(__file__).resolve().parents[2]
QML = GYOKER / "src/picasapy/app/qml/PicasaPy"


def test_editor_panel_is_split_into_internal_named_components() -> None:
    editor_panel = (QML / "EditorPanel.qml").read_text(encoding="utf-8")
    qmldir = (QML / "qmldir").read_text(encoding="utf-8")

    assert len(editor_panel.splitlines()) < 800
    assert 'objectName: "editorPanel"' in editor_panel

    for name in ("EditorPanelTabs", "EditorPanelOverlays"):
        assert f"{name} {{" in editor_panel
        assert f"internal {name} {name}.qml" in qmldir
        assert (QML / f"{name}.qml").is_file()
