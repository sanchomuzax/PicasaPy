"""Túlcsordulás-őr a SAJÁT felületünkön — a #656 első, legolcsóbb lépése.

## Miért ez az első lépés

A #656 négy fázist tervez (a `.tre`-referencia beolvasása, a mi modellünk,
összehasonlító, riport). A jegy maga mondja ki, hogy az **R4 szabály —
túlcsordulás, nem-illeszkedés — REFERENCIA NÉLKÜL is mérhető**, tiszta
invariánsként a saját felületünkön, és hogy ez fogná meg a tulajdonos
egyik panaszát („a Holo effekt csúszkái nem férnek a bal oszlop
szélességébe").

Ez a modul azt az invariánst tartatja be, több felület-ÁLLAPOTBAN
végigjárva a jelenetet: **a felhasználó lássa a tartalmat**, azaz

1. **vágó keret ne vágjon le elemet** — `clip: true` konténerbe nem férő
   gyerek képpontjai egyszerűen nem rajzolódnak ki;
2. **ne legyen levágott (elidált) felirat** — a `Text.truncated` mondja meg;
3. **feliratnak ne fogyjon el vízszintesen a hely** vágó kereten belül —
   ott karakter vész el.

## Amit MA mér (2026-09-17)

Mind a három invariáns **teljesül** — egyetlen, nevesített kivétellel
(`legacyEffectsIntro`, lásd `_KIVETELEK` és a #3278; a fejlesztői gépen
elfér, a CI nagyobb betűjével elidálódik) — a vizsgált nyolc állapotban: a rácson, a
nézőben és a szerkesztő mind a hét fülén **nulla** találat. Az őr tehát
REGRESSZIÓT fog: a #703/#3247 körökben kitakarított hibaosztály nem jöhet
vissza némán.

⚠️ **Nem vakon zöld:** a `TestAzOrnekVanFoga` mesterséges levágást és
elidált feliratot állít elő, és megköveteli, hogy a kereső MINDKETTŐT
meglássa.

## Amit NEM mér — és miért

- **A puszta „kilóg a szülőjéből" NEM lelet**, ha semmi nem vágja el. Mérve:
  a 30×31-es `viewerPrevIcon` egy 20 képpontos `contentItem`-ben, a ✕ glifa
  (8,4 képpont) a `captionTrashButton` 5 képpontos tartalom-dobozában — mind
  a kettő hiánytalanul kirajzolódik, a gomb 17 képpontos keretén belül. A
  helyes ELHELYEZÉST a #656 további fázisa, a `.tre`-hez mérés (R2/R3) fogja.
- **A szöveg SORDOBOZÁNAK függőleges túllógása sem lelet** — a részleteket a
  `_vizszintes_levagas` docstringje mondja el (`trayInfoText` / `trayInfoBar`).
- **Transzformációt nem hagyunk figyelmen kívül**: a `histogramBitmap`
  256×70-es belső képe `Scale`-lel kerül a 213×59-es keretbe (#864); a
  kereső `mapRectToItem`-mel mér, ezért ez helyesen NEM lelet.
- **A görgethető tartalom** (`Flickable`/`ListView`/…) szándékosan lóg túl,
  ezért kimarad.
- A `.tre`-referenciához mért ELHELYEZÉST (R2/R3/R5) — az a #656 további
  fázisa.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QRectF, Qt

#: fél képpont: a QML lebegőpontos geometriája kerekítésből is adhat
#: hajszálnyi eltérést — az nem hiba
TURES = 0.5


def _lathato(elem: QObject) -> bool:
    return bool(elem.property("visible"))


def _gorgetheto_belsejeben(elem: QObject) -> bool:
    """`Flickable`/`ScrollView` tartalma — ott a túllógás SZÁNDÉKOS."""
    szulo = elem.parent()
    while szulo is not None:
        nev = szulo.metaObject().className()
        if "Flickable" in nev or "ScrollView" in nev or "ListView" in nev:
            return True
        szulo = szulo.parent()
    return False


def _meret(elem: QObject, nev: str) -> float:
    ertek = elem.property(nev)
    try:
        return float(ertek)
    except (TypeError, ValueError):
        return 0.0


def _nev(elem: QObject) -> str:
    return elem.objectName() or elem.metaObject().className()


#: Az EGÉRESEMÉNY-elemek szándékosan nagyobbak a gazdájuknál: a kis
#: ikonoknak nagyobb találati felület jár (mérve: a `captionToggleButton`
#: 17×13 gombja alatt 27×23-as `MouseArea`). Ez bevett minta, nem hiba.
_ESEMENY_ELEMEK = ("MouseArea", "Handler", "DropArea")

#: Görgethető tartalom: ott a túllógás a görgetés ÉRTELME.
_GORGETHETO = ("Flickable", "ScrollView", "ListView", "GridView", "PathView")


def _esemeny_elem(elem: QObject) -> bool:
    nev = elem.metaObject().className()
    return any(minta in nev for minta in _ESEMENY_ELEMEK)


#: NEVESÍTETT kivétel — pontosan EGY felirat, jeggyel a kezében.
#:
#: A `legacyEffectsIntro` a fejlesztői gépen elfér két sorban, a CI mindkét
#: lábán viszont (nagyobb rendszerbetű) elidálódik. A #3263 szándékosan
#: adott neki `maximumLineCount: 2` + `elide` végszükség-őrt, hogy a hosszú
#: szöveg ne nyomja ki a szűrő-rácsot a fülről — a szöveg olvashatóságát
#: viszont az nem oldja meg. A döntés a #3278-on: rövidebb mondat,
#: buboréksúgó vagy három soros elrendezés. Amíg az nyitva van, ez az EGY
#: felirat átmehet; MINDEN más levágás piros marad.
_KIVETELEK = ("legacyEffectsIntro",)


def _szoveg_elem(elem: QObject) -> bool:
    return elem.metaObject().indexOfProperty("truncated") >= 0


def _vago_os(elem: QObject) -> QObject | None:
    """A legközelebbi VÁGÓ ős — görgethető ősnél `None`.

    A görgetett tartalom szándékosan lóg túl, ezért ott nincs lelet.
    """
    szulo = elem.parent()
    while szulo is not None and szulo.metaObject().indexOfProperty("width") >= 0:
        nev = szulo.metaObject().className()
        if any(minta in nev for minta in _GORGETHETO):
            return None
        if bool(szulo.property("clip")):
            return szulo
        szulo = szulo.parent()
    return None


def _vizszintes_levagas(elem: QObject, tartalom: float) -> list[str]:
    """Feliratnál CSAK a vízszintes levágás lelet.

    ⚠️ A függőleges szándékosan marad ki: a `Text` SORDOBOZA magasabb, mint
    a betűk tintája, a mért sávmagasságaink pedig szorosak. A `trayInfoText`
    17 képpontos sordoboza a 14 képpontos `trayInfoBar`-ban (mérve, #1914)
    föl-le 1,5 képpontnyi SORKÖZT veszít, betűt nem — ez nem hiba, és ha
    leletnek vennénk, az őr az első napjától zajos volna.
    """
    vago = _vago_os(elem)
    if vago is None or not hasattr(elem, "mapRectToItem"):
        return []
    szelesseg = max(_meret(elem, "width"), tartalom)
    teglalap = elem.mapRectToItem(vago, QRectF(0, 0, szelesseg, 1))
    keret_sz = _meret(vago, "width")
    if teglalap.left() < -TURES or teglalap.right() > keret_sz + TURES:
        return [
            f"{_nev(elem)}: a feliratot vízszintesen levágja a(z) "
            f"{_nev(vago)} — x={teglalap.left():.0f}.."
            f"{teglalap.right():.0f}, keret 0..{keret_sz:.0f}"
        ]
    return []


def tulcsordulasok(gyoker: QObject) -> list[str]:
    """Ami ténylegesen ELVÉSZ a felületről.

    Két, egymástól független eset — mindkettő azt jelenti, hogy a
    felhasználó NEM LÁTJA a tartalom egy részét:

    1. **vágó ős levágja** az elemet (`clip: true` konténer, ami nem
       görgethető) — a képpontok egyszerűen nem rajzolódnak ki;
    2. **feliratnál elfogy a szélesség** (`truncated`, illetve
       `contentWidth > width`) — ott karakter vész el.

    ⚠️ Amit SZÁNDÉKOSAN nem hívunk hibának: ha egy elem a szülője
    téglalapján kilóg, de semmi nem vágja el (pl. a 30×31-es
    `viewerPrevIcon` egy 20 képpontos `contentItem`-ben, vagy a 256×70-es
    `histogramBitmap` a keretében) — az kirajzolódik, tehát nem veszett el
    semmi. Ezt a #656 további fázisa, a `.tre`-hez mért ELHELYEZÉS (R2/R3)
    fogja megfogni, nem ez az őr.
    """
    talalat = []
    for elem in gyoker.findChildren(QObject):
        if elem.metaObject().indexOfProperty("width") < 0 or not _lathato(elem):
            continue
        if _esemeny_elem(elem) or _nev(elem) in _KIVETELEK:
            continue
        if _szoveg_elem(elem):
            if bool(elem.property("truncated")):
                talalat.append(
                    f"{_nev(elem)}: levágott felirat — "
                    f"{elem.property('text')!r}"
                )
                continue
            szelesseg = _meret(elem, "width")
            tartalom = _meret(elem, "contentWidth")
            if (
                bool(elem.property("clip"))
                and szelesseg > 0
                and tartalom > szelesseg + TURES
            ):
                talalat.append(
                    f"{_nev(elem)}: a saját kerete vágja — a szöveg "
                    f"{tartalom:.0f} képpont, a hely {szelesseg:.0f}"
                )
                continue
            talalat.extend(_vizszintes_levagas(elem, tartalom))
            continue
        vago = _vago_os(elem)
        if vago is None or not hasattr(elem, "mapRectToItem"):
            continue
        szelesseg = max(_meret(elem, "width"), _meret(elem, "contentWidth"))
        magassag = max(_meret(elem, "height"), _meret(elem, "contentHeight"))
        if szelesseg <= 0 or magassag <= 0:
            continue
        # ⚠️ `mapRectToItem`, nem kézi x/y-összegzés: a jelenetben
        # TRANSZFORMÁCIÓ is lehet (a `histogramBitmap` 256×70-es belső képe
        # egy `Scale`-lel kerül a 213×59-es keretbe, #864) — összeadva az
        # hamis leletet adna, leképezve viszont pontosan illeszkedik.
        teglalap = elem.mapRectToItem(vago, QRectF(0, 0, szelesseg, magassag))
        keret_sz = _meret(vago, "width")
        keret_ma = _meret(vago, "height")
        if teglalap.left() < -TURES or teglalap.right() > keret_sz + TURES:
            talalat.append(
                f"{_nev(elem)}: vízszintesen levágja a(z) {_nev(vago)} — "
                f"x={teglalap.left():.0f}..{teglalap.right():.0f}, "
                f"keret 0..{keret_sz:.0f}"
            )
        if teglalap.top() < -TURES or teglalap.bottom() > keret_ma + TURES:
            talalat.append(
                f"{_nev(elem)}: függőlegesen levágja a(z) {_nev(vago)} — "
                f"y={teglalap.top():.0f}..{teglalap.bottom():.0f}, "
                f"keret 0..{keret_ma:.0f}"
            )
    return talalat


def levagott_feliratok(gyoker: QObject) -> list[str]:
    """Elidált (levágott) szövegek — a `Text.truncated` mondja meg."""
    return [
        f"{_nev(elem)}: {str(elem.property('text'))[:40]!r}"
        for elem in gyoker.findChildren(QObject)
        if elem.metaObject().indexOfProperty("truncated") >= 0
        and _lathato(elem)
        and elem.property("truncated")
        and _nev(elem) not in _KIVETELEK
    ]


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = window.findChild(QObject, "photoViewer")
    assert nezo is not None
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    qt_app.processEvents()
    return nezo


class TestARacsEsANezo:
    def test_a_racson_nincs_tulcsordulas(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        qt_app.processEvents()

        assert tulcsordulasok(window) == []

    def test_a_racson_nincs_levagott_felirat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        qt_app.processEvents()

        assert levagott_feliratok(window) == []

    def test_a_nezoben_nincs_tulcsordulas(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert tulcsordulasok(window) == []

    def test_a_nezoben_nincs_levagott_felirat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert levagott_feliratok(window) == []


class TestASzerkesztoMindenFule:
    """A hét fül külön ÁLLAPOT — a hiba fülenként más lehet."""

    @pytest.mark.parametrize("lap", range(7))
    def test_a_fulon_nincs_tulcsordulas_es_levagas(self, lap, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None
        panel.setProperty("activeTab", lap)
        qt_app.processEvents()

        assert tulcsordulasok(window) == []
        assert levagott_feliratok(window) == []


class TestAzOrnekVanFoga:
    """⚠️ Mutáció-próba: a kereső MEGLÁTJA a mesterséges hibát.

    Enélkül a fenti nyolc üres lista bármit jelenthetne — például azt is,
    hogy a bejárás nem talál elemeket. A két próba a két leletfajtát külön
    állítja elő: vágó kerettel levágott ELEMET és levágott FELIRATOT."""

    def test_a_levagott_elemet_eszreveszi(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        assert tulcsordulasok(window) == []

        # A léptető ikonja 30 képpont széles egy 20 képpontos
        # `contentItem`-ben — ma ez NEM lelet, mert semmi nem vágja el.
        # Ha a keret vágni kezd, az ikon széle tényleg elvész: pontosan
        # ezt kell meglátnia az őrnek.
        ikon = window.findChild(QObject, "viewerPrevIcon")
        assert ikon is not None, "a léptető ikonja kell a próbához"
        keret = ikon.parent()
        keret.setProperty("clip", True)
        qt_app.processEvents()
        try:
            assert any(
                "viewerPrevIcon" in sor for sor in tulcsordulasok(window)
            )
        finally:
            keret.setProperty("clip", False)

    def test_a_levagott_feliratot_eszreveszi(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        qt_app.processEvents()
        assert levagott_feliratok(window) == []
        assert tulcsordulasok(window) == []

        # A tálca kék infó-sávjának feliratát vágatjuk le: egy sorra
        # korlátozott tördeléssel a hosszú szöveg `truncated` lesz.
        #
        # ⚠️ Miért nem az `elide`-dal? A `TextElideMode` enumhoz nincs
        # converter a kötésben — olvasni kifejezetten hibát ad ("Can't find
        # converter for 'QQuickText::TextElideMode'"), írni pedig NÉMÁN
        # hatástalan (mérve: `contentWidth` 15600 a 1240 képpontos sávban,
        # `truncated` mégis hamis maradt). A `wrapMode`/`maximumLineCount`
        # páros viszont átmegy, és ugyanazt a levágást állítja elő.
        # A SZÉLESSÉGET nem bántjuk: horgonyzott elemnél az első
        # elrendezéskor visszaíródna.
        felirat = window.findChild(QObject, "trayInfoText")
        assert felirat is not None, "a tálca infó-felirata kell a próbához"
        eredeti_szoveg = felirat.property("text")
        felirat.setProperty("wrapMode", 3)  # Text.WrapAnywhere
        felirat.setProperty("maximumLineCount", 1)
        felirat.setProperty("text", "nagyon hosszú felirat " * 200)
        qt_app.processEvents()
        try:
            assert levagott_feliratok(window) != []
            # a fő kereső is meglátja — a `truncated` ott is lelet
            assert any(
                "trayInfoText" in sor for sor in tulcsordulasok(window)
            )
        finally:
            felirat.setProperty("text", eredeti_szoveg)
            felirat.setProperty("maximumLineCount", 2**31 - 1)
            felirat.setProperty("wrapMode", 0)  # Text.NoWrap
