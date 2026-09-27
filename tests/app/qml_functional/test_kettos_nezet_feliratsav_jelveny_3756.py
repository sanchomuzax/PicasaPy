"""#3756: kettős nézetben BAL fókusznál a „Selected" jelvény a felső
sávra csúszott, a feliratsáv (a kék infó-sáv, `TrayBar.qml`) és a csillag
gomb pedig a JOBB kép adatait mutatta / arra hatott, nem a kijelöltre.

## A jelvény (`viewerFocusBadge`)

A #3663 mérése négyzetes próbaképekkel igazolta a jelvény helyét — de
négyzetes képnél a fél letterbox-margója bőven elég a jelvénynek, tehát a
hiba nem látszott. ÁLLÓ képnél (`test_kettos_nezet_fokusz_nagyitas_3741.py`
`_kepek`: `b.jpg` 300×500) a bal fél a magasságra illesztve tölti ki a
rekeszt, a felső margó 0, és a jelvény a `viewerTopBar` sávjába lógott
(mérve a javítás előtt, 1280×1024: a jelvény 41…67 px, a felső sáv
34…80 px). Függőleges elrendezésben SZÉLES képnél ugyanígy a bal
eszközpanelre került.

A mérce MINDEN képaránynál a #3663 mért rése a KIRAJZOLT képhez képest:
a képek síkjával párhuzamos tengelyen ~61 px, a merőlegesen ~27 px. Ehhez a
kettős nézet mindkét fele fenntartja a jelvény helyét (vízszintesen felül
26 + 27 px, függőlegesen balra 86 + 61 px) — ha a kép saját margója ennél
kisebb volna. A próbák ezért:

* a jelvény helyét a kirajzolt képhez mérik álló, négyzetes és széles
  képen, mindkét elrendezésben;
* állítják, hogy a jelvény egyik kirajzolt képet sem metszi, nem lóg a
  felső sávba, és nem megy ki a fotóterületből (a bal panelre);
* a KIRAJZOLT ablakon (`grabWindow`) megnézik, hogy a jelvény helyén
  valóban a jelvény szürkéje (`#666666`) látszik.

## A feliratsáv és a csillag

A tálca `viewerIndex`-e a néző KIJELÖLT sorát (`aktivSor`) követi, nem a
`currentIndex`-et (az mindig a jobb/alsó félé). A próbák a sáv szövegében
a kijelölt kép nevét, dátumát, méretét és sorszámát nézik, és a csillag
gombra VALÓDI kattintással a kijelölt kép kap csillagot (#3014: a parancsok
a kijelölt oldalra hatnak).
"""

from __future__ import annotations

import os
import time

import cv2
import numpy as np
import pytest
from PySide6.QtTest import QTest
from support.qt_wait import wait_for_photo_op

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_kettos_nezet_fokusz_nagyitas_3741 import (
    NARANCS,
    ZOLD,
    _kepek,
)
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    MEROLEGES_RES,
    PARHUZAMOS_RES,
    TURES_MEROLEGES,
    TURES_PARHUZAMOS,
    _ab_modba,
    _elem_teglalap,
    _gyerek,
    _kep_teglalap,
    _klikk,
)

#: a jelvény színe (`Theme.viewerFocusBadgeBg`)
JELVENY_SZURKE = (0x66, 0x66, 0x66)
#: a `b.jpg` módosítási ideje — a sáv dátumából ez különbözteti meg
B_EVE = 2001
#: a `PreserveAspectFit` a festett méretet egész képpontra kerekíti — a
#: határ-állítások ennyi (fél képpontnyi) elcsúszást engednek meg
KEREKITES = 1.0


def _allo_kepek(lib) -> None:
    """`a.jpg` 640×400 (jobb), `b.jpg` 300×500 ÁLLÓ (bal) — a `b.jpg`
    dátuma szándékosan más évre esik, hogy a sáv dátuma is megkülönböztető
    legyen."""
    _kepek(lib)
    regi = time.mktime((B_EVE, 2, 3, 4, 5, 6, 0, 0, -1))
    os.utime(lib / "b.jpg", (regi, regi))


