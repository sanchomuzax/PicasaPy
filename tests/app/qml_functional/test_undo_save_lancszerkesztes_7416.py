"""#7416: az Undo Save UTÁN az Undo gomb a visszaállított szerkesztési láncból épül.

Mérce: picasa-colab-jobs job-940 (gray_ramp.jpg, 1024x256): Kiegyenesítés
(húzás 740-ig), Alkalmaz, Mentés, Undo Save, majd a tiltott Redo kattintása.

* `__18` (Mentés után): „Undo Save", aktív, „Redo" tiltott, „23 KB".
* `__20` (az Undo Save kattintása után): nincs ablak, „Undo Straighten" aktív,
  „Redo" tiltott, „31 KB", a kép a kiegyenesített.
* `__22` (a tiltott Redo kattintása): hatástalan.
* záró fő ini: `backuphash=30630`, `filters=tilt=1,0.391249,0.000000;`,
  `moddate=67eb71776d7bdd01`; `.picasaoriginals/.picasa.ini` 0 bájt,
  `.picasaoriginals/gray_ramp.jpg` nincs.

A képminta a kirajzolt kép 10 x 3 pontja (a #7393 módszere), a `__20` felvételről
mérve (a `__14`-től legfeljebb 1 szint). A szöveges ellenpéldát (az Undo Save
után tiltott, csupasz Undo; `job-919 __22`) a #7408 próbája őrzi
(`test_undo_save_button_7408.py`).
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtQuick import QQuickItem
from support.qt_wait import wait_for_photo_op

from picasapy.app.edit_action_names import undo_label
from picasapy.ini import load_document
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints
from tests.app.qml_functional.test_kiegyenesites_ujranyitas_7393 import (
    HELYI_740,
    Nezo,
)
from tests.app.qml_functional.test_undo_save_button_7408 import (  # noqa: F401
    picasa_szurke_rampas_app as rampas_app_7408,
)
from tests.support.varakozas import var_feltetelre

#: A job-940 `__20` kocka mintája (a kiegyenesített kép Undo Save után).
JOB940_20_MINTA = [
    [40, 59, 79, 98, 118, 137, 156, 176, 195, 215],
    [39, 58, 78, 97, 116, 136, 156, 175, 194, 214],
    [38, 57, 77, 96, 116, 135, 154, 173, 193, 212],
]
#: A kiegyenesítetlen rámpa a 10 oszlopban (`__8`, job-913): kontroll, hogy a
#: minta a kiegyenesítést különbözteti meg, nem a rámpát mérjük vele.
KIEGYENESITETLEN_MINTA = [12, 37, 63, 88, 114, 139, 165, 190, 216, 241]
#: A mért legnagyobb eltérés 1 szint (JPEG-kerekítés), szándékosan szűken.
MINTA_TURES = 3


def _item(window, nev: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _felirat(window, nev: str) -> str:
    return str(_item(window, f"{nev}Label").property("text") or "")


def _elteres(minta, referencia) -> int:
    return int(np.max(np.abs(np.asarray(minta) - np.asarray(referencia))))


class _Folyamat:
    """Kiegyenesítés, Apply, Mentés, Undo Save valódi vezérlőkön."""

    def __init__(self, app, qt_app, tmp_path) -> None:
        window, self.controller, engine = app
        self.window, self.qt_app = window, qt_app
        window.show()
        window.requestActivate()
        assert var_feltetelre(
            qt_app, lambda: self.controller.photos.rowCount() >= 2, 10.0
        )
        self.nezo = Nezo(window, self.controller, qt_app, tmp_path)
        edit = EditorTestHelpers()._edit_controller(engine)
        assert edit is self.nezo.edit
        self.controller.set_edit_controllers(edit)
        edit._undoSaveRequested.connect(self.controller._undo_save_for_editor)
        self.kep = self.nezo.ini.parent / "gray_ramp.jpg"
        self.undo = _item(window, "editUndoButton")
        self.redo = _item(window, "editRedoButton")

    def kiegyenesit_es_alkalmaz(self) -> None:
        self.nezo.eszkoz_nyit()
        self.nezo.huzas(HELYI_740)
        self.nezo.alkalmaz()
        assert self.nezo.tilt_ertekek() == [pytest.approx(0.391249, abs=0.001)]

    def index_az_apply_utan(self) -> None:
        """A Mentés az INDEX `filters` mezőjéből éget; az éles app fájlfigyelője
        az Apply után frissíti, a próba-appban nem fut, ezért kézzel."""
        self.controller._resync_disk_operation_folders([self.kep])
        self.controller._refresh_view()
        lanc = self.nezo.ini_lanc()[len("filters="):]
        assert var_feltetelre(
            self.qt_app,
            lambda: self.controller.photos.photos[0].filters == lanc,
            10.0,
        ), "az index nem vette át az Apply láncát"

    def ment(self) -> None:
        self.index_az_apply_utan()
        wait_for_photo_op(
            self.controller,
            lambda: self.controller.saveRowsToDisk([0]),
            qt_app=self.qt_app,
        )
        assert var_feltetelre(
            self.qt_app,
            lambda: _felirat(self.window, "editUndoButton")
            == QCoreApplication.translate("SaveDialogs", "Undo Save"),
            10.0,
        ), "a Mentés után az Undo gomb nem „Undo Save”"

    def undo_save_kattintas(self) -> None:
        kattints(self.window, self.qt_app, self.undo)
        wait_for_photo_op(self.controller, lambda: None, qt_app=self.qt_app)
        assert self.nezo.edit.waitForBackgroundWorkers(10.0)
        assert var_feltetelre(
            self.qt_app,
            lambda: _felirat(self.window, "editUndoButton")
            != QCoreApplication.translate("SaveDialogs", "Undo Save"),
            10.0,
        ), "az Undo Save kattintása után a gomb nem változott"


@pytest.fixture
def folyamat(rampas_app_7408, qt_app, tmp_path):  # noqa: F811
    return _Folyamat(rampas_app_7408, qt_app, tmp_path)


def test_mentes_nelkul_az_apply_utan_az_undo_gomb_undo_straighten(folyamat):
    """Kész, ha (4): a Mentés nélküli Apply után a gomb nem „Undo Save”."""
    folyamat.kiegyenesit_es_alkalmaz()

    assert folyamat.undo.property("enabled") is True
    assert _felirat(folyamat.window, "editUndoButton") == undo_label("tilt")
    assert _felirat(folyamat.window, "editUndoButton") != (
        QCoreApplication.translate("SaveDialogs", "Undo Save")
    )
    assert folyamat.redo.property("enabled") is False


def test_kiegyenesites_mentes_undo_save_utan_az_undo_undo_straighten(
    folyamat, tmp_path
):
    """Kész, ha (1) és (2): job-940 `__20` és a záró fájlállapot."""
    folyamat.kiegyenesit_es_alkalmaz()
    nezo, window = folyamat.nezo, folyamat.window
    lanc_mentes_elott = nezo.ini_lanc()
    assert lanc_mentes_elott.startswith("filters=tilt=1,0.391")
    bajtok_mentes_elott = folyamat.kep.read_bytes()
    mtime_mentes_elott = folyamat.kep.stat().st_mtime_ns
    assert _elteres(nezo.kep_minta(), JOB940_20_MINTA) <= MINTA_TURES, (
        "a próbakép a Mentés előtt sem a kiegyenesített (kontroll)"
    )

    folyamat.ment()
    assert folyamat.redo.property("enabled") is False
    assert window.grabWindow().save(str(tmp_path / "mentes-utan.png"))
    folyamat.undo_save_kattintas()
    assert window.grabWindow().save(str(tmp_path / "undo-save-utan.png"))

    # (1) a gomb a visszaállított láncból: „Undo Straighten", aktív; Redo tiltott
    assert folyamat.undo.property("enabled") is True
    assert nezo.edit.property("undoAction") == "tilt"
    assert _felirat(window, "editUndoButton") == undo_label("tilt")
    assert _felirat(window, "editUndoButton") not in (
        QCoreApplication.translate("EditorPanel", "Undo"),
        QCoreApplication.translate("SaveDialogs", "Undo Save"),
    )
    assert folyamat.redo.property("enabled") is False
    assert _felirat(window, "editRedoButton") == QCoreApplication.translate(
        "EditorPanel", "Redo"
    )
    # a kép a kiegyenesített, nem a rámpa (kontroll: a rámpától messze van)
    assert var_feltetelre(
        folyamat.qt_app,
        lambda: _elteres(nezo.kep_minta(), JOB940_20_MINTA) <= MINTA_TURES,
        10.0,
    ), (
        "az Undo Save után a kép nem a kiegyenesített: "
        f"eltérés {_elteres(nezo.kep_minta(), JOB940_20_MINTA)}"
    )
    assert _elteres([nezo.kep_minta()[1]], [KIEGYENESITETLEN_MINTA]) > 3 * MINTA_TURES

    # (2) fájlállapot: lánc a fő ini-ben, eredeti-mappa tiszta, bájtok vissza
    kepmappa = folyamat.kep.parent
    szakasz = load_document(kepmappa / ".picasa.ini").section("gray_ramp.jpg")
    assert szakasz is not None
    assert szakasz.get("filters") == lanc_mentes_elott[len("filters="):]
    assert szakasz.get("moddate")
    originals = kepmappa / ".picasaoriginals"
    assert not (originals / "gray_ramp.jpg").exists()
    assert (originals / ".picasa.ini").read_bytes() == b""
    assert folyamat.kep.read_bytes() == bajtok_mentes_elott
    assert folyamat.kep.stat().st_mtime_ns == mtime_mentes_elott
    revert = window.findChild(QQuickItem, "revertConfirmDialog")
    assert revert is None or revert.property("visible") is False


def test_a_tiltott_redo_kattintasa_az_undo_save_utan_hatastalan(folyamat):
    """job-940 `__22`: a tiltott Redo nem változtat semmit."""
    folyamat.kiegyenesit_es_alkalmaz()
    folyamat.ment()
    folyamat.undo_save_kattintas()
    nezo = folyamat.nezo
    lanc, felirat = nezo.ini_lanc(), _felirat(folyamat.window, "editUndoButton")
    bajtok = folyamat.kep.read_bytes()

    kattints(folyamat.window, folyamat.qt_app, folyamat.redo)
    wait_for_photo_op(folyamat.controller, lambda: None, qt_app=folyamat.qt_app)

    assert folyamat.redo.property("enabled") is False
    assert folyamat.undo.property("enabled") is True
    assert _felirat(folyamat.window, "editUndoButton") == felirat == undo_label("tilt")
    assert nezo.ini_lanc() == lanc
    assert folyamat.kep.read_bytes() == bajtok
    assert _elteres(nezo.kep_minta(), JOB940_20_MINTA) <= MINTA_TURES
