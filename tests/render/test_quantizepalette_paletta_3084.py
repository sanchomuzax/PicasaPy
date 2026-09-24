"""#3084 — a Poszterizálás KÉPFÜGGŐ palettára kvantál, a binárisból kiolvasott úton.

## Mi dőlt meg

A korábbi két őr (`test_quantizepalette_racs_2231.py` és
`test_poszterizalas_meres_2454.py`, mindkettő törölve) azt szögezte le,
hogy a kimenet csatornánként egyenletes rácsra ugrik, és hogy ez „ΔE
0,268-ra" egyezik. Mindkét állítás egy TÉVES referenciára épült: az
`export-202608202231` mappa a PicasaPy saját exportja volt, nem a Picasáé
(PR #3440). A valódi Picasa-exportokon a kimenet egyszer sem rácsos.

## Mit olvastunk ki a binárisból (`docs/specs/filterdesc-registry.md`)

- a paletta egy **50 × 50-es mintából** épül (`0x00bb5c44`), amit
  **pontmintavétel** ad (`0x009e7420`): a kimeneti képpont KÖZEPE
  (`+0,5`, `0x00c72150`) 16.16-os fixpontban visszavetítve, egyetlen
  forrásképpont — nem átlag;
- a lépték **mindkét irányban `W / 50`** (`0x00bb5bd0` `fild [ebp+8]`, a
  szélesség): fekvő képen a minta alsó sorai a képen KÍVÜL esnek;
- a képen kívüli mintaképpont **0** (fekete; `0x009a8d80` `rep stosd` 0-val),
  és a beszúró (`0x00bb5d3b`) szűrés nélkül MINDET beszúrja,
  **oszlopfolytonos** sorrendben;
- a keresés `Steps == 2` esetén a gyökérnél **helyettesítő testvért** keres
  a `0x00cf0c48` táblából; minden más csomópont jelzője 1 (`0x00bcb9b8`).

## A mérce

A NAS `3084-poszterizalas` párjai és a mérőszett valódi Picasa-exportja, a
projekt kanonikus ΔE-jével (`tools/golden/compare_render.delta_e_cie76`):

| kép | forrás | rácsos (régi) | ez |
|---|---:|---:|---:|
| mérőkép (8/80/0) | 16,04 | 16,64 | 0,54 |
| természetes fotó (8/80/0) | 14,49 | 17,16 | 0,91 |
| mérőkép `min` (2/0/0) | 26,93 | 40,02 | 0,34 |

Az elmosás a `BlurImageOperation` natív útja
(`test_blur_image_operation_3084.py`); a Gauss-közelítéssel a paletta
ugyanez volt, de a ΔE 2,31 / 1,74 / 4,01.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.render import quantize_palette as qp
from picasapy.render.glimmer_tone import apply_quantizepalette

GYOKER = Path(__file__).resolve().parents[2]
NAS = Path("/mnt/nas/My Pictures/3084-poszterizalas")


def _veletlen(magassag: int, szelesseg: int, magvet: int = 3) -> np.ndarray:
    rng = np.random.default_rng(magvet)
    return rng.integers(0, 256, size=(magassag, szelesseg, 3), dtype=np.uint8)


class TestAMinta:
    def test_50x50_es_pontmintavetel_a_kepppont_kozepen(self):
        kep = _veletlen(100, 100)
        minta = qp.mintakep(kep)
        assert minta.shape == (50, 50, 3)
        # lépték 2: a (x+0,5)·2 = 2x+1 forrásképpont — egyetlen képpont, nem átlag
        for y, x in ((0, 0), (7, 31), (49, 49)):
            assert np.array_equal(minta[y, x], kep[2 * y + 1, 2 * x + 1])

    def test_a_lepték_MINDKET_iranyban_a_szelessegbol(self):
        """Fekvő kép: a sorok is W/50-nel lépnek, tehát a minta alja kilóg."""
        kep = _veletlen(60, 100)
        minta = qp.mintakep(kep)
        # (y+0,5)·2 < 60  ⇔  y < 29,75 → a 0…29. sor a képből jön
        assert np.array_equal(minta[29, 10], kep[59, 21])
        assert not minta[30:].any(), "a képen kívüli mintasorok feketék"

    def test_a_fixpontos_leptetes_a_16_16_os_lefele_kerekites(self):
        """Nem egész lépték: float32 mátrix, a forrás oszlopa
        `floor(f32(0,5·s)·65536) + x·floor(s·65536)`, `>> 16`."""
        kep = _veletlen(80, 137)
        minta = qp.mintakep(kep)
        s = float(np.float32(137 / 50.0))
        kezdo = int(np.floor(float(np.float32(0.5 * s)) * 65536))
        lepes = int(np.floor(s * 65536))
        for x in (0, 1, 17, 49):
            sx = (kezdo + x * lepes) >> 16
            sy = int(np.floor(float(np.float32(3.5 * s)) * 65536)) >> 16
            assert np.array_equal(minta[3, x], kep[sy, sx])

    def test_allo_kepen_minden_mintakeppont_a_kepbol_jon(self):
        kep = _veletlen(100, 60)
        assert qp.mintakep(kep).reshape(-1, 3).any(axis=1).mean() > 0.99


class TestAKereses:
    def test_steps_2_nel_a_gyoker_helyettesito_testvert_keres(self):
        """Csak a 0. és a 7. gyerek létezik; a 3-as indexű szín a táblázat
        `(2, 1, 5, 0, …)` sorából az első LÉTEZŐ testvérhez, a 0-hoz jut."""
        minta = np.zeros((50, 50, 3), np.uint8)
        minta[:, 25:] = (255, 255, 255)
        fa = qp.oktree_epit(minta, steps=2)
        keresett = (0, 128, 128)          # R-bit 0, G-bit 1, B-bit 1 → index 3
        assert qp.keres(fa, keresett) == (0, 0, 0)

    def test_steps_nagyobb_ketto_nel_a_gyoker_atlagat_adja(self):
        minta = np.zeros((50, 50, 3), np.uint8)
        minta[:, 25:] = (255, 255, 255)
        fa = qp.oktree_epit(minta, steps=8)
        assert qp.keres(fa, (0, 128, 128)) == (127, 127, 127)


class TestAKvantalas:
    def test_a_kimenet_legfeljebb_256_szinu_es_a_minta_szineibol_all(self):
        kep = _veletlen(120, 180)
        ki = qp.kvantal(kep, steps=8)
        assert ki.shape == kep.shape and ki.dtype == np.uint8
        assert len(np.unique(ki.reshape(-1, 3), axis=0)) <= 256

    def test_egyszinu_kep_valtozatlan_szinu_marad(self):
        kep = np.full((40, 60, 3), (200, 90, 30), np.uint8)
        ki = qp.kvantal(kep.copy(), steps=8)
        # a 60 széles kép 40 sora: a minta alja fekete, de a (200, 90, 30)
        # rekesze a saját ágában marad
        assert np.array_equal(ki[0, 0], (200, 90, 30))

    def test_a_bemenetet_nem_irja_at(self):
        kep = _veletlen(30, 40)
        eredeti = kep.copy()
        qp.kvantal(kep, steps=5)
        assert np.array_equal(kep, eredeti)

    def test_a_fade_100_a_forrast_adja(self):
        kep = _veletlen(30, 40)
        assert np.array_equal(apply_quantizepalette(kep, fade=100.0), kep)


def _compare_render():
    ut = GYOKER / "tools" / "golden" / "compare_render.py"
    spec = importlib.util.spec_from_file_location("compare_render_3084", ut)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["compare_render_3084"] = modul
    spec.loader.exec_module(modul)
    return modul


#: a mérőszett VALÓDI Picasa-exportja (a 08-20-as a PicasaPy sajátja volt, PR #3440)
MEROSZETT = Path("/mnt/nas/My Pictures/PicasaPy meroszett")
MEROSZETT_EXPORT = MEROSZETT / "export-202608151229"

#: (forrás, export, Steps, Smoothing, plafon) — a plafon a mért ΔE ~másfélszerese
PAROK = (
    (NAS / "quantizepalette__alap.jpg", NAS / "export/quantizepalette__alap.jpg", 8, 80, 1.0),
    (NAS / "Warm grasses by dcsearle.t21.jpg", NAS / "export/Warm grasses by dcsearle.t21.jpg", 8, 80, 1.5),
    (MEROSZETT / "quantizepalette__min.jpg", MEROSZETT_EXPORT / "quantizepalette__min.jpg", 2, 0, 0.6),
    #: a #2770 párja — ugyanaz a fotó, egy korábbi (09-09-i) Picasa-exporttal
    (Path("/mnt/nas/My Pictures/2770-poszterizalas/original.t21.jpg"),
     Path("/mnt/nas/My Pictures/2770-poszterizalas/export.t21.jpg"), 8, 80, 1.5),
)


@pytest.mark.parametrize(("forras_ut", "export_ut", "steps", "simitas", "plafon"), PAROK,
                         ids=lambda v: v.name if isinstance(v, Path) else str(v))
def test_a_picasa_exporthoz_merve(forras_ut, export_ut, steps, simitas, plafon):
    if not (forras_ut.is_file() and export_ut.is_file()):
        pytest.skip("a NAS-os mérőpár nem elérhető")
    cr = _compare_render()
    forras = cv2.cvtColor(cv2.imread(str(forras_ut)), cv2.COLOR_BGR2RGB)
    export = cv2.cvtColor(cv2.imread(str(export_ut)), cv2.COLOR_BGR2RGB)
    mienk = apply_quantizepalette(forras, steps=float(steps), smoothing=float(simitas), fade=0.0)
    de = float(np.mean(cr.delta_e_cie76(mienk, export)))
    assert de < plafon, f"{forras_ut.name}: ΔE {de:.2f} (a plafon {plafon})"
