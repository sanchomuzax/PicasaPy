"""Az ÖRÖKÖLT (a mai Picasa felületén nem elérhető) szűrők katalógusa (#571).

A Picasa 3.9 motorja rengeteg olyan szűrőt ismer, amelynek **nincs
kezelőfelülete**: régebbi verziókból maradtak bent. A motor egy régi
`.picasa.ini`-ből még elolvassa és alkalmazza őket, de a felhasználó nem
tudja előhívni — és ezért **lemérni sem** az eredeti programban.

A PicasaPy ezért **tudatosan többet ad**, mint az eredeti: külön fület kap
ez a készlet. Ez az egyetlen olyan pont, ahol szándékosan eltérünk a Picasa
felületétől; egy későbbi „hűségjavítás" ne vegye ki (ld. #571).

Ez a modul csak a NÉVSORT és a felületi feliratokat tartja — a vezérlők
(csúszkák, tartományok, alapértékek) a `filterdesc.xml`-ből származó
`FILTER_REGISTRY`-ből generálódnak, nem kézzel írt számokból. Azt pedig,
hogy egy effekt ténylegesen renderel-e, a RENDERELŐ dönti el
(`chain.can_render_filter`) — így a felületen nem lehet hazug, aktívnak
látszó, de nem ható gomb.
"""

from __future__ import annotations

from typing import NamedTuple


class LegacyEffect(NamedTuple):
    """Egy örökölt szűrő a fülön: belső kulcs + felületi (angol) felirat.

    A magyar fordítás a szokásos `.ts` úton készül; a `label` az `<source>`.
    """

    key: str
    label: str


#: A fülre kerülő szűrők, a #571-es jegy sorrendjében: elöl azok, amelyeknek
#: a natív visszafejtésből MÁR van modellje, utánuk azok, amelyek csak régi
#: `.picasa.ini`-ből olvashatók.
#:
#: A `debug` („For debugging") SZÁNDÉKOSAN kimarad: fejlesztői eszköz volt,
#: nem felhasználói effekt.
#:
#: #2270 — A FELIRATOK ÉS AZ EREDETI SZÖVEGTÁR
#:
#: Öt felirat (`blur`, `dir_sharp`, `gamma`, `shadow`, `whitept`) az
#: eredeti szövegtárat (`filter_*_label0`) követi.
#:
#: Hat viszont SZÁNDÉKOSAN tér el, megkülönböztető toldattal:
#: `autobacklight`/`fill` (az eredetiben mindkettő „Fill Light"),
#: `triple`/`triple2`/`triple3` (mindhárom „Lighting Fixes") és a
#: `focalpixelate`. Átvételük után a fülön AZONOS feliratú sorok
#: állnának egymás alatt — a felhasználó nem tudná megmondani, melyikre
#: kattint.
#:
#: A döntés mérésen áll (#2148): az eredetiben ezek a szűrők EGY
#: LISTÁBAN SEM szerepelnek — a 21-ből mindössze három érhető el a
#: felületről (`radtint` a 12. csempén Shifttel, `autobacklight` az
#: Alapvető javítások gombján, `rainbow` a Kiegyenesítés gombján
#: ALT-tal), és azok is külön helyeken. Az eredetinek tehát sosem
#: kellett megkülönböztetnie őket. Ez a fül a MI szerkezetünk (#571),
#: ezért a megkülönböztetés a mi igényünk — nem az eredeti hibája.
LEGACY_EFFECTS: tuple[LegacyEffect, ...] = (
    # --- a natív visszafejtésből már megvan a modell ---------------------
    LegacyEffect("radtint", "Radial Tint"),
    LegacyEffect("autobacklight", "Fill Light (one-click)"),
    LegacyEffect("fill", "Fill Light (slider)"),
    # --- irányított család: a natív magokat a #568 fejtette vissza, a
    #     megvalósítás a #623-ban készült el — mind a négy renderel
    #     (a `dir_sharp` horgonya és a `linblur` sugár-leképezése
    #     közelítés, ld. az `apply_*` docstringeket) --------------------
    LegacyEffect("linblur", "Linear Blur"),
    LegacyEffect("dir_sat", "Directional Saturation"),
    LegacyEffect("dir_brite", "Directional Brightness"),
    LegacyEffect("dir_sharp", "Directional Sharpen"),
    # --- csak régi ini-ből olvasható, natív kód még megfejtetlen ---------
    LegacyEffect("triple", "Lighting Fixes (v1)"),
    LegacyEffect("triple2", "Lighting Fixes (v2)"),
    LegacyEffect("triple3", "Lighting Fixes (v3)"),
    LegacyEffect("colorfix", "Color Fixes"),
    LegacyEffect("shadow", "Shadow & Highlight"),
    LegacyEffect("whitept", "Whitepoint"),
    LegacyEffect("gamma", "Gamma Correct"),
    LegacyEffect("contrast", "Contrast"),
    LegacyEffect("colortemp", "Color Temperature"),
    LegacyEffect("blur", "Blur"),
    LegacyEffect("backlight", "Backlight Fix"),
    LegacyEffect("rainbow", "Rainbow"),
    LegacyEffect("autocontrast", "Auto Contrast"),
    # --- halott (legacy) bejegyzés: a natív regiszterben SINCS hozzá
    #     feldolgozó (#567). Azért látszik, mert egy régi láncban
    #     előfordulhat — de más magyarázatot kap, mint a fentiek. --------
    LegacyEffect("focalpixelate", "Focal Pixelate (legacy)"),
)

#: Gyors tagsági halmaz — ebből dönti el a szerkesztő, hogy a megnyitott kép
#: láncában van-e olyan effekt, ami erre a fülre tartozik.
LEGACY_EFFECT_KEYS = frozenset(effect.key for effect in LEGACY_EFFECTS)

__all__ = ["LEGACY_EFFECTS", "LEGACY_EFFECT_KEYS", "LegacyEffect"]
