"""#3120: a nyers (RAW) fájlok a TÖBBI képúton is megnyíljanak.

## A helyzet

A #528 a **megjelenítést** oldotta meg (`rawdecode.py`): a rács bélyegképe, a
néző és a mappaborító már a LibRaw-n megy. A többi képbetöltő viszont
`cv2.imdecode`-dal dolgozik, aminek **nincs nyers dekódere** — ott a nyers
fájl néma `None`.

⚠️ **Nem regresszió:** egyik sem működött korábban sem. A #528 óta viszont a
felhasználó LÁTJA a képet, tehát nekiindul ezeknek a műveleteknek — innentől
válik láthatóvá a hiány.

## Amit ez a lap mér

A közös belépőt (`cvimage.dekodolj_forrast`): ugyanaz a hívás adjon képet
JPEG-re és nyersre is, és a kicsinyítési cél (`goal`) mindkét ágon hasson.

⚠️ Amit NEM mér: a színhűséget. A generált DNG (`tests/support/raw_factory`)
hand-buildelt CFA-minta — azt méri, hogy a LIBRAW útja lefut és képet ad,
nem azt, hogy a szín pontos (ezt a saját docstringje is kimondja).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.cvimage import dekodolj_forrast
from support.jpeg_factory import make_jpeg
from support.raw_factory import ir_dng


@pytest.fixture
def jpeg(tmp_path):
    ut = tmp_path / "minta.jpg"
    make_jpeg(ut, size=(64, 48))
    return ut


@pytest.fixture
def dng(tmp_path):
    ut = tmp_path / "minta.dng"
    ir_dng(ut)
    return ut


class TestAKozosBelepo:
    def test_jpeg_kepet_ad(self, jpeg) -> None:
        kep = dekodolj_forrast(jpeg)
        assert kep is not None and kep.ndim == 3 and kep.shape[2] == 3

    def test_nyers_kepet_ad(self, dng) -> None:
        """⛳ EZ a jegy lényege: a nyers fájl ne néma `None` legyen."""
        kep = dekodolj_forrast(dng)
        assert kep is not None, (
            "a nyers fájl nem dekódolódott — a közös belépő nem ágazik el "
            "a LibRaw felé (#3120)"
        )
        assert kep.ndim == 3 and kep.shape[2] == 3
        assert kep.dtype == np.uint8

    def test_hianyzo_fajl_None(self, tmp_path) -> None:
        """Kontroll: a hiányzó forrás továbbra is `None`, nem kivétel."""
        assert dekodolj_forrast(tmp_path / "nincs.jpg") is None

    def test_serult_fajl_None(self, tmp_path) -> None:
        ut = tmp_path / "serult.jpg"
        ut.write_bytes(b"nem egy kep")
        assert dekodolj_forrast(ut) is None

    def test_serult_NYERS_None(self, tmp_path) -> None:
        """A kiterjesztés önmagában nem elég — a tartalom dönt."""
        ut = tmp_path / "serult.dng"
        ut.write_bytes(b"ez sem egy kep")
        assert dekodolj_forrast(ut) is None


class TestAKicsinyitesiCel:
    @pytest.mark.parametrize("forras", ["jpeg", "dng"])
    def test_a_goal_mindket_agon_hat(self, request, forras) -> None:
        """A `goal` a JPEG-nél a redukált dekódolást választja, a nyersnél a
        LibRaw fél-méretét — a hívónak egy felülete van rá."""
        ut = request.getfixturevalue(forras)
        teljes = dekodolj_forrast(ut)
        kicsi = dekodolj_forrast(ut, goal=16)
        assert teljes is not None and kicsi is not None
        assert max(kicsi.shape[:2]) <= max(teljes.shape[:2])


class TestAHivohelyekAtkotve:
    """A jegy kilenc helyet sorol; a lap a KETTŐT méri, amit a jegy
    elfogadási feltétele külön nevesít (export és duplikátum-kereső)."""

    def test_az_export_nyers_fajlt_is_kiir(self, tmp_path, dng) -> None:
        from picasapy.export import ExportItem, export_photos

        jelentes = export_photos([ExportItem(dng)], tmp_path / "ki")
        assert jelentes.exported, (
            f"a nyers fájl exportja elmaradt; hibák: {jelentes.failed}"
        )
        assert jelentes.exported[0].suffix == ".jpg"

    def test_a_duplikatum_kereso_ujjlenyomatot_ad(self, dng) -> None:
        from picasapy.dedup.phash import compute_dhash

        ujjlenyomat = compute_dhash(dng)
        assert ujjlenyomat is not None, (
            "a nyers fájlhoz nem készült dHash — a duplikátum-kereső "
            "kihagyja (#3120)"
        )


class TestAMentesNEMIrRaNyerset:
    """⛔ A kilencedik hely SZÁNDÉKOSAN kimarad — és ez őrzött döntés.

    A mentés a képet a SAJÁT HELYÉRE írja vissza. Nyers fájlnál ez nem megy
    (DNG/CR2/NEF írása nincs az OpenCV-ben), tehát az átkötés néma hibát vagy
    SÉRÜLT FÁJLT adna a felhasználó nyers képe helyén. Ma a dekódolás áll meg
    — a fájl érintetlen marad.

    Amit az eredeti tesz (a szerkesztést JPEG-ként a nyers MELLÉ menti), a
    jegy szerint MÉRENDŐ. Amíg nincs mérve, a biztonságos viselkedés a
    hibaüzenet — ezt rögzíti ez a lap, hogy senki ne „javítsa meg" az
    átkötéssel."""

    def test_a_nyers_fajl_mentese_HIBAVAL_all_meg(self, dng) -> None:
        from picasapy.app.save_controller import _render_for_save

        with pytest.raises(ValueError, match="Nem dekódolható"):
            _render_for_save(dng, rotate_steps=0, filters="", flip_flags=0)

    def test_a_nyers_fajl_ERINTETLEN_marad(self, dng) -> None:
        """A kontroll: a bukás előtt sem írunk bele."""
        from picasapy.app.save_controller import _render_for_save

        elotte = dng.read_bytes()
        with pytest.raises(ValueError):
            _render_for_save(dng, rotate_steps=0, filters="", flip_flags=0)
        assert dng.read_bytes() == elotte

    def test_a_JPEG_mentese_valtozatlanul_megy(self, jpeg) -> None:
        """Ellenpróba: a döntés csak a nyersre vonatkozik."""
        from picasapy.app.save_controller import _render_for_save

        kep = _render_for_save(jpeg, rotate_steps=0, filters="", flip_flags=0)
        assert kep is not None and kep.ndim == 3
