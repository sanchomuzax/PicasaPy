"""A Szépia és a Fekete-fehér mód a KIRAJZOLT képpontokon — #1657.

A tulajdonos RPi5-ön a menüből választotta a Szépiát, és semmi nem történt.
A képpont-szabályt a `tests/render/test_display_modes_szepia_bw_1657.py`
őrzi; ez a fájl azt méri, hogy a **menüből kattintva** tényleg átalakul-e
a kép — a nagy nézőben ÉS a könyvtár rácsán.

## Miért a menüből, és miért a kirajzolt képpontokból?

Mert a lánc ízületei külön-külön csúszhatnak szét úgy, hogy a modul-szintű
teszt zöld marad (#1454, #1596, #1598): (1) a menütétel nem hívja a
beállítót, (2) a beállító nem jut el a kép-szolgáltatóig, (3) a szolgáltató
megkapja, de a QML nem kéri újra a képet (a Qt URL szerint gyorstárazza a
bélyegképet — változatlan URL-nél a RÉGI képpontok maradnak a képernyőn).
A #1657 épp egy negyedik ízületen bukott: a szolgáltató megkapta a módot,
és **átengedte**.

## A várt színek KIÍRT LITERÁLOK

Egyik sem a termékkódból: a spec 5.7/5.8 egész-aritmetikájából kézzel
kiszámolva (a teljes levezetés a render-szintű testvérfájlban áll). Így a
konstans elrontása itt is bukást okoz.

## A rács próbaképei SZÍNESEK — ez mérési döntés

A #1596 két próbaképe szürke (200 és 255). A fekete-fehér mód azon
**definíció szerint** nem látszik: a luma-súlyok összege pontosan 256,
tehát `Y(g,g,g) = g` — a szürke önmagát adja vissza, és a 255-ös kép a
szépiát is túléli. Ezért használ ez a fájl saját, színes fixture-t
(`qml_app_szines_belyegkep`), amelynek két tónusa ráadásul a szépia
maszk-ágának két oldalára esik.
"""

from __future__ import annotations

import time

import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

#: A menütételek `objectName`-jei (a #1575 névsorából).
TETEL_SZEPIA = "menuViewDisplayModeSepia"
TETEL_FEKETE_FEHER = "menuViewDisplayModeBlackWhite"
TETEL_PROJEKTOR = "menuViewDisplayModeProjector"
#: Kontroll: a 24 bites mód SOHA nem mozdít képpontot (spec 5.1).
TETEL_24BIT = "menuViewDisplayModeNormal"

# --------------------------------------------------------------------------
# A NAGY NÉZŐ próbaképe: négy egyenletes sáv.
#
# BW  — `Y = (77·R + 151·G + 28·B) >> 8`:
#   (255,255,255) → 65280 >> 8 = 255
#   (128,128,128) → 32768 >> 8 = 128
#   (  0,  0,  0) →     0 >> 8 =   0
#   (255,  0,  0) → 19635 >> 8 =  76      (19635 = 76·256 + 179)
#
# SZÉPIA — `v1 = 255 − ((255−Y)·218 >> 8)`, majd a maszkos szorzás:
#   Y=255: v1=255, m=0xFF, v2=0             → (255, 255, 255)
#   Y=128: 127·218=27686>>8=108 → v1=147, m=0xFF, v2=216
#          216·100=21600>>8= 84→171 | 216·130=28080>>8=109→146
#          216·156=33696>>8=131→124        → (171, 146, 124)
#   Y=0  : 255·218=55590>>8=217 → v1= 38, m=0x00, v2=76
#          76·155=11780>>8=46 | 76·125=9500>>8=37 | 76·99=7524>>8=29
#                                          → ( 46,  37,  29)
#   Y=76 : 179·218=39022>>8=152 → v1=103, m=0x00, v2=206
#          206·155=31930>>8=124 | 206·125=25750>>8=100 | 206·99=20394>>8=79
#                                          → (124, 100,  79)
# --------------------------------------------------------------------------

SAVOK = ((255, 255, 255), (128, 128, 128), (0, 0, 0), (255, 0, 0))
EREDETI_SZINEK = set(SAVOK)
VART_BW = {(255, 255, 255), (128, 128, 128), (0, 0, 0), (76, 76, 76)}
VART_SZEPIA = {
    (255, 255, 255),
    (171, 146, 124),
    (46, 37, 29),
    (124, 100, 79),
}

