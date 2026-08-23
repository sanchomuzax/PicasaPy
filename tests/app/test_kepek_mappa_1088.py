"""A Kollázsok mappa a RENDSZER képmappájában van (#1088) — P0.

## A lelet

A tulajdonos elküldte a valódi útvonalakat:

| | útvonal |
|---|---|
| **valódi Picasa** | `C:\\Users\\…\\OneDrive - …\\Képek\\Picasa\\Kollázsok` |
| **PicasaPy** | `C:\\Users\\…\\Pictures\\Picasa\\Kollázsok` |

**Nem tűnt el semmi — sosem volt közös mappa.**

A tulajdonos megfogalmazásában: *„Windows alatt az a Pictures mappa, ami
annak van jelölve a usernek. Nem találgat a Picasa, hanem a Windows
irányelveit elfogadja."*

Vagyis nem a mappa NEVE a kérdés, hanem hogy **a rendszer dönti el**,
melyik a képmappa — és az a döntés követi az átirányítást (nála OneDrive)
és a felhasználó saját beállítását is. A `Path.home() / "Pictures"` ezt
megkerülte.

Az eredeti a shelltől kérdezi (`SHGetSpecialFolderPathA/W`); a Qt
`QStandardPaths.PicturesLocation` ugyanezt az utat járja.

⚠️ **Ez súlyosabb, mint a #1076** (adat-/cache-mappa): ott a saját
adatbázisunk került nem szabványos helyre, itt a **felhasználó fájljai**.
Emiatt nem látta a PicasaPy-ben a Picasával készült kollázsait — és
fordítva.

## Amihez NEM nyúlunk

A `Picasa/Kollázsok` alszintek neve marad: a tulajdonos valódi útvonala is
így végződik, tehát ez egyezik. Csak a **gyökér** volt rossz.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths

from picasapy.app.collage_output import DEFAULT_OUTPUT_SUBPATH, output_dir


class TestAGyoker:
    def test_a_rendszer_kepmappajabol_indul(self):
        """⚠️ Ez a jegy: a `Path.home() / "Pictures"` nem követi sem az
        átirányítást, sem a honosított mappanevet."""
        vart = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.PicturesLocation
            )
        )

        assert output_dir(None).is_relative_to(vart)

    def test_az_alszintek_valtozatlanok(self, tmp_path, monkeypatch):
        """A tulajdonos valódi útvonala is `…/Picasa/Kollázsok`-ra végződik.

        ⚠️ #1131/#1217: a teszt korábban se a felület NYELVÉT, se a
        képmappát nem mondta ki. Zöld volt a fejlesztői gépen (magyar
        felület, létező `Kollázsok` mappa), a CI üres gépén viszont a
        nyers `Collages` jött — a mappanév ugyanis maga is honosított
        erőforrás. A `Picasa` közbülső szint az, ami valóban változatlan;
        a levél neve a felület nyelvéé."""
        from picasapy.app import collage_output

        kepek = tmp_path / "Kepek"
        kepek.mkdir()
        monkeypatch.setattr(collage_output, "pictures_dir", lambda: kepek)
        monkeypatch.setattr(collage_output, "_felulet_nyelve", lambda: "hu")

        assert DEFAULT_OUTPUT_SUBPATH == Path("Picasa") / "Kollázsok"
        assert output_dir(None).parts[-2:] == ("Picasa", "Kollázsok")

    def test_a_beallitott_mappa_tovabbra_is_eroesebb(self):
        """A „Move Database"-szerű felülbírálás nem sérülhet."""
        assert output_dir("/valahol/mashol") == Path("/valahol/mashol")
