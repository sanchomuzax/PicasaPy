"""#2609 — a nagyítás-gombok RAJZA és SZÍNE, kirajzolt képpontokon mérve.

## Miért kirajzolt őr

A #2588 a rajz színét `#6f6f6f`-re vitte, mert a fehér ikon a világos alsó
sávon láthatatlan volt — **de a javításhoz nem készült őr**. A #2609 ezt is
pótolja: ha valaki visszaviszi a fehéret (vagy elrontja az SVG-t úgy, hogy
üresen renderelődik), ez a fájl elbukik.

⚠️ A számolt őr itt nem elég. Az SVG forrásában megnézni, hogy szerepel-e a
`#677294`, semmit nem mond arról, hogy a rajz ki is **látszik**: egy hibás
`viewBox` vagy egy elrontott `path` mellett a forrás-őr zölden menne, a
felhasználó viszont üres gombot látna. Ezért ez a fájl a két SVG-t
**kirajzoltatja** a világos króm színére, és a képpontokon mér.

## A mérés forrása — a respack, nem a felvétel

A #2609 jegy a tulajdonos A/B felvételéből olvasta ki, hogy a rajzunk nem az
eredeti, és a színt `RGB(133,143,189)`-nek becsülte (JPEG-tömörített,
élsimított érték). A pontos számot most a **bináris erőforrás** adja:

    python3 tools/picasa/respack.py png \
        research/copy_Picasa_3_7/Picasa3/runtime/respack.yt <dir> \
        "editpanel/fit_icon"

| réteg | méret | keret | tinta | kitöltés |
|---|---|---|---|---|
| `editpanel/fit_icon` | 14 × 12 | `RGB(132,146,189)` | `RGB(103,114,148)` | `RGB(195,199,213)` |
| `editpanel/1to1_icon` | 17 × 12 | `RGB(132,146,189)` | `RGB(103,114,148)` | — |

A becsült `(133,143,189)` és a mért `(132,146,189)` egy JPEG-hibahatáron
belül van — a felvétel és a bináris ugyanazt mondja.

## Amit ez az őr NEM állít

- a gombok HELYÉT és MÉRETÉT (#2564, #2311 őrei mérik);
- a csempe saját hátterét: az eredeti ikon átlátszatlan, a háttere
  `RGB(209,212,222)` / `RGB(225,227,234)`. Ezt szándékosan **nem** vesszük
  át (az eredetiben a gomb háttere adja, nálunk az alsó sáv krómja) — ezért
  a rajzot átlátszó alapon mérjük, a króm színére renderelve.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

import picasapy.app as app_csomag

_IKON_MAPPA = Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "icons"
_FIT = _IKON_MAPPA / "zoom-fit.svg"
_ACTUAL = _IKON_MAPPA / "zoom-actual.svg"

#: A világos alsó sáv krómja a tulajdonos felvételén (#2609: „háttér 248").
KROM = 248

#: A #2588 mércéje: a felvételen a mi ikonunk kontrasztja 64 volt, az
#: eredeti Picasáé ugyanott 123. A küszöb 100 — a mért érték ma 126.
MIN_KONTRASZT = 100

#: A tinta kékes: a mért `RGB(103,114,148)`-nál B − R = 45, a kereten
#: (132,146,189) B − R = 57. A küszöb bőven alatta, hogy a raszterező
#: élsimítása ne bukjon meg rajta.
MIN_KEKESSEG = 25

#: A két ikon mért mérete a respack rétegfejlécéből.
MERET = {"fit": (14, 12), "actual": (17, 12)}

_KEEPALIVE: list[object] = []

_QML = """
import QtQuick
Rectangle {{
    width: {w}; height: {h}
    color: "#f8f8f8"
    Image {{
        anchors.fill: parent
        source: "{url}"
        sourceSize.width: {w}
        sourceSize.height: {h}
        smooth: false
    }}
}}
"""


def _var_a_kirajzolasra(view: QQuickView, qt_app, masodperc: float = 10.0) -> None:
    """Két egyforma felvételre várunk (a #2494 renderelt őrének mintája)."""
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)
    elozo = None
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        mostani = view.grabWindow()
        if elozo is not None and mostani == elozo:
            return
        elozo = mostani
        time.sleep(0.01)
    qt_app.processEvents()


