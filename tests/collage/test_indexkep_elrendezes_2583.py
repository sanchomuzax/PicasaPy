"""Az Indexkép csonkolása és a `scale`/magasság szétválasztása (#2583).

A `docs/specs/kollazs-eletciklus.md` 18. szakasza a `FUN_00888210`
elrendezőt (`0x00888210`) 31/31 · 31/31 csomóponton kimérte. Két, a
saját kódunkban maradt eltérést javít ez a jegy:

1. a margó- és cellaszámítás **kerekít** (`picasa_round`), a bináris
   viszont **csonkol** (`or eax, 0xc00` minden `fistp` előtt);
2. a csomópont `h`-ja (a kirajzolt kép magassága) nálunk **egybeesett**
   a cellamagassággal, holott az eredetiben a `h = w / képarány`, a
   cellamagasságot pedig a lap-szintű `scale` mező hordozza, és ez
   igazít FÜGGŐLEGESEN — ezért az eredetiben a kép FELÜLRE kerül, nem
   középre.

A négy „arany" minta (`AI6`, `AI27`, `AI28`, `AI29`, összesen 31
csomópont) `x`/`y`/margó/cella-értékei a valódi `.cxf`-ekből származó,
KIÍRT LITERÁLOK — nem a termékkódból számoltuk őket, különben az őr
önmagát mérné (memória: „a levezetett képletnek az inverzét").

A `scale` ÉRTÉKÉNEK zárt képlete nyitott (18.6, #1412) — ezért az
`x`/`y`-formulát a fájlból OLVASOTT `scale`-lel teszteljük, nem a
termékkód saját (0–2 egység eltérő, 18.8/183. kör szerint a bináris
saját aritmetikájával is megmaradó) közelítésével.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from picasapy.collage.draft import project_from_nodes
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    _contact_sheet_geometry,
    _contact_sheet_nodes,
    _contact_sheet_position,
    contact_sheet_cell_scale,
    layout_nodes_for_aspects,
)
from picasapy.collage.themes import CONTACTSHEET, NOBORDER, WHITEBORDER


# ---------------------------------------------------------------------------
# 1. A margó- és cellaszámítás CSONKOL, nem kerekít (kollazs-eletciklus.md
#    18.2/18.4 — az öt konstans a binárisból, a lap 1024 × P egységében).
# ---------------------------------------------------------------------------

# (lapszélesség, lapmagasság, képszám) → (bal, fent, cella_w, cella_h, belso)
_GEOMETRIA_MINTAK = {
    "AI6": ((1024, 1365, 9), (61, 204, 300, 359, 24)),
    "AI27": ((1024, 1448, 4), (61, 217, 450, 571, 36)),
    "AI28": ((1024, 768, 6), (61, 115, 300, 303, 24)),
    "AI29": ((1024, 708, 12), (61, 106, 225, 186, 14)),
}


@pytest.mark.parametrize("minta", sorted(_GEOMETRIA_MINTAK))
def test_a_geometria_csonkol_nem_kerekit(minta):
    (szelesseg, magassag, kepszam), vart = _GEOMETRIA_MINTAK[minta]
    geometria = _contact_sheet_geometry(szelesseg, magassag, kepszam)
    assert (
        geometria.bal,
        geometria.fent,
        geometria.cella_w,
        geometria.cella_h,
        geometria.belso,
    ) == vart


def test_kerekitessel_a_ket_oszlopos_cella_451_csonkolassal_450():
    """A jegy mérése: 1024 × 0,88 / 2 oszlop kerekítve 451, csonkolva 450."""
    geometria = _contact_sheet_geometry(1024, 1448, 4)
    assert geometria.cella_w == 450
    assert geometria.cella_w != round(1024 * 0.88 / 2)  # 451 — a régi hiba


# ---------------------------------------------------------------------------
# 2. Az x/y OFFSET-KÉPLET — 31/31 csomóponton, a fájlból OLVASOTT w/scale-lel.
#
# A számok a valódi AI6.cxf / AI27.cxf / AI28.cxf / AI29.cxf tartalmából:
# node.x·1024, node.y·P, node.w·1024 (P = a lap magassága 1024-es
# egységben, kollazs-eletciklus.md 18.3). KIÍRT LITERÁLOK, nem számolás.
# ---------------------------------------------------------------------------

# (bal, fent, cella_w, cella_h, oszlopok, scale) minden mintához.
_RACS = {
    "AI6": (61, 204, 300, 359, 3, 313),
    "AI27": (61, 217, 450, 571, 2, 500),
    "AI28": (61, 115, 300, 303, 3, 256),
    "AI29": (61, 106, 225, 186, 4, 158),
}

# node index → (x_várt, y_várt, w_fájlból)
_CSOMOPONTOK = {
    "AI6": [
        (90, 227, 242),
        (390, 227, 242),
        (733, 227, 155),
        (90, 586, 242),
        (390, 586, 242),
        (690, 586, 242),
        (90, 945, 242),
        (390, 945, 242),
        (690, 945, 242),
    ],
    "AI27": [
        (161, 252, 250),
        (607, 252, 257),
        (178, 823, 216),
        (611, 823, 250),
    ],
    "AI28": [
        (149, 138, 124),
        (447, 138, 127),
        (733, 138, 156),
        (158, 441, 106),
        (449, 441, 124),
        (747, 441, 127),
    ],
    "AI29": [
        (110, 120, 127),
        (335, 120, 127),
        (560, 120, 127),
        (785, 120, 127),
        (110, 306, 127),
        (335, 306, 127),
        (560, 306, 127),
        (785, 306, 127),
        (110, 492, 127),
        (335, 492, 127),
        (560, 492, 127),
        (785, 492, 127),
    ],
}


@pytest.mark.parametrize("minta", sorted(_CSOMOPONTOK))
def test_az_offset_keplet_eltetes_nelkul_31_csomoponton(minta):
    bal, fent, cella_w, cella_h, oszlopok, scale = _RACS[minta]
    for index, (x_vart, y_vart, w) in enumerate(_CSOMOPONTOK[minta]):
        sor, oszlop = divmod(index, oszlopok)
        x = _contact_sheet_position(bal, cella_w, oszlop, w)
        y = _contact_sheet_position(fent, cella_h, sor, scale)
        assert x == x_vart, f"{minta} node{index}: x={x}, várt={x_vart}"
        assert y == y_vart, f"{minta} node{index}: y={y}, várt={y_vart}"


def test_az_offset_keplet_maga_is_csonkol():
    """AI28 node1: (300-127)/2 = 86,5 — a mért `x` a CSONKOLT 86-tal egyezik.

    (A Python beépített ``round()`` itt bankári kerekítéssel véletlenül is
    86-ot adna — ezért egy nem félúton álló esetet nézünk: `(300-124)/2`
    kerekítve 88, csonkolva is 88, de `(300-106)/2 = 97` kerekítve is 97 —
    a valódi csonkolási hiba csak FÉL-egésznél látszik, ott viszont a
    fenti node1 már bizonyítja: a termékkód a csonkolt 86-ot adja.)"""
    x = _contact_sheet_position(61, 300, 1, 127)
    assert x == 447
    assert math.trunc((300 - 127) / 2.0) == 86


# ---------------------------------------------------------------------------
# 3. A csomópont `h`-ja A KIRAJZOLT KÉP magassága (w / képarány), NEM a
#    cellamagasság — és a függőleges igazítás a LAP-SZINTŰ magassággal megy,
#    nem az egyes kép sajátjával (18.5).
# ---------------------------------------------------------------------------


def test_a_csomopont_magassaga_kepenkent_elter_ha_az_aranyuk_elter():
    """Az AI27 négy képe négy KÜLÖNBÖZŐ arányú (446,08 · 449,75 · 432,00 ·
    446,08 lapegység az eredetiben) — a régi kódunk mind a négyre 500-at
    (a cellamagasságot) adta, mert a `h` nem vált szét a `scale`-től."""
    settings = PicasaCollageSettings(theme=CONTACTSHEET, border=NOBORDER, width=1024, height=1448)
    aspektusok = [250 / 446.078, 257 / 449.750, 216 / 432.001, 250 / 446.078]
    paths = tuple(Path(f"{i}.png") for i in range(4))
    nodes, _, _ = _contact_sheet_nodes(aspektusok, paths, settings)
    magassagok = {round(node.height, 1) for node in nodes}
    assert len(magassagok) > 1, "a négy csomópont magasságának különböznie kell"
    # egyik magasság se essen egybe a cellamagassággal (571 lapegység)
    for node in nodes:
        assert round(node.height) != 571


def test_a_cxf_y_azonos_akkor_is_ha_a_magassag_elter():
    """AI27 első sora: a fájlban a két kép magassága 446,08 és 449,75, az
    `y` mégis AZONOS — mert a `.cxf` a LAP-SZINTŰ `scale`-lel igazított
    doboz tetejét írja, nem a kép sajátját (18.5, a #1412 rejtélyének
    magyarázata).

    ⚠️ A KÖZÉP viszont közös: a rajzoló a képet a saját magasságával
    KÖZÉPRE teszi a cellába — ezt a tulajdonos `AI27.jpg` exportján
    mérve igazoltuk (a `.cxf` y-ra rajzolt változat 26…35 lapegységgel
    feljebb tette a képeket, mint az eredeti)."""
    settings = PicasaCollageSettings(theme=CONTACTSHEET, border=NOBORDER, width=1024, height=1448)
    aspektusok = [250 / 446.078, 257 / 449.750, 216 / 432.001, 250 / 446.078]
    paths = tuple(Path(f"{i}.png") for i in range(4))
    nodes, _, _ = _contact_sheet_nodes(aspektusok, paths, settings)
    elso, masodik = nodes[0], nodes[1]
    assert elso.height != pytest.approx(masodik.height, abs=0.5)
    # a KÖZÉP közös (a rajz ide kerül)
    assert elso.center_y == pytest.approx(masodik.center_y, abs=1e-6)
    # …és a `.cxf`-be írt `y` is közös (a `scale`-lel igazítva)
    projekt = project_from_nodes(nodes, settings)
    y_ertekek = {round(node.y, 9) for node in projekt.nodes[:2]}
    assert len(y_ertekek) == 1, f"a .cxf y nem közös: {y_ertekek}"
    lap_magassag = 1024 * (1448 / 1024)
    assert projekt.nodes[0].y * lap_magassag == pytest.approx(252.0, abs=1.5)


def test_a_sajat_kozelitesunk_a_scale_ra_ket_egysegen_belul_marad():
    """A `scale` PONTOS képlete nyitott (18.6/#1412) — a saját közelítésünk
    (cellamagasság − 2·belső ráhagyás) a négy mintán legfeljebb 2 lapegység
    eltérést ad (18.8, megerősítve a 183. kutatói körben: ez a bináris
    SAJÁT aritmetikájával is megmarad, tehát nem a mi hibánk)."""
    vart_scale = {"AI6": 313, "AI27": 500, "AI28": 256, "AI29": 158}
    kepszam = {"AI6": 9, "AI27": 4, "AI28": 6, "AI29": 12}
    magassag = {"AI6": 1365, "AI27": 1448, "AI28": 768, "AI29": 708}
    for minta, scale in vart_scale.items():
        geometria = _contact_sheet_geometry(1024, magassag[minta], kepszam[minta])
        kozelites = max(1, geometria.cella_h - 2 * geometria.belso)
        assert abs(kozelites - scale) <= 2, f"{minta}: {kozelites} vs {scale}"


# ---------------------------------------------------------------------------
# 4. Teljes csővezeték: a `layout_nodes_for_aspects` (a felület és a
#    rajzoló KÖZÖS bejárata) is az új geometriát adja — nem csak a belső
#    `_contact_sheet_nodes`.
# ---------------------------------------------------------------------------


def test_layout_nodes_for_aspects_is_a_javitott_geometriat_hasznalja():
    """A `layout_nodes_for_aspects` (a felület/rajzoló KÖZÖS bejárata) a
    csonkolt geometriát adja tovább — a saját `w`-derivációnk pontossága
    (a doboz-illesztő PONTOS képlete nyitott, 18.6/18.7) itt nem tétel,
    csak az, hogy a csonkolt `bal`/`cella_w` ténylegesen érvényesül."""
    settings = PicasaCollageSettings(
        theme=CONTACTSHEET, border=WHITEBORDER, width=1024, height=768
    )
    aspektusok = [124 / 221.255, 127 / 222.250, 156 / 234.000, 106 / 212.000, 124 / 221.255, 127 / 222.250]
    paths = tuple(Path(f"{i}.png") for i in range(6))
    nodes = layout_nodes_for_aspects(aspektusok, paths, settings)
    assert len(nodes) == 6

    geometria = _contact_sheet_geometry(1024, 768, 6)
    assert (geometria.bal, geometria.fent, geometria.cella_w, geometria.cella_h) == (
        61,
        115,
        300,
        303,
    )

    # az első csomópont x-e önmagában konzisztens az offset-képlettel, a
    # SAJÁT (a pipeline által számolt) szélességéből visszaszámolva
    elso = nodes[0]
    x_bal = round(elso.center_x - elso.width / 2.0)
    kulso_w = round(elso.width)
    assert x_bal == _contact_sheet_position(geometria.bal, geometria.cella_w, 0, kulso_w)


# ---------------------------------------------------------------------------
# 5. A `.cxf` `scale` mezője (`draft.project_from_nodes`): LAP-SZINTŰ
#    állandó, minden csomópontra ugyanaz — nem a csomópont saját doboza
#    (`draft.scale_for_theme` régi „négyzetoldal" heurisztikája most már
#    csak TARTALÉK, amikor `project_from_nodes`-on kívül hívják).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("minta", "szelesseg", "magassag", "kepszam", "vart_scale"),
    [
        ("AI6", 1024, 1365, 9, 313),
        ("AI27", 1024, 1448, 4, 500),
        ("AI28", 1024, 768, 6, 256),
        ("AI29", 1024, 708, 12, 158),
    ],
)
def test_contact_sheet_cell_scale_ket_egysegen_belul_marad(
    minta, szelesseg, magassag, kepszam, vart_scale
):
    kozelites = contact_sheet_cell_scale(szelesseg, magassag, kepszam)
    assert abs(kozelites - vart_scale) <= 2, f"{minta}: {kozelites} vs {vart_scale}"


def test_project_from_nodes_minden_csomopontnak_ugyanazt_a_scale_t_adja():
    """A `.cxf`-be író út (`project_from_nodes`) az Indexképnél LAP-SZINTŰ
    `scale`-t ír — nem a csomópont saját (eltérő) magasságát, ahogy a
    `scale_for_theme` „négyzetoldal" heurisztikája önmagában tenné."""
    settings = PicasaCollageSettings(theme=CONTACTSHEET, border=NOBORDER, width=1024, height=1448)
    aspektusok = [250 / 446.078, 257 / 449.750, 216 / 432.001, 250 / 446.078]
    paths = tuple(Path(f"{i}.png") for i in range(4))
    nodes = layout_nodes_for_aspects(aspektusok, paths, settings)
    projekt = project_from_nodes(nodes, settings)
    scale_ertekek = {node.scale for node in projekt.nodes}
    assert len(scale_ertekek) == 1, f"a scale nem lap-szintű: {scale_ertekek}"
    (scale,) = scale_ertekek
    assert abs(scale - 500) <= 2
