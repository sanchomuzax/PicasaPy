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
LEGACY_EFFECTS: tuple[LegacyEffect, ...] = (
    # --- a natív visszafejtésből már megvan a modell ---------------------
    LegacyEffect("radtint", "Radial Tint"),
    LegacyEffect("autobacklight", "Fill Light (one-click)"),
    LegacyEffect("fill", "Fill Light (slider)"),
    # --- irányított család: a callbackek megvannak, a pixel-matematika
    #     még nincs megfejtve (#568) -------------------------------------
    LegacyEffect("linblur", "Linear Blur"),
    LegacyEffect("dir_sat", "Directional Saturation"),
    LegacyEffect("dir_brite", "Directional Brightness"),
    LegacyEffect("dir_sharp", "Directional Sharpening"),
    # --- csak régi ini-ből olvasható, natív kód még megfejtetlen ---------
    LegacyEffect("triple", "Lighting Fixes (v1)"),
    LegacyEffect("triple2", "Lighting Fixes (v2)"),
    LegacyEffect("triple3", "Lighting Fixes (v3)"),
    LegacyEffect("colorfix", "Color Fixes"),
    LegacyEffect("shadow", "Shadow and Highlight"),
    LegacyEffect("whitept", "White Point"),
    LegacyEffect("gamma", "Gamma Correction"),
    LegacyEffect("contrast", "Contrast"),
    LegacyEffect("colortemp", "Color Temperature"),
    LegacyEffect("blur", "Softening"),
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
