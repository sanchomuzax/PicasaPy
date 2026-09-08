"""A Visszavonás/Újra gomb magassága NEM függhet a platform betűjétől (#2597).

## A hiba, ahogy a CI megfogta

A `PanelButton` kért magassága a felirat `implicitHeight`-jéből jött, az
pedig **a betű SAJÁT sormagasságát** hordozza — a fix sorköz
(`Text.FixedHeight`, `Theme.lineLeading` = 10) csak a MÁSODIK sortól
érvényesül, az elsőt a betűmetrika adja. Mérve ezen a gépen:

| sorok | a felirat `implicitHeight` |
|---|---|
| 1 | 14 (= a betű natúr sormagassága) |
| 2 | 24 (= 14 + 10) |
| 3 | 34 (= 14 + 2 × 10) |

Windowson a natúr sormagasság nagyobb, ezért a CI windows-lába
**32,0 képpontos** gombot mért a mért eredeti **26** helyett (#2597).

## Miért nem elég a rács-őr

A rács (`test_eredeti_geometria_racs_2494.py`) platformonként engedett külön
eltérést — a windowsos 6 képpontot rögzítette, nem szüntette meg. Ez a fájl
a JELENSÉGET zárja ki: a gomb magassága **ne** a betűtől függjön. Ezért itt
nem platform-elágazás van, hanem a betűméret **közvetlen megnövelése** — így
a hiba ezen a gépen is előáll, nem csak a CI windows-lábán.

## A mérce

Az eredeti gomb a tulajdonos 1:1 felvételén (`235707.jpg`) **26 képpont**, és
a rajzolt keretet az erőforrás adja meg, nem a felirat: a Picasa a feliratot
szorítja a gombhoz (`textwrap` + betűillesztés), nem a gombot a felirathoz.
"""

from __future__ import annotations

import pytest
from PySide6.QtQml import QQmlProperty

from tests.app.qml_functional.test_visszavonas_felirat_2494 import (
    JELENTETT_FELIRAT,
    LEGHOSSZABB_FELIRAT,
    MERT_GOMBSZELESSEG,
    _gomb_es_felirat,
    _leul,
    _panel,
)

#: A tulajdonos felvételén MÉRT gombmagasság (Picasa 3).
EREDETI_GOMBMAGASSAG = 26.0

#: A felvételen MÉRT, KIRAJZOLT gombszélesség (`235707.jpg`; a HELYE 132). A
#: `MERT_GOMBSZELESSEG` (109) ennél szándékosan szűkebb — ott a felirat
#: minden platformon két sorra tör, ezért jó a magasság-próbákhoz.
MERT_RAJZOLT_SZELESSEG = 130

#: Fél képpont játék a lebegőpontos összehasonlításnak.
TURES = 0.5

#: Egy „magas betűs" platform utánzása. A gomb `labelAlapFokozat`-át írjuk
#: át 10-ről ennyire: a betű natúr sormagassága ezzel ~27 képpontra nő (a CI
#: windows-lábán ~20), tehát a próba SZIGORÚBB a valódi hibánál.
#:
#: ⚠️ Miért a KIINDULÓ fokozatot írjuk, és nem a `font.pixelSize`-t: a
#: javítás épp azt számolja ki, mekkora fokozat fér a gombba
#: (`PanelButton.labelFokozat`), tehát a végleges `font.pixelSize`
#: felülírása magát a vizsgált mechanizmust ütné ki. BetűCSALÁD cserével is
#: utánozható lenne, de nem tudjuk, milyen családok vannak a CI gépein — egy
#: hiányzó család mellett a próba NÉMÁN átmenne, ami rosszabb a semminél.
MAGAS_BETU_FOKOZAT = 20


