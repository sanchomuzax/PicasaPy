"""#3729 — az alsó sáv nagyító-csúszkája a MÉRT `scaleslider` geometriával.

A #3709 (PR #3724) képes összevetése a tulajdonos 1920 px-es
képernyőképével a hatókörön kívül ezt találta: a `traySizeSlider` (könyvtár
mód) és a `zoomSlider` (néző mód) a `PicasaSlider` ALAPÉRTÉKÉVEL rajzol (4
képpontos sín, kerek 14×14 fogantyú), miközben a `respack.yt`
`scaleslider/sliderbase` 9 képpont vastag, a `scaleslider/thumb` pedig álló
16×22-es (`docs/specs/ui-audit-editor.md` 7.5, és az `EditorSlider.qml`
`scaleCsalad` ága, ami ugyanezt a mérést már alkalmazza a szerkesztő
paneljein).

Mindkét csúszka a `TrayBar.qml` `trayZoomGroup`-jának a TARTALMA — egy sáv,
módonként cserélt tartalommal (ld. a `TrayBar.qml` #2564 kommentjét), tehát
a két módnak UGYANAZT a geometriát kell mutatnia, különben a néző
megnyitásakor/bezárásakor a fogantyú láthatóan ugrana.

A `TestAKirajzoltKep` a `grabWindow()` KÉPÉN méri a sávot és a fogantyút,
ugyanazzal a módszerrel, mint a #3709 `TestAKirajzoltKep`-je. A mérce a
tulajdonos 1920 px-es képernyőképe
(`research/testdata/screenshot/Képernyőkép 2026-07-18 150933.png`), a
kapcsolósáv (`trayMetadataGroup`) felső keretsorához mérve:

| mi | a képernyőképen | a keretsortól |
|---|---|---|
| a kapcsolósáv felső keretsora | y 947 | 0 |
| a fogantyú rajzának felső sora | y 949 | **+2** |
| a sáv (`scaleslider/sliderbase`, 9 sor) | y 954 … 962 | **+7** … **+15** |
| ebből a háttértől > 30-cal eltérő sorok | 954 … 958, 960 | +7 … +13 |

Az eredeti sávja CSÍKOS (a 959-es belső sor és a 961–962-es alja alig tér
el a háttértől), a mienk egyszínű — ezért a teszt a sáv TETEJÉT és a
kiterjedését (7–9 sor) méri, a folytonosságát nem.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPointF


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.005)
    return False


class TestAKonyvtariCsuszkaGeometriaja:
    """`traySizeSlider` — a könyvtár-mód bélyegkép-mérete csúszkája."""

    def test_a_sav_9_kepponton_a_fogantyu_16x22(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        csuszka = _elem(window, "traySizeSlider")
        assert csuszka.property("grooveThickness") == 9
        assert csuszka.property("handleWidth") == 16
        assert csuszka.property("handleHeight") == 22
        assert csuszka.property("handleRadius") == 3

    def test_a_foglalat_szelessege_valtozatlan_127(self, qml_app_module, qt_app):
        """A javításnak a #3709/#3602 mért réseit NEM szabad elmozdítania."""
        window, _, _ = qml_app_module
        csuszka = _elem(window, "traySizeSlider")
        assert csuszka.property("width") == 127
        assert csuszka.property("grooveInset") == 3


class TestANezoCsuszkaGeometriaja:
    """`zoomSlider` — a néző-mód nagyítás-hármasának csúszkája.

    Ugyanaz a `scaleslider` család, mint a könyvtári csúszkáé (mindkettő a
    `respack.yt` `scaleslider/sliderbase`+`thumb` párjára mutat vissza) —
    a fogantyúnak a két mód közt NEM szabad ugrálnia.
    """

    def test_a_sav_9_kepponton_a_fogantyu_16x22(self, qml_app, qt_app):
        window, _, _ = qml_app
        window.setProperty("viewerOpen", True)
        nezo = _elem(window, "photoViewer")
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert _var(
            qt_app, lambda: _elem(window, "zoomSlider").property("visible")
        )
        csuszka = _elem(window, "zoomSlider")
        assert csuszka.property("grooveThickness") == 9
        assert csuszka.property("handleWidth") == 16
        assert csuszka.property("handleHeight") == 22
        assert csuszka.property("handleRadius") == 3


#: Két ablakszélesség: a referenciakép 1920-a és egy keskenyebb.
ABLAKOK = (1280, 1920)

#: Ennyivel kell eltérnie egy képpontnak (a három csatorna összegében) a
#: sáv hátterétől, hogy rajznak számítson — a #3603/#3709 mércéje.
ELKULONBSEG = 30

#: A keretvonal a cella kitöltésénél is jóval sötétebb (#3709).
KERET_SOTETSEG = 120


def _kep(window, qt_app, szelesseg: int):
    window.setProperty("width", szelesseg)
    window.setProperty("height", 1030)
    for _ in range(10):
        qt_app.processEvents()
    return window.grabWindow()


def _osszeg(kep, x: int, y: int) -> int:
    szin = kep.pixelColor(x, y)
    return szin.red() + szin.green() + szin.blue()


