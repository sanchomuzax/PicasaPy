"""#3760: az 1:1 nagyítás elforgatott képnél túlnagyít.

## A hiba

`PhotoViewer.qml` `actualZoomFactor()`-a a `kep.paintedWidth`-et forgatott
képnél (`iniSteps % 2`) a fájl MAGASSÁGÁVAL osztotta — holott a
`Image.PreserveAspectFit` illesztés a betöltött (forgatatlan) kép saját
arányát követi, tehát a `paintedWidth` a forgatástól FÜGGETLENÜL a fájl
SZÉLESSÉGÉVEL arányos. Egy 300×500-as, 90°-kal elforgatott képnél az
„1:1" a valós 1,04-szeres helyett 1,73-szorosra nagyított.

## Miért KÉPPONTOT mérünk

A #2563 leképezés-őrei (`test_nagyitas_lekepezes_2492.py`) az `r`-t a FUTÓ
kódtól kérdezik — egy rossz `r` mellett is zöldek maradnának, ahogy a #2492
esetében is történt. Itt a próbakép bal felső sarkában egy ismert méretű
jel ül; 1:1 után a KIRAJZOLT ablakot (`grabWindow()`) fényképezzük le, és a
jel mért mérete meg a helye dönt. A jel mérete a nagyítást, a sarok a
forgatás irányát méri — a képlet egyiket sem tudja önmagával igazolni.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, Q_ARG, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _ab_modba,
    _gyerek,
    _klikk,
)

#: portré kép, jól megkülönböztethető szélesség/magasság — a próba épp
#: azt méri, hogy a kettő ne cserélődjön fel rosszul
FAJL_SZELESSEG = 300
FAJL_MAGASSAG = 500
#: a sarokjel oldala fájlképpontban (a fájl bal felső sarkában)
JEL = 40
#: a középső jel oldala — nagy nagyításnál csak a kép közepe látszik
KOZEP_JEL = 20

#: BGR színek; egymástól és a néző hátterétől is messze esnek
ALAP_A = (200, 120, 60)
ALAP_B = (60, 200, 230)
SAROK = (0, 255, 0)
KOZEP = (0, 0, 255)


def _probakep(alap) -> np.ndarray:
    kep = np.full((FAJL_MAGASSAG, FAJL_SZELESSEG, 3), alap, np.uint8)
    kep[0:JEL, 0:JEL] = SAROK
    cy, cx = FAJL_MAGASSAG // 2, FAJL_SZELESSEG // 2
    fel = KOZEP_JEL // 2
    kep[cy - fel:cy + fel, cx - fel:cx + fel] = KOZEP
    return kep


def _kepek_keszit(lib, lepesek: dict[str, int]) -> None:
    """PNG, hogy a tömörítés ne mossa el a jel szélét."""
    ini = ""
    for nev, alap in (("a.png", ALAP_A), ("b.png", ALAP_B)):
        if nev not in lepesek:
            continue
        cv2.imwrite(str(lib / nev), _probakep(alap))
        if lepesek[nev]:
            ini += f"[{nev}]\nrotate=rotate({lepesek[nev]})\n"
    (lib / ".picasa.ini").write_text(ini, encoding="utf-8")


def _var(qt_app, ms: int = 300) -> None:
    for _ in range(10):
        qt_app.processEvents()
    QTest.qWait(ms)
    for _ in range(10):
        qt_app.processEvents()


def _hivd(qt_app, obj, nev, *args):
    QMetaObject.invokeMethod(
        obj, nev, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    _var(qt_app)


def _nezo_nyit(window, qt_app):
    window.resize(1280, 1024)
    window.show()
    for _ in range(20):
        qt_app.processEvents()
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = window.findChild(QObject, "photoViewer")
    assert nezo is not None
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    _var(qt_app, 400)
    return nezo


@pytest.fixture
def nezo_app(qt_app, tmp_path):
    """Gyár: `nyit({"a.png": lépés, …})` → ablak. A lebontás a fixture
    dolga, akkor is, ha a teszt közben elbukik."""
    generatorok = []

    def nyit(lepesek):
        gen = _build_qml_app(
            qt_app, tmp_path,
            kepeket_keszit=lambda lib: _kepek_keszit(lib, lepesek),
        )
        generatorok.append(gen)
        window, _controller, _engine = next(gen)
        return window

    yield nyit
    for gen in generatorok:
        try:
            next(gen)
        except StopIteration:
            pass


# -- mérés a kirajzolt képen ---------------------------------------------


def _felvetel(window, hova) -> np.ndarray:
    """A ténylegesen kirajzolt ablak BGR tömbként, logikai képpontban."""
    kep = window.grabWindow()
    ut = hova / "felvetel.png"
    assert kep.save(str(ut))
    bgr = cv2.imread(str(ut))
    arany = window.devicePixelRatio()
    if arany != 1:
        bgr = cv2.resize(
            bgr, None, fx=1 / arany, fy=1 / arany,
            interpolation=cv2.INTER_NEAREST,
        )
    return bgr


def _keret_resz(bgr, kep_elem) -> np.ndarray:
    """A kép KERETÉNEK kivágata — a filmszalag bélyegképei ugyanezeket a
    színeket hordják, ezért a mérés csak a néző képterületén folyik."""
    keret = kep_elem.parentItem()
    doboz = keret.boundingRect()
    p0 = keret.mapToScene(doboz.topLeft())
    p1 = keret.mapToScene(doboz.bottomRight())
    x0, y0 = max(0, int(p0.x())), max(0, int(p0.y()))
    return bgr[y0:int(p1.y()), x0:int(p1.x())]


def _szin_doboz(resz, szin, hatter=None, tures: int = 40):
    """A `szin`-hez tartozó képpontok befoglaló doboza: (x, y, szél, mag).

    `hatter` megadásával a határ a két szín FELEZŐJE: nagyításkor a
    simítás átmenetet fest a jel szélére, és a fél-átmenetnél húzott
    határ adja a jel valódi kiterjedését (a szigorú tűrés befelé mérne)."""
    kep = resz.astype(int)
    elteres = np.abs(kep - np.array(szin, int)).max(axis=2)
    if hatter is None:
        maszk = elteres <= tures
    else:
        maszk = elteres < np.abs(kep - np.array(hatter, int)).max(axis=2)
    ys, xs = np.nonzero(maszk)
    if len(xs) == 0:
        return None
    return (
        int(xs.min()), int(ys.min()),
        int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1),
    )


def _kep_doboz(resz, alap):
    """A kirajzolt kép teljes doboza: az alapszín és a két jel együtt."""
    dobozok = [
        d for d in (
            _szin_doboz(resz, alap),
            _szin_doboz(resz, SAROK),
            _szin_doboz(resz, KOZEP),
        ) if d is not None
    ]
    x0 = min(d[0] for d in dobozok)
    y0 = min(d[1] for d in dobozok)
    x1 = max(d[0] + d[2] for d in dobozok)
    y1 = max(d[1] + d[3] for d in dobozok)
    return x0, y0, x1 - x0, y1 - y0


def _jel_meret_rendben(jel, oldal: int, tures: int = 1) -> bool:
    return abs(jel[2] - oldal) <= tures and abs(jel[3] - oldal) <= tures


# -- egyes nézet ---------------------------------------------------------


class TestAzEgyAzEgyForgatottKepen:
    @pytest.mark.parametrize("lepes", [1, 3], ids=["90fok", "270fok"])
    def test_1_1_nel_a_jel_valodi_meretu_es_a_forgatott_sarokban(
        self, nezo_app, qt_app, tmp_path, lepes
    ):
        """Kész-ha #1: 1:1-nél elforgatott képen is egy fájlképpont = egy
        képernyőképpont. A fájl bal felső sarkának jele 90°-nál a kép
        JOBB FELSŐ, 270°-nál a BAL ALSÓ sarkába kerül."""
        window = nezo_app({"a.png": lepes})
        nezo = _nezo_nyit(window, qt_app)
        kep = _gyerek(window, "viewerImage")
        assert kep.property("rotation") == 90 * lepes

        _hivd(qt_app, nezo, "zoomActual")

        resz = _keret_resz(_felvetel(window, tmp_path), kep)
        jel = _szin_doboz(resz, SAROK, ALAP_A)
        assert jel is not None, "a sarokjel nem látszik a kirajzolt képen"
        assert _jel_meret_rendben(jel, JEL), (
            f"a {JEL}×{JEL}-es jel kirajzolva {jel[2]}×{jel[3]} — "
            "az 1:1 nem egy fájlképpont = egy képernyőképpont"
        )
        kx, ky, kszel, kmag = _kep_doboz(resz, ALAP_A)
        assert abs(kszel - FAJL_MAGASSAG) <= 1, (kszel, kmag)
        assert abs(kmag - FAJL_SZELESSEG) <= 1, (kszel, kmag)

        jx, jy, jszel, jmag = jel
        if lepes == 1:
            assert abs((jx + jszel) - (kx + kszel)) <= 1, "nem a jobb szélen"
            assert abs(jy - ky) <= 1, "nem a felső szélen"
        else:
            assert abs(jx - kx) <= 1, "nem a bal szélen"
            assert abs((jy + jmag) - (ky + kmag)) <= 1, "nem az alsó szélen"

    @pytest.mark.parametrize("lepes", [1, 3], ids=["90fok", "270fok"])
    def test_a_400_szazalek_is_a_valodi_meret_negyszerese(
        self, nezo_app, qt_app, tmp_path, lepes
    ):
        """Regresszió-őr a csúszka felső végére — ugyanaz a `r`-hiba a
        400 %-os végállást is elrontaná. A kép itt nem fér ki; a közepén
        ülő jelet mérjük."""
        window = nezo_app({"a.png": lepes})
        nezo = _nezo_nyit(window, qt_app)
        kep = _gyerek(window, "viewerImage")

        _hivd(qt_app, nezo, "setZoomValue", 1.0)

        resz = _keret_resz(_felvetel(window, tmp_path), kep)
        jel = _szin_doboz(resz, KOZEP, ALAP_A)
        assert jel is not None, "a középső jel nem látszik"
        vart = 4 * KOZEP_JEL
        assert _jel_meret_rendben(jel, vart, tures=2), (
            f"a {KOZEP_JEL}×{KOZEP_JEL}-es jel 400 %-on {jel[2]}×{jel[3]}, "
            f"nem {vart}×{vart}"
        )


class TestForgatasNelkulValtozatlan:
    def test_forgatas_nelkul_a_kepponthoz_valtozatlan(
        self, nezo_app, qt_app, tmp_path
    ):
        """Kész-ha #2: forgatás nélkül a régóta zöld #2492-viselkedés nem
        romolhat el — a jel a bal felső sarokban, valódi méretben."""
        window = nezo_app({"a.png": 0})
        nezo = _nezo_nyit(window, qt_app)
        kep = _gyerek(window, "viewerImage")
        assert kep.property("rotation") == 0

        _hivd(qt_app, nezo, "zoomActual")

        resz = _keret_resz(_felvetel(window, tmp_path), kep)
        jel = _szin_doboz(resz, SAROK, ALAP_A)
        assert jel is not None
        assert _jel_meret_rendben(jel, JEL), jel
        kx, ky, kszel, kmag = _kep_doboz(resz, ALAP_A)
        assert abs(kszel - FAJL_SZELESSEG) <= 1, (kszel, kmag)
        assert abs(kmag - FAJL_MAGASSAG) <= 1, (kszel, kmag)
        assert abs(jel[0] - kx) <= 1 and abs(jel[1] - ky) <= 1


# -- kettős nézet --------------------------------------------------------


class TestKettosNezetForgatottKeppel:
    """Kettős (`ab`) nézetben a fókuszos fél képére szól az 1:1 (#3741) —
    mindkét forgatás-párral és mindkét fókusszal (a fókuszt a VALÓDI
    `viewerSwapFocus` gombra kattintva váltjuk)."""

    @pytest.mark.parametrize(
        "lepes_a,lepes_b", [(1, 3), (3, 1)], ids=["a90_b270", "a270_b90"])
    @pytest.mark.parametrize("oldal", ["jobb", "bal"])
    def test_1_1_a_fokuszos_fel_kepere(
        self, nezo_app, qt_app, tmp_path, lepes_a, lepes_b, oldal
    ):
        window = nezo_app({"a.png": lepes_a, "b.png": lepes_b})
        nezo = _ab_modba(window, qt_app)
        # #3773: az alapfókusz a bal — a jobbhoz egy kattintással váltunk.
        # ⚠️ A BAL oldalon (a próba előtti #3773 óta az alapfókusz) egy
        # ODA-VISSZA kattintás kell: mérve, hogy a `photoElotte` (bal)
        # `paintedWidth`-je HIBÁS marad (a kerete teljes magasságára nyúlik,
        # a helyes szélesség-illesztés helyett), ha az `aktivOldal` a
        # belépés óta egyszer sem változott — az `onAktivOldalChanged`
        # (`Qt.callLater(viewer.clampPan)` + `beginEditCurrent()`) adja meg
        # azt a plusz réteg-újraszámolást, ami a mérethez kell. Önmagában
        # több `processEvents()`/`qWait()` ezt NEM pótolja (kipróbálva).
        # A JOBB oldal ezt mindig megkapja az egyetlen fókuszváltó
        # kattintástól, a BAL-nak ezért kettő kell (oda-vissza), hogy a
        # kijelölt oldal a próba szerint BAL maradjon.
        _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        if oldal == "bal":
            _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == oldal
        kep = _gyerek(
            window, "viewerImageElotte" if oldal == "bal" else "viewerImage")
        assert kep.property("rotation") in (90, 270)

        _hivd(qt_app, nezo, "zoomActual")

        # a fél kerete egyetlen képet mutat — a nagyobb színfolt dönti el, melyiket
        resz = _keret_resz(_felvetel(window, tmp_path), kep)
        alap = max(
            (ALAP_A, ALAP_B),
            key=lambda szin: (_szin_doboz(resz, szin) or (0, 0, 0, 0))[3],
        )
        _kx, _ky, kszel, kmag = _kep_doboz(resz, alap)
        assert abs(kmag - FAJL_SZELESSEG) <= 1, (
            f"a fókuszos fél képe {kszel}×{kmag} — 1:1-nél a forgatott "
            f"kép magassága a fájl szélessége ({FAJL_SZELESSEG})"
        )
        # 1:1-nél az 500 képpont széles kép szélesebb a félnél, tehát
        # vízszintesen levágódhat — a jel FÜGGŐLEGES mérete teljes
        jel = _szin_doboz(resz, SAROK, alap)
        assert jel is not None, "a sarokjel nem látszik a fókuszos félen"
        assert abs(jel[3] - JEL) <= 1 and jel[2] <= JEL + 1, jel
        assert nezo.property("zoomFactor") == pytest.approx(1.037, abs=0.005)
