"""#2229: a Glimmer `AutoFix` vágás NÉLKÜLI min–max szinthúzás.

A `render/glimmer_ops.py` `autofix`-e eddig a natív „Jó napom van"
(`0x009db610`) megfejtett modelljét hívta, **0,30-as vágópont-keveréssel**
(#535, #721). A Glimmer `AutoFixImageOperation` viszont **másik kódút**, és
a munkavégzője (`0x00bc2d70`) mást csinál:

1. három **egyszerű** 256 rekeszes hisztogram (`0x00bc2e50`) — vágás,
   súlyozás, percentilis **nincs** benne;
2. csatornánként LUT (`0x00bc3170`):

```
lo = az első nem üres rekesz,  hi = az utolsó nem üres rekesz
lo == hi  ->  LUT[x] = 255
egyébként ->  LUT[x] = clamp(round((x − lo)/(hi − lo) · 255 + 0,5), 0, 255)
```

A `255,0` és a `0,5` konstans kiolvasva (`0x00cf39d0`, `0x00c72150`).

A két függvény az EREDETIBEN is különbözik — a #535/#721 a **natív**
parancsot mérte, ez a jegy a **Glimmer**-műveletet.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.glimmer_ops import autofix


def _kep(ertekek: list[int]) -> np.ndarray:
    """Egysoros, szürke kép a megadott értékekből (mindhárom csatorna)."""
    sor = np.array(ertekek, dtype=np.uint8)
    return np.repeat(sor[np.newaxis, :, np.newaxis], 3, axis=2)


def test_a_teljes_min_max_tartomanyt_huzza_szet() -> None:
    """A legkisebb 0-ra, a legnagyobb 255-re megy — vágópont nélkül."""
    ki = autofix(_kep([64, 96, 128, 160, 192]))
    assert ki[0, 0, 0] == 0
    assert ki[0, -1, 0] == 255


def test_a_kozepso_ertek_a_kepletet_koveti() -> None:
    """`round((x − lo)/(hi − lo)·255 + 0,5)` — a 128 a 64…192 sávban
    pontosan félúton van, tehát 128."""
    ki = autofix(_kep([64, 96, 128, 160, 192]))
    assert int(ki[0, 2, 0]) == 128


def test_egyetlen_kiugro_keppont_is_szamit() -> None:
    """A VÁGÓPONTOS modell egy magányos szélső képpontot eldobna; a
    min–max szinthúzás NEM — ez a két modell szétválasztó esete."""
    ki = autofix(_kep([0] + [200] * 200 + [255]))
    # lo = 0, hi = 255 -> az azonosság-leképezés
    assert int(ki[0, 1, 0]) == 200
    assert int(ki[0, 0, 0]) == 0
    assert int(ki[0, -1, 0]) == 255


def test_egyszinu_kep_eseten_MINDEN_255() -> None:
    """`lo == hi` -> a natív ág fixen 255-öt ír a LUT minden rekeszébe."""
    ki = autofix(_kep([77] * 8))
    assert np.all(ki == 255)


def test_csatornankent_kulon_hisztogram() -> None:
    """A LUT csatornánként épül — az egyik csatorna szűk sávja nem
    befolyásolja a másikét."""
    kep = np.zeros((1, 3, 3), dtype=np.uint8)
    kep[0, :, 0] = [10, 20, 30]     # kék: szűk sáv
    kep[0, :, 1] = [0, 128, 255]    # zöld: teljes sáv
    kep[0, :, 2] = [100, 100, 100]  # vörös: egyszínű
    ki = autofix(kep)
    assert list(ki[0, :, 0]) == [0, 128, 255]
    assert list(ki[0, :, 1]) == [0, 128, 255]
    assert list(ki[0, :, 2]) == [255, 255, 255]


def test_a_felezopontok_LEFELE_csonkolnak_nem_paros_fele() -> None:
    """A natív út a `0x00c29990`-en megy, ami **`cvttsd2si`** — csonkol.

    A `+ 0,5` maga a felfelé kerekítés idiómája; `np.round`-dal kétszer
    kerekítenénk, és a numpy bankár-kerekítése a felezőpontokat PÁROS felé
    vinné. Ez a próba az a szétválasztó eset, ahol a kettő eltér.
    """
    # lo = 0, hi = 254 -> a 100-as bemenet nyers értéke 100,3937…,
    # a 101-esé 101,4015… ; a +0,5 után 100,89 és 101,90 -> 100 és 101.
    kep = _kep(list(range(0, 255)))
    ki = autofix(kep)
    varhato = [
        min(255, max(0, int((x - 0) / 254 * 255.0 + 0.5)))  # Python int() = csonkolás
        for x in range(0, 255)
    ]
    assert list(ki[0, :, 0]) == varhato
