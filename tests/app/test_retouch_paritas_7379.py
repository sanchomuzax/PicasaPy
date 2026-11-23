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


def test_az_ecsetmeret_leképezés_nem_változott() -> None:
    """#7379 NEM módosítja az ecsetméret-leképezést: az eredeti leképezése nincs lezárva (7327-11,
    külön jegy: 7327-11c/11d), ezért az osztó és az alapállás a korábbi marad."""
    assert _DEFAULT_BRUSH_SIZE == 20
    assert _BRUSH_SIZE_TO_RELATIVE_DIVISOR == 1000.0


def test_retouch_panel_structure() -> None:
    """#7379: a Retusálás panel címe 'Retouch blemishes', ikon és 'Regions selected' sor nélkül."""
    panel_qml = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy/EditorRetouchPanel.qml"
    content = panel_qml.read_text(encoding="utf-8")

    assert 'qsTr("Retouch blemishes")' in content
    assert 'objectName: "retouchRegionCountLabel"' not in content
    assert 'Regions selected' not in content
    assert 'source: "../../assets/tools/retouch.png"' not in content


def test_photo_viewer_context_actions_retouch_dialog_source() -> None:
    """#7379: a PhotoViewerContextActions.qml-ben a retouch megerősítő a mért alakot adja (kötésekkel)."""
    actions_qml = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy/PhotoViewerContextActions.qml"
    content = actions_qml.read_text(encoding="utf-8")

    assert "retouchLook = key === \"retouch\"" in content
    assert 'title: retouchLook ? qsTr("Confirm") : qsTr("Undo")' in content
    assert 'iconType: retouchLook ? "picasa" : "none"' in content
    assert 'yesText: retouchLook ? qsTr("Undo") : qsTr("Yes")' in content
    assert 'noText: qsTr("No")' in content
    assert "cancelVisible: !retouchLook" in content
    assert "rememberVisible: !retouchLook" in content
    assert "focusNoOnOpen: retouchLook" in content
    assert "dimBackground: !retouchLook" in content
    assert "nativeButtons: retouchLook" in content
    # a jelölő nélküli retus-ablakot egy régi elnyomás nem némíthatja el
    assert 'ask(retouchLook ? "" : "undo-" + key, text)' in content


def test_a_natív_gombkinézet_opt_in_a_többi_hívó_változatlan(qt_app) -> None:
    """#7379: a natív (fehér, keretes) gomb és a hozzá tartozó ConfirmDialog-jelző alapból kikapcsolt,
    tehát a program többi gombja és párbeszéde (zöld Yes-gomb, 8 képpontos köz) változatlan."""
    engine = QQmlEngine()
    qml_root = Path(__file__).parents[2] / "src/picasapy/app/qml"
    engine.addImportPath(str(qml_root))

    gomb = QQmlComponent(engine, str(qml_root / "PicasaPy" / "PicasaButton.qml"))
    assert gomb.isReady(), gomb.errorString()
    peldany = gomb.create()
    assert peldany is not None
    try:
        assert peldany.property("nativeLook") is False
    finally:
        peldany.deleteLater()

    parbeszed = QQmlComponent(engine, str(qml_root / "PicasaPy" / "ConfirmDialog.qml"))
    assert parbeszed.isReady(), parbeszed.errorString()
    dialog = parbeszed.create()
    assert dialog is not None
    try:
        assert dialog.property("nativeButtons") is False
        assert dialog.property("dimBackground") is True
    finally:
        dialog.deleteLater()
        qt_app.processEvents()


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
        dialog.setProperty("nativeButtons", True)
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
        assert dialog.property("nativeButtons") is True

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
