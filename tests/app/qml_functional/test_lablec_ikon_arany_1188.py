"""A lábléc ikonjai a saját képarányukban jelenjenek meg (#1188).

## A tulajdonos jelentése (v0.8.29, Windows), képpel

> „A lábléc ikonjai (helyjelző, tiltás-kör, csillag, két forgatás-nyíl)
> eltorzultak: keskenyek és megnyúltak."

## A mérés

Az érintett ikonok `contentItem: Image`-ként ülnek egy `PicasaButton`-ban.
A `Control` a `contentItem` GEOMETRIÁJÁT maga állítja be — az ott megadott
`anchors.centerIn: parent` ezért hatástalan —, a `Image.fillMode`
alapértelmezése pedig `Image.Stretch`. Az eredmény: a 14×14-es (négyzetes)
SVG a gomb tartalom-dobozára feszül.

Mérve (Linux, offscreen, v0.8.40):

| ikon | doboz | festett |
|---|---|---|
| `trayHoldIcon` | 16×26 | 16×26 |
| `trayClearIcon` | 16×26 | 16×26 |
| `trayCollageIcon` | 20×28 | 20×28 |
| `trayMovieIcon` | 20×28 | 20×28 |
| `trayShareIcon` | 20×28 | 20×28 |

Tehát **nem Windows-specifikus** — ott csak feltűnőbb. A festett méret
mindenhol a dobozzal egyezik, vagyis a kép nyúlik.
"""

import pytest
from PySide6.QtCore import QObject

#: mind négyzetes forrás-SVG, tehát a festett képnek is négyzetesnek kell lennie
NEGYZETES_IKONOK = (
    "trayHoldIcon",
    "trayClearIcon",
    "trayCollageIcon",
    "trayMovieIcon",
    "trayShareIcon",
)


@pytest.mark.parametrize("nev", NEGYZETES_IKONOK)
def test_a_festett_ikon_negyzetes_marad(qml_app, qt_app, nev):
    window, _controller, _ = qml_app
    ikon = window.findChild(QObject, nev)
    assert ikon is not None, f"{nev} nem található"
    szeles = float(ikon.property("paintedWidth"))
    magas = float(ikon.property("paintedHeight"))
    assert szeles > 0 and magas > 0, f"{nev}: nincs megfestett kép"
    assert abs(szeles - magas) < 0.5, (
        f"{nev}: a festett kép {szeles}×{magas} — a négyzetes SVG "
        f"eltorzult a gomb {ikon.property('width')}×"
        f"{ikon.property('height')}-es tartalom-dobozában"
    )


@pytest.mark.parametrize("nev", NEGYZETES_IKONOK)
def test_az_ikon_kitolti_a_doboz_rovidebb_oldalat(qml_app, qt_app, nev):
    """A megőrzés másik fele: ne csak ne torzuljon, de ne is zsugorodjon
    parányira — a rövidebb oldalt töltse ki."""
    window, _controller, _ = qml_app
    ikon = window.findChild(QObject, nev)
    assert ikon is not None
    rovidebb = min(float(ikon.property("width")), float(ikon.property("height")))
    assert float(ikon.property("paintedWidth")) >= rovidebb - 0.5
