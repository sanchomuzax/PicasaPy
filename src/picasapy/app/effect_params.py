"""Effekt-paraméterek a csúszkás alpanelhez (#316).

Az eredeti Picasában a paraméteres effekt gombja nem alkalmaz azonnal: egy
alpanel nyílik, ahol csúszkákkal állítható a hatás, élő előnézettel, és az
Alkalmaz gomb teszi a láncra. Ez a modul a katalógus — effektenként megadja,
milyen csúszkák tartoznak hozzá.

A tartományok és az alapértékek FORRÁSA:
- a `docs/specs/filters-decoded.md` 5. körében MÉRT ini-minták (a felhasználó
  valódi Picasa-exportjaiból) — ezek adják az alapértékeket,
- az implementált render-függvények szignatúrái (`picasapy.render.*`).

Amit tudatosan KIHAGYUNK:
- a **szín-paraméterek** (`00RRGGBB`): csúszkára nem valók, színválasztó
  pedig még nincs — ezek egyelőre az implementált alapértéken maradnak.
- a **4. fül effektjei** (IR, Lomo, Holga, HDR, …): ott a mért minták és az
  implementált alapértékek nem esnek egybe, ezért a paraméter-jelentés még
  nyitott (#332) — előbb golden-mérés kell (#317). Addig ezek egygombos
  effektként viselkednek.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EffectParam:
    """Egy csúszka leírója.

    A `label` ANGOL kulcsszöveg; a fordítást a QML végzi (a felület nyelvi
    rétege ott él, `qsTr`-rel — így a Linguist-eszközök is megtalálják).
    """

    key: str
    label: str
    minimum: float
    maximum: float
    default: float
    step: float = 1.0


#: Effektek, amelyeknek nincs állítható paramétere — a gomb azonnal alkalmaz
#: (ez a Picasa viselkedése is: a Szépia/Fekete-fehér egy kattintás).
PARAMETERLESS_EFFECTS: tuple[str, ...] = ("sepia", "bw", "warm", "grain2", "invert")


def _p(key, label, minimum, maximum, default, step=1.0) -> EffectParam:
    return EffectParam(key, label, minimum, maximum, default, step)


#: A paraméteres effektek csúszkái, a lánc-paraméterek SORRENDJÉBEN (az első
#: csúszka a `filters=` első paramétere az engedélyező „1" flag után).
_CATALOGUE: dict[str, tuple[EffectParam, ...]] = {
    # --- 3. fül: törzs-effektek ---------------------------------------------
    # unsharp=1 mérten azonos az unsharp2=1,0.600000-val
    "unsharp": (_p("amount", "Amount", 0.0, 2.0, 0.6, 0.05),),
    # sat=1,!telítettség — a vezérlő eddigi alapértéke 0,5
    "sat": (_p("saturation", "Saturation", 0.0, 1.0, 0.5, 0.01),),
    # Vignette=1,belső%,erősség
    "vignette": (
        _p("inner", "Inner Radius", 0.0, 100.0, 35.0),
        _p("strength", "Strength", 0.0, 3.0, 1.4, 0.05),
    ),
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
    # tint=1,!!megőrzés,#szín — a szín egyelőre az alapértéken marad
    "tint": (_p("preserve", "Preserve Color", 0.0, 1.0, 0.5, 0.01),),
    # dir_tint=1,x,y,gradiens,árnyék,#szín
    "dir_tint": (
        _p("x", "Center X", 0.0, 1.0, 0.5, 0.01),
        _p("y", "Center Y", 0.0, 1.0, 0.5, 0.01),
        _p("gradient", "Gradient", 0.0, 1.0, 0.5, 0.01),
        _p("shade", "Shade", 0.0, 1.0, 0.5, 0.01),
    ),
    # --- 5. fül: művészi effektek (mért minták, #330/#332) -------------------
    "boost": (_p("strength", "Strength", 0.0, 100.0, 50.0),),
    "soften": (
        _p("amount", "Amount", 0.0, 100.0, 50.0),
        _p("radius", "Radius", 0.0, 100.0, 50.0),
    ),
    "pixelate": (_p("block_size", "Block Size", 2.0, 100.0, 20.0),),
    "focalzoom": (
        _p("x", "Center X", 0.0, 1.0, 0.5, 0.01),
        _p("y", "Center Y", 0.0, 1.0, 0.5, 0.01),
        _p("radius", "Radius", 0.0, 100.0, 50.0),
        _p("strength", "Strength", 0.0, 100.0, 50.0),
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
    "border": (_p("width", "Width", 0.0, 100.0, 20.0),),
    "dropshadow": (
        _p("border_width", "Border Width", 0.0, 50.0, 4.0),
        _p("angle", "Angle", 0.0, 360.0, 90.0),
        _p("blur", "Blur", 0.0, 50.0, 10.0),
    ),
    "museummatte": (
        _p("width", "Width", 0.0, 100.0, 25.0),
        _p("line_position", "Line Position", 0.0, 100.0, 40.0),
    ),
    "polaroid": (_p("border_width", "Border Width", 0.0, 50.0, 5.0),),
}


def effect_params(name: str) -> tuple[EffectParam, ...]:
    """Az effekt csúszkái; ismeretlen vagy paraméter nélküli effektnél üres."""
    if not isinstance(name, str):
        return ()
    return _CATALOGUE.get(name.casefold(), ())


def has_params(name: str) -> bool:
    """Nyíljon-e csúszkás alpanel a gombra kattintva?"""
    return bool(effect_params(name))


def format_param_values(values) -> tuple[str, ...]:
    """A csúszka-értékek a Picasa `%.6f` alakjában (round-trip elv).

    A `filters=` lánc így marad kölcsönösen olvasható az eredeti Picasával.
    """
    return tuple(f"{float(value):.6f}" for value in values)
