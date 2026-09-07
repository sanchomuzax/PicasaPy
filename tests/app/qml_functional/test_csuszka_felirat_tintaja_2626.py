"""#2626 — a szerkesztő csúszka-feliratai a NORMÁL TINTA színét viszik.

## A mérés

A tulajdonos 2026-09-06 22:32-i A/B felvételén
(`research/felirat-ki-bekapcsolva/`, Picasa 3 és PicasaPy ugyanazon a
képen, ugyanabban a percben) a „Derítőfény" feliratra:

| | háttér (medián) | legsötétebb betű-képpont | kontraszt |
|---|---:|---:|---:|
| Picasa 3 | 231 | **47** | **184** |
| PicasaPy | 225 | **122** | **103** |

A 122 nem véletlen: a felirat a `Theme.textGray`-t vitte, ami világos
témában `#7a776f` (luminancia ≈ 120).

## Amit ez az őr állít

A felirat legsötétebb képpontjának kontrasztja a panel hátteréhez képest
legalább **150** — a mért 184 alatt (nem kötjük magunkat a JPEG-ből
olvasott pontos értékhez), a mai 103 fölött.

⚠️ A pontos EREDETI szín nincs kimérve: a 47 élsimított, tömörített
betű-képpontból jön, tehát alsó becslés. Az állítás ezért nem „legyen
`#2f2f2f`", hanem „legyen a normál tinta, ne a másodlagos szürke".
"""

from __future__ import annotations

import time

import numpy as np
from PySide6.QtCore import QObject

#: A mért kontraszt az eredetin 184, nálunk 103 volt — a küszöb a kettő közt.
MIN_KONTRASZT = 150


def _nyisd_a_szerkesztot(window, qt_app):
    window.setProperty("viewerOpen", True)
    nezo = window.findChild(QObject, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    for _ in range(40):
        qt_app.processEvents()
        time.sleep(0.01)
    return nezo


def _doboz(elem):
    sarok = elem.mapToScene(elem.boundingRect().topLeft())
    return (
        int(round(sarok.x())),
        int(round(sarok.y())),
        int(round(elem.width())),
        int(round(elem.height())),
    )


def _kontraszt(kep, elem) -> tuple[float, float]:
    """(háttér-medián, legsötétebb képpont) a felirat dobozában."""
    x0, y0, sz, m = _doboz(elem)
    ertekek = []
    for dy in range(m):
        for dx in range(sz):
            szin = kep.pixelColor(x0 + dx, y0 + dy)
            ertekek.append(
                0.299 * szin.red() + 0.587 * szin.green() + 0.114 * szin.blue()
            )
    tomb = np.array(ertekek, dtype=float)
    assert tomb.size > 0, "üres felirat-doboz"
    return float(np.median(tomb)), float(tomb.min())


class TestACsuszkaFeliratKontrasztja:
    def test_a_deritofeny_felirata_NEM_halvany(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_szerkesztot(window, qt_app)
        felirat = window.findChild(QObject, "fixesFillLightLabel")
        assert felirat is not None, "nincs `fixesFillLightLabel` a felületen"
        assert felirat.property("visible"), "a felirat nem látszik"

        kep = window.grabWindow()
        assert not kep.isNull(), "az ablakot nem lehetett kirajzolni"
        hatter, legsotetebb = _kontraszt(kep, felirat)
        kontraszt = hatter - legsotetebb
        assert kontraszt >= MIN_KONTRASZT, (
            f"a csúszka-felirat kontrasztja {kontraszt:.0f} (háttér "
            f"{hatter:.0f}, legsötétebb betű {legsotetebb:.0f}) — az "
            f"eredetin 184, a küszöb {MIN_KONTRASZT} (#2626)"
        )

    def test_a_felirat_a_TINTA_tokent_hasznalja(self, qml_app, qt_app):
        """Forrás-szintű pár: a renderelt mérés megmondja, hogy elég
        sötét-e; ez azt, hogy a PROJEKT tokenjéből jön, nem beégetve."""
        window, _c, engine = qml_app
        _nyisd_a_szerkesztot(window, qt_app)
        felirat = window.findChild(QObject, "fixesFillLightLabel")
        tema = engine.singletonInstance("PicasaPy", "Theme")
        assert felirat.property("color") == tema.property("ink"), (
            "a felirat nem a `Theme.ink`-et viszi — a másodlagos szürke "
            "(`textGray`) a mérés szerint túl halvány (#2626)"
        )

    def test_a_MASODLAGOS_szurke_nem_ter_vissza(self, qml_app, qt_app):
        window, _c, engine = qml_app
        _nyisd_a_szerkesztot(window, qt_app)
        felirat = window.findChild(QObject, "fixesFillLightLabel")
        tema = engine.singletonInstance("PicasaPy", "Theme")
        assert felirat.property("color") != tema.property("textGray")
