"""A `.cxf` `scale` mezője TÉMÁNKÉNT mást jelent (#1036).

## Mit mond a jegy, és mit mond a MÉRÉS

A jegy leletje az volt, hogy „a rácsos értelmezés a **Képkupacra** nem
működik". A tizenkét golden `.cxf`-en végigmérve **ennek az ellenkezője**
igaz:

- a **Képkupac** csomópont-mezőit a mai kódunk pontosan írja — hat mintán,
  49 csomóponton `|Δscale| ≤ 0,09` lapegység, és az `AI10.jpg` legfelső,
  takaratlan csempéjének mind a négy éle **két képponton belül** van ott,
  ahova a `w`/`h` mutat (1515 képpontos csempe, 5120 képpontos lap);
- a **rácsos** témák `scale`-je viszont NEM a befoglaló négyzet oldala,
  hanem a **cella SZÉLESSÉGE** — és épp ezt írjuk ma rosszul, 39-től 230
  lapegységig tévedve.

A jegy „~930 × 1010 képpont" mérése a golden README-ben külön megnevezett
csapdába esett: a Képkupac csempéi **fedik egymást**, és egy takart csempe
látható része a valódi méreténél kisebb.

## A mért szabály témánként

| téma | a `scale` jelentése | minta |
|---|---|---|
| `picturepile` | a csempe **befoglaló NÉGYZETÉNEK** oldala | AI, AI1, AI2, AI8, AI9, AI10 |
| `picturegrid` | a **kirajzolt cella szélessége** (térköz UTÁN) | AI3 |
| `framegrid` | ugyanaz | AI4 |
| `regulargrid` | ugyanaz | AI5 |
| `contactsheet` | **nem levezetett** — mind a 9 csomóponton 313 | AI6 |
| `multiexp` | 1,0 (#1248) | AI7 |

A rácsos témáknál a golden `w` mezője a térköz ELŐTTI pakolási téglalap, a
`scale` viszont a térköz UTÁNI cellából jön — ezért ez a fájl a rácsos
esetet a **saját cella-számolónkon** (`to_pixel_rects` → `_cell_nodes`)
keresztül állítja, nem a golden `w`-jéből. Így a teszt nem körkörös: az
eredeti pakolási téglalapjait és térközét adjuk be, és a saját utunk
végén hasonlítjuk össze a `scale`-t az eredetiével.

⚠️ Az eredeti a cellát az **1024 képpont széles** lapon kerekíti, mi a
kimeneti felbontáson; a maradék ezért legfeljebb **egy** lapegység. A mai,
hibás szabály ennél két nagyságrenddel messzebb van.
"""

from __future__ import annotations

import pytest

from picasapy.collage.draft import cxf_node_of, project_from_nodes, scale_for_theme
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings, _cell_nodes
from picasapy.collage.rects import NormRect
from picasapy.collage.themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
)

#: `AI1.cxf` (Képkupac, 1:1 álló): a csomópont doboza lapegységben és a
#: fájlban álló `scale`. A doboz `w · 1024` és `h · 1024 · laparány`.
GOLDEN_KUPAC_AI1 = (
    (269.600, 337.000, 337.0),
    (269.600, 337.000, 337.0),
    (188.869, 337.000, 337.0),
    (269.600, 337.000, 337.0),
    (242.400, 303.000, 303.0),
    (224.000, 280.001, 280.0),
    (210.400, 263.000, 263.0),
    (199.200, 249.000, 249.0),
    (190.399, 238.000, 238.0),
)

#: `AI8.cxf` (Képkupac, A4 FEKVŐ) — más laparány, ugyanaz a szabály.
GOLDEN_KUPAC_AI8 = (
    (269.600, 337.019, 337.0),
    (188.869, 337.019, 337.0),
    (242.400, 303.017, 303.0),
    (198.304, 238.013, 238.0),
)

#: `AI3.cxf` (Mozaik): a pakolási téglalapok a `[0,1]²`-ben és a `scale`.
GOLDEN_MOZAIK_AI3 = (
    ((0.571359, 0.000000, 0.785680, 0.375107), 216.0),
    ((0.785679, 0.000000, 1.000000, 0.375107), 214.0),
    ((0.749877, 0.375107, 1.000000, 1.000000), 250.0),
    ((0.571359, 0.375107, 0.749878, 0.687553), 179.0),
    ((0.285679, 0.000000, 0.571358, 0.500000), 289.0),
    ((0.000000, 0.000000, 0.285679, 0.500000), 287.0),
    ((0.000000, 0.500000, 0.285679, 1.000000), 287.0),
    ((0.285679, 0.500000, 0.571358, 1.000000), 289.0),
    ((0.571359, 0.687554, 0.749878, 1.000000), 179.0),
)
GOLDEN_MOZAIK_AI3_TERKOZ = 0.047549

