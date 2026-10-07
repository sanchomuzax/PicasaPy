"""A #4450 beállítása mentődik, és kattintott importnál induló célként él."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QSettings, Qt, QUrl
from PySide6.QtTest import QTest


def _elem(gyoker, nev: str):
    talalat = gyoker.findChild(QObject, nev)
    assert talalat is not None, f"{nev} nem található"
    return talalat


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 3.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    qt_app.processEvents()
    assert feltetel(), uzenet


def _kattint(ablak, elem, qt_app):
    assert elem.property("enabled") is True, f"{elem.objectName()} le van tiltva"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()} nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    for _ in range(10):
        qt_app.processEvents()


def _kozep_y(elem):
    return elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).y()


def _import_vezerlo(engine, tmp_path):
    vezerlo = engine.rootContext().contextProperty("importSourceController")
    assert vezerlo is not None, "importSourceController context property hiányzik"
    settings = QSettings(
        str(tmp_path / "import-settings.ini"), QSettings.Format.IniFormat
    )
    # A fő QML-próba forrásvezérlője külön példányban jön létre; a valódi
    # alkalmazással egyező beállítás-tárat ebben a tesztben a tmp alá tereljük.
    vezerlo._settings = settings
    return vezerlo, settings


def test_beallitasbol_kattintva_menti_es_importnal_felkinalja(
    qml_app, qt_app, tmp_path
):
    foablak, _app_vezerlo, engine = qml_app
    import_vezerlo, settings = _import_vezerlo(engine, tmp_path)
    celu_mappa = tmp_path / "sajat import cel"
    celu_mappa.mkdir()
    magassag_elteresek = (-5, 0, 5)

    foablak.resize(1280, 800)
    menu = _elem(foablak, "menuToolsOptions")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    _varj(
        qt_app,
        lambda: foablak.findChild(QObject, "optionsDialog") is not None
        and foablak.findChild(QObject, "optionsDialog").property("visible"),
        "a Beállítások ablaka nem nyílt meg",
    )
    options = _elem(foablak, "optionsDialog")
    eredeti_options_magassag = options.height()
    mezo = _elem(options, "optionsImportDestField")
    tallozo = _elem(options, "optionsImportDestBrowseButton")
    bezaro = _elem(options, "optionsCloseButton")

    ui_utolso_sor = _elem(options, "optionsSingleClickExitCheck")
    fajlok_elso_sor = _elem(options, "optionsAutoExcludeCheck")
    ui_fajlok_koz: float = _kozep_y(fajlok_elso_sor) - _kozep_y(ui_utolso_sor)
    assert abs(ui_fajlok_koz - 25) <= 3, (
        "a Kezelőfelület és a Fájlok első sora közti térköz eltér a "
        f"referencia 25 px-es értékétől: {ui_fajlok_koz:.1f} px"
    )
    files_divider = _elem(options, "optionsGeneralFilesDivider")
    files_utolso_sor = _elem(options, "optionsSkipRemoveConfirmCheck")
    files_divider_y = files_divider.mapToScene(QPointF(0, 0)).y()
    files_to_divider = files_divider_y - _kozep_y(files_utolso_sor)
    assert abs(files_to_divider - 13) <= 3, (
        "a Fájlok csoport elválasztója nem a referencia szerinti helyen van: "
        f"{files_to_divider:.1f} px az utolsó sor közepétől"
    )
    participation_first = _elem(options, "optionsUsageStatsCheck")
    participation_from_divider = _kozep_y(participation_first) - files_divider_y
    assert abs(participation_from_divider - 20) <= 3, (
        "a Részvétel csoport térköze eltér a referencia 20 px-es értékétől: "
        f"{participation_from_divider:.1f} px"
    )
    participation_divider = _elem(options, "optionsGeneralParticipationDivider")
    participation_divider_y = participation_divider.mapToScene(QPointF(0, 0)).y()
    privacy_link = _elem(options, "optionsPrivacyLink")
    privacy_gap = _kozep_y(privacy_link) - _kozep_y(participation_first)
    assert abs(privacy_gap - 27) <= 3, (
        "az Adatvédelem link és a Részvétel sora közti térköz eltér a "
        f"referencia 27 px-es értékétől: {privacy_gap:.1f} px"
    )
    privacy_to_divider = participation_divider_y - _kozep_y(privacy_link)
    assert abs(privacy_to_divider - 13) <= 3, (
        "a második elválasztó nem a referencia szerinti helyen van: "
        f"{privacy_to_divider:.1f} px az Adatvédelem link közepétől"
    )
    update_mode = _elem(options, "optionsUpdateModeCombo")
    update_from_divider = _kozep_y(update_mode) - participation_divider_y
    assert abs(update_from_divider - 23) <= 3, (
        "az Automatikus frissítések sora eltér a referencia 23 px-es "
        f"elválasztóközétől: {update_from_divider:.1f} px"
    )
    language = _elem(options, "optionsLanguageCombo")
    language_gap = _kozep_y(language) - _kozep_y(update_mode)
    assert abs(language_gap - 32) <= 3, (
        f"a Frissítések és Nyelv sor közti térköz {language_gap:.1f} px, "
        "a referencia 32 px"
    )
    destination_gap = _kozep_y(mezo) - _kozep_y(language)
    assert abs(destination_gap - 32) <= 3, (
        f"a Nyelv és Importcél sor közti térköz {destination_gap:.1f} px, "
        "a referencia 32 px"
    )

    for magassag_elteres in magassag_elteresek:
        foablak.resize(1280, 800 + magassag_elteres)
        options.setProperty("height", eredeti_options_magassag + magassag_elteres)
        qt_app.processEvents()
        assert mezo.property("enabled") is True, "az importcél mező le van tiltva"
        assert Path(str(mezo.property("text"))) == Path(
            import_vezerlo.defaultDestination
        )
        assert tallozo.property("enabled") is True
        assert mezo.isVisible() and tallozo.isVisible(), (
            "az importcél sora nem látszik a Beállítások ablakában"
        )
        mezokozepe = mezo.mapToScene(
            QPointF(mezo.width() / 2, mezo.height() / 2)
        )
        bezaro_kozepe = bezaro.mapToScene(
            QPointF(bezaro.width() / 2, bezaro.height() / 2)
        )
        assert 0 <= mezokozepe.y() < bezaro_kozepe.y(), (
            "az importcél sora a bezáró gomb alá szorult"
        )
        if magassag_elteres == 0:
            kep = options.grabWindow()
            assert not kep.isNull(), "az Általános fül képernyőképe üres"
            assert kep.save(str(tmp_path / "4450-options-after.png")), (
                "az Általános fül képernyőképe nem menthető"
            )

    valaszto = _elem(options, "optionsImportDestFolderDialog")
    aktualis = valaszto.property("currentFolder")
    assert Path(aktualis.toLocalFile()) == Path(import_vezerlo.defaultDestination)
    _kattint(options, tallozo, qt_app)
    _varj(
        qt_app,
        lambda: valaszto.property("visible") is True,
        "a Tallózás gomb nem nyitotta meg a mappaválasztót",
    )
    # Az offscreen natív mappaválasztó nem ad kattintható ablakot; a
    # FolderDialog accepted ágát a Qt Quick Dialogs bevett mintájával jelezzük.
    kivalasztott_url = QUrl.fromLocalFile(str(celu_mappa))
    valaszto.setProperty("selectedFolder", kivalasztott_url)
    assert valaszto.property("selectedFolder") == kivalasztott_url
    assert QMetaObject.invokeMethod(
        valaszto, "accepted", Qt.ConnectionType.DirectConnection
    )
    _varj(
        qt_app,
        lambda: Path(str(mezo.property("text"))) == celu_mappa.resolve(),
        "a Tallózásban választott mappa nem jelent meg a beállításban",
    )
    valaszto.setProperty("visible", False)
    qt_app.processEvents()
    settings.sync()
    assert Path(settings.value("import/defaultdestination")) == celu_mappa.resolve()

    QMetaObject.invokeMethod(options, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    _varj(
        qt_app,
        lambda: options.property("visible") is True,
        "a Beállítások ablaka nem nyílt meg újra",
    )
    assert Path(str(mezo.property("text"))) == celu_mappa.resolve()
    QMetaObject.invokeMethod(options, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()

    for magassag_elteres in magassag_elteresek:
        foablak.resize(1280, 800 + magassag_elteres)
        foablak.show()
        qt_app.processEvents()
        import_gomb = _elem(foablak, "toolbarImportButton")
        kattintasok = []
        import_gomb.clicked.connect(
            lambda *_args, rogzitett=kattintasok: rogzitett.append(True)
        )
        _kattint(foablak, import_gomb, qt_app)
        assert kattintasok, "az eszköztár importgombja nem kapta meg a kattintást"
        _varj(
            qt_app,
            lambda: foablak.findChild(QObject, "importSourceDialog") is not None,
            "az import párbeszéd nem épült fel",
        )
        import_ablak = _elem(foablak, "importSourceDialog")
        _varj(
            qt_app,
            lambda ablak=import_ablak: ablak.property("visible") is True,
            "az Importálás gomb nem nyitotta meg a párbeszédet",
        )
        import_ablak.setProperty(
            "height", import_ablak.height() + magassag_elteres
        )
        qt_app.processEvents()
        assert Path(str(import_ablak.property("destFolder"))) == celu_mappa.resolve(), (
            "az import nem a Beállításokban megadott célmappát ajánlja fel"
        )
        cel_szoveg = _elem(import_ablak, "importSourceDestPathText")
        assert Path(str(cel_szoveg.property("text"))) == celu_mappa.resolve()
        import_ablak.setProperty("visible", False)
        qt_app.processEvents()
