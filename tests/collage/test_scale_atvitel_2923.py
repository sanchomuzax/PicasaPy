"""A csomópont `scale`-je: mit viszünk át, és mit NEM számolunk (#2923).

A jegy a `docs/specs/kollazs-eletciklus.md` **67. szakaszára** épül (277.
kutatói kör): az elrendező a csomópont `+0x2c`-jéhez nem nyúl, minden
hozzáfűző út konstanst ír, a másolók és a dokumentum-`reset` változatlanul
viszik tovább — az egyetlen nem-konstans forrás a **fájl** (`_atof`).

Ebből a jegy két termékkövetelményt vezetett le. Az egyik **elkészült**
(betöltött `.cxf`: a `scale` érintetlenül megy vissza, #2954), a másik —
„frissen létrehozott csomópontnál `scale = 1,0`" — a **mérésen megdől**,
és ez a fájl az ő őre. Két, egymástól független szám mondja ki:

1. `scale = 1,0`-nál az Indexkép `y`-ja elmozdul, mert a `.cxf` a
   `scale`-lel igazított doboz TETEJÉT írja (30.2: 10/10 sor, négy minta);
2. a négy minta `scale`-je a MINTA SAJÁT cellageometriáját követi
   (31.5: 0…2 lapegység) — öröklött, a kollázstól független érték ezt nem
   tudná megtenni.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from picasapy.collage.draft import project_from_nodes
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    _contact_sheet_geometry,
    _contact_sheet_nodes,
    contact_sheet_cell_scale,
)
from picasapy.collage.themes import CONTACTSHEET, NOBORDER

# minta → (lapmagasság, képszám, a FÁJLBAN álló `scale`) — kiírt literálok a
# négy arany `.cxf`-ből (kollazs-eletciklus.md 31.5), nem termékkódból.
_MINTAK = {
    "AI6": (1365, 9, 313),
    "AI27": (1448, 4, 500),
    "AI28": (768, 6, 256),
    "AI29": (708, 12, 158),
}


def _aspektusok_ai27() -> list[float]:
    """Az AI27 négy képének képaránya (a fájlból olvasott dobozokból)."""
    return [250 / 446.078, 257 / 449.750, 216 / 432.001, 250 / 446.078]


def test_a_kozelites_docstringje_nem_allitja_hogy_a_keplet_nyitott():
    """A 67. szakasz LEZÁRTA a kérdést: nincs képlet a binárisban.

    A `contact_sheet_cell_scale` docstringje eddig „a pontos képlet
    nyitott"-ot állított, és a 18.6-ra hivatkozott. A komment sem
    hazudhat: a lezárás után a hivatkozás a 67. szakaszra szól."""
    leiras = inspect.getdoc(contact_sheet_cell_scale) or ""
    assert "nyitott" not in leiras, (
        "a docstring még nyitott kérdésnek mondja a `scale` képletét, "
        "pedig a 67. szakasz lezárta"
    )
    assert "67." in leiras, "a docstring nem hivatkozik a spec 67. szakaszára"


def test_scale_1_0_elmozditana_az_indexkep_sorait():
    """A jegy 2. pontja (`scale = 1,0`) 200+ lapegységet mozdítana az `y`-on.

    Az AI27 első sorának mért `y`-ja 252 lapegység, és ez a `scale`-lel
    (500) igazított doboz teteje. Ugyanaz a csomópont `scale = 1,0`-val
    a cella közepére ugrik — tehát a jegy 2. pontja mért, golden-tesztelt
    viselkedést rontana el."""
    settings = PicasaCollageSettings(
        theme=CONTACTSHEET, border=NOBORDER, width=1024, height=1448
    )
    paths = tuple(Path(f"{i}.png") for i in range(4))
    nodes, _, _ = _contact_sheet_nodes(_aspektusok_ai27(), paths, settings)
    lap_magassag = 1448.0

    mert = project_from_nodes(nodes, settings)
    assert mert.nodes[0].y * lap_magassag == pytest.approx(252.0, abs=1.5)

    egysegre_kenyszeritve = project_from_nodes(
        nodes, settings, node_scales={node.src: 1.0 for node in mert.nodes}
    )
    eltolt_y = egysegre_kenyszeritve.nodes[0].y * lap_magassag
    assert abs(eltolt_y - 252.0) > 200.0, (
        f"a scale=1,0 nem mozdítja az y-t ({eltolt_y}) — a 30.2 mérése szerint kellene"
    )


@pytest.mark.parametrize("minta", sorted(_MINTAK))
def test_a_scale_a_minta_sajat_cellageometriajat_koveti(minta):
    """A `scale` nem lehet a kollázstól FÜGGETLEN, öröklött érték.

    A 67.3 kimondja: gépi úton nem zárható ki, hogy a mintákat író
    Picasa-futás a dokumentumot korábban egy `.cxf`-ből töltötte, és a
    `scale` onnan öröklődött. Ez a teszt ezt SZÁMMAL szűkíti: mind a négy
    mintában a fájl `scale`-je a minta SAJÁT cellageometriájából jön
    (0…2 lapegység, 31.5), a másik három mintáé pedig nem illik rá.
    Egy idegen fájlból örökölt érték ezt nem tudná megtenni."""
    magassag, kepszam, fajl_scale = _MINTAK[minta]
    geometria = _contact_sheet_geometry(1024, magassag, kepszam)
    sajat = max(1, geometria.cella_h - 2 * geometria.belso)
    assert abs(sajat - fajl_scale) <= 2, f"{minta}: {sajat} vs {fajl_scale}"
    for masik, (_, _, masik_scale) in _MINTAK.items():
        if masik == minta:
            continue
        assert abs(sajat - masik_scale) > 2, (
            f"{minta} geometriája a(z) {masik} scale-jére is illik — "
            "a minták nem különböztetnék meg az öröklést a számítástól"
        )


def test_a_betoltott_scale_valtozatlanul_megy_vissza():
    """A jegy 3. pontja (elkészült, #2954) őre: a fájl értéke érintetlen.

    A számolt közelítés az AI27-en 499 — ha a mentés újraszámolná, egy
    Picasával készült kollázs `scale`-je 500-ról 499-re csúszna."""
    settings = PicasaCollageSettings(
        theme=CONTACTSHEET, border=NOBORDER, width=1024, height=1448
    )
    paths = tuple(Path(f"{i}.png") for i in range(4))
    nodes, _, _ = _contact_sheet_nodes(_aspektusok_ai27(), paths, settings)
    szamolt = project_from_nodes(nodes, settings)
    orzott = project_from_nodes(
        nodes, settings, node_scales={node.src: 500.0 for node in szamolt.nodes}
    )
    assert {node.scale for node in orzott.nodes} == {500.0}
    assert contact_sheet_cell_scale(1024, 1448, 4) != 500.0
