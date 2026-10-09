"""A filmkészítő előnézete átmenetet, szöveges diát és hangerőt mutat (#4617)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest


def _elem(gyoker, nev):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a főablak objektumfájában"
    return elem


def _varj(qt_app, feltetel, masodperc=3.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _kattint(window, qt_app, elem, x_arany=0.5):
    assert elem.property("visible"), f"{elem.objectName()} nem látható"
    cel = elem.window() or window
    pont = elem.mapToScene(
        QPointF(elem.property("width") * x_arany, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(cel, Qt.MouseButton.LeftButton, pos=pont)
    qt_app.processEvents()


def _film_megnyit(window, qt_app, magassag):
    window.resize(1280, magassag)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    _kattint(window, qt_app, _elem(window, "trayMovieButton"))
    film = _elem(window, "movieDialog")
    assert _varj(qt_app, lambda: film.property("visible")), (
        "a filmkészítő gomb nem nyitotta meg a párbeszédet"
    )
    return film


def _szines_kep(ut, szin):
    kep = QImage(320, 240, QImage.Format.Format_RGB32)
    kep.fill(QColor(szin))
    assert kep.save(str(ut)), f"nem sikerült elkészíteni a tesztképet: {ut}"
    return QUrl.fromLocalFile(str(ut)).toString()


def _hozzadott_szoveges_dia(window, qt_app, szoveg):
    _kattint(window, qt_app, _elem(window, "movieTabSlide"))
    _kattint(window, qt_app, _elem(window, "movieInsertSlideButton"))
    dialog = _elem(window, "movieTitleDialog")
    assert _varj(qt_app, lambda: dialog.property("visible"))
    _elem(window, "titledialog/captiontext").setProperty("text", szoveg)
    qt_app.processEvents()
    _kattint(window, qt_app, _elem(window, "titledialog/add"))
    assert _varj(qt_app, lambda: not dialog.property("visible"))


def test_kattintott_elonezet_atmenetet_es_szoveges_diakepet_mutat(
    qml_app, qt_app, tmp_path
):
    window, _controller, _engine = qml_app
    eredeti_magassag = window.height()
    try:
        for magassag_elteres in (-5, 0, 5):
            film = _film_megnyit(window, qt_app, 800 + magassag_elteres)
            try:
                forrasok = [
                    _szines_kep(tmp_path / "piros.png", "#ff0000"),
                    _szines_kep(tmp_path / "kek.png", "#0000ff"),
                ]
                film.setProperty("movieClipSources", forrasok)
                film.setProperty("previewSource", forrasok[0])
                _elem(window, "movieSeconds").setProperty("value", 20)
                _elem(window, "movieOverlapSlider").setProperty("value", 0.4)
                _hozzadott_szoveges_dia(window, qt_app, "4617 preview text")

                _kattint(window, qt_app, _elem(window, "moviePreviewButton"))
                transition = _elem(window, "moviePreviewTransition")
                assert _varj(
                    qt_app,
                    lambda: 0.35
                    <= float(
                        _elem(window, "movieDialog").property(
                            "previewTransitionProgress"
                        )
                    )
                    <= 0.65,
                    masodperc=6.0,
                ), "a kattintott előnézet nem rajzolt átmeneti képkockát"

                viewport = _elem(window, "moviePreviewViewport")
                kep = window.grabWindow()
                assert not kep.isNull(), "az előnézeti ablak képe nem készült el"
                kep.save(str(tmp_path / f"film-atmenet-{magassag_elteres}.png"))
                pont = viewport.mapToScene(
                    QPointF(
                        viewport.property("width") / 2,
                        viewport.property("height") / 2,
                    )
                )
                pixel = kep.pixelColor(
                    round(pont.x() * kep.width() / window.width()),
                    round(pont.y() * kep.height() / window.height()),
                )
                assert (
                    35 < pixel.red() < 220 and 35 < pixel.blue() < 220
                ), (
                    "az előnézet átmeneti képpontja nem keverte a piros és kék képet: "
                    f"RGB=({pixel.red()}, {pixel.green()}, {pixel.blue()})"
                )
                assert transition.property("running") is True
                assert _varj(
                    qt_app,
                    lambda film=film: film.property("previewIndex") == 2,
                    masodperc=3.0,
                ), "az előnézet nem léptetett tovább a szöveges diára"
                assert _varj(
                    qt_app,
                    lambda transition=transition: not transition.property("running"),
                    masodperc=2.0,
                ), "a szöveges diára váltó átmenet nem fejeződött be"
                szoveges_kep = window.grabWindow()
                assert not szoveges_kep.isNull()
                szoveges_kep.save(str(tmp_path / f"film-szoveg-{magassag_elteres}.png"))
                szoveges_dia = _elem(window, "moviePreviewIncomingFrame")
                assert szoveges_dia.property("isTextSlide") is True
                assert szoveges_dia.property("displayText") == "4617 preview text"
                assert _elem(window, "moviePreviewImage").property("visible") is False
                canvas = _elem(window, "moviePreviewIncomingFrame/canvas")
                sarok = canvas.mapToScene(QPointF(4, 4))
                pixel = szoveges_kep.pixelColor(
                    round(sarok.x() * szoveges_kep.width() / window.width()),
                    round(sarok.y() * szoveges_kep.height() / window.height()),
                )
                assert pixel.red() < 8 and pixel.green() < 8 and pixel.blue() < 8, (
                    "a szöveges dia háttérszíne nem jelent meg a szövegmentes sarokban: "
                    f"RGB=({pixel.red()}, {pixel.green()}, {pixel.blue()})"
                )
            finally:
                film.close()
                qt_app.processEvents()
    finally:
        window.resize(window.width(), eredeti_magassag)
        qt_app.processEvents()


def test_kattintott_hangerocsuszka_a_hangkimenet_hangerejet_is_allitja(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    hangfajl = tmp_path / "hang.wav"
    eredeti_magassag = window.height()
    for magassag_elteres, x_arany in ((-5, 0.6), (0, 0.75), (5, 0.9)):
        film = _film_megnyit(window, qt_app, 800 + magassag_elteres)
        try:
            film.setProperty("audioFile", QUrl.fromLocalFile(str(hangfajl)).toString())
            qt_app.processEvents()
            assert window.findChild(QObject, "moviePreviewAudioOutput") is None, (
                "az előnézet álló helyzetben, hangkimenet nélkül is betöltött"
            )
            elozo = float(film.property("previewAudioVolume"))
            assert elozo == pytest.approx(controller.movieVolume / 1000)

            _kattint(
                window,
                qt_app,
                _elem(window, "video_control_bar2/volumeslider"),
                x_arany=x_arany,
            )

            uj_hangerő = float(film.property("previewAudioVolume"))
            assert uj_hangerő > elozo, "a kattintott hangerőcsúszka nem változtatta az értéket"
            assert controller.movieVolume == pytest.approx(uj_hangerő * 1000, abs=1)
        finally:
            film.close()
            qt_app.processEvents()
    window.resize(window.width(), eredeti_magassag)
    qt_app.processEvents()
    qml_forras = (
        Path(__file__).parents[3]
        / "src/picasapy/app/qml/PicasaPy/MoviePreviewFrame.qml"
    ).read_text(encoding="utf-8")
    hang_forras = (
        Path(__file__).parents[3]
        / "src/picasapy/app/qml/PicasaPy/MoviePreviewMusicPlayer.qml"
    ).read_text(encoding="utf-8")
    assert 'font.family: String(frame.slideData.font || "DejaVu Sans")' in qml_forras
    assert "Number(frame.slideData.size || 16) * parent.height" in qml_forras
    assert "onOutputVolumeChanged: if (item) item.volume = outputVolume" in (
        Path(__file__).parents[3]
        / "src/picasapy/app/qml/PicasaPy/CreateDialogs.qml"
    ).read_text(encoding="utf-8")
    assert "volume: root.volume" in hang_forras


# rontás-kontroll: javítás előtt a moviePreviewTransition hiányzott → 1 failed
