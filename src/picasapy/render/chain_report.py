"""`apply_filters` jelentés-típusa és a renderelő-oldali tartomány-validáció
(#382, 2–3. pont). Külön modulban, hogy a `chain.py` a 800 soros
fájlméret-korlát alatt maradjon.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.render.chain_geometry import TartalomHely
from picasapy.render.op_geometry import LancHelyzet
from picasapy.render.registry import FILTER_REGISTRY, clamp_slider_value

#: Explicit (csúszka-index → paraméter-pozíció) leképezés a tartomány-
#: validációhoz (#382, 2. pont). Csak azokra a szűrőkre, ahol a leképezés
#: EGYÉRTELMŰ, mert a `chain.py` handlerei már ma is pozíció szerint olvassák
#: a paramétereket ugyanezekkel az indexekkel (ld. `_apply_sat_op`,
#: `_apply_tilt_op`, `_apply_finetune_op`/`_finetune_float`,
#: `_apply_unsharp_op`). Az 5./4. fül Glimmer-effektjeinél a numerikus és
#: szín-paraméterek KEVEREDNEK (ld. `filterdesc-registry.md` 4.1 pontja) —
#: ott a pozíció-leképezés általánosan nem triviális, ezért egyelőre nincs
#: bekötve (jövőbeli finomítás, nem #382 hatóköre). Ugyanezért marad ki a
#: `FocalZoom`/`PicnikFocalPixelate`/`Comicize` (#570/#569): a
#: `registry_data.py`-ban nincs hozzájuk csúszka-bejegyzés (a `filterdesc.xml`
#: e résztét a Glimmer-csővezeték, nem ez a tábla írja le), tehát
#: `FILTER_REGISTRY.get(...)` `None`-t adna vissza.
#:
#: #669: felvéve az irányított család (`dir_sat`/`dir_brite`/`dir_sharp`/
#: `dir_tint`) és a `linblur` — a pozíciókat a `directional.py`/
#: `linear_blur.py` handlerei (`_apply_dir_sat_op` és társai, `chain.py`)
#: adják: a `dir_*` triónál a korong (puck) a `filters=` láncban NEM
#: jelenik meg (ld. `directional.py` modul-docsztring), a két csúszka
#: közvetlenül az 1./2. pozíción áll; a `dir_tint`/`linblur` viszont VALÓDI
#: korong-pozíciót visel, ezért a csúszkák a korong (x, y) UTÁN jönnek.
#: Ugyanezen az alapon (pozíció ≡ regiszterbeli csúszka-sorrend, nincs
#: `log_base`) felvéve még: `radblur`, `radsat`, `radtint`, `glow`/`glow2`
#: (a `log_base`-es Radius csúszkájuk KIMARADT — softclamp-kivétel),
#: `tint`, `fill`.
_RANGE_VALIDATED_PARAM_POSITIONS: dict[str, tuple[tuple[int, int], ...]] = {
    "sat": ((0, 1),),
    "tilt": ((0, 1),),
    "unsharp": ((0, 1),),
    "unsharp2": ((0, 1),),
    #: ⛔ **#3418: a Kiemelések(1)/Árnyékok(2) csúszka NINCS itt.** Eredetileg
    #: mind a négy pozíció szerepelt (`(0,1),(1,2),(2,3),(3,5)`), és épp EZ
    #: adta a 684-es golden mérőkészlet legnagyobb ΔE-jét: a `finetune2__alap`
    #: esete Highlights=Shadows=0,5-tel (0,04-del a csúszka felső állása,
    #: 0,48 fölött) a klemp-elt modellel ΔE=52,3-at adott a valódi Picasa-
    #: exporthoz, a nyers (vágatlan) értékkel ΔE=0,57-et — a `[0..0.48]` a
    #: Picasa CSÚSZKÁJÁNAK a határa, nem a renderelő belső vágása, a natív
    #: képlet a nyers `.picasa.ini`-értéket kapja. A `finetune_level_lut`
    #: (`tone.py`) ezért NEM vág 0,48-ra; a szélsőséges, feketepontot a
    #: fehérpont fölé toló esetet (`finetune__max`/`finetune2__max`,
    #: Shadows=1,0) a `native_level_lut` `black > white` ága kezeli külön
    #: (teljes fehér, ld. ott). A Derítőfény(0) és a Színhőmérséklet(3)
    #: pozíció marad vágva — azok a golden-mérésben nem voltak hibaforrás.
    #:
    #: ⚠️ Ez a tábla ÉS a `tone.finetune_level_lut` KÉT FÜGGETLEN vágás
    #: volt ugyanarra a két paraméterre — csak az egyik eltávolítása
    #: (bármelyiké önmagában) NEM változtat a renderelt képen, mert a
    #: `validate_and_clamp_op` a `chain.py`-beli handler ELŐTT fut le, és a
    #: paramétert már vágva adja tovább. Egy korábbi kör csak a
    #: `tone.py`-t módosította, a mérésen nem látott változást, és emiatt
    #: tévesen elvetette a klemp-hipotézist.
    "finetune": ((0, 1), (3, 5)),
    "finetune2": ((0, 1), (3, 5)),
    "dir_sat": ((0, 1), (1, 2)),
    "dir_brite": ((0, 1), (1, 2)),
    "dir_sharp": ((0, 1), (1, 2)),
    "dir_tint": ((0, 3), (1, 4)),
    "linblur": ((0, 3),),
    "radblur": ((0, 3), (1, 4)),
    "radsat": ((0, 3), (1, 4)),
    "radtint": ((0, 3),),
    "glow": ((0, 1),),
    "glow2": ((0, 1),),
    "tint": ((0, 1),),
    "fill": ((0, 1),),
    # #687: a natív burkolókból bekötött szűrők. A csúszkák a `filters=`
    # láncban közvetlenül az engedélyező flag után, a regiszterbeli
    # sorrendjükben állnak (ld. `chain_native_handlers`), és egyiküknek
    # sincs `log_base`-e, a `shadow` Sugár csúszkáját kivéve — az ezért
    # marad ki a táblából (softclamp-kivétel).
    "contrast": ((0, 1),),
    "gamma": ((0, 1),),
    "colortemp": ((0, 1), (1, 2)),
    "backlight": ((0, 1),),
    # a `shadow` Sugár csúszkája `log_base`-es → softclamp-kivétel, kimarad
    "shadow": ((1, 2), (2, 3)),
    "triple": ((0, 1), (1, 2), (2, 3)),
    "triple2": ((0, 1), (1, 2), (2, 3)),
    "triple3": ((0, 1), (1, 2), (2, 3)),
}

#: A publikus csúszkatartományon kívüli, de a natív callback által külön
#: kezelt belső őrértékek. A `tint` pontos 256-a kihagyja a telítetlenítést
#: (#872); ettől a felületi/regiszterbeli tartomány továbbra is [-1, 255].
_INTERNAL_PARAM_SENTINELS: dict[tuple[str, int], frozenset[float]] = {
    ("tint", 0): frozenset({256.0}),
}


def validate_and_clamp_op(op: FilterOp) -> tuple[FilterOp, tuple[str, ...]]:
    """Tartományra vágja `op` ismert paramétereit (#382, 2. pont).

    A `picasapy.ini.filters` parszer szintjén NEM validálunk (round-trip
    elv) — ez a RENDERELŐ oldali védelem: ha egy paraméter kilóg a
    regiszterben megadott `[minimum, maximum]` tartományból, a renderelés a
    tartományra vágott értékkel folytatódik, és egy magyar nyelvű
    figyelmeztetés kerül a visszaadott listába (a `skipped` mintájára). A
    `log_base`-szal jelzett csúszkáknál (`clamp_slider_value`) a validáció
    KIMARAD — ott a tárolt érték szándékosan túllépheti a névleges
    tartományt (softclamp-kivétel, ld. `registry.clamp_slider_value`). A
    dokumentált natív belső őrértékek szintén változatlanul jutnak el a
    handlerig, anélkül hogy a publikus csúszkatartományt kitágítanánk.
    """
    key = op.name.casefold()
    positions = _RANGE_VALIDATED_PARAM_POSITIONS.get(key)
    spec = FILTER_REGISTRY.get(key)
    if not positions or spec is None:
        return op, ()
    warnings: list[str] = []
    params = list(op.params)
    for slider_index, position in positions:
        if position >= len(params):
            continue
        slider = spec.sliders[slider_index]
        try:
            raw_value = float(params[position])
        except ValueError:
            continue  # hibás/nem-szám paraméter — a handler majd elszáll rajta
        if raw_value in _INTERNAL_PARAM_SENTINELS.get((key, slider_index), frozenset()):
            continue
        clamped, out_of_range = clamp_slider_value(spec, slider, raw_value)
        if out_of_range:
            warnings.append(
                f"{op.name}: {slider.label} = {raw_value:g} a "
                f"[{slider.minimum:g}..{slider.maximum:g}] tartományon kívül, "
                f"vágva: {clamped:g}"
            )
            params[position] = f"{clamped:.6f}"
    if not warnings:
        return op, ()
    return dataclasses.replace(op, params=tuple(params)), tuple(warnings)


class ChainReport(tuple):
    """Az `apply_filters` visszatérési értéke (#382).

    VISSZAFELÉ KOMPATIBILIS 2-elemű tuple: `kép, kihagyott = apply_filters(...)`
    változatlanul működik — a jelentés csak egy `(kép, kihagyott_nevek)`
    tuple, ami emellett `.full_res`/`.slow`/`.resizes`/`.range_warnings`/
    `.legacy_warnings` attribútumokat is hordoz a hívóknak, akiknek ez kell
    (#382 3. pont).

    A `.legacy_warnings` (#567) azokat a kihagyott bejegyzéseket nevesíti,
    amelyeknél MEGVAN az ok, és az nem „még nem implementált":

    * **halott (legacy) név** — a 3.9.141.259 natív regiszterében sem
      render-callbackkel, sem névregisztrációval nem szerepel, tehát maga a
      Picasa sem futtatta már (`chain.DEAD_LEGACY_OPS`);
    * **mérten tétlen név** (#687) — van natív feldolgozója, de a #685
      mérőszettjén maga a Picasa sem változtatott vele a képen
      (`chain.MEASURED_IDLE_OPS`).

    Mindkettő a `skipped`-be is bekerül (a lánc kihagyja őket); a külön
    lista a KÜLÖNBÖZŐ okokat mondja ki, szűrőnként a saját üzenetével.

    A `.helyzet` (#3229) a lánc VÉGÉN érvényes koordináta-állapot: az eredeti
    kép mérete és a hozzá vezető leképezés. Aki a láncot KETTÉVÁGVA futtatja (a
    szerkesztő lánc-prefix gyorsítótára), ezt adja vissza a folytatásnak
    `bejovo=` gyanánt — enélkül a második hívás azt hinné, hogy a kapott kép az
    eredeti, és a `crop64` koordinátái meg a `content_placement` elcsúszna.

    A `.content_placement` (#3166) megmondja, **hol van a fénykép a
    kimenetben**, ha a lánc keret-effektet tartalmaz. Erre a szerkesztő
    átfedő rétegeinek (vágás-téglalap, arckeretek) van szüksége: ők a
    kirajzolt képre horgonyozódnak, az viszont keretes lánc esetén már a
    keretezett kimenet. `None`, ha nem volt keret-effekt.
    """

    # (Nincs `__slots__`: a `tuple` már változó hosszú C-szintű tárolást
    # használ, ami nem kombinálható nem-üres `__slots__`-szal — az extra
    # attribútumok ezért a szokásos instance-`__dict__`-be kerülnek.)

    def __new__(
        cls,
        image: np.ndarray,
        skipped: tuple[str, ...],
        *,
        full_res: bool,
        slow: bool,
        resizes: bool,
        range_warnings: tuple[str, ...],
        legacy_warnings: tuple[str, ...] = (),
        content_placement: TartalomHely | None = None,
        helyzet: LancHelyzet | None = None,
    ) -> "ChainReport":
        obj = super().__new__(cls, (image, skipped))
        obj.full_res = full_res
        obj.slow = slow
        obj.resizes = resizes
        obj.range_warnings = range_warnings
        obj.legacy_warnings = legacy_warnings
        obj.content_placement = content_placement
        obj.helyzet = helyzet
        return obj

    @property
    def image(self) -> np.ndarray:
        return self[0]

    @property
    def skipped(self) -> tuple[str, ...]:
        return self[1]