def _keret_teteje(window, kep, szel: int) -> int:
    """A kapcsolósáv felső keretsora a KÉPEN (a #3709 szerint a cella 1.
    sora; itt nem feltételezzük, hanem megkeressük)."""
    csoport = _elem(window, "trayMetadataGroup")
    teteje = round(csoport.mapToScene(QPointF(0, 0)).y())
    x = szel - 247
    hatter = _osszeg(kep, x, teteje - 3)
    sorok = [
        y for y in range(teteje - 3, teteje + 28)
        if hatter - _osszeg(kep, x, y) > KERET_SOTETSEG
    ]
    assert sorok, "a kapcsolósáv kerete nem rajzolódott ki"
    return sorok[0]


def _rajzolt_sorok(kep, x: int, keret: int, hatter: int) -> list[int]:
    """A keretsortól lefelé azok a sorok, amelyek a háttértől eltérnek.

    A keretsor FÖLÖTT nem keresünk: az eredetiben ott (y 943) a sáv felső
    szegélye fut, ami rajznak számítana."""
    return [
        y for y in range(keret, keret + 26)
        if abs(_osszeg(kep, x, y) - hatter) > ELKULONBSEG
    ]


def _meres(window, kep, szel: int, nev: str) -> tuple[list[int], int]:
    """(a sáv sorai, a fogantyú legfelső sora) a keretsorhoz képest."""
    keret = _keret_teteje(window, kep, szel)
    csuszka = _elem(window, nev)
    foglalat = csuszka.mapToScene(QPointF(0, 0)).x()
    fogantyu = csuszka.property("handle")
    fx = fogantyu.mapToScene(QPointF(0, 0)).x() - foglalat
    # a sávot a fogantyútól TÁVOLI oszlopban mérjük (a jelölővonalakat is
    # kerülve: azok a rajzolt sáv 1., 60. és 119. oszlopában állnak)
    sav_x = round(foglalat + (110 if fx < 60 else 13))
    # a háttér a sáv oszlopában, a keretsor alatt 3-mal: ott sem a sáv, sem
    # a fogantyú nem rajzol
    hatter = _osszeg(kep, sav_x, keret + 3)
    sav = [y - keret for y in _rajzolt_sorok(kep, sav_x, keret, hatter)]
    # a fogantyú rajzának 5. oszlopa: a lekerekített sarkon belül, a
    # középre vésett vonaltól balra
    fogantyu_x = round(foglalat + fx + 4)
    fogantyu_sorai = _rajzolt_sorok(kep, fogantyu_x, keret, hatter)
    assert fogantyu_sorai, "a fogantyú nem rajzolódott ki"
    teteje = fogantyu_sorai[0] - keret
    return sav, teteje


def _ellenoriz(sav: list[int], teteje: int, hol: str) -> None:
    assert sav and sav[0] == 7, (
        f"{hol}: a sáv a keretsor +{sav[0] if sav else '?'}. sorában "
        f"kezdődik ({sav}), az eredetiben +7-ben"
    )
    vastagsag = sav[-1] - sav[0] + 1
    assert 7 <= vastagsag <= 9, (
        f"{hol}: a sáv {vastagsag} sor vastag ({sav}), az eredetiben 7–9 "
        "(a 9 soros réteg halvány alja a küszöb alá eshet)"
    )
    assert teteje == 2, (
        f"{hol}: a fogantyú teteje a keretsor +{teteje}. sorában, az "
        "eredetiben +2-ben (a sáv fölött 5 sorral)"
    )


class TestAKirajzoltKep:
    """A `grabWindow()` képén keresett sorok a képernyőkép számaival."""

    @pytest.mark.parametrize("szel", ABLAKOK)
    def test_konyvtar_mod(self, qml_app_module, qt_app, szel):
        window, _, _ = qml_app_module
        kep = _kep(window, qt_app, szel)
        sav, teteje = _meres(window, kep, szel, "traySizeSlider")
        _ellenoriz(sav, teteje, f"könyvtár, {szel} px")

    def test_nezo_mod(self, qml_app, qt_app):
        window, _, _ = qml_app
        window.setProperty("viewerOpen", True)
        _elem(window, "photoViewer").setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert _var(
            qt_app, lambda: _elem(window, "zoomSlider").property("visible")
        )
        for szel in ABLAKOK:
            kep = _kep(window, qt_app, szel)
            sav, teteje = _meres(window, kep, szel, "zoomSlider")
            _ellenoriz(sav, teteje, f"néző, {szel} px")


class TestANezoSavjaBeljebbAll:
    """A `zoomSlider` rajzolt sávja is 3 képponttal beljebb áll, mint a
    könyvtári csúszkáé — különben a sáv vége a módváltáskor ugrana."""

    def test_a_behuzas_3(self, qml_app, qt_app):
        window, _, _ = qml_app
        window.setProperty("viewerOpen", True)
        _elem(window, "photoViewer").setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert _var(
            qt_app, lambda: _elem(window, "zoomSlider").property("visible")
        )
        csuszka = _elem(window, "zoomSlider")
        assert csuszka.property("grooveInset") == 3
        assert csuszka.property("background").x() == 3
        assert csuszka.property("background").width() == 121
