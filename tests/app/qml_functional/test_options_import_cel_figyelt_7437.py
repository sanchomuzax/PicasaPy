"""#7437: Az Opciókban beállított importcél kerüljön a figyelt mappák közé."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtTest import QTest
from support.halasztott_parbeszed import nyisd_meg
from support.varakozas import var_feltetelre


def _elem(gyoker, nev: str):
    talalat = gyoker.findChild(QObject, nev)
    assert talalat is not None, f"{nev} nem található"
    return talalat


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0):
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _kattint(ablak, elem, qt_app):
    assert elem.property("enabled") is True, f"{elem.objectName()} le van tiltva"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()} nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    for _ in range(10):
        qt_app.processEvents()


def _nyisd_meg_options(foablak, qt_app):
    menu = _elem(foablak, "menuToolsOptions")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    _varj(
        qt_app,
        lambda: foablak.findChild(QObject, "optionsDialog") is not None
        and foablak.findChild(QObject, "optionsDialog").property("visible"),
        "a Beállítások ablaka nem nyílt meg",
    )
    return _elem(foablak, "optionsDialog")


def _valassz_mappat_es_fogadd_el(options, mappa: Path, qt_app):
    tallozo = _elem(options, "optionsImportDestBrowseButton")
    _kattint(options, tallozo, qt_app)
    valaszto = _elem(options, "optionsImportDestFolderDialog")
    _varj(
        qt_app,
        lambda: valaszto.property("visible") is True,
        "a Tallózás gomb nem nyitotta meg a mappaválasztót",
    )
    url = QUrl.fromLocalFile(str(mappa.resolve()))
    valaszto.setProperty("selectedFolder", url)
    assert QMetaObject.invokeMethod(
        valaszto, "accepted", Qt.ConnectionType.DirectConnection
    )
    mezo = _elem(options, "optionsImportDestField")
    _varj(
        qt_app,
        lambda: Path(str(mezo.property("text"))) == mappa.resolve(),
        "a Tallózásban választott mappa nem jelent meg a beállításban",
    )
    valaszto.setProperty("visible", False)
    qt_app.processEvents()


def _nyisd_meg_folder_manager(foablak, qt_app):
    nyisd_meg(foablak, "folderManagerDialog")
    _varj(
        qt_app,
        lambda: foablak.findChild(QObject, "folderManagerDialog") is not None,
        "a Mappakezelő ablaka nem épült fel",
    )
    dialog = _elem(foablak, "folderManagerDialog")
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    _varj(
        qt_app,
        lambda: dialog.property("visible") is True,
        "a Mappakezelő ablaka nem nyílt meg",
    )
    return dialog


def test_import_cel_figyelt_mappak_koze_kerul_7437(qml_app, qt_app, tmp_path):
    foablak, controller, _engine = qml_app
    lib = Path(controller.watchedFolders[0])

    # (1) Új importcél Browse-zal és OK-val -> watchedFolders és Folder Manager visibleWatched listában
    uj_cel = tmp_path / "uj_import_cel"
    uj_cel.mkdir()
    uj_cel_feloldva = str(uj_cel.resolve())
    assert uj_cel_feloldva not in controller.watchedFolders

    options = _nyisd_meg_options(foablak, qt_app)
    _valassz_mappat_es_fogadd_el(options, uj_cel, qt_app)
    ok_gomb = _elem(options, "optionsOkButton")
    _kattint(options, ok_gomb, qt_app)
    _varj(
        qt_app,
        lambda: not options.property("visible"),
        "az OK gomb nem zárta be a Beállításokat",
    )

    assert uj_cel_feloldva in controller.watchedFolders, (
        f"Az új importcél ({uj_cel_feloldva}) nem került a figyelt gyökerek közé"
    )

    fm_dialog = _nyisd_meg_folder_manager(foablak, qt_app)
    visible_watched = list(fm_dialog.property("visibleWatched").toVariant() or [])
    assert uj_cel_feloldva in visible_watched, (
        f"Az új importcél ({uj_cel_feloldva}) nem szerepel a Mappakezelő figyelt listájában: {visible_watched}"
    )
    QMetaObject.invokeMethod(fm_dialog, "cancelChanges", Qt.ConnectionType.DirectConnection)
    _varj(qt_app, lambda: not fm_dialog.property("visible"), "a Mappakezelő nem záródott be")

    # (2) Új importcél Browse-zal és Cancel-lel -> NEM kerül felvételre
    cancel_cel = tmp_path / "cancel_import_cel"
    cancel_cel.mkdir()
    cancel_cel_feloldva = str(cancel_cel.resolve())
    assert cancel_cel_feloldva not in controller.watchedFolders

    options = _nyisd_meg_options(foablak, qt_app)
    _valassz_mappat_es_fogadd_el(options, cancel_cel, qt_app)
    cancel_gomb = _elem(options, "optionsCancelButton")
    _kattint(options, cancel_gomb, qt_app)
    _varj(
        qt_app,
        lambda: not options.property("visible"),
        "a Cancel gomb nem zárta be a Beállításokat",
    )

    assert cancel_cel_feloldva not in controller.watchedFolders, (
        "Cancel után az importcél tévesen felvételre került a figyelt gyökerek közé"
    )

    fm_dialog = _nyisd_meg_folder_manager(foablak, qt_app)
    visible_watched = list(fm_dialog.property("visibleWatched").toVariant() or [])
    assert cancel_cel_feloldva not in visible_watched, (
        "Cancel után az importcél tévesen szerepel a Mappakezelő figyelt listájában"
    )
    QMetaObject.invokeMethod(fm_dialog, "cancelChanges", Qt.ConnectionType.DirectConnection)
    _varj(qt_app, lambda: not fm_dialog.property("visible"), "a Mappakezelő nem záródott be")

    # (3) Már figyelt mappa vagy figyelt mappa alatti mappa -> nincs duplikátum
    darabszam_elotte = len(controller.watchedFolders)
    assert str(lib.resolve()) in controller.watchedFolders

    # 3a: Közvetlenül már figyelt gyökér kiválasztása
    options = _nyisd_meg_options(foablak, qt_app)
    _valassz_mappat_es_fogadd_el(options, lib, qt_app)
    ok_gomb = _elem(options, "optionsOkButton")
    _kattint(options, ok_gomb, qt_app)
    _varj(
        qt_app,
        lambda: not options.property("visible"),
        "az OK gomb nem zárta be a Beállításokat",
    )
    assert len(controller.watchedFolders) == darabszam_elotte
    assert list(controller.watchedFolders).count(str(lib.resolve())) == 1

    # 3b: Figyelt gyökér alatti almappa kiválasztása
    almappa = lib / "al_mappa"
    almappa.mkdir()
    almappa_feloldva = str(almappa.resolve())

    options = _nyisd_meg_options(foablak, qt_app)
    _valassz_mappat_es_fogadd_el(options, almappa, qt_app)
    ok_gomb = _elem(options, "optionsOkButton")
    _kattint(options, ok_gomb, qt_app)
    _varj(
        qt_app,
        lambda: not options.property("visible"),
        "az OK gomb nem zárta be a Beállításokat",
    )
    assert almappa_feloldva not in controller.watchedFolders, (
        "Figyelt gyökér alatti almappa nem vehető fel külön gyökérként"
    )
    assert len(controller.watchedFolders) == darabszam_elotte
