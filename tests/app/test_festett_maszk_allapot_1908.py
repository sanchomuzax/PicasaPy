"""#1908: a festett ecset-maszk munkamenet-állapota.

A maszk **vonásokból** áll elő, nem kész bitképből: a felület a KIRAJZOLT
képhez normált koordinátákat ad, a bitkép a kért felbontáson születik. Így
ugyanaz a festés az előnézeten és a mentett képen ugyanoda esik — a
nagyítástól függetlenül.

Mérve (#1908): az eredeti Picasa a maszkot NEM tárolja (három telepítés
`db3`-ában nulla találat), ezért az állapot munkamenet-élettartamú, és
képváltásnál eldobódik.
"""

from __future__ import annotations

import numpy as np

from picasapy.app.paint_mask import (
    KEZDO_ARANY,
    MAX_ARANY,
    PEREM_ARANY,
    MaszkAllapot,
)


class TestUresAllapot:
    def test_festes_nelkul_NINCS_maszk(self):
        """`None`, nem nulla-tömb — így a hívó a maszk NÉLKÜLI útra mehet, és
        a lánc viselkedése bitre a régi marad."""
        allapot = MaszkAllapot()
        assert allapot.ures is True
        assert allapot.maszk(40, 60) is None

    def test_torles_utan_ismet_NINCS_maszk(self):
        allapot = MaszkAllapot()
        allapot.fess(0.5, 0.5, 0.1)
        assert allapot.maszk(40, 60) is not None
        allapot.torold()
        assert allapot.maszk(40, 60) is None


class TestFestes:
    def test_a_befestett_pont_KORUL_all_a_suly(self):
        allapot = MaszkAllapot()
        allapot.fess(0.25, 0.5, 0.1)
        maszk = allapot.maszk(40, 80)
        assert maszk is not None
        assert maszk[20, 20] > 0.99
        assert maszk[20, 75] == 0.0

    def test_a_KOR_alakja_allo_kepen_is_kor(self):
        """A sugár a RÖVIDEBB oldalhoz mérődik, tehát a folt nem lapul el."""
        allapot = MaszkAllapot()
        allapot.fess(0.5, 0.5, 0.2)
        maszk = allapot.maszk(100, 50)
        assert maszk is not None
        vizszintes = int((maszk[50, :] > 0.5).sum())
        fuggolegesen = int((maszk[:, 25] > 0.5).sum())
        assert abs(vizszintes - fuggolegesen) <= 2, (
            f"a folt nem kör: {vizszintes} × {fuggolegesen}"
        )

    def test_a_perem_LAGY(self):
        allapot = MaszkAllapot()
        allapot.fess(0.5, 0.5, 0.3)
        maszk = allapot.maszk(60, 60)
        assert maszk is not None
        koztes = maszk[(maszk > 0.05) & (maszk < 0.95)]
        assert koztes.size > 0, (
            f"nincs átmeneti sáv — a perem kemény (PEREM_ARANY={PEREM_ARANY})"
        )

    def test_a_koordinatak_0_1_re_vagodnak(self):
        allapot = MaszkAllapot()
        allapot.fess(-3.0, 9.0, 0.1)
        vonas = allapot.vonasok[0]
        assert 0.0 <= vonas.x <= 1.0 and 0.0 <= vonas.y <= 1.0

    def test_ket_vonas_osszeadodik(self):
        allapot = MaszkAllapot()
        allapot.fess(0.2, 0.5, 0.08)
        allapot.fess(0.8, 0.5, 0.08)
        maszk = allapot.maszk(50, 100)
        assert maszk is not None
        assert maszk[25, 20] > 0.9 and maszk[25, 80] > 0.9


class TestRadir:
    def test_a_radir_LEVONJA_a_sulyt(self):
        allapot = MaszkAllapot()
        allapot.fess(0.5, 0.5, 0.3)
        tele = allapot.maszk(60, 60)
        allapot.fess(0.5, 0.5, 0.15, torol=True)
        utana = allapot.maszk(60, 60)
        assert tele is not None and utana is not None
        assert tele[30, 30] > 0.9
        assert utana[30, 30] < 0.1, "a radír nem törölt a közepén"
        assert utana[30, 44] > 0.5

    def test_a_SORREND_szamit(self):
        """Aki később festett, az ír felül — a radír után újra festhetek."""
        allapot = MaszkAllapot()
        allapot.fess(0.5, 0.5, 0.3)
        allapot.fess(0.5, 0.5, 0.2, torol=True)
        allapot.fess(0.5, 0.5, 0.1)
        maszk = allapot.maszk(60, 60)
        assert maszk is not None and maszk[30, 30] > 0.9


