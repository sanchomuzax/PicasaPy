"""#3773: „ab" módban a bal a JELENLEGI kép, a jobb a KÖVETKEZŐ — és
belépéskor a bal a KIJELÖLT.

## A hiba (mérve a #3756 (PR #3765) átnézésekor, referencia-képekből:
`Colab EN 33` „7 of 24", `Colab EN 34` a jobb képre kattintás után
„8 of 24")

Az eredeti Picasában „ab" módba lépéskor a **bal** kép a jelenlegi
(`currentIndex`), a jobb a következő (`abMasikSor`), és a bal a
kijelölt (`aktivOldal === "bal"`, alapérték). A #3013/#3014 óta nálunk
ez fordítva állt: a bal a `abMasikSor` (következő) képet mutatta, a
jobb a `currentIndex`-et (jelenlegit), és az alapfókusz `"jobb"` volt.

Ez a lap a sorrend-cserét rögzíti: a `viewerImageElotte` (bal/felső
Item) mostantól a `currentIndex`-hez, a `viewerImage` (jobb/alsó Item)
a `abMasikSor`-hoz kötött — az `aktivSor`/`_kijeloltSort`/`_masodikSort`
képletek és az alapértelmezett `aktivOldal` ("bal") ezzel összhangban.

A #3741 (saját keretek, `balFokusz`) és a #3756 (jelvény-helyfoglalás)
viselkedése nem sérül: a `balFokusz`/`fokuszKep` a fizikai BAL/JOBB
oldalt jelöli, függetlenül attól, melyik sorszámot mutatja épp az adott
oldal — ezt a `test_kettos_nezet_atfedo_fokusz_3741.py` és a
`test_kettos_nezet_feliratsav_jelveny_3756.py` továbbra is őrzi (a
bennük szereplő alapérték-feltételezéseket ez a jegy igazította).

## A kirajzolt ablakon (a lap második fele)

A mérce a `Colab EN 33` (belépés: a kék sávon „7 of 24", a „Selected"
jelvény a BAL kép fölött) és a `Colab EN 34` (a jobb képre kattintva
„8 of 24", a jelvény a JOBB kép fölött) képernyőkép. A próbák 24 képes
mappán a 7. képnél lépnek „ab" módba — ugyanott, ahol a referencia.

Minden kép más, telített színű; a próbák a `grabWindow()` képén a két fél
KÖZEPÉNEK színéből olvassák ki, melyik kép látszik. Így a „helykitöltő"
(a szolgáltató szürke négyzete) és a „mindkét félen ugyanaz a kép" hiba
is elbukik — nem csak a sorszám-property-k.

Mérve a javítás előtt: belépéskor a bal fél a helykitöltőt mutatta (a
második vezérlő régi kulcsa kiszorította a fő vezérlő képét a két helyes
gyorsítótárból), jobb fókusznál ▶ után pedig mindkét félen ugyanaz a kép
állt (a fő vezérlő a kötött `abMasikSor` régi értékét olvasta).
"""

from __future__ import annotations

import colorsys

import cv2
import numpy as np
import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _ab_modba,
    _elem_teglalap,
    _gyerek,
    _kep_teglalap,
    _klikk,
)


