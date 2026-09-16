"""#3166, 3. lépés — az átfedő rétegek a keret-leképezésen át kapják a helyüket.

A #819 `resizes` ágának utolsó darabja: a mérés (`chain_geometry`) és a
jelentés (`ChainReport.content_placement`) megvan, a FELÜLET viszont eddig a
keretezett kimenet teljes téglalapjára horgonyozta a vágás-téglalapot és az
arckereteket — vagyis a keret is „fénykép" volt nekik.

Amit itt mérünk:

* az előnézet-szolgáltató MEGJEGYZI az utolsó render keret-elhelyezését, és
  kérhető a fotó azonosítójával;
* a vezérlő `framePlacement`-je ezt adja tovább a QML-nek (keret nélkül
  `None`, tehát a rétegek a mai módon viselkednek);
* a `PhotoViewer.qml` a két réteget EGY közös, a leképezés szerint
  elhelyezett és elforgatott területbe teszi.

⚠️ A LÁTVÁNYT ez a teszt nem méri: hogy az arckeret a Polaroid-os képen
valóban a fejen áll, az a renderelt kimenethez mért próba
(`tests/render/test_keret_geometria_3166.py`) és a felület-geometria együtt
adja.
"""

from pathlib import Path

import numpy as np
import pytest

from picasapy.app.edit_preview import EditPreviewProvider
from picasapy.ini.filters import parse_filters

_QML = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"
)


@pytest.fixture
def kep(tmp_path):
    """800 × 600-as próbakép a lemezen — a szolgáltató fájlból dekódol."""
    import cv2

    ut = tmp_path / "proba.jpg"
    tomb = np.zeros((600, 800, 3), dtype=np.uint8)
    tomb[:, :] = (40, 80, 160)
    cv2.imwrite(str(ut), tomb)
    return ut


class TestSzolgaltato:
    def test_keretes_lancnal_megvan_a_hely(self, kep):
        szolgaltato = EditPreviewProvider()
        szolgaltato.register(
            "1", kep, parse_filters("Border=1,20,5,0,000000,ffffff,0")
        )
        hely = szolgaltato.frame_placement("1")
        assert hely is not None
        assert hely.szelesseg < 1.0
        assert hely.magassag < 1.0

    def test_keret_nelkul_nincs_hely(self, kep):
        szolgaltato = EditPreviewProvider()
        szolgaltato.register("1", kep, parse_filters("sepia=1;"))
        assert szolgaltato.frame_placement("1") is None

    def test_ismeretlen_fotora_nincs_hely(self):
        assert EditPreviewProvider().frame_placement("nincs-ilyen") is None

    def test_a_lezaras_elfelejti(self, kep):
        szolgaltato = EditPreviewProvider()
        szolgaltato.register(
            "1", kep, parse_filters("Border=1,20,5,0,000000,ffffff,0")
        )
        szolgaltato.unregister("1")
        assert szolgaltato.frame_placement("1") is None

    def test_a_keret_eltavolitasa_torli_a_helyet(self, kep):
        """A lánc visszavonása után a rétegek NE maradjanak eltolva."""
        szolgaltato = EditPreviewProvider()
        szolgaltato.register(
            "1", kep, parse_filters("Border=1,20,5,0,000000,ffffff,0")
        )
        szolgaltato.register("1", kep, ())
        assert szolgaltato.frame_placement("1") is None


class TestQmlAtfedok:
    @property
    def forras(self):
        return _QML.read_text(encoding="utf-8")

    def test_van_kozos_tartalom_terulet(self):
        assert 'objectName: "frameContentArea"' in self.forras

    def test_a_ket_reteg_a_kozos_teruletben_van(self):
        f = self.forras
        # a cropOverlay és a facesOverlay a közös területet kapja szülőnek
        assert f.count("parent: frameContentArea") >= 2

    def test_a_terulet_a_vezerlo_lekepezesebol_szamol(self):
        assert "editController.framePlacement" in self.forras

    def test_a_terulet_FORGAT(self):
        """A `Polaroid` szöget ad — a QML forgatásának ellentétes előjelű."""
        assert "rotation: hely ? -hely.szog : 0" in self.forras


# --- a QML-formula MÉRVE: a Polaroid alatt is a fejen marad az arckeret ----


