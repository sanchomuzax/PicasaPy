"""Film-gomb a mappa-fejlécben (#4539).

## A lelet

Az eredeti Picasa mappa-fejlécében (`headerpanel/create_movie`, „Create
Movie Presentation") a kollázs-gomb mellett ALAPBÓL látszik a film-gomb.
Bizonyíték: a referencia-képernyőkép `research/testdata/screenshot/
2026-07-17 20 54 38.png` fejléce, nagyítva: ▸ · [+kép = kollázs] ·
[+filmszalag = film] · ☆ · mentés · Feltöltés ▾. A `ui-leltar.csv` a
`headerpanel/create_movie` elemet `mousedown` tulajdonsággal, rejtés nélkül
adja meg. Az elhelyezés a spec 2.8/c szakaszában van rögzítve.

Nálunk a film-gomb eddig csak a tálcán és a személyalbum-fejlécben volt.

## Mit mér ez a fájl

- a gomb ott van a mappa-fejlécben, és a kollázs-gomb után áll;
- VALÓDI kattintásra a Filmkészítő nyílik meg, a csoport képeivel;
- a gomb nem takarja a Feltöltés-gombot (a jobb oldali, nem
  testreszabható elemek a film után folytatódnak);
- mindez −5 / 0 / +5 px ablakmagasságnál is.
"""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg
from tests.support.qml_blokk import blokk_horgony_utan

_FEED = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "LightboxFeed.qml"
).read_text(encoding="utf-8")
_HEADER = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "LightboxHeader.qml"
).read_text(encoding="utf-8")

_MAPPA_KEPEI = ("elso.jpg", "masodik.jpg", "harmadik.jpg")


def _mappa_kepei(lib) -> None:
    for nev in _MAPPA_KEPEI:
        make_jpeg(lib / nev, size=(640, 400))


def _keres(elem: QQuickItem, object_name: str):
    if elem.objectName() == object_name:
        return elem
    for child in elem.childItems():
        found = _keres(child, object_name)
        if found is not None:
            return found
    return None


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(ablak, qt_app, elem: QQuickItem) -> None:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseMove(ablak, kozep, 10)
    qt_app.processEvents()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep,
    )
    qt_app.processEvents()


def _fejlec_gomb(ablak):
    gomb = _keres(ablak.contentItem(), "headerMovieButton")
    assert gomb is not None, "a mappa-fejlécből hiányzik a film-gomb"
    return gomb


class TestAGombOttVan:
    def test_a_mappa_fejlecben_van_film_gomb(self, qt_app, tmp_path):
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, vezerlo, _motor = next(gen)
        try:
            assert _varj(qt_app, lambda: vezerlo.photos.rowCount() == 3)
            gomb = _fejlec_gomb(ablak)
            assert gomb.isVisible(), "a film-gomb rejtett a mappa-fejlécben"
        finally:
            gen.close()

    def test_a_MERT_meret_29x27_mint_a_kollazs(self, qt_app, tmp_path):
        """A `headerpanel/create_collage` mellé, ugyanekkora gomb (spec 1.10.5)."""
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, vezerlo, _motor = next(gen)
        try:
            assert _varj(qt_app, lambda: vezerlo.photos.rowCount() == 3)
            gomb = _fejlec_gomb(ablak)
            assert (gomb.width(), gomb.height()) == (29.0, 27.0)
        finally:
            gen.close()

    def test_a_kollazs_gomb_utan_all(self, qt_app, tmp_path):
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, vezerlo, _motor = next(gen)
        try:
            assert _varj(qt_app, lambda: vezerlo.photos.rowCount() == 3)
            film = _fejlec_gomb(ablak)
            kollazs = _keres(ablak.contentItem(), "headerCollageButton")
            assert kollazs is not None
            assert film.mapToScene(QPointF(0, 0)).x() > (
                kollazs.mapToScene(QPointF(0, 0)).x()
            ), "a film-gomb nem a kollázs-gomb után áll"
        finally:
            gen.close()

    def test_nem_takarja_a_feltoltes_gombot(self, qt_app, tmp_path):
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, vezerlo, _motor = next(gen)
        try:
            assert _varj(qt_app, lambda: vezerlo.photos.rowCount() == 3)
            film = _fejlec_gomb(ablak)
            feltoltes = _keres(ablak.contentItem(), "headerUploadButton")
            assert feltoltes is not None
            film_jobb = film.mapToScene(QPointF(0, 0)).x() + film.width()
            assert feltoltes.mapToScene(QPointF(0, 0)).x() >= film_jobb, (
                "a Feltöltés-gomb a film-gomb alá csúszott"
            )
        finally:
            gen.close()


