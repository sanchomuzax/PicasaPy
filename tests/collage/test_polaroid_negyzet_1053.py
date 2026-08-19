"""A polaroid csempe oldalaránya MINDIG 0,8333 — a fotótól függetlenül (#1053).

## A lelet

A keret-arányaink jók (`POLAROID_WIDTH_RATIO / POLAROID_HEIGHT_RATIO =
1,145 / 1,374 = 0,83333`), csak **rossz alapra** alkalmaztuk őket: a fotó
SAJÁT méretére, az eredeti pedig a `scale × scale` **négyzetre hozott**
fotóra. Ezért lett nálunk a csempe alakja képfüggő.

## A bizonyíték (a tulajdonos két eredeti polaroid kollázsa)

`AI.cxf` és `AI2.cxf`, 18 polaroid csomópont, két különböző lapformátum:
**mind** `w/h = 0,833`, négy különböző forrásképpel, és akkor is, ha a
`scale` eltér (295,4 vs 337).

A kontroll ugyanezekre a képekre, keret NÉLKÜL (`AI1.cxf`): ott a csempe
**követi a kép arányát** — a `7a816215` kép 0,560-at ad. Ugyanaz a kép
polaroiddal 0,833. A különbség tehát a KERETHEZ tartozik.

Hogy a fotó KÖRBEVÁGÁSSAL kerül a négyzetbe (nem illesztéssel), két
független úton dőlt el: algebrailag (ha a külső arány és a keret-arányok
hányadosa is 0,8333, akkor `fw/fh = 1,000`), és a golden JPEG legfelső,
takaratlan csempéjének képpontjaiból — a fotón belül **nincs papír**, ami
0,80 és 0,56 arányú forrásnál illesztésnél látszana.

## Miért nem kozmetikai

Más alakú csempék más helyre esnek. A mi polaroid Képkupacunk ezért lógott
ki már 9 képnél is, miközben az eredeti ugyanott egyet sem — a #1045
beszorítása ezt a tünetet takarta el, nem az okát.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.collage.frames import (
    POLAROID_HEIGHT_RATIO,
    POLAROID_WIDTH_RATIO,
)
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    layout_nodes_for_aspects,
)
from picasapy.collage.themes import PICTUREPILE

#: A mért érték a golden fájlokban: 0,83313 és 0,83328 — a képlet 0,83333.
POLAROID_ARANY = POLAROID_WIDTH_RATIO / POLAROID_HEIGHT_RATIO

#: A kerekítés miatti tűrés. A csempe egész képpont, tehát kis csempénél a
#: kerekítés önmagában is elmozdítja az arányt.
TURES = 0.005

#: Szándékosan SZÉLSŐSÉGES keverék: álló panorámától fekvőig. Pont az a
#: lényeg, hogy a csempe alakja EGYIKTŐL SEM függjön.
ARANYOK = (0.56, 0.80, 1.00, 1.78, 0.75, 1.33, 0.56, 0.80, 1.00)


def _csomopontok(keret: str, aranyok=ARANYOK, szelesseg=1600, magassag=1200):
    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE, width=szelesseg, height=magassag, border=keret, seed=7
    )
    utak = [Path(f"/nincs/k{i}.jpg") for i in range(len(aranyok))]
    return layout_nodes_for_aspects(list(aranyok), utak, beallitas)


class TestAPolaroidCsempeAlakja:
    """⚠️ Ez a jegy lelete: 18 golden csomópont mind 0,833-at ad."""

    @pytest.mark.parametrize("index", range(len(ARANYOK)))
    def test_minden_csempe_ugyanazt_az_aranyt_adja(self, index):
        csomopont = _csomopontok("polaroid")[index]

        arany = csomopont.width / csomopont.height

        assert arany == pytest.approx(POLAROID_ARANY, abs=TURES), (
            f"a {ARANYOK[index]} arányú kép csempéje {arany:.4f} — a "
            f"polaroid csempe az eredetiben MINDIG {POLAROID_ARANY:.4f}"
        )

    @pytest.mark.parametrize("index", range(len(ARANYOK)))
    def test_nagy_lapon_az_elteres_a_KEREKITESRE_szorul(self, index):
        """⚠️ A `TURES` nem lazaság, hanem a KEREKÍTÉS padlója.

        A csempe egész képpont, és az illesztő a Picasa 0,499-es
        ráhagyásával kerekít — egy 412 képpontos csempénél ez önmagában
        0,0017-et mozdít az arányon. Ha a lapot nagyobbra vesszük, a
        kerekítés súlya lecsökken, és az aránynak a jegy szigorú
        ±0,001-ébe kell esnie. Ez különbözteti meg a KÉPLET hibáját a
        kerekítésétől: ha a képlet volna rossz, a nagy lap sem segítene."""
        csomopont = _csomopontok("polaroid", szelesseg=9600, magassag=7200)[index]

        arany = csomopont.width / csomopont.height

        assert arany == pytest.approx(POLAROID_ARANY, abs=0.001)

    def test_a_1_145_es_az_1_374_hanyadosa_adja(self):
        """A keret-arányaink JÓK — a jegy nem róluk szól. Ha valaki ezeket
        igazítaná a 0,8333-hoz, rossz helyen javítana."""
        assert POLAROID_WIDTH_RATIO / POLAROID_HEIGHT_RATIO == pytest.approx(
            0.83333, abs=1e-4
        )


class TestAKontroll:
    """A keret nélküli és a fehér szegélyes csempe VÁLTOZATLAN.

    A golden `AI1.cxf` (noborder) ugyanazokra a képekre a kép arányát
    hozza — 0,560 és 0,800 EGY kollázsban. Ha ez itt elmozdulna, azt
    rontanánk el, ami ma bizonyítottan jó."""

    @pytest.mark.parametrize("index", range(len(ARANYOK)))
    def test_a_noborder_csempe_a_kep_aranyat_koveti(self, index):
        csomopont = _csomopontok("noborder")[index]

        arany = csomopont.width / csomopont.height

        assert arany == pytest.approx(ARANYOK[index], abs=0.01)

    def test_a_whiteborder_tobbfele_alakot_ad(self):
        aranyok = {
            round(cs.width / cs.height, 2) for cs in _csomopontok("whiteborder")
        }

        assert len(aranyok) > 1, (
            "a fehér szegélyes csempe alakja a képtől függ — ha egyformává "
            "vált, a polaroid-szabály átszivárgott oda is"
        )


class TestAKilogasValodiProbaja:
    """A jegy igazi mércéje: a helyes csempeméret mellett a 9 képes polaroid
    kupacnak a BESZORÍTÁS NÉLKÜL is a lapon kell maradnia.

    A #1045 beszorítása a tünetet vágta le; ha az ok megszűnik, a
    beszorításnak nem marad dolga. Ezt úgy állítjuk, hogy a csomópont
    középpontja megegyezik a `pile_layout` NYERS középpontjával."""

    def _beszoritottak(self, keret, aranyok=ARANYOK) -> int:
        from picasapy.collage.fitting import MsvcRandom
        from picasapy.collage.nodes import pixels_to_sheet
        from picasapy.collage.pile import pile_layout

        beallitas = PicasaCollageSettings(
            theme=PICTUREPILE, width=1600, height=1200, border=keret, seed=7
        )
        nyers = pile_layout(
            len(aranyok), beallitas.width, beallitas.height,
            MsvcRandom(beallitas.seed),
        )
        csomopontok = _csomopontok(keret, aranyok)
        return sum(
            1
            for cs, hely in zip(csomopontok, nyers, strict=True)
            if abs(cs.center_x - pixels_to_sheet(hely.center_x, beallitas.width)) > 0.01
            or abs(cs.center_y - pixels_to_sheet(hely.center_y, beallitas.width)) > 0.01
        )

    @pytest.mark.parametrize(
        "aranyok",
        [ARANYOK, (0.80, 0.75) * 4 + (0.80,)],
        ids=["vegyes", "csak-allo"],
    )
    def test_a_polaroid_nem_log_ki_jobban_a_keret_nelkulinel(self, aranyok):
        """⚠️ Ez a jegy VALÓDI mércéje, és szándékosan NEM „nulla".

        A maradék beszorítás a `scatter_centers` sávjának a baja (#1045): a
        sáv a LEGKISEBB csempe szorzójával szűkül, a margót viszont a
        LEGNAGYOBB igényli — ez keret nélkül is előjön, csupa álló képnél
        1/9. Ha itt „nullát" követelnénk, egy MÁSIK jegy hibáját tennénk
        ennek a feltételévé.

        Amit ez a jegy állíthat: a polaroid csempe alakja többé nem tesz
        rosszabbat a keret nélkülinél. A javítás előtt a vegyes készleten
        3 csempét mozdított a beszorítás, keret nélkül nullát."""
        polaroid = self._beszoritottak("polaroid", aranyok)
        keret_nelkul = self._beszoritottak("noborder", aranyok)

        assert polaroid <= keret_nelkul + 1, (
            f"polaroiddal {polaroid} csempét szorít be a védelem, keret "
            f"nélkül {keret_nelkul} — a csempe alakja még mindig eltér"
        )

    def test_a_javitas_elotti_harom_helyett_legfeljebb_egy(self):
        """A javítás előtti mért állapot: a vegyes készleten HÁROM csempét
        mozdított a beszorítás. Ez az őr azt fogja meg, ha visszacsúsznánk."""
        assert self._beszoritottak("polaroid") <= 1
