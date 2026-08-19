"""A MENTÉS SIKERKRITÉRIUMA: a kollázs megjelenik a Projektek gyűjteményben.

## Miért született ez a fájl

A felhasználó a v0.8.7-en ezt jelezte: *„Kollázs mentés után továbbra sem
jelenik meg a Projekt mappában SEMMI."* Ekkor a `tests/app/test_collage_output_949.py`
**20 tesztje zölden futott** — mert azok azt állították, amit a kód csinál
(a JPEG és a `.cxf` párja megszületik), és **egyetlen sem** azt, amit a
felhasználó lát: hogy az album meg is JELENIK a bal hasábon.

A hiányzó láncszem a kimeneti mappa `.picasa.ini`-je: a Projektek
gyűjtemény a `[Picasa] P2category` kulcsból épül (#1029), a mentés viszont
soha nem írta ki.

⚠️ Ez a fájl szándékosan a **teljes láncot** járja végig — mentés →
`.picasa.ini` → a gyűjteményt tápláló lekérdezés —, mert a lánc bármelyik
szeme külön-külön „működhet" úgy, hogy a felhasználó semmit nem lát.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import cv2
import pytest

from picasapy.app import collage_output as output
from picasapy.collage.nodes import CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.ini import is_projects_category, load_document, read_folder_category
from picasapy.scanner import PICASA_INI_NAME


@pytest.fixture
def kepek(tmp_path):
    """Három valódi JPEG — a mentésnek olvasható forrás kell."""
    mappa = tmp_path / "forras"
    mappa.mkdir()
    utak = []
    for i, szin in enumerate([(0, 0, 255), (0, 255, 0), (255, 0, 0)]):
        ut = mappa / f"k{i}.jpg"
        cv2.imwrite(str(ut), np.full((300, 400, 3), szin, dtype=np.uint8))
        utak.append(ut)
    return utak


def _ment(cel_mappa, kepek):
    """Egy valódi mentés, ahogy a panel csinálja."""
    beallitasok = PicasaCollageSettings(width=800, height=600)
    csomopontok = tuple(
        CollageNode(str(ut), 0.25 + 0.25 * i, 0.5, 300.0, 220.0)
        for i, ut in enumerate(kepek)
    )
    cel = output.output_path(cel_mappa, "Kollázsok")
    return output.render_collage(csomopontok, beallitasok, cel, album_title="Kollázsok")


class TestAMentettKollazsMegjelenikAProjektekAlatt:
    def test_a_kollazs_kepe_tenyleg_letrejon(self, tmp_path, kepek):
        """Alap: a JPEG megszületik. Enélkül a többinek nincs értelme."""
        cel_mappa = tmp_path / "Képek" / "Picasa" / "Kollázsok"
        eredmeny = _ment(cel_mappa, kepek)

        assert eredmeny.path is not None, "a mentés nem adott vissza útvonalat"
        assert eredmeny.path.exists(), f"a kollázs képe nem jött létre: {eredmeny.path}"
        assert eredmeny.path.stat().st_size > 0

    def test_a_mappa_kap_picasa_ini_t(self, tmp_path, kepek):
        """A mentés megjelöli a mappát — ez hiányzott (#1029 forrása)."""
        cel_mappa = tmp_path / "Képek" / "Picasa" / "Kollázsok"
        _ment(cel_mappa, kepek)

        ini = cel_mappa / ".picasa.ini"
        assert ini.exists(), (
            "a mentés NEM írt .picasa.ini-t a kimeneti mappába — enélkül a "
            "kollázs sehol nem jelenik meg a bal hasábon"
        )

    def test_A_LENYEG_a_mappa_PROJEKT_kategoriat_kap(self, tmp_path, kepek):
        """⚠️ EZ A SIKERKRITÉRIUM: a Projektek gyűjtemény ezt olvassa.

        Ha ez bukik, a felhasználó a mentés után üres Projekteket lát —
        akkor is, ha a JPEG hibátlanul elkészült."""
        cel_mappa = tmp_path / "Képek" / "Picasa" / "Kollázsok"
        _ment(cel_mappa, kepek)

        kategoria = read_folder_category(load_document(cel_mappa / PICASA_INI_NAME))
        assert kategoria is not None, "a .picasa.ini-ben nincs P2category kulcs"
        assert is_projects_category(kategoria), (
            f"a mappa kategóriája {kategoria!r} — a Projektek gyűjtemény így "
            "üres marad a mentés után"
        )

    def test_a_masodik_mentes_nem_torli_az_elsot(self, tmp_path, kepek):
        """A meglévő ini-t nem szabad felülírni — adatvesztés volna."""
        cel_mappa = tmp_path / "Képek" / "Picasa" / "Kollázsok"
        cel_mappa.mkdir(parents=True)
        (cel_mappa / ".picasa.ini").write_text(
            "[Picasa]\nname=Sajat nev\nvalami=megorzendo\n", encoding="utf-8"
        )

        _ment(cel_mappa, kepek)

        tartalom = (cel_mappa / ".picasa.ini").read_text(encoding="utf-8")
        assert "valami=megorzendo" in tartalom, "a mentés ELDOBTA a meglévő ini-adatot"
        assert "name=Sajat nev" in tartalom, "a mentés felülírta a meglévő album-nevet"
        assert is_projects_category(
            read_folder_category(load_document(cel_mappa / PICASA_INI_NAME))
        )

    def test_ekezetes_es_szokozos_mappanev(self, tmp_path, kepek):
        """A valódi mappanév ékezetes (`Kollázsok`) — windowsos csapda."""
        cel_mappa = tmp_path / "Képek és videók" / "Picasa" / "Kollázsok"
        eredmeny = _ment(cel_mappa, kepek)

        assert eredmeny.path is not None and eredmeny.path.exists()
        assert is_projects_category(
            read_folder_category(load_document(cel_mappa / PICASA_INI_NAME))
        )


class TestAzIndexbeIsBekerul:
    """⚠️ A MÁSODIK, FÜGGETLEN BLOKKOLÓ — enélkül a `.picasa.ini` sem elég.

    A Projektek gyűjtemény lekérdezése így indul:

        SELECT path FROM folders WHERE has_ini = 1

    Vagyis csak a MÁR INDEXELT mappákon megy végig. A kollázs célmappája
    viszont tipikusan egyetlen figyelt gyökér alatt sincs — mérve a valódi
    indexen: 68 mappa, egy sem a Kollázsok.

    Ez a teszt azért indul ÜRES indexszel, mert a korábbi tesztek előre
    feltöltött `folders` táblán futottak, és emiatt ez a hiba
    szerkezetileg megfoghatatlan volt.
    """

    def test_a_mentes_utan_a_PROJEKTEK_lekerdezes_megtalalja(self, tmp_path, kepek):
        from picasapy.index import open_index
        from picasapy.index.project_folders import project_folders

        cel_mappa = tmp_path / "Képek" / "Picasa" / "Kollázsok"
        db = tmp_path / "index.db"

        with open_index(db) as conn:
            assert list(project_folders(conn)) == [], "az index nem üresen indult"

        eredmeny = _ment(cel_mappa, kepek)
        assert eredmeny.path is not None and eredmeny.path.exists()

        # a mentés vezérlő-oldali lépése: a célmappa felvétele az indexbe
        from picasapy.index.sync import sync_folder

        with open_index(db) as conn:
            sync_folder(conn, cel_mappa, cel_mappa)

        with open_index(db) as conn:
            talalatok = list(project_folders(conn))

        assert talalatok, (
            "a mentett kollázs mappája NEM jelenik meg a Projektek "
            "gyűjteményben — a felhasználó üres listát lát a mentés után"
        )
        assert any(Path(t.path) == cel_mappa for t in talalatok), (
            f"a Projektek lista nem a mentési mappát adja: {talalatok}"
        )
