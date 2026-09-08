"""A képtálca „További lehetőségek…" gombjának ikonja (#2537).

Az eredetiben ez az `outputlayout/export7_icon` (a `.tre` szerint a
`morebutton` gyereke). A rajzot a `respack.yt` rétegképéből mértük ki
(`tools/picasa/respack.py png … export7`, réteg-eltolás 2 173 134, 83 bájt;
levezetés: `docs/specs/picasa-keptalca.md` 21.3):

```
      #          ← 0. sor:  1 képpont
     ###         ← 1. sor:  3
    #####        ← 2. sor:  5
   #######       ← 3. sor:  7
  #########      ← 4. sor:  9
 ###########     ← 5. sor: 11
#############    ← 6. sor: 13
```

**13 × 7, egyetlen tömör alakzat, 49 látható képpont, egyetlen szín**
(`#69729B`), élsimítás nélkül — a sáv tizenegy ikonja közül ez az egyetlen,
amiben csak egy szín van.

## Miért a KIRAJZOLT képpontokat méri

Egy „létezik a fájl és hivatkozik rá valaki" próba akkor is zöld marad, ha a
rajz mást ábrázol. Ez a lap a Qt SVG-motorjával (a `Image` elemmel, tehát
UGYANAZZAL az úttal, amit az alkalmazás használ) rajzoltatja ki az ikont, és
soronként megszámolja a képpontokat.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

#: A MÉRT soronkénti képpontszám (a csúcs FELÜL).
MERT_SOROK = (1, 3, 5, 7, 9, 11, 13)

#: A MÉRT szín (`#69729B`, RGB 105, 114, 155).
MERT_SZIN = (105, 114, 155)

#: Nagyítás a mintavételhez — a blokkok közepén olvasunk.
NAGYITAS = 14

_IKON = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/icons/tray-more.svg"
)

_KEEPALIVE: list = []


@pytest.fixture(scope="module")
def kirajzolt(qt_app):
    """Az ikon kirajzolva, a QML `Image`-ével — nem SVG-szöveg-elemzéssel."""
    qml = f"""
import QtQuick
Rectangle {{
  width: 13 * {NAGYITAS}; height: 7 * {NAGYITAS}; color: "white"
  Image {{
    anchors.fill: parent
    source: "{QUrl.fromLocalFile(str(_IKON)).toString()}"
    fillMode: Image.PreserveAspectFit
    smooth: false
  }}
}}
"""
    view = QQuickView()
    komponens = QQmlComponent(view.engine())
    komponens.setData(qml.encode("utf-8"), QUrl())
    hibak = [hiba.toString() for hiba in komponens.errors()]
    assert hibak == [], hibak
    gyoker = komponens.create()
    assert gyoker is not None
    gyoker.setParentItem(view.contentItem())
    view.resize(13 * NAGYITAS, 7 * NAGYITAS)
    view.show()
    for _ in range(4):
        qt_app.processEvents()
        hurok = QEventLoop()
        QTimer.singleShot(60, hurok.quit)
        hurok.exec()
    kep = view.grabWindow()
    _KEEPALIVE.extend((view, gyoker, komponens))
    return kep


def _festett(kep, x: int, y: int) -> bool:
    szin = QColor(kep.pixel(x * NAGYITAS + NAGYITAS // 2, y * NAGYITAS + NAGYITAS // 2))
    return szin.red() < 200


def test_a_fajl_letezik():
    assert _IKON.is_file(), f"hiányzik a mért ikon: {_IKON}"


def test_a_gomb_hivatkozik_ra():
    qml = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/qml/PicasaPy/TrayBar.qml"
    ).read_text(encoding="utf-8")
    assert 'iconSource: "icons/tray-more.svg"' in qml, (
        "a `trayMoreButton` nem hivatkozik a mért ikonra — a #2493 óta ikon "
        "nélkül állt"
    )


def test_a_kirajzolt_alak_a_MERT_haromszog(kirajzolt):
    """Soronként 1, 3, 5, 7, 9, 11, 13 képpont — tömör, FELFELE mutató
    háromszög. Ez a próba a RAJZOT nézi, nem az SVG szövegét."""
    kapott = tuple(sum(1 for x in range(13) if _festett(kirajzolt, x, y)) for y in range(7))
    assert kapott == MERT_SOROK, (
        f"a kirajzolt alak nem a mért háromszög: soronként {kapott}, "
        f"várt {MERT_SOROK}"
    )


def test_a_csucs_FELUL_van(kirajzolt):
    """A tájolás nem díszítés: a képtálca az ablak alján ül, a
    túlcsordulás-lista FÖLFELE nyílik (és a mérés is ezt adta — két
    egyértelmű tájolású testvér-ikonnal ellenőrizve)."""
    felso = sum(1 for x in range(13) if _festett(kirajzolt, x, 0))
    also = sum(1 for x in range(13) if _festett(kirajzolt, x, 6))
    assert felso < also, f"az ikon fejjel lefelé áll (felül {felso}, alul {also})"


def test_a_szin_a_MERT_ertek(kirajzolt):
    """A sáv mind a tizenegy ikonjának fő színe `#69729B`; ez az egyetlen,
    amiben CSAK ez az egy szín van."""
    kozep = QColor(
        kirajzolt.pixel(6 * NAGYITAS + NAGYITAS // 2, 6 * NAGYITAS + NAGYITAS // 2)
    )
    kapott = (kozep.red(), kozep.green(), kozep.blue())
    assert all(abs(a - b) <= 2 for a, b in zip(kapott, MERT_SZIN, strict=True)), (
        f"a kirajzolt szín {kapott}, a mért {MERT_SZIN}"
    )