def _rajzold(qt_app, svg: Path, meret: tuple[int, int]):
    """A megadott SVG a króm színére renderelve, natív méretben."""
    szeles, magas = meret
    view = QQuickView()
    component = QQmlComponent(view.engine())
    component.setData(
        _QML.format(w=szeles, h=magas, url=QUrl.fromLocalFile(str(svg)).toString())
        .encode("utf-8"),
        QUrl(),
    )
    hibak = [hiba.toString() for hiba in component.errors()]
    assert hibak == [], hibak
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(szeles, magas)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)
    kep = view.grabWindow()
    _KEEPALIVE.extend((view, root, component))
    assert kep.width() >= szeles and kep.height() >= magas, (
        f"a felvétel kisebb az ikonnál: {kep.width()}x{kep.height()}"
    )
    return kep


def _keppontok(kep, meret: tuple[int, int]) -> list[list[tuple[int, int, int]]]:
    szeles, magas = meret
    sorok = []
    for y in range(magas):
        sor = []
        for x in range(szeles):
            szin = kep.pixelColor(x, y)
            sor.append((szin.red(), szin.green(), szin.blue()))
        sorok.append(sor)
    return sorok


def _vilagossag(p: tuple[int, int, int]) -> float:
    return sum(p) / 3.0


def _tinta(sorok, kuszob: float = 235.0) -> set[tuple[int, int]]:
    """Azok a képpontok, amelyek érdemben sötétebbek a krómnál."""
    return {
        (x, y)
        for y, sor in enumerate(sorok)
        for x, p in enumerate(sor)
        if _vilagossag(p) < kuszob
    }


def _belso(sorok):
    """A kereten belüli terület — a keret maga nem jel."""
    return [sor[1:-1] for sor in sorok[1:-1]]


def _jelcsoportok(sorok) -> list[list[int]]:
    """A kereten belüli, egymástól elváló tintás oszlopcsoportok."""
    belso = _belso(sorok)
    csoportok: list[list[int]] = []
    for x in range(len(belso[0])):
        van = any(_vilagossag(sor[x]) < 235.0 for sor in belso)
        if not van:
            continue
        if csoportok and csoportok[-1][-1] == x - 1:
            csoportok[-1].append(x)
        else:
            csoportok.append([x])
    return csoportok


@pytest.fixture(scope="module")
def _fit(qt_app):
    return _keppontok(_rajzold(qt_app, _FIT, MERET["fit"]), MERET["fit"])


@pytest.fixture(scope="module")
def _actual(qt_app):
    return _keppontok(_rajzold(qt_app, _ACTUAL, MERET["actual"]), MERET["actual"])


class TestLathatosag:
    """A #2588 hiányzó regresszió-őre: a rajz a világos krómon LÁTSZIK."""

    @pytest.mark.parametrize("nev", ["fit", "actual"])
    def test_a_rajz_egyaltalan_kirajzolodik(self, nev, _fit, _actual):
        sorok = _fit if nev == "fit" else _actual
        assert _tinta(sorok), (
            f"a(z) {nev} ikon ÜRESEN renderelődött — a felhasználó üres "
            "gombot látna, miközben a forrás-őrök zöldek lennének"
        )

    @pytest.mark.parametrize("nev", ["fit", "actual"])
    def test_a_kontraszt_eleri_a_mercet(self, nev, _fit, _actual):
        sorok = _fit if nev == "fit" else _actual
        legsotetebb = min(_vilagossag(p) for sor in sorok for p in sor)
        kontraszt = KROM - legsotetebb
        assert kontraszt >= MIN_KONTRASZT, (
            f"a(z) {nev} ikon kontrasztja {kontraszt:.0f}, a mérce "
            f"{MIN_KONTRASZT} (a #2588 elŐtt 64 volt, az eredetié 123)"
        )