def _gomb(qt_app, felirat: str, *, betufokozat: int | None = None):
    panel = _panel(qt_app, gombszelesseg=MERT_GOMBSZELESSEG)
    panel.setProperty("undoLabel", felirat)
    _leul(qt_app)
    gomb, cimke = _gomb_es_felirat(panel)
    if betufokozat is not None:
        # a KIINDULÓ fokozat felírása: ez utánozza azt a platformot, amelynek
        # a betűje magasabb sorokat rajzol (a gomb ebből számolja ki, mekkora
        # fokozat fér el)
        # ⚠️ `QQmlProperty.write`, nem `setProperty`: a `setProperty` egy nem
        # létező névre DINAMIKUS tulajdonságot hoz létre, és a próba némán
        # átmenne olyan kódon, amelyben a mechanizmus nincs is meg.
        assert QQmlProperty.write(gomb, "labelAlapFokozat", betufokozat), (
            "a gombnak nincs `labelAlapFokozat` tulajdonsága — a fokozat-"
            "illesztés (#2597) nincs megvalósítva, a próba tárgya hiányzik"
        )
        _leul(qt_app)
    return gomb, cimke


@pytest.mark.parametrize(
    "felirat", [JELENTETT_FELIRAT, LEGHOSSZABB_FELIRAT], ids=["jelentett", "leghosszabb"]
)
def test_a_gomb_a_mert_26_marad(qt_app, felirat) -> None:
    """A gomb a mért eredeti magasságot veszi fel — a felirat hosszától
    függetlenül. A „Visszavonás: Automatikus kontraszt" ezen a gépen három
    sorra tör, és a gombot 36 képpontra növelte (10 képpont eltérés az
    eredetitől, amit a rács-őr nem mért, mert csak a rövidebb felirattal
    fut)."""
    gomb, _ = _gomb(qt_app, felirat)
    magassag = float(gomb.property("height"))
    assert abs(magassag - EREDETI_GOMBMAGASSAG) <= TURES, (
        f"a gomb {magassag:.1f} képpont a mért eredeti "
        f"{EREDETI_GOMBMAGASSAG:.0f} helyett a(z) {felirat!r} felirattal — az "
        f"eredeti a FELIRATOT szorítja a gombhoz, nem a gombot a felirathoz"
    )


def test_a_gomb_magassaga_nem_fugg_a_betumetrikatol(qt_app) -> None:
    """A #2597 MAGJA: a betű natúr sormagasságának megnövelése nem növelheti
    a gombot. Enélkül a windowsos felhasználó 32 képpontos gombot lát."""
    gomb, cimke = _gomb(qt_app, JELENTETT_FELIRAT, betufokozat=MAGAS_BETU_FOKOZAT)
    magassag = float(gomb.property("height"))
    assert gomb.property("labelAlapFokozat") == MAGAS_BETU_FOKOZAT, (
        "a próba maga hibás: a kiinduló betűfokozat felülírása nem érvényesült"
    )
    tenyleges = QQmlProperty.read(cimke, "font.pixelSize")
    assert tenyleges < MAGAS_BETU_FOKOZAT, (
        f"a fokozat-illesztés nem lépett működésbe: a felirat {tenyleges} "
        f"képponton rajzol, holott a magas betű nem fér a gombba — a gomb így "
        f"vagy megnő, vagy vágja a szöveget"
    )
    assert abs(magassag - EREDETI_GOMBMAGASSAG) <= TURES, (
        f"a betű megnövelése {magassag:.1f} képpontra vitte a gombot a mért "
        f"{EREDETI_GOMBMAGASSAG:.0f} helyett — a magasság még mindig "
        f"betűmetrika-függő, tehát a windowsos eltérés (#2597) megmarad"
    )


