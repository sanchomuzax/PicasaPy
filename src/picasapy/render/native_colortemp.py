"""A `colortemp` szűrő natív magja (#687) — `0x0090ea10`.

A szerkezet DEKOMPILÁLT (`docs/specs/picasa-native-filter-workers.md` 2.5):

```c
k_down[i] = (i * (256 - s)) >> 8;                            // lekicsinyítés
k_up[i]   = clamp((i * (65536 / (256 - s))) >> 8, 0, 255);   // a pontos inverze
P[i]      = i * (256 - i);                                   // középtónus-parabola
t_pos     = (t >= 1) ? t : 0;

r = k_down[R];   R' = r + ((P[r] * t)     >> 15);
g = k_down[G];   G' = g + ((P[g] * t_pos) >> 17);
b = k_down[B];   B' = b - ((P[b] * t)     >> 15);
ki = (k_up[clamp(R')], k_up[clamp(G')], k_up[clamp(B')])
```

Három dolog, ami ebből következik: a hatás **középtónus-súlyozott** (a fekete
és a fehér közelében `P → 0`, ott nem változik semmi); a zöld **negyed
súllyal** és **csak melegítéskor** mozdul; a fehérváltás pedig egy globális
lekicsinyítés, amit a végén a pontos inverze visszaad — ez teremt fejteret,
hogy a vörös emelése ne vágjon be.

**Ez NEM a `finetune`/`finetune2` p5 színhőmérséklete.** Azt a #551 mérése
alapján a `tone.apply_color_temperature` csatornánkénti konstans szorzói
adják, és ott ez a natív képlet MÉRTEN rosszabbul illeszkedett — a két utat
szándékosan nem vezetjük egy kulcsra.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image

#: A hideg↔meleg csúszka egészre skálázása. A `filterdesc.xml` szerint a
#: csúszka tartománya `[-0.5, 0.5]`; a ×256 a #685 mérőszettjén IGAZOLT
#: (a `colortemp` mindhárom mérőesete a `t/HidegMeleg = 256` aránynál a
#: legjobb, ΔE 0,63–1,30 — az érintetlen kép 11,7–55,3).
_COOL_TO_WARM_SCALE = 256.0

#: A fehérváltás csúszka egészre skálázása. **MÉRT, nem visszafejtett:** a
#: natív kódban a szorzás az x87-veremen történik, a dekompilátum nem őrizte
#: meg. A #685 mérőszettjén a ×128 adódott (a `s/Fehérváltás = 128` arány
#: mindkét nem-nulla mérőesetben a legjobb) — vagyis a fele annak, amit a
#: hideg↔meleg tengely kap. A #317 kalibrációs jegye finomíthatja.
_WHITE_SHIFT_SCALE = 128.0

#: A `256 - s` osztó nem mehet nulláig: a natív kód ott elszállna. A csúszka
#: névleges felső állása (1,0) a mért skálával 128-at ad, tehát ez a védés
#: éles használatban sosem lép be — csak a tartományon kívüli ini-értéknél.
_MAX_WHITE_SHIFT_STEPS = 255

_LEVELS = np.arange(256, dtype=np.int64)

#: A középtónus-parabola: `P[i] = i · (256 − i)`, maximuma 16384 a 128-nál.
_MIDTONE_PARABOLA = _LEVELS * (256 - _LEVELS)


def _white_shift_tables(shift_steps: int) -> tuple[np.ndarray, np.ndarray]:
    """A `k_down` / `k_up` táblapár a fehérváltás egész lépéseiből."""
    span = 256 - shift_steps
    down = (_LEVELS * span) >> 8
    up = np.clip((_LEVELS * (65536 // span)) >> 8, 0, 255)
    return down, up


def apply_native_colortemp(
    image: np.ndarray, cool_to_warm: float, white_shift: float
) -> np.ndarray:
    """`colortemp=1,HidegMeleg,Fehérváltás` — a natív `0x0090ea10` mása.

    A modul docstringje írja le az algoritmust és azt, hogy a két csúszka
    egészre skálázása közül a hideg↔meleg tengelyé visszafejtett-és-mért, a
    fehérváltásé viszont KIZÁRÓLAG mért (`_WHITE_SHIFT_SCALE`).

    Mindkét csúszka nullán a kimenet bájtra azonos a bemenettel.
    """
    validate_image(image)
    warm = int(round(cool_to_warm * _COOL_TO_WARM_SCALE))
    shift = min(
        max(int(round(white_shift * _WHITE_SHIFT_SCALE)), 0),
        _MAX_WHITE_SHIFT_STEPS,
    )
    if warm == 0 and shift == 0:
        return image.copy()
    down, up = _white_shift_tables(shift)
    warm_green = warm if warm >= 1 else 0
    values = image.astype(np.int64)
    red, green, blue = (down[values[..., channel]] for channel in range(3))
    shifted = (
        np.clip(red + ((_MIDTONE_PARABOLA[red] * warm) >> 15), 0, 255),
        np.clip(green + ((_MIDTONE_PARABOLA[green] * warm_green) >> 17), 0, 255),
        np.clip(blue - ((_MIDTONE_PARABOLA[blue] * warm) >> 15), 0, 255),
    )
    return np.stack([up[channel] for channel in shifted], axis=-1).astype(np.uint8)


__all__ = ["apply_native_colortemp"]
