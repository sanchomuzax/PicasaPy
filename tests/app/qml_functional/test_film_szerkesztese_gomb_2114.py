"""A „Mozgófilm szerkesztése" gomb a szerkesztőben (#2114).

## A mérés

Az eredetiben `editpanel/editslideshow` a `editpanel/editcollage`
IKERPÁRJA: ugyanaz a kezelő (`0x00567a00`), mindkettő `m_hidden`
(`editpanel.tre:1341` és `:1350`) — csak akkor jön elő, ha a megnyitott
fájl egy PROJEKT kimenete. A felirat és a buboréksúgó a hivatalos magyar
szövegtárból való (`panel-feliratok-hu.tsv:4928`, `:4929`).

## Amit ez az őr állít

- a gomb **alapból rejtett**, és csak akkor látszik, ha a fájl mellett ott
  a `.mxf` projektfájl;
- a kattintás elsüti a néző `editMovieRequested` jelzését az AKTUÁLIS
  fájl útvonalával;
- a kollázs-gomb ikerpárként **változatlan** marad.

## Amit NEM állít

A párbeszéd feltöltését — az a `Main.qml` `openSavedMovie` dolga, és a
vezérlő-oldali próbák (`test_film_projekt_visszaut_2114.py`) mérik, mit ad
vissza a projektfájl.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

from picasapy.movie.mxf import MxfAtmenet, MxfForras, MxfProjekt, write_mxf


def _gyerek(gyoker, nev):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nincs a jelenetben"
    return elem


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = _gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    nezo.setProperty("visible", True)
    qt_app.processEvents()
    return nezo


def _projektet_ir_a_kep_melle(nezo) -> Path:
    """A megnyitott kép mellé `.mxf`-et teszünk.

    ⚠️ A valós eset egy VIDEÓ kimenet, de a feltétel — és a vezérlő
    lekérdezése — a projektfájl MEGLÉTE, nem a médiatípus; a próbának így
    nem kell videót kódolnia."""
    kep = Path(str(nezo.property("currentFilePath")).replace("file://", ""))
    projekt = MxfProjekt(
        defaulttrans=MxfAtmenet(advanceinterval=3.0),
        atmenetek=(MxfAtmenet(forras=MxfForras(index=0, filename=str(kep))),),
    )
    return write_mxf(kep.with_suffix(".mxf"), projekt)


class TestAGombLathatosaga:
    def test_projektfajl_nelkul_REJTETT(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert _gyerek(window, "viewerEditMovieButton").property("visible") is False

    def test_projektfajllal_ELOJON(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _projektet_ir_a_kep_melle(nezo)
        # a jelző a `currentFilePath`-ra köt — újraértékeltetjük a lapozással
        nezo.setProperty("currentIndex", 1)
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()

        assert _gyerek(window, "viewerEditMovieButton").property("visible") is True

    def test_a_kollazs_gomb_valtozatlanul_rejtett(self, qml_app, qt_app):
        """Az ikerpár másik fele nem kapcsolódhat be a film projektjétől."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _projektet_ir_a_kep_melle(nezo)
        nezo.setProperty("currentIndex", 1)
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()

        assert _gyerek(window, "viewerEditCollageButton").property("visible") is False


class TestAKattintasJelzest_ad:
    def test_a_gomb_az_AKTUALIS_utvonallal_jelez(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _projektet_ir_a_kep_melle(nezo)
        nezo.setProperty("currentIndex", 1)
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()

        kapott = []
        nezo.editMovieRequested.connect(kapott.append)
        _gyerek(window, "viewerEditMovieButton").clicked.emit()
        qt_app.processEvents()

        assert kapott == [str(nezo.property("currentFilePath"))]
