"""Az „Automatikus" képminőség = a FORRÁS kvantálási tábláinak átvétele (#1138).

Az eredeti levezetése: `docs/specs/export-parbeszed.md` 3.3 és 7.1. A
párbeszéd öt fokozata közül az „Automatikus" NEM egy szám: a
`0x00739c4d`-nél egy külön logikai jelző áll be (`[objektum+0xa40] = 1`),
és a kimenet a forrás JPEG-kvantálási tábláit veszi át. A tulajdonos
mérőszettjén a forrás és a Picasa exportjának DQT-je **bájtra azonos**,
miközben a fájlméret más — tehát tényleg újrakódolt.

A mérce ezért itt is a DQT: a kimeneti JPEG kvantálási táblái egyezzenek
a forráséval, MÉG AKKOR IS, ha a képet át kellett méretezni (vagyis a
bájthű másolás — `_is_noop_copy` — nem menti meg a helyzetet).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from picasapy.export import ExportItem, ExportSettings, export_photos


def _forras_jpeg(cel: Path, quality: int = 97, meret=(160, 120)) -> Path:
    """Determinisztikus, ZAJOS tesztkép — a sima felület minden minőségen
    ugyanazt a bájtsort adná, és a mérés nem mondana semmit."""
    zaj = (np.random.RandomState(1138).rand(meret[1], meret[0], 3) * 255).astype(
        "uint8"
    )
    Image.fromarray(zaj).save(cel, format="JPEG", quality=quality)
    return cel


def _dqt(path: Path) -> dict[int, list[int]]:
    with Image.open(path) as kep:
        return {index: list(tabla) for index, tabla in kep.quantization.items()}


class TestAutomatikusMinoseg:
    def test_ujrakodolasnal_is_a_forras_tablait_veszi_at(self, tmp_path):
        """A 7.1 mérése: a Picasa exportja MÁS méretű, de AZONOS DQT-jű.

        Átméretezést kérünk, hogy a bájthű másolás ága biztosan kimaradjon
        — különben a teszt akkor is zöld lenne, ha az „Automatikus" nem
        csinálna semmit."""
        forras = _forras_jpeg(tmp_path / "forras.jpg")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=forras)],
            cel,
            ExportSettings(max_dimension=80, quality_automatic=True),
        )

        assert jelentes.failed == (), jelentes.reasons
        (kimenet,) = jelentes.exported
        assert _dqt(kimenet) == _dqt(forras), (
            'az „Automatikus" nem vette át a forrás kvantálási tábláit'
        )
        with Image.open(kimenet) as kep:
            assert max(kep.size) == 80, "az átméretezés elmaradt"

    def test_a_nem_automatikus_fokozat_NEM_veszi_at(self, tmp_path):
        """Kontroll: enélkül nem tudnánk, hogy a fenti egyezés nem
        véletlen. A „Minimális" (65) tábláinak KÜLÖNBÖZNIÜK kell egy
        q=97-es forrásétól."""
        forras = _forras_jpeg(tmp_path / "forras.jpg")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=forras)],
            cel,
            ExportSettings(max_dimension=80, jpeg_quality=65),
        )

        (kimenet,) = jelentes.exported
        assert _dqt(kimenet) != _dqt(forras)

    def test_olvashatatlan_tablaknal_a_kozelites_marad(self, tmp_path):
        """Nem JPEG forrásnak nincs DQT-je — ilyenkor az export nem
        bukhat el, csak a közelítő értékre esik vissza."""
        forras = tmp_path / "forras.png"
        zaj = (np.random.RandomState(7).rand(40, 40, 3) * 255).astype("uint8")
        Image.fromarray(zaj).save(forras, format="PNG")
        cel = tmp_path / "ki"

        jelentes = export_photos(
            [ExportItem(source=forras)],
            cel,
            ExportSettings(quality_automatic=True),
        )

        assert jelentes.failed == (), jelentes.reasons
        assert len(jelentes.exported) == 1


class TestMinosegFeloldas:
    """A `resolve_export_quality` a fokozat NEVÉBŐL ad számot; az
    „Automatikus" külön jelző, ezért a hívónak külön kell megkérdeznie."""

    def test_az_automatikus_fokozat_felismerheto(self):
        from picasapy.export import is_automatic_quality

        assert is_automatic_quality("automatic") is True
        assert is_automatic_quality("Automatic") is True
        assert is_automatic_quality("normal") is False
        assert is_automatic_quality("custom") is False
        assert is_automatic_quality("") is False

    def test_a_nulla_csuszkaallas_egyre_emelkedik(self):
        """A 21 fogásos egyéni csúszka 0-s állása 0×5 = 0 minőséget adna;
        az IJG-kódoló a 0-t 1-re emeli (`if (quality <= 0) quality = 1`),
        ezért a mi leképezésünk sem dobhat kivételt rá."""
        from picasapy.export import resolve_export_quality

        assert resolve_export_quality("custom", 0) == 1
        assert resolve_export_quality("custom", 100) == 100
