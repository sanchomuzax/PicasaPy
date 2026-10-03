"""A valódi szerkesztőgomb frissítése Alkalmaz/Mégse után (#4063)."""

from pathlib import Path
from time import monotonic

import pytest
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTranslator
from PySide6.QtTest import QTest


_I18N_DIR = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "picasapy"
    / "app"
    / "i18n"
)
_VISSZAVONAS_URESEN = "Visszavonás"


@pytest.fixture
def _magyar_forditas(qt_app):
    """A valódi feliratot a termék magyar fordítójával ellenőrizzük."""
    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(_I18N_DIR)), (
        "a picasapy_hu.qm nem tölthető be"
    )
    qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található a főablakban"
    return item


def _wait_until(qt_app, condition, description: str, timeout_s: float = 3.0) -> None:
    """Határidőig eseményeket dolgoz fel, és állapotváltozásra vár."""
    deadline = monotonic() + timeout_s
    while not condition() and monotonic() < deadline:
        qt_app.processEvents()
        QTest.qWait(10)
    qt_app.processEvents()
    assert condition(), description


def _click(window, item, qt_app) -> None:
    assert item.property("visible") is True, f"{item.objectName()} nem látható"
    center = item.mapToScene(
        QPointF(float(item.property("width")) / 2,
                float(item.property("height")) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    qt_app.processEvents()


def _open_viewer(qml_app_negyzet_kepek, qt_app):
    window, _controller, _engine = qml_app_negyzet_kepek
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    _wait_until(
        qt_app,
        lambda: _item(window, "viewerEditorPanel").property("visible") is True,
        "a valódi szerkesztőpanel nem nyílt meg",
    )
    assert not window.grabWindow().isNull(), "a főablak nem rajzolódott ki"
    return window, viewer, _item(window, "viewerEditorPanel")


def _visszavonas_allapot(window) -> tuple[bool, str]:
    """A tényleges gomb engedélyezettségét és kirajzolt szövegét olvassa."""
    button = _item(window, "editUndoButton")
    rendered_text = _item(window, "editUndoButtonLabel")
    return bool(button.property("enabled")), str(rendered_text.property("text"))


def _elokeszit_eszkozt(window, viewer, panel, qt_app, tool: str) -> tuple[str, str]:
    """Eszközönként létrehozza az Alkalmazáshoz szükséges piszkozatot."""
    edit = viewer.property("editCtl")
    if tool == "param":
        panel.setProperty("activeTab", 2)
        qt_app.processEvents()
        _click(window, _item(window, "effectRadsat"), qt_app)
        gombnev = "effectParamApplyButton"
        megse_gombnev = "effectParamCancelButton"
    else:
        eszkoz_csempe = {
            "crop": "editToolCrop",
            "tilt": "editToolTilt",
            "retouch": "editToolRetouch",
            "redeye": "editToolRedeye",
            "text": "editToolText",
        }[tool]
        _click(window, _item(window, eszkoz_csempe), qt_app)

    if tool == "param":
        pass
    elif tool == "crop":
        overlay = _item(window, "cropOverlay")
        overlay.setProperty("cropRect", QRectF(0.2, 0.2, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        gombnev = "cropApplyButton"
        megse_gombnev = "cropCancelButton"
    elif tool == "tilt":
        slider = _item(window, "tiltSlider")
        point = slider.mapToScene(
            QPointF(float(slider.property("width")) * 0.8,
                    float(slider.property("height")) / 2)
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            point.toPoint(),
        )
        _wait_until(
            qt_app,
            lambda: abs(float(slider.property("value"))) > 0.1,
            "a valódi csúszkakattintás nem állított be kiegyenesítést",
        )
        gombnev = "tiltApplyButton"
        megse_gombnev = "tiltCancelButton"
    elif tool == "retouch":
        edit.beginRetouchPatch(0.5, 0.5)
        edit.commitRetouchPatch(0.2, 0.2)
        gombnev = "retouchApplyButton"
        megse_gombnev = "retouchCancelButton"
    elif tool == "redeye":
        edit.addRedeyeRegion(0.3, 0.3, 0.2, 0.2)
        gombnev = "redeyeApplyButton"
        megse_gombnev = "redeyeCancelButton"
    else:
        _item(window, "textContentField").setProperty("text", "Próbaszöveg")
        qt_app.processEvents()
        edit.previewTextPlacement(0.5, 0.5)
        gombnev = "textApplyButton"
        megse_gombnev = "textCancelButton"

    qt_app.processEvents()
    apply_button = _item(window, gombnev)
    cancel_button = _item(window, megse_gombnev)
    assert cancel_button.property("visible") is True
    _wait_until(
        qt_app,
        lambda: apply_button.property("enabled") is True,
        f"az előkészített {tool} Alkalmaz gombja nem engedélyezett",
    )
    return gombnev, megse_gombnev


@pytest.mark.parametrize(
    ("tool", "apply_text"),
    (
        ("crop", "Visszavonás: Vágás"),
        ("tilt", "Visszavonás: Kiegyenesítés"),
        ("retouch", "Visszavonás: Retusálások"),
        ("redeye", "Visszavonás: Vörösszem"),
        ("param", "Visszavonás: Fókuszos FF"),
        # A text= külön ini-kulcs, szándékosan nem része a filters= undo-veremnek.
        ("text", None),
    ),
    ids=("crop", "straighten", "retouch", "red-eye", "effect-params", "text-not-undoable"),
)
@pytest.mark.parametrize("action", ("apply", "cancel"), ids=("alkalmaz", "megse"))
def test_alkalmaz_megse_utan_a_valodi_visszavonas_gomb_frissul(
    _magyar_forditas, qml_app_negyzet_kepek, qt_app, tool, apply_text, action
):
    """A felhasználó által látott és kattintható gomb állapota a mérce."""
    window, viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app)
    assert _visszavonas_allapot(window) == (False, _VISSZAVONAS_URESEN)
    apply_name, cancel_name = _elokeszit_eszkozt(
        window, viewer, panel, qt_app, tool
    )

    gomb = _item(window, apply_name if action == "apply" else cancel_name)
    _click(window, gomb, qt_app)

    vart_felirat = (
        apply_text
        if action == "apply" and apply_text is not None
        else _VISSZAVONAS_URESEN
    )
    vart_engedelyezett = action == "apply" and apply_text is not None
    aktualis = _visszavonas_allapot(window)
    print(
        f"#4063 {tool}/{action}: editUndoButton.enabled={aktualis[0]}, "
        f"renderelt szöveg={aktualis[1]!r}"
    )
    assert aktualis == (vart_engedelyezett, vart_felirat), (
        f"{tool}/{action} után a valódi Visszavonás gomb állapota hibás: "
        f"várt={(vart_engedelyezett, vart_felirat)!r}, kapott={aktualis!r}"
    )
