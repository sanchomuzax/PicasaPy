"""A film újraexportálásakor választható a csere vagy az új fájl (#4612)."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtTest import QTest

from picasapy.movie.mxf import MxfAtmenet, MxfForras, MxfProjekt, write_mxf
from picasapy.movie.slideshow import MovieReport


def _elem(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található a főablakban"
    return objektum


def _varj(qt_app, feltetel, masodperc=3.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _kattintas(window, qt_app, elem):
    """Az elem aktuális, ablakbeli közepére kattint."""
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        elem.window() or window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _filmet_nyit(window, qt_app):
    _kattintas(window, qt_app, _elem(window, "trayMovieButton"))
    film = _elem(window, "movieDialog")
    assert _varj(qt_app, lambda: film.property("visible")), (
        "a filmkészítő gomb nem nyitotta meg a párbeszédet"
    )
    return film


def test_ujraexportnal_kattintassal_valaszthato_a_csere_az_uj_es_a_megse(
    qml_app, qt_app, tmp_path, monkeypatch
):
    window, controller, _engine = qml_app
    kimeneti_mappa = tmp_path / "filmek"
    controller._get_settings().setValue("movie/outputDir", str(kimeneti_mappa))

    elozo = kimeneti_mappa / "korabbi.mp4"
    elozo.parent.mkdir(parents=True)
    elozo.write_bytes(b"korabbi film")
    forrasok = [Path(controller.photos.filePathAt(sor)) for sor in (0, 1)]
    write_mxf(
        elozo.with_suffix(".mxf"),
        MxfProjekt(
            defaulttrans=MxfAtmenet(advanceinterval=3.0),
            atmenetek=tuple(
                MxfAtmenet(
                    forras=MxfForras(index=index, filename=str(forras))
                )
                for index, forras in enumerate(forrasok)
            ),
        ),
    )

    exportok = []

    def export_mock(forrasok, cel, _beallitasok, progress=None):
        ut = Path(cel)
        ut.parent.mkdir(parents=True, exist_ok=True)
        ut.write_bytes(b"uj film")
        exportok.append(ut)
        return MovieReport(
            target=ut,
            used=tuple(Path(forras) for forras in forrasok),
            skipped=(),
            reasons=(),
            frames=1,
        )

    monkeypatch.setattr("picasapy.app.create_controller.export_movie", export_mock)
    assert callable(getattr(window, "openSavedMovie", None)), (
        "a főablak nem teszi hívhatóvá a projektnyitó útvonalat"
    )
    window.openSavedMovie(str(elozo))
    qt_app.processEvents()
    film = _elem(window, "movieDialog")
    assert film.property("previousMoviePath") == str(elozo), (
        "a megnyitott filmfájl útvonala nem jutott el a filmkészítőhöz"
    )
    eredmeny = _elem(window, "createResultDialog")

    alapmagassag = window.height()
    muveletek = (
        (-5, "movieReplaceExistingButton", elozo),
        (0, "movieCreateNewButton", None),
        (5, "movieReplaceCancelButton", "cancel"),
    )
    try:
        for eltolás, gombnev, vart_cel in muveletek:
            window.resize(window.width(), alapmagassag + eltolás)
            qt_app.processEvents()
            if not film.property("visible"):
                film = _filmet_nyit(window, qt_app)
            _kattintas(window, qt_app, _elem(window, "movieCreateButton"))

            valaszto = _elem(window, "movieReplaceDialog")
            assert _varj(
                qt_app, lambda valaszto=valaszto: valaszto.property("visible")
            ), (
                "újraexportáláskor nem jelent meg a meglévő filmről szóló kérdés"
            )

            elotte = len(exportok)
            _kattintas(window, qt_app, _elem(window, gombnev))
            if vart_cel == "cancel":
                assert _varj(
                    qt_app, lambda valaszto=valaszto: not valaszto.property("visible")
                ), (
                    "a Mégse nem zárta be a választó párbeszédet"
                )
                assert film.property("visible") is True, (
                    "a Mégse bezárta a film szerkesztését"
                )
                assert len(exportok) == elotte, "a Mégse mégis elindította az exportot"
                film.close()
                qt_app.processEvents()
                continue

            assert _varj(
                qt_app, lambda elotte=elotte: len(exportok) == elotte + 1
            ), (
                f"a(z) {gombnev} nem indította el az exportot"
            )
            if vart_cel:
                assert exportok[-1] == vart_cel, (
                    "a csere nem a korábbi film fájljára exportált"
                )
                assert vart_cel.read_bytes() == b"uj film", (
                    "a csere nem írta felül a korábbi filmfájlt"
                )
            else:
                assert exportok[-1] != elozo, (
                    "az új film a korábbi fájl helyett arra exportált"
                )
                assert exportok[-1].is_file(), "az új filmfájl nem jött létre"
                assert elozo.is_file(), "az új létrehozása eltüntette a korábbi filmet"
            assert _varj(qt_app, lambda: eredmeny.property("visible")), (
                "az export befejezése nem adott eredményjelzést"
            )
            eredmeny.close()
            qt_app.processEvents()
    finally:
        film = window.findChild(QObject, "movieDialog")
        if film is not None and film.property("visible"):
            film.close()
        for nev in (
            "movieReplaceDialog",
            "movieProgressDialog",
            "createResultDialog",
        ):
            dialog = window.findChild(QObject, nev)
            if dialog is not None and dialog.property("visible"):
                dialog.close()
        qt_app.processEvents()
