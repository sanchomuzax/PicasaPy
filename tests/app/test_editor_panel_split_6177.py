"""A szerkesztőpanel komponensekre bontásának szerkezeti őre (#6177)."""

from pathlib import Path

from tests.support.editor_panel_family import editor_panel_family_source


GYOKER = Path(__file__).resolve().parents[2]
QML = GYOKER / "src/picasapy/app/qml/PicasaPy"


def test_editor_panel_is_split_into_internal_named_components() -> None:
    editor_panel = editor_panel_family_source(QML)
    qmldir = (QML / "qmldir").read_text(encoding="utf-8")

    assert len((QML / "EditorPanel.qml").read_text(encoding="utf-8").splitlines()) < 400
    assert 'objectName: "editorPanel"' in editor_panel

    for name in ("EditorPanelTabs", "EditorPanelOverlays", "EditorUndoRow"):
        assert f"{name} {{" in editor_panel
        if name != "EditorUndoRow":
            assert f"internal {name} {name}.qml" in qmldir
        assert (QML / f"{name}.qml").is_file()
