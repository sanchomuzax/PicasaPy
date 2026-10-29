"""A szerkesztőpanel állapot- és vizuális részei önálló QML-komponensek (#6225)."""

from pathlib import Path


GYOKER = Path(__file__).resolve().parents[2]
QML = GYOKER / "src/picasapy/app/qml/PicasaPy"
KOMPONENSEK = (
    "EditorPanelCropState",
    "EditorPanelEffectState",
    "EditorPanelFinetuneState",
    "EditorPanelTextState",
    "EditorPanelToolsState",
    "EditorPanelBlurEffects",
)


def test_editor_panel_es_komponenscsaladja_400_sor_alatt_marad() -> None:
    panel = (QML / "EditorPanel.qml").read_text(encoding="utf-8")
    qmldir = (QML / "qmldir").read_text(encoding="utf-8")

    assert len(panel.splitlines()) < 400
    assert 'objectName: "editorPanel"' in panel

    for nev in KOMPONENSEK:
        komponens = QML / f"{nev}.qml"
        assert komponens.is_file()
        forras = komponens.read_text(encoding="utf-8")
        assert len(forras.splitlines()) < 400
        assert "required property var editorPanel" in forras
        assert f"{nev} {{" in panel
        assert f"internal {nev} {nev}.qml" in qmldir

    for nev in ("EditorPanelTabs", "EditorPanelOverlays", "EditorUndoRow"):
        assert (QML / f"{nev}.qml").is_file()
        assert len((QML / f"{nev}.qml").read_text(encoding="utf-8").splitlines()) < 400

    for nev in (
        "cropActive",
        "textDraftContent",
        "fillLight",
        "aspectIndex",
        "paramPanelActive",
    ):
        assert f"property alias {nev}:" in panel
