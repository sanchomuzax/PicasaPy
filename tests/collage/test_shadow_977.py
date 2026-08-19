"""A kollázs VETETT ÁRNYÉKA — a négy témánkénti paraméterkészlet (#977).

Spec: `docs/specs/picasa-kollazs-felulet.md` **9/b**.

A jegy előtti állapot: az „Árnyékok rajzolása" jelölőnégyzet bekapcsolható
volt, az érték a `.cxf`-be is bekerült — **rajzolás viszont sehol nem
történt**. A felhasználó élesben jelezte: „nem látszik a vetett árnyék".

## Amit ez a lap őriz

A jegy legkönnyebben elrontható állítása, hogy **NÉGY külön
paraméterkészlet van, nem egy közös**. Aki egyetlen átlátszatlansággal írja
meg, négy témából kettőt elront — és ez **zöld teszt mellett is néma hiba**,
mert a különbség csak a képen látszik.

| téma | eltolás x | eltolás y | elmosás | átlátszatlanság | alfa |
|---|---|---|---|---|---|
| Képkupac | `0,001·A·W + 1` | `0,0015·A·W + 1` | `0,01·A·W` | 0,4 | **102** |
| Mozaik, Képkockamozaik | `0,0017·W + 1` | `0,0025·W + 1` | `0,008·W` | 0,4 | **102** |
| Rács, Indexkép | `0,001·k + 1` | `0,002·k + 2` | `0,03·k` | **0,6** | **153** |
| Többszörös exponálás | — | — | — | **nincs árnyék** | — |

Ezért a lap három rétegben mér:

1. **paraméter** — a tizenkét konstans, az alfa, a `k` levezetése, a
   8-képpontos érvényességi kapu;
2. **kimenet** — hogy a mentett képen az árnyék TÉNYLEG ott van, ahova a
   képlet mutatja (jobbra-le), és hogy a Rács/Indexkép árnyéka **sötétebb**,
   mint a Képkupacé/Mozaiké — ez az az állítás, ami egyetlen közös
   készlettel megbukna;
3. **golden** — a felhasználó nyolc eredeti Picasa-kollázsán mért értékek
   (privát repó, `referencia/kollazs-golden/`) tűréssel visszaolvasva.

⚠️ **Beégetett SHA/MD5 SEHOL** (#942 tanulsága): a kivonat a platformot is
szerződésbe foglalná, és a Windows-lábon némán bukna. Minden állítás
tűréssel mér.
"""

from __future__ import annotations

import math
from dataclasses import replace

import cv2
import numpy as np
import pytest

from picasapy.collage.nodes import CollageNode
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    make_picasa_collage,
    render_nodes,
)
from picasapy.collage.shadow import (
    ALPHA_SCALE,
    BOUNDS_GROWTH_FACTOR,
    CONTACT_USABLE_HEIGHT,
    CONTACT_USABLE_WIDTH,
    MIN_CELL_EDGE_PIXELS,
    RASTER_RADIUS_FACTOR,
    SHADOW_RECIPES,
    CellEdgeTooSmall,
    ShadowParams,
    cell_edge,
    draw_shadow,
    pile_scale,
    shadow_params,
)
from picasapy.collage.themes import (
    COLLAGE_THEMES,
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
    capabilities_for,
)

# --- Segédek ----------------------------------------------------------------


def _feher_kepek(mappa, darab, oldal=48):
    """FEHÉR próbaképek: a fehér lapon csak az árnyék lesz nem-fehér.

    Ez a mérés kulcsa — így a legsötétebb képpont MINDIG az árnyék, és nem
    kell a fotó tartalmát a háttértől elválasztani (a golden-mérés éppen
    ezen bukott el először: a fénykép széle maga is sötét)."""
    utak = []
    for i in range(darab):
        kep = np.full((oldal, oldal + 4 * i, 3), 255, dtype=np.uint8)
        ut = mappa / f"feher{i}.png"
        assert cv2.imwrite(str(ut), kep)
        utak.append(ut)
    return utak


def _feher_lap(szelesseg, magassag):
    return np.full((magassag, szelesseg, 3), 255, dtype=np.uint8)


