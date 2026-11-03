"""A régi Picasa-szűrők katalógusa (#571, #6443).

A mai Picasa felületén nem elérhető szűrők régebbi verziókból maradtak a
motorban. A PicasaPy egyetlen fülön kínálja azokat, amelyekre van valódi
renderelője; a natív regiszterben nem létező `focalpixelate` a lánc
felismeréséhez marad a katalógusban, de a fül nem jeleníti meg.

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


#: A régi szűrők ismert nevei a #571-es katalógussorrendben. A felület a
#: működő neveket kínálja; a dead `focalpixelate` név marad az ini-lánc
#: figyeléséhez, és a QML katalógusából kiszűrjük (#6443).
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
    #     (a `linblur` sugár-leképezése közelítés, ld. az
    #     `apply_linblur` docstringjét) ---------------------------------
    LegacyEffect("linblur", "Linear Blur"),
    LegacyEffect("dir_sat", "Directional Saturation"),
    LegacyEffect("dir_brite", "Directional Brightness"),
    LegacyEffect("dir_sharp", "Directional Sharpen"),
    # --- további visszafejtett régi korrekciók ---------------------------
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
    # --- halott (legacy) bejegyzés: a felületre nem kerül, de a natív
    #     regiszterben nincs hozzá feldolgozó (#567), és egy régi láncban
    #     előfordulhat — a láncjelzőknek meg kell őrizniük. ---------------
    LegacyEffect("focalpixelate", "Focal Pixelate (legacy)"),
)

#: Gyors tagsági halmaz — ebből dönti el a szerkesztő, hogy a megnyitott kép
#: láncában van-e olyan effekt, ami erre a fülre tartozik.
LEGACY_EFFECT_KEYS = frozenset(effect.key for effect in LEGACY_EFFECTS)

__all__ = ["LEGACY_EFFECTS", "LEGACY_EFFECT_KEYS", "LegacyEffect"]