# --------------------------------------------------------------------------
# A RÁCS két próbaképe (`conftest._szines_proba_kepek`).
#
#   (16, 156, 129): 77·16+151·156+28·129 = 1232+23556+3612 = 28400 >> 8 = 110
#       szépia: 145·218=31610>>8=123 → v1=132 ≥128 → m=0xFF, v2=(132^255)·2=246
#               246·100=24600>>8= 96→159 | 246·130=31980>>8=124→131
#               246·156=38376>>8=149→106           ⇒ (159, 131, 106)
#   (16,  89,  70): 77·16+151· 89+28· 70 = 1232+13439+1960 = 16631 >> 8 =  64
#       szépia: 191·218=41638>>8=162 → v1= 93 <128 → m=0x00, v2=186
#               186·155=28830>>8=112 | 186·125=23250>>8= 90
#               186· 99=18414>>8= 71                ⇒ (112,  90,  71)
#
# A két kép tehát a szépia maszk-ágának KÉT OLDALÁT méri a rácson is — és
# mindkettő MUTÁCIÓ-ÉRZÉKENY (ld. a conftest `PROBA_SZIN_*` indoklását).
# --------------------------------------------------------------------------

RACS_VILAGOS = (16, 156, 129)
RACS_SOTET = (16, 89, 70)
RACS_BW_VILAGOS = (110, 110, 110)
RACS_BW_SOTET = (64, 64, 64)
RACS_SZEPIA_VILAGOS = (159, 131, 106)
RACS_SZEPIA_SOTET = (112, 90, 71)

#: Meddig várunk arra, hogy a rács felvegye a várt színt. A határidő
#: lejárta után a hívó ugyanúgy állít a TÉNYLEGES színeken (a #1596 mintája).
HATARIDO = 10.0


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _kattint(root, name):
    """A menütétel aktiválása — a valódi kattintás mindkét lépése (#1575)."""
    item = _child(root, name)
    if item.property("checkable"):
        QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


def _tombbe(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    raw = raw.reshape((height, converted.bytesPerLine()))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _szinek(tomb: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(c) for c in p) for p in tomb.reshape(-1, 3)}


# ==========================================================================
# 1. A NAGY NÉZŐ (#1598 útja: app/edit_preview.py)
# ==========================================================================


@pytest.fixture
def savos(qml_app, qt_app, tmp_path):
    """Négy sávos próbakép nyitott szerkesztésben (a #1577/#1578 mintája).

    A szolgáltatót a bekötött `EditController`-től kérjük el, nem külön
    példányosítjuk — épp az a kérdés, hogy a MOTORBA kötött lánc működik-e.
    A kép PNG, tehát a sávok színe bitre a megadott.
    """
    import cv2

    window, controller, engine = qml_app
    edit_controller = engine.rootContext().contextProperty("editController")
    assert edit_controller is not None, "az editController nincs a QML-kontextusban"
    provider = edit_controller._provider

    path = tmp_path / "savok.png"
    kep = np.zeros((len(SAVOK), 6, 3), dtype=np.uint8)
    for sor, szin in enumerate(SAVOK):
        kep[sor, :] = tuple(reversed(szin))  # az OpenCV BGR-ben ír
    assert cv2.imwrite(str(path), kep)

    edit_controller.beginEdit("sav", str(path))
    qt_app.processEvents()

    def keres() -> set[tuple[int, int, int]]:
        return _szinek(_tombbe(provider.requestImage("sav", None, None)))

    return window, controller, edit_controller, keres