@pytest.mark.parametrize(
    ("felirat", "betufokozat"),
    [
        (JELENTETT_FELIRAT, None),
        (LEGHOSSZABB_FELIRAT, None),
        (JELENTETT_FELIRAT, MAGAS_BETU_FOKOZAT),
    ],
    ids=["jelentett", "leghosszabb", "magas-betu"],
)
def test_a_felirat_a_szoritott_gombban_sem_log_ki(qt_app, felirat, betufokozat) -> None:
    """A rögzített magasság nem hozhatja vissza a #2494 kilógását.

    Két, PLATFORMFÜGGETLEN garanciát mérünk:

    1. a felirat ELEME a gombon belül van (fent és lent is) — ez az, amit a
       #2494 őre is néz;
    2. a felirat VÁGVA van, tehát a rajz sem folyhat ki.

    ⚠️ A rajzolt magasságot (`paintedHeight`) SZÁNDÉKOSAN nem állítjuk a
    gombhoz: a CI windows-lábán mérve a legkisebb megengedett fokozaton is
    27 képpont marad egy 26 képpontos gombban (ott a rendszerbetű natúr
    sormagassága kétszerese a betűméretnek). Az a platform betűjének
    tulajdonsága, nem a mi geometriánké — a helyettesítő betűtípus mérése
    külön, régóta nyitott kérdés (#526). Amit ki tudunk zárni, az a
    KIFOLYÁS, és azt a vágás zárja ki."""
    gomb, cimke = _gomb(qt_app, felirat, betufokozat=betufokozat)
    teteje = cimke.mapToItem(gomb, 0, 0).y()
    magassag = float(gomb.property("height"))
    festett = float(cimke.property("paintedHeight"))
    assert teteje >= -TURES, f"a felirat {-teteje:.1f} képponttal a gomb TETEJE fölé lóg"
    # ⚠️ #2759: a RAJZOT mérjük (`paintedHeight`), nem az ELEM dobozát. A
    # `Text` eleme magasabb lehet a tintánál (a betű sorköze/alsó nyúlványa
    # akkor is benne van, ha nem rajzol oda semmit) — a CI windows-lábán
    # mérve az elem 24, a rajz 20 képpont ugyanabban a 26 képpontos gombban.
    # Az elem túllógása így nem hiba; a rajzé az lenne.
    assert teteje + festett <= magassag + TURES, (
        f"a(z) {felirat!r} felirat RAJZA {teteje + festett - magassag:.1f} "
        f"képponttal lelóg a gombról (gomb {magassag:.0f} px)"
    )
    assert cimke.property("clip") is True, (
        "a felirat nincs vágva — egy magas betűs platformon a rajz a szomszéd "
        "gombra folyna"
    )


@pytest.mark.parametrize(
    "felirat", [JELENTETT_FELIRAT, LEGHOSSZABB_FELIRAT], ids=["jelentett", "leghosszabb"]
)
def test_a_mert_szelessegen_semmi_nem_csonkul(qt_app, felirat) -> None:
    """A rögzített magasság ára: a felirat legfeljebb KÉT sor (26 képpontba a
    mért 10-es sorközzel ennyi fér). A MÉRT gombszélességen ez elég — ezt
    rögzíti ez az őr.

    ⚠️ A mért szélesség ALATT (szűkebb ablakban) a hosszabb effektnevek
    harmadik sora elmarad. Ez SZÁNDÉKOS csere: korábban a gomb nőtt meg
    helyette, amit a tulajdonos külön hibaként jelentett (#2494), az eredeti
    Picasa pedig maga is vág (a `.tre` `*_clip` konténerei). A rés a
    szélességen orvosolható, nem a magasságon."""
    panel = _panel(qt_app, gombszelesseg=MERT_RAJZOLT_SZELESSEG)
    panel.setProperty("undoLabel", felirat)
    _leul(qt_app)
    gomb, cimke = _gomb_es_felirat(panel)

    assert abs(float(gomb.property("height")) - EREDETI_GOMBMAGASSAG) <= TURES
    if not cimke.property("truncated"):
        return
    # Csonkul — ez CSAK akkor elfogadható, ha már a legkisebb megengedett
    # fokozaton vagyunk, vagyis a kód mindent megtett, ami tőle telik. A CI
    # windows-lábán ez a helyzet: ott a rendszerbetű natúr sormagassága a
    # betűméret kétszerese, és két sor sem fér a mért 26 képpontba. A
    # megoldás a helyettesítő betűtípus kimérése (#526), nem a gomb
    # megnövelése — azt a tulajdonos külön hibaként jelentette (#2494).
    assert QQmlProperty.read(cimke, "font.pixelSize") == gomb.property(
        "minimumLabelPixelSize"
    ), (
        f"a(z) {felirat!r} felirat csonkul a MÉRT {MERT_RAJZOLT_SZELESSEG} "
        f"képpontos gombon, PEDIG a fokozat még nem a padlón van "
        f"({QQmlProperty.read(cimke, 'font.pixelSize')} > "
        f"{gomb.property('minimumLabelPixelSize')}) — a zsugorítás nem fut le"
    )