class TestBelepeskorABalAJelenlegi:
    def test_a_bal_a_kijelolt_belepeskor(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("aktivOldal") == "bal", (
            "„ab” módba lépéskor a bal oldalnak kell kijelöltnek lennie"
        )

    def test_a_kijelolt_sor_a_jelenlegi_kep(self, qml_app, qt_app):
        """`aktivSor` (a kijelölt oldal sora) a belépéskori alapállapotban
        a `currentIndex`-szel kell egyezzen — ez a bal oldal tartalma."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("aktivSor") == nezo.property("currentIndex")

    def test_a_masodik_sor_a_kovetkezo_kep(self, qml_app, qt_app):
        """A NEM kijelölt (jobb) oldal sora a `abMasikSor` — ez a
        következő kép, amíg a `masodikIndex` nincs külön választva."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("abMasikSor") == nezo.property("currentIndex") + 1


class TestABalOldalASajatSzerkesztese:
    """#3187: a KIJELÖLT oldalt a FŐ szerkesztő-vezérlő rendereli (nincs
    `@masodik` rekesz-kulcs az előnézet-URL-jében), a NEM kijelöltet a
    második rekesz (`@masodik`) — ld. `test_ab_kettos_nezet_3014.py`
    `test_a_masik_oldal_a_SAJAT_rekeszen_at_jon`-ját, a #3773 óta
    FORDÍTOTT oldalhozzárendeléssel."""

    def test_a_bal_oldal_a_FO_vezerlot_kapja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        forras = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" not in forras, forras

    def test_a_jobb_oldal_a_MASODIK_rekeszt_kapja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        forras = _gyerek(window, "viewerImage").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" in forras, forras


class TestAFokuszAtviteleNemLapoz:
    """A referencia „7 of 24" → „8 of 24" a jobb képre kattintás UTÁN —
    ez a `aktivSor` (a kijelölt sor) váltása, NEM tényleges lapozás: a
    `currentIndex` a kattintás után is a régi sorban áll, csak az
    `aktivSor` mutat immár a `abMasikSor`-ra."""

    def test_jobb_kepre_kattintva_az_aktivSor_a_kovetkezot_mutatja(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        eredeti_current = nezo.property("currentIndex")
        eredeti_masik = nezo.property("abMasikSor")

        _klikk(qt_app, window, _gyerek(window, "viewerImage"))

        assert nezo.property("aktivOldal") == "jobb"
        assert nezo.property("currentIndex") == eredeti_current, (
            "a jobb képre kattintás nem lapozás — a currentIndex nem "
            "mozdulhat el"
        )
        assert nezo.property("aktivSor") == eredeti_masik


# -- a kirajzolt ablakon, a referencia mellett ------------------------------

KEPEK_SZAMA = 24
#: a referencia `Colab EN 33` a 7. képnél lép „ab" módba (0-tól számolva 6)
BELEPESI_SOR = 6
#: a #3663 mért rése a kirajzolt kép és a jelvény között
PARHUZAMOS_RES = 61
MEROLEGES_RES = 27
SZIN_TURES = 30


def _szin(sor: int) -> tuple[int, int, int]:
    """A `sor`-adik kép RGB-színe — telített, a szomszédtól távoli árnyalat."""
    arnyalat = (sor * 7 % KEPEK_SZAMA) / KEPEK_SZAMA
    r, g, b = colorsys.hsv_to_rgb(arnyalat, 0.85, 0.85)
    return int(r * 255), int(g * 255), int(b * 255)


def _kepek(lib) -> None:
    for sor in range(KEPEK_SZAMA):
        r, g, b = _szin(sor)
        kep = np.full((600, 800, 3), (b, g, r), np.uint8)
        cv2.imwrite(str(lib / f"k{sor + 1:02d}.jpg"), kep)


@pytest.fixture
def huszonnegy_kep(qt_app, tmp_path):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek)
    yield next(gen)
    try:
        next(gen)
    except StopIteration:
        pass


def _var(qt_app, ms: int = 200) -> None:
    for _ in range(10):
        qt_app.processEvents()
    QTest.qWait(ms)
    for _ in range(10):
        qt_app.processEvents()


def _ab_modba_a_7_kepnel(window, qt_app):
    window.resize(1280, 1024)
    window.show()
    _var(qt_app)
    window.setProperty("viewerOpen", True)
    nezo = _gyerek(window, "photoViewer")
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", BELEPESI_SOR)
    )
    _var(qt_app, 300)
    _klikk(qt_app, window, _gyerek(window, "viewerLayoutAb"))
    _var(qt_app, 300)
    assert nezo.property("layoutMode") == "ab"
    return nezo


def _latszo_sor(window, qt_app, nev: str) -> int | None:
    """Melyik kép látszik a fél KIRAJZOLT közepén (`None`: egyik sem —
    például a helykitöltő szürkéje)."""
    _var(qt_app)
    t = _kep_teglalap(_gyerek(window, nev))
    kep = window.grabWindow()
    c = kep.pixelColor(int((t["bal"] + t["jobb"]) / 2), int((t["fent"] + t["lent"]) / 2))
    latott = (c.red(), c.green(), c.blue())
    for sor in range(KEPEK_SZAMA):
        if all(abs(a - b) <= SZIN_TURES for a, b in zip(latott, _szin(sor), strict=True)):
            return sor
    return None


def _ket_fel(window, qt_app) -> tuple[int | None, int | None]:
    return (
        _latszo_sor(window, qt_app, "viewerImageElotte"),
        _latszo_sor(window, qt_app, "viewerImage"),
    )


def _filmszalag_elem(window, sor: int):
    film = _gyerek(window, "viewerFilmstrip")
    for elem in film.property("contentItem").childItems():
        if elem.property("racsSor") == sor:
            return elem
    raise AssertionError(f"a filmszalagon nincs {sor}. sor")


def _sav(window) -> str:
    return _gyerek(window, "trayInfoText").property("nyersSzoveg")