def _legsotetebb(kep):
    """A kép legsötétebb csatorna-értéke (fehér lapon = a legerősebb árnyék)."""
    return int(kep.min())


# --- 1. A NÉGY paraméterkészlet — nem egy közös -----------------------------


class TestNegyKulonKeszlet:
    """A jegy magja: négy készlet, két különböző átlátszatlansággal."""

    @pytest.mark.parametrize(
        ("tema", "vart_alfa"),
        [
            (PICTUREPILE, 102),
            (PICTUREGRID, 102),
            (FRAMEGRID, 102),
            (REGULARGRID, 153),
            (CONTACTSHEET, 153),
        ],
    )
    def test_az_alfa_temankent_102_vagy_153(self, tema, vart_alfa):
        """`alfa = egész(átlátszatlanság · 256)` — 0,4 → 102, 0,6 → 153."""
        p = shadow_params(tema, page_width=2048, page_height=1536, count=6)
        assert p is not None
        assert p.alpha == vart_alfa

    def test_a_ket_alfa_tenyleg_ketto(self):
        """Ha valaki egyetlen közös készletet ír, ez az állítás bukik."""
        alfak = {
            shadow_params(t, page_width=2048, page_height=1536, count=6).alpha
            for t in (PICTUREPILE, PICTUREGRID, FRAMEGRID, REGULARGRID, CONTACTSHEET)
        }
        assert alfak == {102, 153}

    def test_a_recept_tabla_egyetlen_helyen_el(self):
        """Mind a hat témára VAN bejegyzés — néma kihagyás nincs.

        A táblában a Mozaik és a Képkockamozaik UGYANAZT a receptet kapja
        (egy hívó, két vtable), ugyanígy a Rács és az Indexkép — ez a
        négy készlet a hat témára."""
        assert set(SHADOW_RECIPES) == set(COLLAGE_THEMES)
        assert SHADOW_RECIPES[PICTUREGRID] is SHADOW_RECIPES[FRAMEGRID]
        assert SHADOW_RECIPES[REGULARGRID] is SHADOW_RECIPES[CONTACTSHEET]
        kulonbozo = {r for r in SHADOW_RECIPES.values() if r is not None}
        assert len(kulonbozo) == 3, "három recept az öt árnyékos témára"

    @pytest.mark.parametrize("tema", sorted(set(COLLAGE_THEMES) - {MULTIEXP}))
    def test_az_eltolas_pozitiv_es_y_nagyobb_mint_x(self, tema):
        """Az árnyék jobbra-LE csúszik, és a függőleges eltolás a nagyobb."""
        p = shadow_params(tema, page_width=2048, page_height=1536, count=6)
        assert p.offset_x > 0.0
        assert p.offset_y > p.offset_x

    def test_a_ket_racsos_kulonbozo_eltolas_aranyt_ad(self):
        """Az eltolás aránya sem közös: 1:1,5 / 1:1,47 / 1:2.

        Ha egyetlen készlet volna, a három arány egybeesne."""
        aranyok = []
        for tema in (PICTUREPILE, PICTUREGRID, REGULARGRID):
            p = shadow_params(tema, page_width=4096, page_height=3072, count=9)
            aranyok.append(p.offset_y / p.offset_x)
        assert len({round(a, 2) for a in aranyok}) == 3


# --- 2. A tizenkét konstans ------------------------------------------------


