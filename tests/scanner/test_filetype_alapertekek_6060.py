"""#6060 — frissítés után egyetlen meglévő kép sem tűnhet el.

A v0.9.269 a GIF, PNG és TGA csoportot alapból kikapcsolta (#5898): akinél a
fájltípus-választás sosem volt elmentve, annál a frissítés után ezek a képek
némán kimaradtak a könyvtárból. Hiányzó beállításnál ezért minden csoport
bekapcsolt; csak az elmentett kikapcsolás szűr.
"""

from PySide6.QtCore import QSettings

from picasapy.app.filetype_preferences import enabled_filetypes, file_type_enabled
from picasapy.index import open_index, sync_tree
from picasapy.scanner.filetypes import FILETYPE_GROUPS


def _nevek(conn):
    return {row["name"] for row in conn.execute("SELECT name FROM photos")}


def test_hianyzo_beallitasnal_minden_csoport_bekapcsolt(tmp_path):
    settings = QSettings(str(tmp_path / "profil.ini"), QSettings.Format.IniFormat)
    assert all(file_type_enabled(settings, group) for group in FILETYPE_GROUPS)
    assert enabled_filetypes(settings) is None


def test_tiszta_profilban_png_gif_tga_indexelodik_elmentett_tiltas_szur(tmp_path):
    from PIL import Image

    root = tmp_path / "kepek"
    folder = root / "AI"
    folder.mkdir(parents=True)
    kep = Image.new("RGB", (12, 8), (30, 80, 140))
    formats = (("gif", "GIF"), ("png", "PNG"), ("tga", "TGA"), ("jpg", "JPEG"))
    for extension, image_format in formats:
        kep.save(folder / f"kep.{extension}", format=image_format)
    settings = QSettings(str(tmp_path / "profil.ini"), QSettings.Format.IniFormat)

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(
            conn, root, incremental=False, enabled_filetypes=enabled_filetypes(settings)
        )
        assert _nevek(conn) == {"kep.gif", "kep.png", "kep.tga", "kep.jpg"}

        settings.setValue("library/fileTypes/png", False)
        sync_tree(
            conn, root, incremental=False, enabled_filetypes=enabled_filetypes(settings)
        )
        assert _nevek(conn) == {"kep.gif", "kep.tga", "kep.jpg"}
