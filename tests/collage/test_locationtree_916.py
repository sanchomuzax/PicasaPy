"""#916: a Képkockamozaik kényszeres pakolója (`CLocationTree`).

A `framegrid` pakolója az eredetiben a **`CLocationTree`** — nem a Mozaik
alap pakolója. A hangsúlyos („képkockaközéppont") kép téglalapját a téma
pakolója SZÁMOLJA, és a fa azt **változatlanul átveszi**; a többi kép a
maradék területre kerül.

A számok MÉRVE vannak, nem illesztve:

| honnan | mi |
|---|---|
| `0x00829d8c` (a téma gyártója) | `[téma+0x58] = 0,5` (`0xc7dafc`) — a hangsúlyos kép MÉRETE |
| `0x00889185`–`0x00889241` | a téglalap képlete: a lap közepére, a kép oldalarányával |
| `0x0083d556`–`0x0083d59d` | a gomb CSAK a kép azonosítóját tárolja (`+0x54`), téglalapot NEM |
| `0x008906e0` | kényszeres kép nélkül az eredeti is az ALAP pakolóra esik vissza |
| `0x00897b1c` | a kényszeres levél a téglalapot átveszi, és NEM darabol tovább |

⚠️ Amit ez az őr NEM mér: a látványt. Hogy a maradék képek „szépen"
rendeződnek a hangsúlyos kép körül, gépi teszt nem mondja ki — csak azt,
hogy nem fedik, és hogy a hangsúlyos kép a mért helyén van.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from picasapy.collage import location_tree as lt
from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.nodes import SHEET_UNITS
from picasapy.collage.packing import pack
from picasapy.collage.picasa_render import (
    FRAMEGRID,
    PicasaCollageSettings,
    layout_nodes_for_aspects,
)

#: az egykori közelítés, amit ez a jegy kivezetett
KOZELITES = (0.25, 0.25, 0.75, 0.75)


def _ora(tickek):
    """Determinisztikus óra: a keresés pontosan annyi kört fut, amennyit adunk."""
    sorozat = iter(tickek)

    def ora() -> float:
        try:
            return next(sorozat)
        except StopIteration:  # pragma: no cover — a teszt elég tickkel hív
            return 1e9

    return ora


class TestAHangsulyosKepTeglalapja:
    def test_a_lap_KOZEPERE_kerul(self):
        r = lt.frame_center_rect(1.5, 1.5)
        assert (r.x0 + r.x1) / 2 == pytest.approx(0.5)
        assert (r.y0 + r.y1) / 2 == pytest.approx(0.5)

    def test_fekvo_kepnel_a_SZELESSEG_a_lap_fele(self):
        """`[téma+0x58] = 0,5` — fekvő képnél a szélességre hat."""
        r = lt.frame_center_rect(2.0, 1.4)
        assert r.width == pytest.approx(0.5)

    def test_allo_kepnel_a_MAGASSAG_a_lap_fele(self):
        r = lt.frame_center_rect(0.75, 1.4)
        assert r.height == pytest.approx(0.5)

    @pytest.mark.parametrize("arany", [0.5, 0.75, 1.0, 1.3333, 2.0, 3.0])
    @pytest.mark.parametrize("lap", [1.3333, 1.0, 0.75])
    def test_a_teglalap_KEPPONTBAN_a_kep_aranyat_tartja(self, arany, lap):
        """A hangsúlyos kép nem torzul: a cella képpontban a kép aránya."""
        r = lt.frame_center_rect(arany, lap)
        assert (r.width * lap) / r.height == pytest.approx(arany, rel=1e-6)

    def test_a_KOZELITES_csak_az_egyezo_arany_hatareset(self):
        """A régi `(0,25 … 0,75)` akkor helyes, ha a kép aránya = a lapé."""
        r = lt.frame_center_rect(1.5, 1.5)
        assert (r.x0, r.y0, r.x1, r.y1) == pytest.approx(KOZELITES)

    def test_es_MASHOL_a_kozelites_HIBAS(self):
        """Ez az eset bukott meg a kivezetett közelítéssel."""
        r = lt.frame_center_rect(3.0, 1.3333)
        assert (r.x0, r.y0, r.x1, r.y1) != pytest.approx(KOZELITES)
        assert r.height == pytest.approx(0.5 * 1.3333 / 3.0, rel=1e-6)

    def test_a_lapon_TULNYULO_teglalap_levagodik(self):
        """A `[0,1]²`-en kívüli cella nálunk értelmezhetetlen — levágjuk."""
        r = lt.frame_center_rect(1.0, 4.0)
        assert 0.0 <= r.y0 < r.y1 <= 1.0

    @pytest.mark.parametrize("arany,lap", [(0.0, 1.5), (1.5, 0.0), (-1.0, 1.0)])
    def test_ervenytelen_aranyt_elutasit(self, arany, lap):
        with pytest.raises(ValueError):
            lt.frame_center_rect(arany, lap)


class TestAPakolas:
    def test_kenyszeres_kep_NELKUL_az_alap_pakolo_fut(self):
        """`0x008906e0`: kényszer nélkül a `CLocationTree` visszaesik."""
        aranyok = [1.5, 0.8, 1.2, 1.0]
        alap = pack(aranyok, 1.3333, MsvcRandom(7), time_limit=0.0)
        mienk = lt.pack_with_center(
            aranyok, 1.3333, MsvcRandom(7), center=None, time_limit=0.0
        )
        assert mienk == alap

    def test_a_hangsulyos_kep_a_MERT_helyere_kerul(self):
        aranyok = [1.5, 0.8, 3.0, 1.0]
        cellak = lt.pack_with_center(
            aranyok, 1.3333, MsvcRandom(3), center=2, time_limit=0.0
        )
        assert cellak[2] == lt.frame_center_rect(3.0, 1.3333)

    def test_a_tobbi_kep_NEM_fedi_a_hangsulyosat(self):
        aranyok = [1.5, 0.8, 1.2, 1.0, 0.6, 2.2]
        cellak = lt.pack_with_center(
            aranyok, 1.3333, MsvcRandom(11), center=0, time_limit=0.0
        )
        kozep = cellak[0]
        for cella in cellak[1:]:
            atfed = (
                min(cella.x1, kozep.x1) - max(cella.x0, kozep.x0) > 1e-9
                and min(cella.y1, kozep.y1) - max(cella.y0, kozep.y0) > 1e-9
            )
            assert not atfed

    def test_minden_kep_kap_cellat(self):
        aranyok = [1.5, 0.8, 1.2, 1.0, 0.6]
        cellak = lt.pack_with_center(
            aranyok, 1.3333, MsvcRandom(5), center=1, time_limit=0.0
        )
        assert len(cellak) == len(aranyok)

    def test_EGYETLEN_kep_a_teljes_lapot_kapja(self):
        """Nincs mit köré pakolni — a kényszer ilyenkor nem szűkít."""
        cellak = lt.pack_with_center([1.5], 1.5, MsvcRandom(1), center=0)
        assert (cellak[0].x0, cellak[0].y0) == (0.0, 0.0)
        assert (cellak[0].x1, cellak[0].y1) == (1.0, 1.0)

    def test_a_kereses_IDOKORLATOS_es_a_kiindulot_nem_rontja(self):
        """Az óra lejárta után nem indul új kör (`0x00890c57`)."""
        aranyok = [1.5, 0.8, 1.2, 1.0, 0.6]
        egy_kor = lt.pack_with_center(
            aranyok, 1.3333, MsvcRandom(9), center=0, time_limit=0.0
        )
        sok_kor = lt.pack_with_center(
            aranyok,
            1.3333,
            MsvcRandom(9),
            center=0,
            time_limit=1.0,
            clock=_ora([0.0, 0.1, 0.2, 0.3, 2.0]),
        )
        assert lt.wasted_area(sok_kor, aranyok, 1.3333) <= lt.wasted_area(
            egy_kor, aranyok, 1.3333
        )

    def test_az_ervenytelen_kozepindex_nem_kenyszer(self):
        aranyok = [1.5, 0.8]
        assert lt.pack_with_center(
            aranyok, 1.3333, MsvcRandom(2), center=7, time_limit=0.0
        ) == pack(aranyok, 1.3333, MsvcRandom(2), time_limit=0.0)


class TestARajzoloBekotese:
    def test_a_framegrid_a_MERT_teglalapot_hasznalja(self):
        """A rajzoló csomópontja lapegységben — de a HELY ugyanaz a mérés."""
        aranyok = (1.5, 0.8, 3.0)
        utak = tuple(Path(f"/k/{i}.jpg") for i in range(3))
        beall = PicasaCollageSettings(theme=FRAMEGRID, frame_center=2, seed=4)
        nodes = layout_nodes_for_aspects(aranyok, utak, beall)
        hangsulyos = [n for n in nodes if n.path == utak[2]]
        assert len(hangsulyos) == 1
        csomo = hangsulyos[0]
        lap = beall.width / beall.height
        mert = lt.frame_center_rect(3.0, lap)
        egyseg = SHEET_UNITS / beall.width
        assert csomo.center_x == pytest.approx(0.5 * beall.width * egyseg, abs=1.0)
        assert csomo.center_y == pytest.approx(0.5 * beall.height * egyseg, abs=1.0)
        assert csomo.width == pytest.approx(
            mert.width * beall.width * egyseg, abs=1.0
        )
        #: a hangsúlyos kép NEM torzul: a csomópont doboza a kép aránya.
        #: A tűrés a CELLA egész képpontra kerekítéséből jön (266,7 → 266),
        #: nem a képletből — 1600×1200-as lapon ez negyed százalék.
        assert csomo.width / csomo.height == pytest.approx(3.0, rel=1e-2)

    def test_a_KOZELITES_mar_nem_letezik_a_forrasban(self):
        """A jegy kimondott feltétele: a `_FRAMEGRID_CENTER` kivezetve."""
        forras = Path(
            __import__("picasapy.collage.picasa_render", fromlist=["x"]).__file__
        ).read_text(encoding="utf-8")
        assert "_FRAMEGRID_CENTER" not in forras
        assert "tudatos közelítés" not in forras
