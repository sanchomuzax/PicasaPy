"""#2096: a kollázs EREDMÉNYE akkor is látszik, ha a Létrehozás-párbeszédek
sosem nyíltak meg.

## Miért van erre külön őr

A #1612 halasztani akarta a `CreateDialogs`-t. A #1743 őre megfogta: a
komponens KÉT `Connections { target: controller }` blokkot tartott, és a
fájl végi a kollázs/film EREDMÉNYÉT jelzi vissza. A kollázs viszont a
**Kollázs panelről** is indítható — halasztva a kezelő nem létezik, tehát a
„Kollázs elmentve…" visszajelzés NÉMÁN elveszne.

Ez az őr a VALÓDI utat méri: a vezérlő jelét adja ki úgy, hogy a
párbeszédeket előtte senki nem nyitotta meg.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _uzenet(window) -> str:
    par = window.findChild(QObject, "createResultDialog")
    assert par is not None, (
        "a createResultDialog nincs meg — a jelzés senkihez nem ért el (#2096)"
    )
    return str(par.property("message") or "")


def _settle(qt_app, korok=4):
    for _ in range(korok):
        qt_app.processEvents()


class TestPanelrolInditottKollazs:
    def test_a_SIKER_uzenete_megjelenik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.collageFinished.emit("/tmp/kollazs.jpg", 7, 0, 0)
        _settle(qt_app)
        szoveg = _uzenet(window)
        assert "/tmp/kollazs.jpg" in szoveg, szoveg
        assert "7" in szoveg, szoveg

    def test_a_HIBA_uzenete_megjelenik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.collageFailed.emit("nincs hely a lemezen")
        _settle(qt_app)
        assert "nincs hely a lemezen" in _uzenet(window)

    def test_a_par_beszed_LATHATOVA_is_valik(self, qml_app, qt_app):
        """Nem elég, hogy az üzenet beáll — meg is kell jelennie."""
        window, controller, _engine = qml_app
        controller.collageFinished.emit("/tmp/k.jpg", 3, 0, 0)
        _settle(qt_app)
        par = window.findChild(QObject, "createResultDialog")
        assert par is not None and par.property("visible") is True


class TestFilm:
    def test_a_film_eredmenye_is_megjelenik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.movieFinished.emit("/tmp/film.mp4", 12, 0, 0)
        _settle(qt_app)
        assert "/tmp/film.mp4" in _uzenet(window)

    def test_a_film_HIBAJA_is_megjelenik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.movieFailed.emit("a kodek hiányzik")
        _settle(qt_app)
        assert "a kodek hiányzik" in _uzenet(window)
