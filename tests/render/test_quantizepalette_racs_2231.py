"""#2231: a Poszterizálás kimenete csatornánként EGYENLETES RÁCSRA ugrik.

## Miért van erre őr

A #2231 jegy azt kérte, hogy a `QuantizePalette` OKTREE-alapú
palettaválasztásra álljon át, mert a binárisban álló
`glimmer::QuantizePaletteImageOperation` (`0x00bb5ad0` → `0x00bb5b60`)
bizonyíthatóan oktree-t épít. **A binárisbeli olvasat helyes, a
következtetés mégsem áll:** a szállított szűrő LÁTHATÓ kimenete nem
palettaválasztás.

Mérve a NAS-mérőszett `quantizepalette__*` képein, a Picasa saját
exportjához hasonlítva (`export-202608202231`):

```
eset  Steps          ΔE mi↔Picasa   ΔE hű oktree↔Picasa   ΔE forrás↔Picasa
alap     8               0,268             28,552              19,009
min      2               0,687             93,301              73,485
```

A Picasa kimeneti képpontértékeinek **97,6%-a** (`min`: 98,4%) a
`round(i·255/(Steps−1))` rácson ül, ±2-vel. A rács `Steps = 8`-ra:
`0, 36, 73, 109, 146, 182, 219, 255`.

Az alábbi tesztek ezt a MÉRT viselkedést szögezik le. Mindegyik BUKIK,
ha valaki palettaválasztóra (oktree-re) cseréli a megvalósítást —
szándékosan, mert a csere a mérés szerint rontana.

⚠️ **Amit NEM állítanak:** azt, hogy a binárisbeli oktree-út nem létezik.
Létezik; hogy miért nem az fut a `.picasa.ini`-vezérelt renderben, az
NYITOTT kérdés (`docs/specs/filterdesc-registry.md`).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_tone import apply_quantizepalette

#: `Steps = 8` rácspontjai — `round(i·255/7)`, i = 0…7.
RACS_8 = (0, 36, 73, 109, 146, 182, 219, 255)


def _egyszinu(szin, meret: int = 8) -> np.ndarray:
    """Egyetlen színnel kitöltött kép — az elmosás rajta azonosság."""
    kep = np.empty((meret, meret, 3), dtype=np.uint8)
    kep[..., :] = np.array(szin, dtype=np.uint8)
    return kep


def _kimeneti_szin(szin, steps: float = 8.0) -> tuple[int, int, int]:
    """A hatás után a (homogén) kép közepének színe."""
    ki = apply_quantizepalette(
        _egyszinu(szin), steps=steps, smoothing=100.0, fade=0.0
    )
    return tuple(int(v) for v in ki[4, 4])


class TestASzurkeSkalaAMertRacsraUgrik:
    """A mérőkép felső, 12 mezős szürke sávja — forrás → a Picasa kimenete.

    A jobb oszlop a Picasa `export-202608202231/quantizepalette__alap.jpg`
    fájljából KIOLVASOTT érték (y = 70, a mezők közepe).
    """

    @pytest.mark.parametrize(
        ("forras", "picasa"),
        [
            (10, 0),
            (31, 36),
            (53, 36),
            (74, 73),
            (95, 109),
            (116, 109),
            (138, 146),
            (159, 146),
            (180, 182),
            (202, 219),
            (223, 219),
            (244, 255),
        ],
    )
    def test_a_szurke_mezo_a_picasa_ertekere_kepzodik(self, forras, picasa):
        kapott = _kimeneti_szin((forras, forras, forras))
        assert kapott == (picasa, picasa, picasa), (
            f"a {forras} szürke a Picasánál {picasa} lett, nálunk {kapott[0]}"
        )


class TestACsatornakFuggetlenek:
    """A színes sáv mezői — a leképezés csatornánként külön fut.

    Ez az a tulajdonság, amit egy palettaválasztó NEM tud utánozni: a
    `(41, 60, 199)` mezőből a Picasa `(36, 73, 182)`-t csinál, és ez a
    szín **nincs benne a forrásképben**. Oktree csak a kép SAJÁT
    színeinek átlagait adhatja vissza.
    """

    @pytest.mark.parametrize(
        ("forras", "picasa"),
        [
            ((200, 40, 40), (182, 36, 36)),
            ((40, 179, 60), (36, 182, 73)),
            ((41, 60, 199), (36, 73, 182)),
            ((220, 200, 41), (219, 182, 36)),
            ((200, 40, 190), (182, 36, 182)),
            ((39, 200, 210), (36, 182, 219)),
            ((235, 235, 235), (219, 219, 219)),
        ],
    )
    def test_a_szines_mezo_a_picasa_szinere_kepzodik(self, forras, picasa):
        assert _kimeneti_szin(forras) == picasa

    def test_minden_csatorna_a_racson_van(self):
        vegyes = np.arange(256, dtype=np.uint8).reshape(16, 16)
        kep = np.stack([vegyes, vegyes[::-1], vegyes.T], axis=2)
        ki = apply_quantizepalette(kep, steps=8.0, smoothing=100.0, fade=0.0)
        assert set(np.unique(ki).tolist()) <= set(RACS_8)


class TestAKepponkentiLekepezesKEPFUGGETLEN:
    """Ugyanaz a bemeneti szín ugyanazt a kimenetet adja MÁS képben is.

    Ez az őr foga. Egy oktree-paletta a kép színeloszlásából épül, tehát
    két különböző képben ugyanaz a képpont MÁS színt kapna. A mérés
    szerint a Picasa nem így viselkedik.
    """

    def test_ugyanaz_a_szin_mas_kornyezetben_is_ugyanaz(self):
        szin = (41, 60, 199)
        egyedul = apply_quantizepalette(
            _egyszinu(szin), steps=8.0, smoothing=100.0, fade=0.0
        )[4, 4]

        tarka = np.zeros((8, 8, 3), dtype=np.uint8)
        tarka[..., :] = np.array(szin, dtype=np.uint8)
        tarka[0, :] = (255, 0, 0)
        tarka[1, :] = (0, 255, 0)
        tarka[2, :] = (250, 250, 5)
        kornyezetben = apply_quantizepalette(
            tarka, steps=8.0, smoothing=100.0, fade=0.0
        )[4, 4]

        assert tuple(egyedul) == tuple(kornyezetben), (
            "a leképezés a kép színeloszlásától függ — ez palettaválasztás, "
            "nem a mért, csatornánként egyenletes rács"
        )

    def test_a_kimenet_uj_szint_is_adhat(self):
        """A `(36, 73, 182)` nincs a bemenetben — paletta nem adhatná."""
        kep = _egyszinu((41, 60, 199))
        ki = apply_quantizepalette(kep, steps=8.0, smoothing=100.0, fade=0.0)
        bemeneti = {tuple(int(v) for v in sor) for sor in kep.reshape(-1, 3)}
        assert (36, 73, 182) not in bemeneti
        assert tuple(int(v) for v in ki[4, 4]) == (36, 73, 182)


class TestAStepsASZINTSZAM:
    """`Steps` a csatornánkénti SZINTSZÁM, nem a paletta mérete.

    A binárisban a `Steps` a redukciós keret (`Steps − 1`, `Steps == 2`
    esetén 2), tehát ott palettaméret volna. A MÉRT kimeneten viszont
    `Steps = 8` mellett nyolc, `Steps = 2` mellett két csatornaszint van.
    """

    @pytest.mark.parametrize("steps", [2, 3, 8, 16, 30])
    def test_csatornankent_pontosan_steps_racspont_van(self, steps):
        atmenet = np.repeat(
            np.linspace(0, 255, 256, dtype=np.float32)[np.newaxis, :, np.newaxis],
            3,
            axis=2,
        ).astype(np.uint8)
        ki = apply_quantizepalette(
            atmenet, steps=float(steps), smoothing=100.0, fade=0.0
        )
        varhato = {round(i * 255 / (steps - 1)) for i in range(steps)}
        assert set(np.unique(ki[..., 0]).tolist()) <= varhato

    def test_steps_kettonel_a_ket_szelso_ertek_marad(self):
        """A mérőszett `min` esete: `Steps = 2` → csak 0 és 255."""
        assert _kimeneti_szin((10, 130, 250), steps=2.0) == (0, 255, 255)
