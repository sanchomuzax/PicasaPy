"""A Picasa natív tónus-magjai: szinthúzás, kontraszt, gamma (#687).

A képletek a `docs/specs/picasa-native-filter-workers.md` 2.2–2.4 pontjában
rögzített, **dekompilált** munkafüggvényekből valók — nem illesztett
közelítések:

| cím | mi ez | ki hívja |
|---|---|---|
| `0x0090c1e0` | a szinthúzó LUT-építő (fekete-/fehérpont + gamma) | `triple2`, `triple3`, `autolight`, `finetune*` |
| `0x0090c100` | a kontraszt LUT-építő (exp(2·c) a középpont körül) | `contrast`, `triple` |
| `0x0090bc60` | a közös, 16 bites LUT-alkalmazó | mindkettő |

**Egy dokumentált eltérés a natívtól: a ditherelés.** A natív alkalmazó
(`0x0090bc60`) képpontonként egy MT19937-mintát húz, és a LUT helyi
meredekségével arányos, ±delta/2 amplitúdójú zajt kever a kimenetbe — ettől
nem sávosodik a széthúzott hisztogram. Ez a zaj nulla várható értékű, és
— a #2868 mérése szerint — **determinisztikus**: a generátor magozásában
nincs entrópiaforrás, a vetőmag `0x2D8228BE`, tehát futásról futásra
ugyanaz a zajkép. (A korábbi „nem determinisztikus, ezért villogna"
indoklás MEGDŐLT; a `picasa-native-filter-workers.md` 2.2-ben a #2868
helyesbítette.)

**A dither a #3092 óta MEGVAN** (`apply_native_lut16`). A bejárási sorrend
a #2926-tal került mérésre (`picasa-native-filter-workers.md` **2.2/b** és
**2.2/c**): sorfolytonos bejárás, képpontonként pontosan egy minta
mindhárom csatornára, csempézés és szálindítás nélkül.

**Mérve, a #685 mérőszettjén (a `contrast` három esete):**

| | ΔE dither NÉLKÜL | ΔE ditherrel | forrás ↔ export |
|---|---:|---:|---:|
| `contrast__alap` | 0,4666 | 0,5167 | 13,19 |
| `contrast__max` | 0,4881 | 0,5646 | 37,19 |
| `contrast__min` | 0,2954 | 0,3347 | 44,56 |

⚠️ **A ΔE tehát NEM javult, hanem kicsit ROMLOTT** (+0,04…+0,08) — és ennek
megvan az oka: a mi zajmintánk **nem azonos** a natívéval (más temperáló
maszkok, és a natív generátor állapota folyamat-globális), ezért a két zaj
nem oltja ki egymást, hanem **összeadódik**. Bitre egyezésre a jegy
kimondottan nem törekszik.

**A haszon a másik oldalon mérhető** — ugyanazon a képen, a hisztogram
üres rekeszeinek számában:

| szinthúzás | lyukak dither nélkül | ditherrel |
|---|---:|---:|
| erős (0,35–0,65) | **117** | **0** |
| közepes (0,2–0,8) | **46** | **0** |

⇒ A csere ára 0,05 ΔE (a készlet ~1,0-es zajszintje alatt), a nyeresége a
sávosodás teljes megszűnése. Ez a jegy kimondott célja.

⚠️ **Bitre egyezésre a #3092 sem törekszik:** a natív generátor állapota
folyamat-globális (az index `0x00d67f74` a hívások közt tovább él), tehát
ugyanannak a képnek a zaja attól is függ, mit dolgozott fel előtte a
program.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.render.curves import validate_image

#: A natív LUT teljes kitérése: `255 · 256` (8.8 fixpont).
NATIVE_LUT_FULL = 0xFF00

#: A natív dither generátorának vetőmagja (#2868). A `0x00d67f70` MT19937-et
#: a `.CRT$XC` tábla ELSŐ magozója indítja (`0xc416b0` → `0x00c32520`), tehát
#: az 1–3. `rand()`-ot kapja; az MSVC alapmagjával (1) ezek `41, 18467, 6334`,
#: és `mag = r3 ^ ((r2 ^ (r1 << 12)) << 12)` ⇒ `0x2D8228BE`.
#:
#: ⚠️ Entrópiaforrás NINCS a magozásban — a tábla mind a 884 bejegyzése
#: átnézve —, tehát a zajkép futásról futásra ugyanaz.
NATIVE_DITHER_SEED = 0x2D8228BE

#: A fényerő-paraméter szorzója a kontraszt-LUT-ban (`0x0090c100`):
#: ±1 nagyjából ±100 nyolcbites szintnek felel meg.
_BRIGHTNESS_SCALE = 25600.0

#: A kontraszt-feszítés középpontja (50 %) a 16 bites skálán.
_CONTRAST_PIVOT = 32768.0

_LEVELS = np.arange(256, dtype=np.float64)


def native_level_lut(
    black: float, white: float, gamma: float = 1.0
) -> np.ndarray:
    """A szinthúzó LUT (`0x0090c1e0`) — 256 elem, 16 bites értékekkel.

    ```c
    invG  = 1.0 / gamma;
    scale = (white != black) ? 1.0 / (white - black) : 1.0;
    LUT[i] = clamp(round((pow(i/255, invG) * 65280 - black * 65280) * scale),
                   0, 0xFF00);
    ```

    A sorrend **gamma → feketepont-eltolás → fehérpont-skálázás**. A
    degenerált (`white == black`) párnál a natív kód 1,0-s skálával megy
    tovább — ezt szándékosan átvesszük, mert a `triple2` felső
    csúszkaállásában (fekete = fehér = 1,0) éppen ez adja a mérésben látott
    fekete képet.

    ⛔ **#3418: `black > white` (INVERTÁLT feketepont) → TELJES FEHÉR.** A
    `finetune`/`finetune2` szűrő wire-formátuma nem korlátozza a Shadows
    (`black`) paramétert a `filterdesc.xml` UI-tartományára — az csak a
    csúszkát fogja vissza, a `.picasa.ini`-be kézzel/hibásan írt, tartományon
    kívüli érték a natív kódot **is** eléri. A 684-es golden mérőkészlet
    `finetune__max`/`finetune2__max` esete pont ezt méri (Shadows=1,0,
    Highlights=0,5 → `black=1,0 > white=0,5`): a képlet fenti alakja ekkor
    egy INVERTÁLT rámpát adna (a sötét bemenet fehér, a világos fekete
    lenne), a valódi Picasa-export viszont gyakorlatilag **egyenletes
    fehér** (ΔE a tiszta fehértől 3,4–3,7 — a JPEG zajszintjével egyező
    nagyságrend). Az invertált-rámpás modellünk ugyanerre 43–47 ΔE-t adott.
    Nincs dekompilált bizonyíték ARRA, hogyan jut el a natív kód a teljes
    fehérhez (feltehetően egy előjel nélküli/fixpontos reciprok-tábla
    „elszáll" negatív osztónál) — ez itt a MÉRÉSBŐL illesztett viselkedés,
    nem visszafejtett képlet.
    """
    if gamma <= 0.0:
        raise ValueError(f"A gamma pozitív kell legyen, nem {gamma}")
    if black > white:
        return np.full(256, NATIVE_LUT_FULL, dtype=np.int64)
    scale = 1.0 / (white - black) if white != black else 1.0
    curve = np.power(_LEVELS / 255.0, 1.0 / gamma)
    values = (curve * NATIVE_LUT_FULL - black * NATIVE_LUT_FULL) * scale
    return np.clip(np.rint(values), 0, NATIVE_LUT_FULL).astype(np.int64)


def native_contrast_lut(
    contrast: float, brightness: float = 0.0, gamma: float = 1.0
) -> np.ndarray:
    """A kontraszt-LUT (`0x0090c100`) — 256 elem, 16 bites értékekkel.

    ```c
    k = exp(2.0 * contrast);
    LUT[i] = clamp(round(k * ((pow(i/255, 1/gamma) * 65280
                               + brightness * 25600) - 32768) + 32768),
                   0, 0xFF00);
    ```

    A kontraszt a **középpont (50 %) körül** feszít, a fényerő **additív**, a
    gamma pedig a kontraszt ELŐTT hat.
    """
    if gamma <= 0.0:
        raise ValueError(f"A gamma pozitív kell legyen, nem {gamma}")
    factor = math.exp(2.0 * contrast)
    curve = np.power(_LEVELS / 255.0, 1.0 / gamma)
    shifted = curve * NATIVE_LUT_FULL + brightness * _BRIGHTNESS_SCALE
    values = factor * (shifted - _CONTRAST_PIVOT) + _CONTRAST_PIVOT
    return np.clip(np.rint(values), 0, NATIVE_LUT_FULL).astype(np.int64)


def _azonossag_lut(tabla: np.ndarray) -> bool:
    """Igaz, ha a LUT a 8.8 fixpontos AZONOSSÁG (`LUT[c] == c · 256`).

    Ilyen LUT-ot a semleges csúszka-állás ad; ld. a kapu indoklását az
    `apply_native_lut16`-ban."""
    if tabla.size < 256:
        return False
    return bool(np.array_equal(tabla[:256], np.arange(256, dtype=np.int64) * 256))


def _dither_minta(darab: int) -> np.ndarray:
    """`darab` darab 8 bites minta a natív generátorból (#3092).

    MT19937, a mért vetőmaggal — a `numpy` `RandomState`-je **ugyanaz az
    algoritmus** (624 szavas állapot, ugyanaz a temperálás: `>>11`,
    `<<7 & 0x9d2c5680`… ⚠️ a natív temperáló maszkjai ettől ELTÉRNEK
    (`0xff3a58ad`, `0xffffdf8c`), tehát a mintasorozat NEM azonos.

    Ez tudatos döntés, és a jegy (#3092) ki is mondja: **bitre egyezésre nem
    törekszünk**, mert a natív generátor állapota folyamat-globális (index
    `0x00d67f74`), tehát ugyanannak a képnek a zaja ott attól is függ, mit
    dolgozott fel előtte a program. A cél a SÁVOSODÁS megszüntetése a mért
    szabály szerint: egy minta képpontonként, a helyi meredekséggel arányos
    amplitúdó, nulla várható érték.

    Amit viszont átveszünk: a vetőmag értékét (a determinizmus forrása) és a
    sorfolytonos bejárást — a mintákat egyetlen, összefüggő sorozatból
    osztjuk ki, nem soronként vagy csempénként újramagozva (2.2/b, 2.2/c)."""
    generator = np.random.RandomState(NATIVE_DITHER_SEED)
    return generator.randint(0, 256, size=darab, dtype=np.int64)


def apply_native_lut16(
    image: np.ndarray, lut16: np.ndarray, *, dither: bool = True
) -> np.ndarray:
    """A közös 16 bites LUT-alkalmazó (`0x0090bc60`), **ditherrel** (#3092).

    ```c
    r = MT19937_next() & 0xff;              // KÉPPONTONKÉNT EGY minta
    for c in (R, G, B):
        lo    = LUT[c];  delta = LUT[c+1] - lo;
        v     = lo + ((delta * r) >> 8) - (delta >> 1);
        out_c = clamp(v >> 8, 0, 255);
    ```

    A `LUT` **257 elemű**: a 257. elem az utolsó másolata, hogy a `LUT[c+1]`
    ne fusson ki. A zaj amplitúdója a görbe helyi meredekségével (`delta`)
    arányos — ott ditherel, ahol a szinthúzás széthúzza a hisztogramot, és
    éppen ezért nem sávosodik.

    Egy minta jut egy képpontra, mindhárom csatornára ugyanaz ⇒ a zaj
    **szürke**, nem színes (2.2/b.2)."""
    validate_image(image)
    tabla = np.asarray(lut16, dtype=np.int64)
    if not dither:
        #: ⚠️ A `dither=False` NEM a natív viselkedés — a GÖRBE mérésére van.
        #: A dither ±0,5 szintnyi zajt visz a kimenetbe, ami a golden-lapok
        #: görbe-illesztését elmossa: ott a LUT alakja a mérés tárgya, nem a
        #: zaj. A terméki utak mind a ditherelt ágon mennek.
        return np.clip(tabla[:256] >> 8, 0, 255).astype(np.uint8)[image]
    if _azonossag_lut(tabla):
        #: ⛳ A SEMLEGES beállítás AZONOSSÁG marad — a dither nem nyúl hozzá.
        #:
        #: A natív képlet semleges LUT-tal (`lo = 256c`, `delta = 256`)
        #: `v = 256c + r − 128`-at ad, tehát a csonkolás után `c` vagy `c−1`:
        #: az eredeti is „zajt" vinne bele. CSAKHOGY az eredetiben a semleges
        #: csúszka **nem kerül a láncba**, tehát ez az eset ott elő sem áll —
        #: a viselkedése nincs mérve.
        #:
        #: Nálunk viszont ELŐÁLL: a `.picasa.ini`-ben bent maradhat egy
        #: nullára visszaállított bejegyzés, és akkor a kép némán ±1-gyel
        #: sötétedne, zajosan. Ugyanaz a csapda, amit a #956 a
        #: színhőmérséklet nulla állásánál fogott meg (`0x008f7fe6 jnp`): a
        #: natív hívó ott is KAPUZ.
        return image.copy()
    if tabla.size < 257:
        #: a natív LUT 257 elemű; a rövidebb táblát az utolsó elem másolata
        #: egészíti ki (`LUT[256] = LUT[255]`)
        tabla = np.concatenate([tabla, tabla[-1:]])

    lo = tabla[:256][image.astype(np.int64)]
    delta = (tabla[1:257] - tabla[:256])[image.astype(np.int64)]

    magassag, szelesseg = image.shape[:2]
    #: sorfolytonos bejárás: a minta a KÉPPONTHOZ tartozik, nem a csatornához
    minta = _dither_minta(magassag * szelesseg).reshape(magassag, szelesseg, 1)

    ertek = lo + ((delta * minta) >> 8) - (delta >> 1)
    return np.clip(ertek >> 8, 0, 255).astype(np.uint8)


def apply_native_levels(
    image: np.ndarray, black: float, white: float, gamma: float = 1.0
) -> np.ndarray:
    """Szinthúzás a natív magok szerint (`0x0090c3b0`).

    Ez a `triple2` (fekete-/fehérpont csúszka) és a `triple3`
    (Kiemelések/Árnyékok) második lépése. A #685 mérőszettjén a teljes
    `triple2`/`triple3` lánc átlagos ΔE-je a valódi Picasa-kimenethez
    **0,00–0,37** (az érintetlen kép 14,8–58,8) — vagyis pixelpontos.
    """
    return apply_native_lut16(image, native_level_lut(black, white, gamma))


def apply_native_contrast(
    image: np.ndarray,
    contrast: float,
    brightness: float = 0.0,
    gamma: float = 1.0,
) -> np.ndarray:
    """Kontraszt a natív mag szerint (`0x0090c2c0`).

    A `contrast` szűrő burkolója (`0x008f8a20`) fényerőnek 0-t, gammának
    1,0-t ad; a `triple` (`0x008f8a60`) mindkettőt csúszkából tölti.

    A #685 mérőszettjén az önálló `contrast` szűrő átlagos ΔE-je a valódi
    Picasa-kimenethez **0,18–0,31** (az érintetlen kép 6,0–20,9).
    """
    return apply_native_lut16(
        image, native_contrast_lut(contrast, brightness, gamma)
    )


def apply_gamma(image: np.ndarray, level: float) -> np.ndarray:
    """`gamma` („Gamma Correct") — a szinthúzó LUT tiszta gamma-ága.

    A burkoló (`0x008f8e30`) az egyetlen csúszkából `exp(szint)`-et számol
    (`0x0040eac0` = `exp`), és ezt adja tovább GAMMA-ként; a LUT-építő
    `1/gamma`-val emel hatványra, tehát a tényleges kitevő `exp(−szint)`.
    Pozitív szint világosít, negatív sötétít, a 0 azonosság, és a két
    végpont (0 és 255) helyben marad.

    A #685 mérőszettjén ez a leképezés adódott (mindhárom csúszkaálláson
    ΔE **0,34–0,41**, míg a fordított irány 8,3–45,7) — vagyis a kitevő
    iránya nem feltevés, hanem mért.
    """
    return apply_native_levels(image, 0.0, 1.0, gamma=math.exp(level))


__all__ = [
    "NATIVE_LUT_FULL",
    "apply_gamma",
    "apply_native_contrast",
    "apply_native_levels",
    "apply_native_lut16",
    "native_contrast_lut",
    "native_level_lut",
]
