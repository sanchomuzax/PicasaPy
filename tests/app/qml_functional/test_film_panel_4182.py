"""A Filmkészítő megmaradt vezérlői működnek a főablakból (#4182)."""

from __future__ import annotations

import os
import time

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

_KEEP_ALIVE: list[QObject] = []


def _elem(gyoker, nev):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a főablak objektumfájában"
    return elem


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _darab(qml_lista) -> int:
    if isinstance(qml_lista, list):
        return len(qml_lista)
    return qml_lista.property("length").toInt()


def _gorgess_elemhez(scroll, elem, qt_app) -> None:
    """A görgethető nézetben az elem aktuális geometriájához igazít."""
    flickable = scroll.property("contentItem")
    lathato_teteje = scroll.mapToScene(QPointF(0, 0)).y()
    lathato_alja = scroll.mapToScene(
        QPointF(scroll.property("width"), scroll.property("height"))
    ).y()
    elem_teteje = elem.mapToScene(QPointF(0, 0)).y()
    elem_alja = elem.mapToScene(
        QPointF(0, elem.property("height"))
    ).y()
    gorgetes = flickable.property("contentY")
    if elem_alja > lathato_alja + 3:
        max_gorgetes = max(
            0,
            scroll.property("contentHeight") - flickable.property("height"),
        )
        flickable.setProperty(
            "contentY", min(max_gorgetes, gorgetes + elem_alja - lathato_alja + 3)
        )
    elif elem_teteje < lathato_teteje - 3:
        flickable.setProperty(
            "contentY", max(0, gorgetes - (lathato_teteje - elem_teteje + 3))
        )
    qt_app.processEvents()


def _teljesen_latszik(a_nezoterben, elem, *, megnevezes: str) -> None:
    """A vezérlő teljes geometriája a látható nézőtéren belül van-e."""
    nezo_teteje = a_nezoterben.mapToScene(QPointF(0, 0))
    nezo_alja = a_nezoterben.mapToScene(
        QPointF(a_nezoterben.property("width"), a_nezoterben.property("height"))
    )
    elem_teteje = elem.mapToScene(QPointF(0, 0))
    elem_alja = elem.mapToScene(
        QPointF(elem.property("width"), elem.property("height"))
    )
    assert (
        elem_teteje.x() >= nezo_teteje.x() - 3
        and elem_teteje.y() >= nezo_teteje.y() - 3
        and elem_alja.x() <= nezo_alja.x() + 3
        and elem_alja.y() <= nezo_alja.y() + 3
    ), (
        f"{megnevezes} nincs teljesen a nézőtéren belül: "
        f"elem=({elem_teteje.x():.1f}, {elem_teteje.y():.1f}, "
        f"{elem_alja.x():.1f}, {elem_alja.y():.1f}), "
        f"nézőtér=({nezo_teteje.x():.1f}, {nezo_teteje.y():.1f}, "
        f"{nezo_alja.x():.1f}, {nezo_alja.y():.1f})"
    )


def _kep_szin(kep, window, pont: QPointF):
    """A jelenlegi QQuickWindow-geometriából számított képpontszín."""
    x = round(pont.x() * kep.width() / window.width())
    y = round(pont.y() * kep.height() / window.height())
    return kep.pixelColor(x, y)


def _kattints(window, qt_app, elem: QObject) -> QPoint:
    assert elem.property("visible"), f"{elem.objectName()} nem látható"
    cel = elem.window() or window
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(cel, Qt.MouseButton.LeftButton, pos=pont)
    qt_app.processEvents()
    return pont


def _dia_felvetel(window, qt_app, szoveg=None):
    """Szöveges dia felvétele a címdia-párbeszéden át (#4198, 2.10)."""
    _kattints(window, qt_app, _elem(window, "movieInsertSlideButton"))
    dialog = _elem(window, "movieTitleDialog")
    assert _varj(qt_app, lambda: dialog.property("visible"))
    if szoveg is not None:
        _elem(window, "titledialog/captiontext").setProperty("text", szoveg)
        qt_app.processEvents()
    _kattints(window, qt_app, _elem(window, "titledialog/add"))
    assert _varj(qt_app, lambda: not dialog.property("visible"))