#: `AI4.cxf` (Képkockamozaik) — NAGY térközzel, ez a legélesebb minta.
GOLDEN_KOCKA_AI4 = (
    ((0.350000, 0.250000, 0.650000, 0.750000), 280.0),
    ((0.000000, 0.588045, 0.350000, 1.000000), 319.0),
    ((0.000000, 0.000000, 0.350000, 0.588045), 319.0),
    ((0.650000, 0.000000, 1.000000, 0.500000), 319.0),
    ((0.650000, 0.500000, 1.000000, 1.000000), 319.0),
    ((0.350000, 0.750000, 0.500000, 1.000000), 127.0),
    ((0.500000, 0.750000, 0.650000, 1.000000), 127.0),
    ((0.350000, 0.000000, 0.500000, 0.250000), 127.0),
    ((0.500000, 0.000000, 0.650000, 0.250000), 127.0),
)
GOLDEN_KOCKA_AI4_TERKOZ = 0.382546

#: A két rácsos minta lapja: 4:3 fekvő, 5120 × 3840.
_LAP_W, _LAP_H = 5120, 3840


def _lap(theme: str, spacing: float = 0.0) -> PicasaCollageSettings:
    return PicasaCollageSettings(
        width=_LAP_W, height=_LAP_H, theme=theme, spacing=spacing, border=NOBORDER
    )


def _racsos_scale(
    minta: tuple[tuple[tuple[float, float, float, float], float], ...],
    theme: str,
    terkoz: float,
) -> list[tuple[float, float]]:
    """A SAJÁT utunk `scale`-je az eredeti pakolási téglalapjaiból.

    Visszaadja a `(mi, golden)` párokat, hogy az állítás egy helyen legyen."""
    beallitas = _lap(theme, terkoz)
    rects = tuple(NormRect(*negyes) for negyes, _ in minta)
    nodes = _cell_nodes([f"/nincs/{i}.png" for i in range(len(rects))], rects, beallitas)
    projekt = project_from_nodes(nodes, beallitas)
    return [(csp.scale, golden) for csp, (_, golden) in zip(projekt.nodes, minta, strict=True)]


class TestKepkupac:
    """A Képkupac értelmezése MA IS helyes — ezt rögzítjük, nem javítjuk."""

    @pytest.mark.parametrize(
        "minta", (GOLDEN_KUPAC_AI1, GOLDEN_KUPAC_AI8), ids=("AI1", "AI8")
    )
    def test_a_befoglalo_negyzet_oldalat_irja(self, minta) -> None:
        for szeles, magas, golden in minta:
            assert scale_for_theme(szeles, magas, PICTUREPILE) == pytest.approx(
                golden, abs=0.1
            )

    def test_a_teljes_uton_is(self) -> None:
        """Nem csak a képlet: a `project_from_nodes` kimenetén is."""
        beallitas = PicasaCollageSettings(
            width=5120, height=5120, theme=PICTUREPILE, border=NOBORDER
        )
        nodes = [
            CollageNode(
                path="/nincs/a.png",
                center_x=SHEET_UNITS * 0.5,
                center_y=SHEET_UNITS * 0.5,
                width=szeles,
                height=magas,
                border=NOBORDER,
            )
            for szeles, magas, _ in GOLDEN_KUPAC_AI1
        ]
        projekt = project_from_nodes(nodes, beallitas)
        for csp, (_, _, golden) in zip(projekt.nodes, GOLDEN_KUPAC_AI1, strict=True):
            assert csp.scale == pytest.approx(golden, abs=0.1)


