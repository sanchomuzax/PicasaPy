"""A gyári projekt-mappák honosított neve és a régi mappák felismerése (#1131).

## A tulajdonos képernyőképe

```
Projektek (4)
  Kollázsok (4)          <- a MI régi mappánk (#1088 előtt)
  Screen Captures (28)   <- angol nevű, korábbi Picasa
  Kollázsok (24)         <- a valódi Picasáé
  Képernyőfelvételek (170)
```

## A lelet — bizonyíték

A mappanév **maga is honosított erőforrás**: `Scrapture::capturepath`
értéke `Picasa\\Screen Captures\\`, magyarul `Picasa\\Képernyőfelvételek\\`.
Ezért **más nyelvű Picasa MÁS mappát hoz létre, a régit nem költözteti**.
A tulajdonos NAS-korpusza megerősíti: `Movies`, `Filmek` ÉS
`Mozgófilmek` egymás mellett.

➡️ Ebből következik a szabály, amit ez a lap mér: az ÍRÁS a mai nyelv
szerinti mappába megy, de a MEGLÉVŐ (bármely nyelvű) mappát fel kell
ismernünk — különben mi nyitunk néma harmadikat.
"""

from pathlib import Path

import pytest

from picasapy.app.project_folder_names import (
    ProjectFolderKind,
    ismert_nevek,
    letezo_vagy_honos_mappa,
    project_folder_name,
)


class TestHonositottNev:
    def test_a_magyar_nev_a_honositott(self):
        assert project_folder_name(ProjectFolderKind.COLLAGES, "hu") == "Kollázsok"
        assert project_folder_name(ProjectFolderKind.MOVIES, "hu") == "Filmek"
        assert (
            project_folder_name(ProjectFolderKind.SCREEN_CAPTURES, "hu")
            == "Képernyőfelvételek"
        )

    def test_az_angol_az_eredeti_kulcs_szerinti(self):
        assert project_folder_name(ProjectFolderKind.COLLAGES, "en") == "Collages"
        assert (
            project_folder_name(ProjectFolderKind.SCREEN_CAPTURES, "en")
            == "Screen Captures"
        )

    def test_ismeretlen_nyelvnel_az_angol(self):
        assert project_folder_name(ProjectFolderKind.MOVIES, "de") == "Movies"


class TestIsmertNevek:
    def test_minden_ismert_alak_szerepel(self):
        """A felismeréshez MINDEN nyelvi alak kell — a NAS-korpuszban a
        `Movies`, `Filmek` és `Mozgófilmek` egymás mellett áll."""
        nevek = ismert_nevek(ProjectFolderKind.MOVIES)
        assert {"Movies", "Filmek", "Mozgófilmek"} <= set(nevek)

    def test_a_kollazs_mindket_alakja(self):
        assert {"Collages", "Kollázsok"} <= set(ismert_nevek(ProjectFolderKind.COLLAGES))


class TestLetezoMappaNyer:
    def test_ha_van_MEGLEVO_mappa_azt_hasznaljuk(self, tmp_path):
        """⚠️ A jegy magja: ne nyissunk néma harmadikat."""
        picasa = tmp_path / "Picasa"
        (picasa / "Movies").mkdir(parents=True)

        cel = letezo_vagy_honos_mappa(picasa, ProjectFolderKind.MOVIES, "hu")

        assert cel == picasa / "Movies", "a meglévő angol mappát kellett volna használni"

    def test_ha_TOBB_letezik_a_honos_nyeri(self, tmp_path):
        """Több nyelvi alak esetén a MAI nyelv szerinti — az a felhasználó
        aktuális Picasájának a mappája."""
        picasa = tmp_path / "Picasa"
        (picasa / "Movies").mkdir(parents=True)
        (picasa / "Filmek").mkdir()

        cel = letezo_vagy_honos_mappa(picasa, ProjectFolderKind.MOVIES, "hu")

        assert cel == picasa / "Filmek"

    def test_ha_egyik_sem_letezik_a_honos_nev(self, tmp_path):
        picasa = tmp_path / "Picasa"
        picasa.mkdir()

        cel = letezo_vagy_honos_mappa(picasa, ProjectFolderKind.COLLAGES, "hu")

        assert cel == picasa / "Kollázsok"

    def test_a_fajlt_nem_nezi_mappanak(self, tmp_path):
        picasa = tmp_path / "Picasa"
        picasa.mkdir()
        (picasa / "Movies").write_text("nem mappa", encoding="utf-8")

        cel = letezo_vagy_honos_mappa(picasa, ProjectFolderKind.MOVIES, "hu")

        assert cel == picasa / "Filmek"


class TestKollazsBekotes:
    def test_a_kollazs_celmappaja_a_meglevot_hasznalja(self, tmp_path, monkeypatch):
        """A #1088 után a valódi képmappába írunk — ha ott már van
        `Collages`, abba, és nem nyitunk `Kollázsok`-at mellé."""
        from picasapy.app import collage_output

        kepek = tmp_path / "Képek"
        (kepek / "Picasa" / "Collages").mkdir(parents=True)
        monkeypatch.setattr(collage_output, "pictures_dir", lambda: kepek)

        assert collage_output.output_dir(None) == kepek / "Picasa" / "Collages"

    def test_beallitott_mappa_valtozatlanul_nyer(self, tmp_path, monkeypatch):
        from picasapy.app import collage_output

        sajat = tmp_path / "sajat"
        assert collage_output.output_dir(str(sajat)) == sajat