def _szeles_kepek(lib) -> None:
    """Két panoráma: `a.jpg` 2000×300 (alsó), `b.jpg` 2400×300 (felső) —
    függőleges elrendezésben a fél teljes szélességét kitöltenék."""
    a = np.full((300, 2000, 3), ZOLD[::-1], np.uint8)
    b = np.full((300, 2400, 3), NARANCS[::-1], np.uint8)
    cv2.imwrite(str(lib / "a.jpg"), a, [cv2.IMWRITE_JPEG_QUALITY, 98])
    cv2.imwrite(str(lib / "b.jpg"), b, [cv2.IMWRITE_JPEG_QUALITY, 98])


@pytest.fixture
def allo_kep(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_allo_kepek)


@pytest.fixture
def szeles_kep(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_szeles_kepek)


# -- segédek ---------------------------------------------------------------


def _elrendez(window, qt_app, *, oldal: str, fuggoleges: bool):
    window.resize(1280, 1024)
    window.show()
    for _ in range(20):
        qt_app.processEvents()
    nezo = _ab_modba(window, qt_app)
    if fuggoleges:
        _klikk(qt_app, window, _gyerek(window, "viewerSwapLayout"))
        assert nezo.property("fuggolegesElrendezes") is True
    if oldal == "bal":
        _klikk(qt_app, window, _gyerek(window, "viewerImageElotte"))
    assert nezo.property("aktivOldal") == oldal
    for _ in range(10):
        qt_app.processEvents()
    QTest.qWait(200)
    return nezo


def _meres(window, oldal: str) -> dict:
    fokusz = "viewerImageElotte" if oldal == "bal" else "viewerImage"
    return {
        "kep": _kep_teglalap(_gyerek(window, fokusz)),
        "bal_kep": _kep_teglalap(_gyerek(window, "viewerImageElotte")),
        "jobb_kep": _kep_teglalap(_gyerek(window, "viewerImage")),
        "jelveny": _elem_teglalap(_gyerek(window, "viewerFocusBadge")),
        "felso_sav": _elem_teglalap(_gyerek(window, "viewerTopBar")),
        "terulet": _elem_teglalap(_gyerek(window, "viewerPhotoArea")),
    }


def _metszi(a: dict, b: dict) -> bool:
    return (a["bal"] < b["jobb"] and b["bal"] < a["jobb"]
            and a["fent"] < b["lent"] and b["fent"] < a["lent"])


def _res(m: dict, oldal: str, fuggoleges: bool) -> tuple[float, float]:
    """(párhuzamos, merőleges) rés a kirajzolt kép és a jelvény között."""
    kep, j = m["kep"], m["jelveny"]
    if fuggoleges:
        merol = kep["lent"] - j["lent"] if oldal == "bal" else j["fent"] - kep["fent"]
        return kep["bal"] - j["jobb"], merol
    parh = kep["jobb"] - j["jobb"] if oldal == "bal" else j["bal"] - kep["bal"]
    return parh, kep["fent"] - j["lent"]


def _jelveny_ellenorzes(window, qt_app, *, oldal: str, fuggoleges: bool):
    m = _meres(window, oldal)
    j = m["jelveny"]
    parh, merol = _res(m, oldal, fuggoleges)
    leiras = f"jelvény {j}, kép {m['kep']}"
    assert abs(parh - PARHUZAMOS_RES) <= TURES_PARHUZAMOS, (
        f"párhuzamos rés {parh:.1f} px (mérce {PARHUZAMOS_RES}±"
        f"{TURES_PARHUZAMOS}) — {leiras}"
    )
    assert abs(merol - MEROLEGES_RES) <= TURES_MEROLEGES, (
        f"merőleges rés {merol:.1f} px (mérce {MEROLEGES_RES}±"
        f"{TURES_MEROLEGES}) — {leiras}"
    )
    for nev in ("bal_kep", "jobb_kep"):
        assert not _metszi(j, m[nev]), f"a jelvény rálóg a {nev}-re — {leiras}"
    assert j["fent"] >= m["felso_sav"]["lent"] - KEREKITES, (
        f"a jelvény a felső sávba lóg ({j['fent']:.0f} < "
        f"{m['felso_sav']['lent']:.0f})"
    )
    assert j["bal"] >= m["terulet"]["bal"] - KEREKITES, (
        f"a jelvény kilóg a fotóterületből a bal panelre ({j['bal']:.0f} < "
        f"{m['terulet']['bal']:.0f})"
    )
    _jelveny_latszik(window, qt_app, j)


