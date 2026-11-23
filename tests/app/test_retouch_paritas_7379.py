"""Retusálás panel és megerősítő ablak paritástesztjei (#7379).

⚠️ Ezek a próbák a forrásszöveget olvassák és számolnak: a vizuális egyezést NEM mérik.
A renderelt képkockát mérő próbák: `tests/app/qml_functional/test_retouch_renderelt_7379.py`.
"""

from __future__ import annotations

from pathlib import Path
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.app.edit_controller_shared import (
    _BRUSH_SIZE_TO_RELATIVE_DIVISOR,
    _DEFAULT_BRUSH_SIZE,
)


def test_retouch_brush_default_size_and_diameter() -> None:
    """#7379: az ecsetcsúszka alapállása 50 (a sáv közepe), és az alapállású átmérő 50 px a 987×247-es képen."""
    assert _DEFAULT_BRUSH_SIZE == 50
    # 987×247-es megjelenítés, 247 px rövidebb oldal:
    sugar = (_DEFAULT_BRUSH_SIZE / _BRUSH_SIZE_TO_RELATIVE_DIVISOR) * 247
    atmero = 2 * sugar
    assert round(atmero) == 50


def test_retouch_panel_structure() -> None:
    """#7379: a Retusálás panel címe 'Retouch blemishes', ikon és 'Regions selected' sor nélkül."""
    panel_qml = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy/EditorRetouchPanel.qml"
    content = panel_qml.read_text(encoding="utf-8")

    assert 'qsTr("Retouch blemishes")' in content
    assert 'objectName: "retouchRegionCountLabel"' not in content
    assert 'Regions selected' not in content
    assert 'source: "../../assets/tools/retouch.png"' not in content


def test_photo_viewer_context_actions_retouch_dialog_source() -> None:
    """#7379: a PhotoViewerContextActions.qml-ben a retouch megerősítő a mért alakot adja."""
    actions_qml = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy/PhotoViewerContextActions.qml"
    content = actions_qml.read_text(encoding="utf-8")

    assert 'key === "retouch"' in content
    assert 'title = qsTr("Confirm")' in content
    assert 'iconType = "picasa"' in content
    assert 'yesText = qsTr("Undo")' in content
    assert 'noText = qsTr("No")' in content
    assert 'cancelVisible = false' in content
    assert 'rememberVisible = false' in content
    assert 'focusNoOnOpen = true' in content
    assert 'dimBackground = false' in content
    # a Vörösszem ága a régi alakot tartja (halványítással együtt)
    assert 'dimBackground = true' in content
    # a jelölő nélküli retus-ablakot egy régi elnyomás nem némíthatja el
    assert 'ask(key === "retouch" ? "" : "undo-" + key, text)' in content


def test_confirm_dialog_retouch_mode_behavior(qt_app) -> None:
    """#7379: a ConfirmDialog a retouch paraméterekkel a kétgombos elutasító fókuszos alakot ölti."""
    engine = QQmlEngine()
    import_path = str(Path(__file__).parents[2] / "src/picasapy/app/qml")
    engine.addImportPath(import_path)

    qml_file = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy/ConfirmDialog.qml"
    component = QQmlComponent(engine, str(qml_file))
    assert component.isReady(), component.errorString()

    dialog = component.create()
    assert dialog is not None
    try:
        # Retouch beállítások alkalmazása
        dialog.setProperty("title", "Confirm")
        dialog.setProperty("iconType", "picasa")
        dialog.setProperty("yesText", "Undo")
        dialog.setProperty("noText", "No")
        dialog.setProperty("cancelVisible", False)
        dialog.setProperty("rememberVisible", False)
        dialog.setProperty("focusNoOnOpen", True)
        # alapból a modális ablak halványítja a hátteret; a retus-ág kikapcsolja
        assert dialog.property("dim") is True
        dialog.setProperty("dimBackground", False)
        assert dialog.property("dim") is False

        assert dialog.property("title") == "Confirm"
        assert dialog.property("iconType") == "picasa"
        assert dialog.property("yesText") == "Undo"
        assert dialog.property("noText") == "No"
        assert dialog.property("cancelVisible") is False
        assert dialog.property("rememberVisible") is False
        assert dialog.property("focusNoOnOpen") is True

        confirmed_calls = []
        denied_calls = []
        dialog.confirmed.connect(lambda: confirmed_calls.append(True))
        dialog.denied.connect(lambda: denied_calls.append(True))

        # Elutasítás tesztelése (_deny hívás a No gomb útján)
        dialog._deny()
        qt_app.processEvents()
        assert denied_calls == [True]
        assert confirmed_calls == []
    finally:
        dialog.deleteLater()
        qt_app.processEvents()
