"""#866: a hisztogram alatti EXIF-blokk a MÉRT hét formátumot követi.

A blokk pontosan hét formátum-sztringből épül (`il_NerdView::1..7`,
`docs/specs/picasa-hisztogram.md` 6.) — és a `0x00567e10` másoló is hét
mezőt mozgat, ami független megerősítés a hetes számra. Vaku NINCS köztük.

⚠️ A számok C-locale-ban (PONTTAL) jelennek meg: ez a mi ADR-004-es
döntésünk (a gép számai végig pontosak), nem az eredeti formátumából jön.
Amit ez az őr mér, az a TIZEDESJEGYEK SZÁMA és a mezők jelenléte.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QLocale

from picasapy.app.formatting import camera_summary_text, format_exposure

_QML = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "HistogramBox.qml"
).read_text(encoding="utf-8")


@dataclass
class _Exif:
    camera: str | None = None
    focal_mm: float | None = None
    focal_35mm: int | None = None
    exposure_seconds: float | None = None
    f_number: float | None = None
    iso: int | None = None
    flash_fired: bool | None = None


def _osszefoglalo(**mezok) -> str:
    return camera_summary_text(_Exif(**mezok), QLocale.c(), lambda s: s)


def _jobb_oszlop(szoveg: str) -> list[str]:
    return [sor.split("\t")[1] for sor in szoveg.split("\n") if "\t" in sor]


class TestATizedesjegyek:
    def test_a_fokusztavolsag_EGY_tizedes(self):
        """`%3.1f` — a korábbi `g`/4 `6.700`-at adott."""
        assert "Focal length: 6.7 mm" in _osszefoglalo(focal_mm=6.7)

    def test_a_kerek_fokusztavolsag_is_egy_tizedes(self):
        assert "Focal length: 24.0 mm" in _osszefoglalo(focal_mm=24.0)

    def test_a_rekesz_EGY_tizedes(self):
        """`f/%3.1f` — a korábbi `g`/3 `f/1.70`-et adott."""
        assert "f/1.7" in _osszefoglalo(f_number=1.7)
        assert "f/1.70" not in _osszefoglalo(f_number=1.7)

    def test_a_35mm_egyenertek_NULLA_tizedes(self):
        """`%3.0f` — egész."""
        assert "(35 mm equivalent: 24 mm)" in _osszefoglalo(focal_35mm=24)


class TestAZarido:
    def test_egy_masodperc_ALATT_egesz_nevezo(self):
        assert format_exposure(1 / 125, QLocale.c()) == "1/125 s"

    def test_egy_masodperc_FOLOTT_egy_tizedes(self):
        """`%2.1f s` — a korábbi `g`/3 `2.50`-et adott."""
        assert format_exposure(2.5, QLocale.c()) == "2.5 s"
        assert format_exposure(10.0, QLocale.c()) == "10.0 s"


class TestAzISO:
    def test_legalabb_ket_karakter_szeles(self):
        """`ISO: %2d` — a kis érték szóközzel töltődik."""
        assert "ISO:  8" in _osszefoglalo(iso=8)

    def test_a_nagyobb_erteket_nem_vagja(self):
        assert "ISO: 3200" in _osszefoglalo(iso=3200)


class TestAVakuSorNINCS:
    """A hét formátum között vaku NEM szerepel — a blokkba sem kerülhet."""

    @pytest.mark.parametrize("villant", [True, False])
    def test_a_vaku_nem_jelenik_meg(self, villant):
        szoveg = _osszefoglalo(iso=100, flash_fired=villant)
        assert "Flash" not in szoveg
        assert _jobb_oszlop(szoveg) == ["ISO: 100"]

    def test_a_vaku_a_TULAJDONSAGOKBAN_megmarad(self):
        """Az adat nem tűnt el: az eredetiben is ott van a tulajdonságok
        közt — csak a hisztogram-blokkból marad ki."""
        from picasapy.app import formatting

        forras = Path(formatting.__file__).read_text(encoding="utf-8")
        assert 'add("Flash"' in forras


class TestAKetOszlop:
    """A mért geometria: `detail1` 138 × 41, `detail2` 69 × 41, 6 px réssel —
    összesen 213, pontosan a hisztogram szélessége."""

    @pytest.mark.parametrize(
        "kotes",
        [
            "leftColumnWidth: 138",
            "columnGap: 6",
            "rightColumnWidth: 69",
            "height: 41",
            "y: 82",
        ],
    )
    def test_a_mert_geometria_a_forrasban_all(self, kotes):
        assert kotes in _QML

    def test_a_ket_oszlop_a_hisztogram_szelessege(self):
        assert 138 + 6 + 69 == 213

    def test_az_ures_allapot_szovege_PONTTAL_zarul(self):
        assert 'qsTr("No EXIF data available.")' in _QML


class TestASorpar:
    def test_a_ket_oszlop_kulon_sorokba_kerul(self):
        szoveg = _osszefoglalo(
            camera="Xiaomi Mi Note 10", focal_mm=6.7, focal_35mm=24,
            exposure_seconds=1 / 125, f_number=1.7, iso=3200,
        )
        sorok = [sor.split("\t") for sor in szoveg.split("\n")]
        assert [b for b, _ in sorok] == [
            "Xiaomi Mi Note 10", "Focal length: 6.7 mm",
            "(35 mm equivalent: 24 mm)",
        ]
        assert [j for _, j in sorok] == ["1/125 s", "f/1.7", "ISO: 3200"]

    def test_EXIF_nelkul_ures(self):
        assert _osszefoglalo() == ""
