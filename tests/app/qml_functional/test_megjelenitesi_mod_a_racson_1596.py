"""A megjelenítési mód a KÖNYVTÁR RÁCSÁN — #1596.

A #1598 mérése a nagy nézőre nézve zöld: a menüből váltva a kirajzolt kép
tényleg átalakul. **A rácson viszont mind a tizenegy tétel képpontra azonos
felvételt adott** — semmi nem történt. Az ok szerkezeti: a színezés csak az
`editpreview` szolgáltatóban futott (`app/edit_preview.py`), amit kizárólag
a nagy néző használ; a rács a `thumbs` szolgáltatóból rajzol
(`ThumbDelegate.qml` → `cell.thumbUrl` → `app/thumbnail_provider.py`).

## Miért a kirajzolt ablak, és nem a szolgáltató kimenete?

Mert a #1596 hibája épp a szolgáltató és a képernyő KÖZÖTT volt. Egy olyan
teszt, amely a `provider.requestImage(...)`-t hívja, akkor is zöld lenne, ha
a rács soha nem kérné újra a képet (a Qt a bélyegképet URL szerint
gyorstárazza — változatlan URL-nél a RÉGI képpontok maradnak a képernyőn).
Ezért itt a `window.grabWindow()` felvételéből olvassuk vissza a rács
celláinak képpontjait, a menütételre kattintva.

A lánc, amit ez lefed: menütétel → `AppController.setDisplayMode` →
`wire_display_mode` → `PhotoGridModel` URL-cimke + `revision` →
`LightboxFeed` `itemAt()` újrakötés → `ThumbDelegate` `Image.source`
csere → `ThumbnailProvider.requestImage` → kirajzolás.

## A próbaképek EGYENLETESEK — ez mérési döntés

A bélyegkép útja kétszer méretez át (a gyorstár 256 px-re, majd a QML
`Image` a cellába), és a JPEG is veszteséges. Egy éles él mindkét helyen
elmosódna. Két egyenletes tónusú képen viszont a teljes lánc BITRE pontos —
mérve (#1596): a rács mindkét cellája EGYETLEN színt tartalmaz
(`{(200,200,200)}` és `{(255,255,255)}`). Az állításokban ezért nincs
tűrés: a folt minden képpontja a várt szín.

## A várt színek KIÍRT LITERÁLOK

Nem a termék konstansaiból olvasva — a spec egész-aritmetikájából
kiszámolva, hogy a konstans elrontása is bukást okozzon
(`docs/specs/picasa-megjelenitesi-modok.md` 5.4/5.5/5.6/5.9):

* Projektor mód: `200·220>>8 = 171`, `255·220>>8 = 219`
* LCD fehérpont: `200·246>>8 = 192`
* Lineáris gamma: a MÉRT tábla 200. eleme = `215`
* Túlcsordulás:  `(255,255,255) → (255,127,127)`, a `200`-as kép ÉRINTETLEN

## Amit ez a fájl SZÁNDÉKOSAN nem követel meg

Az öt meg nem valósított mód (`auto`, `normal`, `dither16`, `rdesk`, `mac`)
a **#1579** dolga. Az itteni `TestMegNemValositottModok` tételesen
felsorolja mind az ötöt, és azt állítja, hogy a rács képe NEM változik —
vagyis ha valamelyik később megvalósul, ez a teszt szól, és az elvárást a
#1579 írja át. Ez nem ellentmond a #1596-nak: ott a lánc hiányzott, itt a
képpont-szabály hiányzik.

A `sepia` és a `bw` a **#1657** óta KIKERÜLT ebből a névsorból: azok ma már
mozdítanak képpontot, és a rácson is hatnak — a mérésüket a
`test_szepia_bw_a_kepernyon_es_a_racson_1657.py` végzi.
"""

from __future__ import annotations

import hashlib
import time

import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

#: A menütételek `objectName`-jei (a #1575 névsorából).
TETEL_AUTO = "menuViewDisplayModeAuto"
TETEL_24BIT = "menuViewDisplayModeNormal"
TETEL_16BIT = "menuViewDisplayMode16Bit"
TETEL_TAVOLI_ASZTAL = "menuViewDisplayModeRemoteDesktop"
TETEL_LCD = "menuViewDisplayModeLcd"
TETEL_PROJEKTOR = "menuViewDisplayModeProjector"
TETEL_TULCSORDULAS = "menuViewDisplayModeOverflow"
TETEL_MAC = "menuViewDisplayModeMacGamma"
TETEL_LINEARIS = "menuViewDisplayModeLinearGamma"
TETEL_SZEPIA = "menuViewDisplayModeSepia"
TETEL_FEKETE_FEHER = "menuViewDisplayModeBlackWhite"

#: A két próbakép egyenletes tónusa (ld. a conftest `_proba_kepek`-jét).
HATTER = (200, 200, 200)
FEHER = (255, 255, 255)

