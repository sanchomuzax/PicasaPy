"""A vászon állapotából `.cxf` piszkozat — a hiányzó hívó (#960).

A #431 megadta a `.cxf` írását és a piszkozat életciklusát, a #942 pedig a
csomópont-geometriát (`CollageNode`, `render_nodes`). Ez a lap a KETTŐ
KÖZÖTTI leképezést és a lemezre került fájl TARTALMÁT állítja.

⚠️ A jegy kifejezetten kimondja: a KIMENETET kell ellenőrizni. Ezért a lap
gerince az a teszt, amelyik valódi képekből elrendezést számol, kirajzolja
(`render_nodes`), a rajzolt vászon csomópontjaiból piszkozatot ír a
lemezre, majd a FÁJLBÓL visszaolvasva veti össze a szögeket és a
geometriát a vászonéval. Egy „meghívtuk a függvényt" jellegű állítás pont
azt nem fogná meg, ami a #431-nél gond volt: hogy a piszkozat kitalált
geometriát tartalmaz.
"""

from __future__ import annotations

from pathlib import Path

import math

import cv2
import numpy as np
import pytest

from picasapy.collage.autosave import read_autosave, write_autosave
from picasapy.collage.cxf import CxfNode, CxfProject, loads
from picasapy.collage.draft import (
    aspect_ratio_text,
    collage_node_of,
    cxf_node_of,
    nodes_from_project,
    orientation_of,
    page_ratio_of,
    project_from_nodes,
)
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    layout_nodes,
    make_picasa_collage,
    render_nodes,
)
from picasapy.collage.themes import (
    CONTACTSHEET,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    POLAROID,
)


# --- Segédek ----------------------------------------------------------------


def _mintakepek(mappa, darab=6):
    """Néhány „csúnya" méretű próbakép a lemezre (a kerekítés miatt)."""
    utak = []
    for i in range(darab):
        szeles, magas = 60 + i * 17, 40 + (i * 23) % 70
        kep = np.zeros((magas, szeles, 3), dtype=np.uint8)
        kep[:, :, i % 3] = 200
        ut = mappa / f"k{i}.png"
        assert cv2.imwrite(str(ut), kep)
        utak.append(ut)
    return utak


def _pile_beallitas(**csere) -> PicasaCollageSettings:
    alap = {
        "theme": PICTUREPILE,
        "border": POLAROID,
        "width": 640,
        "height": 480,
        "seed": 7,
    }
    alap.update(csere)
    return PicasaCollageSettings(**alap)


# --- Az oldalarány és a tájolás ---------------------------------------------


class TestOldalarany:
    def test_a_format_mindig_a_NAGYOBB_oldallal_kezdodik(self):
        """A minta `format="15:10"` + `orientation="portrait"` párosa (spec
        1.6): az arány szövege NEM forog a tájolással, a tájolás mondja meg,
        merre áll a lap."""
        assert aspect_ratio_text(1600, 1200) == "4:3"
        assert aspect_ratio_text(1200, 1600) == "4:3"
        assert orientation_of(1600, 1200) == "landscape"
        assert orientation_of(1200, 1600) == "portrait"

    def test_a_lap_aranya_a_formatumbol_es_a_tajolasbol(self):
        assert page_ratio_of("15:10", "portrait") == pytest.approx(1.5)
        assert page_ratio_of("15:10", "landscape") == pytest.approx(1 / 1.5)
        # értelmezhetetlen arány esetén sem omolhat össze a helyreállítás
        assert page_ratio_of("ide-oda", "landscape") > 0.0


# --- A mértékegységek (a jegy első teendője) --------------------------------