def _tooltip_probe(engine, target: QObject) -> QObject:
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick\nimport QtQuick.Controls\nItem {
            property var targetItem
            readonly property string attachedText:
                targetItem.ToolTip.text
        }""",
        QUrl(),
    )
    assert component.isReady(), component.errors()
    probe = component.createWithInitialProperties({"targetItem": target})
    assert probe is not None, component.errors()
    _KEEP_ALIVE.extend((component, probe))
    return probe


def test_a_film_panel_feliratai_es_muveletei_a_foablakbol_minden_magassagon(
    qml_app_email, qt_app
):
    window, controller, engine = qml_app_email
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    film_gomb = _elem(window, "trayMovieButton")
    alapmagassag = window.height()
    film = None
    try:
        for eltolás in (-5, 0, 5):
            window.resize(window.width(), alapmagassag + eltolás)
            qt_app.processEvents()
            _kattints(window, qt_app, film_gomb)
            film = _elem(window, "movieDialog")
            assert film.property("visible") is True
            _kattints(window, qt_app, _elem(window, "movieTabMotion"))

            for nev in (
                "moviesize_label",
                "audio_label",
                "ordering_header_label",
                "movieSmartOrder",
                "movieAlbumOrder",
                "movieChronologicalOrder",
                "lengthslider_label",
                "burstslider_label",
                "rewind",
                "movieRemoveSlideButton",
                "movieAddClipsButton",
                "movieDeleteClipButton",
                "tabpanel2",
                "movieSlideText",
                "movieTextStyleBox",
                "text_picker_panel",
                "bkg_picker_panel",
                "txcolorpicker_bevel",
            ):
                elem = _elem(window, nev)
                if elem.property("visible"):
                    assert elem.property("width") > 0 and elem.property("height") > 0

            assert _elem(window, "moviesize_label").property("text") == "Méretek"
            assert _elem(window, "audio_label").property("text") == "Hangsáv:"
            assert _elem(window, "ordering_header_label").property("text") == (
                "Diák rendezése:"
            )
            assert _elem(window, "lengthslider_label").property("text") == (
                "Összes fénykép"
            )
            assert _elem(window, "burstslider_label").property("text") == (
                "Ne legyen szűrés a készítés ideje alapján"
            )
            rewind = _elem(window, "rewind")
            assert _tooltip_probe(engine, rewind).property("attachedText") == (
                "Vissza a kijelölt diához"
            )
            _kattints(window, qt_app, _elem(window, "movieTabSlide"))
            outline = _elem(window, "movieOutlineBox")
            assert _tooltip_probe(engine, outline).property("attachedText") == (
                "Automatikus körvonal (mint a filmfeliratok esetében)"
            )
            remove = _elem(window, "movieRemoveSlideButton")
            assert _tooltip_probe(engine, remove).property("attachedText") == (
                "A kijelölt dia eltávolítása"
            )
            _kattints(window, qt_app, _elem(window, "movieTabClips"))
            add = _elem(window, "movieAddClipsButton")
            assert _tooltip_probe(engine, add).property("attachedText") == (
                "A kijelölt klip(ek) hozzáadása a mozgófilm végéhez"
            )
            delete = _elem(window, "movieDeleteClipButton")
            assert _tooltip_probe(engine, delete).property("attachedText") == (
                "A kijelölt klip(ek) eltávolítása a tálcáról"
            )
            film.close()
            film = None
            qt_app.processEvents()

        _kattints(window, qt_app, film_gomb)
        film = _elem(window, "movieDialog")
        _kattints(window, qt_app, _elem(window, "movieTabSlide"))
        assert _elem(window, "tabpanel2").property("visible")
        text = _elem(window, "movieSlideText")
        assert text.property("visible")
        styles = _elem(window, "movieTextStyleBox")
        assert len(list(styles.property("model") or [])) == 12
        outline = _elem(window, "movieOutlineBox")
        _kattints(window, qt_app, outline)
        assert outline.property("checked") is True

        _elem(window, "txcolorpicker_bevel")
        _kattints(window, qt_app, _elem(window, "movieTextColorButton"))
        szinvalaszto = _elem(window, "text_picker_panel")
        assert _varj(qt_app, lambda: szinvalaszto.property("visible"))
        szinvalaszto.close()
        _kattints(window, qt_app, _elem(window, "movieBackgroundColorButton"))
        hattervalaszto = _elem(window, "bkg_picker_panel")
        assert _varj(qt_app, lambda: hattervalaszto.property("visible"))
        hattervalaszto.close()

        _dia_felvetel(window, qt_app)
        dia_lista = _elem(window, "movieSlideList")
        assert _varj(qt_app, lambda: dia_lista.property("count") == 1)
        assert film.property("movieSlides").property("length").toInt() == 1
        _kattints(window, qt_app, _elem(window, "movieRemoveSlideButton"))
        assert dia_lista.property("count") == 0

        _kattints(window, qt_app, _elem(window, "movieTabClips"))
        length = _elem(window, "lengthslider/scaleslider")
        burst = _elem(window, "burstslider/scaleslider")
        length.setProperty("value", 0.5)
        assert _elem(window, "movieLengthCount").property("text") == "0"
        length.setProperty("value", 1.0)
        assert _elem(window, "movieLengthCount").property("text") == "2"
        burst.setProperty("value", 0.5)
        assert film.property("movieBurstThresholdSeconds") == 21600
        assert _elem(window, "burstslider_label").property("text") == (
            "Az utolsó időszak képeinek eltávolítása: 21600"
        )
        _elem(window, "movieClipList").setProperty("currentIndex", 1)
        _kattints(window, qt_app, _elem(window, "movieDeleteClipButton"))
        assert _darab(film.property("movieClipSources")) == 1
        _kattints(window, qt_app, _elem(window, "movieAddClipsButton"))
        assert _darab(film.property("movieClipSources")) == 2

        _elem(window, "movieClipList").setProperty("currentIndex", 1)
        _elem(window, "movieSeconds").setProperty("value", 10)
        _kattints(window, qt_app, _elem(window, "movieTabMotion"))
        scroll = _elem(window, "movieTabPanelMotion")
        preview = _elem(window, "moviePreviewButton")
        flickable = scroll.property("contentItem")
        assert flickable.property("contentY") == 0, "az előnézet ellenőrzése nem görgethet"
        hatter = film.property("background")
        hatter_teteje = hatter.mapToScene(QPointF(0, 0)).y()
        hatter_alja = hatter.mapToScene(
            QPointF(hatter.property("width"), hatter.property("height"))
        ).y()
        gomb_teteje = preview.mapToScene(QPointF(0, 0)).y()
        gomb_alja = preview.mapToScene(
            QPointF(0, preview.property("height"))
        ).y()
        assert gomb_teteje >= hatter_teteje - 3
        assert gomb_alja <= hatter_alja + 3, "az előnézetgomb kilóg a párbeszéd látható teréből"
        _kattints(window, qt_app, preview)
        assert _elem(window, "moviePreviewTimer").property("running") is True
        assert _varj(qt_app, lambda: film.property("previewIndex") == 1)
        _kattints(window, qt_app, preview)
        assert _elem(window, "moviePreviewTimer").property("running") is False
        _kattints(window, qt_app, _elem(window, "rewind"))
        assert film.property("previewIndex") == 1
        assert not _elem(window, "moviePreviewTimer").property("running")

        for nev in ("movieSmartOrder", "movieAlbumOrder", "movieChronologicalOrder"):
            radio = _elem(window, nev)
            motion = _elem(window, "movieTabPanelMotion")
            flickable = motion.property("contentItem")
            lathato_teteje = motion.mapToScene(QPointF(0, 0)).y()
            lathato_alja = motion.mapToScene(
                QPointF(motion.property("width"), motion.property("height"))
            ).y()
            radio_teteje = radio.mapToScene(QPointF(0, 0)).y()
            radio_alja = radio.mapToScene(
                QPointF(0, radio.property("height"))
            ).y()
            gorgetes = flickable.property("contentY")
            if radio_alja > lathato_alja + 3:
                max_gorgetes = max(
                    0,
                    motion.property("contentHeight")
                    - flickable.property("height"),
                )
                flickable.setProperty(
                    "contentY",
                    min(max_gorgetes, gorgetes + radio_alja - lathato_alja + 3),
                )
            elif radio_teteje < lathato_teteje - 3:
                flickable.setProperty(
                    "contentY", max(0, gorgetes - (lathato_teteje - radio_teteje + 3))
                )
            qt_app.processEvents()
            _kattints(window, qt_app, radio)
            assert radio.property("checked") is True
    finally:
        if film is not None:
            film.close()
        window.resize(window.width(), alapmagassag)
        qt_app.processEvents()


@pytest.mark.parametrize(
    "fixture_nev", ["qml_app", "qml_app_email"], ids=["angol", "magyar"]
)
@pytest.mark.parametrize(
    ("kijeloles", "elvart_darabszam"),
    [([0], 1), ([0, 1], 2)],
    ids=["egy-kep", "tobb-kep"],
)
def test_a_film_elonezete_gorgetes_nelkul_latszik_es_kattinthato(
    request, qt_app, fixture_nev, kijeloles, elvart_darabszam
):
    window, _controller, _engine = request.getfixturevalue(fixture_nev)
    window.setProperty("selectedIndexes", kijeloles)
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    eredeti_meret = (window.width(), window.height())
    window.resize(1280, 800)
    qt_app.processEvents()
    film_gomb = _elem(window, "trayMovieButton")
    alapmagassag = window.height()
    film = None
    try:
        for eltolás in (-5, 0, 5):
            window.resize(window.width(), alapmagassag + eltolás)
            qt_app.processEvents()
            _kattints(window, qt_app, film_gomb)
            film = _elem(window, "movieDialog")
            assert _varj(qt_app, lambda film=film: film.property("visible"))
            assert _darab(film.property("movieClipSources")) == elvart_darabszam
            _kattints(window, qt_app, _elem(window, "movieTabMotion"))
            _elem(window, "movieSeconds").setProperty("value", 10)

            panel = _elem(window, "moviePreviewPanel")
            motion = _elem(window, "movieTabPanelMotion")
            footer = _elem(window, "movieCancelButton")
            assert panel.property("visible") is True
            assert _elem(window, "moviePreviewImage").property("visible") is True
            preview = _elem(window, "moviePreviewButton")
            assert preview.property("visible") is True

            panel_teteje = panel.mapToScene(QPointF(0, 0)).y()
            panel_alja = panel.mapToScene(
                QPointF(panel.property("width"), panel.property("height"))
            ).y()
            fultartalom_alja = motion.mapToScene(
                QPointF(0, motion.property("height"))
            ).y()
            footer_teteje = footer.mapToScene(QPointF(0, 0)).y()
            assert panel_teteje >= fultartalom_alja - 3, "az előnézet a fülek görgetett tartalmában maradt"
            assert panel_alja <= footer_teteje + 3, "az előnézet a párbeszéd alsó gombsorába lóg"

            hatter = film.property("background")
            hatter_teteje = hatter.mapToScene(QPointF(0, 0)).y()
            hatter_alja = hatter.mapToScene(
                QPointF(hatter.property("width"), hatter.property("height"))
            ).y()
            gomb_teteje = preview.mapToScene(QPointF(0, 0)).y()
            gomb_alja = preview.mapToScene(
                QPointF(0, preview.property("height"))
            ).y()
            assert gomb_teteje >= hatter_teteje - 3
            assert 0 < film.property("height") <= window.height(), (
                "a párbeszéd magassága kilép a főablakból"
            )
            assert gomb_alja <= hatter_alja + 3, (
                "a gomb nincs a párbeszéd látható terében: "
                f"dialógus={film.property('height'):.1f}, "
                f"főablak={window.height():.1f}, "
                f"háttér={hatter.property('height'):.1f}"
            )

            flickable = motion.property("contentItem")
            assert flickable.property("contentY") == 0, "a próba alatt nem görgettünk"

            for nev in (
                "movieAudioOptionBox",
                "movieShowCaptions",
                "movieShowDates",
                "movieCropToFit",
                "movieRemoveLowResFaces",
                "movieSmartOrder",
                "movieAlbumOrder",
                "movieChronologicalOrder",
            ):
                _teljesen_latszik(motion, _elem(window, nev), megnevezes=nev)

            bar = _elem(window, "video_control_bar2/controlbar")
            for nev in (
                "video_control_bar2/moviescrubslider_container",
                "video_control_bar2/time",
                "video_control_bar2/scaleslider",
                "video_control_bar2/volumeslider",
                "video_control_bar2/moviecontrolsclip",
                "video_control_bar2/1to1",
                "video_control_bar2/fullscreen",
            ):
                elem = _elem(window, nev)
                assert elem.property("visible") is True
                assert elem.property("width") > 0 and elem.property("height") > 0
            assert bar.property("visible") is True

            timer = _elem(window, "moviePreviewTimer")
            _kattints(window, qt_app, preview)
            assert timer.property("running") is True, "a valódi kattintás nem indította el az előnézetet"
            if elvart_darabszam > 1:
                assert _varj(
                    qt_app,
                    lambda film=film: film.property("previewIndex") == 1,
                )
            _kattints(window, qt_app, preview)
            assert timer.property("running") is False, "a valódi kattintás nem állította le az előnézetet"

            film.close()
            film = None
            qt_app.processEvents()
    finally:
        if film is not None:
            film.close()
        window.resize(*eredeti_meret)
        qt_app.processEvents()


def test_a_kis_foablakban_a_filmful_gorgetosavval_marad_lathato(
    qml_app_email, qt_app
):
    window, _controller, _engine = qml_app_email
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    eredeti_meret = (window.width(), window.height())
    film = None
    try:
        for eltolás in (-5, 0, 5):
            window.resize(1280, 560 + eltolás)
            qt_app.processEvents()
            _kattints(window, qt_app, _elem(window, "trayMovieButton"))
            film = _elem(window, "movieDialog")
            assert _varj(qt_app, lambda film=film: film.property("visible"))
            assert 0 < film.property("height") <= window.height()

            motion = _elem(window, "movieTabPanelMotion")
            scrollbar = _elem(window, "movieMotionScrollBar")
            assert motion.property("contentHeight") > motion.property("height")
            assert scrollbar.property("visible") is True

            film.close()
            film = None
            qt_app.processEvents()
    finally:
        if film is not None:
            film.close()
        window.resize(*eredeti_meret)
        qt_app.processEvents()


def test_a_movie_dialog_hattere_cime_es_gombjai_a_parbeszedben_maradnak(
    qml_app, qt_app
):
    """A valódi párbeszéd háttere és a fontos gombjai minden magasságon látszanak."""
    window, _controller, _engine = qml_app
    window.setProperty("selectedIndexes", [0, 1])
    qt_app.processEvents()
    film_gomb = _elem(window, "trayMovieButton")
    alapmagassag = window.height()
    film = None
    try:
        for eltolás in (-5, 0, 5):
            window.resize(window.width(), alapmagassag + eltolás)
            qt_app.processEvents()
            _kattints(window, qt_app, film_gomb)
            film = _elem(window, "movieDialog")
            assert _varj(qt_app, lambda film=film: film.property("visible"))
            kep = window.grabWindow()
            assert not kep.isNull(), "a főablak grabWindow() képe üres"
            if eltolás == 0 and os.environ.get("PICASA_MOVIE_DIALOG_SCREENSHOT"):
                assert kep.save(os.environ["PICASA_MOVIE_DIALOG_SCREENSHOT"])

            assert film.property("title") == "Movie"
            motion = _elem(window, "movieTabPanelMotion")
            assert motion.property("contentWidth") <= motion.property("width") + 3, (
                "a Film fül vízszintes tartalma kilóg a párbeszéd nézőteréből"
            )
            hatter = film.property("background")
            assert hatter is not None, "a Movie párbeszédnek nincs hátteret adó eleme"
            assert hatter.property("visible") is True
            assert hatter.property("opacity") >= 0.99
            szin = hatter.property("color")
            if hasattr(szin, "alphaF"):
                assert szin.alphaF() >= 0.99, "a párbeszéd háttere áttetsző"

            parbeszed_bal = hatter.mapToScene(QPointF(0, 0))
            parbeszed_jobb = hatter.mapToScene(
                QPointF(hatter.property("width"), hatter.property("height"))
            )
            parbeszed = QRectF(parbeszed_bal, parbeszed_jobb)
            # Az alsó keretsáv szöveg és gomb nélküli: itt a kirajzolt
            # kitöltést hasonlítjuk a párbeszéden kívüli könyvtárnézethez.
            sor_y = parbeszed.bottom() - 8
            kitoltes = _kep_szin(kep, window, QPointF(parbeszed.left() + 8, sor_y))
            kint = _kep_szin(kep, window, QPointF(parbeszed.right() + 10, sor_y))
            keret = _kep_szin(kep, window, QPointF(parbeszed.left(), sor_y))
            assert kitoltes.alpha() == 255, "a Movie párbeszéd kitöltése nem fed"
            assert max(
                abs(kitoltes.red() - kint.red()),
                abs(kitoltes.green() - kint.green()),
                abs(kitoltes.blue() - kint.blue()),
            ) >= 10, "a Movie párbeszéd kitöltése a grabWindow képen átlátszó"
            assert max(
                abs(keret.red() - kitoltes.red()),
                abs(keret.green() - kitoltes.green()),
                abs(keret.blue() - kitoltes.blue()),
            ) >= 10, "a Movie párbeszéd kerete nem különül el a kitöltéstől"
            vezérlok = [
                _elem(window, "movieBrowseButton"),
                _elem(window, "movieAddAudioButton"),
                _elem(window, "movieRemoveAudioButton"),
                _elem(window, "movieCancelButton"),
                _elem(window, "movieCreateButton"),
            ]
            belso = parbeszed.adjusted(-3, -3, 3, 3)
            for elem in vezérlok:
                assert elem.property("visible"), f"{elem.objectName()} nem látható"
                bal_fent = elem.mapToScene(QPointF(0, 0))
                jobb_lent = elem.mapToScene(
                    QPointF(elem.property("width"), elem.property("height"))
                )
                gomb_teglalap = QRectF(bal_fent, jobb_lent)
                assert belso.contains(gomb_teglalap), (
                    f"{elem.objectName() or elem.property('text')} kilóg a Movie "
                    f"párbeszédből: {gomb_teglalap} kívül: {parbeszed}"
                )

            film.close()
            film = None
            qt_app.processEvents()
    finally:
        if film is not None and film.property("visible"):
            film.close()
        window.resize(window.width(), alapmagassag)
        qt_app.processEvents()


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_a_filmszalag_atrendezese_a_mxf_kimenetbe_kerul(
    qml_app_email, qt_app, tmp_path, magassag_eltolas
):
    """A filmszalagon húzott szöveges dia sorrendje a projektben is megmarad."""
    window, _controller, _engine = qml_app_email
    window.setProperty("selectedIndexes", [0, 1])
    qt_app.processEvents()
    alapmagassag = window.height()
    film = None
    try:
        window.resize(window.width(), alapmagassag + magassag_eltolas)
        qt_app.processEvents()
        _kattints(window, qt_app, _elem(window, "trayMovieButton"))
        film = _elem(window, "movieDialog")
        _kattints(window, qt_app, _elem(window, "movieTabSlide"))

        filmstrip = _elem(window, "viewedit")
        assert filmstrip.property("visible")
        field = _elem(window, "movieSlideText")
        _kattints(window, qt_app, field)
        _dia_felvetel(window, qt_app, "Első dia")
        _dia_felvetel(window, qt_app, "Második dia")
        _dia_felvetel(window, qt_app, "Harmadik dia")
        assert _varj(qt_app, lambda: filmstrip.property("count") == 3)
        filmstrip.setProperty("contentY", 0)
        movie_slide_list = _elem(window, "movieSlideList")
        slide_scroll = _elem(window, "tabpanel2")
        _gorgess_elemhez(slide_scroll, filmstrip, qt_app)

        # A kirajzolt sordelegáltak aktuális geometriájából kattintunk.
        def sor_pont(index):
            nev = f"movieSlideDelegate{index}"
            sor = next(
                (
                    gyerek
                    for gyerek in movie_slide_list.property("contentItem").childItems()
                    if gyerek.objectName() == nev
                ),
                None,
            )
            assert sor is not None, f"{nev} nem rajzolódott ki a filmszalagon"
            pont = sor.mapToScene(
                QPointF(sor.property("width") / 2, sor.property("height") / 2)
            ).toPoint()
            return pont

        ablak = filmstrip.window() or window
        QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, pos=sor_pont(0))
        qt_app.processEvents()
        assert field.property("text") == "Első dia"
        _gorgess_elemhez(slide_scroll, field, qt_app)
        field_ablak = field.window() or window
        _kattints(window, qt_app, field)
        QTest.keyClick(
            field_ablak,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.ControlModifier,
        )
        for karakter in "Szerkesztett elso dia":
            if karakter == " ":
                gomb = Qt.Key.Key_Space
            else:
                gomb = Qt.Key(ord(karakter.upper()))
            modosito = (
                Qt.KeyboardModifier.ShiftModifier
                if karakter.isupper()
                else Qt.KeyboardModifier.NoModifier
            )
            QTest.keyClick(field_ablak, gomb, modosito)
        qt_app.processEvents()

        _gorgess_elemhez(slide_scroll, filmstrip, qt_app)
        start = sor_pont(1)
        cel = sor_pont(0)
        QTest.mousePress(ablak, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(ablak, cel, delay=100)
        QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, pos=cel)
        qt_app.processEvents()
        assert [slide["text"] for slide in film.property("movieSlides").toVariant()] == [
            "Második dia",
            "szerkesztett elso dia",
            "Harmadik dia",
        ]

        # Ctrl-kattintással két dia együtt kijelölhető és áthúzható.
        start = sor_pont(1)
        QTest.mouseClick(
            ablak,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ControlModifier,
            pos=start,
        )
        qt_app.processEvents()
        assert len(film.property("movieSlideSelection").toVariant()) == 2
        start = sor_pont(1)
        cel = sor_pont(2)
        QTest.mousePress(ablak, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(ablak, cel, delay=100)
        QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, pos=cel)
        qt_app.processEvents()
        assert [slide["text"] for slide in film.property("movieSlides").toVariant()] == [
            "Harmadik dia",
            "Második dia",
            "szerkesztett elso dia",
        ]

        # A filmszalagon kívülre húzás törli a kijelölt diát.
        start = sor_pont(0)
        cel = filmstrip.mapToScene(
            QPointF(filmstrip.property("width") / 2, filmstrip.property("height") + 12)
        ).toPoint()
        QTest.mousePress(ablak, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(ablak, cel, delay=100)
        QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, pos=cel)
        qt_app.processEvents()
        assert filmstrip.property("count") == 2

        kimenet = tmp_path / "filmszalag.mp4"
        film.setProperty("targetFile", str(kimenet))
        _kattints(window, qt_app, _elem(window, "movieCreateButton"))
        from picasapy.movie.mxf import read_mxf

        def _projekt_kesz():
            # A fájl a megírás közben már létezhet, de még üres (#4220).
            try:
                return read_mxf(kimenet.with_suffix(".mxf"))
            except (OSError, ValueError, SyntaxError):
                return None

        assert _varj(qt_app, lambda: _projekt_kesz() is not None, 30)
        projekt = _projekt_kesz()
        assert [atmenet.forras.text for atmenet in projekt.atmenetek[-2:]] == [
            "Második dia",
            "szerkesztett elso dia",
        ]
    finally:
        if film is not None and film.property("visible"):
            film.close()
        window.resize(window.width(), alapmagassag)
        qt_app.processEvents()
