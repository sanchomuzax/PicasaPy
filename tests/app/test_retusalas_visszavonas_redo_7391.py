"""A megerősített retusálás-visszavonás nem hagy Újra-bejegyzést (#7391).

Az eredetiben az „Undo Retouches" megerősített visszavonása után az „Undo" és a
„Redo" egyaránt tiltott, a feliratuk csupasz (job-907 `__24`); a „Retouch fixes
cannot be recovered with redo." üzenet szerint a retusálás nem hozható vissza.

⚠️ Ez a próba a vezérlő állapotát olvassa (számol), a gombok képét nem veti össze
semmivel: a renderelt, a `job-907 __24` bal paneljével összevetett próba
`tests/app/qml_functional/test_retusalas_redo_panel_7391.py`.

Mérve csak az egyszerű eset (retusálás Apply, majd megerősített Undo). Hogy az
eredeti mit tesz, ha a retusálás UTÁN még egy lépést visszavontunk (azaz van
Újra-bejegyzés), NINCS mérve: az itt megadott viselkedés (a verem ürül) a
„nem hozható vissza" üzenetből következő döntés, nem felvételből mért adat.
"""

from __future__ import annotations

import pytest
from PySide6.QtTest import QSignalSpy

from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    make_jpeg(tmp_path / "a.jpg", size=(320, 160))
    ctl = EditController(EditPreviewProvider())
    ctl.beginEdit("1", str(tmp_path / "a.jpg"))
    return ctl


def _retusalast_alkalmaz(ctl) -> None:
    ctl.enterRetouchTool()
    ctl.beginRetouchPatch(0.5, 0.5)
    ctl.commitRetouchPatch(0.2, 0.2)
    ctl.applyRetouch()
    ctl.exitRetouchTool()


def test_megerositett_retusalas_visszavonas_utan_nincs_ujra(controller) -> None:
    """(1) Retusálás Apply, Undo után az Undo és a Redo is tiltott, a feliratuk csupasz."""
    _retusalast_alkalmaz(controller)
    assert controller.undoAction == "retouch"
    assert controller.canUndo is True
    assert controller.canRedo is False

    controller.undo()

    assert controller.hasRetouch is False
    assert controller.canUndo is False
    assert controller.undoAction == ""
    assert controller.undoLabel == "Undo"
    assert controller.canRedo is False
    assert controller.redoAction == ""
    assert controller.redoLabel == "Redo"


def test_az_ujra_nem_hozza_vissza_a_retusalast(controller) -> None:
    _retusalast_alkalmaz(controller)
    controller.undo()
    controller.redo()  # tiltott gomb: a hívás nem tehet semmit
    assert controller.hasRetouch is False
    assert controller.canRedo is False


def test_mas_muvelet_visszavonasa_utan_az_ujra_aktiv_marad(controller) -> None:
    """(4) A Crop Undo-ja után a Redo továbbra is aktív, „Redo: Crop" felirattal."""
    controller.applyCrop(0.1, 0.1, 0.5, 0.5)
    controller.undo()
    assert controller.canRedo is True
    assert controller.redoAction == "crop"
    assert controller.redoLabel.startswith("Redo")
    assert controller.redoLabel != "Redo"
    controller.redo()
    assert controller.hasCrop is True


def test_a_voroszem_visszavonasa_valtozatlanul_az_ujra_verembe_kerul(controller) -> None:
    """A Vörösszem eredeti viselkedése nincs mérve (7327-10), ezért a régi marad."""
    controller.enterRedeyeTool()
    controller.addRedeyeRegion(0.40, 0.40, 0.10, 0.10)
    controller.applyRedeye()
    assert controller.undoAction == "redeye"
    controller.undo()
    assert controller.canRedo is True
    assert controller.redoAction == "redeye"


def test_retusalas_egy_masik_lepes_alatt_a_visszavonas_ures_verem(controller) -> None:
    """A retusálás visszavonása után a MEGELŐZŐ lépések Undo-ja a megszokott módon megy."""
    controller.applyCrop(0.1, 0.1, 0.5, 0.5)
    _retusalast_alkalmaz(controller)
    controller.undo()  # a megerősített retusálás-visszavonás
    assert controller.canRedo is False
    assert controller.undoAction == "crop"
    controller.undo()  # a Crop már a megszokott módon az Újra-verembe kerül
    assert controller.canRedo is True
    assert controller.redoAction == "crop"


def test_ujra_bejegyzes_mellett_a_retusalas_visszavonasa_nem_ad_vissza_retusalast(
    controller,
) -> None:
    """Retusálás, majd Crop; a Crop Undo-ja után van Újra-bejegyzés (a Crop utáni állapot, benne a
    retusálással). A retusálás megerősített visszavonása után ez a bejegyzés nem maradhat: a Redo a
    retusálást is visszahozná, holott az üzenet szerint nem hozható vissza.

    NINCS mérve, mit tesz ilyenkor az eredeti: ez a döntés az üzenetből következik, nem felvételből."""
    _retusalast_alkalmaz(controller)
    controller.applyCrop(0.1, 0.1, 0.5, 0.5)
    controller.undo()  # a Crop visszavonása: van Újra-bejegyzés
    assert controller.canRedo is True
    assert controller.undoAction == "retouch"

    controller.undo()  # a megerősített retusálás-visszavonás

    assert controller.canRedo is False
    assert controller.redoLabel == "Redo"
    controller.redo()
    assert controller.hasRetouch is False
    assert controller.hasCrop is False


def test_ujrajelzes_kiadodik_ha_a_retusalas_visszavonasa_uriti_a_vermet(controller) -> None:
    """A kötések frissülnek: a `canRedo` és a `redoLabel` változását a kezelő jelzi, különben a
    panel az Újra gombot aktívnak mutatná egy üres veremmel."""
    _retusalast_alkalmaz(controller)
    controller.applyCrop(0.1, 0.1, 0.5, 0.5)
    controller.undo()  # van Újra-bejegyzés, a verem tetején a retusálás
    assert controller.canRedo is True

    can_redo = QSignalSpy(controller.canRedoChanged)
    redo_label = QSignalSpy(controller.redoLabelChanged)
    controller.undo()  # a megerősített retusálás-visszavonás

    assert controller.canRedo is False
    assert can_redo.count() >= 1
    assert redo_label.count() >= 1


def test_ujranyitott_kep_mentett_retusalasanak_visszavonasa_sem_ad_ujrat(
    qt_app, tmp_path
) -> None:
    """Az újranyitáskor a mentett láncból épített verem `retouch` lépése is ugyanígy viselkedik."""
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    make_jpeg(tmp_path / "a.jpg", size=(320, 160))
    elso = EditController(EditPreviewProvider())
    elso.beginEdit("1", str(tmp_path / "a.jpg"))
    _retusalast_alkalmaz(elso)
    elso.endEdit()

    masodik = EditController(EditPreviewProvider())
    masodik.beginEdit("1", str(tmp_path / "a.jpg"))
    assert masodik.undoAction == "retouch"
    masodik.undo()
    assert masodik.canRedo is False
    assert masodik.redoLabel == "Redo"
    assert masodik.hasRetouch is False
