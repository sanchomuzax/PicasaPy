"""A videó VÁGÁSPONTJAI a `filters=` láncban (#1838).

Az eredeti Picasa videó-vezérlősávján be- és kimeneti pont áll
(`video_control_bar/setin`, `setout`), és a kezelő (`0x005952d0`) a
`moviestart` / `movieend` neveket hivatkozza — vagyis a vágáspontok **nem
önálló ini-kulcsok**, hanem a `filters=` lánc tokenjei, ott, ahol a
képszerkesztés tokenjei is:

```ini
[M4V01962.MP4]
filters=movieend=b40728fd;moviestart=80252d;
```

## A formátum — MÉRVE, nem következtetve

| jellemző | érték | honnan |
|---|---|---|
| a token neve | `moviestart`, `movieend` | `0xc81978` / `0xc81984` |
| az érték hossza | **64 bit** | `0x004673a0`: `%I64x`, két 32 bites rekeszbe olvas |
| az alak | kisbetűs hex, **vezető nullák nélkül** | a valódi minta: `80252d` (6 jegy) és `b40728fd` (8 jegy) |
| a sorrend | **nem kötött** | a mintában a `movieend` áll elöl |
| hiányzó token | „nincs vágás azon az oldalon" | az egyik videón nincs `movieend` |
| az időegység | **100 nanoszekundum** (DirectShow `REFERENCE_TIME`) | kontroll-mérés, lent |

**Az időegységet kontroll-mérés döntötte el**, nem egyezés-keresés: a tokenek
értékét a videók `ffprobe`-bal mért hosszához illesztve

| token | dekódolva | 100 ns-ként | ms-ként | a videó hossza |
|---|---:|---:|---:|---:|
| `80252d` | 8 398 125 | **0,840 s** ✅ | 8 398 s ❌ | 385,886 s |
| `b40728fd` | 3 020 368 125 | **302,037 s** ✅ | 3 020 368 s ❌ | 385,886 s |
| `bf0df826` | 3 205 363 750 | **320,536 s** ✅ | 3 205 364 s ❌ | 374,374 s |

a milliszekundumos olvasat órákat adna egy hatperces klipre.

## Amit ez a modul NEM tesz

Nem rajzol felületet, és nem vágja a videót: a vágáspontokat **értelmezi és
visszaírja**. A vezérlők (`setin`, `setout`, `trimslider`, `reset_trim`,
`capture_frame`) a #1838 további része.

⚠️ A lánc többi tokenje **érintetlen** marad, és a tokenek sorrendje sem
rendeződik át: egy idegen `.picasa.ini`-t nem mi írtunk, és a round-trip elv
szerint amit nem értünk, azt megőrizzük.
"""

from __future__ import annotations

from dataclasses import dataclass

from .filters import FilterOp, parse_filters_prefix, serialize_filters

#: A DirectShow `REFERENCE_TIME` egysége másodpercben: 100 ns.
TICK_PER_SECOND = 10_000_000

#: A két token neve, ahogy a bináris hivatkozza.
START_TOKEN = "moviestart"
END_TOKEN = "movieend"

#: Egy 64 bites előjel nélküli érték felső korlátja — a `%I64x` ennyit olvas.
_MAX_TICK = 2**64 - 1


@dataclass(frozen=True)
class MovieTrim:
    """A videó két vágáspontja 100 ns-os egységben; `None` = nincs vágás.

    A `None` SZÁNDÉKOSAN nem 0 és nem a hossz: a hiányzó token azt jelenti,
    hogy azon az oldalon nincs vágás, és ezt a különbséget az írásnak is
    meg kell őriznie (0-t írni azt állítaná, hogy a felhasználó a nulla
    pontra állította a kezdést)."""

    start: int | None = None
    end: int | None = None

    @property
    def trimmed(self) -> bool:
        return self.start is not None or self.end is not None

    def start_ms(self) -> int | None:
        return None if self.start is None else ticks_to_ms(self.start)

    def end_ms(self) -> int | None:
        return None if self.end is None else ticks_to_ms(self.end)