class TestRacsosTemak:
    """A rácsos témák `scale`-je a CELLA SZÉLESSÉGE, nem a nagyobbik oldal."""

    @pytest.mark.parametrize(
        ("minta", "theme", "terkoz"),
        (
            (GOLDEN_MOZAIK_AI3, PICTUREGRID, GOLDEN_MOZAIK_AI3_TERKOZ),
            (GOLDEN_KOCKA_AI4, FRAMEGRID, GOLDEN_KOCKA_AI4_TERKOZ),
        ),
        ids=("AI3-picturegrid", "AI4-framegrid"),
    )
    def test_egyezik_a_goldennel(self, minta, theme, terkoz) -> None:
        for mi, golden in _racsos_scale(minta, theme, terkoz):
            assert mi == pytest.approx(golden, abs=1.0)

    def test_a_szelesseget_irja_akkor_is_ha_a_magassag_nagyobb(self) -> None:
        """A megkülönböztető állítás: álló cellánál a kettő NEM esik egybe."""
        assert scale_for_theme(219.465, 288.082, PICTUREGRID) == pytest.approx(219.465)
        assert scale_for_theme(219.465, 288.082, REGULARGRID) == pytest.approx(219.465)
        assert scale_for_theme(219.465, 288.082, FRAMEGRID) == pytest.approx(219.465)
        # a Képkupac ugyanezen a dobozon MÁST ad — ez a témafüggés lényege
        assert scale_for_theme(219.465, 288.082, PICTUREPILE) == pytest.approx(288.082)

    def test_a_regi_szabaly_ELBUKNA(self) -> None:
        """Őr: a `max(w, h)` szabály a golden mintán bizonyíthatóan téved.

        Ha valaki visszaállítja, ez a teszt mondja meg, hogy nem elírás
        történt — az `AI4` első cellája 357,6-ot kapna 280 helyett."""
        legnagyobb_elteres = max(
            abs(max(mi_szeles, mi_magas) - golden)
            for (mi_szeles, mi_magas), (_, golden) in zip(
                _racsos_dobozok(GOLDEN_KOCKA_AI4, FRAMEGRID, GOLDEN_KOCKA_AI4_TERKOZ),
                GOLDEN_KOCKA_AI4,
                strict=True,
            )
        )
        assert legnagyobb_elteres > 25.0


def _racsos_dobozok(minta, theme: str, terkoz: float) -> list[tuple[float, float]]:
    """A cellák doboza lapegységben — a fenti őrhöz."""
    beallitas = _lap(theme, terkoz)
    rects = tuple(NormRect(*negyes) for negyes, _ in minta)
    nodes = _cell_nodes([f"/nincs/{i}.png" for i in range(len(rects))], rects, beallitas)
    return [(csp.width, csp.height) for csp in nodes]


class TestMasKetTema:
    def test_multiexp_valtozatlanul_egy(self) -> None:
        """Az `AI7.cxf` mérése (#1248) — ezt a #1036 nem érinti."""
        assert scale_for_theme(1024.0, 768.0, MULTIEXP) == 1.0

    def test_indexkep_a_befoglalo_negyzeten_marad(self) -> None:
        """Az Indexkép `scale`-je MÉRVE 313, de LEVEZETVE nincs.

        Az `AI6.cxf` mind a kilenc csomópontján 313 áll — a csomópont
        dobozától (242 × 302,6 és 155 × 276,6 lapegység) függetlenül, tehát
        ez lap-szintű állandó, nem csomópont-méret. Se a `k` cellaél (300),
        se a cella magassága (359) nem adja ki; egyetlen mintánk van rá.
        Amíg nincs levezetés, a régi szabály marad — de KIMONDVA, hogy
        tudjuk, mit nem tudunk."""
        assert scale_for_theme(242.0, 302.574, CONTACTSHEET) == pytest.approx(302.574)


class TestOdaVissza:
    def test_a_geometria_valtozatlan_marad(self) -> None:
        """A `scale` javítása az `x/y/w/h`-hoz NEM nyúlhat.

        Ez a mező az egyetlen, amit a saját olvasónk nem használ (#1071),
        tehát a körbejárásunk nem is fogná meg, ha elrontanánk mellette a
        geometriát."""
        node = CollageNode(
            path="/nincs/a.png",
            center_x=300.0,
            center_y=400.0,
            width=200.0,
            height=350.0,
            border=NOBORDER,
        )
        alap = cxf_node_of(node, page_width=5120, page_ratio=0.75)
        beallitas = _lap(PICTUREGRID)
        projekt = project_from_nodes([node], beallitas)
        kiirt = projekt.nodes[0]
        assert (kiirt.x, kiirt.y, kiirt.w, kiirt.h) == (alap.x, alap.y, alap.w, alap.h)
        assert kiirt.theta == alap.theta