def _jelveny_latszik(window, qt_app, j: dict) -> None:
    """A KIRAJZOLT ablakon a jelvény két szélén (a felirat mellett) a
    jelvény szürkéje látszik — nem a kép, nem a felső sáv."""
    for _ in range(10):
        qt_app.processEvents()
    QTest.qWait(200)
    kep = window.grabWindow()
    kozep_y = (j["fent"] + j["lent"]) / 2
    for x in (j["bal"] + 8, j["jobb"] - 8):
        c = kep.pixelColor(int(round(x)), int(round(kozep_y)))
        szin = (c.red(), c.green(), c.blue())
        assert all(abs(a - b) <= 12 for a, b in zip(szin, JELVENY_SZURKE,
                                                     strict=True)), (
            f"a jelvény helyén ({x:.0f}, {kozep_y:.0f}) {szin} látszik, "
            f"nem a jelvény szürkéje {JELVENY_SZURKE}"
        )


# -- a jelvény ---------------------------------------------------------------


class TestAJelvenyVizszintesen:
    def test_allo_kep_bal_fokusz(self, allo_kep, qt_app):
        window = allo_kep[0]
        _elrendez(window, qt_app, oldal="bal", fuggoleges=False)
        _jelveny_ellenorzes(window, qt_app, oldal="bal", fuggoleges=False)

    def test_allo_kep_jobb_fokusz(self, allo_kep, qt_app):
        window = allo_kep[0]
        _elrendez(window, qt_app, oldal="jobb", fuggoleges=False)
        _jelveny_ellenorzes(window, qt_app, oldal="jobb", fuggoleges=False)

    def test_negyzetes_kep_bal_fokusz(self, qml_app_negyzet_kepek, qt_app):
        window = qml_app_negyzet_kepek[0]
        _elrendez(window, qt_app, oldal="bal", fuggoleges=False)
        _jelveny_ellenorzes(window, qt_app, oldal="bal", fuggoleges=False)

    def test_negyzetes_kep_jobb_fokusz(self, qml_app_negyzet_kepek, qt_app):
        window = qml_app_negyzet_kepek[0]
        _elrendez(window, qt_app, oldal="jobb", fuggoleges=False)
        _jelveny_ellenorzes(window, qt_app, oldal="jobb", fuggoleges=False)


class TestAJelvenyFuggolegesen:
    def test_szeles_kep_felso_fokusz(self, szeles_kep, qt_app):
        window = szeles_kep[0]
        _elrendez(window, qt_app, oldal="bal", fuggoleges=True)
        _jelveny_ellenorzes(window, qt_app, oldal="bal", fuggoleges=True)

    def test_szeles_kep_also_fokusz(self, szeles_kep, qt_app):
        window = szeles_kep[0]
        _elrendez(window, qt_app, oldal="jobb", fuggoleges=True)
        _jelveny_ellenorzes(window, qt_app, oldal="jobb", fuggoleges=True)

    def test_negyzetes_kep_felso_fokusz(self, qml_app_negyzet_kepek, qt_app):
        window = qml_app_negyzet_kepek[0]
        _elrendez(window, qt_app, oldal="bal", fuggoleges=True)
        _jelveny_ellenorzes(window, qt_app, oldal="bal", fuggoleges=True)