class TestMertekegysegek:
    def test_a_pozicio_a_BAL_FELSO_sarok_es_tengelyenkent_aranyos(self):
        """A `.cxf` a bal-felső sarkot tárolja, tengelyenként a vászon
        arányában (spec 1.6), a `CollageNode` viszont a KÖZÉPPONTOT
        lapegységben."""
        node = CollageNode(
            path="/x.jpg",
            center_x=512.0,
            center_y=256.0,
            width=256.0,
            height=128.0,
        )
        # fekvő 2:1 lap → a lap magassága 512 lapegység
        cxf_node = cxf_node_of(node, page_width=1024, page_ratio=0.5)
        assert cxf_node.x == pytest.approx((512.0 - 128.0) / SHEET_UNITS)
        assert cxf_node.w == pytest.approx(256.0 / SHEET_UNITS)
        assert cxf_node.y == pytest.approx((256.0 - 64.0) / (SHEET_UNITS * 0.5))
        assert cxf_node.h == pytest.approx(128.0 / (SHEET_UNITS * 0.5))

    def test_a_theta_valtozatlan_radian(self):
        node = CollageNode(path="/x.jpg", width=100.0, height=100.0, theta=-0.4)
        assert cxf_node_of(node, page_width=800, page_ratio=0.75).theta == -0.4

    def test_a_scale_KEPPONTBAN_a_befoglalo_negyzet_oldala(self):
        """A minta ezt dönti el: `w=0,274210`, `h=0,219401`, `scale=337`.

        Álló 15:10 lapon a csomópont doboza 0,274210·1024 = 280,8 ×
        0,219401·1536 = **337,0** lapegység — vagyis a `scale` a doboz
        NAGYOBBIK oldala képpontban (1024 képpont széles lapon), nem a
        szélessége. A Képkupacnál ez pontosan a `pile_size` négyzet oldala,
        amibe a csempe illeszkedik."""
        node = CollageNode(path="/x.jpg", width=280.8, height=337.0)
        cxf_node = cxf_node_of(node, page_width=1024, page_ratio=1.5)
        assert cxf_node.scale == pytest.approx(337.0, abs=0.1)

    def test_a_minta_csomopontja_visszafejtve(self):
        """A spec 1.6 valódi mintája: a mi olvasatunkkal a doboz nagyobbik
        oldala 337 lapegység — ugyanaz, amit a `scale` mond."""
        minta = CxfNode(
            x=0.297852,
            y=0.248047,
            w=0.274210,
            h=0.219401,
            theta=-0.009167,
            scale=337.0,
            theme=POLAROID,
        )
        node = collage_node_of(minta, page_ratio=1.5)
        assert node.width == pytest.approx(280.79, abs=0.05)
        assert node.height == pytest.approx(337.0, abs=0.05)
        assert max(node.width, node.height) == pytest.approx(minta.scale, abs=0.05)

    def test_oda_vissza_ugyanaz_a_csomopont(self):
        eredeti = CollageNode(
            path="/kep.jpg",
            center_x=333.25,
            center_y=180.5,
            width=210.5,
            height=140.25,
            theta=0.1234,
            border=POLAROID,
        )
        cxf_node = cxf_node_of(eredeti, page_width=1600, page_ratio=0.75)
        vissza = collage_node_of(cxf_node, page_ratio=0.75)
        assert vissza.center_x == pytest.approx(eredeti.center_x, abs=1e-3)
        assert vissza.center_y == pytest.approx(eredeti.center_y, abs=1e-3)
        assert vissza.width == pytest.approx(eredeti.width, abs=1e-3)
        assert vissza.height == pytest.approx(eredeti.height, abs=1e-3)
        assert vissza.theta == pytest.approx(eredeti.theta, abs=1e-6)
        assert vissza.border == POLAROID


# --- A projekt egésze --------------------------------------------------------