class TestABekotes:
    """A gomb NE csak létezzen — nyissa is meg a Filmkészítőt."""

    def test_a_jelzes_a_feedben_FOGADVA_van(self):
        assert "onMovieRequested" in _FEED, (
            "a fejléc film-jelzését senki nem fogja el — néma gomb"
        )

    def test_a_CSOPORT_kepeit_adja_at_nem_a_kijelolest(self):
        blokk = blokk_horgony_utan(_FEED, "onMovieRequested")
        assert "modelData.start" in blokk and "modelData.count" in blokk, (
            "a film-gomb nem a csoport sorait adja át"
        )

    def test_a_fejlecben_jelzi_a_szulonek(self):
        assert "movieRequested()" in _HEADER


_ABLAKMAGASSAG_ELTOLAS = (-5, 0, 5)


class TestKattintasra:
    def test_megnyitja_a_filmkeszitot_a_mappa_kepeivel(self, qt_app, tmp_path):
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, vezerlo, _motor = next(gen)
        try:
            assert _varj(qt_app, lambda: vezerlo.photos.rowCount() == 3)
            gomb = _fejlec_gomb(ablak)
            assert gomb.isEnabled()
            _kattints(ablak, qt_app, gomb)
            film = ablak.findChild(QObject, "movieDialog")
            assert film is not None, "a kattintás nem építette fel a Filmkészítőt"
            assert _varj(qt_app, lambda: film.property("visible")), (
                "a film-gomb nem nyitotta meg a Filmkészítőt"
            )
            forrasok = film.property("movieClipSources")
            if hasattr(forrasok, "toVariant"):
                forrasok = forrasok.toVariant()
            nevek = [Path(QUrl(str(url)).toLocalFile()).name for url in forrasok]
            # A rács saját rendezését követi, nem a fájlnevet — a HALMAZT
            # mérjük: a mappa minden képe, és más nem.
            assert sorted(nevek) == sorted(_MAPPA_KEPEI), (
                f"nem a mappa képei jutottak a filmkészítőhöz: {nevek!r}"
            )
            assert film.property("personMovieMode") is False, (
                "a mappa-film személyalbum-módban nyílt meg"
            )
            film.close()
        finally:
            gen.close()

    def test_ablakmagassag_eltolassal_is(self, qt_app, tmp_path):
        """−5 / 0 / +5 px: a gomb helye és a kattintás ugyanaz marad."""
        gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_mappa_kepei)
        ablak, vezerlo, _motor = next(gen)
        try:
            assert _varj(qt_app, lambda: vezerlo.photos.rowCount() == 3)
            eredeti = ablak.height()
            for eltolas in _ABLAKMAGASSAG_ELTOLAS:
                ablak.setHeight(eredeti + eltolas)
                assert _varj(
                    qt_app,
                    lambda eltolas=eltolas: ablak.height() == eredeti + eltolas,
                ), f"a főablak magassága nem állt be ({eltolas:+} px)"
                gomb = _fejlec_gomb(ablak)
                assert gomb.isVisible() and gomb.isEnabled(), (
                    f"a film-gomb nem kattintható ({eltolas:+} px)"
                )
                _kattints(ablak, qt_app, gomb)
                film = ablak.findChild(QObject, "movieDialog")
                assert film is not None and _varj(
                    qt_app, lambda film=film: film.property("visible")
                ), f"a film-gomb nem nyitotta meg a Filmkészítőt ({eltolas:+} px)"
                film.close()
                qt_app.processEvents()
        finally:
            gen.close()