class TestKepletek:
    """A képletek pontos alakja — az `+1,0` additív taggal EGYÜTT."""

    def test_a_mozaik_keplete_a_lap_szelessegebol(self):
        """`W` = a LAP szélessége (a golden `AI4` ezt dönti el)."""
        p = shadow_params(PICTUREGRID, page_width=5120, page_height=3840, count=9)
        assert p.offset_x == pytest.approx(0.0017 * 5120 + 1.0)
        assert p.offset_y == pytest.approx(0.0025 * 5120 + 1.0)
        assert p.blur == pytest.approx(0.008 * 5120)

    def test_az_additiv_tag_megvan(self):
        """A `+1,0` (Rácsnál `+2,0`) NEM hagyható el.

        Nélküle a Mozaik eltolása 8,70/12,80 volna a mért 10,0/14,5 helyett
        — a golden-mérés külön kimondja, hogy a tag nélkül távolabb esne."""
        mozaik = shadow_params(PICTUREGRID, page_width=5120, page_height=3840, count=9)
        assert mozaik.offset_x - 0.0017 * 5120 == pytest.approx(1.0)
        assert mozaik.offset_y - 0.0025 * 5120 == pytest.approx(1.0)

        racs = shadow_params(REGULARGRID, page_width=5120, page_height=3840, count=9)
        k = cell_edge(5120, 3840, 9)
        assert racs.offset_x - 0.001 * k == pytest.approx(1.0)
        assert racs.offset_y - 0.002 * k == pytest.approx(2.0)

    def test_a_kepkupac_leptek_a_darabszambol_jon(self):
        """`A = min(1, 1/sqrt(sqrt(n) − 1))` — a 9.0 darabszám-görbéje."""
        assert pile_scale(0) == 1.0
        assert pile_scale(1) == 1.0
        # n ≤ 4-nél a képlet 1,0 fölé menne — a `min` levágja
        assert pile_scale(2) == 1.0
        assert pile_scale(4) == 1.0
        assert pile_scale(9) == pytest.approx(1.0 / math.sqrt(2.0))
        assert pile_scale(100) == pytest.approx(1.0 / 3.0)
        # monoton csökkenő a felső szakaszon
        assert pile_scale(200) < pile_scale(100) < pile_scale(9)

    def test_a_kepkupac_keplete_a_lepteket_hasznalja(self):
        p = shadow_params(PICTUREPILE, page_width=5120, page_height=5120, count=9)
        alap = pile_scale(9) * 5120
        assert p.offset_x == pytest.approx(0.001 * alap + 1.0)
        assert p.offset_y == pytest.approx(0.0015 * alap + 1.0)
        assert p.blur == pytest.approx(0.01 * alap)

    def test_a_kepkupac_arnyeka_a_kepmerettel_egyutt_zsugorodik(self):
        """Több kép → kisebb kép → kisebb árnyék. Ez az `A` létjogosultsága."""
        keves = shadow_params(PICTUREPILE, page_width=4096, page_height=4096, count=9)
        sok = shadow_params(PICTUREPILE, page_width=4096, page_height=4096, count=100)
        assert sok.blur < keves.blur
        assert sok.offset_y < keves.offset_y

    def test_a_kozos_szarmaztatott_ertekek(self):
        """`sugár = elmosás·8`, `alfa = egész(átl.·256)`, `bővítés = elmosás·1,5`."""
        p = ShadowParams(offset_x=3.0, offset_y=5.0, blur=40.0, opacity=0.4)
        assert p.raster_radius == pytest.approx(40.0 * RASTER_RADIUS_FACTOR)
        assert p.alpha == int(0.4 * ALPHA_SCALE)
        assert p.bounds_growth == pytest.approx(40.0 * BOUNDS_GROWTH_FACTOR)


# --- 3. A `k` cellaél levezetése -------------------------------------------


