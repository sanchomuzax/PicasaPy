"""A „Továbbiak…" klipgyűjtő sáv gombcsoportja KÖZÉPEN áll (#3605).

A #1939 a sávot (`thumbui/single_action_container`) a kényszerek szerint
helyezte el, a tartalmát viszont a sáv JOBB széléhez kötötte. Az eredetiben
(`thumbui.tre:651–675`) a három elem egy fix, **481 × 30**-as csoportban ül
(`thumbui/single_action_group`, `m_centerXY`), és a csoport a sáv KÖZEPÉN
marad, az ablak szélesedésével nem vándorol a jobb szélre.

## A csoport belseje

```
| 2 | üzenet 335 | 9 | Vissza 109 | 3 | × 18 | 5 |   = 481
```

- a két belső rés (9 és 3) a #3582 mérése, ezek eddig is egyeztek;
- a jobb szél 5-öse a jegy 1920 px-es számából jön: a sáv 702,8 … 1900,
  a közepe 1301,4, a csoport jobb széle 1301,4 + 240,5 = 1541,9, a mért
  × jobb széle 1537 ⇒ 5 (kerekítve);
- a bal 2 a maradék: 481 − 474 − 5.

A mérés KIRAJZOLT ablakban, a módba lépve (látható sávon), két szélességen
fut: egy jobbra horgonyzott csoport csak az egyiken eshetne véletlenül középre.
"""
from __future__ import annotations

import time

from PySide6.QtCore import QPointF
from PySide6.QtQuick import QQuickItem

#: a QML geometriája tört szám lehet (a `splitX` kerekített)
TURES = 0.5
CSOPORT_SZELES = 481
BELSO_BAL = 2
BELSO_JOBB = 5
RES_UZENET_GOMB = 9
RES_GOMB_X = 3


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for it in _walk(window.contentItem()):
        if it.objectName() == nev:
            return it
    return None


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _vizszintes(elem) -> tuple[float, float]:
    """A kirajzolt (jelenet-koordinátás) bal és jobb szél.

    Az elem SAJÁT (0, 0) pontjából: a `Text` `boundingRect`-je a szöveg
    dobozát adja (jobbra igazítva eltolva), nem az elemét."""
    bal = elem.mapToScene(QPointF(0, 0)).x()
    return bal, bal + elem.width()


def _modba(window, qt_app):
    window.setProperty("backToCollagePrompted", True)
    sav = _elem(window, "traySingleActionBar")
    assert sav is not None, "nincs klipgyűjtő sáv"
    assert _var(qt_app, lambda: sav.isVisible() is True), (
        "a sáv a módba lépve sem látszik"
    )
    return sav


def _meres(window, qt_app, szelesseg: int) -> dict[str, tuple[float, float]]:
    window.setWidth(szelesseg)
    sav = _elem(window, "traySingleActionBar")
    assert _var(qt_app, lambda: abs(window.width() - szelesseg) < 1)
    qt_app.processEvents()
    return {
        nev: _vizszintes(_elem(window, nev))
        for nev in (
            "traySingleActionBar",
            "traySingleActionGroup",
            "traySingleActionMessage",
            "traySingleActionReturn",
            "traySingleActionClose",
        )
    } | {"_sav_latszik": (float(sav.isVisible()), 0.0)}