class TestProjekt:
    def test_a_beallitasok_atvezetese(self):
        beallitas = PicasaCollageSettings(
            theme=PICTUREGRID,
            width=1600,
            height=1200,
            background=(10, 20, 30),  # BGR!
            spacing=0.25,
        )
        node = CollageNode(path="/x.jpg", width=100.0, height=100.0)
        projekt = project_from_nodes([node], beallitas)
        assert projekt.theme == PICTUREGRID
        assert projekt.aspect_ratio == "4:3"
        assert projekt.orientation == "landscape"
        assert projekt.spacing == pytest.approx(0.25)
        # a `background` BGR, a `.cxf` ARGB nagybetűs hexa
        assert projekt.background.color == "FF1E140A"

    def test_a_szoveges_mezok_a_hivotol_jonnek(self):
        node = CollageNode(path="/x.jpg", width=10.0, height=10.0)
        projekt = project_from_nodes(
            [node], _pile_beallitas(), album_title="Nyaralás"
        )
        assert projekt.album_title == "Nyaralás"

    def test_a_kepenkenti_keret_a_csomopontbol_jon(self):
        """A `.cxf` meglepetése: a `<theme>` a `<node>`-on belül van."""
        nodes = [
            CollageNode(path="/a.jpg", width=10.0, height=10.0, border=POLAROID),
            CollageNode(path="/b.jpg", width=10.0, height=10.0, border=NOBORDER),
        ]
        projekt = project_from_nodes(nodes, _pile_beallitas())
        assert [n.theme for n in projekt.nodes] == [POLAROID, NOBORDER]

    def test_a_forras_utvonala_kimegy_a_fajlba(self):
        node = CollageNode(path="/képek/nyár.jpg", width=10.0, height=10.0)
        projekt = project_from_nodes([node], _pile_beallitas())
        assert projekt.nodes[0].src == "/képek/nyár.jpg"

    def test_a_projekt_oda_vissza_ugyanazokat_a_csomopontokat_adja(self):
        eredetiek = [
            CollageNode(
                path=f"/k{i}.jpg",
                center_x=100.0 + 37.5 * i,
                center_y=80.0 + 21.25 * i,
                width=120.0 + i,
                height=90.0 + i,
                theta=0.05 * (i - 2),
            )
            for i in range(4)
        ]
        beallitas = _pile_beallitas(border=NOBORDER)
        vissza = nodes_from_project(project_from_nodes(eredetiek, beallitas))
        assert len(vissza) == len(eredetiek)
        for uj, regi in zip(vissza, eredetiek, strict=True):
            assert uj.center_x == pytest.approx(regi.center_x, abs=1e-3)
            assert uj.center_y == pytest.approx(regi.center_y, abs=1e-3)
            assert uj.width == pytest.approx(regi.width, abs=1e-3)
            assert uj.height == pytest.approx(regi.height, abs=1e-3)
            assert uj.theta == pytest.approx(regi.theta, abs=1e-6)
            assert str(uj.path) == regi.path


# --- A KIMENET: a lemezre írt piszkozat tartalma ----------------------------