class TestCellaEl:
    """`k` = egy kép cellájának élhossza (spec 9/b.3)."""

    def test_a_hasznos_terulet_088_es_079(self):
        """A 0,88/0,79 a bemenet — a maradék 21 % az Indexkép fejlécéé."""
        assert CONTACT_USABLE_WIDTH == 0.88
        assert CONTACT_USABLE_HEIGHT == 0.79

    def test_a_golden_indexkep_cellaele(self):
        """A golden `AI6` (contactsheet, 3841×5120, 9 kép) → `k` = 1126.

        Innen `elmosás = 0,03·1126 = 33,8`; a képen MÉRT sugár 34,5."""
        assert cell_edge(3841, 5120, 9) == 1126
        p = shadow_params(CONTACTSHEET, page_width=3841, page_height=5120, count=9)
        assert p.blur == pytest.approx(33.78, abs=0.1)

    @pytest.mark.parametrize(
        ("darab", "vart_oszlop_sor_szorzat_legalabb"), [(3, 3), (9, 9), (24, 24)]
    )
    def test_a_csokkento_ciklus_elfer_minden_kepnek(
        self, darab, vart_oszlop_sor_szorzat_legalabb
    ):
        """A ciklus addig csökkenti `k`-t, amíg `oszlopok·sorok ≥ n`.

        Legalább három darabszámra ellenőrizve (a jegy „Kész, ha" pontja)."""
        rect_w, rect_h = 3841, 5120
        k = cell_edge(rect_w, rect_h, darab)
        hasznos_w = int(rect_w * CONTACT_USABLE_WIDTH)
        hasznos_h = int(rect_h * CONTACT_USABLE_HEIGHT)
        oszlopok = hasznos_w // k
        sorok = hasznos_h // k
        assert oszlopok * sorok >= vart_oszlop_sor_szorzat_legalabb
        # és `k+1`-gyel MÁR nem férne el — a ciklus nem lép túl a célon
        if k + 1 <= min(hasznos_w, hasznos_h):
            assert (hasznos_w // (k + 1)) * (hasznos_h // (k + 1)) < darab

    def test_tobb_kep_kisebb_cella(self):
        assert cell_edge(3841, 5120, 100) < cell_edge(3841, 5120, 9)

    def test_a_nyolc_keppontos_kapu_hibat_jelez(self):
        """A kapu alatt a rajzolás HIBÁT jelez, nem rajzol torzat.

        Az eredeti `−1`-gyel tér vissza (`0x008881ca`, `0x008881f1`); nálunk
        ez beszédes kivétel — a néma, torz rajz a rosszabb."""
        with pytest.raises(CellEdgeTooSmall):
            cell_edge(40, 40, 400)

    def test_a_kapu_hatara_nyolc_keppont(self):
        assert MIN_CELL_EDGE_PIXELS == 8

    @pytest.mark.parametrize("rossz", [(0, 100, 4), (100, 0, 4), (100, 100, 0)])
    def test_az_ervenytelen_bemenet_hangosan_szol(self, rossz):
        with pytest.raises(ValueError):
            cell_edge(*rossz)


# --- 4. A Többszörös exponálásnak NINCS árnyéka ----------------------------


class TestTobbszorosExponalas:
    """A tiltás a képesség-maszk 11. bitjéből jön, nem témanév-hasonlításból."""

    def test_a_maszk_dontii_el_kinek_van_arnyeka(self):
        """A `shadow_params` PONTOSAN azokra ad `None`-t, akiknek a 11. bitje 0.

        Így a tiltás forrása egyetlen helyen (a maszk) marad — a golden
        `AI7.cxf`-ben `shadows="0"`, a felhasználó be sem tudta kapcsolni."""
        for tema in COLLAGE_THEMES:
            van = shadow_params(tema, page_width=2048, page_height=1536, count=4)
            assert (van is not None) == capabilities_for(tema).shadow, tema

    def test_a_multiexp_recepje_ures(self):
        assert SHADOW_RECIPES[MULTIEXP] is None
        assert capabilities_for(MULTIEXP).shadow is False

    def test_a_multiexp_kimenete_nem_valtozik_a_jelolotol(self, tmp_path):
        """A jelölő bekapcsolása a Többszörös exponálás képén NEM látszik."""
        forrasok = _feher_kepek(tmp_path, 3)
        alap = {"theme": MULTIEXP, "width": 320, "height": 240}
        be = make_picasa_collage(forrasok, PicasaCollageSettings(**alap, shadow=True))
        ki = make_picasa_collage(forrasok, PicasaCollageSettings(**alap, shadow=False))
        assert np.array_equal(be.image, ki.image)


# --- 5. A KIMENET: az árnyék tényleg ott van --------------------------------


def _csempe_csomopont(ut):
    """Egy 300 lapegység oldalú csempe a lap közepén."""
    return CollageNode(
        path=ut,
        center_x=512.0,
        center_y=384.0,
        width=300.0,
        height=300.0,
        fill=True,
    )


class TestKimenet:
    """A mérce: a MENTETT képen legyen árnyék, a helyes irányban."""

    def test_a_bekapcsolt_arnyek_meg_is_jelenik(self, tmp_path):
        """A jegy lényege: bekapcsolva LÁTSZIK, kikapcsolva nem.

        A javítás előtt mindkét kép fehér volt — ez az az eset, amit a
        felhasználó élesben jelzett."""
        ut = _feher_kepek(tmp_path, 1)[0]
        beallitas = PicasaCollageSettings(
            theme=PICTUREGRID, width=1200, height=900, background=(255, 255, 255)
        )
        arnyekkal = render_nodes(
            [_csempe_csomopont(ut)],
            replace(beallitas, shadow=True),
        ).image
        arnyek_nelkul = render_nodes(
            [_csempe_csomopont(ut)],
            replace(beallitas, shadow=False),
        ).image
        assert _legsotetebb(arnyek_nelkul) == 255, "árnyék nélkül a lap tiszta fehér"
        assert _legsotetebb(arnyekkal) < 250, "bekapcsolva LÁTSZANIA kell"

    def test_az_arnyek_jobbra_le_esik(self, tmp_path):
        """Az eltolás iránya: jobbra-le, és FÜGGŐLEGESEN nagyobb.

        A mérés a csempe négy oldalán kívüli sáv „tintáját" (255 − érték)
        összegzi — tűréssel, kivonat nélkül."""
        ut = _feher_kepek(tmp_path, 1)[0]
        beallitas = PicasaCollageSettings(
            theme=PICTUREGRID,
            width=1200,
            height=900,
            background=(255, 255, 255),
            shadow=True,
        )
        kep = render_nodes([_csempe_csomopont(ut)], beallitas).image.astype(np.int32)
        tinta = 255 - kep[:, :, 0]

        # a csempe a lap közepén: 300 lapegység = 351 képpont oldal
        oldal = round(300.0 * 1200 / 1024)
        kozep_x = round(512.0 * 1200 / 1024)
        kozep_y = round(384.0 * 1200 / 1024)
        bal, jobb = kozep_x - oldal // 2, kozep_x + oldal // 2
        fent, lent = kozep_y - oldal // 2, kozep_y + oldal // 2

        balra = int(tinta[fent:lent, :bal].sum())
        jobbra = int(tinta[fent:lent, jobb:].sum())
        felette = int(tinta[:fent, bal:jobb].sum())
        alatta = int(tinta[lent:, bal:jobb].sum())

        assert jobbra > balra, "az árnyék JOBBRA csúszik"
        assert alatta > felette, "az árnyék LEFELÉ csúszik"
        assert alatta > jobbra, "a függőleges eltolás a nagyobb"

    def test_a_racsos_temak_arnyeka_sotetebb(self, tmp_path):
        """A Rács (alfa 153) sötétebb árnyékot ad, mint a Mozaik (alfa 102).

        **Ez az az állítás, amit egyetlen közös készlet nem tud teljesíteni**
        — és amit a képen kívül semmi nem mutat meg."""
        forrasok = _feher_kepek(tmp_path, 4)
        kozos = {
            "width": 1200,
            "height": 900,
            "background": (255, 255, 255),
            "spacing": 0.3,
            "shadow": True,
            "seed": 4242,
        }
        mozaik = make_picasa_collage(
            forrasok, PicasaCollageSettings(theme=PICTUREGRID, **kozos)
        ).image
        racs = make_picasa_collage(
            forrasok, PicasaCollageSettings(theme=REGULARGRID, **kozos)
        ).image
        assert _legsotetebb(mozaik) < 255 and _legsotetebb(racs) < 255
        assert _legsotetebb(racs) < _legsotetebb(mozaik) - 5, (
            "a 60 %-os árnyék érzékelhetően sötétebb a 40 %-osnál "
            f"(Rács {_legsotetebb(racs)} vs. Mozaik {_legsotetebb(mozaik)})"
        )

    def test_a_befoglalo_bovites_nelkul_levagodna_az_arnyek(self, tmp_path):
        """A befoglaló `elmosás × 1,5`-tel bővül MINDEN élen.

        A mérés: az árnyék a csempe jobb szélén TÚL is folytatódik, legalább
        `elmosás` képpontnyira. Aki csak a csempe dobozába rajzol, itt
        bukik — az árnyék éles vonalban levágódna."""
        ut = _feher_kepek(tmp_path, 1)[0]
        beallitas = PicasaCollageSettings(
            theme=PICTUREGRID,
            width=1200,
            height=900,
            background=(255, 255, 255),
            shadow=True,
        )
        p = shadow_params(PICTUREGRID, page_width=1200, page_height=900, count=1)
        kep = render_nodes([_csempe_csomopont(ut)], beallitas).image
        oldal = round(300.0 * 1200 / 1024)
        kozep_x = round(512.0 * 1200 / 1024)
        kozep_y = round(384.0 * 1200 / 1024)
        jobb = kozep_x + oldal // 2

        sor = kep[kozep_y, :, 0]
        arnyekos = np.flatnonzero(sor < 255)
        assert arnyekos.size, "kell lennie árnyéknak a csempe sorában"
        legtavolabb = int(arnyekos[-1])
        assert legtavolabb >= jobb + p.blur, (
            f"az árnyék {legtavolabb - jobb} képponttal ér túl a csempén, "
            f"pedig az elmosás {p.blur:.1f} — levágódott"
        )

    def test_a_lap_szelen_allo_csempe_arnyeka_sem_borul(self, tmp_path):
        """A lap sarkába tolt csempe árnyéka a vászon szélén VÁGÓDIK, nem hibázik."""
        ut = _feher_kepek(tmp_path, 1)[0]
        beallitas = PicasaCollageSettings(
            theme=PICTUREGRID,
            width=600,
            height=400,
            background=(255, 255, 255),
            shadow=True,
        )
        sarokban = CollageNode(
            path=ut, center_x=0.0, center_y=0.0, width=200.0, height=200.0
        )
        tulra = CollageNode(
            path=ut, center_x=4000.0, center_y=4000.0, width=200.0, height=200.0
        )
        kep = render_nodes([sarokban, tulra], beallitas).image
        assert kep.shape == (400, 600, 3)

    def test_a_forgatott_csempe_arnyeka_is_dolt(self, tmp_path):
        """A Képkupac csomópontjai forgatva vannak — az árnyék velük fordul."""
        ut = _feher_kepek(tmp_path, 1)[0]
        beallitas = PicasaCollageSettings(
            theme=PICTUREPILE,
            width=1200,
            height=900,
            background=(255, 255, 255),
            shadow=True,
        )
        egyenes = CollageNode(
            path=ut, center_x=512.0, center_y=384.0, width=300.0, height=300.0
        )
        dolt = CollageNode(
            path=ut,
            center_x=512.0,
            center_y=384.0,
            width=300.0,
            height=300.0,
            theta=math.radians(25.0),
        )
        a = render_nodes([egyenes], beallitas).image
        b = render_nodes([dolt], beallitas).image
        assert not np.array_equal(a, b)
        assert _legsotetebb(a) < 255 and _legsotetebb(b) < 255

    def test_az_arnyek_a_csempe_ALATT_van(self, tmp_path):
        """Az árnyék nem takarja el a saját képét — a csempe fölé kerül.

        Fehér képpel a csempe belseje TISZTA fehér marad."""
        ut = _feher_kepek(tmp_path, 1)[0]
        beallitas = PicasaCollageSettings(
            theme=REGULARGRID,
            width=1200,
            height=900,
            background=(255, 255, 255),
            shadow=True,
        )
        kep = render_nodes([_csempe_csomopont(ut)], beallitas).image
        kozep_x = round(512.0 * 1200 / 1024)
        kozep_y = round(384.0 * 1200 / 1024)
        assert tuple(int(c) for c in kep[kozep_y, kozep_x]) == (255, 255, 255)


# --- 6. A rajzoló önmagában --------------------------------------------------


class TestDrawShadow:
    """A `draw_shadow` szerződése — vászon-szinten, csomópont nélkül."""

    def test_az_alfa_a_teljesen_fedett_helyen_pontos(self):
        """Nagy csempe, kicsi elmosás → a fedett rész pontosan `alfa`-nyit sötétít.

        Fehér lapon a 40 %-os árnyék 153, a 60 %-os 102 körül áll."""
        for atlatszatlansag, vart in ((0.4, 255 * (1 - 102 / 255)), (0.6, 255 * (1 - 153 / 255))):
            vaszon = _feher_lap(400, 400)
            p = ShadowParams(
                offset_x=60.0, offset_y=60.0, blur=2.0, opacity=atlatszatlansag
            )
            draw_shadow(vaszon, x=100, y=100, width=200, height=200, theta=0.0, params=p)
            # a csempétől jobbra-le, a fedett magban
            assert int(vaszon[290, 290, 0]) == pytest.approx(vart, abs=2)

    def test_a_nulla_elmosas_eles_arnyekot_ad(self):
        vaszon = _feher_lap(300, 300)
        p = ShadowParams(offset_x=20.0, offset_y=20.0, blur=0.0, opacity=0.5)
        draw_shadow(vaszon, x=50, y=50, width=100, height=100, theta=0.0, params=p)
        assert int(vaszon[160, 160, 0]) < 200
        assert int(vaszon[10, 10, 0]) == 255

    def test_a_vaszonon_kivuli_csempe_nem_hibazik(self):
        vaszon = _feher_lap(200, 200)
        p = ShadowParams(offset_x=3.0, offset_y=5.0, blur=8.0, opacity=0.4)
        draw_shadow(vaszon, x=-500, y=-500, width=100, height=100, theta=0.0, params=p)
        draw_shadow(vaszon, x=900, y=900, width=100, height=100, theta=0.0, params=p)
        assert int(vaszon.min()) == 255

    @pytest.mark.parametrize("meret", [(0, 10), (10, 0), (-3, 10)])
    def test_az_ures_csempe_nem_rajzol(self, meret):
        vaszon = _feher_lap(100, 100)
        p = ShadowParams(offset_x=3.0, offset_y=5.0, blur=4.0, opacity=0.4)
        draw_shadow(
            vaszon, x=10, y=10, width=meret[0], height=meret[1], theta=0.0, params=p
        )
        assert int(vaszon.min()) == 255


# --- 7. Golden: a felhasználó nyolc eredeti Picasa-kollázsa -----------------


class TestGolden:
    """A privát `referencia/kollazs-golden/` mérései, tűréssel visszaolvasva.

    A minták maguk NEM kerülhetnek a nyilvános repóba (a felhasználó
    fényképei), a belőlük MÉRT számok viszont igen — ezek a jegy és a spec
    9/b.4 hivatkozott értékei."""

    def test_ai4_framegrid_eltolas_es_sugar(self):
        """`AI4` (framegrid, 5120 széles): mért dx 10,0 / dy 14,5 / sugár 44,5–46."""
        p = shadow_params(FRAMEGRID, page_width=5120, page_height=3840, count=9)
        assert p.offset_x == pytest.approx(10.0, abs=0.5)
        assert p.offset_y == pytest.approx(14.5, abs=1.0)
        # a MÉRT sugár a látható kifutás; a képlet elmosása 40,96
        assert p.blur == pytest.approx(45.0, rel=0.12)

    def test_ai6_contactsheet_sugar(self):
        """`AI6` (contactsheet, 3841×5120, 9 kép): mért sugár 34,5."""
        p = shadow_params(CONTACTSHEET, page_width=3841, page_height=5120, count=9)
        assert p.blur == pytest.approx(34.5, abs=1.0)

    def test_ai1_picturepile_nagysagrend(self):
        """`AI1` (picturepile, 5120×5120, 9 kép): mért (3,0 ; 5,0), sugár ≈ 33,5.

        ⚠️ **Feltételes**: a Képkupac csomópontjai el vannak forgatva, ezért
        a tengelyirányú mérés keveri a komponenseket — a tűrés itt tágabb, és
        ezt a spec 9/b.4 is kimondja."""
        p = shadow_params(PICTUREPILE, page_width=5120, page_height=5120, count=9)
        assert p.offset_x == pytest.approx(3.0, abs=2.0)
        assert p.offset_y == pytest.approx(5.0, abs=2.0)
        assert p.blur == pytest.approx(33.5, rel=0.15)