class TestACsoportKozepen:
    def test_van_481_szeles_csoport(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _modba(window, qt_app)
        csoport = _elem(window, "traySingleActionGroup")
        assert csoport is not None, (
            "nincs `single_action_group` — a három elem nem csoportban áll"
        )
        assert abs(csoport.width() - CSOPORT_SZELES) <= TURES
        assert abs(csoport.height() - 30) <= TURES

    def test_a_csoport_kozepe_a_sav_kozepe_KET_szelessegen(
        self, qml_app, qt_app,
    ):
        window, _c, _e = qml_app
        _modba(window, qt_app)
        eredeti = window.width()
        try:
            kozepek = []
            for szelesseg in (max(eredeti, 1280), max(eredeti, 1280) + 400):
                m = _meres(window, qt_app, szelesseg)
                assert m["_sav_latszik"][0] == 1.0
                sav_bal, sav_jobb = m["traySingleActionBar"]
                cs_bal, cs_jobb = m["traySingleActionGroup"]
                sav_kozep = (sav_bal + sav_jobb) / 2
                cs_kozep = (cs_bal + cs_jobb) / 2
                assert abs(cs_kozep - sav_kozep) <= TURES + 0.5, (
                    f"{szelesseg} px: a csoport közepe {cs_kozep:.1f}, "
                    f"a sávé {sav_kozep:.1f}"
                )
                kozepek.append(cs_kozep)
                # a × NEM tapad a sáv jobb széléhez
                x_jobb = m["traySingleActionClose"][1]
                assert sav_jobb - x_jobb > 100, (
                    f"{szelesseg} px: a × a sáv jobb szélénél ({x_jobb:.1f})"
                )
            # ellenpróba: a sáv bal széle 0,365 · Δ-val, a jobb Δ-val mozdul,
            # tehát a közép (1 + 0,365) / 2 · 400 = 273 px-et — egy jobbra
            # horgonyzott csoport 400-at lépne
            assert abs((kozepek[1] - kozepek[0]) - 273) <= 2
        finally:
            window.setWidth(eredeti)
            qt_app.processEvents()

    def test_a_csoport_belseje_a_mert_resekkel(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _modba(window, qt_app)
        m = _meres(window, qt_app, max(window.width(), 1280))
        cs_bal, cs_jobb = m["traySingleActionGroup"]
        u_bal, u_jobb = m["traySingleActionMessage"]
        g_bal, g_jobb = m["traySingleActionReturn"]
        x_bal, x_jobb = m["traySingleActionClose"]
        assert abs((u_bal - cs_bal) - BELSO_BAL) <= TURES
        assert abs((g_bal - u_jobb) - RES_UZENET_GOMB) <= TURES
        assert abs((x_bal - g_jobb) - RES_GOMB_X) <= TURES
        assert abs((cs_jobb - x_jobb) - BELSO_JOBB) <= TURES


class TestAKirajzoltKep:
    def test_a_sav_jobb_vege_URES(self, qml_app, qt_app):
        """Képponton: a csoporttól jobbra a sáv egyszínű háttér.

        A régi elrendezésben itt ült a × és a zöld „Vissza" gomb.
        """
        window, _c, _e = qml_app
        _modba(window, qt_app)
        eredeti = window.width()
        try:
            m = _meres(window, qt_app, max(eredeti, 1280) + 400)
            sav = _elem(window, "traySingleActionBar")
            fent = sav.mapToScene(sav.boundingRect().topLeft()).y()
            kep = window.grabWindow()
            arany = kep.width() / window.width()
            cs_jobb = m["traySingleActionGroup"][1]
            sav_jobb = m["traySingleActionBar"][1]
            y = round((fent + sav.height() / 2) * arany)
            szinek = {
                kep.pixel(round(x * arany), y)
                for x in range(int(cs_jobb) + 4, int(sav_jobb) - 4, 3)
            }
            assert len(szinek) == 1, (
                f"a sáv jobb végén {len(szinek)} szín — ott még van valami"
            )
            # pozitív kontroll: a képkocka tényleg kirajzolt, a csoportban
            # (gomb, ×) több szín is van
            cs_bal = m["traySingleActionGroup"][0]
            csoport_szinei = {
                kep.pixel(round(x * arany), y)
                for x in range(int(cs_bal) + 1, int(cs_jobb) - 1)
            }
            assert len(csoport_szinei) > 1, "a sáv nincs kirajzolva"
        finally:
            window.setWidth(eredeti)
            qt_app.processEvents()