class TestSzin:
    """A tinta KÉKES, ahogy a respack és a felvétel is mondja."""

    @pytest.mark.parametrize("nev", ["fit", "actual"])
    def test_a_tinta_kekes_nem_semleges_szurke(self, nev, _fit, _actual):
        sorok = _fit if nev == "fit" else _actual
        sotet = sorted(
            (p for sor in sorok for p in sor), key=_vilagossag
        )[: max(4, len(_tinta(sorok)) // 4)]
        kekesseg = sum(p[2] - p[0] for p in sotet) / len(sotet)
        assert kekesseg >= MIN_KEKESSEG, (
            f"a(z) {nev} ikon tintája nem kékes (B − R = {kekesseg:.0f}, a "
            f"mérce {MIN_KEKESSEG}); a mért eredeti RGB(103,114,148) → 45"
        )


class TestARajz:
    """A két rajz alakja — a respack képpontterképe szerint."""

    def test_a_fit_kulso_kerete_SZAGGATOTT(self, _fit):
        """Az eredeti keret 2 be / 1 ki; a mienk eddig tömör volt."""
        felso = _fit[0]
        tinta = [_vilagossag(p) < 235.0 for p in felso]
        valtasok = sum(1 for i in range(1, len(tinta)) if tinta[i] != tinta[i - 1])
        assert valtasok >= 4, (
            "a fit ikon felső kerete TÖMÖR (a váltások száma "
            f"{valtasok}); az eredeti 2 be / 1 ki mintát rajzol"
        )

    def test_az_actual_HAROM_jelcsoportot_rajzol(self, _actual):
        """`1` · `:` · `1` — a kereten BELÜL három, egymástól elváló oszlopcsoport."""
        csoportok = _jelcsoportok(_actual)
        assert len(csoportok) == 3, (
            f"a kereten belül {len(csoportok)} jelcsoport van, nem 3 "
            f"(`1` · `:` · `1`): {csoportok}"
        )

    def test_a_ketpont_ALACSONYABB_a_szamjegyeknel(self, _actual):
        """A középső csoport a kettőspont: két pont, nem teljes magasságú jel.

        Ez választja el az eredeti `1:1`-et a régi `||:||` rajzunktól, ahol
        mind az öt oszlopcsoport végigért. A mért eredetiben a számjegy
        hat sort tölt (y 3…8), a kettőspont kettőt (y 4 és y 7).
        """
        belso = _belso(_actual)
        csoportok = _jelcsoportok(_actual)
        assert len(csoportok) == 3, f"előbb a három csoportnak kell meglennie: {csoportok}"
        magas = [
            max(
                sum(1 for sor in belso if _vilagossag(sor[x]) < 235.0)
                for x in csoport
            )
            for csoport in csoportok
        ]
        bal, kozep, jobb = magas
        assert kozep < bal and kozep < jobb, (
            f"a kettőspont {kozep} sor magas, a két számjegy {bal} és "
            f"{jobb} — a kettőspontnak alacsonyabbnak kell lennie"
        )


class TestAForrasNemHazudik:
    """A fejléc-komment nem állíthatja többé, hogy nincs referencia."""

    @pytest.mark.parametrize("svg", [_FIT, _ACTUAL])
    def test_a_fejlec_a_respackre_hivatkozik(self, svg):
        fej = svg.read_text(encoding="utf-8").split("-->", 1)[0]
        assert "respack" in fej, (
            f"{svg.name}: a fejléc nem nevezi meg a mérés forrását"
        )
        assert "#677294" in fej, (
            f"{svg.name}: a fejléc nem mondja ki a MÉRT tintaszínt "
            "(RGB(103,114,148) = #677294)"
        )
        assert "felirat-ki-bekapcsolva" in fej, (
            f"{svg.name}: a fejléc nem hivatkozik a tulajdonos A/B "
            "felvételére (`research/felirat-ki-bekapcsolva/`), amiből a "
            "jegy elindult"
        )