class TestKiirtPiszkozat:
    def test_a_kiirt_fajl_szogei_a_VASZON_szogei(self, tmp_path):
        """A jegy mércéje: a fájlból visszaolvasott csomópont-szögek
        egyeznek a KIRAJZOLT vászonéval."""
        utak = _mintakepek(tmp_path)
        kepek = [cv2.imread(str(ut)) for ut in utak]
        beallitas = _pile_beallitas()
        csomopontok = layout_nodes(kepek, utak, beallitas)
        vaszon = render_nodes(csomopontok, beallitas)
        assert vaszon.nodes == tuple(csomopontok), (
            "a rajzoló jelentése a TÉNYLEGESEN kirajzolt csomópontokat adja"
        )
        # az őrnek legyen foga: a Képkupac tényleg forgat
        assert any(abs(node.theta) > 1e-3 for node in csomopontok)

        mappa = tmp_path / "kollazsok"
        write_autosave(mappa, project_from_nodes(vaszon.nodes, beallitas))

        projekt = read_autosave(mappa)
        assert projekt is not None
        assert [n.theta for n in projekt.nodes] == pytest.approx(
            [n.theta for n in csomopontok], abs=1e-6
        )

    def test_a_visszaolvasott_geometria_a_vaszone(self, tmp_path):
        utak = _mintakepek(tmp_path)
        kepek = [cv2.imread(str(ut)) for ut in utak]
        beallitas = _pile_beallitas()
        csomopontok = layout_nodes(kepek, utak, beallitas)
        mappa = tmp_path / "kollazsok"
        write_autosave(mappa, project_from_nodes(csomopontok, beallitas))

        vissza = nodes_from_project(read_autosave(mappa))
        for uj, regi in zip(vissza, csomopontok, strict=True):
            assert uj.center_x == pytest.approx(regi.center_x, abs=1e-2)
            assert uj.center_y == pytest.approx(regi.center_y, abs=1e-2)
            assert uj.width == pytest.approx(regi.width, abs=1e-2)
            assert uj.height == pytest.approx(regi.height, abs=1e-2)
            assert uj.border == regi.border
            assert str(uj.path) == str(regi.path)

    def test_a_kiirt_fajl_valodi_cxf_marad(self, tmp_path):
        """CRLF, hat tizedes, `<collage>` gyökér — a #431 formátuma."""
        utak = _mintakepek(tmp_path, darab=2)
        kepek = [cv2.imread(str(ut)) for ut in utak]
        beallitas = _pile_beallitas()
        mappa = tmp_path / "kollazsok"
        cel = write_autosave(
            mappa,
            project_from_nodes(layout_nodes(kepek, utak, beallitas), beallitas),
        )
        adat = cel.read_bytes()
        assert adat.startswith(b'<?xml version="1.0" encoding="utf-8" ?>\r\n')
        assert b"\r\n" in adat and b"\n\n" not in adat
        assert isinstance(loads(adat), CxfProject)

    def test_a_make_picasa_collage_is_visszaadja_a_csomopontokat(self, tmp_path):
        """A vezérlő innen kapja a geometriát — enélkül csak kitalálni
        tudná."""
        utak = _mintakepek(tmp_path, darab=4)
        for tema in (PICTUREPILE, PICTUREGRID, CONTACTSHEET):
            jelentes = make_picasa_collage(utak, _pile_beallitas(theme=tema))
            assert len(jelentes.nodes) == len(utak), tema
            assert all(
                math.isfinite(n.center_x) and n.width > 0 for n in jelentes.nodes
            ), tema

    def test_a_tobbszoros_exponalasnak_IS_vannak_csomopontjai(self, tmp_path):
        """⚠️ Ez a teszt VISSZAFELÉ állt (#1248).

        Azt őrizte, hogy a `multiexp` piszkozata csomópont NÉLKÜLI, azzal
        az indoklással, hogy a téma nem helyez el képeket. A geometriára ez
        igaz — a `.cxf`-re NEM. Mérve az `AI7.cxf`-en (valódi Picasa-minta,
        `referencia/kollazs-golden/`): az eredeti **képenként EGY**
        csomópontot ír, mind azonos, teljes lapos geometriával.

        A hiánynak ára volt: a tulajdonos gépén (v0.8.45) a többszörös
        exponálású kollázs ÚJRASZERKESZTÉSKOR fekete lapot adott, mentéskor
        pedig azt jelentette, hogy „az összes képet eltávolították" — mert
        a `.cxf` tényleg nem tudta, MELYIK képekből készült."""
        utak = _mintakepek(tmp_path, darab=3)
        jelentes = make_picasa_collage(utak, _pile_beallitas(theme=MULTIEXP))

        assert len(jelentes.nodes) == len(utak)
        assert [n.path for n in jelentes.nodes] == [str(u) for u in utak]

    def test_a_multiexp_cxf_csomopontja_az_AI7_mintat_koveti(self, tmp_path):
        """A mért alak: `x=0 y=0 w=1 h=1 theta=0 scale=1`, `noborder`.

        A `scale` külön figyelmet érdemel: a #1071 mérte ki, hogy a nem
        szabványos `scale` a VALÓDI Picasát viszi szét szerkesztéskor
        (óriási, felnagyított töredékek). Az AI7 mintában `1.000000` áll."""
        utak = _mintakepek(tmp_path, darab=2)
        beallitas = _pile_beallitas(theme=MULTIEXP)
        jelentes = make_picasa_collage(utak, beallitas)

        projekt = project_from_nodes(jelentes.nodes, beallitas)

        assert len(projekt.nodes) == 2
        for csomopont in projekt.nodes:
            assert (csomopont.x, csomopont.y) == (0.0, 0.0)
            assert (csomopont.w, csomopont.h) == (1.0, 1.0)
            assert csomopont.theta == 0.0
            assert csomopont.scale == 1.0
            assert csomopont.theme == NOBORDER
            assert csomopont.src

    def test_a_multiexp_piszkozat_visszaolvasva_ugyanazokat_a_kepeket_adja(
        self, tmp_path
    ):
        """A tulajdonos tünete: fekete lap újraszerkesztéskor (#1248)."""
        utak = _mintakepek(tmp_path, darab=3)
        beallitas = _pile_beallitas(theme=MULTIEXP)
        jelentes = make_picasa_collage(utak, beallitas)

        vissza = nodes_from_project(project_from_nodes(jelentes.nodes, beallitas))

        assert [Path(n.path) for n in vissza] == [Path(u) for u in utak]