class TestNagyNezo:
    """A menüből kattintva a nagy néző képe átalakul (#1598 útja)."""

    def test_kattintas_elott_erintetlen(self, savos):
        _window, controller, _edit, keres = savos
        assert controller.property("displayMode") == "auto"
        assert keres() == EREDETI_SZINEK

    @pytest.mark.parametrize(
        ("tetel", "mod", "vart"),
        [
            (TETEL_FEKETE_FEHER, "bw", VART_BW),
            (TETEL_SZEPIA, "sepia", VART_SZEPIA),
        ],
    )
    def test_a_menupontra_kattintva_valtozik_a_kep(
        self, savos, qt_app, tetel, mod, vart
    ):
        window, controller, _edit, keres = savos
        _kattint(window, tetel)
        qt_app.processEvents()
        assert controller.property("displayMode") == mod
        assert keres() == vart

    @pytest.mark.parametrize(
        ("tetel", "mod"),
        [(TETEL_FEKETE_FEHER, "bw"), (TETEL_SZEPIA, "sepia")],
    )
    def test_a_mod_elhagyasa_visszaallitja(self, savos, qt_app, tetel, mod):
        """A mód nem éghet bele semmilyen gyorsítótárba."""
        window, controller, _edit, keres = savos
        _kattint(window, tetel)
        qt_app.processEvents()
        assert keres() != EREDETI_SZINEK

        _kattint(window, TETEL_24BIT)
        qt_app.processEvents()
        assert controller.property("displayMode") == "normal"
        assert keres() == EREDETI_SZINEK, (
            f"a(z) {mod!r} mód elhagyása után nem az eredeti kép jött vissza"
        )

    def test_a_ket_mod_kulonbozik(self, savos, qt_app):
        """Kontroll: nem ugyanaz a kettő — a szépia nem csak szürkít."""
        window, _controller, _edit, keres = savos
        _kattint(window, TETEL_FEKETE_FEHER)
        qt_app.processEvents()
        bw = keres()
        _kattint(window, TETEL_SZEPIA)
        qt_app.processEvents()
        assert keres() != bw


# ==========================================================================
# 2. A KÖNYVTÁR RÁCSA (#1596 útja: app/thumbnail_provider.py)
# ==========================================================================


def _cella_kepek(grid) -> list:
    """A rács `thumbImage` elemei a VIZUÁLIS fáról (a #1596 mintája)."""
    talalt: list = []

    def bejar(item) -> None:
        if item.objectName() == "thumbImage":
            talalt.append(item)
        for gyerek in item.childItems():
            bejar(gyerek)

    bejar(grid.property("contentItem"))
    return talalt


def _foltok(window, grid) -> list:
    """Cellánként a kirajzolt bélyegkép BELSŐ foltjának színhalmaza."""
    tomb = _tombbe(window.grabWindow())
    eredmeny = []
    for kep in _cella_kepek(grid):
        szeles = float(kep.property("paintedWidth"))
        magas = float(kep.property("paintedHeight"))
        if szeles <= 0 or magas <= 0:
            continue
        doboz_szeles = float(kep.property("width"))
        doboz_magas = float(kep.property("height"))
        bal_felso = kep.mapToScene(
            QPointF((doboz_szeles - szeles) / 2, (doboz_magas - magas) / 2)
        )
        x, y = int(bal_felso.x()), int(bal_felso.y())
        folt = tomb[
            y + int(magas * 0.25) : y + int(magas * 0.75),
            x + int(szeles * 0.25) : x + int(szeles * 0.75),
        ]
        eredmeny.append(
            {tuple(int(c) for c in p) for p in np.unique(folt.reshape(-1, 3), axis=0)}
        )
    return eredmeny


def _varva_foltok(window, grid, qt_app, vart) -> list:
    """A cella-foltok, legfeljebb `HATARIDO`-ig várva `vart`-ra (#1596).

    A `vart` csak a várakozás LEÁLLÍTÁSÁRA szolgál; az állítást a hívó
    végzi a visszaadott listán, tehát a határidő lejárta nem hallgat el
    semmit.
    """
    hatarido = time.monotonic() + HATARIDO
    while True:
        qt_app.processEvents()
        foltok = _foltok(window, grid)
        if foltok == vart or time.monotonic() > hatarido:
            return foltok
        QTest.qWait(20)


@pytest.fixture
def racs(qml_app_szines_belyegkep, qt_app):
    """Kirajzolt könyvtár-rács a két egyenletes, SZÍNES próbaképpel."""
    window, controller, _engine = qml_app_szines_belyegkep
    grid = _child(window, "photoGrid")
    QMetaObject.invokeMethod(grid, "forceLayout")
    eredeti = [{RACS_VILAGOS}, {RACS_SOTET}]
    foltok = _varva_foltok(window, grid, qt_app, eredeti)
    assert foltok == eredeti, (
        "a mérés előfeltétele nem áll fenn: a rács nem a két egyenletes "
        f"színes próbaképet rajzolja ki — {foltok}"
    )
    return window, controller, grid


