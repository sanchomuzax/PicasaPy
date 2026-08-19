"""#989: a hat téma HAT KÜLÖNBÖZŐ elrendezést ad — a magban, kép nélkül.

A #920 kollázs-panelje a téma-választót megjelenítette, de a vászon
elrendezése mindig ugyanaz maradt: a `collage_layout.laid_out` a Képkupac
szórását hívta, téma nélkül. A hat pakoló (`pile`, `packing`,
`regular_grid`, `contact_sheet`, `multi_exposure`) KÉSZ volt, csak a
mentési úton futott.

Ez a fájl a KIMENETET állítja, nem a hívást: ugyanazokra a forrásokra a
csomópontok geometriája (középpont, méret, szög) témánként érdemben
eltér, és a determinisztikus témák (Rács, Indexkép) a rájuk jellemző
szabályos alakot adják.

⚠️ **Beégetett képpont-ellenőrzés (SHA/MD5) itt nincs** — az a platformot
is szerződésbe foglalná, és a Windows-lábon némán bukna (#942 tanulsága).
Az állítások SZERKEZETIEK: rács-e a rács, a fejléc alatt van-e az
indexkép, középen van-e a hangsúlyos kép.

⚠️ A Mozaik pakolója (`packing.pack`) IDŐKORLÁTOS véletlen keresés, tehát
NEM determinisztikus. Erre a témára ezért csak olyan állítás születik itt,
ami a keresés kimenetelétől független (a cellák kitöltik a lapot).
"""

from __future__ import annotations

import math

import pytest

from picasapy.collage import rects
from picasapy.collage.fitting import fit_aspect_inside, fit_inside
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    layout_nodes_for_aspects,
)
from picasapy.collage.themes import (
    COLLAGE_THEMES,
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    REGULARGRID,
)

#: Hat forrás, szándékosan vegyes oldaránnyal: fekvő, álló, négyzetes.
#: Egyforma arányoknál a Rács és a Mozaik véletlenül egybeeshetne.
ASPEKTUSOK = (4 / 3, 3 / 4, 1.0, 16 / 9, 1.0, 2 / 3)
UTAK = tuple(f"/kepek/{index}.jpg" for index in range(len(ASPEKTUSOK)))

LAP_SZELESSEG = 1024
LAP_MAGASSAG = 768


def _beallitas(tema: str, **extra) -> PicasaCollageSettings:
    return PicasaCollageSettings(
        theme=tema,
        width=LAP_SZELESSEG,
        height=LAP_MAGASSAG,
        seed=7,
        **extra,
    )


def _csomopontok(tema: str, **extra):
    return layout_nodes_for_aspects(
        ASPEKTUSOK, UTAK, _beallitas(tema, **extra)
    )


def _geometria(nodes) -> tuple:
    """Az elrendezés UJJLENYOMATA: a csomópont-dobozok rendezve.

    Rendezve, mert az állítás az ELRENDEZÉSRŐL szól, nem a rétegsorrendről
    — két téma akkor is különbözik, ha csak más sorrendben rakja ki
    ugyanazokat a dobozokat, de a fordítottja (ugyanaz a geometria más
    sorrendben) nem számít különbségnek."""
    return tuple(
        sorted(
            (
                round(node.center_x, 1),
                round(node.center_y, 1),
                round(node.width, 1),
                round(node.height, 1),
                round(node.theta, 4),
            )
            for node in nodes
        )
    )


class TestAzOldalaranyIllesztő:
    """A panel csak az INDEX oldalarányát ismeri, a rajzoló a dekódolt
    képet — ugyanaz a doboz kell, hogy kijöjjön mindkettőből."""

    @pytest.mark.parametrize("cel", [(320, 240), (1024, 768), (37, 91), (500, 500)])
    def test_ugyanazt_adja_mint_a_kepmeretes_valtozat(self, cel):
        cel_w, cel_h = cel
        for forras_w in (13, 80, 400, 1600, 4000):
            for forras_h in (9, 60, 300, 1200, 3000):
                assert fit_aspect_inside(
                    forras_w / forras_h, cel_w, cel_h
                ) == fit_inside(forras_w, forras_h, cel_w, cel_h), (
                    forras_w,
                    forras_h,
                    cel,
                )

    def test_az_ervenytelen_bemenet_hangosan_szol(self):
        with pytest.raises(ValueError):
            fit_aspect_inside(0.0, 100, 100)
        with pytest.raises(ValueError):
            fit_aspect_inside(1.0, 0, 100)


