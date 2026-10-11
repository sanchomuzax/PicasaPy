"""A film szöveges dia neve és infósora valódi felületi kattintással (#4402)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtTest import QTest


def _elem(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található a főablak objektumfájában"
    return objektum


def _kattintas(window, qt_app, item):
    """Kattintás az elem aktuális, ablakhoz viszonyított közepére."""
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _lista_sor(lista, index):
    """A ListView éppen kirajzolt delegáltja a vizuális fából."""
    nev = f"movieSlideDelegate{index}" if lista.objectName() == "movieSlideList" else (
        f"movieClipDelegate{index}"
    )
    sor = next(
        (
            gyerek
            for gyerek in lista.property("contentItem").childItems()
            if gyerek.objectName() == nev
        ),
        None,
    )
    assert sor is not None, f"{nev} nem rajzolódott ki a listában"
    return sor


def _varj(qt_app, feltetel, lejarat_ms=3000):
    """A QML-állapotot határidős, eseményfeldolgozó ciklusban várja."""
    from PySide6.QtCore import QElapsedTimer

    ora = QElapsedTimer()
    ora.start()
    while ora.elapsed() < lejarat_ms:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _film_megnyit(window, qt_app):
    _kattintas(window, qt_app, _elem(window, "trayMovieButton"))
    film = _elem(window, "movieDialog")
    assert _varj(qt_app, lambda: film.property("visible")), (
        "a Filmkészítő gomb nem nyitotta meg a párbeszédet"
    )
    return film


def _uj_szoveges_dia(window, qt_app):
    _kattintas(window, qt_app, _elem(window, "movieTabSlide"))
    _kattintas(window, qt_app, _elem(window, "movieInsertSlideButton"))
    dialog = _elem(window, "movieTitleDialog")
    assert _varj(qt_app, lambda: dialog.property("visible")), (
        "az Insert Text Slide gomb nem nyitotta meg a szerkesztőt"
    )
    _elem(window, "titledialog/captiontext").setProperty("text", "4402 custom text")
    _kattintas(window, qt_app, _elem(window, "titledialog/add"))
    assert _varj(qt_app, lambda: not dialog.property("visible")), (
        "az Add gomb nem zárta be a címdia-szerkesztőt"
    )


def test_a_szoveges_dia_a_filmcsikon_es_a_listaban_is_text_slide_nevu(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    eredeti_magassag = window.height()

    for eltolás in (-5, 0, 5):
        window.resize(window.width(), eredeti_magassag + eltolás)
        qt_app.processEvents()
        film = _film_megnyit(window, qt_app)
        _uj_szoveges_dia(window, qt_app)

        dia_lista = _elem(window, "movieSlideList")
        assert int(dia_lista.property("count")) == 1
        dia_sor = _lista_sor(dia_lista, 0)
        assert dia_sor.property("text") == "Text Slide", (
            "a lista a dia tartalmát mutatja a Text Slide név helyett"
        )
        _kattintas(window, qt_app, dia_sor)

        _kattintas(window, qt_app, _elem(window, "movieTabClips"))
        filmcsik = _elem(window, "movieClipList")
        assert int(filmcsik.property("count")) == 3, (
            "a filmcsík nem tartalmazza a két fotót és az új szöveges diát"
        )
        dia_filmcsik_sor = _lista_sor(filmcsik, 2)
        assert dia_filmcsik_sor.property("text") == "Text Slide"
        _kattintas(window, qt_app, dia_filmcsik_sor)
        assert int(_elem(window, "movieSlideList").property("currentIndex")) == 0

        film.close()
        qt_app.processEvents()


def test_az_infotext_fenykepeken_es_szoveges_diakon_is_nevet_meretet_es_sorszamot_mutat(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    eredeti_magassag = window.height()

    for eltolás in (-5, 0, 5):
        window.resize(window.width(), eredeti_magassag + eltolás)
        qt_app.processEvents()
        film = _film_megnyit(window, qt_app)
        _kattintas(window, qt_app, _elem(window, "movieTabClips"))

        filmcsik = _elem(window, "movieClipList")
        filmcsik.setProperty("contentY", 0)
        qt_app.processEvents()
        _kattintas(window, qt_app, _lista_sor(filmcsik, 0))
        infotext = window.findChild(QObject, "makemoviepanel/infotext")
        assert infotext is not None, "hiányzik a makemoviepanel/infotext sor"
        kep = _elem(window, "moviePreviewTransitionImage")
        assert _varj(
            qt_app,
            lambda kep=kep: int(kep.property("sourceSize").width()) > 0
            and int(kep.property("sourceSize").height()) > 0,
        ), "a kijelölt fotó képpontmérete nem töltődött be"

        nev = Path(controller.photos.filePathAt(0)).name
        szelesseg = controller.photos.pixelWidthAt(0)
        magassag = controller.photos.pixelHeightAt(0)
        foto_sor = infotext.property("text")
        assert f"{nev}     {szelesseg}x{magassag}" in foto_sor, (
            f"a fotó infósora nem tartalmazza a nevét és méretét: {foto_sor!r}"
        )
        assert "(1 of 2)" in foto_sor, (
            f"a fotó infósora nem mutatja a film szerinti sorszámot: {foto_sor!r}"
        )

        _uj_szoveges_dia(window, qt_app)
        filmcsik = _elem(window, "movieClipList")
        assert int(filmcsik.property("count")) == 3
        _kattintas(window, qt_app, _elem(window, "movieTabClips"))
        filmcsik.setProperty("contentY", 0)
        qt_app.processEvents()
        _kattintas(window, qt_app, _lista_sor(filmcsik, 0))
        assert "(1 of 3)" in infotext.property("text"), (
            "a fotó sorszáma nem számolja bele a szöveges diát a filmbe"
        )
        filmcsik.setProperty(
            "contentY",
            max(
                0,
                float(filmcsik.property("contentHeight"))
                - float(filmcsik.property("height")),
            ),
        )
        qt_app.processEvents()
        _kattintas(window, qt_app, _lista_sor(filmcsik, 2))
        infotext = _elem(window, "makemoviepanel/infotext")
        movie_size = list(_elem(window, "movieHeightBox").property("model"))[
            int(_elem(window, "movieHeightBox").property("currentIndex"))
        ]
        meret = str(movie_size).split()[0]
        assert f"Text Slide     {meret} pixels" in infotext.property("text"), (
            "a szöveges dia infósora nem a dia nevét és filmképméretét mutatja: "
            f"{infotext.property('text')!r}"
        )
        assert "(3 of 3)" in infotext.property("text"), (
            "a szöveges dia infósora nem mutatja a film szerinti sorszámát: "
            f"{infotext.property('text')!r}"
        )

        film.close()
        qt_app.processEvents()
