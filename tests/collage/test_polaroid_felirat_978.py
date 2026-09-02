"""#978 — a Polaroid-képfelirat MÉRT doboza, színe és betűmérete.

A felirat rajzolása a #942 óta megvan, de a **tipográfiája találgatás
volt**: fix `(60,60,60)` tinta, `sáv/44.0` betűméret, és a nem-Unicode
Hershey-betűkészlet (amitől a magyar ékezetek `?`-ként jelentek meg).

A mért értékek (`docs/specs/picasa-kollazs-felulet.md` 9/c):

* doboz a polaroid-kerethez normalizálva: x **0.098 … 0.902**,
  y **0.792 … 0.980** (`0xcf4e18`, `0xcf4e28`, `0xcf4e1c`, `0xcf4e20`);
* betűméret `(egész)(magasság × 14 / 360)` (`0x0080c510`, `0xcf3d50`);
* szín **ADAPTÍV** (`0x00887aff`–`0x00887b23`): világos háttéren
  `0xFF4A4A4A` = RGB(74,74,74), **sötét háttéren FEHÉR**. A küszöb
  komponensenként `0x7F`.

⚠️ Az adaptív szín a jegy TÖRZSÉBŐL hiányzott — csak a spec
helyesbítése tartalmazza. Fix szürkével sötét háttéren olvashatatlan
felirat lenne.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.collage.frames import polaroid_geometry
from picasapy.collage.nodes import (
    CAPTION_BOX,
    caption_font_px,
    caption_ink_bgr,
)


class TestDoboz:
    def test_a_MERT_normalizalt_doboz(self):
        assert CAPTION_BOX == pytest.approx((0.098, 0.792, 0.902, 0.980))

    def test_a_bal_es_a_jobb_margo_EGYENLO(self):
        bal, _, jobb, _ = CAPTION_BOX
        assert bal == pytest.approx(1.0 - jobb, abs=1e-9)

    def test_a_doboz_a_foto_ALATT_kezdodik(self):
        """Önellenőrzés a specből: négyzetes fotónál a fotó alsó éle
        `(1+0,0725)/1,374 = 0,781`, a felirat 0,792-nél kezdődik."""
        g = polaroid_geometry(360, 360)
        foto_also_el = (g.photo_y + 360) / g.outer_height
        _, fent, _, _ = CAPTION_BOX
        assert foto_also_el < fent
        assert fent - foto_also_el < 0.05


class TestBetumeret:
    @pytest.mark.parametrize(
        "magassag,varhato",
        [(360, 14), (720, 28), (180, 7), (100, 3), (1000, 38)],
    )
    def test_a_MERT_keplet(self, magassag, varhato):
        """`(egész)(magasság × 14 / 360)` — csonkolás, nem kerekítés."""
        assert caption_font_px(magassag) == varhato

    def test_sosem_nulla(self):
        """Nagyon kicsi keretnél is olvasható marad — 0 képpontos betű
        néma eltűnés lenne."""
        assert caption_font_px(1) >= 1


class TestAdaptivSzin:
    def test_vilagos_hatteren_a_MERT_sotetszurke(self):
        assert caption_ink_bgr((255, 255, 255)) == (74, 74, 74)

    def test_sotet_hatteren_FEHER(self):
        """`0xB5B5B5 + 0x4A4A4A = 0xFFFFFF` — a spec zárt alakja.

        Fog: fix szürkével ez a teszt bukik, és a sötét hátterű kollázs
        felirata olvashatatlan lenne."""
        assert caption_ink_bgr((0, 0, 0)) == (255, 255, 255)

    @pytest.mark.parametrize("komponens", [0x7E, 0x00, 0x40])
    def test_a_kuszob_ALATT_feher(self, komponens):
        assert caption_ink_bgr((komponens,) * 3) == (255, 255, 255)

    @pytest.mark.parametrize("komponens", [0x7F, 0x80, 0xFF])
    def test_a_kuszobON_es_felette_sotetszurke(self, komponens):
        assert caption_ink_bgr((komponens,) * 3) == (74, 74, 74)


class TestRajzolas:
    def _csempe(self, felirat, hatter=(217, 217, 217)):
        from picasapy.collage.nodes import _draw_polaroid_caption

        g = polaroid_geometry(300, 300)
        tile = np.full((g.outer_height, g.outer_width, 3), hatter, dtype=np.uint8)
        _draw_polaroid_caption(tile, felirat, 300, 300)
        return tile, g

    def test_az_EKEZETES_felirat_is_kirajzolodik(self):
        """Fog: a Hershey-betűkészlet nem Unicode — „Ősz" helyett „?sz"-t
        rajzolt. A két írásmódnak KÜLÖNBÖZŐ képet kell adnia."""
        ekezetes, _ = self._csempe("Ősz")
        ekezet_nelkuli, _ = self._csempe("Osz")
        assert not np.array_equal(ekezetes, ekezet_nelkuli)

    def test_a_felirat_a_MERT_dobozon_BELUL_marad(self):
        tile, g = self._csempe("Nagyon hosszú képfelirat, ami kilógna")
        hatter = np.array((217, 217, 217), dtype=np.uint8)
        eltero = np.any(tile != hatter, axis=2)
        ys, xs = np.nonzero(eltero)
        assert len(xs) > 0, "semmi nem rajzolódott ki"
        bal, fent, jobb, lent = CAPTION_BOX
        assert xs.min() >= int(bal * g.outer_width) - 1
        assert xs.max() <= int(jobb * g.outer_width) + 1
        assert ys.min() >= int(fent * g.outer_height) - 1
        assert ys.max() <= int(lent * g.outer_height) + 1

    def test_ures_feliratnal_nem_rajzol(self):
        tile, _ = self._csempe("   ")
        assert np.all(tile == np.array((217, 217, 217), dtype=np.uint8))


class TestNegyKombinacio:
    """#978: a felirat KÉT feltételhez kötött — kapcsoló BE ÉS polaroid keret.

    Az eredetiben a `0x00839830` mindkettőt megnézi. Nálunk a rajzolási
    úton a KAPCSOLÓ eddig nem is szerepelt: kikapcsolva is látszott a
    felirat. Ez a négy eset zárja le.
    """

    def _vaszon(self, *, border, captions):
        from picasapy.collage.nodes import CollageNode, draw_nodes
        from picasapy.collage.themes import POLAROID, WHITEBORDER

        keret = POLAROID if border == "polaroid" else WHITEBORDER
        kep = np.full((120, 120, 3), (40, 90, 160), dtype=np.uint8)
        # ⚠️ A méretek LAPEGYSÉGBEN vannak (`SHEET_UNITS`), nem a lap
        # törtrészeként — 0,6 egy 1 képpontos csempét adna, és a teszt
        # némán mindig zöld lenne.
        from picasapy.collage.nodes import SHEET_UNITS

        node = CollageNode(
            path=None,
            center_x=SHEET_UNITS / 2,
            center_y=SHEET_UNITS / 2,
            width=SHEET_UNITS * 0.6,
            height=SHEET_UNITS * 0.6,
            theta=0.0,
            border=keret,
            caption="Ősz a kertben",
        )
        vaszon = np.full((600, 600, 3), 255, dtype=np.uint8)
        draw_nodes(vaszon, [node], [kep], 600, captions=captions)
        return vaszon

    def _van_sotet_szoveg(self, vaszon):
        """A mért tinta világos háttéren RGB(74,74,74) — ilyen sötét
        képpont sem a fehér vásznon, sem a `#D9D9D9` papíron, sem a kék
        fotón nem fordul elő."""
        return bool(np.any(np.all(np.abs(vaszon.astype(int) - 74) <= 12, axis=2)))

    def test_polaroid_ES_bekapcsolva_LATSZIK(self):
        assert self._van_sotet_szoveg(
            self._vaszon(border="polaroid", captions=True)
        )

    def test_polaroid_de_KIkapcsolva_nem_latszik(self):
        """Fog: e nélkül a kapcsoló néma volt — a felhasználó kikapcsolta,
        és a felirat továbbra is ott maradt a mentett képen."""
        assert not self._van_sotet_szoveg(
            self._vaszon(border="polaroid", captions=False)
        )

    def test_MAS_keret_bekapcsolva_sem_latszik(self):
        assert not self._van_sotet_szoveg(
            self._vaszon(border="feher", captions=True)
        )

    def test_MAS_keret_KIkapcsolva_sem_latszik(self):
        assert not self._van_sotet_szoveg(
            self._vaszon(border="feher", captions=False)
        )


class TestKapcsoloLanca:
    """#978: a kapcsoló a VEZÉRLŐTŐL a rajzolóig eljut.

    A négy kombináció a rajzolót méri; ez a lánc **bekötését**. Fog: ha
    valaki a `render_settings`-ből kifelejti a `captions`-t, a rajzoló az
    alapértékére (igaz) esik vissza, és a kapcsoló megint néma lesz — a
    tesztek pedig hamis zöldet adnának, mert külön-külön mind működik.
    """

    def _beallitas(self, captions):
        from picasapy.app.collage_output import render_settings

        return render_settings(
            theme="picturegrid",
            border="polaroid",
            spacing=0.0,
            shadows=False,
            page_ratio=1.0,
            background_rgb=(255, 255, 255),
            frame_center=-1,
            seed=1,
            width=400,
            captions=captions,
        )

    def test_a_kapcsolo_ATMEGY_a_render_beallitasba(self):
        assert self._beallitas(True).captions is True
        assert self._beallitas(False).captions is False

    def test_az_ALAPERTEK_bekapcsolt(self):
        """A meglévő hívók (és a `.cxf` visszatöltése) ne változzanak."""
        from picasapy.collage.picasa_render import PicasaCollageSettings

        assert PicasaCollageSettings().captions is True
