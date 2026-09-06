"""#2497 — a szerkesztés mentési hibái ne csak „elmenjenek", hanem
LÁTSZÓDJANAK: a VALÓDI alkalmazásfában (Main.qml + valódi `EditController`)
a három jelzés hatására a párbeszéd ÁLLAPOTA változik meg (`visible`).

Miért nem elég a meglévő #459-es teszt: az egy `_FakeEditController`-rel,
önállóan betöltött `EditorPanel`-en csak az `message` szövegtulajdonságot
állítja. A projekt tanulsága szerint a „jelzés elment"-típusú teszt üresen
zöld tud lenni — a bekötés LÁNCÁT kell mérni (valódi kontextus-tulajdonság,
valódi ablak), és a felület ÁLLAPOTÁT állítani.

A harmadik jelzésnek (`editChainRejected`, #643) eddig SEMMILYEN
felület-tesztje nem volt.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

import pytest


@pytest.fixture
def edit_controller(qml_app):
    """A VALÓDI, Main.qml-hez kötött `editController` kontextus-tulajdonság."""
    _window, _controller, engine = qml_app
    controller = engine.rootContext().contextProperty("editController")
    assert controller is not None, "az editController nincs a QML-kontextusban"
    return controller


def _dialog(window, name: str) -> QObject:
    dialog = window.findChild(QObject, name)
    assert dialog is not None, f"nincs ilyen párbeszéd a valódi fában: {name}"
    return dialog


class TestMentesiHibaLatszik:
    def test_csak_olvashato_mappa_megnyitja_a_parbeszedet(self, qml_app, qt_app,
                                                          edit_controller):
        window, _controller, _engine = qml_app
        dialog = _dialog(window, "editReadOnlyDialog")
        assert dialog.property("visible") is False

        edit_controller.editSaveReadOnly.emit()
        qt_app.processEvents()

        assert dialog.property("visible") is True, (
            "az írásvédettség NÉMÁN futott le — a párbeszéd nem nyílt meg"
        )
        assert "read only" in dialog.property("message")

    def test_lemezhiba_megnyitja_a_hibaparbeszedet(self, qml_app, qt_app,
                                                   edit_controller):
        window, _controller, _engine = qml_app
        dialog = _dialog(window, "editSaveErrorDialog")
        assert dialog.property("visible") is False

        edit_controller.editSaveFailed.emit("teszt: a lemez megtelt")
        qt_app.processEvents()

        assert dialog.property("visible") is True, (
            "a mentési hiba NÉMÁN futott le — a párbeszéd nem nyílt meg"
        )
        message = dialog.property("message")
        assert "disk error" in message
        assert "teszt: a lemez megtelt" in message

    def test_lanc_visszautasitas_megnyitja_a_hibaparbeszedet(self, qml_app, qt_app,
                                                             edit_controller):
        """#643: az őr visszautasítása — itt a lemezzel semmi baj, ezért az
        üzenet a kivételé, „disk error" keret NÉLKÜL."""
        window, _controller, _engine = qml_app
        dialog = _dialog(window, "editSaveErrorDialog")
        assert dialog.property("visible") is False

        edit_controller.editChainRejected.emit("teszt: az őr visszautasította")
        qt_app.processEvents()

        assert dialog.property("visible") is True, (
            "a lánc visszautasítása NÉMÁN futott le (#2497)"
        )
        message = dialog.property("message")
        assert message == "teszt: az őr visszautasította"
        assert "disk error" not in message
