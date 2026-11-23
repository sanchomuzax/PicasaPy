"""A Retusálás ecsetkörének mérete az eredeti Picasa szerint (#7406).

A leképezés az eredeti binárisból és a `job-907`/`job-908`/`job-917`/`job-918`
felvételekből (`docs/specs/paritas-folyamat-7327.md`, G):

- a csúszka `t ∈ [0, 1]` helyzetéből (a fogantyú KÖZEPÉNEK helye a futásban) a
  mező `s = t`: LINEÁRIS (mérve a futás 24,2% és 73,5%-án és mindkét végén;
  az `s = t²` és az `s = 1,5·t - 0,5` cáfolt);
- a kör sugara a képernyőn `R = max(3, 100 · s · z)` képpont, ahol `z` a nézet
  nagyítása (1,0 = 100%): a nagyítással arányos;
- a forrásképi sugár `r = R / z`; a kép méretétől (szélesség, magasság,
  rövidebb oldal) NEM függ;
- induláskor `s = 0,25` (`0x0060a763`), miközben a fogantyú a csúszka
  KÖZEPÉN áll; a csúszka megérintése után `s = t`.

Nincs mérve, ezért nincs benne: a bináris `min(100, min(w, h) / 2)` kapuja a
200 képpontnál kisebb nézetre, a bináris `3 · max(z, 1)` minimuma (z ≤ 1-nél
azonos a 3-mal, z = 1,07-nél 0,21 képpont a különbség, amit a mérés nem
választ szét), és az 1:1 nagyítás.

A modul tiszta számolás (nincs Qt, nincs állapot), hogy a vezérlő és a próbák
ugyanabból a helyből számoljanak.
"""

from __future__ import annotations

import math

#: A csúszka egész skálája (`EditorRetouchPanel.qml`: `from: 1; to: 100`).
SLIDER_MIN = 1
SLIDER_MAX = 100
#: Induláskor a fogantyú a futás KÖZEPÉN áll (a 1..100 skálán az 50 a
#: `t = 0,495`: a közép ±0,5 képponton belül).
SLIDER_DEFAULT = 50

#: A csúszka megérintése előtti `s` (a konstruktor kezdőértéke, `0x0060a763`).
INITIAL_FRACTION = 0.25
#: A forrásképi sugár `s = 1`-nél, képpontban (a bináris `min(100, ...)` felső
#: korlátja a nézet rövidebb oldalára, legalább 200 képpontos nézeten).
SOURCE_RADIUS_AT_FULL = 100.0
#: A kör legkisebb sugara a KÉPERNYŐN, képpontban.
MIN_SCREEN_RADIUS = 3.0


def slider_position(value: int) -> float:
    """A csúszka egész értékéből a fogantyú helye a futásban, `[0, 1]`-re vágva."""
    span = SLIDER_MAX - SLIDER_MIN
    return max(0.0, min(1.0, (value - SLIDER_MIN) / span))


def brush_fraction(value: int, *, touched: bool) -> float:
    """Az `s` mező: érintetlen csúszkánál az induló érték, megérintés után `t`."""
    return slider_position(value) if touched else INITIAL_FRACTION


def sanitize_zoom(zoom: float) -> float:
    """Érvénytelen (nem véges vagy nem pozitív) nagyítás helyett az 1,0."""
    if not math.isfinite(zoom) or zoom <= 0.0:
        return 1.0
    return zoom


def screen_radius(fraction: float, zoom: float) -> float:
    """A kör sugara a képernyőn, képpontban: `max(3, 100 · s · z)`."""
    z = sanitize_zoom(zoom)
    return max(MIN_SCREEN_RADIUS, SOURCE_RADIUS_AT_FULL * fraction * z)


def source_radius(fraction: float, zoom: float) -> float:
    """A kör sugara a forrásképen, képpontban: a képernyő-sugár osztva a nagyítással."""
    z = sanitize_zoom(zoom)
    return screen_radius(fraction, z) / z


def relative_radius(radius_px: float, shorter_side: int) -> float:
    """A forrásképi sugár a `retouch=2` token relatív alakjában (a kép rövidebb
    oldalához mérve; az `ini/retouch.py` formátuma változatlan marad).

    A képnél nagyobb kör a képre vágva (1,0): az ini 16 bites kódolása 1,0 alatt
    marad."""
    if shorter_side <= 0:
        raise ValueError(f"a kép rövidebb oldala pozitív kell legyen, kapott: {shorter_side}")
    return min(1.0, radius_px / shorter_side)
