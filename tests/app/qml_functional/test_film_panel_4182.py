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
    return qml_lista.property("length").toInt()


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

        _kattints(window, qt_app, _elem(window, "movieInsertSlideButton"))
        dia_lista = _elem(window, "movieSlideList")
        assert dia_lista.property("count") == 1
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
        ablak_vege = scroll.mapToScene(
            QPointF(scroll.property("width"), scroll.property("height"))
        ).y()
        gomb_vege = preview.mapToScene(
            QPointF(0, preview.property("height"))
        ).y()
        if gomb_vege > ablak_vege:
            max_gorgetes = max(
                0,
                scroll.property("contentHeight") - flickable.property("height"),
            )
            flickable.setProperty(
                "contentY", min(max_gorgetes, gomb_vege - ablak_vege + 3)
            )
            qt_app.processEvents()
        assert preview.mapToScene(
            QPointF(0, preview.property("height"))
        ).y() <= ablak_vege + 3
        _kattints(window, qt_app, _elem(window, "moviePreviewButton"))
        assert _varj(qt_app, lambda: film.property("previewIndex") == 1)
        flickable.setProperty("contentY", 0)
        qt_app.processEvents()
        _kattints(window, qt_app, _elem(window, "rewind"))
        assert film.property("previewIndex") == 1
        assert not _elem(window, "moviePreviewTimer").property("running")

        for nev in ("movieSmartOrder", "movieAlbumOrder", "movieChronologicalOrder"):
            _kattints(window, qt_app, _elem(window, nev))
            assert _elem(window, nev).property("checked") is True
    finally:
        if film is not None:
            film.close()
        window.resize(window.width(), alapmagassag)
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
        field.setProperty("text", "Első dia")
        _kattints(window, qt_app, _elem(window, "movieInsertSlideButton"))
        field.setProperty("text", "Második dia")
        _kattints(window, qt_app, _elem(window, "movieInsertSlideButton"))
        field.setProperty("text", "Harmadik dia")
        _kattints(window, qt_app, _elem(window, "movieInsertSlideButton"))
        assert filmstrip.property("count") == 3
        filmstrip.setProperty("contentY", 0)

        # A lista valódi soraiból és geometriájából számoljuk a húzást.
        def sor_pont(index):
            sor_magassag = filmstrip.property("contentHeight") / 3
            y = sor_magassag * (index + 0.5) - filmstrip.property("contentY")
            return filmstrip.mapToScene(
                QPointF(filmstrip.property("width") / 2, y)
            ).toPoint()

        ablak = filmstrip.window() or window
        QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, pos=sor_pont(0))
        qt_app.processEvents()
        assert field.property("text") == "Első dia"
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
        assert _varj(qt_app, lambda: kimenet.with_suffix(".mxf").exists(), 30)

        from picasapy.movie.mxf import read_mxf

        projekt = read_mxf(kimenet.with_suffix(".mxf"))
        assert [atmenet.forras.text for atmenet in projekt.atmenetek[-2:]] == [
            "Második dia",
            "szerkesztett elso dia",
        ]
    finally:
        if film is not None and film.property("visible"):
            film.close()
        window.resize(window.width(), alapmagassag)
        qt_app.processEvents()
