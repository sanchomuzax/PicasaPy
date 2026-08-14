"""A Google Earth-export végpontja: KML + bélyegképek (#530)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from picasapy.export.earth import (
    KML_FILE_NAME,
    THUMBS_DIR_NAME,
    export_google_earth,
)

KML_NS = "{http://earth.google.com/kml/2.0}"


@dataclass
class _Rekord:
    """A PhotoRecord-ból csak azt tartalmazza, amit az export használ."""

    path: str
    exif_lat: float | None = None
    exif_lon: float | None = None
    caption: str | None = None
    taken_at: str | None = None


def _kep(tmp_path: Path, nev: str, meret=(800, 600)) -> Path:
    utvonal = tmp_path / nev
    Image.new("RGB", meret, (120, 160, 200)).save(utvonal, "JPEG", quality=80)
    return utvonal


class TestGeocimkezettKepek:
    def test_kiirja_a_kml_t_es_a_belyegkepet(self, tmp_path: Path) -> None:
        forras = _kep(tmp_path, "budapest.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [_Rekord(str(forras), 47.5, 19.0, caption="Halászbástya")],
            cel,
            folder_name="Nyaralás",
        )

        assert jelentes.kml_path == cel / KML_FILE_NAME
        assert jelentes.kml_path.exists()
        assert jelentes.placemarks == 1
        belyegkepek = list((cel / THUMBS_DIR_NAME).glob("*.jpg"))
        assert len(belyegkepek) == 1

    def test_a_belyegkep_kisebb_az_eredetinel(self, tmp_path: Path) -> None:
        forras = _kep(tmp_path, "nagy.jpg", meret=(2000, 1500))
        cel = tmp_path / "earth"

        export_google_earth(
            [_Rekord(str(forras), 47.5, 19.0)], cel, folder_name="M",
            thumb_max_dimension=400,
        )

        with Image.open(next((cel / THUMBS_DIR_NAME).glob("*.jpg"))) as kep:
            assert max(kep.width, kep.height) <= 400

    def test_a_kml_a_belyegkepre_relativan_hivatkozik(self, tmp_path: Path) -> None:
        """A KML és a képek együtt mozognak — abszolút útvonal használhatatlan
        lenne egy másik gépen."""
        forras = _kep(tmp_path, "kep.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [_Rekord(str(forras), 47.5, 19.0)], cel, folder_name="M"
        )

        szoveg = jelentes.kml_path.read_text(encoding="utf-8")
        assert f"{THUMBS_DIR_NAME}/kep.jpg" in szoveg
        assert str(tmp_path) not in szoveg

    def test_a_felirat_nelkuli_kep_a_fajlnevet_kapja(self, tmp_path: Path) -> None:
        """Az eredeti `%CAPTION_OR_NAME%`-je: felirat, annak híján fájlnév."""
        forras = _kep(tmp_path, "IMG_0042.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [_Rekord(str(forras), 47.5, 19.0)], cel, folder_name="M"
        )

        gyoker = ET.fromstring(jelentes.kml_path.read_text(encoding="utf-8"))
        nev = gyoker.find(
            f"{KML_NS}Document/{KML_NS}Folder/{KML_NS}Placemark/{KML_NS}name"
        )
        assert nev.text == "IMG_0042.jpg"


class TestKoordinataNelkul:
    def test_a_koordinata_nelkuli_kep_kimarad(self, tmp_path: Path) -> None:
        geo = _kep(tmp_path, "geo.jpg")
        nemgeo = _kep(tmp_path, "nemgeo.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [_Rekord(str(geo), 47.5, 19.0), _Rekord(str(nemgeo))],
            cel,
            folder_name="M",
        )

        assert jelentes.placemarks == 1
        assert jelentes.skipped_without_location == 1

    def test_felig_hianyzo_koordinata_is_kimarad(self, tmp_path: Path) -> None:
        """Szélesség hosszúság nélkül nem hely — nem tehető a térképre."""
        felig = _kep(tmp_path, "felig.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [_Rekord(str(felig), exif_lat=47.5)], cel, folder_name="M"
        )

        assert jelentes.kml_path is None
        assert jelentes.skipped_without_location == 1

    def test_egyetlen_geocimkezett_kep_nelkul_nem_ir_fajlt(
        self, tmp_path: Path
    ) -> None:
        """Üres térképet exportálni félrevezető — a hívó a jelentésből tudja,
        mi történt."""
        forras = _kep(tmp_path, "a.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth([_Rekord(str(forras))], cel, folder_name="M")

        assert jelentes.kml_path is None
        assert jelentes.placemarks == 0
        assert not cel.exists() or not (cel / KML_FILE_NAME).exists()