class TestANegyzetesKepHelyeValtozatlan:
    """A #3663 mért elrendezése négyzetes képnél változatlan: ha a kép saját
    margója elég, a jelvény helyfoglalása nem mozdít a képen — a kép a saját
    keretének KÖZEPÉN áll (a main-en mért viselkedés), a jelvény pedig a mért
    61/27 px-es résre kerül. Abszolút koordinátát a teszt nem vár: a
    fotóterület magassága a betűkészlettől függ (a CI DejaVu betűjével 2,5 px-
    szel más, mint helyben), a középre állás és a rés viszont nem."""

    @staticmethod
    def _kozepen(kep: dict, keret: dict) -> None:
        assert abs((kep["fent"] - keret["fent"]) - (keret["lent"] - kep["lent"])) <= 1.0, (kep, keret)
        assert abs((kep["bal"] - keret["bal"]) - (keret["jobb"] - kep["jobb"])) <= 1.0, (kep, keret)

    def test_vizszintes(self, qml_app_negyzet_kepek, qt_app):
        window = qml_app_negyzet_kepek[0]
        _elrendez(window, qt_app, oldal="bal", fuggoleges=False)
        m = _meres(window, "bal")
        self._kozepen(m["bal_kep"], _elem_teglalap(_gyerek(window, "viewerImageElotteKeret")))
        self._kozepen(m["jobb_kep"], _elem_teglalap(_gyerek(window, "viewerImageKeret")))
        assert m["bal_kep"]["fent"] == m["jobb_kep"]["fent"]
        parh, merol = _res(m, "bal", fuggoleges=False)
        assert abs(parh - 61) <= 1 and abs(merol - 27) <= 1, (parh, merol)

    def test_fuggoleges(self, qml_app_negyzet_kepek, qt_app):
        window = qml_app_negyzet_kepek[0]
        _elrendez(window, qt_app, oldal="bal", fuggoleges=True)
        m = _meres(window, "bal")
        self._kozepen(m["bal_kep"], _elem_teglalap(_gyerek(window, "viewerImageElotteKeret")))
        parh, merol = _res(m, "bal", fuggoleges=True)
        assert abs(parh - 61) <= 1 and abs(merol - 27) <= 1, (parh, merol)


# -- a feliratsáv és a csillag -------------------------------------------------


class TestAFeliratsavAKijeloltKepetKoveti:
    def _szoveg(self, window) -> str:
        return _gyerek(window, "trayInfoText").property("nyersSzoveg")

    def test_bal_fokusznal_a_bal_kep_adatai(self, allo_kep, qt_app):
        window = allo_kep[0]
        _elrendez(window, qt_app, oldal="bal", fuggoleges=False)
        szoveg = self._szoveg(window)
        assert "b.jpg" in szoveg and "a.jpg" not in szoveg, szoveg
        assert str(B_EVE) in szoveg, f"nem a kijelölt kép dátuma: {szoveg!r}"
        assert "300x500 pixels" in szoveg, szoveg
        assert "(2 / 2)" in szoveg, szoveg

    def test_jobb_fokusznal_a_jobb_kep_adatai(self, allo_kep, qt_app):
        window = allo_kep[0]
        _elrendez(window, qt_app, oldal="jobb", fuggoleges=False)
        szoveg = self._szoveg(window)
        assert "a.jpg" in szoveg and "b.jpg" not in szoveg, szoveg
        assert str(B_EVE) not in szoveg, szoveg
        assert "640x400 pixels" in szoveg, szoveg
        assert "(1 / 2)" in szoveg, szoveg

    def test_gombbal_valtott_fokuszt_is_koveti(self, allo_kep, qt_app):
        window = allo_kep[0]
        nezo = _elrendez(window, qt_app, oldal="jobb", fuggoleges=False)
        _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == "bal"
        szoveg = self._szoveg(window)
        assert "b.jpg" in szoveg and "300x500 pixels" in szoveg, szoveg


class TestACsillagAKijeloltKepreHat:
    def test_bal_fokusznal_a_bal_kep_kap_csillagot(self, allo_kep, qt_app):
        window, controller, _engine = allo_kep
        nezo = _elrendez(window, qt_app, oldal="bal", fuggoleges=False)
        bal_sor = nezo.property("aktivSor")
        jobb_sor = nezo.property("currentIndex")
        assert bal_sor != jobb_sor
        assert not controller.photos.starAt(bal_sor)

        gomb = _gyerek(window, "trayStarButton")
        wait_for_photo_op(
            controller, lambda: _klikk(qt_app, window, gomb), qt_app=qt_app
        )

        assert controller.photos.starAt(bal_sor), (
            "a kijelölt (bal) kép nem kapott csillagot"
        )
        assert not controller.photos.starAt(jobb_sor), (
            "a NEM kijelölt (jobb) kép kapott csillagot"
        )
