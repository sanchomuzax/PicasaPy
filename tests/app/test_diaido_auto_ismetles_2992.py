"""A diaidő ±1 gombja NYOMVA TARTHATÓ (#2992).

## A mérés, ami ezt kikényszerítette

Az eredeti vezérlősáv diaidő-csoportja (`oneup/dtclip`) két léptető gombot
tartalmaz, és **mindkettőn ott a `Property setautorepeat 1`**
(`picasa-create-features.md` 2/b, „A diaidő-csoport"):

| elem | méret | mi ez |
|---|---|---|
| `minusone` | 14 × 13 | −1 mp, **auto-ismétlő** |
| `tps` | 48 × 15 | a szám |
| `plusone` | 14 × 13 | +1 mp, **auto-ismétlő** |

Nálunk a két gomb megvolt, de **kattintásonként egyet** lépett: 30
másodpercre állítani 29 kattintás.

⚠️ **Az ismétlés SEBESSÉGÉT a forrás nem adja meg** — a `.tre` csak a
jelzőt (`setautorepeat 1`). A Qt alapértelmezését használjuk
(`autoRepeatDelay` 300 ms, `autoRepeatInterval` 100 ms); ez **nem mért
érték**, és a lap ezt ki is mondja.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject


def _gomb(qml_app, nev):
    window, _controller, _lib, _engine = qml_app
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"nincs ilyen elem: {nev}"
    return elem


@pytest.mark.parametrize("nev", ["slideshowTimeMinus", "slideshowTimePlus"])
def test_a_lepteto_gomb_auto_ismetlo(qml_app, nev):
    """A `setautorepeat 1` átvéve: a gomb nyomva tartva ismétel."""
    gomb = _gomb(qml_app, nev)
    assert gomb.property("autoRepeat") is True, (
        f"{nev}: az `autoRepeat` nincs bekapcsolva — nyomva tartva nem lép"
    )


@pytest.mark.parametrize("nev", ["slideshowExitButton", "slideshowStarButton"])
def test_a_TOBBI_gomb_NEM_auto_ismetlo(qml_app, nev):
    """Kontroll: az ismétlés csak a léptetőké.

    Ha az `autoRepeat` a `PicasaButton` alapértelmezésébe kerülne, ez a
    próba bukna — a kilépés vagy a csillagozás nyomva tartva ismételve
    kifejezetten káros volna."""
    assert _gomb(qml_app, nev).property("autoRepeat") is False