class TestKepvaltas:
    def test_MAS_kepre_valtva_a_festes_eldobodik(self):
        allapot = MaszkAllapot()
        allapot.valts_kepre("a.jpg")
        allapot.fess(0.5, 0.5, 0.2)
        assert allapot.valts_kepre("b.jpg") is True
        assert allapot.ures is True

    def test_UGYANARRA_a_kepre_valtva_megmarad(self):
        """A felület sokszor újraköti ugyanazt a képet — az nem törölhet."""
        allapot = MaszkAllapot()
        allapot.valts_kepre("a.jpg")
        allapot.fess(0.5, 0.5, 0.2)
        assert allapot.valts_kepre("a.jpg") is False
        assert allapot.ures is False


class TestMertAlapertekek:
    def test_a_ket_mert_arany(self):
        """`BrushSizeAndEraserButton`: `startValueFactor` / `maximumFactor`."""
        assert KEZDO_ARANY == 0.03
        assert MAX_ARANY == 0.2

    def test_a_maszk_float32_es_0_1_kozott_all(self):
        allapot = MaszkAllapot()
        allapot.fess(0.5, 0.5, 0.2)
        maszk = allapot.maszk(30, 30)
        assert maszk is not None
        assert maszk.dtype == np.float32
        assert float(maszk.min()) >= 0.0 and float(maszk.max()) <= 1.0


class TestAzElonezetAtveszi:
    """#1908: az előnézet-szolgáltató a VONÁSOKAT kapja, és maga rasztereз.

    (A bitképet azért nem a vezérlő adja, mert az előnézet felbontása a
    dekódolástól függ — a vonás normált, tehát bármelyik méreten ugyanoda esik.)
    """

    def _kep(self, tmp_path):
        from picasapy.lazy_cv2 import cv2

        ut = tmp_path / "kep.jpg"
        kep = np.zeros((40, 60, 3), dtype=np.uint8)
        kep[..., 0] = 200
        kep[..., 1] = 120
        kep[..., 2] = 60
        sikeres, puffer = cv2.imencode(".jpg", kep)
        assert sikeres
        ut.write_bytes(puffer.tobytes())
        return ut

    def test_a_festes_CSAK_a_befestett_oldalt_valtoztatja(self, qt_app, tmp_path):
        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.app.paint_mask import Vonas
        from picasapy.ini.filters import parse_filters

        ut = self._kep(tmp_path)
        szolgaltato = EditPreviewProvider()
        ops = parse_filters("PicnikTint=1,0.000000,80cfff;")

        szolgaltato.register("1", ut, ops)
        nelkul = szolgaltato._images.get("1")
        assert nelkul is not None

        # a BAL felet festjük be (x = 0,25 körüli nagy folt)
        szolgaltato.register(
            "1", ut, ops, paint_strokes=(Vonas(0.25, 0.5, 0.35),)
        )
        maszkkal = szolgaltato._images.get("1")
        assert maszkkal is not None

        def kepont(kep, x, y):
            return kep.pixelColor(x, y).getRgb()[:3]

        # a jobb szél a maszk NÉLKÜLI esethez képest MÁS (ott nincs festés),
        # a bal oldal viszont mindkettőben effektezett
        assert kepont(nelkul, 58, 20) != kepont(maszkkal, 58, 20), (
            "a maszk nélküli hívás a TELJES képre futott — ez a régi, elvárt "
            "viselkedés; ha itt egyezik, a maszk nem hatott"
        )

    def test_vonas_nelkul_a_regi_ut_fut(self, qt_app, tmp_path):
        """Visszafelé kompatibilitás: üres vonás-sorozat = a mai viselkedés."""
        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.ini.filters import parse_filters

        ut = self._kep(tmp_path)
        ops = parse_filters("PicnikTint=1,0.000000,80cfff;")
        a = EditPreviewProvider()
        a.register("1", ut, ops)
        b = EditPreviewProvider()
        b.register("1", ut, ops, paint_strokes=())
        egyik, masik = a._images["1"], b._images["1"]
        assert egyik.size() == masik.size()
        assert egyik.pixelColor(30, 20) == masik.pixelColor(30, 20)
