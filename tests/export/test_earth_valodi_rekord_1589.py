"""A Google Earth-export VALÓDI `PhotoRecord`-dal (#1589).

## A lelet

A #530 tesztjei duck-typed rekorddal dolgoztak (`_Rekord`: `path`,
`exif_lat`, `exif_lon`), és végig zöldek voltak — miközben a FUTÓ
alkalmazásban a funkció két okból sem működött:

1. a valódi `PhotoRecord`-nak **nincs `path` mezője** (`folder_path` +
   `name` van), ezért a háttérszál `AttributeError`-rel elhasalt;
2. a szűrés **csak az EXIF GPS-t** nézte, a PicasaPy saját geocímkéje
   viszont az `.picasa.ini` `geotag=` kulcsába kerül — aki a programban
   címkézte meg a képeit, üres exportot kapott.

Ez a fájl ezért SZÁNDÉKOSAN a valódi `PhotoRecord`-ot használja: a
teszt-dupla pontosan azt a két mezőt hozta magával, amitől a hiba
láthatatlan maradt.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from picasapy.export.earth import KML_FILE_NAME, export_google_earth
from picasapy.index import PhotoRecord


def _kep(mappa: Path, nev: str) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    utvonal = mappa / nev
    Image.new("RGB", (400, 300), (10, 120, 80)).save(utvonal, "JPEG", quality=80)
    return utvonal


def _rekord(mappa: Path, nev: str, **tobbi) -> PhotoRecord:
    return PhotoRecord(
        id=1,
        folder_path=str(mappa),
        name=nev,
        kind="image",
        size=1234,
        mtime_ns=0,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=400,
        height=300,
        **tobbi,
    )


class TestValodiPhotoRecord:
    def test_a_folder_path_es_name_parbol_megtalalja_a_fajlt(
        self, tmp_path: Path
    ) -> None:
        """`PhotoRecord`-nak nincs `path` mezője — ettől hasalt el a
        háttérszál (#1589)."""
        mappa = tmp_path / "kepek"
        _kep(mappa, "a.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [_rekord(mappa, "a.jpg", exif_lat=47.5, exif_lon=19.0)],
            cel,
            folder_name="Nyaralás",
        )

        assert jelentes.kml_path == cel / KML_FILE_NAME
        assert jelentes.placemarks == 1
        assert (cel / KML_FILE_NAME).exists()

    def test_az_INI_geocimke_is_a_terkepre_kerul(self, tmp_path: Path) -> None:
        """A PicasaPy saját geocímkéje az ini `geotag=` kulcsába megy — az
        EXIF-mezők ilyenkor ÜRESEK."""
        mappa = tmp_path / "kepek"
        _kep(mappa, "b.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [_rekord(mappa, "b.jpg", geotag="47.4979,19.0402")],
            cel,
            folder_name="Budapest",
        )

        assert jelentes.placemarks == 1, (
            "az ini-ben címkézett kép nem került a térképre"
        )
        assert jelentes.skipped_without_location == 0
        szoveg = (cel / KML_FILE_NAME).read_text(encoding="utf-8")
        # a KIÍRT literál a mérce, nem a termék konstansa
        assert "19.0402" in szoveg
        assert "47.4979" in szoveg

    def test_az_ini_cimke_ERŐSEBB_az_EXIF_nel(self, tmp_path: Path) -> None:
        """A `PhotoRecord.location` sorrendje: ini `geotag=` > EXIF GPS. Az
        exportnak ugyanezt kell adnia, különben a térkép és a rács
        geo-jelvényei szétcsúsznak."""
        mappa = tmp_path / "kepek"
        _kep(mappa, "c.jpg")
        cel = tmp_path / "earth"

        export_google_earth(
            [
                _rekord(
                    mappa,
                    "c.jpg",
                    geotag="47.4979,19.0402",
                    exif_lat=1.5,
                    exif_lon=2.5,
                )
            ],
            cel,
            folder_name="Budapest",
        )

        szoveg = (cel / KML_FILE_NAME).read_text(encoding="utf-8")
        assert "19.0402" in szoveg
        assert "2.5" not in szoveg, "az EXIF nyerte a `geotag=` fölött"

    def test_a_hely_nelkuli_kep_kimarad_es_MEGSZAMOLJUK(
        self, tmp_path: Path
    ) -> None:
        mappa = tmp_path / "kepek"
        _kep(mappa, "d.jpg")
        _kep(mappa, "e.jpg")
        cel = tmp_path / "earth"

        jelentes = export_google_earth(
            [
                _rekord(mappa, "d.jpg", geotag="47.4979,19.0402"),
                _rekord(mappa, "e.jpg"),
            ],
            cel,
            folder_name="Vegyes",
        )

        assert jelentes.placemarks == 1
        assert jelentes.skipped_without_location == 1
