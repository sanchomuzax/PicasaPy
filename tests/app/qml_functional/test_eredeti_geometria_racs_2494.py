"""RÁCS-ŐR: a mért EREDETI geometriától való eltérés nem nőhet (#2494).

## Miért ez az őr, és miért nem elég a meglévő

A #2494-es őr azt méri, hogy a felirat **belefér-e** a gombba — és ez zöld
volt akkor is, amikor a tulajdonos visszaesést jelentett. A kilógás ugyanis
megszűnt, csak épp **a gomb nőtt meg** helyette: az eredetiben 26 px, nálunk
38 px. A „belefér" tehát igaz állítás volt egy rossz megoldásra.

A tulajdonos szava (2026-09-06): *„TILOS ELRONTANI MŰKÖDŐ FEATURE-ÖKET!"* és
*„A teszteknek a referenciaképekhez kell hasonlítaniuk, nem újraszámolt
értékekhez."* Ez az őr azt méri, amit ő lát: **mennyire térünk el az
eredetitől.**

## A referencia — a tulajdonos képernyőmentéséről mérve

`/mnt/nas/My Pictures/235707.jpg` (bal: PicasaPy, jobb: Picasa 3), a
`referencia/kepek-leltar.md` szerint. A gomb kerete az eredetiben
**380 … 405 → 26 px**.

## Hogyan fog ez az őr (RÁCS)

`MAI_ELTERES` a MA MÉRT eltérés (2026-09-06, friss `main`: **0 px** — a
gombunk 26.0, mint az eredeti). Ez a szám **csak csökkenhet**:

* ha az eltérés NŐ, az őr elbukik — visszaesés;
* ha az eltérés CSÖKKEN, az őr szintén elbukik, azzal az üzenettel, hogy
  szorítsd meg a rácsot. Így a javulás nem maradhat rögzítetlen, és a
  következő kör már a szigorúbb számhoz mér.

⚠️ A rácsot **csak a javítással együtt** szabad átírni, felfelé soha.
"""

from __future__ import annotations

import os

from tests.app.qml_functional.test_visszavonas_felirat_2494 import (
    JELENTETT_FELIRAT,
    MERT_GOMBSZELESSEG,
    _gomb_es_felirat,
    _leul,
    _panel,
)

#: A tulajdonos képernyőmentésén MÉRT eredeti gombmagasság (Picasa 3).
EREDETI_GOMBMAGASSAG = 26.0

#: A MA mért eltérés képpontban, PLATFORMONKÉNT. CSAK CSÖKKENHET.
#:
#: ⚠️ A gomb magassága BETŰMETRIKA-FÜGGŐ (a `PicasaButton` a `lineHeight`-ből
#: és a `Theme.lineLeading`-ből számol), és a két platform betűje más.
#: Egyetlen szám ezért nem állhat mindkettőn — a FŐÁG CI-je 2026-09-06-án
#: emiatt lett piros: Linuxon 26.0 px (eltérés 0), Windowson 32.0 px
#: (eltérés 6). Az őr Linuxon kalibrált `0.0`-ja a windows-lábon
#: visszaesésnek látszott, holott a kód nem változott.
#:
#: A megoldás NEM a kihagyás (az üresen zöld őr rosszabb a pirosnál,
#: ld. #2555): mindkét platformon ÉL a racsni, csak a saját mai állásához.
#:
#: | platform | ma mért gomb | eltérés a mért eredetitől |
#: |---|---|---|
#: | POSIX (a fejlesztői gép) | 26.0 px | **0.0** — paritás |
#: | Windows | 32.0 px → **26.0** (#2597) | 6.0 → **0.0** |
#:
#: ⭐ **A windowsos 6 px MEGSZŰNT (2026-09-08, #2597).** A gomb magassága
#: azóta nem betűmetrika-függő: a `PanelButton.rogzitettMagassag` a MÉRT 26
#: képpontot veszi fel, a felirat pedig igazodik hozzá (fokozat-illesztés,
#: legfeljebb két sor) — ahogy az eredeti is a feliratot szorítja a gombhoz.
#: Ezért mindkét platform rácsa **0,0**. A jelenséget külön őr zárja ki:
#: `test_gombmagassag_platformfuggetlen_2597.py` (ott a próba nem
#: platform-elágazás, hanem magas betűs platform utánzása, tehát helyben is
#: fut).
_ELTERESEK = {"nt": 0.0, "posix": 0.0}
MAI_ELTERES = _ELTERESEK.get(os.name, 0.0)

#: Fél képpont játék a lebegőpontos összehasonlításnak.
TURES = 0.5


def test_a_gomb_nem_ter_el_JOBBAN_az_eredetitol(qt_app) -> None:
    panel = _panel(qt_app, gombszelesseg=MERT_GOMBSZELESSEG)
    panel.setProperty("undoLabel", JELENTETT_FELIRAT)
    _leul(qt_app)
    gomb, _ = _gomb_es_felirat(panel)

    mienk = float(gomb.property("height"))
    elteres = abs(mienk - EREDETI_GOMBMAGASSAG)

    assert elteres <= MAI_ELTERES + TURES, (
        f"NŐTT az eltérés az eredetitől: a gomb {mienk:.1f} px, az eredeti "
        f"{EREDETI_GOMBMAGASSAG:.0f} px, az eltérés {elteres:.1f} px — a "
        f"{os.name} rács {MAI_ELTERES:.0f} px. Ez visszaesés: a tulajdonos "
        f"ezt a képernyőn látja meg."
    )
    assert elteres >= MAI_ELTERES - TURES, (
        f"JAVULT az eltérés ({elteres:.1f} px a {os.name} rács "
        f"{MAI_ELTERES:.0f} px helyett) — szorítsd meg a rácsot: írd át az "
        f"`_ELTERESEK` megfelelő platform-értékét {elteres:.1f}-re UGYANEBBEN "
        f"a PR-ben, különben a következő kör visszaengedheti a régit."
    )
