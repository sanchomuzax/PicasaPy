"""#3558: a Tulajdonságok panel Fehéregyensúly sora ismeretlen kódnál a szám.

Forrás: `docs/specs/picasa-metaadat-tulajdonsagok.md` 15. szakasz — a
`<WhiteBalance/>` elem (94-es kulcs = EXIF `0xa403`) értékformázója a
`0x009f3f00`: 0 → „Automatikus”, 1 → „Kézi”, minden más kód → maga a szám
(`%ld`). Hiányzó mezőnél a sor nem jelenik meg. Ugyanez a szabály, mint a
Tömörítés-soré (#3535).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QLocale

piexif = pytest.importorskip("piexif")


def _photo(folder, name):
    from types import SimpleNamespace

    return SimpleNamespace(
        name=name, folder_path=str(folder), size=1024, width=4, height=4,
        taken_at=None, kind="photo", keywords=(),
    )


def _sorok(tmp_path, kod):
    """A panel sorai egy `kod` fehéregyensúlyú (vagy mező nélküli) képre."""
    from PIL import Image

    from picasapy.app.formatting import properties_entries

    path = tmp_path / f"wb{kod}.jpg"
    Image.new("RGB", (4, 4), "red").save(path, "JPEG")
    exif_ifd = {piexif.ExifIFD.ISOSpeedRatings: 100}
    if kod is not None:
        exif_ifd[piexif.ExifIFD.WhiteBalance] = kod
    piexif.insert(piexif.dump({"Exif": exif_ifd}), str(path))
    return dict(
        properties_entries(_photo(tmp_path, path.name), QLocale("en"), lambda t: t)
    )


@pytest.mark.parametrize(
    ("kod", "vart"),
    [
        (0, "Auto"),
        (1, "Manual"),
        # ismeretlen kód → a szám (`%ld`), nem tűnik el a sor
        (2, "2"),
        (255, "255"),
    ],
)
def test_feheregyensuly_sor(tmp_path, kod, vart):
    assert _sorok(tmp_path, kod).get("White Balance") == vart


def test_hianyzo_mezonel_nincs_sor(tmp_path):
    sorok = _sorok(tmp_path, None)
    assert sorok.get("ISO") == "100"  # a kép EXIF-je beolvasódott
    assert "White Balance" not in sorok


def test_olvaso_az_ismeretlen_kodot_szamkent_adja(tmp_path):
    from PIL import Image

    from picasapy.metadata.reader import read_exif_details

    path = tmp_path / "wb.jpg"
    Image.new("RGB", (4, 4), "red").save(path, "JPEG")
    piexif.insert(
        piexif.dump({"Exif": {piexif.ExifIFD.WhiteBalance: 2}}), str(path)
    )
    assert read_exif_details(path).white_balance == "2"
