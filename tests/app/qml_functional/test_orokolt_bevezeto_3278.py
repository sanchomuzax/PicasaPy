"""#3278/#6443: a korábbi szürke bevezetőt a fül buboréksúgója váltja fel."""

from __future__ import annotations

from PySide6.QtCore import QObject


def test_combined_tab_keeps_the_requested_tooltip_without_intro_text(
    qml_app, qt_app
):
    window = qml_app[0]
    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("activeTab", 5)
    qt_app.processEvents()

    tab = window.findChild(QObject, "editTabEffects4")
    assert tab is not None
    assert tab.property("description") == (
        "Forgotten or deprecated effects brought back to life"
    )
    assert window.findChild(QObject, "legacyEffectsIntro") is None
