"""#943: a kollázs-panel tiszta rétegei — elrendezés, beállítások, kimenet.

Ezek a modulok (`collage_layout`, `collage_prefs`, `collage_output`) Qt
nélkül futnak, ezért itt olyasmi is állítható, ami a vezérlőn át csak
körülményesen látszana — például hogy a háttérszín **BGR**-be fordul a
renderelőnek, vagy hogy egy sérült beállítás az alapértelmezésre esik.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from picasapy.app import collage_layout as layout
from picasapy.app import collage_output as output
from picasapy.app import collage_prefs as prefs
from picasapy.app.collage_model import CollageNode, initial_node_width
from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREPILE,
    REGULARGRID,
)


@dataclass
class _Photo:
    folder_path: str
    name: str
    caption: str | None = None
    width: int | None = 400
    height: int | None = 300


class _Settings:
    """Minimális QSettings-utánzat: csak `value(kulcs, alapérték)` kell."""

    def __init__(self, data=None):
        self._data = dict(data or {})

    def value(self, key, default=None):
        return self._data.get(key, default)


class TestForrasok:
    def test_a_savon_kivuli_sor_kimarad(self):
        photos = [_Photo("/kepek", "a.jpg")]
        # az elvárt útvonalat UGYANAZZAL a `Path`-szal állítjuk elő, amivel a
        # kód is: Windowson a `Path("/kepek") / "a.jpg"` visszaperjelet ad
        # (`\\kepek\\a.jpg`), a beégetett perjeles alak ott elbukna — a main
        # windows-lába pontosan ezen piroslott
        vart_ut = str(Path("/kepek") / "a.jpg")
        assert layout.sources_from_photos(photos, [0, 5, -1]) == (
            layout.CollageSource(vart_ut, "", pytest.approx(4 / 3)),
        )

    def test_a_hianyzo_meret_negyzetes(self):
        assert layout.aspect_of(None, None) == 1.0
        assert layout.aspect_of(0, 100) == 1.0
        assert layout.aspect_of("nem szám", 5) == 1.0

    def test_a_felirat_atjon(self):
        photos = [_Photo("/kepek", "a.jpg", "Nyár")]
        assert layout.sources_from_photos(photos, [0])[0].caption == "Nyár"


class TestElrendezes:
    # ⚠️ #989: a `laid_out` szignatúrája MEGVÁLTOZOTT. A régi alak
    # (`sources, page_ratio, border, rng`) nem ismert témát — a törzse
    # mindig a Képkupac szórását futtatta, ezért a panel téma-választója
    # nem hatott a vászonra. A véletlenforrás helyére a MAG került: a hat
    # pakoló közül több (Mozaik, Képkockamozaik) maga építi a generátorát,
    # tehát egy kívülről beadott, félig elhasznált `rng` értelmét vesztette.

    def test_a_kepkupac_negyzetbe_illeszt(self):
        """A darabszámból jövő méret a NÉGYZET oldala (`pile_size`), nem a
        csomópont szélessége — az álló és a fekvő kép így egyforma nagy."""
        from picasapy.collage.pile import pile_size

        sources = tuple(
            layout.CollageSource(f"/k/{i}.jpg", "", 1.0) for i in range(5)
        )
        nodes = layout.laid_out(sources, 0.75, NOBORDER, seed=1)
        for index, node in enumerate(nodes, start=1):
            # a kupacban a sorrendben hátrébb lévő kép KISEBB (1.9.2)
            assert max(node.width, node.height) == pytest.approx(
                pile_size(index, 1024), abs=1.0
            ), index
        # a fogantyú viszonyítási pontja a darabszámé (spec 6.2) — ez a
        # legkisebb, tehát az UTOLSÓ kép négyzete
        assert initial_node_width(5) == pytest.approx(pile_size(5, 1024), abs=1.0)

    def test_a_kozeppontok_a_lapon_belul_vannak(self):
        sources = tuple(
            layout.CollageSource(f"/k/{i}.jpg", "", 1.0) for i in range(6)
        )
        nodes = layout.laid_out(sources, 0.75, NOBORDER, seed=7)
        assert all(0.0 <= n.center_x <= 1024.0 for n in nodes)
        assert all(0.0 <= n.center_y <= 768.0 for n in nodes)

    def test_ures_forras_ures_lista(self):
        assert layout.laid_out((), 0.75, NOBORDER, seed=1) == ()

    def test_ugyanaz_a_mag_ugyanazt_az_elrendezest_adja(self):
        sources = (layout.CollageSource("/k/a.jpg", "", 1.0),)
        egy = layout.laid_out(sources, 1.0, NOBORDER, seed=42)
        ket = layout.laid_out(sources, 1.0, NOBORDER, seed=42)
        assert egy == ket

    def test_a_tema_MAS_elrendezest_ad(self):
        """A jegy magja: a `theme` tényleg eljut a pakolóig."""
        sources = tuple(
            layout.CollageSource(f"/k/{i}.jpg", "", 1.0 + i * 0.3) for i in range(5)
        )
        kupac = layout.laid_out(sources, 0.75, NOBORDER, theme=PICTUREPILE, seed=3)
        racs = layout.laid_out(sources, 0.75, NOBORDER, theme=REGULARGRID, seed=3)
        assert [(n.center_x, n.width) for n in kupac] != [
            (n.center_x, n.width) for n in racs
        ]

    def test_a_kep_oldalaranya_atmegy_a_csomopontra(self):
        """A rés doboza a rácsnál a CELLÁÉ — a kép arányát ezért külön mező
        őrzi, különben a következő újrarendezés torz arányokkal dolgozna."""
        sources = (layout.CollageSource("/k/a.jpg", "", 16 / 9),)
        for tema in (PICTUREPILE, REGULARGRID):
            nodes = layout.laid_out(sources, 0.75, NOBORDER, theme=tema, seed=1)
            assert nodes[0].aspect == pytest.approx(16 / 9), tema

    def test_a_kepkockakozeppont_a_lista_vegere_kerul(self):
        sources = tuple(
            layout.CollageSource(f"/k/{i}.jpg", "", 1.0) for i in range(4)
        )
        nodes = layout.laid_out(
            sources, 0.75, NOBORDER, theme=FRAMEGRID, frame_center=1, seed=5
        )
        assert nodes[-1].path == "/k/1.jpg"
        assert layout.frame_center_after(FRAMEGRID, 1, len(nodes)) == len(nodes) - 1
        # a többi témát a rögzítés nem rendezi át
        assert layout.frame_center_after(PICTUREPILE, 1, 4) == 1
        assert layout.layout_uses_frame_center(FRAMEGRID) is True
        assert layout.layout_uses_frame_center(PICTUREPILE) is False

    def test_a_szetszoras_a_meretet_nem_bantja(self):
        nodes = (
            CollageNode("/k/a.jpg", 1.0, 2.0, 300.0, 200.0, theta=0.3),
        )
        uj = layout.rescattered(nodes, 0.75, MsvcRandom(3))
        assert (uj[0].width, uj[0].height, uj[0].theta) == (300.0, 200.0, 0.3)
        assert (uj[0].center_x, uj[0].center_y) != (1.0, 2.0)


class TestBeallitasok:
    def test_ures_beallitasbol_alapertekek(self):
        p = prefs.load_prefs(_Settings())
        assert p.theme == PICTUREPILE
        assert p.format_key == "Desktop4x3"
        assert p.orientation == "landscape"
        assert p.captions is True
        assert p.shadows_explicit is False

    def test_az_arnyek_alapertelmezese_a_temabol(self):
        """Amíg a felhasználó nem nyúlt hozzá, a téma 14. bitje dönt."""
        assert prefs.load_prefs(_Settings()).shadows is True
        p = prefs.load_prefs(_Settings({prefs.THEME_KEY: MULTIEXP}))
        assert p.shadows is False and p.shadows_explicit is False

    def test_a_mentett_arnyek_ertek_szandekos(self):
        p = prefs.load_prefs(
            _Settings({prefs.THEME_KEY: CONTACTSHEET, prefs.SHADOWS_KEY: "false"})
        )
        assert p.shadows is False and p.shadows_explicit is True

    @pytest.mark.parametrize(
        "ertek,vart", [("true", True), ("1", True), ("0", False), ("hupsz", True)]
    )
    def test_a_jelzo_ertelmezese(self, ertek, vart):
        assert prefs.flag(ertek, True) is vart

    def test_serult_ertekek_alapertelmezesre_esnek(self):
        p = prefs.load_prefs(
            _Settings(
                {
                    prefs.THEME_KEY: "kollazs2000",
                    prefs.FORMAT_KEY: 17,
                    prefs.ORIENTATION_KEY: "átlós",
                }
            )
        )
        assert (p.theme, p.format_key, p.orientation) == (
            PICTUREPILE,
            "Desktop4x3",
            "landscape",
        )


class TestKimenet:
    def test_a_hatterszin_BGR_be_fordul(self):
        """A `PicasaCollageSettings.background` OpenCV-sorrendű; aki a
        fordítást kihagyja, kék helyett pirosat rajzol."""
        settings = output.render_settings(
            theme=PICTUREPILE,
            border=NOBORDER,
            spacing=0.0,
            shadows=True,
            page_ratio=0.75,
            background_rgb=(10, 20, 30),
            frame_center=-1,
            seed=1,
        )
        assert settings.background == (30, 20, 10)

    def test_a_magassag_a_lap_aranyabol(self):
        settings = output.render_settings(
            theme=PICTUREPILE,
            border=NOBORDER,
            spacing=0.0,
            shadows=False,
            page_ratio=0.5,
            background_rgb=(0, 0, 0),
            frame_center=-1,
            seed=1,
            width=1000,
        )
        assert (settings.width, settings.height) == (1000, 500)

    def test_a_minusz_egy_kepkockakozeppont_NINCS_rogzites(self):
        common = dict(
            theme=PICTUREPILE,
            border=NOBORDER,
            spacing=0.0,
            shadows=False,
            page_ratio=1.0,
            background_rgb=(0, 0, 0),
            seed=1,
        )
        assert output.render_settings(frame_center=-1, **common).frame_center is None
        assert output.render_settings(frame_center=2, **common).frame_center == 2

    # ⚠️ #949: ez a három eset ÁTÍRÓDOTT. A #943 időbélyeges nevet
    # (`kollázs-20260818-213005.jpg`) és `~/Pictures/Kollázsok` mappát
    # rögzített — a spec 9.1 táblája viszont mindkettőt TEENDŐKÉNT sorolja
    # fel („a `Picasa` közbülső szint pótlása", „cím-alapú név + `%s%lu`
    # számozás"). A régi teszt tehát a saját korábbi tévedésünket őrizte,
    # nem az eredeti viselkedést. A részletes állítások a
    # `test_collage_output_949.py`-ban élnek; itt a rétegre néző alap marad.

    def test_a_fajlnev_tove_a_CIM_ures_cimnel_kollazs(self, tmp_path):
        assert output.output_path(tmp_path, "Nyaralás").name == "Nyaralás.jpg"
        assert output.output_path(tmp_path, "").name == "kollázs.jpg"

    def test_ket_gyors_mentes_nem_irja_felul_egymast(self, tmp_path):
        egy = output.output_path(tmp_path, "Nyaralás")
        egy.write_bytes(b"")
        ket = output.output_path(tmp_path, "Nyaralás")
        assert egy != ket
        assert ket.name == "Nyaralás1.jpg"

    def test_a_celmappa_beallitasbol_vagy_alapertelmezesbol(self, tmp_path):
        assert output.output_dir(str(tmp_path)) == tmp_path
        # ⚠️ #1088: a gyökér a RENDSZER képmappája, nem `Path.home()/Pictures`.
        # A tulajdonosnál a Képek mappa OneDrive-ra volt átirányítva ÉS
        # honosított néven állt — emiatt a PicasaPy és a Picasa két külön
        # mappába dolgozott.
        assert output.output_dir(None) == (
            output.pictures_dir() / output.DEFAULT_OUTPUT_SUBPATH
        )
        assert output.DEFAULT_OUTPUT_SUBPATH.parts == ("Picasa", "Kollázsok")
