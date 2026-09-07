"""#2608 — a felirat-sáv őre RENDERELT KÉPPONTOT néz, nem tulajdonságot.

## Miért ez a fájl létezik

A #2565 és a #2587 minden állítása QML-TULAJDONSÁGRA ment (`isVisible()`,
`width()`, `color`). Ezek zöldek voltak akkor is, amikor a tulajdonos
képernyőjén a sáv majdnem fekete volt és a kapcsológomb kikapcsolva
egyáltalán nem látszott — a hibát az ő szeme találta meg, nem a tesztünk.
Ugyanez az osztály engedte ki a #2494-et is: *„a tesztednek látnia kellett
volna, nem csak kiszámolnia."*

Ez a fájl ezért `grabWindow()`-val KÉPET készít, és a képpontokat hasonlítja
a referenciából KIMÉRT értékekhez.

## A referencia és a mért számok

`research/felirat-ki-bekapcsolva/` — a tulajdonos négy felvétele
(1920 × 1080, 2026-09-06 22:32), Picasa 3 és PicasaPy, be- és kikapcsolt
felirattal. A Picasa 3 oldaláról kimérve:

| mit | hol a felvételen | érték |
|---|---|---|
| sáv háttere BE | `picasa3-…-bekapcsolva`, y 906…926, x 700 | `RGB(198,198,198)` |
| sáv magassága | ugyanott | 21 px |
| sáv KI állapotban | `picasa3-…-kikapcsolva`, ugyanaz az ablak | NINCS — a fotó `RGB(128,128,128)` háttere látszik |
| kapcsológomb doboza | mindkét felvételen x 287…303, y 910…922 | 17 × 13 px, világos (≥225 mind a három csatornán) |
| a gomb rajza BE | `bekapcsolva` | két sötét vonal a fehér dobozban |
| a gomb rajza KI | `kikapcsolva` | a doboz ÜRES |

⚠️ A szín-egyezést a világos témára mérjük; a sötét témára a `Theme` saját
`captionBar` értéke (`#333333`) a mérce, azt is renderelt képpontból.

⚠️ A `research/` mappa **`.gitignore`-olt** — a felvételek a fejlesztői gépen
élnek, a CI-n nincsenek. Ezért a fenti számokat ide ÁTÍRVA őrizzük
konstansként, és a fájl létezésére NEM állítunk semmit: egy CI-n mindig
kihagyott teszt nem őr (a környezetfüggő skip csapdája).
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject

#: A felvételek helye a fejlesztői gépen (a CI-n nincs ott, ld. a fejlécet).
REFERENCIA_MAPPA = "research/felirat-ki-bekapcsolva/"

#: MÉRT: a sáv háttere világos témában (`picasa3-…-bekapcsolva`, y 907…919).
SAV_SZIN_VILAGOS = (198, 198, 198)
#: MÉRT: a fotó-terület háttere, ami KI állapotban a sáv helyén látszik.
FOTO_HATTER = (128, 128, 128)
#: MÉRT: a sáv magassága (y 906…926 = 21 sor).
SAV_MAGAS = 21
#: MÉRT: a kapcsológomb doboza (x 287…303, y 910…922).
GOMB_SZELES, GOMB_MAGAS = 17, 13
#: A doboz „világos" küszöbe: a felvételen mind a három csatorna 225 fölött.
VILAGOS_KUSZOB = 225
#: A JPEG-tömörítés és a betűsimítás miatt csatornánként ennyit engedünk.
SZIN_TURES = 6


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AssertionError, AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.01)
    return False


def _walk(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _walk(gyerek)


def _elem(window, nev: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


def _nyisd_a_nezot(window, qt_app):
    window.setProperty("viewerOpen", True)
    nezo = _elem(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    assert _var(
        qt_app, lambda: _elem(window, "captionToggleButton").isVisible()
    ), "a felirat-kapcsoló meg sem jelent — a próba előfeltétele bukott"
    return nezo


def _leforgat(window, qt_app):
    """Renderelt képkocka. A `grabWindow` egy kimerítést igényel."""
    for _ in range(20):
        qt_app.processEvents()
        time.sleep(0.01)
    kep = window.grabWindow()
    assert not kep.isNull(), "a renderelés üres képet adott"
    return kep


def _rgb(kep, x: int, y: int) -> tuple[int, int, int]:
    szin = kep.pixelColor(int(x), int(y))
    return (szin.red(), szin.green(), szin.blue())


def _kozel(a, b, tures: int = SZIN_TURES) -> bool:
    return all(abs(x - y) <= tures for x, y in zip(a, b, strict=True))


def _sor_medianja(kep, x: int, y: int, szeles: int):
    """Egy vízszintes sáv-sor jellemző színe.

    ⚠️ NEM a sor közepét mintázzuk: ott a felirat (illetve a „Készítsen
    képfeliratot!" felszólítás) áll, és egy élsimított betű-képpontot
    mérnénk a sáv háttere helyett. A medián a betűkre érzéketlen.
    """
    csatornak = [[], [], []]
    for dx in range(2, szeles - 2):
        for i, ertek in enumerate(_rgb(kep, x + dx, y)):
            csatornak[i].append(ertek)
    return tuple(sorted(c)[len(c) // 2] for c in csatornak)


def _doboz(elem):
    """Az elem képernyő-téglalapja egész képpontokban."""
    bal_fent = elem.mapToScene(elem.boundingRect().topLeft())
    return (
        int(round(bal_fent.x())),
        int(round(bal_fent.y())),
        int(round(elem.width())),
        int(round(elem.height())),
    )


class TestASavKEPPONTJAI:
    """A sáv színe és magassága RENDERELT képen, világos témában."""

    def test_a_sav_hattere_a_MERT_vilagosszurke(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _elem(window, "captionBar")
        x, y, sz, m = _doboz(sav)
        kep = _leforgat(window, qt_app)
        minta = _sor_medianja(kep, x, y + m // 2, sz)
        assert _kozel(minta, SAV_SZIN_VILAGOS), (
            f"a felirat-sáv renderelt színe {minta}, a Picasa 3-é "
            f"{SAV_SZIN_VILAGOS} (mérve: research/felirat-ki-bekapcsolva/"
            "picasa3-felirat-bekapcsolva, y 907…919). A tulajdonos "
            "felvételén ez RGB(23,23,23) volt."
        )

    def test_a_sav_MERT_magassaga_a_kepen(self, qml_app, qt_app):
        """Nem az elem `height`-je: a KÉPEN megszámolt egyszínű sorok."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        x, y, sz, _m = _doboz(_elem(window, "captionBar"))
        kep = _leforgat(window, qt_app)
        sorok = 0
        for dy in range(-4, SAV_MAGAS + 8):
            if _kozel(_sor_medianja(kep, x, y + dy, sz), SAV_SZIN_VILAGOS):
                sorok += 1
        assert sorok == SAV_MAGAS, (
            f"a sáv a képen {sorok} képpont magas, a mért érték {SAV_MAGAS} "
            "(picasa3-felirat-bekapcsolva, y 906…926)"
        )

    def test_kikapcsolva_a_sav_helyen_a_FOTO_hattere_van(
        self, qml_app, qt_app
    ):
        """Az eredetiben a sáv nem elsötétül, hanem ELTŰNIK."""
        window, _c, _e = qml_app
        nezo = _nyisd_a_nezot(window, qt_app)
        x, y, sz, m = _doboz(_elem(window, "captionBar"))
        nezo.metaObject().invokeMethod(nezo, "billentsdAFeliratot")
        qt_app.processEvents()
        kep = _leforgat(window, qt_app)
        minta = _sor_medianja(kep, x, y + m // 2, sz)
        assert _kozel(minta, FOTO_HATTER), (
            f"kikapcsolt feliratnál a sáv helyén {minta} van, az eredetiben a "
            f"fotó háttere {FOTO_HATTER} (picasa3-felirat-kikapcsolva)"
        )


class TestAKapcsoloRAJZA:
    """A gomb doboza és a benne lévő rajz — mindkét állapotban, képen."""

    @staticmethod
    def _vilagos_dobozok(kep, x, y, sz, m):
        """A gomb dobozának világos képpontjai és a sötét rajz aránya."""
        vilagos = sotet = 0
        for dy in range(m):
            for dx in range(sz):
                r, g, b = _rgb(kep, x + dx, y + dy)
                if min(r, g, b) >= VILAGOS_KUSZOB:
                    vilagos += 1
                elif max(r, g, b) < 140:
                    sotet += 1
        return vilagos, sotet

    def test_bekapcsolva_a_dobozban_VAN_rajz(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        x, y, sz, m = _doboz(_elem(window, "captionToggleButton"))
        assert (sz, m) == (GOMB_SZELES, GOMB_MAGAS), (
            f"a kapcsoló {sz} × {m}, a mért méret {GOMB_SZELES} × "
            f"{GOMB_MAGAS} (x 287…303, y 910…922 a felvételen)"
        )
        kep = _leforgat(window, qt_app)
        vilagos, sotet = self._vilagos_dobozok(kep, x, y, sz, m)
        assert vilagos > 0.3 * sz * m, (
            f"a kapcsoló doboza nem világos: {vilagos} világos képpont a "
            f"{sz * m}-ből (az eredetiben fehér doboz)"
        )
        assert sotet >= 8, (
            f"a bekapcsolt kapcsolóban nincs rajz ({sotet} sötét képpont) — "
            "az eredetiben két vízszintes vonal van a fehér dobozban"
        )

    def test_kikapcsolva_a_doboz_URES_de_LATSZIK(self, qml_app, qt_app):
        """A tulajdonos első kifogása: kikapcsolva a gomb ELTŰNT."""
        window, _c, _e = qml_app
        nezo = _nyisd_a_nezot(window, qt_app)
        nezo.metaObject().invokeMethod(nezo, "billentsdAFeliratot")
        qt_app.processEvents()
        gomb = _elem(window, "captionToggleButton")
        x, y, sz, m = _doboz(gomb)
        assert (sz, m) == (GOMB_SZELES, GOMB_MAGAS)
        kep = _leforgat(window, qt_app)
        vilagos, sotet = self._vilagos_dobozok(kep, x, y, sz, m)
        assert vilagos > 0.3 * sz * m, (
            f"kikapcsolva a kapcsoló doboza nem látszik a KÉPEN: {vilagos} "
            f"világos képpont a {sz * m}-ből. Az eredetiben ilyenkor is ott "
            "van egy üres fehér doboz (picasa3-felirat-kikapcsolva)."
        )
        assert sotet <= 4, (
            f"kikapcsolva a dobozban rajz van ({sotet} sötét képpont) — az "
            "eredetiben a doboz ÜRES"
        )

    def test_a_gomb_helye_nem_ugrik_a_KEPEN(self, qml_app, qt_app):
        """A felvételen mindkét állapotban x 287…303, y 910…922."""
        window, _c, _e = qml_app
        nezo = _nyisd_a_nezot(window, qt_app)
        gomb = _elem(window, "captionToggleButton")
        be = _doboz(gomb)
        nezo.metaObject().invokeMethod(nezo, "billentsdAFeliratot")
        qt_app.processEvents()
        _leforgat(window, qt_app)
        ki = _doboz(gomb)
        assert be == ki, (
            f"a kapcsoló elmozdult a két állapot közt: {be} → {ki}"
        )


class TestSotetTema:
    """A sötét témára a saját tokenünk a mérce — de RENDERELT képpontból."""

    def test_a_sav_a_sotet_token_szinet_viszi(self, qml_app, qt_app):
        window, _c, engine = qml_app
        tema = engine.singletonInstance("PicasaPy", "Theme")
        _nyisd_a_nezot(window, qt_app)
        tema.setProperty("dark", True)
        qt_app.processEvents()
        try:
            vart = tema.property("captionBar")
            sav = _elem(window, "captionBar")
            x, y, sz, m = _doboz(sav)
            kep = _leforgat(window, qt_app)
            minta = _sor_medianja(kep, x, y + m // 2, sz)
            assert _kozel(
                minta, (vart.red(), vart.green(), vart.blue())
            ), (
                f"sötét témában a sáv renderelt színe {minta}, a token "
                f"{vart.name()}"
            )
        finally:
            tema.setProperty("dark", False)
            qt_app.processEvents()


@pytest.mark.parametrize(
    "nev", ["captionBar", "captionToggleButton", "captionBarBackground"]
)
def test_a_mert_elemnevek_megvannak(qml_app, qt_app, nev):
    """Az őr elemnévre keres: ha egy átnevezés elviszi, itt bukjon."""
    window, _c, _e = qml_app
    _nyisd_a_nezot(window, qt_app)
    assert _elem(window, nev) is not None
