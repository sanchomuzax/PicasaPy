"""A Filmkészítő panel látható és kezelhető a főablakból (#4125)."""

from __future__ import annotations

import struct
import wave

from PySide6.QtCore import QEventLoop, QObject, QPoint, QTimer, Qt, QUrl
from PySide6.QtTest import QTest
from picasapy.lazy_cv2 import cv2
from picasapy.movie.mxf import read_mxf
from picasapy.movie.slideshow import _ffmpeg_exe


def _elem(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található a főablak objektumfájában"
    return objektum


def _darab(value):
    if hasattr(value, "property"):
        return value.property("length").toInt()
    return len(value or [])


def _kattintas(window, qt_app, item):
    """Valódi egérkattintás az elem pillanatnyi geometriájának közepére."""
    kozep = item.mapToScene(item.boundingRect().center())
    cel = item.window() or window
    QTest.mouseClick(
        cel,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()
    QTest.qWait(30)


def test_a_filmkeszito_vezerloi_es_kimenete_valodi_kattintassal_minden_magassagon(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    for name in ("captions", "cropfit", "removeLowResFaces"):
        controller.setMoviePreference(name, True)
        assert controller.moviePreference(name) is True
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    film_gomb = _elem(window, "trayMovieButton")
    eredeti_magassag = window.height()

    film_parbeszed = None
    try:
        for eltolás in (-5, 0, 5):
            window.resize(window.width(), eredeti_magassag + eltolás)
            qt_app.processEvents()
            _kattintas(window, qt_app, film_gomb)
            film_parbeszed = _elem(window, "movieDialog")
            assert film_parbeszed.property("visible") is True, (
                "a főablak film gombja nem nyitotta meg a panelt"
            )

            for nev in (
                "movieTabMotion",
                "movieTabSlide",
                "movieTabClips",
                "movieTransitionBox",
                "movieOverlapSlider",
                "movieAudioOptionBox",
                "movieHeightBox",
                "movieSlideText",
                "movieFontBox",
                "movieTextSizeBox",
                "movieTextStyleBox",
                "movieBoldBox",
                "movieItalicBox",
                "movieOutlineBox",
                "movieClipList",
            ):
                _elem(window, nev)

            atmenetek = list(
                _elem(window, "movieTransitionBox").property("model") or []
            )
            hangsavok = list(
                _elem(window, "movieAudioOptionBox").property("model") or []
            )
            assert len(atmenetek) == 22, (
                f"a képváltási lista {len(atmenetek)} elemű"
            )
            assert len(hangsavok) == 3, (
                f"a hangsáv-lista {len(hangsavok)} elemű"
            )

            film_parbeszed.close()
            film_parbeszed = None
            qt_app.processEvents()

        assert _ffmpeg_exe(), "az imageio-ffmpeg vagy a rendszer FFmpeg kell a hangsávhoz"
        _kattintas(window, qt_app, film_gomb)
        film_parbeszed = _elem(window, "movieDialog")
        assert _darab(film_parbeszed.property("movieClipSources")) == 2
        _kattintas(window, qt_app, _elem(window, "movieTabClips"))
        _elem(window, "movieClipList").setProperty("currentIndex", 1)
        _kattintas(window, qt_app, _elem(window, "movieDeleteClipButton"))
        assert _darab(film_parbeszed.property("movieClipSources")) == 1
        _kattintas(window, qt_app, _elem(window, "movieAddClipsButton"))
        assert _darab(film_parbeszed.property("movieClipSources")) == 2
        _kattintas(window, qt_app, _elem(window, "movieRecomputeButton"))
        assert _elem(window, "movieTabs").property("currentIndex") == 0
        film_parbeszed.setProperty("targetFile", QUrl.fromLocalFile(str(tmp_path / "film.mp4")).toString())
        film_parbeszed.setProperty("audioFile", QUrl.fromLocalFile(str(tmp_path / "hang.wav")).toString())
        film_parbeszed.setProperty("audioOption", 2)
        _elem(window, "movieHeightBox").setProperty("currentIndex", 0)
        _elem(window, "movieTransitionBox").setProperty("currentIndex", 4)
        _elem(window, "movieSeconds").setProperty("value", 10)
        _elem(window, "movieShowDates").setProperty("checked", True)
        _elem(window, "movieSmartOrder").setProperty("checked", True)

        hang = tmp_path / "hang.wav"
        with wave.open(str(hang), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(8000)
            wav.writeframes(b"".join(struct.pack("<h", 5000) for _ in range(8000)))

        _kattintas(window, qt_app, _elem(window, "movieTabSlide"))
        _elem(window, "movieSlideText").setProperty("text", "4125")
        _kattintas(window, qt_app, _elem(window, "movieInsertSlideButton"))
        title_dialog = _elem(window, "movieTitleDialog")
        assert title_dialog.property("visible") is True, (
            "a szöveges dia gombja nem nyitotta meg a címdia-szerkesztőt"
        )
        _kattintas(window, qt_app, _elem(window, "titledialog/add"))
        assert title_dialog.property("visible") is False
        assert _elem(window, "movieSlideList").property("count") == 1
        _kattintas(window, qt_app, _elem(window, "movieTabMotion"))

        hurok = QEventLoop()
        eredmeny = []
        hiba = []
        idozito = QTimer(hurok)
        idozito.setSingleShot(True)
        idozito.timeout.connect(hurok.quit)
        controller.movieFinished.connect(lambda *args: (eredmeny.append(args), hurok.quit()))
        controller.movieFailed.connect(lambda message: (hiba.append(message), hurok.quit()))
        idozito.start(45000)
        _kattintas(window, qt_app, _elem(window, "movieCreateButton"))
        hurok.exec()
        idozito.stop()
        assert not hiba, f"a valódi filmkimenet hibát jelzett: {hiba}"
        assert eredmeny, "a film elkészítése nem küldött kész jelzést 45 másodpercen belül"

        cel = tmp_path / "film.mp4"
        assert cel.is_file() and cel.stat().st_size > 0
        olvaso = cv2.VideoCapture(str(cel))
        ok, kep = olvaso.read()
        olvaso.release()
        assert ok and kep.shape[:2] == (240, 320)
        projekt = read_mxf(cel.with_suffix(".mxf"))
        assert projekt.curresolution == 0
        assert projekt.musicfile == str(hang)
        assert projekt.audiooption == 2
        assert projekt.defaulttrans.transition == 4
        assert projekt.showcaption and projekt.showdates
        assert projekt.cropfit == 1 and projekt.removelowresfaces
        assert projekt.ordering == 0
        assert len(projekt.atmenetek) == 3
        assert projekt.atmenetek[-1].forras.tipus == 2
        assert projekt.atmenetek[-1].forras.text == "4125"
    finally:
        if film_parbeszed is not None:
            film_parbeszed.close()
            qt_app.processEvents()
        for nev in ("movieProgressDialog", "createResultDialog"):
            dialog = window.findChild(QObject, nev)
            if dialog is not None:
                dialog.close()
        qt_app.processEvents()
