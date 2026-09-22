"""#3377: a keret két vastagsága az előnézeti aránnyal skálázódik, a
feliratsáv és a sarok-rádiusz NEM.

Az eredeti `BorderImageOperation` (`0x00bbe430`) a két vastagságot
`imageWidth / fullResImageWidth` tényezővel szorozza és csonkítja; a
`captionheight`-nál és a `cornerradius`-nál nincs szorzás
(`docs/specs/filterdesc-registry.md`, „A `Border` négy attribútumának
EGYSÉGE", C és F). A szerkesztő előnézete 2560 képpontnál hosszabb képet
kicsinyítve dekódol — eddig a keret ott nyers képpontban rajzolódott, tehát
az előnézeten arányaiban VASTAGABB volt, mint a mentett képen.
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtGui import QImage

from picasapy.ini import parse_filters
from picasapy.render import apply_filters
from picasapy.render.elonezeti_arany import elonezeti_arany, jelenlegi_arany

KERET = "Border=1,20,5,0,000000,ffffff,0;"
FELIRATOS = "Border=1,20,5,0,000000,ffffff,30;"
MUZEUM = "MuseumMatte=1,25,40,1a0e03,f0eae4;"


def _kep(szeles: int, magas: int) -> np.ndarray:
    return np.full((magas, szeles, 3), 128, dtype=np.uint8)


def _render(kep, lanc, arany=None):
    if arany is None:
        return apply_filters(kep, parse_filters(lanc))
    with elonezeti_arany(arany):
        return apply_filters(kep, parse_filters(lanc))


class TestAVastagsagSkalazodik:
    def test_teljes_felbontason_valtozatlan(self):
        kimenet = _render(_kep(400, 300), KERET).image
        assert kimenet.shape[:2] == (300 + 50, 400 + 50)

    def test_fel_aranyon_a_vastagsag_fele_csonkitva(self):
        # 20·0,5 = 10, 5·0,5 = 2,5 → 2 (csonkítás, nem kerekítés)
        kimenet = _render(_kep(200, 150), KERET, arany=0.5).image
        assert kimenet.shape[:2] == (150 + 24, 200 + 24)

    def test_a_feliratsav_NEM_skalazodik(self):
        teljes = _render(_kep(400, 300), FELIRATOS).image
        fel = _render(_kep(200, 150), FELIRATOS, arany=0.5).image
        # a felirat mindkét esetben 30 képpont a keret alatt
        assert teljes.shape[0] - teljes.shape[1] == (300 + 50 + 30) - (400 + 50)
        assert fel.shape[0] == 150 + 24 + 30

    def test_a_museummatte_vastagsaga_is_skalazodik(self):
        kimenet = _render(_kep(200, 150), MUZEUM, arany=0.5).image
        # 25·0,5 = 12,5 → 12; 40·0,5 = 20
        assert kimenet.shape[:2] == (150 + 64, 200 + 64)

    def test_a_tartalom_helye_a_skalazott_kerettel_szamol(self):
        """A geometria-számoló és a renderelő nem sodródhat el (#3166)."""
        jelentes = _render(_kep(200, 150), KERET, arany=0.5)
        hely = jelentes.content_placement
        assert hely is not None
        assert hely.szelesseg == pytest.approx(200 / 224, abs=1e-9)
        assert hely.magassag == pytest.approx(150 / 174, abs=1e-9)

    def test_a_blokk_utan_az_arany_visszaall(self):
        with elonezeti_arany(0.25):
            assert jelenlegi_arany() == 0.25
        assert jelenlegi_arany() == 1.0

    @pytest.mark.parametrize("rossz", [0.0, -1.0, float("nan"), float("inf")])
    def test_ervenytelen_aranynal_1_marad(self, rossz):
        with elonezeti_arany(rossz):
            assert jelenlegi_arany() == 1.0


def _keret_vastagsag(kep: np.ndarray) -> int:
    """A felső fekete sáv vastagsága a középső oszlopban (LÁTOTT mérés)."""
    oszlop = kep[:, kep.shape[1] // 2].astype(int).sum(axis=1)
    return int(np.argmax(oszlop > 60))


def test_az_elonezet_ugyanazt_a_keretet_MUTATJA_mint_a_mentett_kep():
    """A kicsinyítve mutatott mentett kép és az előnézet keretét a KÉPEN
    mérjük. Arány nélkül az előnézet kerete kétszer olyan vastag lenne."""
    teljes = _render(_kep(2000, 1500), KERET).image
    kicsinyitett = QImage(
        teljes.tobytes(), teljes.shape[1], teljes.shape[0], teljes.shape[1] * 3,
        QImage.Format.Format_RGB888,
    ).scaled(teljes.shape[1] // 2, teljes.shape[0] // 2)
    mutatott = np.frombuffer(
        kicsinyitett.convertToFormat(QImage.Format.Format_RGB888).constBits(), dtype=np.uint8
    ).reshape(kicsinyitett.height(), kicsinyitett.bytesPerLine())[:, : kicsinyitett.width() * 3]
    mutatott = mutatott.reshape(kicsinyitett.height(), kicsinyitett.width(), 3)

    elonezet = _render(_kep(1000, 750), KERET, arany=0.5).image
    arany_nelkul = _render(_kep(1000, 750), KERET).image

    assert _keret_vastagsag(mutatott) == 10
    assert _keret_vastagsag(elonezet) == 10
    assert _keret_vastagsag(arany_nelkul) == 20


@pytest.fixture
def nagy_jpeg(tmp_path):
    """4000 × 3000-es kép: a szerkesztő 2560-ra kicsinyítve dekódolja."""
    import cv2

    ut = tmp_path / "nagy.jpg"
    cv2.imwrite(str(ut), np.full((3000, 4000, 3), 128, dtype=np.uint8))
    return ut


@pytest.mark.parametrize("shared_cache", [True, False], ids=["gyorsitotar", "hatter"])
def test_a_szerkeszto_elonezete_az_arannyal_rajzolja_a_keretet(
    nagy_jpeg, shared_cache
):
    """Végponttól végpontig: 4000 → 2560 (arány 0,64). A keret 20·0,64 =
    12,8 → 12 és 5·0,64 = 3,2 → 3 képpont, tehát oldalanként 15 — nem 25."""
    from picasapy.app.edit_preview import EditPreviewProvider

    szolgaltato = EditPreviewProvider()
    szolgaltato.register("1", nagy_jpeg, parse_filters(KERET), shared_cache=shared_cache)
    kep = szolgaltato.requestImage("1", None, None)
    assert (kep.width(), kep.height()) == (2560 + 30, 1920 + 30)


def test_teljes_felbontasu_dekodnal_az_arany_1(nagy_jpeg):
    from picasapy.app.edit_preview import _elonezeti_arany

    forras = np.zeros((1920, 2560, 3), dtype=np.uint8)
    assert _elonezeti_arany(nagy_jpeg, 1.0, forras, False) == pytest.approx(0.64)
    assert _elonezeti_arany(nagy_jpeg, 1.0, forras, True) == 1.0
    assert _elonezeti_arany(nagy_jpeg.with_name("nincs.jpg"), 1.0, forras, False) == 1.0
