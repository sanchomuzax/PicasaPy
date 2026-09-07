"""#1919 — az összecsukott mappa-/album-token: KIRAJZOLT képpontokon mérve.

## Miért kirajzolt őr

Mert a projekt legdrágább hibája (#2494) az volt, hogy egy teszt a
geometriát KISZÁMOLTA, de a kirajzolt eredményt nem nézte meg. A
tulajdonos szava: *„A tesztednek látnia kellett volna, nem csak
kiszámolnia."* A token minden állítása — a pirula mérete, a színe, az
áttetszősége, a rétegsorrend — csak a raszteren dől el.

## A MÉRCE: `…214629.jpg`

`research/Picasa3-also-talca-ikonok-viselkedese/Teljes képernyő rögzítése
2026. 09. 01. 214629.jpg` (1920 × 1080). Amit rajta lemértem:

| mit | hol | érték |
|---|---|---|
| a tálca doboza (`thumbui/scratchback`) | x 7…643, y 949…1026 | 78 magas |
| a sáv (`thumbui/clip(scratch): scratch`) | a dobozon 5 képponttal beljebb | y 954…1021 ⇒ **68 magas** |
| `scratch/albumcover` | y 961…1012, x 309…337 | **29 × 52** |
| `scratch/highlight` | x 251…392, y 979…995 | **142 × 17** |
| a pirula színe fehér fölött | | **RGB(107, 153, 186)** |
| a felirat | | fehér, `m_displayfont12` ⇒ 12 px |

A cover 52-es magassága PONTOSAN 68 − 8 − 8, azaz a `scratch.tre`
`albumsize` behúzása; a 29-es szélesség 29/52 = 0,558, ami a forráskép
saját aránya (816/1456 = 0,560) — tehát ARÁNYTARTÓ illesztés.

## Amit ez az őr NEM állít

- **A token MÉRETÉNEK sorszám-függését.** Egyetlen ilyen felvétel van; ha
  a token mérete a tálca elemszámától is függ (mint a bélyegképeké,
  #1904), azt nem tudjuk. Az őr a MÉRT egy esetet rögzíti.
- **A megjelenés IDEJÉT.** Az eredeti szabálya kimérve megvan (a
  `scratch/album` állapot-küldöttje, `0x00563530`: akkor látszik, ha van
  album-/mappa-kijelölés, annak van eleme, és a kép-kijelölés üres) — de a
  PicasaPy ezt még nem futtatja magától, mert az a tálca mindennapi
  kinézetét írná át. Az őr azt méri, HOGYAN néz ki a token, nem azt, mikor
  jelenik meg.
- **A pirula alapszínét és α-ját külön-külön.** A JPEG miatt az α csak
  ±0,05 pontosságú; ami mérhető és ellenőrizhető, az az EREDMÉNY a fehér
  háttér fölött, és hogy a kép fölött sötétebb (tehát áttetsző).
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

#: A MÉRT sávmagasság (`thumbui/clip(scratch): scratch`), amiben a token ül.
MERT_SAV_MAGASSAG = 68

#: A `scratch.tre` `albumsize` behúzása mind a négy oldalon.
MERT_BEHUZAS = 8

#: A MÉRT borító-magasság: 68 − 8 − 8.
MERT_BORITO_MAGASSAG = MERT_SAV_MAGASSAG - 2 * MERT_BEHUZAS

#: A `scratch/highlight` MÉRT kényszerei: vízszintesen ±4, függőlegesen +1.
MERT_PIRULA_PAD_X = 4
MERT_PIRULA_PAD_Y = 1

#: A pirula MÉRT színe a fehér tálcaháttér fölött.
MERT_PIRULA_FEHEREN = (107, 153, 186)

#: A sáv szélessége a próbán. Bőven elég a feliratnak — a kilógás nem
#: ennek az őrnek a tárgya.
_SZELES = 420

_KEEPALIVE: list[object] = []

#: A borító MÉRETARÁNYA szándékosan a felvételen mért forrásé
#: (816 × 1456 ⇒ 0,560): így a kirajzolt szélesség/magasság összevethető a
#: mért 29/52 = 0,558-cal. A kép EGYSZÍNŰ, TELÍTETT PIROS — determinisztikus
#: (nincs JPEG-zaj), és a pirula áttetszőségét ez mutatja meg a
#: legélesebben: a kék pirula piros fölött látványosan más, mint fehéren.
_BORITO_SZELES = 816
_BORITO_MAGAS = 1456

_QML = """
import QtQuick
import PicasaPy 1.0
Rectangle {
    width: %d; height: %d
    // a tálca doboza (`Theme.trayPanelBg`) VILÁGOS témán fehér — a mért
    // eredetiben 248; a különbség 7 egység, a tűrésen belül
    color: "#ffffff"
    TrayAlbumToken {
        objectName: "proba"
        anchors.fill: parent
        photoCount: 82
        isAlbum: false
        coverSource: "%s"
    }
}
"""


def _borito_fajl(konyvtar) -> str:
    """Egyszínű piros PNG a mért forrás oldalarányával."""
    from PySide6.QtGui import QImage

    kep = QImage(_BORITO_SZELES, _BORITO_MAGAS, QImage.Format_RGB32)
    kep.fill(QColor(255, 0, 0))
    utvonal = konyvtar / "borito.png"
    assert kep.save(str(utvonal), "PNG")
    return QUrl.fromLocalFile(str(utvonal)).toString()


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


@pytest.fixture(scope="module")
def _rajz(qt_app, tmp_path_factory):
    import picasapy.app.application as app_module

    borito = _borito_fajl(tmp_path_factory.mktemp("talca-token-1919"))
    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    forras = _QML % (_SZELES, MERT_SAV_MAGASSAG, borito)
    component.setData(forras.encode("utf-8"), QUrl())
    hibak = [hiba.toString() for hiba in component.errors()]
    assert hibak == [], hibak
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(_SZELES, MERT_SAV_MAGASSAG)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)
    kep = view.grabWindow()
    _KEEPALIVE.extend((view, root, component))
    return kep, root


def _rgb(kep, x: int, y: int) -> tuple[int, int, int]:
    szin: QColor = kep.pixelColor(x, y)
    return (szin.red(), szin.green(), szin.blue())


def _borito_doboz(kep) -> tuple[int, int, int, int]:
    """A PIROS borító befoglalója a rajzon (x0, y0, x1, y1).

    A pirula alatt a piros elkékül, ezért nem az „r > g" a szűrő, hanem az
    hogy a képpont NEM a fehér háttér.
    """
    xs, ys = [], []
    for y in range(MERT_SAV_MAGASSAG):
        for x in range(_SZELES):
            r, g, b = _rgb(kep, x, y)
            if (r, g, b) != (255, 255, 255) and r > b:
                xs.append(x)
                ys.append(y)
    assert xs, "a borító EGYÁLTALÁN nem rajzolódott ki"
    return min(xs), min(ys), max(xs), max(ys)


def _pirula_sorai(kep, x: int) -> list[int]:
    """Az adott oszlopban a KÉKES sorok — ez a pirula függőleges nyoma."""
    return [
        y
        for y in range(MERT_SAV_MAGASSAG)
        if (lambda p: p[2] > p[0] + 15)(_rgb(kep, x, y))
    ]


def _pirula_doboz(kep) -> tuple[int, int, int, int]:
    xs, ys = [], []
    for y in range(MERT_SAV_MAGASSAG):
        for x in range(_SZELES):
            r, _g, b = _rgb(kep, x, y)
            if b > r + 15:
                xs.append(x)
                ys.append(y)
    assert xs, "a `scratch/highlight` pirula NEM rajzolódott ki"
    return min(xs), min(ys), max(xs), max(ys)


class TestATokenEgyaltalanKirajzolodik:
    """Üres rajzon minden alábbi állítás vákuumban menne át."""

    def test_a_borito_es_a_pirula_is_latszik(self, _rajz):
        kep, _root = _rajz
        assert _borito_doboz(kep)
        assert _pirula_doboz(kep)


class TestABoritoGeometriaja:
    """`scratch/albumcover`: `m_centerXY` az `albumsize`-ban, arányt tartva."""

    def test_a_borito_MAGASSAGA_a_savbol_ket_behuzas(self, _rajz):
        kep, _root = _rajz
        _x0, y0, _x1, y1 = _borito_doboz(kep)
        magassag = y1 - y0 + 1
        assert magassag == MERT_BORITO_MAGASSAG, (
            f"a borító {magassag} képpont magas; a mért felvételen "
            f"{MERT_BORITO_MAGASSAG} (= {MERT_SAV_MAGASSAG} − 2 × "
            f"{MERT_BEHUZAS}, a `scratch.tre` `albumsize` behúzása)"
        )

    def test_a_borito_ARANYTARTO_nem_vagott(self, _rajz):
        """A felvételen 29 × 52 ⇒ 0,558, a forrás aránya 0,560."""
        kep, _root = _rajz
        x0, y0, x1, y1 = _borito_doboz(kep)
        arany = (x1 - x0 + 1) / (y1 - y0 + 1)
        assert abs(arany - 816 / 1456) < 0.05, (
            f"a borító oldalaránya {arany:.3f}; a forrásé "
            f"{816 / 1456:.3f}, a felvételen mért 29/52 = 0,558 — "
            "a kép tehát NEM aránytartóan illeszkedik"
        )

    def test_a_borito_VIZSZINTESEN_kozepen_all(self, _rajz):
        kep, _root = _rajz
        x0, _y0, x1, _y1 = _borito_doboz(kep)
        kozep = (x0 + x1) / 2
        assert abs(kozep - (_SZELES - 1) / 2) <= 1, (
            f"a borító közepe x = {kozep}, a sáv közepe "
            f"{(_SZELES - 1) / 2} (`m_centerXY`)"
        )

    def test_a_borito_FUGGOLEGESEN_kozepen_all(self, _rajz):
        kep, _root = _rajz
        _x0, y0, _x1, y1 = _borito_doboz(kep)
        kozep = (y0 + y1) / 2
        assert abs(kozep - (MERT_SAV_MAGASSAG - 1) / 2) <= 1, (
            f"a borító közepe y = {kozep}, a sáv közepe "
            f"{(MERT_SAV_MAGASSAG - 1) / 2}"
        )


class TestAPirulaGeometriaja:
    """`scratch/highlight`: X −4 … +4, Y 0 … +1, `round 2`."""

    def _felirat(self, root):
        felirat = root.findChild(object, "trayAlbumTokenLabel")
        assert felirat is not None, "nincs `trayAlbumTokenLabel` a fában"
        return felirat

    def test_a_pirula_a_felirattol_4_4_keppontal_szelesebb(self, _rajz):
        kep, root = _rajz
        felirat = self._felirat(root)
        x0, _y0, x1, _y1 = _pirula_doboz(kep)
        szelesseg = x1 - x0 + 1
        elvart = round(felirat.property("width")) + 2 * MERT_PIRULA_PAD_X
        assert abs(szelesseg - elvart) <= 1, (
            f"a pirula {szelesseg} képpont széles, a felirat "
            f"{felirat.property('width'):.0f} + 2 × {MERT_PIRULA_PAD_X} = "
            f"{elvart} lenne (`XConstraint 0,0,−4` / `1,1,4`)"
        )

    def test_a_pirula_a_felirathoz_kepest_EGY_keppontal_magasabb(self, _rajz):
        kep, root = _rajz
        felirat = self._felirat(root)
        _x0, y0, _x1, y1 = _pirula_doboz(kep)
        magassag = y1 - y0 + 1
        elvart = round(felirat.property("height")) + MERT_PIRULA_PAD_Y
        assert abs(magassag - elvart) <= 1, (
            f"a pirula {magassag} képpont magas, a felirat "
            f"{felirat.property('height'):.0f} + {MERT_PIRULA_PAD_Y} = "
            f"{elvart} lenne (`YConstraint 0,0,0` / `1,1,1`)"
        )

    def test_a_pirula_VIZSZINTESEN_kozepen_all(self, _rajz):
        kep, _root = _rajz
        x0, _y0, x1, _y1 = _pirula_doboz(kep)
        kozep = (x0 + x1) / 2
        assert abs(kozep - (_SZELES - 1) / 2) <= 1, (
            f"a pirula közepe x = {kozep}, a sáv közepe "
            f"{(_SZELES - 1) / 2} (`m_centerXY` a feliraton)"
        )

    def test_a_pirula_SARKA_le_van_kerekitve(self, _rajz):
        """`Property round 2`: a NÉGY sarokban a háttér átüt, a pirula
        derekán ugyanabban az oszlopban nem.

        ⚠️ Nem a kék képpontok SZÁMÁT nézzük soronként: a sarok élsimított
        képpontja is „kékes" marad, tehát a szélesség nem szűkül. Ami
        valóban változik, az a sarokpont VILÁGOSSÁGA.
        """
        kep, _root = _rajz
        x0, y0, x1, y1 = _pirula_doboz(kep)
        derek_y = (y0 + y1) // 2
        for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            sarok = _rgb(kep, cx, cy)
            oldal = _rgb(kep, cx, derek_y)
            assert sum(sarok) > sum(oldal) + 60, (
                f"a ({cx}, {cy}) sarok {sarok}, ugyanaz az oszlop a "
                f"derékon {oldal} — a sarok nincs lekerekítve "
                "(`Property round 2`)"
            )


class TestAPirulaSZINE:
    def _pirula_feheren(self, kep) -> tuple[int, int, int]:
        """A pirula a BAL SZÉLÉN: ott fehér a háttér, és nincs betű.

        ⚠️ A pirula KÖZEPÉT nem szabad mintavenni: a felirat végigfut
        rajta, és az élsimított betűszél világos kékeset ad — abból
        „a pirula túl világos" hamis lelet lesz.
        """
        x0, y0, x1, y1 = _pirula_doboz(kep)
        bx0, _by0, _bx1, _by1 = _borito_doboz(kep)
        x = x0 + 2
        assert x < bx0, "a pirula nem lóg túl a borítón — rossz a próba"
        return _rgb(kep, x, (y0 + y1) // 2)

    def test_a_pirula_a_MERT_szint_adja_feheren(self, _rajz):
        kep, _root = _rajz
        kapott = self._pirula_feheren(kep)
        elteres = max(
            abs(a - b)
            for a, b in zip(kapott, MERT_PIRULA_FEHEREN, strict=True)
        )
        assert elteres <= 8, (
            f"a pirula fehér fölött {kapott}, a felvételen mért "
            f"{MERT_PIRULA_FEHEREN} (legnagyobb csatorna-eltérés {elteres})"
        )

    def test_a_pirula_ATTETSZO_a_borito_folott_MAS(self, _rajz):
        """A felvételen a pirula a képen sötétebb, mint a fehér háttéren —
        ez az `usealpha`/áttetszőség egyetlen kirajzolt bizonyítéka."""
        kep, _root = _rajz
        _px0, py0, _px1, py1 = _pirula_doboz(kep)
        bx0, _by0, bx1, _by1 = _borito_doboz(kep)
        feheren = self._pirula_feheren(kep)
        # a borító sávjában a LEGVÖRÖSEBB képpont: ez a piros alapon
        # átütő pirula (a fehér betűk r − b-je 0 körüli, a fehér háttér
        # fölötti pirula erősen NEGATÍV)
        boriton = max(
            (_rgb(kep, x, y) for y in range(py0, py1 + 1)
             for x in range(bx0, bx1 + 1)),
            key=lambda p: p[0] - p[2],
        )
        assert boriton != feheren, (
            "a pirula a borító fölött UGYANOLYAN, mint a fehér háttéren — "
            "vagyis átlátszatlan; a felvételen áttetsző"
        )
        assert (boriton[0] - boriton[2]) - (feheren[0] - feheren[2]) >= 40, (
            f"a pirula a PIROS borító fölött {boriton}, a fehéren "
            f"{feheren} — a háttér alig üt át rajta, tehát nem áttetsző"
        )


class TestARetegsorrend:
    """`Property predraw 1`: a pirula a felirat ALÁ rajzolódik."""

    def test_a_feliratbol_FEHER_keppontok_latszanak_a_pirulan(self, _rajz):
        kep, _root = _rajz
        x0, y0, x1, y1 = _pirula_doboz(kep)
        vilagosak = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if min(_rgb(kep, x, y)) > 200
        ]
        assert len(vilagosak) > 20, (
            f"a pirulán csak {len(vilagosak)} világos képpont van — a fehér "
            "felirat vagy nincs kirajzolva, vagy a pirula RÁRAJZOLÓDOTT "
            "(`predraw` megsértve)"
        )


class TestAFelirat:
    """A felirat a `CThumbUI::UpdateAlbumCover` formátumból épül fel."""

    def _felirat_szoveg(self, root) -> str:
        felirat = root.findChild(object, "trayAlbumTokenLabel")
        return str(felirat.property("text"))

    def test_a_felirat_a_DARABSZAMOT_is_kiirja(self, _rajz):
        _kep, root = _rajz
        assert "82" in self._felirat_szoveg(root)

    def test_a_felirat_HAROM_darabbol_all(self, _rajz):
        """`%1$s - %2$d %3$s` — a mappa/album felirat, a szám és az
        egység, kötőjellel elválasztva (ASCII kötőjel, nem gondolatjel:
        a `stringres` `%1$s - %2$d %3$s`-t ad)."""
        _kep, root = _rajz
        szoveg = self._felirat_szoveg(root)
        assert " - " in szoveg, (
            f"a felirat ({szoveg!r}) nem a mért formátumot követi "
            "(`%1$s - %2$d %3$s`)"
        )
        elotte, utana = szoveg.split(" - ", 1)
        assert elotte.strip(), "a felirat első darabja üres"
        assert utana.split()[0] == "82", (
            f"a darabszám nem a formátum második helyén áll: {szoveg!r}"
        )


class TestAFeliratDarabszamFuggese:
    """A felirat HÁROM különböző alakot vesz fel — mind a három MÉRVE.

    A `0x0056ba10` (`CThumbUI::UpdateAlbumCover`) ágai:

    - `cmp ebp, ebx / je 0x56bbbf` — NULLA elemnél a
      `CThumbUI::UpdateAlbumCoverNoSel` („Nincs kijelölés") kerül ki,
      UGYANARRA a `scratch/albumlabel` csomópontra;
    - `cmp ebp, 1` (`0x0056bb26`) — EGYNÉL a `…UpdateAlbumphoto`
      („photo"), kettőtől a `…UpdateAlbumCoverphotos` („photos").

    Rajz nélkül mérünk: a szám → felirat leképezés a `labelText` kötésen
    dől el, azt viszont EGY példányon, a valódi komponensből olvassuk ki
    (nem újraszámoljuk a tesztben).
    """

    @staticmethod
    def _felirat(qt_app, *, photo_count: int, is_album: bool = False) -> str:
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlEngine

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        component = QQmlComponent(engine)
        component.setData(
            (
                "import QtQuick\n"
                "import PicasaPy 1.0\n"
                "TrayAlbumToken { photoCount: %d; isAlbum: %s }"
                % (photo_count, "true" if is_album else "false")
            ).encode("utf-8"),
            QUrl(),
        )
        hibak = [hiba.toString() for hiba in component.errors()]
        assert hibak == [], hibak
        elem = component.create()
        assert elem is not None
        szoveg = str(elem.property("labelText"))
        _KEEPALIVE.extend((engine, component, elem))
        return szoveg

    def test_NULLA_elemnel_a_Nincs_kijeloles_all_rajta(self, qt_app):
        szoveg = self._felirat(qt_app, photo_count=0)
        assert " - " not in szoveg, (
            f"nulla elemnél a formátumot írtuk ki ({szoveg!r}); az eredeti "
            "a `CThumbUI::UpdateAlbumCoverNoSel`-t teszi a feliratra"
        )
        assert szoveg.strip()

    def test_EGY_elemnel_EGYES_szamu_egyseg(self, qt_app):
        assert self._felirat(qt_app, photo_count=1).endswith("photo")

    def test_KETTONEL_mar_TOBBES_szamu(self, qt_app):
        assert self._felirat(qt_app, photo_count=2).endswith("photos")

    def test_az_ALBUM_mas_feliratot_kap_mint_a_mappa(self, qt_app):
        mappa = self._felirat(qt_app, photo_count=5, is_album=False)
        album = self._felirat(qt_app, photo_count=5, is_album=True)
        assert mappa != album, (
            "a mappa és az album UGYANAZT a feliratot kapja; az eredetiben "
            "`CThumbUI::UpdateAlbumFolder` vs. `…UpdateAlbumAlbum`"
        )