class TestArckeretAPolaroidAlatt:
    """A jegy utolsó „Kész, ha" pontja: `Polaroid`-os láncnál az arckeret a
    helyén marad.

    A mérés a `tests/render/test_keret_geometria_3166.py` módszerét követi
    (gradiens háttér + egy teljes tengelyen átfutó, enyhe jelölő-sáv, a
    különbség-kép profiljának súlypontja) — de itt nem a renderelő mátrixát
    hasonlítjuk, hanem **azt a számítást, amit a `PhotoViewer.qml` végez** a
    `framePlacement` szótárból. Így a felületi formula is mérve van, nem
    csak átvezetve.

    ⚠️ A tűrés 2 képpont: a relatív koordináta `[0..1]` felbontása és a
    képpont-középpontok közti félképpontos eltérés ennyit megenged.
    """

    FORRAS_W, FORRAS_H = 800, 600
    SAV, SAV_X, SAV_Y, DELTA = 24, 300, 220, 18
    TURES_PX = 2.0
    LANC = "Polaroid=1,5,e2e2e2"

    def _hatter(self):
        fuggoleges = np.linspace(30, 220, self.FORRAS_H, dtype=np.float32)[:, None]
        vizszintes = np.linspace(-20, 20, self.FORRAS_W, dtype=np.float32)[None, :]
        szurke = np.clip(fuggoleges + vizszintes, 0, 255).astype(np.uint8)
        return np.dstack([szurke, szurke, szurke])

    def _forras(self, sav):
        kep = self._hatter()
        if sav == "vizszintes":
            resz = kep[self.SAV_Y : self.SAV_Y + self.SAV, :].astype(np.int16)
            kep[self.SAV_Y : self.SAV_Y + self.SAV, :] = np.clip(
                resz + self.DELTA, 0, 255
            )
        elif sav == "fuggoleges":
            resz = kep[:, self.SAV_X : self.SAV_X + self.SAV].astype(np.int16)
            kep[:, self.SAV_X : self.SAV_X + self.SAV] = np.clip(
                resz + self.DELTA, 0, 255
            )
        return kep

    def _mert(self, sav):
        from picasapy.render.chain import apply_filters

        ops = parse_filters(self.LANC)
        vel = apply_filters(self._forras(sav), ops)[0].astype(np.float64)
        nelkul = apply_filters(self._forras(None), ops)[0].astype(np.float64)
        elteres = np.abs(vel - nelkul).sum(axis=2)
        profil = elteres.sum(axis=1) if sav == "vizszintes" else elteres.sum(axis=0)
        suly = np.clip(profil - np.percentile(profil, 60), 0.0, None)
        assert suly.sum() > 0
        return float((np.arange(suly.size) * suly).sum() / suly.sum()), nelkul.shape

    def _hely(self, kep_ut):
        szolgaltato = EditPreviewProvider()
        szolgaltato.register("1", kep_ut, parse_filters(self.LANC))
        hely = szolgaltato.frame_placement("1")
        assert hely is not None
        return hely

    @staticmethod
    def _qml_pont(hely, kimenet_w, kimenet_h, rel_x, rel_y):
        """A `PhotoViewer.qml` `frameContentArea`-jának aritmetikája.

        A terület a kirajzolt képen belül ül (itt 1:1-ben a kimenet), a
        középpontja `(kozepX, kozepY)`, a mérete `(szelesseg, magassag)`, és
        `-szog` fokkal EL VAN FORGATVA (a QML `rotation`-je az óramutató
        járásával egyező, a renderelő szöge ellentétes).
        """
        import math

        terulet_w = hely.szelesseg * kimenet_w
        terulet_h = hely.magassag * kimenet_h
        # a réteg a területen belül relatív koordinátával rajzol
        dx = rel_x * terulet_w - terulet_w / 2.0
        dy = rel_y * terulet_h - terulet_h / 2.0
        theta = math.radians(-hely.szog)
        return (
            hely.kozep_x * kimenet_w + dx * math.cos(theta) - dy * math.sin(theta),
            hely.kozep_y * kimenet_h + dx * math.sin(theta) + dy * math.cos(theta),
        )

    def test_a_fuggoleges_jelolo_oda_kerul_ahova_a_felulet_rajzolna(self, kep):
        hely = self._hely(kep)
        mert_x, alak = self._mert("fuggoleges")
        rel_x = (self.SAV_X + (self.SAV - 1) / 2.0) / (self.FORRAS_W - 1)
        jos_x, _jos_y = self._qml_pont(hely, alak[1], alak[0], rel_x, 0.5)
        assert abs(jos_x - mert_x) <= self.TURES_PX, f"x {jos_x:.2f} ≠ {mert_x:.2f}"

    def test_a_vizszintes_jelolo_oda_kerul_ahova_a_felulet_rajzolna(self, kep):
        hely = self._hely(kep)
        mert_y, alak = self._mert("vizszintes")
        rel_y = (self.SAV_Y + (self.SAV - 1) / 2.0) / (self.FORRAS_H - 1)
        _jos_x, jos_y = self._qml_pont(hely, alak[1], alak[0], 0.5, rel_y)
        assert abs(jos_y - mert_y) <= self.TURES_PX, f"y {jos_y:.2f} ≠ {mert_y:.2f}"

    def test_kereten_KIVUL_a_mai_viselkedes(self, kep):
        """Keret nélkül a terület a teljes kirajzolt kép — a mai eset."""
        szolgaltato = EditPreviewProvider()
        szolgaltato.register("1", kep, parse_filters("sepia=1;"))
        assert szolgaltato.frame_placement("1") is None