def parse_tick(value: str) -> int | None:
    """64 bites hex → 100 ns-os egység; `None`, ha nem értelmezhető.

    Elnézően olvasunk: az idegen `.picasa.ini` tartalmát nem mi írtuk, és egy
    romlott érték nem hiúsíthatja meg a videó megnyitását — ilyenkor „nincs
    vágás azon az oldalon" a helyes olvasat."""
    szoveg = (value or "").strip()
    if not szoveg:
        return None
    try:
        tick = int(szoveg, 16)
    except ValueError:
        return None
    if tick < 0 or tick > _MAX_TICK:
        return None
    return tick


def format_tick(tick: int) -> str:
    """100 ns-os egység → a MÉRT alak: kisbetűs hex, vezető nullák nélkül."""
    if tick < 0 or tick > _MAX_TICK:
        raise ValueError(f"A vágáspont nem 64 bites érték: {tick}")
    return format(tick, "x")


def ticks_to_ms(tick: int) -> int:
    """100 ns → ezredmásodperc (lefelé kerekítve — a lejátszó ms-ban áll)."""
    return tick // 10_000


def ms_to_ticks(ms: int) -> int:
    """Ezredmásodperc → 100 ns."""
    return int(ms) * 10_000


def trim_from_ops(ops: tuple[FilterOp, ...]) -> MovieTrim:
    """A vágáspontok a MÁR elemzett láncból.

    Több előfordulásnál az UTOLSÓ nyer — ugyanaz a szabály, amit a lánc
    többi tokenjénél is követünk (a későbbi írás felülírja a korábbit)."""
    start: int | None = None
    end: int | None = None
    for op in ops:
        if not op.params:
            continue
        if op.name == START_TOKEN:
            start = parse_tick(op.params[0])
        elif op.name == END_TOKEN:
            end = parse_tick(op.params[0])
    return MovieTrim(start=start, end=end)


def trim_from_filters(value: str) -> MovieTrim:
    """A vágáspontok a `filters=` lánc NYERS szövegéből.

    Az OLVASÓ ág elemzőjét használja (`parse_filters_prefix`): egy idegen
    fájl hibás tagja nem dobhat kivételt a videó megnyitásakor."""
    if not value:
        return MovieTrim()
    return trim_from_ops(parse_filters_prefix(value))


def ops_with_trim(
    ops: tuple[FilterOp, ...], trim: MovieTrim
) -> tuple[FilterOp, ...]:
    """A lánc a megadott vágáspontokkal — a többi token ÉRINTETLEN.

    * meglévő tokent a HELYÉN írunk át (a sorrend nem rendeződik át);
    * `None` érték esetén a tokent KIVESSZÜK (nincs vágás azon az oldalon);
    * új tokent a lánc VÉGÉRE fűzünk.
    """
    ertekek = {START_TOKEN: trim.start, END_TOKEN: trim.end}
    eredmeny: list[FilterOp] = []
    latott: set[str] = set()
    for op in ops:
        if op.name in ertekek:
            if op.name in latott:
                continue  # a duplikátumot nem őrizzük meg kétszer
            latott.add(op.name)
            tick = ertekek[op.name]
            if tick is None:
                continue
            eredmeny.append(FilterOp(op.name, (format_tick(tick),)))
            continue
        eredmeny.append(op)
    for nev in (START_TOKEN, END_TOKEN):
        tick = ertekek[nev]
        if tick is not None and nev not in latott:
            eredmeny.append(FilterOp(nev, (format_tick(tick),)))
    return tuple(eredmeny)


def filters_with_trim(value: str, trim: MovieTrim) -> str:
    """A `filters=` lánc szövege a megadott vágáspontokkal."""
    ops = parse_filters_prefix(value) if value else ()
    return serialize_filters(ops_with_trim(ops, trim))


__all__ = [
    "END_TOKEN",
    "START_TOKEN",
    "TICK_PER_SECOND",
    "MovieTrim",
    "filters_with_trim",
    "format_tick",
    "ms_to_ticks",
    "ops_with_trim",
    "parse_tick",
    "ticks_to_ms",
    "trim_from_filters",
    "trim_from_ops",
]
