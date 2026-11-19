"""#7255: a csukott jobb fiók bezáró jele („✕”) nem látszik az ablak jobb szélén.

A csukott fiók 0 széles, de a fejlécének jobbra horgonyzott bezáró gombja a
fiók szélén kívülre, az ablak jobb szélére rajzolódott, épp oda, ahol a #7255
óta a zöld találati sáv jobbra igazított `Date Range:` felirata áll.

A próba a renderelt képet nézi, különbségként: a gomb helyét kétszer rögzíti,
egyszer látható, egyszer átlátszóvá tett gombbal. Ha a csukott fiók semmit nem
rajzol ki belőle, a két kép a gomb helyén azonos.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPointF

from tests.support.varakozas import var_feltetelre


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _terulet(kep, x0, y0, szel, mag):
    return [
        kep.pixel(x, y)
        for x in range(max(0, x0), min(x0 + szel, kep.width()))
        for y in range(max(0, y0), min(y0 + mag, kep.height()))
    ]


def test_a_csukott_fiok_bezaro_jele_nem_rajzolodik_ki(qml_app, qt_app):
    window = qml_app[0]
    fiok = _gyerek(window, "rightDrawer")
    assert var_feltetelre(qt_app, lambda: fiok.property("width") == 0, 10.0), "a fiók nem csukott"
    gomb = _gyerek(window, "rightDrawerClose")
    qt_app.processEvents()

    bal_felso = gomb.mapToScene(QPointF(0, 0))
    x0, y0 = int(bal_felso.x()), int(bal_felso.y())
    szel, mag = int(gomb.property("width")), int(gomb.property("height"))

    lathato = _terulet(window.grabWindow(), x0, y0, szel, mag)
    gomb.setProperty("opacity", 0.0)
    qt_app.processEvents()
    rejtett = _terulet(window.grabWindow(), x0, y0, szel, mag)
    gomb.setProperty("opacity", 1.0)

    assert lathato, "a gomb helye a képen kívül esik"
    elter = sum(a != b for a, b in zip(lathato, rejtett, strict=True))
    assert elter == 0, (
        f"a csukott fiók bezáró jele kirajzolódott (x {x0}..{x0 + szel}, y {y0}..{y0 + mag}, "
        f"{elter} eltérő képpont)"
    )
