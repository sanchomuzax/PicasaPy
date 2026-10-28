"""A Glimmer AutoFix hisztogram- és mintavételi műveletei."""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.quantize_palette import pontminta_racs



#: Az `AutoFix` LUT-képletének kiolvasott konstansai (#2229):
#: `0x00cf39d0` = 255,0 és `0x00c72150` = 0,5.
_AUTOFIX_SKALA = 255.0

_AUTOFIX_KEREKITES = 0.5


#: A pontminta küszöbe (#3797, `0x00bc2ea6` `cmp eax, 0x3e8`): ennél NEM
#: nagyobb képpontszámnál a teljes kép számít.
_AUTOFIX_MINTA_KUSZOB = 1000



def _autofix_mintameret(szelesseg: int, magassag: int) -> tuple[int, int]:
    """A pontminta rácsmérete 1000 képpont fölött (#3797, `0x00bc2f6a`,
    `0x00bc2fb5`): `s = sqrt(float32(1000 / (w·h)))`,
    `nW = max(1, trunc(w·s + 0,5))`, `nH = max(1, trunc(h·s + 0,5))`.
    960 × 640-nél ez 39 × 26."""
    arany = np.float32(_AUTOFIX_MINTA_KUSZOB / float(szelesseg * magassag))
    s = float(np.sqrt(arany))
    nW = max(1, int(szelesseg * s + 0.5))
    nH = max(1, int(magassag * s + 0.5))
    return nW, nH



def _autofix_hisztogram_forras(image: np.ndarray) -> np.ndarray:
    """A hisztogram forrása: ≤ 1000 képpontnál a teljes kép, fölötte az
    `nW × nH` pontminta (#3797). A `diag(w/nW, h/nH)` mátrix, 16.16
    fixpontban, ugyanazzal a mintavevővel, mint a `QuantizePalette`
    (`render/quantize_palette.py`, `pontminta_racs`)."""
    magassag, szelesseg = image.shape[:2]
    if szelesseg * magassag <= _AUTOFIX_MINTA_KUSZOB:
        return image
    nW, nH = _autofix_mintameret(szelesseg, magassag)
    return pontminta_racs(image, nW, nH, szelesseg / float(nW), magassag / float(nH))



def autofix(image: np.ndarray) -> np.ndarray:
    """`AutoFix`: a Glimmer belső, effekt-csővezetékekben újrahasznált
    automatikus javítása — **vágás nélküli min–max szinthúzás** (#2229).

    ⚠️ **NEM azonos a „Jó napom van"-nal.** A natív parancs
    (`0x009db610`, #535/#721) vágópont-keverést végez; a Glimmer
    `AutoFixImageOperation` **másik kódút**, és a munkavégzője
    (`0x00bc2d70`) mást csinál:

    1. három **egyszerű** 256 rekeszes hisztogram (`0x00bc2e50`) — vágás,
       súlyozás, percentilis **nincs** benne, és 1000 képpont fölött NEM
       a teljes képen, hanem egy pontmintán számol (ld. lent);
    2. csatornánként LUT (`0x00bc3170`), ami viszont a TELJES képre hat:

    ```
    lo = az első nem üres rekesz,  hi = az utolsó nem üres rekesz
    lo == hi  ->  LUT[x] = 255
    egyébként ->  LUT[x] = clamp(trunc((x − lo)/(hi − lo)·255 + 0,5), 0, 255)
    ```

    A `255,0` és a `0,5` konstans kiolvasva (`0x00cf39d0`, `0x00c72150`).

    A különbség nem elméleti: egyetlen kiugró szélső képpont a vágópontos
    modellben eltűnik, itt viszont **meghatározza a tartományt**. Hat
    Glimmer-effekt hívja belül (Holga, NightVision, PencilSketch, Sixties,
    Cinemascope, kétszer a PencilSketch), tehát mindegyik kimenetét
    érinti.

    **A hisztogram mintája (#3797).** 1000 képpont fölött a hisztogram
    NEM a teljes képből, hanem egy `nW × nH` pontmintából épül:
    `s = sqrt(float32(1000/(w·h)))`, `nW = max(1, trunc(w·s + 0,5))`,
    `nH = max(1, trunc(h·s + 0,5))`. A minta legközelebbi szomszéd,
    a mintaképpont közepét (`+0,5`) vetíti vissza a `diag(w/nW, h/nH)`
    mátrixszal, 16.16 fixpontban — ugyanaz a mintavevő, mint a
    `QuantizePalette`-ben (`render/quantize_palette.py`,
    `pontminta_racs`). A ritka szélső képpontok (pl. egy vékony sötét
    vonal) így kimaradnak a tartomány-számításból; a LUT-ot ennek
    ellenére a teljes képre alkalmazzuk. Ld. `docs/specs/filterdesc-registry.md`,
    6/a pont.
    """
    validate_image(image)
    minta = _autofix_hisztogram_forras(image)
    kimenet = np.empty_like(image)
    for csatorna in range(image.shape[2]):
        sik = minta[..., csatorna]
        hasznalt = np.flatnonzero(np.bincount(sik.reshape(-1), minlength=256))
        lo, hi = int(hasznalt[0]), int(hasznalt[-1])
        if lo == hi:
            kimenet[..., csatorna] = 255
            continue
        x = np.arange(256, dtype=np.float64)
        # CSONKOLÁS, nem kerekítés: a natív út a `0x00c29990`-en át megy,
        # ami `cvttsd2si` — trunkál. A `+ 0,5` MAGA a felfelé kerekítés
        # idiómája; `np.round`-dal kétszer kerekítenénk, és a felezőpontok
        # a numpy bankár-kerekítése miatt páros felé csúsznának el
        # (pl. 101,5 -> 102 helyett a natív 101-et ad).
        lut = np.clip(
            np.floor((x - lo) / (hi - lo) * _AUTOFIX_SKALA + _AUTOFIX_KEREKITES),
            0.0,
            255.0,
        ).astype(np.uint8)
        kimenet[..., csatorna] = lut[image[..., csatorna]]
    return kimenet
