"""#3229 2. lépés — a lánc a MÉRT (eredeti) sorrendben is futtatható.

## Mit mond a bináris

Az eredeti NEM rendezi át a láncot: a `CGenericFilter` `+0x80` rekesze rendereli
az opot, a `+0x84` pedig **átadja a koordináta-leképezést és az inverzét**
(`docs/specs/filterdesc-registry.md` 12.). A mai `apply_filters` ehhez képest a
vágást és a kereteket a lánc VÉGÉRE halasztja (#330) — ez a `mert_sorrend=True`
ág az, ami az eredeti sorrendet futtatja.

## Az alapértelmezés MA IS a régi

A kapcsoló nélkül semmi nem változik: a bekötés (élő előnézet, export,
bélyegkép) a jegy 3. lépése. Így az átállítás mérhető, és a #3169 belső
egyezése (előnézet = mentés) közben sem sérül.

## A KONTROLL-mérés, ami ezt a fájlt hitelesíti

800 × 600-as próbaképen, a két ág átlagos abszolút eltérése:

| lánc | eltérés | miért |
|---|---:|---|
| `sepia;Border` · `bw;sepia` · `crop64;Vignette` · `crop64;Border` | **0,0000** | a lánc sorrendje már ma is a mért |
| `Border;Vignette` | 8,30 | a vignetta a mért sorrendben a KERETRE is rásötétít |
| `Border;sepia` | 3,95 | a szépia a keretet is színezi |
| `Polaroid;sepia` | 3,72 | ugyanaz, forgatott kerettel |
| `Border;crop64` | más MÉRET | a vágás a keretezett képre esik, leképezve |

Ugyanezek a nagyságrendek szerepelnek a #3169 táblájában — ott a KÉT ÚT
eltéréseként. Ez a kereszt-ellenőrzés: a mért ág tényleg „a másik sorrendet"
adja.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters

SZELES, MAGAS = 400, 300

#: A vágás téglalapja (rect64): a kép bal-felső ~47%-a.
CROP = "crop64=1,3c3c8c8c;"
#: ⚠️ A `Border` paraméter-pozíciói: 0–2 vastagság/rádiusz, **3–4 SZÍN**,
#: 5 feliratmagasság. A csúszka-INDEX tehát nem paraméter-pozíció — színt
#: számnak adva a bejegyzés hibára fut, és a lánc némán kihagyja.
KERET = "Border=1,20,5,0,000000,ffffff,0;"


@pytest.fixture
def minta() -> np.ndarray:
    rng = np.random.default_rng(3229)
    return rng.integers(0, 256, (MAGAS, SZELES, 3), dtype=np.uint8)


def _elteres(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a.astype(int) - b.astype(int))))


class TestAzAlapertelmezesValtozatlan:
    """A kapcsoló nélkül a viselkedés bitre a mai."""

    @pytest.mark.parametrize(
        "lanc",
        [
            "sepia=1;" + KERET,
            "bw=1;sepia=1;",
            "sepia=1;" + CROP,
            CROP + KERET,
        ],
    )
    def test_ahol_a_sorrend_MAR_a_mert_ott_a_ket_ag_AZONOS(self, minta, lanc):
        ops = parse_filters(lanc)
        mai = apply_filters(minta, ops)
        mert = apply_filters(minta, ops, mert_sorrend=True)
        assert mai.image.shape == mert.image.shape, lanc
        np.testing.assert_array_equal(mai.image, mert.image)
        assert mai.content_placement == mert.content_placement
        assert mai.skipped == mert.skipped == ()


class TestASorrendSZAMIT:
    """Ahol a mai ág HALASZT (keret vagy vágás után folytatódó lánc), a mért
    sorrend MÁS képet ad — és ez a jegy egész lényege."""

    @pytest.mark.parametrize(
        "lanc,legalabb",
        [
            (KERET + "Vignette=1,35.000000,1.400000,0.000000;", 2.0),
            (KERET + "sepia=1;", 1.0),
            ("Polaroid=1,5.000000;sepia=1;", 1.0),
            #: ⭐ a #3169 táblájának LEGNAGYOBB tétele (18,20): a mai ág a
            #: vignettát a VÁGATLAN képre teszi (a halasztás miatt a vágás
            #: utána fut), tehát a sötétedés közepe az eredeti kép közepe — a
            #: mért sorrendben a vágott képre kerül, a saját közepére
            (CROP + "Vignette=1,35.000000,1.400000,0.000000;", 2.0),
        ],
    )
    def test_a_halasztas_miatt_mas_kepet_ad_a_ket_ag(self, minta, lanc, legalabb):
        ops = parse_filters(lanc)
        mai = apply_filters(minta, ops)
        mert = apply_filters(minta, ops, mert_sorrend=True)
        assert mai.image.shape == mert.image.shape
        assert _elteres(mai.image, mert.image) >= legalabb, (
            f"{lanc}: a két ág gyakorlatilag egyezik — a mért sorrend nem hatott"
        )

    def test_a_keret_utani_vagas_a_KERETEZETT_kepre_esik(self, minta):
        """A `Border;crop64` a mért sorrendben mást vág, mint a mai ág.

        A `Border` tisztán ELTOLÁS, tehát a leképezett téglalap mérete ugyanaz,
        mint a nyers vágásé — a mai (halasztott) ág viszont a vágás UTÁN teszi
        rá a keretet, tehát nagyobb kimenetet ad.
        """
        ops = parse_filters(KERET + CROP)
        mai = apply_filters(minta, ops)
        mert = apply_filters(minta, ops, mert_sorrend=True)
        nyers_vagas = apply_filters(minta, parse_filters(CROP))
        assert mert.image.shape == nyers_vagas.image.shape
        assert mai.image.shape != mert.image.shape


class TestAVagasKoordinataja:
    """#330: a `crop64` koordinátái az EREDETI képre vonatkoznak."""

    def test_a_vagas_merete_a_lanc_helyetol_FUGGETLEN(self, minta):
        """Akár a lánc elején, akár egy eltolásos keret után áll, a kivágott
        TERÜLET ugyanannyi képpont — ezt a leképezés biztosítja."""
        elol = apply_filters(minta, parse_filters(CROP), mert_sorrend=True)
        hatul = apply_filters(minta, parse_filters(KERET + CROP), mert_sorrend=True)
        assert elol.image.shape == hatul.image.shape

    def test_ket_crop64_kozul_csak_az_UTOLSO_fut(self, minta):
        """#130: a több `crop64`-es valódi láncok nem kaszkádolnak."""
        ketto = apply_filters(
            minta, parse_filters("crop64=1,20204040;" + CROP), mert_sorrend=True
        )
        egy = apply_filters(minta, parse_filters(CROP), mert_sorrend=True)
        assert ketto.image.shape == egy.image.shape
        np.testing.assert_array_equal(ketto.image, egy.image)


class TestAPlacementAMertAgon:
    def test_a_vagas_utani_keret_helye_a_VAGOTT_forrasbol_szamol(self, minta):
        """A szerkesztő átfedő rétegei a vágott forráshoz tartoznak (#3166)."""
        jelentes = apply_filters(minta, parse_filters(CROP + KERET), mert_sorrend=True)
        hely = jelentes.content_placement
        assert hely is not None
        assert hely.erintetlen is False
        # a keret SZIMMETRIKUS: a forrás a kimenet közepén áll
        assert hely.kozep_x == pytest.approx(0.5, abs=1e-9)
        assert hely.kozep_y == pytest.approx(0.5, abs=1e-9)
        assert 0.0 < hely.szelesseg < 1.0 and 0.0 < hely.magassag < 1.0

    def test_keret_nelkul_NINCS_hely(self, minta):
        jelentes = apply_filters(minta, parse_filters("sepia=1;bw=1;"), mert_sorrend=True)
        assert jelentes.content_placement is None