class TestHatKulonbozoElrendezes:
    def test_mind_a_hat_temanak_van_csomopont_elrendezese(self):
        for tema in COLLAGE_THEMES:
            nodes = _csomopontok(tema, frame_center=1)
            assert len(nodes) == len(ASPEKTUSOK), tema
            assert all(
                node.width > 0.0
                and node.height > 0.0
                and math.isfinite(node.center_x)
                and math.isfinite(node.center_y)
                for node in nodes
            ), tema

    def test_a_hat_tema_hat_kulonbozo_geometriat_ad(self):
        """A jegy MÉRCÉJE: ugyanazokra a forrásokra hat eltérő elrendezés.

        A Képkockamozaik rögzített képpel szerepel — enélkül az eredeti is
        az alap (Mozaik-)pakolóra esik vissza, tehát jogosan azonos."""
        ujjlenyomatok = {
            tema: _geometria(_csomopontok(tema, frame_center=1))
            for tema in COLLAGE_THEMES
        }
        for egyik in COLLAGE_THEMES:
            for masik in COLLAGE_THEMES:
                if egyik >= masik:
                    continue
                assert ujjlenyomatok[egyik] != ujjlenyomatok[masik], (
                    f"{egyik} és {masik} UGYANAZT az elrendezést adja"
                )

    def test_ures_forrasnal_ures_lista(self):
        for tema in COLLAGE_THEMES:
            assert layout_nodes_for_aspects((), (), _beallitas(tema)) == []


class TestRacs:
    """A Rács SZABÁLYOS: egyforma cellák, egyenletes lépésköz."""

    def test_egyforma_cellak_egyenletes_racsban(self):
        """A cellák egyformák — EGY képpont tűréssel: a cellahatárok egész
        képpontra kerekednek (`picasa_round`), tehát 1024 / 3 osztásnál a
        341 és a 342 váltakozik. Ez az eredeti viselkedése, nem hiba."""
        nodes = _csomopontok(REGULARGRID)
        szelessegek = [node.width for node in nodes]
        magassagok = [node.height for node in nodes]
        assert max(szelessegek) - min(szelessegek) <= 1.5, "a cellák nem egyformák"
        assert max(magassagok) - min(magassagok) <= 1.5

        oszlopok = sorted({round(node.center_x, 1) for node in nodes})
        sorok = sorted({round(node.center_y, 1) for node in nodes})
        assert len(oszlopok) * len(sorok) >= len(ASPEKTUSOK)
        for tengely in (oszlopok, sorok):
            lepesek = [b - a for a, b in zip(tengely, tengely[1:], strict=False)]
            for lepes in lepesek:
                assert lepes == pytest.approx(lepesek[0], abs=1.5)

    def test_a_racs_nem_log_le_a_laprol(self):
        nodes = _csomopontok(REGULARGRID)
        assert all(node.center_x - node.width / 2 >= -1.0 for node in nodes)
        assert all(node.center_y - node.height / 2 >= -1.0 for node in nodes)
        assert all(
            node.center_x + node.width / 2 <= 1024.0 + 1.0 for node in nodes
        )


class TestIndexkep:
    """Az Indexkép a fejlécsáv ALATT kezdődik — ez különbözteti a Rácstól."""

    def test_a_fejlecsav_alatt_kezdodik(self):
        nodes = _csomopontok(CONTACTSHEET)
        # a sáv a lap magasságának 8%-a, lapegységben ugyanennyi képpont
        # (a lap 1024 egység SZÉLES, tehát az osztó itt 1,0)
        sav = round(LAP_MAGASSAG * 0.08)
        assert min(node.center_y - node.height / 2 for node in nodes) >= sav - 1.0

    def test_lejjebb_ul_mint_a_racs(self):
        indexkep = _csomopontok(CONTACTSHEET)
        racs = _csomopontok(REGULARGRID)
        assert min(n.center_y for n in indexkep) > min(n.center_y for n in racs)


class TestTobbszorosExponalas:
    """A Többszörös exponálás nem HELYEZ el: mindent a lap közepére tesz."""

    def test_minden_kep_a_lap_kozepen_all(self):
        nodes = _csomopontok(MULTIEXP)
        assert {(round(n.center_x, 1), round(n.center_y, 1)) for n in nodes} == {
            (512.0, 384.0)
        }

    def test_minden_kep_a_lapra_van_igazitva(self):
        nodes = _csomopontok(MULTIEXP)
        for node in nodes:
            assert node.width <= 1024.0 + 1.0
            assert node.height <= 768.0 + 1.0
            # a hosszabbik oldal FELÜL ül a lapon (illesztés, nem zsugorítás)
            assert node.width >= 1024.0 - 2.0 or node.height >= 768.0 - 2.0


