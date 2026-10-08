"""A feliratvágólap meglévő képfeliratot csak megerősítéssel cserél (#4628)."""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest

from tests.support.qt_wait import wait_for_photo_op


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem) -> None:
    assert _varj(qt_app, lambda: elem.width() > 0 and elem.height() > 0), (
        f"{elem.objectName()}: nincs mérete, nem kattintható"
    )
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _kijelol(window, qt_app, controller, height_delta: int) -> int:
    window.setProperty("height", float(window.property("height")) + height_delta)
    sor = next(
        i for i, photo in enumerate(controller.photos.photos)
        if photo.name == "a.jpg"
    )
    window.setProperty("selectedIndex", sor)
    window.setProperty("selectedIndexes", [sor])
    qt_app.processEvents()
    return sor


def _indit_beillesztest(window, qt_app) -> None:
    assert QMetaObject.invokeMethod(
        window,
        "illesdBeAFeliratot",
        Qt.ConnectionType.DirectConnection,
    ), "a Szöveg beillesztése kezelő nem hívható"
    qt_app.processEvents()


class TestFeliratBeillesztesMegerositese:
    def test_csere_a_replace_gombbal(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        sor = _kijelol(window, qt_app, controller, height_delta=5)
        wait_for_photo_op(controller, lambda: controller.setCaption(sor, "Régi felirat"))
        controller.setCaptionClipboardText("Új felirat")

        _indit_beillesztest(window, qt_app)
        dialog = _gyerek(window, "pasteCaptionReplaceDialog")
        assert _varj(qt_app, lambda: dialog.property("opened")), (
            "a meglévő felirat lecserélése előtt nincs megerősítés"
        )
        assert _gyerek(window, "pasteCaptionReplaceMessage").property("text") == (
            "Are you sure you want to replace the existing caption with the "
            "contents of the clipboard?\n(This operation is not undoable)"
        )
        assert _gyerek(window, "pasteCaptionReplaceButton").property("text") == "Replace"
        assert _gyerek(window, "pasteCaptionCancelButton").property("text") == "Cancel"

        _kattints(window, qt_app, _gyerek(window, "pasteCaptionReplaceButton"))

        assert _varj(
            qt_app, lambda: controller.photos.captionAt(sor) == "Új felirat"
        ), "a Csere gomb nem cserélte le a feliratot"
        assert not dialog.property("opened")

    def test_megse_eseten_valtozatlan_marad(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        sor = _kijelol(window, qt_app, controller, height_delta=-5)
        wait_for_photo_op(controller, lambda: controller.setCaption(sor, "Maradjon"))
        controller.setCaptionClipboardText("Ne kerüljön be")

        _indit_beillesztest(window, qt_app)
        dialog = _gyerek(window, "pasteCaptionReplaceDialog")
        assert _varj(qt_app, lambda: dialog.property("opened")), (
            "a meglévő felirat lecserélése előtt nincs megerősítés"
        )
        _kattints(window, qt_app, _gyerek(window, "pasteCaptionCancelButton"))

        assert _varj(qt_app, lambda: not dialog.property("opened"))
        assert controller.photos.captionAt(sor) == "Maradjon"

    def test_ures_feliratnal_nem_kerdez(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        sor = _kijelol(window, qt_app, controller, height_delta=0)
        controller.setCaptionClipboardText("Új felirat")

        _indit_beillesztest(window, qt_app)
        dialog = _gyerek(window, "pasteCaptionReplaceDialog")

        assert not dialog.property("opened"), "üres feliratnál nem kell kérdezni"
        assert _varj(
            qt_app, lambda: controller.photos.captionAt(sor) == "Új felirat"
        ), "üres feliratra nem került át a vágólap szövege"
