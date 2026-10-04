"""#1977 + #4125: a Mozgófilm-párbeszéd HÉT méretet kínál, a futó felületen.

A vezérlő-oldali szélesség-átvitelt a `tests/app/test_film_felbontasok_1977.py`
méri. Ez az őr azt méri, ami abból nem látszik: hogy a hét méret **ki is
jut a választóba**, és hogy az alapérték a specifikáció szerinti 640x480.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt

VALASZTO = "movieHeightBox"

#: A spec 2.6/c hét mérete, az eredeti erőforrás-felirat alakjában.
VART = [
    "320x240", "640x480", "800x600", "1024x768",
    "1600x1200", "1280x720 (720p)", "1920x1080 (1080p)",
]


def _elem(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _nyisd_a_film_parbeszedet(window, qt_app):
    """A párbeszéd Loader mögött él — a MENÜBŐL kell megnyitni.

    Kijelölés nélkül a menütétel tiltott (#455/#1472), ezért előbb
    kijelölünk egy képet."""
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    tetel = _elem(window, "menuCreateMovie")
    assert tetel.property("enabled") is True, (
        "a Mozgófilm menüpont kijelölt képpel sem elérhető"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "movieHeightBox")


def test_a_valaszto_mind_a_het_meretet_kinalja(qml_app, qt_app):
    window, _controller, _engine = qml_app
    valaszto = _nyisd_a_film_parbeszedet(window, qt_app)

    model = list(valaszto.property("model") or [])
    assert model == VART, f"a méretlista eltér: {model}"


def test_az_alapertelmezes_a_spec_szerinti_640x480(qml_app, qt_app):
    """A 2.8/b szerint a makemovieres alapértéke az 1-es, 640x480-as sor."""
    window, _controller, _engine = qml_app
    valaszto = _nyisd_a_film_parbeszedet(window, qt_app)

    index = valaszto.property("currentIndex")
    model = list(valaszto.property("model") or [])
    assert model[index] == "640x480", (
        f"az alapértelmezés {model[index]!r} lett a 640x480 helyett"
    )
