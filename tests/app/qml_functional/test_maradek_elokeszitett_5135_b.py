"""A #5135 maradék vezérlői, 2. rész: nyomtatás, film, címdia - VALÓDI kattintással.

Az első rész (`test_maradek_elokeszitett_5135.py`) az arcot, az Emberek-panelt,
a geotag-párbeszédet és az importot fedi; ez a fájl a folytatás:

- `printPreviewPrevButton`, `printPreviewNextButton` - a több oldalas
  nyomtatási előnézet lapozása;
- `movieSoloClip` - a film csak a kijelölt klipet exportálja;
- `titledialog/outline` - a címdia körvonal-jelölője a mentett diába kerül.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF
from test_maradek_elokeszitett_5135 import (
    _elem,
    _filmet_nyit,
    _kattint,
    _lista,
    _varj,
)
from test_racs_vezerlok_valodi_5135 import (
    _kattints_mindenablakban,
    _zar,
)

try:
    import PySide6.QtPrintSupport  # noqa: F401

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover
    _QTPRINTSUPPORT_VAN = False


def _legfelso_elem(gyoker, pont):
    """A pont alatti legmélyebb látható elem neve (a kattintás célpontja)."""
    elem = gyoker
    while True:
        helyi = elem.mapFromScene(pont)
        gyerek = elem.childAt(helyi.x(), helyi.y())
        if gyerek is None:
            return elem
        elem = gyerek


def _lapozo_allapot(dialog, gomb) -> str:
    kozep = gomb.mapToScene(QPointF(gomb.width() / 2, gomb.height() / 2))
    cel = _legfelso_elem(gomb.window().contentItem(), kozep)
    return (
        f"oldal={dialog.property('previewPage')}"
        f"/{dialog.property('previewPageCount')}, "
        f"gomb={gomb.property('enabled')} {gomb.width()}x{gomb.height()} "
        f"@({kozep.x():.0f},{kozep.y():.0f}), "
        f"ablak={gomb.window().width()}x{gomb.window().height()}, "
        f"a pont alatt: {cel.objectName()!r} ({type(cel).__name__}, "
        f"{cel.metaObject().className()})"
    )


# ---------------------------------------------------------------------------
# 5. printPreviewPrev/NextButton - több oldalas nyomtatási előnézet
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason="a PySide6.QtPrintSupport modul hiányzik ezen a gépen",
)
class TestNyomtatasElonezetLapozas:
    def test_a_lapozo_gombok_valodi_kattintassal_leptetik_az_elonezetet(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        _kattint(window, qt_app, _elem(window, "trayPrintButton"))
        dialog = _elem(window, "printDialog")
        assert _varj(qt_app, lambda: dialog.property("visible") is True), (
            "a nyomtatás gomb nem nyitotta meg a párbeszédet"
        )
        szoveg = _elem(window, "printPreviewPageText")
        assert _varj(qt_app, lambda: szoveg.property("text") == "1 / 2"), (
            f"az előnézet nem két lapos: {szoveg.property('text')!r}"
        )

        # #5520: az önálló ablak első kattintása aktiválás nélkül elveszhet
        dialog.requestActivate()
        assert _varj(qt_app, lambda: dialog.property("active") is True), (
            "a nyomtatási párbeszéd nem lett aktív"
        )
        # #5520: a nyitás utáni átméretezés (`meretezesIdozito`) lecsengése
        # előtt a gomb elmozdulhat a lenyomás és a felengedés között
        assert _varj(
            qt_app, lambda: dialog.property("meretezesFuggoben") is False
        ), "a nyomtatási párbeszéd méretezése nem csengett le"
        kovetkezo = _elem(window, "printPreviewNextButton")
        assert _varj(qt_app, lambda: kovetkezo.property("enabled") is True), (
            "a Következő gomb nem lett engedélyezett"
        )
        _kattints_mindenablakban(qt_app, "printPreviewNextButton")
        assert _varj(qt_app, lambda: szoveg.property("text") == "2 / 2"), (
            "a Következő gomb nem léptette az előnézetet: "
            + _lapozo_allapot(dialog, kovetkezo)
        )
        assert kovetkezo.property("enabled") is False

        _kattints_mindenablakban(qt_app, "printPreviewPrevButton")
        assert _varj(qt_app, lambda: szoveg.property("text") == "1 / 2"), (
            "az Előző gomb nem léptette vissza az előnézetet"
        )
        _zar(qt_app, dialog)


# ---------------------------------------------------------------------------
# 6. movieSoloClip - a film csak a kijelölt klipet exportálja
# ---------------------------------------------------------------------------


class TestFilmEgyKlip:
    def test_a_csak_ezt_a_klipet_jelolo_negyzet_egy_klipet_exportal(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        from picasapy.movie.slideshow import MovieReport

        window, controller, _engine = qml_app
        controller._get_settings().setValue("movie/outputDir", str(tmp_path / "filmek"))
        exportok: list[list[str]] = []

        def export_mock(forrasok, cel, _beallitasok, progress=None):
            exportok.append([Path(str(f)).name for f in forrasok])
            ut = Path(cel)
            ut.parent.mkdir(parents=True, exist_ok=True)
            ut.write_bytes(b"film")
            return MovieReport(
                target=ut,
                used=tuple(Path(str(f)) for f in forrasok),
                skipped=(),
                reasons=(),
                frames=1,
            )

        monkeypatch.setattr("picasapy.app.create_controller.export_movie", export_mock)
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        film = _filmet_nyit(window, qt_app)
        assert len(_lista(film.property("movieClipSources"))) == 2
        _kattint(window, qt_app, _elem(window, "movieTabClips"))
        _elem(window, "movieClipList").setProperty("currentIndex", 1)
        solo = _elem(window, "movieSoloClip")
        _kattint(window, qt_app, solo)
        assert _varj(qt_app, lambda: solo.property("checked") is True), (
            "a Csak ezt a klipet jelölő nem jelölődött be"
        )
        _kattint(window, qt_app, _elem(window, "movieTabMotion"))

        _kattint(window, qt_app, _elem(window, "movieCreateButton"))

        nev_masodik = Path(controller.photos.filePathAt(1)).name
        assert _varj(qt_app, lambda: len(exportok) == 1), (
            "a film létrehozása nem indította el az exportot"
        )
        assert exportok[0] == [nev_masodik], (
            f"a jelölő bejelölve is több klipet exportált: {exportok[0]}"
        )


# ---------------------------------------------------------------------------
# 7. titledialog/outline - a címdia körvonal-jelölője a mentett diába kerül
# ---------------------------------------------------------------------------


class TestCimdiaKorvonal:
    def test_a_korvonal_jelolo_a_mentett_diara_kerul(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        film = _filmet_nyit(window, qt_app)

        _kattint(window, qt_app, _elem(window, "movieTabSlide"))
        _kattint(window, qt_app, _elem(window, "movieInsertSlideButton"))
        cimdia = _elem(window, "movieTitleDialog")
        assert _varj(qt_app, lambda: cimdia.property("visible") is True), (
            "a szöveges dia gombja nem nyitotta meg a címdia-szerkesztőt"
        )
        jelolo = _elem(window, "titledialog/outline")
        assert jelolo.property("checked") is False, "a próba feltétele: alapból nincs körvonal"
        _kattint(window, qt_app, jelolo)
        assert _varj(qt_app, lambda: jelolo.property("checked") is True), (
            "a körvonal-jelölőre kattintás nem jelölte be"
        )

        _kattint(window, qt_app, _elem(window, "titledialog/add"))

        assert _varj(qt_app, lambda: cimdia.property("visible") is not True)
        dias = _lista(film.property("movieSlides"))
        assert dias, "a címdia nem került a film diái közé"
        assert dias[-1].get("outline") is True, (
            "a bejelölt körvonal nem jutott el a mentett diáig"
        )
