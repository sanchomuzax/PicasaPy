"""#2641 — a csúszka fogantyújába VÉSETT középvonal, KIRAJZOLT képpontokon.

## A mérés forrása

    # a `png` alparancs EGY szűrőt fogad, tehát két futás kell
    python3 tools/picasa/respack.py png \\
        research/copy_Picasa_3_7/Picasa3/runtime/respack.yt <dir> "slider"

Mindkét fogantyú-réteg **ugyanazt** a vésést adja (a rajz 14 képpont
széles, a réteg 16):

| réteg | méret | a vésés oszlopai | a vésés sorai | tömör sorok |
|---|---|---|---|---|
| `scaleslider/thumb` | 16 × 22 | x = 6 (199) · x = 7 (244) | y 5…13 | 19 |
| `editslider/thumb` | 16 × 26 | x = 6 (199) · x = 7 (244) | y 5…17 | 23 |

Vagyis: **a rajz vízszintes közepén két képpont**, a sötét balra, a
világos jobbra (a fény alulról), és függőlegesen **5-5 képpont marad ki**
felül és alul — mindkét méretnél ugyanannyi, tehát a behúzás ABSZOLÚT,
nem arányos. A környező fogantyú-képpontok 232…240 között vannak.

## Miért kirajzolt őr, és mire NEM bukik

A `PicasaSlider.qml`-ben ott állhatna a `Repeater` úgy is, hogy a vonal
mérete nulla, a színe a fogantyúé, vagy a fogantyún kívülre esik — a
forrás-keresés mindháromra zöld maradna. Ez az őr a `grabWindow()` képét
méri (a `test_csuszka_sav_szine_2627.py` mintájára).

A fogantyú helyét és méretét **a QML-elemtől kérdezzük**, nem beégetett
számból: így a próba a vonal TÖRLÉSÉRE bukik, a fogantyú méretének
megváltoztatására viszont NEM (a jegy ezt a kétirányú mutációt kérte).
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPointF, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

#: A vésés BEHÚZÁSA a fogantyú két végétől — mindkét mért rétegen 5.
MERT_BEHUZAS = 5

#: A vésés két oszlopa a mért rétegen: 199 (sötét) és 244 (világos), a
#: környezet ott 232…240 — vagyis az eredetiben a sötét oldal ~34-gyel a
#: környezete ALATT, a világos ~11-gyel FÖLÖTT áll. A küszöbök ennél
#: lazábbak, hogy az élsimítás ne buktassa meg őket, de a „nincs vonal"
#: esetet (különbség 0) biztosan kizárják.
MIN_SOTET_KULONBSEG = 12
#: #2656 ÓTA: a fogantyú átmenete átlós lett (a mért 245/225/234/211
#: sarokértékekkel), a vésés melletti háttér ezért a régi ~240 helyett
#: KIRAJZOLVA ~228,8 — a világos oszlop (244) emelkedése ~15,2, közel a
#: mért +12-höz. A küszöböt ezért a mért értékre EMELTÜK (a korábbi 3
#: csak a régi, túl világos átmenet miatt kellett).
MIN_VILAGOS_KULONBSEG = 12

#: #2663: a SÖTÉT témás fogantyú-kitöltés mellett a vésés-háttér
#: KIRAJZOLVA ~112,1. A `Theme.sliderHandleGrooveDark`/`…Light` sötét ága
#: ezt figyelembe véve lett hangolva: a sötét oldal ~30-cal a háttér
#: ALATT (jóval a jegy kért ~40-es felső korlátja alatt — az máshogy
#: „csík", nem „vésés" lenne), a világos ~12-vel FÖLÖTTE.
MIN_SOTET_KULONBSEG_SOTET_TEMA = 15
MAX_SOTET_KULONBSEG_SOTET_TEMA = 40
MIN_VILAGOS_KULONBSEG_SOTET_TEMA = 6

#: A próba fogantyúja — az `editslider/thumb` mért mérete (#2627/#2631).
FOGANTYU_SZELES = 16
FOGANTYU_MAGAS = 26

#: A MUTÁCIÓ-PRÓBA fogantyúja: MÁS méret, ugyanannak a szabálynak kell
#: érvényesülnie. Ha az őr beégetett képpont-koordinátán állna, ez bukna.
MASIK_SZELES = 20
MASIK_MAGAS = 22

#: ⚠️ A próba szélessége SZÁNDÉKOSAN páros úgy, hogy a fogantyú EGÉSZ
#: képpontra essen: `(120 − 16) / 2 = 52` és `(120 − 20) / 2 = 50`.
#: 121-gyel a fogantyú x-e 52,5 lett, a vésés fél képponttal elcsúszott,
#: és a próba a rasztert mérte volna, nem a rajzot. Az alábbi
#: `test_a_fogantyu_EGESZ_keppontra_esik` ezt fogja meg, ha valaki a
#: méreteken változtat.
_SZELES = 120
_MAGAS = 40

_KEEPALIVE: list[object] = []

_QML = """
import QtQuick
import PicasaPy 1.0
Rectangle {
    width: %d; height: %d
    color: "#ffffff"
    Component.onCompleted: Theme.dark = %s
    PicasaSlider {
        objectName: "proba"
        anchors.centerIn: parent
        width: parent.width
        grooveThickness: 9
        handleWidth: %d
        handleHeight: %d
        handleRadius: 3
        from: 0; to: 100; value: 50
    }
}
"""


def _var_a_kirajzolasra(view: QQuickView, qt_app, masodperc: float = 10.0) -> None:
    """Két egyforma felvétel = kész a rajz (#918: az elrendezés késik)."""
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


def _rajzol(qt_app, szeles: int, magas: int, dark: bool = False):
    """A kirajzolt kép ÉS a fogantyú valódi doboza az ablak koordinátáiban."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(
        (_QML % (_SZELES, _MAGAS, str(dark).lower(), szeles, magas)).encode("utf-8"),
        QUrl(),
    )
    hibak = [hiba.toString() for hiba in component.errors()]
    assert hibak == [], hibak
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(_SZELES, _MAGAS)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)

    csuszka = root.findChild(object, "proba")
    assert csuszka is not None, "a próba-csúszka nincs a jelenetben"
    fogantyu = csuszka.property("handle")
    assert fogantyu is not None, "a csúszkának nincs fogantyúja"
    sarok = fogantyu.mapToScene(QPointF(0.0, 0.0))
    doboz = (
        sarok.x(), sarok.y(),
        round(fogantyu.width()), round(fogantyu.height()),
    )
    kep = view.grabWindow()
    _KEEPALIVE.extend((view, root, component))
    return kep, doboz


def _vilagossag(kep, x: int, y: int) -> float:
    szin: QColor = kep.pixelColor(x, y)
    return (szin.red() + szin.green() + szin.blue()) / 3


def _oszlop_atlaga(kep, x: int, y0: int, y1: int) -> float:
    """Egy oszlop átlagos világossága a [y0, y1) sorokon."""
    return sum(_vilagossag(kep, x, y) for y in range(y0, y1)) / (y1 - y0)


@pytest.fixture(scope="module")
def _rajz(qt_app):
    return _rajzol(qt_app, FOGANTYU_SZELES, FOGANTYU_MAGAS)


@pytest.fixture(scope="module")
def _rajz_masik(qt_app):
    return _rajzol(qt_app, MASIK_SZELES, MASIK_MAGAS)


@pytest.fixture(scope="module")
def _rajz_sotet_tema(qt_app):
    """#2663: ugyanaz a fogantyúméret, de `Theme.dark = true`."""
    return _rajzol(qt_app, FOGANTYU_SZELES, FOGANTYU_MAGAS, dark=True)


def _veses_oszlopai(doboz: tuple[int, int, int, int]) -> tuple[int, int]:
    """A vésés két oszlopa: a fogantyú közepétől balra, illetve rajta."""
    x, _y, szeles, _magas = doboz
    kozep = int(x) + round(szeles / 2)
    return (kozep - 1, kozep)


def _veses_sorai(doboz: tuple[int, int, int, int]) -> tuple[int, int]:
    """A vésés [tól, ig) sorai: 5-5 képpont behúzással."""
    _x, y, _szeles, magas = doboz
    return (int(y) + MERT_BEHUZAS, int(y) + magas - MERT_BEHUZAS)


class TestAFogantyuKirajzolodik:
    """Üres rajzon minden alábbi állítás vákuumban menne át."""

    def test_a_fogantyu_doboza_ertelmes(self, _rajz):
        _kep, (x, y, szeles, magas) = _rajz
        assert (szeles, magas) == (FOGANTYU_SZELES, FOGANTYU_MAGAS)
        assert 0 <= x and 0 <= y, f"a fogantyú a képen kívülre esett: {(x, y)}"
        assert x + szeles <= _SZELES and y + magas <= _MAGAS

    def test_a_fogantyu_EGESZ_keppontra_esik(self, _rajz):
        """Fél képpontos helyen a vésés két oszlopa szétkenődik, és a
        próba a raszterezőt mérné, nem a rajzot."""
        _kep, (x, y, _szeles, _magas) = _rajz
        assert x == int(x) and y == int(y), (
            f"a fogantyú {(x, y)}-nél áll — a próba szélességét/magasságát "
            "úgy kell megválasztani, hogy egész képpontra essen"
        )

    def test_a_fogantyu_VILAGOS_a_sav_folott(self, _rajz):
        """A fogantyú a mért 232…247 tartományban van — nem üres folt."""
        kep, doboz = _rajz
        x, y, _szeles, magas = doboz
        atlag = _oszlop_atlaga(
            kep, int(x) + 2, int(y) + MERT_BEHUZAS, int(y) + magas - MERT_BEHUZAS
        )
        assert atlag > 180, (
            f"a fogantyú bal széle {atlag:.0f} világosságú — a mért "
            "eredetiben 232…247, tehát itt nem a fogantyút mérjük"
        )


class TestAVeset:
    """A jegy tárgya: két képpont a fogantyú közepén."""

    def _hatter(self, kep, doboz) -> float:
        """A vésés melletti, ÉRINTETLEN fogantyú-képpontok világossága."""
        sotet_x, vilagos_x = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        bal = _oszlop_atlaga(kep, sotet_x - 2, y0, y1)
        jobb = _oszlop_atlaga(kep, vilagos_x + 2, y0, y1)
        return (bal + jobb) / 2

    def test_a_SOTET_oszlop_ott_van(self, _rajz):
        kep, doboz = _rajz
        sotet_x, _ = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        veses = _oszlop_atlaga(kep, sotet_x, y0, y1)
        hatter = self._hatter(kep, doboz)
        assert hatter - veses >= MIN_SOTET_KULONBSEG, (
            f"a vésés sötét oszlopa (x={sotet_x}) {veses:.0f}, a környező "
            f"fogantyú {hatter:.0f} — a mért különbség ~35, a mérce "
            f"{MIN_SOTET_KULONBSEG}"
        )

    def test_a_VILAGOS_oszlop_ott_van(self, _rajz):
        kep, doboz = _rajz
        _, vilagos_x = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        veses = _oszlop_atlaga(kep, vilagos_x, y0, y1)
        hatter = self._hatter(kep, doboz)
        assert veses - hatter >= MIN_VILAGOS_KULONBSEG, (
            f"a vésés világos oszlopa (x={vilagos_x}) {veses:.0f}, a "
            f"környező fogantyú {hatter:.0f} — a mért különbség ~10, a "
            f"mérce {MIN_VILAGOS_KULONBSEG}"
        )

    def test_a_SOTET_oldal_BALRA_van_a_vilagostol(self, _rajz):
        """A fény alulról jön: a sötét oszlop a kisebbik x. Ha a kettő
        felcserélődne, a két előző állítás külön-külön még átmenne."""
        kep, doboz = _rajz
        sotet_x, vilagos_x = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        assert sotet_x < vilagos_x
        assert _oszlop_atlaga(kep, sotet_x, y0, y1) < _oszlop_atlaga(
            kep, vilagos_x, y0, y1
        ), "a vésés sötét és világos oldala fel van cserélve"

    def test_a_veses_NEM_er_a_fogantyu_vegeig(self, _rajz):
        """A mért 5-5 képpontos behúzás: a fogantyú tetején és alján a
        vésés oszlopa már ugyanolyan, mint a szomszédja."""
        kep, doboz = _rajz
        sotet_x, _ = _veses_oszlopai(doboz)
        _x, y, _szeles, magas = doboz
        for sor, hol in ((int(y) + 1, "tetején"), (int(y) + magas - 2, "alján")):
            veses = _vilagossag(kep, sotet_x, sor)
            szomszed = _vilagossag(kep, sotet_x - 2, sor)
            assert abs(veses - szomszed) < MIN_SOTET_KULONBSEG, (
                f"a vésés a fogantyú {hol} is ott van (y={sor}: "
                f"{veses:.0f} vs {szomszed:.0f}) — a mért behúzás "
                f"{MERT_BEHUZAS} képpont"
            )

    def test_a_behuzas_PONTOSAN_a_mert_5_keppont(self, _rajz):
        """A két véget néző előző állítás vakfoltja: `vesesBehuzas: 2`
        mellett is átmenne, pedig az a mért értéktől 3 képponttal tér el.
        Ezért itt MEGSZÁMOLJUK a vésett sorokat, és a kezdetüket is
        megmérjük — a mért 19 tömör sorból 9 vésett (5-5 kimarad)."""
        kep, doboz = _rajz
        sotet_x, _ = _veses_oszlopai(doboz)
        _x, y, _szeles, magas = doboz
        sorok = [
            sor
            for sor in range(int(y), int(y) + magas)
            if _vilagossag(kep, sotet_x - 2, sor) - _vilagossag(kep, sotet_x, sor)
            >= MIN_SOTET_KULONBSEG
        ]
        assert sorok, "egyetlen vésett sor sincs — a vonal hiányzik"
        assert len(sorok) == magas - 2 * MERT_BEHUZAS, (
            f"{len(sorok)} vésett sor van a fogantyú {magas} sorából, "
            f"a mért behúzás mellett {magas - 2 * MERT_BEHUZAS} lenne"
        )
        assert min(sorok) - int(y) == MERT_BEHUZAS, (
            f"a vésés a fogantyú tetejétől {min(sorok) - int(y)} képponttal "
            f"kezdődik, a mért érték {MERT_BEHUZAS}"
        )


class TestAMasikMereten:
    """A szabály a fogantyú méretétől függetlenül él (mutáció-próba)."""

    def test_a_veses_a_masik_fogantyun_is_ott_van(self, _rajz_masik):
        kep, doboz = _rajz_masik
        _x, _y, szeles, magas = doboz
        assert (szeles, magas) == (MASIK_SZELES, MASIK_MAGAS)
        sotet_x, vilagos_x = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        sotet = _oszlop_atlaga(kep, sotet_x, y0, y1)
        vilagos = _oszlop_atlaga(kep, vilagos_x, y0, y1)
        hatter = (
            _oszlop_atlaga(kep, sotet_x - 2, y0, y1)
            + _oszlop_atlaga(kep, vilagos_x + 2, y0, y1)
        ) / 2
        assert hatter - sotet >= MIN_SOTET_KULONBSEG, (
            f"{szeles}×{magas}-os fogantyún nincs sötét vésés-oszlop "
            f"({sotet:.0f} vs {hatter:.0f})"
        )
        assert vilagos - hatter >= MIN_VILAGOS_KULONBSEG, (
            f"{szeles}×{magas}-os fogantyún nincs világos vésés-oszlop "
            f"({vilagos:.0f} vs {hatter:.0f})"
        )


#: FÜGGŐLEGES próba. A vésés ilyenkor VÍZSZINTES vonal, és a hossza a
#: fogantyú SZÉLESSÉGÉBŐL jön (`width - 2 * behúzás`) — ezért a próba
#: fogantyúja fekvő: 26 széles, 16 magas, akárcsak az `editslider/thumb`
#: elforgatva. A jegy elfogadási feltétele mindkét tájolás.
_FUGGOLEGES_SZELES = 26
_FUGGOLEGES_MAGAS = 16

_QML_FUGGOLEGES = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0
Rectangle {
    width: %d; height: %d
    color: "#ffffff"
    PicasaSlider {
        objectName: "proba"
        anchors.centerIn: parent
        orientation: Qt.Vertical
        height: parent.height
        grooveThickness: 9
        handleWidth: %d
        handleHeight: %d
        handleRadius: 3
        from: 0; to: 100; value: 50
    }
}
"""


def _rajzol_sablonnal(qt_app, sablon: str, ablak: tuple[int, int],
                      fogantyu_meret: tuple[int, int]):
    """Ugyanaz, mint a `_rajzol`, de tetszőleges QML-sablonnal."""
    import picasapy.app.application as app_module

    szeles_ablak, magas_ablak = ablak
    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(
        (sablon % (szeles_ablak, magas_ablak, *fogantyu_meret)).encode("utf-8"),
        QUrl(),
    )
    hibak = [hiba.toString() for hiba in component.errors()]
    assert hibak == [], hibak
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(szeles_ablak, magas_ablak)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)

    csuszka = root.findChild(object, "proba")
    assert csuszka is not None
    fogantyu = csuszka.property("handle")
    assert fogantyu is not None
    sarok = fogantyu.mapToScene(QPointF(0.0, 0.0))
    doboz = (
        sarok.x(), sarok.y(),
        round(fogantyu.width()), round(fogantyu.height()),
    )
    kep = view.grabWindow()
    _KEEPALIVE.extend((view, root, component))
    return kep, doboz


@pytest.fixture(scope="module")
def _rajz_fuggoleges(qt_app):
    # az ablak magassága páros, hogy a fogantyú EGÉSZ képpontra essen:
    # (40 − 16) / 2 = 12
    return _rajzol_sablonnal(
        qt_app, _QML_FUGGOLEGES, (60, 40),
        (_FUGGOLEGES_SZELES, _FUGGOLEGES_MAGAS),
    )


class TestFuggolegesCsuszkan:
    """A jegy elfogadási feltétele MINDKÉT tájolásra szól.

    Függőleges csúszkán a vésés vízszintes vonal: a SÖTÉT sor van felül, a
    világos alatta — ugyanaz a bal-felüli fényirány, mint vízszintesen
    (balra sötét, jobbra világos).
    """

    def _sorai(self, doboz) -> tuple[int, int]:
        _x, y, _szeles, magas = doboz
        kozep = int(y) + round(magas / 2)
        return (kozep - 1, kozep)

    def _oszlopai(self, doboz) -> tuple[int, int]:
        x, _y, szeles, _magas = doboz
        return (int(x) + MERT_BEHUZAS, int(x) + szeles - MERT_BEHUZAS)

    def _sor_atlaga(self, kep, sor: int, x0: int, x1: int) -> float:
        return sum(_vilagossag(kep, x, sor) for x in range(x0, x1)) / (x1 - x0)

    def test_a_fogantyu_doboza_ertelmes(self, _rajz_fuggoleges):
        _kep, (x, y, szeles, magas) = _rajz_fuggoleges
        assert (szeles, magas) == (_FUGGOLEGES_SZELES, _FUGGOLEGES_MAGAS)
        assert x == int(x) and y == int(y), (
            f"a fogantyú {(x, y)}-nél áll — nem egész képponton"
        )

    def test_a_veses_VIZSZINTES_vonal_a_kozepen(self, _rajz_fuggoleges):
        kep, doboz = _rajz_fuggoleges
        sotet_sor, vilagos_sor = self._sorai(doboz)
        x0, x1 = self._oszlopai(doboz)
        _x, y, _szeles, magas = doboz
        sotet = self._sor_atlaga(kep, sotet_sor, x0, x1)
        vilagos = self._sor_atlaga(kep, vilagos_sor, x0, x1)
        hatter = (
            self._sor_atlaga(kep, int(y) + 1, x0, x1)
            + self._sor_atlaga(kep, int(y) + magas - 2, x0, x1)
        ) / 2
        assert hatter - sotet >= MIN_SOTET_KULONBSEG, (
            f"függőleges csúszkán nincs sötét vésés-sor "
            f"(y={sotet_sor}: {sotet:.0f} vs a fogantyú {hatter:.0f})"
        )
        assert vilagos - hatter >= MIN_VILAGOS_KULONBSEG, (
            f"függőleges csúszkán nincs világos vésés-sor "
            f"(y={vilagos_sor}: {vilagos:.0f} vs {hatter:.0f})"
        )

    def test_a_SOTET_sor_FELUL_van(self, _rajz_fuggoleges):
        """Ha a kettő felcserélődne, az előző állítás még átmenne."""
        kep, doboz = _rajz_fuggoleges
        sotet_sor, vilagos_sor = self._sorai(doboz)
        x0, x1 = self._oszlopai(doboz)
        assert sotet_sor < vilagos_sor
        assert self._sor_atlaga(kep, sotet_sor, x0, x1) < self._sor_atlaga(
            kep, vilagos_sor, x0, x1
        ), "függőleges csúszkán a vésés sötét és világos oldala fel van cserélve"


class TestAVesesSzineiTemafuggoek:
    """#2663 — FORDÍTOTT elvárás a korábbi (`…NemTemafuggok`) próbához
    képest: mostantól a fogantyú ÉS a vésés is témafüggő, EGYÜTT (a #2641
    code review pontosan ezt a sorrendet kérte — lásd a Theme.qml
    kommentjét a `sliderHandleGrooveDark`/`…Light` fölött).

    A forrást olvassuk, mert a hiba természete forrás-szintű: egy
    visszacsúszott `dark ? …` ág törlése a kirajzolt próbán (ami csak EGY
    témában fut egyszerre) nem feltétlenül látszana minden konfiguráción.
    """

    def _theme_forras(self) -> str:
        import picasapy.app.application as app_module

        utvonal = app_module._APP_DIR / "qml" / "PicasaPy" / "Theme.qml"
        return utvonal.read_text(encoding="utf-8")

    def _slider_forras(self) -> str:
        import picasapy.app.application as app_module

        utvonal = app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaSlider.qml"
        return utvonal.read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "tulajdonsag",
        ["sliderHandleGrooveDark", "sliderHandleGrooveLight"],
    )
    def test_a_veses_szine_temafuggo(self, tulajdonsag):
        forras = self._theme_forras()
        sorok = [
            sor.strip()
            for sor in forras.splitlines()
            if tulajdonsag in sor and "property" in sor
        ]
        assert len(sorok) == 1, (
            f"a `{tulajdonsag}` {len(sorok)} helyen van megadva a Theme.qml-ben"
        )
        assert "dark ?" in sorok[0], (
            f"a `{tulajdonsag}` NEM témafüggő ({sorok[0]!r}). A fogantyú "
            "kitöltése #2663 óta témafüggő, a vésésnek EGYÜTT kell "
            "maradnia vele — lásd a Theme.qml megjegyzését."
        )

    def test_a_fogantyu_kitoltese_temafuggo(self):
        """A fenti szabály előfeltétele. Ha a fogantyú kitöltése (vagy a
        kerete) beégetett hexával térne vissza, ez a próba bukik — és
        emlékeztet rá, hogy a vésés a fogantyúval EGYÜTT módosítandó."""
        forras = self._slider_forras()
        kezd = forras.index("handle: Item")
        fogantyu_blokk = forras[kezd : forras.index("readonly property real vesesBehuzas")]
        assert "Theme.sliderHandle" in fogantyu_blokk, (
            "a fogantyú kitöltése/kerete nem a Theme tokenjeiből jön — "
            "#2663 óta ezeknek témafüggőnek kell lenniük"
        )
        for tiltott in ("#fdfdfd", "#e4e4e4", "#d8d8d8", "#c8c8c8", "#b5b5b5", "#8f8f8f"):
            assert tiltott not in fogantyu_blokk, (
                f"a fogantyú rajza beégetett {tiltott} színt tartalmaz — "
                "ennek a Theme.sliderHandle* tokenekből kellene jönnie"
            )


class TestAVesesSotetTemaban:
    """#2663 elfogadási feltétele: a vésés-őr fusson le SÖTÉT témára is, és
    a sötét oszlop a szomszédjánál LEGFELJEBB ~40-nel legyen sötétebb —
    vésés maradjon, ne csík (a #2641 review pontosan ETTŐL óvott egy
    korábbi, a világos fogantyúra hangolt kísérletnél: 193/133 volt a
    különbség, jóval e fölött)."""

    def _hatter(self, kep, doboz) -> float:
        sotet_x, vilagos_x = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        bal = _oszlop_atlaga(kep, sotet_x - 2, y0, y1)
        jobb = _oszlop_atlaga(kep, vilagos_x + 2, y0, y1)
        return (bal + jobb) / 2

    def test_a_SOTET_oszlop_ott_van_es_nem_csik(self, _rajz_sotet_tema):
        kep, doboz = _rajz_sotet_tema
        sotet_x, _ = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        veses = _oszlop_atlaga(kep, sotet_x, y0, y1)
        hatter = self._hatter(kep, doboz)
        kulonbseg = hatter - veses
        assert kulonbseg >= MIN_SOTET_KULONBSEG_SOTET_TEMA, (
            f"sötét témában a vésés sötét oszlopa (x={sotet_x}) {veses:.0f}, "
            f"a környező fogantyú {hatter:.0f} — a különbség {kulonbseg:.1f}, "
            f"a mérce {MIN_SOTET_KULONBSEG_SOTET_TEMA}"
        )
        assert kulonbseg <= MAX_SOTET_KULONBSEG_SOTET_TEMA, (
            f"sötét témában a vésés sötét oszlopa {kulonbseg:.1f}-cal "
            f"sötétebb a környezeténél — a jegy szerint ez fölötte már nem "
            f"vésés, hanem csík (felső korlát {MAX_SOTET_KULONBSEG_SOTET_TEMA})"
        )

    def test_a_VILAGOS_oszlop_ott_van(self, _rajz_sotet_tema):
        kep, doboz = _rajz_sotet_tema
        _, vilagos_x = _veses_oszlopai(doboz)
        y0, y1 = _veses_sorai(doboz)
        veses = _oszlop_atlaga(kep, vilagos_x, y0, y1)
        hatter = self._hatter(kep, doboz)
        assert veses - hatter >= MIN_VILAGOS_KULONBSEG_SOTET_TEMA, (
            f"sötét témában a vésés világos oszlopa (x={vilagos_x}) "
            f"{veses:.0f}, a környező fogantyú {hatter:.0f} — a mérce "
            f"{MIN_VILAGOS_KULONBSEG_SOTET_TEMA}"
        )

    def test_a_fogantyu_maga_is_sotet(self, _rajz_sotet_tema):
        """Előfeltétel: sötét témában a fogantyú TÉNYLEG sötétebb, mint
        világosban — különben a fenti két próba egy világos fogantyún
        futna, és semmit nem bizonyítana a sötét ágról."""
        kep, doboz = _rajz_sotet_tema
        hatter = self._hatter(kep, doboz)
        assert hatter < 180, (
            f"a fogantyú háttere sötét témában {hatter:.0f} — ez még "
            "mindig világos fogantyúnak látszik, a Theme.dark nem ért el "
            "a kitöltéshez"
        )
