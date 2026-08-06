"""A `filterdesc.xml` alapján épített szűrő-regiszter (#382).

Egyetlen, adatvezérelt igazságforrás a `filters=` lánc mind a 84
szűrőjéről: UI-név, üzemmód, teljesítmény-/geometria-jelzők, csúszkánkénti
név/tartomány/alapérték. A nyers táblát a `registry_data.py` tartalmazza
(kézzel felvéve `docs/specs/filterdesc-registry.md` 2. és 4.2 fejezetéből);
ez a modul építi belőle a tipizált, frozen dataclass-okat, és ad néhány
segédfüggvényt a renderelő (`chain.py`) számára.

A `.picasa.ini`-PARSZER szintjén (`picasapy.ini.filters`) szándékosan NEM
történik itt semmilyen szigorítás — a round-trip elv szent, amit nem
értünk, azt változatlanul visszaírjuk. A regiszter csak a RENDERELŐ oldalán
használatos (tartomány-validáció, sáv-jelzők).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from picasapy.render.registry_data import RAW_FILTERS

FilterMode = Literal["history", "oneclick", "soft", "tool", "effect"]
ZeroState = Literal["none", "zero", "defaults"]
ColorKind = Literal["none", "wheel_v0", "wheel_v1", "circle"]


@dataclass(frozen=True)
class SliderSpec:
    """Egyetlen csúszka a szűrőn belül (offset-korrigált tartománnyal)."""

    index: int
    label: str
    minimum: float
    maximum: float
    default: float | None
    log_base: float | None  # jelenléte esetén: a tárolt érték a MAPPELT érték
    hidden: bool


@dataclass(frozen=True)
class FilterSpec:
    """Egy szűrő teljes leírása a filterdesc-regiszterből."""

    key: str  # ini-kulcs, kisbetűsítve illesztve
    label: str
    mode: FilterMode
    zero_state: ZeroState
    full_res: bool
    slow: bool
    resizes: bool  # MEGVÁLTOZTATJA a kimeneti képméretet
    rotates: bool
    persists_region: bool
    sliders: tuple[SliderSpec, ...]
    color_kind: ColorKind
    has_puck: bool  # fókuszpont-kurzor → x,y paraméterek


def _derive_zero_state(mode: str, sliders: tuple[SliderSpec, ...]) -> ZeroState:
    """A `zerostate` XML-attribútumot a táblázat nem közli soronként — csak a
    `finetune2` mintapéldája ismert (`zerostate="zero"`, ld. a doksi 1.
    fejezetének XML-részlete). Ebből a mintából vezetjük le a szabályt: a
    „Gyakori javítások"/„Finomhangolás" (`mode="soft"`) csúszkák „nulla"
    állapota `zero`, HACSAK valamelyik csúszka nem-nulla `default`-tal
    rendelkezik (pl. `triple2` White Point-ja `1.0`) — ekkor `defaults`. A
    többi módnál (`history`/`oneclick`/`tool`/`effect`) nincs értelmezett
    „nulla" fül-állapot, ezért `none`.

    Ez levezetett (nem a nyers táblából olvasott) érték — a `finetune2`
    esetén IGAZOLTAN egyezik az eredetivel, a többinél ésszerű becslés.
    """
    if mode != "soft":
        return "none"
    has_nonzero_default = any(
        slider.default is not None and slider.default != 0.0 for slider in sliders
    )
    return "defaults" if has_nonzero_default else "zero"


def _build_slider(raw: tuple) -> SliderSpec:
    index, label, minimum, maximum, default, log_base, hidden = raw
    return SliderSpec(
        index=index,
        label=label,
        minimum=minimum,
        maximum=maximum,
        default=default,
        log_base=log_base,
        hidden=hidden,
    )


def _build_spec(raw: tuple) -> FilterSpec:
    (
        key,
        label,
        mode,
        full_res,
        slow,
        resizes,
        rotates,
        persists_region,
        sliders_raw,
        color_kind,
        has_puck,
    ) = raw
    sliders = tuple(_build_slider(s) for s in sliders_raw)
    return FilterSpec(
        key=key,
        label=label,
        mode=mode,
        zero_state=_derive_zero_state(mode, sliders),
        full_res=full_res,
        slow=slow,
        resizes=resizes,
        rotates=rotates,
        persists_region=persists_region,
        sliders=sliders,
        color_kind=color_kind,
        has_puck=has_puck,
    )


#: A teljes regiszter, ini-kulcs (kisbetűsített) → `FilterSpec`.
FILTER_REGISTRY: dict[str, FilterSpec] = {
    raw[0]: _build_spec(raw) for raw in RAW_FILTERS
}


def get_filter_spec(key: str) -> FilterSpec | None:
    """A regiszter-bejegyzés lekérése kis-nagybetű-tűrően, `None` ha ismeretlen."""
    return FILTER_REGISTRY.get(key.casefold())


def clamp_slider_value(
    spec: FilterSpec, slider: SliderSpec, value: float
) -> tuple[float, bool]:
    """`(vágott_érték, kilógott_e)` — a `[minimum, maximum]` tartományra vágva.

    **Softclamp-kivétel (#382):** a `log_base`-szal jelzett csúszkáknál a
    tárolt érték a logaritmikusan LEKÉPEZETT tényleges paraméter, nem a
    csúszkaállás — ez a `range`-en túl is eshet (valós minta:
    `glow=1,0.432749,2.469705`, ahol a mért sugár túllépi a névleges [0,1]
    tartományt). Ilyen csúszkánál a validációt ki kell hagyni.
    """
    del spec  # jelenleg nem használt, de a szignatúra a jövőbeli bővítéshez kell
    if slider.log_base is not None:
        return value, False
    if value < slider.minimum:
        return slider.minimum, True
    if value > slider.maximum:
        return slider.maximum, True
    return value, False


def chain_flags(keys: "list[str] | tuple[str, ...]") -> tuple[bool, bool, bool]:
    """`(full_res, slow, resizes)` — igaz, ha a `keys` (a láncban szereplő,
    kisbetű-érzéketlenül illesztett szűrőnevek) között van legalább egy,
    amire az adott jelző fenn áll a regiszterben. Az ismeretlen (regiszterben
    nem szereplő) neveket figyelmen kívül hagyja."""
    full_res = slow = resizes = False
    for key in keys:
        spec = get_filter_spec(key)
        if spec is None:
            continue
        full_res = full_res or spec.full_res
        slow = slow or spec.slow
        resizes = resizes or spec.resizes
    return full_res, slow, resizes


__all__ = [
    "FilterSpec",
    "SliderSpec",
    "FILTER_REGISTRY",
    "get_filter_spec",
    "clamp_slider_value",
    "chain_flags",
]