class TestKepkockamozaik:
    """A rögzített kép a lap közepére, hangsúlyos méretben."""

    def test_a_rogzitett_kep_kozepre_es_legfelulre_kerul(self):
        nodes = _csomopontok(FRAMEGRID, frame_center=1)
        hangsulyos = nodes[-1]  # a lista VÉGE a legfelső réteg
        assert hangsulyos.path == UTAK[1]
        assert hangsulyos.center_x == pytest.approx(512.0, abs=2.0)
        assert hangsulyos.center_y == pytest.approx(384.0, abs=2.0)
        assert hangsulyos.width == pytest.approx(512.0, abs=2.0)

    def test_rogzites_nelkul_az_alap_pakolora_esik_vissza(self):
        """Az eredeti is ezt teszi (`CLocationTree` csak KIEGÉSZÍTI a
        pakolót) — a két téma ilyenkor jogosan egyforma szerkezetű."""
        nodes = _csomopontok(FRAMEGRID)
        assert [node.path for node in nodes] == list(UTAK)


class TestMozaik:
    def test_a_cellak_kitoltik_a_lapot(self):
        """A pakoló időkorlátos keresés, tehát a PONTOS cellák nem
        jósolhatók — az viszont igen, hogy hézagmentesen kitöltik a lapot."""
        nodes = _csomopontok(PICTUREGRID)
        terulet = sum(node.width * node.height for node in nodes)
        assert terulet == pytest.approx(1024.0 * 768.0, rel=0.02)


class TestATerkozMindketTajolasban:
    """A térköz `a = W/H` szorzója — a felhasználó nyolc golden-kollázsa
    (2026-08-19) ezt méréssel igazolta, három témán (Mozaik, Képkockamozaik,
    Rács), és korábban a 2014-es naptáron két ellentétes tájolásban is.

    ## Mit állít ez, és miért pont ezt

    A szorzó a `rects.to_pixel_rects`-ben KIZÁRÓLAG a függőleges réseket
    skálázza (`rects.py:106-107`). Ennek egyetlen értelme van: hogy a rés
    **képpontban mérve** vízszintesen és függőlegesen EGYFORMA legyen —
    normalizált koordinátában ugyanaz a szám álló és fekvő lapon más
    képpontnyi távolság.

    Ezért a teszt nem a szorzót olvassa vissza (az a képlet ismétlése
    volna), hanem a **következményét** méri: a csempék közti tényleges
    képpont-rés. És mindkét tájolásban méri — ha valaki a szorzót
    elhagyja, vagy a VÍZSZINTESRE teszi, az egyik tájolás azonnal elromlik,
    a másik akár helyes is maradhat. Egytájolású teszt ezt átengedné.
    """

    #: két cella egymás mellett és egymás alatt — a négy szomszédos rés
    #: mindegyike mérhető rajta
    _RECTS = (
        rects.NormRect(0.0, 0.0, 0.5, 0.5),
        rects.NormRect(0.5, 0.0, 1.0, 0.5),
        rects.NormRect(0.0, 0.5, 0.5, 1.0),
        rects.NormRect(0.5, 0.5, 1.0, 1.0),
    )

    @pytest.mark.parametrize(
        "szelesseg,magassag,tajolas",
        [(1600, 1200, "fekvő"), (1200, 1600, "álló"), (1500, 1500, "négyzetes")],
    )
    def test_a_res_kepponban_egyforma_vizszintesen_es_fuggolegesen(
        self, szelesseg, magassag, tajolas
    ):
        dobozok = rects.to_pixel_rects(self._RECTS, szelesseg, magassag, 0.5)
        bal_felso, jobb_felso, bal_also = dobozok[0], dobozok[1], dobozok[2]

        vizszintes_res = jobb_felso.x0 - bal_felso.x1
        fuggoleges_res = bal_also.y0 - bal_felso.y1

        assert vizszintes_res > 0 and fuggoleges_res > 0, (
            f"{tajolas}: nincs rés a csempék közt — a térköz nem hatott"
        )
        # a kerekítés (`picasa_round`) miatt 1 képpont eltérés megengedett
        assert abs(vizszintes_res - fuggoleges_res) <= 1, (
            f"{tajolas} ({szelesseg}×{magassag}): a rés NEM egyforma — "
            f"vízszintes {vizszintes_res} px, függőleges {fuggoleges_res} px. "
            "Ez az `a = W/H` szorzó hiánya vagy rossz tengelyre tétele."
        )

    def test_nulla_terkoznel_nincs_res_egyik_tajolasban_sem(self):
        for szelesseg, magassag in ((1600, 1200), (1200, 1600)):
            dobozok = rects.to_pixel_rects(self._RECTS, szelesseg, magassag, 0.0)
            assert dobozok[1].x0 == dobozok[0].x1
            assert dobozok[2].y0 == dobozok[0].y1