def _jelveny_a_kep_folott(window, oldal: str) -> None:
    """A „Selected" jelvény a kijelölt kép fölött, a mért 61/27 px-es résen."""
    nev = "viewerImageElotte" if oldal == "bal" else "viewerImage"
    kep = _kep_teglalap(_gyerek(window, nev))
    j = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))
    assert kep["bal"] < j["bal"] and j["jobb"] < kep["jobb"], (oldal, j, kep)
    parh = kep["jobb"] - j["jobb"] if oldal == "bal" else j["bal"] - kep["bal"]
    merol = kep["fent"] - j["lent"]
    assert abs(parh - PARHUZAMOS_RES) <= 1, (oldal, parh, j, kep)
    assert abs(merol - MEROLEGES_RES) <= 1, (oldal, merol, j, kep)


class TestBelepesAReferenciaSzerint:
    def test_belepeskor_kattintas_nelkul_a_bal_a_7_a_jobb_a_8(self, huszonnegy_kep, qt_app):
        """`Colab EN 33`: belépés után SEMMI kattintás — a bal fél a 7.
        képet mutatja (nem a helykitöltőt), a jobb a 8.-at."""
        window = huszonnegy_kep[0]
        _ab_modba_a_7_kepnel(window, qt_app)

        assert _ket_fel(window, qt_app) == (BELEPESI_SOR, BELEPESI_SOR + 1)

    def test_belepeskor_a_sav_7_24_es_a_jelveny_a_bal_folott(self, huszonnegy_kep, qt_app):
        window = huszonnegy_kep[0]
        _ab_modba_a_7_kepnel(window, qt_app)

        assert "(7 / 24)" in _sav(window), _sav(window)
        _jelveny_a_kep_folott(window, "bal")

    def test_a_jobb_kepre_kattintva_8_24_es_a_jelveny_a_jobb_folott(
        self, huszonnegy_kep, qt_app
    ):
        """`Colab EN 34`: a kattintás fókuszt vált, nem lapoz."""
        window = huszonnegy_kep[0]
        _ab_modba_a_7_kepnel(window, qt_app)

        _klikk(qt_app, window, _gyerek(window, "viewerImage"))

        assert "(8 / 24)" in _sav(window), _sav(window)
        _jelveny_a_kep_folott(window, "jobb")
        assert _ket_fel(window, qt_app) == (BELEPESI_SOR, BELEPESI_SOR + 1)


class TestLapozasUtanKetKulonbozoKep:
    """▶ után a két fél két KÜLÖNBÖZŐ, szomszédos kép, képtartalommal —
    mindkét fókusszal."""

    def test_bal_fokusznal(self, huszonnegy_kep, qt_app):
        window = huszonnegy_kep[0]
        _ab_modba_a_7_kepnel(window, qt_app)

        _klikk(qt_app, window, _gyerek(window, "viewerNextButton"))

        assert _ket_fel(window, qt_app) == (BELEPESI_SOR + 1, BELEPESI_SOR + 2)
        assert "(8 / 24)" in _sav(window), _sav(window)

    def test_jobb_fokusznal(self, huszonnegy_kep, qt_app):
        window = huszonnegy_kep[0]
        _ab_modba_a_7_kepnel(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerImage"))

        _klikk(qt_app, window, _gyerek(window, "viewerNextButton"))

        assert _ket_fel(window, qt_app) == (BELEPESI_SOR + 1, BELEPESI_SOR + 2)
        assert "(9 / 24)" in _sav(window), _sav(window)

    def test_jobb_fokusznal_ketszer(self, huszonnegy_kep, qt_app):
        """Mérve a javítás előtt: két ▶ után mindkét fél a helykitöltőt mutatta."""
        window = huszonnegy_kep[0]
        _ab_modba_a_7_kepnel(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerImage"))

        _klikk(qt_app, window, _gyerek(window, "viewerNextButton"))
        _klikk(qt_app, window, _gyerek(window, "viewerNextButton"))

        assert _ket_fel(window, qt_app) == (BELEPESI_SOR + 2, BELEPESI_SOR + 3)

    def test_jobb_fokusznal_rogzitett_masik_keppel_a_bal_lapoz(
        self, huszonnegy_kep, qt_app
    ):
        """Jobb fókusznál a filmszalagról választott jobb kép rögzített
        (`masodikIndex`) — ▶ után a bal fél (a második rekesz) a következő
        képet rajzolja ki, a jobb helyben marad."""
        window = huszonnegy_kep[0]
        _ab_modba_a_7_kepnel(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerImage"))
        _klikk(qt_app, window, _filmszalag_elem(window, 4))
        assert _ket_fel(window, qt_app) == (BELEPESI_SOR, 4)

        _klikk(qt_app, window, _gyerek(window, "viewerNextButton"))

        assert _ket_fel(window, qt_app) == (BELEPESI_SOR + 1, 4)
        assert "(5 / 24)" in _sav(window), _sav(window)
