"""A Picasa 3 natív BGRA-elmosása (`0x00bc5680`, skalár ág) bitre pontosan (#3474).

A `DropShadow` rajzolója (`0x00bcd940`) ezt a diszpécsert hívja. A skalár
megvalósítás (`0x00bc6590` → `0x00bc7540` vízszintes, `0x00bc77b0`
függőleges; kimeneti segéd `0x00bc5480`, együtthatók `0x00bc5360`) egész
aritmetikájú, futóablakos dobozszűrő, tört súlyú szélső mintákkal:

    ki[i] = ( w · (s[i−h] + s[i+h]) + 2^k · Σ_{j=i−h+1}^{i+h−1} s[j] ) // osztó

ahol a mintaindex a sor/oszlop szélére VÁGOTT (a szélső minta ismétlődik),
az osztás előjel nélküli egész osztás (csonkol), és minden menet kimenete
bájt. A `quality` menetszámot jelent: előbb `quality` vízszintes, aztán
`quality` függőleges menet; mindegyik a négy csatornát (B, G, R, A)
egymástól függetlenül, azonos képlettel dolgozza fel — előszorzás és
alfa-súlyozás NINCS.

A `(k, h, w, osztó)` négyest a `0x00bc5360` képezi a sugárból (lásd
:func:`sugar_egyutthatok`). A sugarat előbb a `0x00bc52c0` `0…253` közé
vágja, a diszpécser pedig a tartomány felére korlátozza; egy tengely csak
akkor mosódik, ha a sugara > 1,0 és a hossza ≥ 2.

Igazolás: a natív kód unicorn-emulátorban futtatott kimenetével bitre
egyezik (#3474; a golden-készlet a
`tests/support/native_filter_reference/nativ_blur_3474.json`).
"""

from __future__ import annotations

import numpy as np

#: `0x00bc52c0`: a sugár felső korlátja (`[0x00cf0b4c]` = 253,0f).
SUGAR_MAX = 253.0
#: `0x00bc52c0`: a minőség (menetszám) tartománya.
MINOSEG_MIN, MINOSEG_MAX = 1, 15
#: `0x00bc5360`: a belső lépték kezdőértéke (`mov [esi], 6`).
_LEPTEK_ALAP = 6


def _ftol(x: float) -> int:
    """Az MSVC `_ftol2` (`0x00c29990`): nulla felé csonkoló egészre alakítás."""
    return int(np.trunc(x))


def sugar_egyutthatok(sugar: float) -> tuple[int, int, int, int]:
    """A `0x00bc5360` leképezése: sugár → `(k, h, w, osztó)`.

    - `k`: a belső minták súlyának kitevője (súly `2^k`),
    - `h`: a szélső minta távolsága (a belső minták `i−h+1 … i+h−1`),
    - `w`: a két szélső minta tört súlya (`0 ≤ w < 2^k`),
    - `osztó`: az összsúly, `(2h−1)·2^k + 2w`.
    """
    r = np.float32(sugar)
    n = _ftol(float(r))
    k = _LEPTEK_ALAP
    if n > 1:
        while k != 0:
            k -= 1
            n >>= 1
            if n <= 1:
                break
    if k != 0:
        # 0x00bc5401: v = chop((r − 1,0) · 2^(k−1)), 80 bites x87-ben pontos.
        v = _ftol((float(r) - 1.0) * float(1 << (k - 1))) & 0xFFFFFFFF
        maszk = (1 << k) - 1
        w = v & maszk
        h = ((v & ~maszk & 0xFFFFFFFF) >> k) + 1
        oszto = ((1 << k) + 2 * v) & 0xFFFFFFFF
        return k, h, w, oszto
    # 0x00bc539d (n ≥ 64): egész szélességű doboz, tört súly nélkül.
    # 0x00529e10 = ceilf (a CRT 0x00c090f0-ja; x87-ágán RC=felfelé, 0x1b3f).
    r1 = float(np.float32(float(r) - 1.0))
    v = _ftol(np.ceil(r1) * -0.5)
    h = 1 - v
    return 0, h, 0, 2 * h - 1


