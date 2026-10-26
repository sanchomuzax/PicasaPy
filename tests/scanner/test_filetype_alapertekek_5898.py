"""#5898 — a tiszta profil fájltípusai a regisztrált Picasa-alapértékeket követik."""

from PySide6.QtCore import QSettings

from picasapy.app.filetype_preferences import enabled_filetypes
from picasapy.index import open_index, sync_tree


def test_tiszta_profilban_png_kimarad_engedelyezes_utan_indexelodik(tmp_path):
    from PIL import Image

    root = tmp_path / "kepek"
    folder = root / "mappa"
    folder.mkdir(parents=True)
    kep = Image.new("RGB", (12, 8), (30, 80, 140))
    for extension, image_format in (("gif", "GIF"), ("png", "PNG"), ("tga", "TGA")):
        kep.save(folder / f"kep.{extension}", format=image_format)

    settings = QSettings(str(tmp_path / "profil.ini"), QSettings.Format.IniFormat)
    index_path = tmp_path / "index.db"

    with open_index(index_path) as conn:
        # Üres QSettings-fájl = tiszta profil; az alkalmazás beállításadaptere
        # adja át a szkennereknek a csoportok aktuális állapotát.
        sync_tree(
            conn,
            root,
            incremental=False,
            enabled_filetypes=enabled_filetypes(settings),
        )
        fajlnevek = {
            row["name"] for row in conn.execute("SELECT name FROM photos").fetchall()
        }
        assert fajlnevek == set(), "a GIF, PNG és TGA tiszta profilban kimarad"

        # Egy korábban elmentett, nem alapértelmezett választás maradjon élő.
        settings.setValue("library/fileTypes/gif", True)
        sync_tree(
            conn,
            root,
            incremental=False,
            enabled_filetypes=enabled_filetypes(settings),
        )
        fajlnevek = {
            row["name"] for row in conn.execute("SELECT name FROM photos").fetchall()
        }
        assert fajlnevek == {"kep.gif"}
        settings.sync()
        assert settings.value("library/fileTypes/gif", type=bool) is True

        settings.setValue("library/fileTypes/gif", False)
        settings.setValue("library/fileTypes/png", True)
        sync_tree(
            conn,
            root,
            incremental=False,
            enabled_filetypes=enabled_filetypes(settings),
        )
        fajlnevek = {
            row["name"] for row in conn.execute("SELECT name FROM photos").fetchall()
        }

    assert fajlnevek == {"kep.png"}