#: `200·220>>8` és `255·220>>8` — KIÍRVA, nem a `PROJECTOR_MULTIPLIER`-ből.
PROJEKTOROS_HATTER = (171, 171, 171)
PROJEKTOROS_FEHER = (219, 219, 219)
#: `200·246>>8` és `255·246>>8` — KIÍRVA, nem az `LCD_MULTIPLIER`-ből.
LCD_HATTER = (192, 192, 192)
LCD_FEHER = (245, 245, 245)
#: A MÉRT lineáris gamma-tábla 200. és 255. eleme — KIÍRVA, nem a
#: `LINEAR_GAMMA_LUT`-ból indexelve.
LINEARIS_HATTER = (215, 215, 215)
LINEARIS_FEHER = (255, 255, 255)
#: A túlcsordulás-jelölő (`0xFFFF7F7F`) — KIÍRVA.
JELOLO = (255, 127, 127)

#: Meddig várunk arra, hogy a rács felvegye a várt színt. A határidő
#: lejárta után a hívó ugyanúgy állít a TÉNYLEGES színhalmazon — az őr foga
#: nem vész el, csak a türelme fogy el (a #1598 mintája).
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


def _cella_kepek(grid) -> list:
    """A rács `thumbImage` elemei a VIZUÁLIS fáról.

    A `Repeater`-delegate-ek nem QObject-gyermekei a rácsnak, ezért a
    `findChildren` nem látná őket (a `test_qml_feed_virtualization`
    `contentItem`-bejárásának mintája).
    """
    talalt: list = []

    def bejar(item) -> None:
        if item.objectName() == "thumbImage":
            talalt.append(item)
        for gyerek in item.childItems():
            bejar(gyerek)

    bejar(grid.property("contentItem"))
    return talalt


def _foltok(window, grid) -> list:
    """Cellánként a kirajzolt bélyegkép BELSŐ foltjának színhalmaza.

    A folt a kirajzolt téglalap középső 50 %-a: a `PreserveAspectFit` miatt
    a kép kisebb a befoglaló doboznál, a szegély/keret pedig a szélén
    rajzol. Egyenletes próbaképnél a belső folt egyetlen színű.
    """
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
    """A cella-foltok színhalmazai, legfeljebb `HATARIDO`-ig várva `vart`-ra.

    A `vart` csak a várakozás LEÁLLÍTÁSÁRA szolgál; az állítást a hívó
    végzi a visszaadott listán, tehát a határidő lejárta nem hallgat el
    semmit — a hívó a tényleges (rossz) színeket kapja meg.
    """
    hatarido = time.monotonic() + HATARIDO
    while True:
        qt_app.processEvents()
        foltok = _foltok(window, grid)
        if foltok == vart or time.monotonic() > hatarido:
            return foltok
        QTest.qWait(20)


@pytest.fixture
def racs(qml_app_valodi_belyegkep, qt_app):
    """Kirajzolt, elrendezett könyvtár-rács a két egyenletes próbaképpel."""
    window, controller, _engine = qml_app_valodi_belyegkep
    grid = _child(window, "photoGrid")
    QMetaObject.invokeMethod(grid, "forceLayout")
    foltok = _varva_foltok(window, grid, qt_app, [{HATTER}, {FEHER}])
    assert foltok == [{HATTER}, {FEHER}], (
        "a mérés előfeltétele nem áll fenn: a rács nem a két egyenletes "
        f"próbaképet rajzolja ki — {foltok}"
    )
    return window, controller, grid


class TestRacsKeppontok:
    """A menüből váltott mód a rács KIRAJZOLT képpontjain."""

    def test_alaphelyzetben_nincs_atalakitas(self, racs, qt_app):
        _window, controller, _grid = racs
        assert controller.property("displayMode") == "auto"

    def test_projektor_mod_sotetit_a_racson(self, racs, qt_app):
        window, controller, grid = racs
        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        assert controller.property("displayMode") == "projector"

        vart = [{PROJEKTOROS_HATTER}, {PROJEKTOROS_FEHER}]
        assert _varva_foltok(window, grid, qt_app, vart) == vart, (
            "a Projektor módra kattintva a KÖNYVTÁR RÁCSA nem sötétedett — "
            "a lánc a menü és a rács képpontjai között szakadt meg (#1596)"
        )

    def test_lcd_mod_sotetit_a_racson(self, racs, qt_app):
        window, controller, grid = racs
        _kattint(window, TETEL_LCD)
        qt_app.processEvents()
        assert controller.property("displayMode") == "lcd"

        vart = [{LCD_HATTER}, {LCD_FEHER}]
        assert _varva_foltok(window, grid, qt_app, vart) == vart

    def test_linearis_gamma_a_racson(self, racs, qt_app):
        window, controller, grid = racs
        _kattint(window, TETEL_LINEARIS)
        qt_app.processEvents()
        assert controller.property("displayMode") == "linear"

        vart = [{LINEARIS_HATTER}, {LINEARIS_FEHER}]
        assert _varva_foltok(window, grid, qt_app, vart) == vart

    def test_tulcsordulas_jelolodik_a_racson(self, racs, qt_app):
        window, controller, grid = racs
        _kattint(window, TETEL_TULCSORDULAS)
        qt_app.processEvents()
        assert controller.property("displayMode") == "overflow"

        # a nem telített kép ÉRINTETLEN — nincs tűrés, nincs mellékhatás
        vart = [{HATTER}, {JELOLO}]
        assert _varva_foltok(window, grid, qt_app, vart) == vart, (
            "a Túlcsordult képpontok módra kattintva a rácson nem jelent "
            "meg a jelölőszín"
        )

    def test_a_modot_elhagyva_visszaall_a_racs(self, racs, qt_app):
        window, _controller, grid = racs
        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        sotet = [{PROJEKTOROS_HATTER}, {PROJEKTOROS_FEHER}]
        assert _varva_foltok(window, grid, qt_app, sotet) == sotet

        _kattint(window, TETEL_24BIT)
        qt_app.processEvents()
        eredeti = [{HATTER}, {FEHER}]
        assert _varva_foltok(window, grid, qt_app, eredeti) == eredeti, (
            "a mód elhagyása után a sötétítés a rácson maradt"
        )