def _menet(kep: np.ndarray, tengely: int, k: int, h: int, w: int, oszto: int) -> np.ndarray:
    """Egy egydimenziós menet a megadott tengely mentén (`0x00bc7540`/`0x00bc77b0`).

    A képlet egy `[w, 2^k, …, 2^k, w]` súlyú, `2h + 1` hosszú szűrő a szélre
    vágott (ismételt) mintákon, utána egész osztás. A részösszeg a teljes
    sugártartományban legfeljebb 64 515 (`255 · (2w + 2^k · (2h − 1))`,
    mérve r = 1,01 … 253-ra), tehát a float32-es OpenCV-szűrő EGÉSZ
    pontossággal számolja (#3084: a numpy-futóösszeg a célgép előnézeti
    felbontásán 7 s volt). A `sepFilter2D` nem vált Fourier-útra, mint a
    `filter2D` nagy kernelnél.
    """
    from picasapy.lazy_cv2 import cv2

    sulyok = np.zeros(2 * h + 1, dtype=np.float32)
    sulyok[1:-1] = float(1 << k)
    sulyok[0] += w
    sulyok[-1] += w
    egyseg = np.ones(1, dtype=np.float32)
    kx, ky = (sulyok, egyseg) if tengely == 1 else (egyseg, sulyok)
    bemenet = kep.astype(np.float32)
    osszeg = cv2.sepFilter2D(bemenet, cv2.CV_32F, kx, ky, borderType=cv2.BORDER_REPLICATE)
    if osszeg.ndim == 2:
        osszeg = osszeg[..., np.newaxis]
    return (osszeg.astype(np.int64) // oszto).astype(np.uint8)


def _vagott_sugar(sugar: float, hossz: int) -> np.float32:
    """`0x00bc52c0` (0…253) majd a diszpécser `min(r, float32(hossz · 0,5))`-e."""
    r = np.float32(sugar)
    if not r > 0:  # a NaN és a negatív is 0 lesz
        r = np.float32(0.0)
    r = min(r, np.float32(SUGAR_MAX))
    return min(r, np.float32(hossz * 0.5))


def nativ_blur_bgra(
    kep: np.ndarray, sugar_x: float, sugar_y: float, quality: int = 3
) -> np.ndarray:
    """A natív `0x00bc5680` elmosás a teljes képre (`HxWx4` uint8, BGRA-sorrend).

    A csatornákat a kód nem különbözteti meg, tehát a csatornasorrend a
    kimenetet nem befolyásolja; a bemenet NEM előszorzott-átalakított.
    """
    if kep.ndim != 3 or kep.shape[2] != 4 or kep.dtype != np.uint8:
        raise ValueError("nativ_blur_bgra: HxWx4 uint8 kép kell")
    magas, szeles = kep.shape[:2]
    q = min(max(int(quality), MINOSEG_MIN), MINOSEG_MAX)
    rx = _vagott_sugar(sugar_x, szeles)
    ry = _vagott_sugar(sugar_y, magas)
    ki = kep.copy()
    return _tengelyenkent(ki, rx, ry, q)


def nativ_blur_csatorna(
    csatorna: np.ndarray, sugar_x: float, sugar_y: float, quality: int = 3
) -> np.ndarray:
    """Ugyanaz az elmosás egyetlen `HxW` uint8 csatornára.

    A natív kód a négy bájtot egymástól függetlenül, azonos képlettel
    mossa (`0x00bc5480`), ezért egy csatorna önállóan is számolható — a
    `DropShadow`-nál csak az alfa változik (az RGB a rétegen állandó).
    """
    if csatorna.ndim != 2 or csatorna.dtype != np.uint8:
        raise ValueError("nativ_blur_csatorna: HxW uint8 tömb kell")
    magas, szeles = csatorna.shape
    q = min(max(int(quality), MINOSEG_MIN), MINOSEG_MAX)
    ki = _tengelyenkent(
        csatorna[..., np.newaxis].copy(),
        _vagott_sugar(sugar_x, szeles),
        _vagott_sugar(sugar_y, magas),
        q,
    )
    return ki[..., 0]


def _tengelyenkent(ki: np.ndarray, rx: np.float32, ry: np.float32, q: int) -> np.ndarray:
    """`0x00bc6590`: előbb `q` vízszintes, aztán `q` függőleges menet."""
    magas, szeles = ki.shape[:2]
    if szeles >= 2 and rx > 1.0:
        par = sugar_egyutthatok(float(rx))
        for _ in range(q):
            ki = _menet(ki, 1, *par)
    if magas >= 2 and ry > 1.0:
        par = sugar_egyutthatok(float(ry))
        for _ in range(q):
            ki = _menet(ki, 0, *par)
    return ki


#: `0x00bb5050` — a sugár-kvantáló sávjai: `(alsó, felső, az alsó is benne)`;
#: a sávba eső sugár a FELSŐ értéket kapja (float32 konstansok,
#: `0x00cf3a58`/`0x00cf3a54` … `0x00cf3a48`/`0x00cf3a44`).
_KVANTALO_SAVOK = (
    (np.float32(5.0), np.float32(5.13), False),
    (np.float32(4.0), np.float32(4.13), False),
    (np.float32(3.0), np.float32(3.0625), True),
    (np.float32(2.0), np.float32(2.065), False),
)

#: `0x00bb4de0`: a `BlurImageOperation` tengelyenkénti felső korlátja
BLUR_OPERATION_MAX = np.float32(255.0)


def sugar_kvantal(sugar: float) -> float:
    """`0x00bb5050` — a `BlurImageOperation` sugár-kvantálója (#3084).

    1 alatt (és NaN-ra) 0; a 2/3/4/5 körüli keskeny sávok a sáv felső
    értékére ugranak (a 3-as sáv alulról zárt, a többi nyitott);
    egyébként a sugár változatlan.
    """
    x = np.float32(sugar)
    if not x >= np.float32(1.0):
        return 0.0
    for also, felso, zart in _KVANTALO_SAVOK:
        benne = (x >= also) if zart else (x > also)
        if benne and x < felso:
            return float(felso)
    return float(x)


def blur_image_operation(
    kep: np.ndarray, xblur: float, yblur: float, quality: int = 3
) -> np.ndarray:
    """A `glimmer::BlurImageOperation` (`0x00bb4de0`) egy `HxWxC` uint8 képre.

    Tengelyenként: 255 fölött 255, különben a `0x00bb5050` kvantáló; utána
    a DropShadow-val közös natív diszpécser (`0x00bb4fc9 call 0x00bc5680`).
    A csatornákat a natív kód egymástól függetlenül mossa, ezért RGB-re is
    ugyanazt adja, mint a BGRA első három csatornáján.
    """
    if kep.ndim != 3 or kep.dtype != np.uint8:
        raise ValueError("blur_image_operation: HxWxC uint8 kép kell")

    def _tengely(ertek: float) -> float:
        return float(BLUR_OPERATION_MAX) if np.float32(ertek) > BLUR_OPERATION_MAX else sugar_kvantal(ertek)

    magas, szeles = kep.shape[:2]
    q = min(max(int(quality), MINOSEG_MIN), MINOSEG_MAX)
    return _tengelyenkent(
        kep.copy(),
        _vagott_sugar(_tengely(xblur), szeles),
        _vagott_sugar(_tengely(yblur), magas),
        q,
    )
