"""Effekt-paraméterek a csúszkás alpanelhez (#316, #516, #600).

Az eredeti Picasában a paraméteres effekt gombja nem alkalmaz azonnal: egy
alpanel nyílik, ahol csúszkákkal/jelölőnégyzetekkel/színválasztókkal
állítható a hatás, élő előnézettel, és az Alkalmaz gomb teszi a láncra. Ez a
modul a katalógus — effektenként megadja, milyen vezérlők tartoznak hozzá.

A vezérlők FORRÁSA a `docs/specs/filterdesc-registry.md` **4.2 szakasza**
("Vezérlők effektenként") — ez a Picasa saját `filterdesc.xml`
csúszka-regiszteréből átvezetett, min–max–alapérték szintig hiteles lista.
A vezérlők SORRENDJE viszont NEM a 4.2 táblázat deklarációs sorrendje, hanem
a `filters=` lánc tényleges POZÍCIÓ-sorrendje (`chain_glimmer_handlers.py`
`_float_at`/`_color_at`/`_bool_at` hívásainak sorrendje) — ez a 4.1 szakasz
"numerikusok max 3 → színek → maradék numerikus → jelölők" szabálya szerint
gyakran ELTÉR a 4.2 deklarációs sorrendtől (pl. `Sixties`: a 4.2-ben
"Rounded, Outer, Fade", az ini-ben "Fade, Outer, Rounded").

A vezérlők FELIRATA (#600) a Picasa saját szótárából való: a
`Picasa3i18n.dll` `ImageFilters` osztálya 69 vezérlő-feliratot tartalmaz, 41
nyelven — a leképezés a `docs/specs/picasa-effekt-feliratok.md`. Több eredeti
elnevezés NEM magától értetődő (a `Blur` kulcs felirata „Size" = Méret, a
`Smoothing`-é „Detail" = Részletek, a `Steps`-é „Number of Colors" = Színek
száma), ezért a feliratot kitalálni tilos: a felhasználó a régi programból
ezeket a szavakat ismeri. Ahol a vezérlő-KÉSZLETÜNK maga tér el az
eredetitől (`pencilsketch`, `comicize`, `neon`, `soften`, `focalzoom`,
illetve a nem-Glimmer örökölt szűrők: `radblur`, `radsat`, `dir_tint`,
`tint`, `radtint`), ott a felirat sem vezethető le — ezek a #600 jegyben
külön fel vannak sorolva, és saját munkára várnak.

A négy „tint-szerű" örökölt szűrő (`ansel`, `tint`, `dir_tint`, `radtint`)
és a `finetune`/`finetune2`/`colorfix` színválasztója UGYANAZT a natív
`editpanel/colorwheel%d` vezérlőt használja — ennek felirata a
`filterdesc.xml`-től függetlenül, mindig „Pick Color" (a szerkesztőpanel
`editpaneltext.tre` erőforrásából mérve, ld. `docs/specs/filters-decoded.md`
„A `colorwheel version=…`" szakasza) — ez NEM kitalált név, hanem a
`PickColor` szótári kulcs (`picasa-effekt-feliratok.md`).

FIGYELEM (#700 nyomán, binárisból igazolva): a felirat NEM csak a vezérlő
azonosítójától függ. A `Picasa3.exe` `FUN_008fcfa0` négy csúszkánál a SZŰRŐ
azonosítójára is elágazik, és felülírja az alapértelmezést — ezért van
`Holga`/`Lomo` alatt „Blur Edges" (Élhomályosítás) a „Size" helyett,
`Pixelate` alatt „Pixel Size", `HDR` alatt „Strength", `Boost` alatt szintén
„Strength". A teljes felülíró tábla a
`docs/specs/picasa-effekt-feliratok.md` „Szűrőnkénti felülírás" szakaszában
van; új effekt felvételekor ELŐBB azt kell megnézni.

Amit tudatosan KIHAGYUNK (ld. a #516 jegy jelentése):
- a **festhető maszk / ecset** effektek (`ReanimatedEyeColor`, `Soften`,
  `PicnikTint`) — a Picasában ecsettel kijelölt területre hatnak, a
  PicasaPy-nak még nincs ilyen eszköze (#381); önálló munka.
- `PicnikFocalPixelate` — a `render/` rétegben NINCS hozzá handler (a natív
  `focalpixelate` egy MÁSIK, `chain.KNOWN_UNRENDERED_OPS`-beli szűrő), így
  vezérlők hozzáadása egy nem-létező renderert kötne be — ez már nem
  "kicsi és egyértelmű" javítás (#516 jelentés).
- `Boost`, `Cinemascope`, `Comicize`, `Invert`, `Neon`, `PencilSketch` — a
  #516 jegy szerint ezeknél a vezérlőszám MA MÁR egyezik az eredetivel,
  nincs teendő. (A `FocalZoom` ide korábban szintén be volt sorolva — ez
  #717-ben TÉVESNEK bizonyult: a regiszter 6, a katalógusunk csak 4
  paramétert tartott, ld. lent.)
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class EffectParam:
    """Egy vezérlő leírója.

    A `label` ANGOL kulcsszöveg; a fordítást a QML végzi (a felület nyelvi
    rétege ott él, `qsTr`-rel — így a Linguist-eszközök is megtalálják).

    `kind`: `"slider"` (számtartomány), `"checkbox"` (jelölőnégyzet) vagy
    `"color"` (színválasztó). `minimum`/`maximum`/`default`/`step` csak
    `"slider"`-nél értelmezett (checkboxnál `default` 0.0/1.0); `color` csak
    `"color"`-nál értelmezett (`"#rrggbb"` alak).

    `max_formula`/`default_formula`: képfüggő tartományok jelzői — a
    tényleges min(W,H)/H értéket `resolve_effect_params()` számolja ki, itt
    csak a KÉPLET neve él (`None` = nincs képfüggés).
    """

    key: str
    label: str
    kind: str = "slider"
    minimum: float = 0.0
    maximum: float = 100.0
    default: float = 0.0
    step: float = 1.0
    color: str = "#000000"
    max_formula: str | None = None
    default_formula: str | None = None


#: Effektek, amelyeknek nincs állítható paramétere — a gomb azonnal alkalmaz
#: (ez a Picasa viselkedése is: a Szépia/Fekete-fehér egy kattintás).
# #2141: a `grain2` KIKERÜLT — az 1. fül 5. csempéje az eredeti
# elsődlegesére (`picnikgrain`) kötött, aminek VAN csúszkája. A
# `grain2` a Shiftes másodlagos, felületi belépési pont nélkül.
PARAMETERLESS_EFFECTS: tuple[str, ...] = ("sepia", "bw", "warm", "invert")


def _slider(key, label, minimum, maximum, default, step=1.0, max_formula=None, default_formula=None) -> EffectParam:
    return EffectParam(
        key, label, "slider", minimum, maximum, default, step,
        max_formula=max_formula, default_formula=default_formula,
    )


# a korábbi `_p` név megmarad — a katalógus alább végig ezt használja
_p = _slider


def _checkbox(key, label, default=False) -> EffectParam:
    return EffectParam(key, label, "checkbox", 0.0, 1.0, 1.0 if default else 0.0, 1.0)


def _color(key, label, color) -> EffectParam:
    return EffectParam(key, label, "color", 0.0, 1.0, 0.0, 1.0, color=color)


#: A paraméteres effektek vezérlői, a lánc-paraméterek SORRENDJÉBEN (az első
#: vezérlő a `filters=` első paramétere az engedélyező „1" flag után).
_CATALOGUE: dict[str, tuple[EffectParam, ...]] = {
    # --- 3. fül: törzs-effektek ---------------------------------------------
    # unsharp=1 mérten azonos az unsharp2=1,0.600000-val
    "unsharp": (_p("amount", "Amount", 0.0, 2.0, 0.6, 0.05),),
    # sat=1,!telítettség — a vezérlő eddigi alapértéke 0,5
    "sat": (_p("saturation", "Saturation", 0.0, 1.0, 0.5, 0.01),),
    # glow2=1,intenzitás,sugár
    "glow2": (
        _p("intensity", "Intensity", 0.0, 1.0, 0.5, 0.01),
        _p("radius", "Radius", 0.0, 100.0, 20.0),
    ),
    # radblur=1,x,y,méret,mérték
    "radblur": (
        _p("x", "Center X", 0.0, 1.0, 0.5, 0.01),
        _p("y", "Center Y", 0.0, 1.0, 0.5, 0.01),
        _p("size", "Size", 0.0, 1.0, 0.3, 0.01),
        _p("amount", "Amount", 0.0, 1.0, 0.5, 0.01),
    ),
    # radsat=1,x,y,sugár,élesség
    "radsat": (
        _p("x", "Center X", 0.0, 1.0, 0.5, 0.01),
        _p("y", "Center Y", 0.0, 1.0, 0.5, 0.01),
        _p("radius", "Radius", 0.0, 1.0, 0.3, 0.01),
        _p("sharpness", "Sharpness", 0.0, 1.0, 0.5, 0.01),
    ),
    # tint=1,!!megőrzés,#szín (#717: a szín korábban hiányzott a láncból)
    "tint": (
        _p("preserve", "Preserve Color", 0.0, 1.0, 0.5, 0.01),
        _color("color", "Pick Color", "#ffffff"),
    ),
    # ansel=1,#szín (#717: korábban egyáltalán nem volt katalógus-bejegyzése —
    # a gomb egykattintásos alapértékkel, színválasztó nélkül alkalmazott)
    "ansel": (_color("color", "Pick Color", "#ffffff"),),
    # dir_tint=1,x,y,gradiens,árnyék,#szín (#717: a szín korábban hiányzott)
    "dir_tint": (
        _p("x", "Center X", 0.0, 1.0, 0.5, 0.01),
        _p("y", "Center Y", 0.0, 1.0, 0.5, 0.01),
        _p("gradient", "Gradient", 0.0, 1.0, 0.5, 0.01),
        _p("shade", "Shade", 0.0, 1.0, 0.5, 0.01),
        _color("color", "Pick Color", "#ffffff"),
    ),
    # radtint=1,x,y,feather,#szín (#565/#717: korábban egyáltalán nem volt
    # katalógus-bejegyzése — a „Régi effektek" fül gombja egykattintásos,
    # rögzített `edit_controller._EFFECT_PARAMS["radtint"]` alapértékkel
    # alkalmazott, alpanel/színválasztó nélkül)
    "radtint": (
        _p("x", "Center X", 0.0, 1.0, 0.5, 0.01),
        _p("y", "Center Y", 0.0, 1.0, 0.5, 0.01),
        _p("gradient", "Gradient", 0.0, 1.0, 0.25, 0.01),
        _color("color", "Pick Color", "#ffffff"),
    ),
    # --- 5. fül: művészi effektek — egyezők (nincs teendő, #516) ------------
    # Boost: Impact — a felirata viszont „Strength" (felülírás)
    "boost": (_p("strength", "Strength", 0.0, 100.0, 50.0),),
    "soften": (
        _p("amount", "Amount", 0.0, 100.0, 50.0),
        _p("radius", "Radius", 0.0, 100.0, 50.0),
    ),
    # FocalZoom=1,x,y,Impact,Radius,Hardness,Fade (#570/#600/#717): a
    # katalógus korábban csak az első két csúszkát tartotta, ÉS azokat
    # tévesen "Radius"/"Strength" néven — a #600 táblázata szerint a
    # helyes felirat-sorrend Impact → Radius → Edge Hardness → Fade
    # (`docs/specs/filterdesc-registry.md` 4.2, ill. a #600 jegy „FocalZoom"
    # sora); a #516 „nincs teendő" megjegyzése ezt a négy csúszkát
    # kettőnek nézte, ez volt a #717 valódi oka.
    "focalzoom": (
        _p("x", "Center X", 0.0, 1.0, 0.5, 0.01),
        _p("y", "Center Y", 0.0, 1.0, 0.5, 0.01),
        _p("impact", "Impact", 1.0, 100.0, 50.0),
        _p("radius", "Radius", 10.0, 100.0, 50.0),
        _p("hardness", "Edge Hardness", 0.0, 100.0, 50.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    "pencilsketch": (
        _p("blur_radius", "Blur Radius", 0.5, 20.0, 2.0, 0.5),
        _p("brightness", "Brightness", 0.0, 200.0, 100.0),
        _p("color_mix", "Color Mix", 0.0, 100.0, 0.0),
    ),
    "neon": (_p("intensity", "Intensity", 0.0, 100.0, 50.0),),
    "comicize": (
        _p("edge_strength", "Edge Strength", 0.0, 100.0, 20.0),
        _p("posterize", "Posterize", 0.0, 100.0, 50.0),
        _p("smoothness", "Smoothness", 0.0, 100.0, 50.0),
    ),
    # --- #516: a filterdesc-registry.md 4.2 szerint kiegészített/javított --
    # Border: OuterThickness, InnerThickness, CornerRadius, OuterColor,
    # InnerColor, CaptionHeight (a `apply_border_op` POZÍCIÓ-sorrendje)
    "border": (
        _p("outer_thickness", "Outer Thickness", 0.0, 100.0, 20.0),
        _p("inner_thickness", "Inner Thickness", 0.0, 100.0, 5.0),
        _p("corner_radius", "Corner Radius", 0.0, 0.0, 0.0, max_formula="half_min_wh"),
        _color("outer_color", "Outer Color", "#000000"),
        _color("inner_color", "Inner Color", "#ffffff"),
        _p("caption_height", "Caption Height", 0.0, 0.0, 0.0, max_formula="sixth_h"),
    ),
    # DropShadow: Distance, Angle, Blur, ShadowColor, BackgroundColor, Fade
    "dropshadow": (
        _p("distance", "Distance", 0.0, 30.0, 4.0),
        _p("angle", "Angle", 0.0, 360.0, 90.0),
        _p("blur", "Size", 0.0, 100.0, 10.0),
        _color("shadow_color", "Shadow Color", "#000000"),
        _color("background_color", "Background Color", "#ffffff"),
        _p("fade", "Fade", 0.0, 100.0, 30.0),
    ),
    # MuseumMatte: OuterThickness, InnerThickness, OuterColor, InnerColor
    "museummatte": (
        _p("outer_thickness", "Outer Thickness", 0.0, 100.0, 25.0),
        _p("inner_thickness", "Inner Thickness", 0.0, 100.0, 40.0),
        _color("outer_color", "Outer Color", "#1a0e03"),
        _color("inner_color", "Inner Color", "#f0eae4"),
    ),
    # Polaroid: Rotate, OuterColor (az ini-ben Rotate jön előbb)
    "polaroid": (
        _p("rotate", "Rotate", -10.0, 10.0, 5.0, 0.5),
        _color("outer_color", "Outer Color", "#e2e2e2"),
    ),
    # Pixelate: Impact, BlendMode (renderer ma NEM használja — ld. jelentés),
    # Fade — a BlendMode vezérlőt a Fade pozíciója miatt kell tartani
    "pixelate": (
        _p("impact", "Pixel Size", 2.0, 150.0, 20.0),
        _p("blend_mode", "Blend Mode", 0.0, 9.0, 9.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # Vignette: Blur, Strength, Fade, Color
    "vignette": (
        _p("blur", "Size", 0.0, 50.0, 35.0),
        _p("strength", "Strength", 1.0, 2.0, 1.4, 0.05),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
        _color("color", "Vignette Color", "#000000"),
    ),
    # Matte: Blur, Strength, Fade, Color — a Vignette motorja fehér színnel
    "matte": (
        _p("blur", "Size", 0.0, 50.0, 40.0),
        _p("strength", "Strength", 1.0, 2.0, 1.2, 0.05),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
        _color("color", "Matte Color", "#ffffff"),
    ),
    # HDR: Radius, Contrast, Fade — a Contrast felirata „Strength" (felülírás)
    "hdr": (
        _p("radius", "Radius", 1.3, 80.0, 20.0, 0.1),
        _p("contrast", "Strength", 1.0, 7.0, 3.0, 0.1),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # LocalContrast: Radius, Contrast — nincs Fade
    "localcontrast": (
        _p("radius", "Radius", 1.3, 40.0, 15.0, 0.1),
        _p("contrast", "Contrast", 1.0, 3.0, 1.5, 0.1),
    ),
    # Orton: Bloom, Brightness, Fade
    "orton": (
        _p("bloom", "Bloom", 0.0, 50.0, 25.0),
        _p("brightness", "Brightness", 0.0, 100.0, 50.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # Holga: Blur, Grain, Fade — a Blur felirata itt „Blur Edges" (felülírás)
    "holga": (
        _p("blur", "Blur Edges", 0.0, 100.0, 70.0),
        _p("grain", "Grain", 0.0, 100.0, 30.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # Lomo: Blur, Fade — a Blur felirata itt „Blur Edges" (felülírás)
    "lomo": (
        _p("blur", "Blur Edges", 0.0, 100.0, 50.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # IR: Fade
    "ir": (_p("fade", "Fade", 0.0, 100.0, 0.0),),
    # CrossProcess: Fade
    "crossprocess": (_p("fade", "Fade", 0.0, 100.0, 0.0),),
    # NightVision: Brightness, Contrast, Fade
    "nightvision": (
        _p("brightness", "Brightness", -50.0, 50.0, 0.0),
        _p("contrast", "Contrast", -50.0, 50.0, 0.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # HeatMap: Hue, Fade
    "heatmap": (
        _p("hue", "Hue", -180.0, 180.0, 0.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # QuantizePalette: Steps, Smoothing, Fade
    "quantizepalette": (
        _p("steps", "Number of Colors", 2.0, 30.0, 8.0),
        _p("smoothing", "Detail", 0.0, 100.0, 80.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
    ),
    # TwoTone: Brightness, Contrast, Fade, BlackColor, WhiteColor
    "twotone": (
        _p("brightness", "Brightness", -95.0, 95.0, 0.0),
        _p("contrast", "Contrast", 0.0, 100.0, 20.0),
        _p("fade", "Fade", 0.0, 100.0, 0.0),
        _color("black_color", "First Color", "#004488"),
        _color("white_color", "Second Color", "#ffff00"),
    ),
    # RoundedEdges: CornerRadius, OuterColor
    "roundededges": (
        _p("corner_radius", "Corner Radius", 0.0, 0.0, 0.0,
           max_formula="half_min_wh", default_formula="tenth_min_wh"),
        _color("outer_color", "Outer Color", "#ffffff"),
    ),
    # Sixties: Fade, OuterColor, Rounded (checkbox)
    "sixties": (
        _p("fade", "Fade", 0.0, 100.0, 20.0),
        _color("outer_color", "Outer Color", "#ffffff"),
        _checkbox("rounded", "Rounded Corners", default=True),
    ),
    # PicnikGrain: Grain, Lighten (checkbox)
    "picnikgrain": (
        _p("grain", "Grain", 0.0, 50.0, 10.0),
        _checkbox("lighten", "Lighten", default=False),
    ),
    # --- #2141: a csempe-átkötés HOZTA IDE a következő kettőt -------------
    # Az 1. effekt-fül Élesítés és Árnyalás csempéje az eredeti
    # elsődlegesére (`unsharp2`, `PicnikTint`) került át. Katalógus-bejegyzés
    # nélkül ezek `has_params=False`-ok lettek volna, vagyis a csempe
    # NÉMÁN elveszi a csúszkát, és alapértékkel azonnal alkalmaz. Az
    # adatok forrása a szűrő-regiszter (`registry_data.py`, a
    # `filterdesc.xml`-ből) — nem becslés.
    #
    # unsharp2=1,mennyiség — a felső vég 3,0 (az `unsharp` v1-é 1,0),
    # az alapérték mindkettőnél 0,6
    "unsharp2": (_p("amount", "Amount", 0.0, 3.0, 0.6, 0.05),),
    # PicnikTint=1,elhalványítás — a regiszter EGY csúszkát ad („Fade",
    # 0–100, alap 0). Színválasztója NINCS: az örökölt `tint` az, aminek
    # `preserve` + `#szín` párja van.
    "picniktint": (_p("fade", "Fade", 0.0, 100.0, 0.0),),
}


#: Fallback méret, ha (még) nincs betöltött kép — CSAK a szerkesztőpanel
#: önálló (editController nélküli) tesztjeiben/előnézetében fordulhat elő;
#: valós szerkesztésnél mindig van `_image_path` (ld. `EditController.
#: beginEdit`), ezért ez a szám a felhasználó elé sosem kerül ténylegesen.
_FALLBACK_WIDTH = 1600.0
_FALLBACK_HEIGHT = 1200.0


def effect_params(name: str) -> tuple[EffectParam, ...]:
    """Az effekt vezérlői; ismeretlen vagy paraméter nélküli effektnél üres.

    A képfüggő tartományok (`max_formula`/`default_formula`) itt MÉG a
    névvel szerepelnek — a tényleges min(W,H)/H értéket
    `resolve_effect_params()` számolja ki.
    """
    if not isinstance(name, str):
        return ()
    return _CATALOGUE.get(name.casefold(), ())


def resolve_effect_params(
    name: str, width: float | None = None, height: float | None = None
) -> tuple[EffectParam, ...]:
    """`effect_params(name)`, a képfüggő min/max/alapérték kiszámolva.

    `width`/`height` hiányában (nincs betöltött kép) a `_FALLBACK_WIDTH/
    HEIGHT`-tal számol — ez csak a panel ideiglenes/teszt-állapotában
    fordulhat elő.
    """
    params = effect_params(name)
    if not params:
        return params
    if not width or not height or width <= 0 or height <= 0:
        width, height = _FALLBACK_WIDTH, _FALLBACK_HEIGHT
    half_min_wh = min(width, height) / 2.0
    sixth_h = height / 6.0
    tenth_min_wh = min(width, height) / 10.0
    resolved = []
    for param in params:
        maximum = param.maximum
        default = param.default
        if param.max_formula == "half_min_wh":
            maximum = half_min_wh
        elif param.max_formula == "sixth_h":
            maximum = sixth_h
        if param.default_formula == "tenth_min_wh":
            default = tenth_min_wh
        if maximum != param.maximum or default != param.default:
            param = replace(param, maximum=maximum, default=default)
        resolved.append(param)
    return tuple(resolved)


def has_params(name: str) -> bool:
    """Nyíljon-e vezérlős alpanel a gombra kattintva?"""
    return bool(effect_params(name))


def format_param_values(values, params=None) -> tuple[str, ...]:
    """A vezérlő-értékek a Picasa `filters=` alakjában (round-trip elv).

    `params` nélkül (visszafelé kompatibilis mód) minden érték számként, a
    Picasa `%.6f` alakjában megy — ez az EREDETI (#316) viselkedés. `params`
    átadásával (a katalógus vezérlőivel PÁRHUZAMOSAN) a `kind` szerint
    formázunk: `checkbox` egész `0`/`1`-ként (a Picasa is így írja a
    jelölőnégyzeteket, tizedesjegy nélkül), `color` `"00rrggbb"` hexaként
    (a `filters=` `AARRGGBB` alakja, alfa `00`), a többi (`slider`)
    változatlanul `%.6f`-ként.
    """
    if params is None:
        return tuple(f"{float(value):.6f}" for value in values)
    formatted: list[str] = []
    for value, param in zip(values, params, strict=False):
        if param.kind == "checkbox":
            formatted.append("1" if value else "0")
        elif param.kind == "color":
            hex_value = str(value).strip().lstrip("#")
            if len(hex_value) != 6:
                raise ValueError(f"Érvénytelen szín (nem #rrggbb alakú): {value!r}")
            int(hex_value, 16)  # ValueError, ha nem hexa
            formatted.append("00" + hex_value.lower())
        else:
            formatted.append(f"{float(value):.6f}")
    return tuple(formatted)
