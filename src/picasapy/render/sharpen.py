"""Élesítés: unsharp / unsharp2 — a natív `0x0090c4a0` szerint (#3851).

Az `unsharp=1` (v1) bitre azonos az `unsharp2=1,0.600000`-val (mérve).

## A keverés: `K = csonk(512 · s)`, egész aritmetika (#3851)

A visszahívás (`0x008f8f30`) az `s` erősséget és a beégetett 1,5-ös
szélesítőt adja a munkavégzőnek (`0x0090c4a0`). Az ott kiolvasott keverés
(spec `docs/specs/filters-decoded.md`, „`unsharp` / `unsharp2` — a keverés és
az erősség kiolvasva"):

* `K = csonk(512 · s)` (`0x0090c582`, `[0xcf4c48]` = 512,0);
* képpontonként, csatornánként `ki = clamp(A + (((A − B) · K) >> 8), 0, 255)`,
  ahol A az eredeti, B az elmosott kép, a `>>` aritmetikai (`sar`, lefelé
  kerekít) — `0x0090c5f5`–`0x0090c667`.

Az erősítés tehát **`K/256 = 2·s`**. A korábbi, mérésből illesztett `1,21·s`
az alapállásban (s = 0,6 → 1,2) még közel járt, a legerősebb állásban
(s = 3,0 → 6,0 helyett 3,63) viszont jóval gyengébben élesített.

## Az elmosás: köbös B-spline, 1 : 1 léptéken, FIXPONTOSAN (#762, #3851)

Az `unsharp` nem Gauss-szal mos, hanem az ÁTMÉRETEZŐT (`ytResampler`) hívja
**1 : 1 léptékkel**, a **2-es szűrőmóddal** (`0x0090c4fa`: `mov [esp+0x58],
2`). A 2-es mód magja **köbös B-spline**, tartósugár 2; a beégetett `1,5f`
a szélesítőbe megy, és a lépték pontosan `1/(1,5 + 0,001)`
(`0x00a3f728`–`0x00a3f741`, `[0xcf3db0]` = 0,001).

| bizonyíték | cím |
|---|---|
| a súlytáblát két móddal indexelt ugrótábla építi | `0xa40550` (tartósugár) · `0xa40574` (súlyfüggvény) |
| a 2-es mód tartósugara **2,0** | `0xa40550[2] = 0xa3f6df` |
| a 2-es mód magja **köbös B-spline** | `0xa40574[2] = 0xa3fb82`; `x ≥ 2 → 0`, `1 ≤ x < 2 → (2−x)³/6`, `0 ≤ x < 1 → (4−6x²+3x³)/6` |
| a szélesítő alapon 1,0, az `unsharp` **1,5**-öt ír bele | `0x00a3f553` `fld1` · `0x0090c4e2` |

A B-spline **nem interpoláló** (`w(±1) = 1/6 ≠ 0`), ezért 1 : 1 arányban is
mos. Az átméretező a súlyokat EGÉSSZÉ alakítja, és egész aritmetikával
alkalmaz (`filterdesc-registry.md` 5/c):

* `w_int = csonk(w · 16383 / Σw)`, a maradék (`16383 − Σ w_int`) a középső
  csapé; a képen kívüli csap kimarad, tehát a szélen a súlyok
  képpontonként újranormálódnak;
* csatornánként `(Σ w_int · p + 255) >> 14`, előbb a vízszintes menet, 8
  bites köztes képpel, utána a függőleges.

A belső mag így `0 · 538 · 4029 · 7249 · 4029 · 538 · 0` (összeg 16383). A
legerősebb állásban ez a fixpontos elmosás a döntő: a hatszoros erősítés a
köztes kép egész kerekítését is felnagyítja (lebegőpontos elmosással a max
állás ΔE-je 0,861 maradna, fixpontossal 0,277).
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import validate_image

#: A B-spline tartósugara a 2-es szűrőmódban (`0xa40550[2]`).
_BSPLINE_SUPPORT = 2.0

#: Az `unsharp` beégetett szélesítő szorzója (`0x0090c4e2`).
_UNSHARP_KERNEL_SCALE = 1.5

#: Az átméretező a szélesítőhöz 0,001-et ad (`[0xcf3db0]`).
_SZELESITO_TOBBLET = 0.001

#: A mag félszélessége: `ceil(2,0 · 1,5) = 3` képpont.
_SUGAR = int(np.ceil(_BSPLINE_SUPPORT * _UNSHARP_KERNEL_SCALE))

#: Fixpontos súlyegység, kerekítő és eltolás (`0x00a4031f`, `0x00a427b0`).
_FIX_EGYSEG = 16383
_FIX_KEREKITO = 255
_FIX_ELTOLAS = 14

#: `K = csonk(512 · s)` (`0x0090c582`, `[0xcf4c48]`), a keverés `>> 8`.
_KEVERES_SKALA = 512
_KEVERES_ELTOLAS = 8

#: A paraméter nélküli (v1) unsharp mért egyenértékese: unsharp2 s=0,6.
UNSHARP_V1_STRENGTH = 0.6

_BELSO_MAG: np.ndarray | None = None


def _cubic_bspline(x: float) -> float:
    """A köbös B-spline súlyfüggvény, a MÉRT három szakasszal (`0xa3fb82`)."""
    x = abs(x)
    if x >= _BSPLINE_SUPPORT:
        return 0.0
    if x >= 1.0:
        return (2.0 - x) ** 3 / 6.0
    return (4.0 - 6.0 * x * x + 3.0 * x**3) / 6.0


def _nyers_sulyok() -> np.ndarray:
    """A `−3 … 3` eltolások lebegőpontos, normálatlan súlyai."""
    leptek = _UNSHARP_KERNEL_SCALE + _SZELESITO_TOBBLET
    return np.array(
        [_cubic_bspline(offset / leptek) for offset in range(-_SUGAR, _SUGAR + 1)],
        dtype=np.float64,
    )


def _tengely_sulyok(meret: int) -> np.ndarray:
    """Egy tengely `(meret, 7)` alakú EGÉSZ súlyai, képpontonként normálva.

    A képen kívüli csap súlya 0, és nem számít a `Σw`-be; a maradék a
    középső (a kimeneti képponttal azonos indexű) csapé.
    """
    eltolasok = np.arange(-_SUGAR, _SUGAR + 1)
    indexek = np.arange(meret)[:, None] + eltolasok[None, :]
    ervenyes = (indexek >= 0) & (indexek < meret)
    nyers = np.where(ervenyes, _nyers_sulyok()[None, :], 0.0)
    osszeg = nyers.sum(axis=1, keepdims=True)
    sulyok = np.trunc(nyers * _FIX_EGYSEG / osszeg).astype(np.int32)
    sulyok[:, _SUGAR] += _FIX_EGYSEG - sulyok.sum(axis=1)
    return sulyok


def unsharp_blur_kernel() -> np.ndarray:
    """A belső (szélektől távoli) képpontok egész súlyai, összegük 16383.

    `0 · 538 · 4029 · 7249 · 4029 · 538 · 0` — a ±3-as csap nyers súlya
    `B₃(3/1,501) ≈ 4·10⁻¹⁰`, ez egészre csonkolva 0.
    """
    global _BELSO_MAG
    if _BELSO_MAG is None:
        _BELSO_MAG = _tengely_sulyok(2 * _SUGAR + 1)[_SUGAR].copy()
    return _BELSO_MAG.copy()


def _fixpontos_kimenet(gyujto: np.ndarray) -> np.ndarray:
    """`(Σ w·p + 255) >> 14`, 8 bitre. A gyűjtő egész értékű float32 —
    `16383 · 255 + 255 < 2²⁴`, tehát pontos."""
    return np.floor((gyujto + _FIX_KEREKITO) * (1.0 / (1 << _FIX_ELTOLAS))).astype(np.uint8)


def _szelso_gyujto(kep: np.ndarray, sulyok: np.ndarray, poz: int, tengely: int) -> np.ndarray:
    """Egy szélső sor/oszlop gyűjtője a saját, újranormált súlyaival."""
    resz = np.zeros(np.take(kep, [poz], axis=tengely).shape, dtype=np.float32)
    for csap in range(2 * _SUGAR + 1):
        suly = int(sulyok[poz, csap])
        if suly:
            forras = np.take(kep, [poz + csap - _SUGAR], axis=tengely)
            resz += np.float32(suly) * forras
    return resz


def _tengely_menten(kep: np.ndarray, tengely: int) -> np.ndarray:
    """Egy fixpontos menet a megadott tengely mentén (1 = vízszintes)."""
    meret = kep.shape[tengely]
    belso = unsharp_blur_kernel().astype(np.float32)
    mag = belso.reshape(1, -1) if tengely == 1 else belso.reshape(-1, 1)
    gyujto = cv2.filter2D(kep, cv2.CV_32F, mag, borderType=cv2.BORDER_CONSTANT)
    # a szélső képpontok súlyai újranormálódnak: ezeket külön számoljuk
    szelek = set(range(min(_SUGAR, meret))) | set(range(max(meret - _SUGAR, 0), meret))
    sulyok = _tengely_sulyok(meret)
    for poz in sorted(szelek):
        resz = _szelso_gyujto(kep, sulyok, poz, tengely)
        if tengely == 1:
            gyujto[:, poz : poz + 1] = resz
        else:
            gyujto[poz : poz + 1] = resz
    return _fixpontos_kimenet(gyujto)


def unsharp_blur(image: np.ndarray) -> np.ndarray:
    """Az `unsharp` elmosása: fixpontos köbös B-spline, előbb vízszintesen,
    8 bites köztes képpel (#762, #3851)."""
    return _tengely_menten(_tengely_menten(image, 1), 0)


def unsharp_blend(original: np.ndarray, blurred: np.ndarray, strength: float) -> np.ndarray:
    """A natív keverés: `clamp(A + (((A − B) · K) >> 8), 0, 255)`,
    `K = csonk(512 · s)` (#3851)."""
    k = int(_KEVERES_SKALA * strength)
    eredeti = original.astype(np.int32)
    kulonbseg = eredeti - blurred.astype(np.int32)
    kimenet = eredeti + ((kulonbseg * k) >> _KEVERES_ELTOLAS)
    return np.clip(kimenet, 0, 255).astype(np.uint8)


def apply_unsharp(
    image: np.ndarray, strength: float = UNSHARP_V1_STRENGTH
) -> np.ndarray:
    """Unsharp mask a natív szerint: fixpontos B-spline elmosás, `2·s`
    erősítés egész keveréssel (#3851)."""
    validate_image(image)
    if strength < 0:
        raise ValueError(f"Az élesítés erőssége nem lehet negatív: {strength}")
    if int(_KEVERES_SKALA * strength) == 0:
        return image.copy()
    return unsharp_blend(image, unsharp_blur(image), strength)
