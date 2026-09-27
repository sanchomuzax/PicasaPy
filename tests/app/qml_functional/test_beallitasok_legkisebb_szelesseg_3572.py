"""#3572 — a Beállítások ablak a legkisebb szélességén, magyarul se lógjon ki.

A hivatalos magyar feliratok hosszabbak az angolnál. Az átnézés mérte, hogy
a `minimumWidth` (480 px) szélességen egy nem tördelődő jelölő-felirat
kitolja a fül tartalmát, és vele a fülsort és a „Tallózás…” gombokat is.

Az őr a VALÓDI `OptionsDialog`-ot tölti be a magyar `.qm`-mel a legkisebb
szélességen, és kimondja: a Webalbumok fül hosszú feliratai tördelődnek, és
nem szélesítik a fület. Geometriát mér, képet nem hasonlít referenciához.

#3661 — a fülsor: a korábbi, ad-hoc mérés (nem a csomagolt Open Sans-szal,
nem a `PicasaStyle`/`Fusion` stílussal) betűkészlet-függőnek látta a teljes
ablak kilógását. A `qml_app` fixture viszont UGYANAZT a csomagolt betűt és
stílust tölti be, amivel az éles app is indul (#901/#3279) — ezzel mérve a
8 magyar fülcím összesen ~646 px-et kér 456 px rendelkezésre álló helyen a
legkisebb (480 px-es) ablakszélességen, függetlenül a futtató gép
rendszerbetűitől. Ezt a lenti `test_a_fulsor_gorgethetov_valik_es_nem_log_ki`
mondja ki.

Az átnézés (#3661 2. köre) két további, geometriára/láthatóságra épülő őrt
kért, mert az első kör csak `clip`/`implicitWidth`-et nézett, ami NEM
garantálja, hogy semmi nem lóg ki, és azt sem, hogy alapméreten minden fül
görgetés nélkül elfér:

- `test_480_pxen_semmilyen_lathato_elem_nem_log_ki_egyik_fulon_sem` — mind a
  8 fülre, kattintással váltva, minden LÁTHATÓ elem `mapToScene`-nel számolt
  jobb széle az ablakon belül marad (a `clip: true` elemek BELSEJÉBE nem megy
  le, hiszen az ottani túlcsordulást szándékosan levágja a keret).
- `test_alapmereten_minden_fulcim_teljesen_a_fulsoron_belul_van` — a dialógus
  MEGNYITÁSKORI (nem összehúzott) szélességén mind a 8 fülcím teljesen a
  fülsoron belül van, görgetés nélkül; a fülváltás kattintással történik.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt, QTranslator, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app

_I18N_DIR = Path(picasapy.app.__file__).parent / "i18n"
_TURES = 1.0
_ELETBEN: list = []


def _latszo_elemek(gyoker: QQuickItem):
    for gyerek in gyoker.childItems():
        if not gyerek.isVisible() or gyerek.opacity() == 0:
            continue
        yield gyerek
        yield from _latszo_elemek(gyerek)


def _latszo_elemek_vagas_hataran(gyoker: QQuickItem):
    """Mint `_latszo_elemek`, de `clip: true` elemnél MEGÁLL — a levágó
    elemet magát még jelenti, a belsejébe már nem megy le. A fülsor
    (`TabBar`) és a fülverem (`StackLayout`) is `clip: true`: az ezeken
    BELÜLI, a látható sávnál szélesebb tartalom szándékosan levágott, tehát
    nem a mi hibánk, ha a jobb széle a vágó elemen túl esne."""
    for gyerek in gyoker.childItems():
        if not gyerek.isVisible() or gyerek.opacity() == 0:
            continue
        yield gyerek
        if gyerek.clip():
            continue
        yield from _latszo_elemek_vagas_hataran(gyerek)


def _kattints_kozepere(ablak, qt_app, elem):
    """Valódi bal kattintás `elem` közepére (a `test_qml_options_dialog.py`
    `_kattints`-mintája) — a fülváltás a tesztekben ETTŐL kezdve
    kattintással, nem a `currentIndex` tulajdonság közvetlen írásával
    történik."""
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _uj_ablak(qml_app, qt_app, fordito):
    _window, _controller, engine = qml_app
    engine.retranslate()
    komponens = QQmlComponent(engine)
    komponens.setData(b"import PicasaPy 1.0\nOptionsDialog { visible: true }\n", QUrl())
    assert komponens.errors() == [], [h.toString() for h in komponens.errors()]
    ablak = komponens.create()
    assert ablak is not None
    QQmlEngine.setObjectOwnership(ablak, QQmlEngine.ObjectOwnership.CppOwnership)
    # ⚠️ a `komponens`-t IS életben kell tartani, nem csak az `ablak`-ot: ha a
    # QQmlComponent Python-oldali wrappere ITT, a függvény visszatérésekor
    # GC-re kerülne, az ablakot is magával rántja („Internal C++ object
    # already deleted” a fixture KÖVETKEZŐ sorában) — mérve, amikor a
    # komponens-létrehozást ebbe a segédfüggvénybe emeltem ki.
    _ELETBEN.append(komponens)
    _ELETBEN.append(ablak)
    qt_app.processEvents()
    return ablak


@pytest.fixture
def magyar_beallitasok(qml_app, qt_app):
    fordito = QTranslator(qt_app)
    assert fordito.load("picasapy_hu", str(_I18N_DIR))
    qt_app.installTranslator(fordito)
    ablak = _uj_ablak(qml_app, qt_app, fordito)
    ablak.setProperty("width", ablak.property("minimumWidth"))
    qt_app.processEvents()
    try:
        yield ablak
    finally:
        ablak.setProperty("visible", False)
        qt_app.removeTranslator(fordito)
        _ELETBEN.clear()


@pytest.fixture
def magyar_beallitasok_alapmereten(qml_app, qt_app):
    """Mint `magyar_beallitasok`, de a dialógus MEGNYITÁSKORI (nem a
    legkisebbre összehúzott) szélességén marad — ezen a méreten a 8 fülnek
    görgetés nélkül kell elférnie (#3661 2. lelet)."""
    fordito = QTranslator(qt_app)
    assert fordito.load("picasapy_hu", str(_I18N_DIR))
    qt_app.installTranslator(fordito)
    ablak = _uj_ablak(qml_app, qt_app, fordito)
    try:
        yield ablak
    finally:
        ablak.setProperty("visible", False)
        qt_app.removeTranslator(fordito)
        _ELETBEN.clear()


_WEBALBUM_JELOLOK = (
    "optionsWebStripedUploadCheck",
    "optionsWebKeepJpegQualityCheck",
    "optionsWebConfirmSyncDisableCheck",
)


def test_a_webalbum_hosszu_feliratai_tordelodnek(magyar_beallitasok, qt_app):
    """A #3572 saját feliratai: a hosszú magyar szöveg tördelődik, és nem
    szélesíti a fület (a kiváltó mérésben 652 px-re tolta a tartalmat)."""
    ablak = magyar_beallitasok
    ablak.findChild(QObject, "optionsTabBar").setProperty("currentIndex", 6)
    for _ in range(5):
        qt_app.processEvents()
    verem = ablak.findChild(QObject, "optionsTabStack")
    for nev in _WEBALBUM_JELOLOK:
        jelolo = ablak.findChild(QObject, nev)
        assert jelolo.property("width") <= verem.property("width") + _TURES, nev
    # a leghosszabb feliratnak ténylegesen több sorba kell törnie
    hosszu = ablak.findChild(QObject, "optionsWebStripedUploadCheck")
    assert hosszu.property("contentItem").property("lineCount") > 1, "nem tördelődik"


_FUL_NEVEK = (
    "optionsTabGeneral",
    "optionsTabEmail",
    "optionsTabFileTypes",
    "optionsTabSlideshow",
    "optionsTabPrinting",
    "optionsTabNetwork",
    "optionsTabWebAlbums",
    "optionsTabNameTags",
)


def test_a_fulsor_gorgethetov_valik_es_nem_log_ki(magyar_beallitasok, qt_app):
    """#3661: a 8 magyar fülcím (csomagolt Open Sans-szal mérve, ahogy az
    éles app is indul) összesen szélesebb, mint a legkisebb ablakszélesség
    (mérve: ~646 px a rendelkezésre álló 456 px-hez). A `TabBar` Fusion-
    stílusa ezt eddig egyenlő, túl szűk részekre osztotta el — a fülcímek
    (`IconLabel`/`Text`) nem tördelődnek és nem "elide"-olódnak, ezért a
    szomszédos fülekre, a legutolsó pedig a fülsoron túlra folyt volna.

    A javítás után minden fülgomb a SAJÁT feliratának megfelelő (implicit)
    szélességet kapja — tehát semelyik gombot nem szűkíti a fülsor —, a
    `TabBar` pedig `clip: true`, így a 456 px-en túli rész nem látható
    tartalom, hanem a görgethető (`ListView`-alapú) fülsoron kívül eső,
    levágott rész."""
    ablak = magyar_beallitasok
    tabBar = ablak.findChild(QObject, "optionsTabBar")
    assert tabBar.property("clip") is True, "a fülsoron túli rész kilóghat"
    for nev in _FUL_NEVEK:
        gomb = ablak.findChild(QObject, nev)
        assert gomb.property("width") == pytest.approx(
            gomb.property("implicitWidth"), abs=_TURES
        ), f"{nev}: a fülsor összeszűkítette a saját feliratánál"


def test_480_pxen_semmilyen_lathato_elem_nem_log_ki_egyik_fulon_sem(
    magyar_beallitasok, qt_app
):
    """#3661 (2. kör, 3. lelet) — GEOMETRIAI, láthatóságra épülő őr.

    Az első kör őre (fent) csak `clip`/`implicitWidth`-et nézett — ez NEM
    garantálja, hogy semmi nem lóg ki: pl. egy nem tördelődő jelölő-felirat
    (`optionsMailUseHtmlCheck`, `optionsUsageStatsCheck`) a fül SAJÁT
    tartalmának implicit szélességét húzza fel anélkül, hogy a `TabBar`-hoz
    bármi köze lenne.

    Ez az őr minden fülre VALÓDI kattintással vált (nem a `currentIndex`
    tulajdonság közvetlen írásával), és a fülváltás UTÁN megméri: az ablak
    teljes látható elemfájának (a `clip: true` elemek BELSEJE nélkül, hiszen
    az ottani túlcsordulás szándékosan levágott) minden tagja `mapToScene`-
    nel számolt jobb széle az ablak szélességén BELÜL marad."""
    ablak = magyar_beallitasok
    ablak_szelesseg = ablak.property("width")
    for nev in _FUL_NEVEK:
        gomb = ablak.findChild(QObject, nev)
        _kattints_kozepere(ablak, qt_app, gomb)
        for elem in _latszo_elemek_vagas_hataran(ablak.contentItem()):
            jobb_szel = elem.mapToScene(QPointF(elem.width(), 0)).x()
            assert jobb_szel <= ablak_szelesseg + _TURES, (
                f"{nev}: {elem.objectName() or elem} túllóg "
                f"({jobb_szel} > {ablak_szelesseg})"
            )


def test_alapmereten_minden_fulcim_teljesen_a_fulsoron_belul_van(
    magyar_beallitasok_alapmereten, qt_app
):
    """#3661 (2. kör, 2. lelet) — a dialógus MEGNYITÁSKORI (nem összehúzott)
    szélességén mind a 8 fülcím görgetés NÉLKÜL, teljesen a fülsoron belül
    látszik — a mainen ez már így volt, a PR alatt viszont az első fül
    balról levágva, a „Névcímkék”-ből csak „N” látszott (regresszió).

    A fülváltás itt is kattintással történik; minden fülre kattintás UTÁN
    ellenőrizzük, hogy a KATTINTOTT fülgomb `mapToScene`-nel számolt bal ÉS
    jobb széle egyaránt a fülsoron (`optionsTabBar`) belül van."""
    ablak = magyar_beallitasok_alapmereten
    tab_bar = ablak.findChild(QObject, "optionsTabBar")
    bal_hatar = tab_bar.mapToScene(QPointF(0, 0)).x()
    jobb_hatar = tab_bar.mapToScene(QPointF(tab_bar.width(), 0)).x()
    for nev in _FUL_NEVEK:
        gomb = ablak.findChild(QObject, nev)
        _kattints_kozepere(ablak, qt_app, gomb)
        gomb_bal = gomb.mapToScene(QPointF(0, 0)).x()
        gomb_jobb = gomb.mapToScene(QPointF(gomb.width(), 0)).x()
        assert gomb_bal >= bal_hatar - _TURES, (
            f"{nev}: a fülcím bal széle a fülsor elé lóg ({gomb_bal} < {bal_hatar})"
        )
        assert gomb_jobb <= jobb_hatar + _TURES, (
            f"{nev}: a fülcím jobb széle túllóg a fülsoron "
            f"({gomb_jobb} > {jobb_hatar})"
        )
    # görgetés nélkül: a fülsor nyilai ezen a méreten nem jelennek meg
    for nyil in ("optionsTabScrollLeftButton", "optionsTabScrollRightButton"):
        gomb = ablak.findChild(QObject, nyil)
        assert gomb.property("visible") is False, (
            f"{nyil}: alapméreten nem kéne görgetnie a fülsornak"
        )
