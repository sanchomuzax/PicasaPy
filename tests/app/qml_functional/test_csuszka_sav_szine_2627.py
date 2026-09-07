"""#2627 — a csúszka SÁVJA: KIRAJZOLT képpontokon mérve.

## Miért kirajzolt őr

A testvérfájl (`test_csuszka_geometria_2627.py`) a FORRÁST nézi: benne
áll-e a `grooveThickness: 9`. Az a szám viszont semmit nem mond arról,
hogy a sáv **kilenc képpontot foglal-e a képernyőn**, és végképp semmit a
színéről. A tulajdonos szava a #2494-ből: *„A tesztednek látnia kellett
volna, nem csak kiszámolnia."*

## A mérés forrása: a respack, nem a felvétel

A jegy a tulajdonos A/B felvételéből indult, és a sávot `RGB(185,199,219)`-
nek becsülte — JPEG-tömörített, élsimított érték. A pontos számot a
bináris erőforrás adja:

    python3 tools/picasa/respack.py png \
        research/copy_Picasa_3_7/Picasa3/runtime/respack.yt <dir> \
        "scaleslider/sliderbase"

| réteg | méret | kitöltés | felső szegély | jelölők |
|---|---|---|---|---|
| `scaleslider/sliderbase` | 121 × 9 | `RGB(202,213,229)` | `RGB(154,162,174)` | `RGB(243,245,249)` az x = 5 · 60 · 115 oszlopban |
| `editslider/sliderbase` | 191 × 27 (a sáv a 8…16. sor) | ugyanaz | ugyanaz | x = 8 · 95 · 182 |

Mindkettőnél a **két vég és a pontos KÖZÉP** kap jelölőt — arányban
0,0 · 0,5 · 1,0.

## Amit ez az őr NEM állít

- a fogantyú színét és alakját (a `scaleslider/thumb` semleges szürke; a
  geometriát a #2631 mérte, a közepére vésett függőleges vonal külön jegy);
- a sötét téma értékeit: az eredetiben nincs sötét mód, a sötét pár saját
  döntés (a Theme.qml kimondja).
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPointF, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

#: A MÉRT sávmagasság (a respack rétegfejlécéből, #2631).
MERT_SAV = 9

#: A MÉRT kitöltés és szegély (`scaleslider/sliderbase`).
MERT_KITOLTES = (202, 213, 229)
MERT_SZEGELY = (154, 162, 174)

#: A jelölők helye a sáv hosszához viszonyítva.
MERT_JELOLOK = (0.0, 0.5, 1.0)

#: Mennyivel kékebb a kitöltés a pirosnál: 229 − 202 = 27. A küszöb ennél
#: alacsonyabb, hogy a raszterező ne bukjon meg rajta — de a SEMLEGES
#: szürkét (különbség 0) biztosan kizárja.
MIN_KEKESSEG = 15

_SZELES = 121
_MAGAS = 40

_KEEPALIVE: list[object] = []

#: A FOGANTYÚ bal széle az ablak koordinátáiban — a `_kep()` tölti ki.
#: #2641: a jelölőket számoló próbának tudnia kell, meddig mérhet: a
#: `value: 100` állásban a fogantyú RÁÜL a jobb szélső jelölőre.
_FOGANTYU: dict[str, float] = {}

#: ⚠️ A `grooveThickness` itt SZÁNDÉKOSAN beírt 9, nem a `MERT_SAV`
#: konstansból jön. Ha ugyanaz a szám adná a kérést és a mércét is, az
#: állítás tautológia lenne: bármit írnánk át, együtt mozdulna. Így viszont
#: a próba azt méri, amit a forrás-őr NEM tud — hogy a kért 9 képpont
#: tényleg 9 képpontot foglal a képernyőn. Hogy a szerkesztő csúszkái
#: kérik-e a 9-et, azt a `test_csuszka_geometria_2627.py` méri.
_QML = """
import QtQuick
import PicasaPy 1.0
Rectangle {
    width: %d; height: %d
    color: "#ffffff"
    PicasaSlider {
        objectName: "proba"
        anchors.centerIn: parent
        width: parent.width
        grooveThickness: 9
        handleWidth: 16
        handleHeight: 22
        handleRadius: 3
        from: 0; to: 100; value: 100
    }
}
""" % (_SZELES, _MAGAS)


def _var_a_kirajzolasra(view: QQuickView, qt_app, masodperc: float = 10.0) -> None:
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


def _kep(qt_app):
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(_QML.encode("utf-8"), QUrl())
    hibak = [hiba.toString() for hiba in component.errors()]
    assert hibak == [], hibak
    root = component.create()
    assert root is not None
    csuszka = root.findChild(object, "proba")
    assert csuszka is not None
    fogantyu = csuszka.property("handle")
    assert fogantyu is not None
    _FOGANTYU["bal"] = fogantyu.mapToScene(QPointF(0.0, 0.0)).x()
    root.setParentItem(view.contentItem())
    view.resize(_SZELES, _MAGAS)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)
    kep = view.grabWindow()
    _KEEPALIVE.extend((view, root, component))
    return kep


def _oszlop(kep, x: int) -> list[tuple[int, int, int]]:
    ki = []
    for y in range(_MAGAS):
        szin: QColor = kep.pixelColor(x, y)
        ki.append((szin.red(), szin.green(), szin.blue()))
    return ki


def _sav_sorai(kep, x: int) -> list[int]:
    """A NEM fehér sorok a megadott oszlopban — ez a sáv függőleges nyoma."""
    return [
        y for y, p in enumerate(_oszlop(kep, x)) if p != (255, 255, 255)
    ]


@pytest.fixture(scope="module")
def _rajz(qt_app):
    return _kep(qt_app)


class TestASavKirajzolodik:
    def test_a_sav_egyaltalan_latszik(self, _rajz):
        """Üres rajzon minden alábbi állítás vákuumban menne át."""
        assert _sav_sorai(_rajz, 3), (
            "a csúszka sávja ÜRESEN renderelődött — a forrás-őrök ilyenkor "
            "is zöldek maradnának"
        )


class TestASavMAGASSAGA:
    def test_a_sav_a_MERT_kilenc_keppont(self, _rajz):
        """A sáv bal harmadában (a fogantyún kívül) mérve."""
        sorok = _sav_sorai(_rajz, 3)
        magassag = max(sorok) - min(sorok) + 1
        assert magassag == MERT_SAV, (
            f"a kirajzolt sáv {magassag} képpont, a mért {MERT_SAV} "
            f"(sorok: {min(sorok)}…{max(sorok)})"
        )


class TestASavSZINE:
    """A jegy tárgya: a sáv kékes, nem semleges szürke."""

    def _kitoltes(self, kep) -> tuple[int, int, int]:
        """A sáv BELSEJE: a szegélytől és a jelölőktől távol."""
        x = _SZELES // 4
        sorok = _sav_sorai(kep, x)
        kozep = (min(sorok) + max(sorok)) // 2
        szin = kep.pixelColor(x, kozep)
        return (szin.red(), szin.green(), szin.blue())

    def test_a_kitoltes_KEKES_nem_semleges(self, _rajz):
        r, _g, b = self._kitoltes(_rajz)
        assert b - r >= MIN_KEKESSEG, (
            f"a sáv kitöltése nem kékes (B − R = {b - r}, a mérce "
            f"{MIN_KEKESSEG}); a mért eredeti {MERT_KITOLTES} → 27"
        )

    def test_a_kitoltes_a_MERT_szint_adja(self, _rajz):
        kapott = self._kitoltes(_rajz)
        elteres = max(abs(a - b) for a, b in zip(kapott, MERT_KITOLTES, strict=True))
        assert elteres <= 6, (
            f"a sáv kitöltése {kapott}, a mért {MERT_KITOLTES} "
            f"(legnagyobb csatorna-eltérés {elteres})"
        )

    def test_a_felso_szegely_SOTETEBB_a_kitoltesnel(self, _rajz):
        """A mért szegély RGB(154,162,174) — jóval sötétebb a kitöltésnél."""
        x = _SZELES // 4
        sorok = _sav_sorai(_rajz, x)
        szegely = _rajz.pixelColor(x, min(sorok))
        vilagossag = (szegely.red() + szegely.green() + szegely.blue()) / 3
        kitoltes = sum(self._kitoltes(_rajz)) / 3
        assert vilagossag < kitoltes - 15, (
            f"a felső szegély világossága {vilagossag:.0f}, a kitöltésé "
            f"{kitoltes:.0f} — a mért különbség 51"
        )


class TestAJelolok:
    """Három jelölő: a két vég és a KÖZÉP — a respackből."""

    def test_a_kozepen_VILAGOSABB_oszlop_all(self, _rajz):
        sorok = _sav_sorai(_rajz, _SZELES // 4)
        y = (min(sorok) + max(sorok)) // 2
        kozep_x = round(1 + 0.5 * (_SZELES - 3))
        kozep = _rajz.pixelColor(kozep_x, y)
        hatter = _rajz.pixelColor(_SZELES // 4, y)
        assert sum(kozep.getRgb()[:3]) > sum(hatter.getRgb()[:3]) + 30, (
            "a sáv közepén nincs világosabb jelölő — pedig a respack "
            "mindkét rétegben pontosan középre tesz egyet "
            f"(közép {kozep.getRgb()[:3]}, sáv {hatter.getRgb()[:3]})"
        )

    def test_a_KET_LATHATO_jelolo_ott_van(self, _rajz):
        """A fogantyú ALATTI részt nem mérjük — ott nem a sávot látjuk.

        ⚠️ #2641: ez a próba korábban a TELJES sort pásztázta, és három
        csoportot várt. A harmadik csoport azonban NEM a jobb szélső
        jelölő volt, hanem maga a fogantyú (a `value: 100` állásban ráül a
        jobb végre, és világosabb a sávnál) — a valódi harmadik jelölő
        eddig sem látszott. Az egyezés véletlen volt: amint a fogantyú
        közepébe vésett vonal kettévágta a fogantyú fényes foltját, négy
        csoport lett belőle. Mostantól csak a fogantyútól BALRA mérünk, és
        ott a mért kettőt (bal vég + közép) állítjuk.
        """
        sorok = _sav_sorai(_rajz, _SZELES // 4)
        y = (min(sorok) + max(sorok)) // 2
        kitoltes = sum(_rajz.pixelColor(_SZELES // 4, y).getRgb()[:3]) / 3
        hatar = int(_FOGANTYU["bal"])
        assert hatar > _SZELES // 2, (
            f"a fogantyú bal széle {hatar} — a jelölők nagy része alatta "
            "van, így ez a próba nem mérne semmit"
        )
        vilagos = [
            x
            for x in range(hatar)
            if _rajz.pixelColor(x, y) != QColor(255, 255, 255)
            and sum(_rajz.pixelColor(x, y).getRgb()[:3]) / 3 > kitoltes + 10
        ]
        csoportok = 0
        elozo = -5
        for x in vilagos:
            if x != elozo + 1:
                csoportok += 1
            elozo = x
        assert csoportok == 2, (
            f"{csoportok} jelölő-csoportot mértem a fogantyú előtt, a "
            f"respack ott kettőt ad (bal vég + közép): {vilagos}. A "
            f"harmadik, jobb szélső jelölő a fogantyú alatt van "
            f"(a mért helyek aránya: {MERT_JELOLOK})"
        )
