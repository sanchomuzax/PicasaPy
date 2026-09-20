"""#3229 3. lépés — a MÉRT sorrend az ALAPÉRTELMEZÉS, és ezt golden dönti el.

## A tulajdonos exportja döntött (2026-09-19)

A `My Pictures\\3229-lanc-sorrend` készlet négy képét az eredeti, windowsos
Picasa exportálta. A döntő kép az `01-keret-utan-szepia.jpg`
(`Border=1,20,5,0,00000000,00ffffff,0;sepia=1;`): az eredeti kimenetén a keret
**barnás**, átlagos RGB **(46, 37, 28)** — vagyis a szépia a KERETRE is
ráment, tehát az eredeti a lánc sorrendjében dolgozik.

A kontroll a `02-szepia-utan-keret.jpg` (`sepia=1;Border=…`): ott a keret
**fekete** marad (0, 0, 0), ahogy kell, ha utoljára kerül fel.

Mérve a két águnkkal, ugyanezen a képen:

| ág | a keret RGB-je | átlagos ΔE a referenciához |
|---|---|---:|
| a régi (halasztott) | 0, 0, 0 | 4,481 |
| **a mért sorrend** | **46, 37, 29** | **2,278** |

⚠️ A készlet `04-vagas-utan-vignetta.jpg` képe NEM mér: a vágás a `filters=`
sorba került, a Picasa viszont a képszekció `crop=` kulcsából vág, ezért az
export vágatlan maradt. A vágás sorrendjét ezért továbbra is a #3169 bináris
mérése és a `test_mert_sorrend_3229.py` próbái fedik, nem golden.

## Amit ez a fájl őriz

Az itteni állítások **a renderelt kimenet képpontjait** mérik (a #3166
mintája), nem formulát hasonlítanak formulához: a keretsáv tényleges színét
olvassuk ki, és a szépia jelenlétét a csatornák SORRENDJE adja (R > G > B).
A referencia abszolút értékeit nem másoljuk ide — a próbakép más —, a
SZERKEZETI állítás viszont ugyanaz, ami a goldenen eldőlt.
"""

from __future__ import annotations

import numpy as np

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters

#: A golden-készlet Border-paramétere, szó szerint a `.picasa.ini`-ből.
KERET = "Border=1,20.000000,5.000000,0.000000,00000000,00ffffff,0.000000;"
SZEPIA = "sepia=1;"


def _proba(magassag: int = 240, szelesseg: int = 320) -> np.ndarray:
    """Középszürke próbakép — a keret színe így elválik a képtartalomtól."""
    return np.full((magassag, szelesseg, 3), 128, np.uint8)


def _keretsav(kep: np.ndarray) -> np.ndarray:
    """A kimenet legkülső képpont-sávja, (N, 3) alakban."""
    p = max(2, min(kep.shape[:2]) // 100)
    return np.concatenate(
        [
            kep[:p].reshape(-1, 3),
            kep[-p:].reshape(-1, 3),
            kep[:, :p].reshape(-1, 3),
            kep[:, -p:].reshape(-1, 3),
        ]
    )


class TestAKeretreRamegyAKesobbiEffekt:
    def test_a_keret_utan_futo_szepia_a_keretet_is_szinezi(self):
        """Ez az állítás dőlt el a tulajdonos exportján."""
        kep = apply_filters(_proba(), parse_filters(KERET + SZEPIA)).image
        r, g, b = _keretsav(kep).mean(axis=0)
        # szépia: a vörös csatorna a legnagyobb, a kék a legkisebb
        assert r > g > b, f"a keret nem szépiás: RGB=({r:.1f},{g:.1f},{b:.1f})"
        assert r - b > 5.0, f"a színezés túl gyenge: R−B={r - b:.1f}"

    def test_a_szepia_utan_felkerulo_keret_SEMLEGES_marad(self):
        """A kontroll-eset: fordított sorrendben a keret nem színeződik."""
        kep = apply_filters(_proba(), parse_filters(SZEPIA + KERET)).image
        r, g, b = _keretsav(kep).mean(axis=0)
        assert abs(r - b) < 1.0, f"a keret mégis színezett: R−B={r - b:.1f}"

    def test_a_ket_sorrend_LATHATOAN_mas_kepet_ad(self):
        elol = apply_filters(_proba(), parse_filters(KERET + SZEPIA)).image
        hatul = apply_filters(_proba(), parse_filters(SZEPIA + KERET)).image
        assert elol.shape == hatul.shape
        elteres = float(np.mean(np.abs(elol.astype(float) - hatul.astype(float))))
        assert elteres > 1.0, f"a két sorrend ugyanazt adta ({elteres:.3f})"


class TestAzAlapertelmezesAMertSorrend:
    def test_a_kapcsolo_nelkuli_hivas_a_MERT_sorrendet_adja(self):
        alap = apply_filters(_proba(), parse_filters(KERET + SZEPIA)).image
        mert = apply_filters(_proba(), parse_filters(KERET + SZEPIA), mert_sorrend=True).image
        assert np.array_equal(alap, mert)

    def test_a_regi_halasztott_ag_MAS_kepet_adott(self):
        """Kontroll: a kikapcsolt ág a régi (semleges keretű) képet adja."""
        regi = apply_filters(_proba(), parse_filters(KERET + SZEPIA), mert_sorrend=False).image
        r, g, b = _keretsav(regi).mean(axis=0)
        assert abs(r - b) < 1.0, f"a régi ág is színezte a keretet: R−B={r - b:.1f}"


class TestAzElonezetUgyanaztAdjaMintAMentes:
    def test_a_lanc_ketteva_vagva_ugyanazt_adja(self):
        """A szerkesztő lánc-prefix gyorsítótára a láncot KETTÉVÁGJA.

        A #3169 ezen a láncon 18,2 átlagos eltérést mért a két úton; a mért
        sorrendben a kettévágott futtatás ugyanazt adja, mint az egészben
        futtatott — ezért tűnhetett el az előnézet/mentés eltérése.
        """
        for lanc in (
            "crop64=1,20204040;Vignette=1,35.000000,1.400000,0.000000;",
            KERET + "Vignette=1,35.000000,1.400000,0.000000;",
            KERET + SZEPIA,
        ):
            ops = parse_filters(lanc)
            egyben = apply_filters(_proba(), ops).image
            prefix = apply_filters(_proba(), ops[:-1]).image
            ketteva = apply_filters(prefix, ops[-1:]).image
            assert egyben.shape == ketteva.shape, lanc
            elteres = float(np.mean(np.abs(egyben.astype(float) - ketteva.astype(float))))
            assert elteres == 0.0, f"{lanc}: a két út eltér ({elteres:.3f})"