class TestMegNemValositottModok:
    """Az öt, ma képpontot NEM mozdító tétel — a #1579 dolga.

    Itt SZÁNDÉKOSAN azt állítjuk, hogy a rács képe változatlan: a #1596
    hatóköre a LÁNC, nem a képpont-szabály. Ha a #1579 valamelyiket
    megvalósítja, ez a teszt szól, és az elvárást ott kell átírni.

    A `sepia`/`bw` a #1657 óta NEM tartozik ide, a `dither16`/`rdesk`/`mac`
    pedig a #1658 óta: azok jelölt, letiltott tételek, rájuk kattintani sem
    lehet — a rács változatlanságát ott a letiltás garantálja.
    """

    @pytest.mark.parametrize(
        ("tetel", "mod"),
        [
            (TETEL_AUTO, "auto"),
            (TETEL_24BIT, "normal"),
            # ⚠️ #1658: a `dither16`, az `rdesk` és a `mac` tétele MA jelölt és
            # LETILTOTT — kattintani sem lehet rájuk, tehát módot sem állítanak.
            # A rács változatlanságát rájuk a letiltás garantálja (a
            # `test_megjelenitesi_mod_jelolesek_1658.py` méri); itt csak a két
            # SZÁNDÉKOS üresjárat marad, amelyik tényleg választható.
        ],
    )
    def test_a_racs_kepe_valtozatlan(self, racs, qt_app, tetel, mod):
        window, controller, grid = racs
        # az `auto` már aktív, ezért előbb elmozdítjuk — különben a
        # kattintás no-op volna, és a próba semmit nem mérne
        if controller.property("displayMode") == mod:
            _kattint(window, TETEL_PROJEKTOR)
            qt_app.processEvents()
            sotet = [{PROJEKTOROS_HATTER}, {PROJEKTOROS_FEHER}]
            assert _varva_foltok(window, grid, qt_app, sotet) == sotet

        _kattint(window, tetel)
        qt_app.processEvents()
        assert controller.property("displayMode") == mod

        eredeti = [{HATTER}, {FEHER}]
        assert _varva_foltok(window, grid, qt_app, eredeti) == eredeti


class TestGyorstarTisztasag:
    """A mód NEM éghet bele a lemezen tárolt bélyegképbe (#1576/#1596).

    A megjelenítési mód nem a bélyegkép TARTALMA, hanem megjelenítési
    átalakító. Ha beleégne a gyorstárba, a mód kikapcsolása után is festve
    maradna a kép — és az exportba, a kollázsba, a webre is átszivárogna.
    """

    def test_a_lemezes_gyorstar_bajtra_azonos_marad(self, racs, qt_app, tmp_path):
        window, _controller, grid = racs
        gyorstar = tmp_path / "thumbs"

        def ujjlenyomat() -> dict:
            return {
                str(f.relative_to(gyorstar)): hashlib.sha256(
                    f.read_bytes()
                ).hexdigest()
                for f in sorted(gyorstar.rglob("*"))
                if f.is_file()
            }

        elotte = ujjlenyomat()
        assert elotte, "a próba előfeltétele nem áll fenn: üres a gyorstár"

        _kattint(window, TETEL_TULCSORDULAS)
        qt_app.processEvents()
        vart = [{HATTER}, {JELOLO}]
        assert _varva_foltok(window, grid, qt_app, vart) == vart

        assert ujjlenyomat() == elotte, (
            "a megjelenítési mód BELEÉGETT a lemezen tárolt bélyegképbe — "
            "a mód kikapcsolása után is festve maradna a kép"
        )

    def test_a_modot_elhagyva_a_gyorstar_kepe_ter_vissza(self, racs, qt_app):
        """A visszaállás nem újragenerálásból jön: a gyorstár képe tiszta."""
        window, _controller, grid = racs
        _kattint(window, TETEL_LCD)
        qt_app.processEvents()
        sotet = [{LCD_HATTER}, {LCD_FEHER}]
        assert _varva_foltok(window, grid, qt_app, sotet) == sotet

        _kattint(window, TETEL_AUTO)
        qt_app.processEvents()
        eredeti = [{HATTER}, {FEHER}]
        assert _varva_foltok(window, grid, qt_app, eredeti) == eredeti