class TestRacs:
    """A menüből kattintva a rács cellái is átalakulnak (#1596 útja)."""

    @pytest.mark.parametrize(
        ("tetel", "mod", "vart"),
        [
            (
                TETEL_FEKETE_FEHER,
                "bw",
                [{RACS_BW_VILAGOS}, {RACS_BW_SOTET}],
            ),
            (
                TETEL_SZEPIA,
                "sepia",
                [{RACS_SZEPIA_VILAGOS}, {RACS_SZEPIA_SOTET}],
            ),
        ],
    )
    def test_a_menupontra_kattintva_valtozik_a_racs(
        self, racs, qt_app, tetel, mod, vart
    ):
        window, controller, grid = racs
        _kattint(window, tetel)
        qt_app.processEvents()
        assert controller.property("displayMode") == mod
        assert _varva_foltok(window, grid, qt_app, vart) == vart

    @pytest.mark.parametrize(
        "tetel", [TETEL_FEKETE_FEHER, TETEL_SZEPIA]
    )
    def test_a_mod_elhagyasa_visszaallitja_a_racsot(self, racs, qt_app, tetel):
        window, _controller, grid = racs
        _kattint(window, tetel)
        qt_app.processEvents()

        _kattint(window, TETEL_24BIT)
        qt_app.processEvents()
        eredeti = [{RACS_VILAGOS}, {RACS_SOTET}]
        assert _varva_foltok(window, grid, qt_app, eredeti) == eredeti, (
            "a mód elhagyása után a színezés a rácson maradt"
        )


# ==========================================================================
# 3. A MÓD NEM ÍR A LEMEZRE (#1657 követelmény)
# ==========================================================================


class TestNemModositAFajlt:
    """A megjelenítési mód NEM a szerkesztő effektje: nem ír semmit.

    A szerkesztő `sepia`/`bw` effektje a `.picasa.ini` `filters=` láncába
    kerül és a mentett képre ír; ez itt csak a képernyőre hat. Ha a kettő
    valaha összecsúszna, a felhasználó fájljai némán átszíneződnének.

    A próba akkor ér valamit, ha a mód TÉNYLEG fest — különben azt mérnénk,
    hogy egy meg sem történt művelet nem írt fájlt. Ezért mindkét állítás
    előtt megvárjuk a várt képpontokat, és azt külön ki is mondjuk.
    """

    @pytest.mark.parametrize(
        ("tetel", "vart"),
        [
            (TETEL_FEKETE_FEHER, [{RACS_BW_VILAGOS}, {RACS_BW_SOTET}]),
            (TETEL_SZEPIA, [{RACS_SZEPIA_VILAGOS}, {RACS_SZEPIA_SOTET}]),
        ],
    )
    def test_a_festes_nem_nyul_a_lemezhez(self, racs, qt_app, tetel, vart, tmp_path):
        import hashlib

        def lenyomatok() -> dict[str, str]:
            return {
                str(f.relative_to(tmp_path)): hashlib.sha256(
                    f.read_bytes()
                ).hexdigest()
                for f in sorted(tmp_path.rglob("*"))
                if f.is_file() and f.suffix.lower() in {".jpg", ".ini"}
            }

        window, controller, grid = racs
        elotte = lenyomatok()
        assert any(n.endswith(".jpg") for n in elotte), (
            f"a mérés előfeltétele nem áll fenn: nincs képfájl — {elotte}"
        )

        _kattint(window, tetel)
        qt_app.processEvents()
        # 1) a mód VALÓBAN fest — enélkül a fájl-állítás vacuous volna
        assert _varva_foltok(window, grid, qt_app, vart) == vart, (
            "a mód nem festett, tehát a lemez-állítás semmit nem bizonyítana"
        )
        QTest.qWait(200)
        qt_app.processEvents()

        # 2) …és közben egyetlen képfájl és egyetlen .picasa.ini sem változott
        assert lenyomatok() == elotte, (
            "a megjelenítési mód megváltoztatta a lemezen a képet vagy a "
            ".picasa.ini-t — ez a szerkesztő effektjének a dolga volna"
        )

        # 3) a `filters=` lánc meg sem született (a szerkesztő effektje ide írna)
        inik = list(tmp_path.rglob("*.ini"))
        for ini in inik:
            szoveg = ini.read_text(encoding="utf-8", errors="replace")
            assert "filters=" not in szoveg, (
                f"a megjelenítési mód a {ini.name} filters= láncába írt: {szoveg!r}"
            )
        assert controller.property("displayMode") in {"bw", "sepia"}
