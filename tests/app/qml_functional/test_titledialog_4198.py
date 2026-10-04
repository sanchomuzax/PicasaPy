"""A Filmkészítő címdia-párbeszéde a főablaktól a videókimenetig (#4198)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
from PySide6.QtCore import QElapsedTimer, QEventLoop, QObject, QPoint, QTimer, Qt, QUrl
from PySide6.QtTest import QTest
from picasapy.lazy_cv2 import cv2
from picasapy.movie.mxf import read_mxf
from picasapy.movie.slideshow import _ffmpeg_exe


def _elem(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található a főablak objektumfájában"
    return objektum


def _kattintas(window, qt_app, item):
    """Valódi kattintás az elem pillanatnyi geometriájának közepére."""
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        item.window() or window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _var(qt_app, feltetel, lejarat_ms=3000):
    """Határidős ciklus időzített Qt/QML-állapotokhoz."""
    ora = QElapsedTimer()
    ora.start()
    while ora.elapsed() < lejarat_ms:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _close_open_create_dialogs(window, qt_app):
    for nev in (
        "movieTitleDialog",
        "movieRecomputeConfirmDialog",
        "movieDialog",
    ):
        dialog = window.findChild(QObject, nev)
        if dialog is not None:
            dialog.close()
    qt_app.processEvents()


def _filmkezito_megnyit(window, qt_app):
    _kattintas(window, qt_app, _elem(window, "trayMovieButton"))
    film = _elem(window, "movieDialog")
    assert _var(qt_app, lambda: film.property("visible")), (
        "a főablak Filmkészítő gombja nem nyitotta meg a párbeszédet"
    )
    _kattintas(window, qt_app, _elem(window, "movieTabSlide"))
    return film


def _cimdiaszerkeszto_megnyit(window, qt_app):
    _kattintas(window, qt_app, _elem(window, "movieInsertSlideButton"))
    dialog = window.findChild(QObject, "movieTitleDialog")
    if dialog is None:
        # A rontás-kontrollnál a hiányzó párbeszédet is zárjuk le, hogy a
        # Qt ne tartson nyitott filmablakot az alkalmazás lebontásakor.
        film = window.findChild(QObject, "movieDialog")
        if film is not None:
            film.close()
            qt_app.processEvents()
        assert dialog is not None, "movieTitleDialog nem található a főablakban"
    assert _var(qt_app, lambda: dialog.property("visible")), (
        "a szöveges dia gombja nem nyitotta meg a címdia-szerkesztőt"
    )
    return dialog


def test_cimdia_parbeszed_kattintastol_valodi_videokimenetig(
    qml_app, qt_app, tmp_path, request
):
    window, controller, _engine = qml_app
    request.addfinalizer(lambda: _close_open_create_dialogs(window, qt_app))
    title_source = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/qml/PicasaPy/MovieTitleDialog.qml"
    ).read_text(encoding="utf-8")
    assert "font.family: fontFamilyBox.currentText" in title_source
    assert "font.pixelSize: titleDialog.sizeValues[sizeList.currentIndex]" in title_source
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    # A Qt-modell rekordja fagyasztott; a teszt a kijelölt kép tesztadatát
    # cseréli, és nem indít aszinkron IPTC-írást.
    controller.photos._photos = (
        replace(controller.photos._photos[0], caption="Caption 4198"),
        *controller.photos._photos[1:],
    )
    assert controller.photos.captionAt(0) == "Caption 4198"
    qt_app.processEvents()

    eredeti_magassag = window.height()
    for eltolás in (-5, 0, 5):
        window.resize(window.width(), eredeti_magassag + eltolás)
        qt_app.processEvents()
        film = _filmkezito_megnyit(window, qt_app)
        for nev in (
            "movieSlideText",
            "movieFontBox",
            "movieTextSizeBox",
            "movieTextStyleBox",
            "movieBoldBox",
            "movieItalicBox",
            "movieOutlineBox",
        ):
            _elem(window, nev)
        dialog = _cimdiaszerkeszto_megnyit(window, qt_app)
        for nev in (
            "titledialog/add",
            "titledialog/cancel",
            "titledialog/captionchk",
            "titledialog/previewimage",
            "titledialog/previewtext",
            "titledialog/sizelist",
            "titledialog/stylelist",
            "titledialog/captiontext",
        ):
            _elem(window, nev)
        if eltolás == 0:
            felvetel = tmp_path / "movie-title-dialog.png"
            assert window.grabWindow().save(str(felvetel)), (
                "a címdia-párbeszéd képernyőképe nem menthető"
            )
        assert _elem(window, "titledialog/captionchk").property("enabled")
        assert _elem(window, "titledialog/previewtext").property("text")
        _kattintas(window, qt_app, _elem(window, "titledialog/cancel"))
        assert _var(qt_app, lambda dialog=dialog: not dialog.property("visible")), (
            "a Cancel nem zárta be a címdia-szerkesztőt"
        )
        assert _elem(window, "movieSlideList").property("count") == 0, (
            "a Cancel mégis létrehozott egy szöveges diát"
        )
        film.close()
        qt_app.processEvents()

    assert _ffmpeg_exe(), "a valódi videókimenethez FFmpeg szükséges"
    window.resize(window.width(), eredeti_magassag)
    qt_app.processEvents()
    film = _filmkezito_megnyit(window, qt_app)
    dialog = _cimdiaszerkeszto_megnyit(window, qt_app)
    szoveg = _elem(window, "titledialog/captiontext")
    szoveg.setProperty("text", "A cím a képfeliratból jön")
    _elem(window, "titledialog/sizelist").setProperty("currentIndex", 7)
    _elem(window, "titledialog/stylelist").setProperty("currentIndex", 3)
    font_name = _elem(window, "titledialog/fontfamily").property("currentText")
    _kattintas(window, qt_app, _elem(window, "titledialog/captionchk"))
    assert _elem(window, "titledialog/previewtext").property("text") == "Caption 4198"

    film.setProperty("backgroundColor", "#16a8d0")
    _kattintas(window, qt_app, _elem(window, "titledialog/add"))
    assert _var(qt_app, lambda: not dialog.property("visible")), (
        "az Add nem zárta be a címdia-szerkesztőt"
    )
    assert _elem(window, "movieSlideList").property("count") == 1, (
        "az Add kattintása nem hozott létre címdiát"
    )
    assert _elem(window, "movieSlideList").property("currentIndex") == 0
    movie_slide_text = _elem(window, "movieSlideText")
    assert movie_slide_text.property("text") == "Caption 4198", (
        "a beépített szerkesztő nem töltötte be a kijelölt címdia szövegét"
    )

    _kattintas(window, qt_app, _elem(window, "movieTabClips"))
    recompute = _elem(window, "movieRecomputeButton")
    _kattintas(window, qt_app, recompute)
    confirm = window.findChild(QObject, "movieRecomputeConfirmDialog")
    assert confirm is not None, "hiányzik az újraszámolás megerősítő párbeszéde"
    assert _var(qt_app, lambda: confirm.property("visible")), (
        "az újraszámolás nem figyelmeztetett a kézzel felvett szöveges diára"
    )
    _kattintas(window, qt_app, _elem(window, "movieRecomputeConfirmCancelButton"))
    assert _elem(window, "movieSlideList").property("count") == 1, (
        "a megszakított újraszámolás elvesztette a kézzel felvett diát"
    )
    _kattintas(window, qt_app, recompute)
    assert _var(qt_app, lambda: confirm.property("visible")), (
        "a második újraszámolás előtt nem jelent meg újra a figyelmeztetés"
    )
    _kattintas(window, qt_app, _elem(window, "movieRecomputeConfirmYesButton"))
    assert _elem(window, "movieSlideList").property("count") == 0, (
        "az elfogadott újraszámolás nem dobta el a kézzel felvett diát"
    )
    assert _elem(window, "movieTabs").property("currentIndex") == 0

    _kattintas(window, qt_app, _elem(window, "movieTabSlide"))
    dialog = _cimdiaszerkeszto_megnyit(window, qt_app)
    _elem(window, "titledialog/captiontext").setProperty(
        "text", "A cím a képfeliratból jön"
    )
    _elem(window, "titledialog/sizelist").setProperty("currentIndex", 7)
    _elem(window, "titledialog/stylelist").setProperty("currentIndex", 3)
    font_name = _elem(window, "titledialog/fontfamily").property("currentText")
    _kattintas(window, qt_app, _elem(window, "titledialog/captionchk"))
    assert _elem(window, "titledialog/previewtext").property("text") == "Caption 4198"
    film.setProperty("backgroundColor", "#16a8d0")
    _kattintas(window, qt_app, _elem(window, "titledialog/add"))
    assert _var(qt_app, lambda: not dialog.property("visible"))
    assert _elem(window, "movieSlideList").property("count") == 1
    assert movie_slide_text.property("text") == "Caption 4198"
    movie_slide_text.setProperty("text", "Edited after title dialog")

    target = tmp_path / "titledialog-4198.mp4"
    film.setProperty("targetFile", QUrl.fromLocalFile(str(target)).toString())
    _elem(window, "movieHeightBox").setProperty("currentIndex", 0)
    _kattintas(window, qt_app, _elem(window, "movieTabMotion"))
    _elem(window, "movieSeconds").setProperty("value", 10)
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
    assert not hiba, f"a videókimenet hibát jelzett: {hiba}"
    assert eredmeny, "a videó nem készült el 45 másodpercen belül"
    assert target.is_file() and target.stat().st_size > 0

    projekt = read_mxf(target.with_suffix(".mxf"))
    cimdia = projekt.atmenetek[-1].forras
    assert cimdia.tipus == 2
    assert cimdia.text == "Edited after title dialog"
    assert cimdia.szovegparam.fontname == font_name
    assert cimdia.szovegparam.size == 22
    assert cimdia.szovegparam.styleid == 3

    video = cv2.VideoCapture(str(target))
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_count - 1))
    ok, frame = video.read()
    video.release()
    assert ok and (width, height) == (320, 240)
    # A klasszikus képfelirat alul középen áll; a bal felső, szöveg nélküli
    # rész kitöltőszíne igazolja, hogy a címdia a tényleges videóba is bekerült.
    folt = np.median(frame[8:20, 8:20].reshape(-1, 3), axis=0)
    vart_bgr = np.array([208, 168, 22])
    assert np.max(np.abs(folt - vart_bgr)) <= 12, (
        f"a videó címdia-képkockájának háttérszíne hibás: {folt}"
    )
# Rontás-kontroll: a korábbi állapotban hiányzó `movieSlideText` mező miatt piros.
