"""A tesztüzem naplója írja ki a VÉDETT GYÖKEREK számát — #1712.

A #1706 mérése kimondta: a takarítás (`prune_foreign_folders`) és az
exportcél-visszavétel költsége **nem** az indexelt mappák számával
skálázik, hanem a védett gyökerekével (figyelt mappák + nyilvántartott
exportcélok, max. 20) — mérve ~4 `lstat`/gyökér, hálózati megosztáson
egyenként ~47 ms.

Ez a szám a naplóból eddig **hiányzott**, ezért a tulajdonos két naplója
(v0.8.133 és v0.8.134) alapján nem lehetett eldönteni, mi drágult meg.

⚠️ Csak DARABSZÁM kerül a naplóba — a #1654 adatvédelmi garanciája
(se útvonal, se fájlnév, se felhasználónév) változatlanul áll.
"""

from __future__ import annotations

from picasapy.perf.tesztuzem import KonyvtarMeret, naplo_szovege

FEJLEC = {"app_version": "v0.8.136", "platform": "Linux"}
MERET = KonyvtarMeret(mappak=18, kepek=421)


class TestASzamMegjelenik:
    def test_a_vedett_gyokerek_szama_a_naploban_van(self):
        szoveg = naplo_szovege(
            idovonal_jelentes="(idővonal)", fejlec=FEJLEC, meret=MERET,
            vedett_gyokerek=21,
        )
        assert "védett gyökerek:  21" in szoveg, (
            "a #1706 domináns tényezője nem jelenik meg a naplóban"
        )

    def test_a_mappa_es_kepszam_valtozatlanul_ott_van(self):
        """Ellenpróba: az új sor nem szorította ki a meglévőket."""
        szoveg = naplo_szovege(
            idovonal_jelentes="(idővonal)", fejlec=FEJLEC, meret=MERET,
            vedett_gyokerek=21,
        )
        assert "indexelt mappák:  18" in szoveg
        assert "indexelt képek:   421" in szoveg


class TestVisszafeleKompatibilis:
    def test_szam_nelkul_a_sor_KIMARAD(self):
        """Ha nincs adat, ne írjunk oda nullát — az félrevezetne.

        A nulla azt jelentené, hogy nincs védett gyökér (ami lehetetlen: a
        figyelt mappa maga is az). A hiányzó sor őszintébb.
        """
        szoveg = naplo_szovege(
            idovonal_jelentes="(idővonal)", fejlec=FEJLEC, meret=MERET,
        )
        assert "védett gyökerek" not in szoveg
        assert "indexelt mappák:  18" in szoveg


class TestAdatvedelem:
    def test_a_szam_nem_hoz_be_utvonalat(self):
        """A #1654 garanciája: a napló darabszámokat tartalmaz, nem utakat."""
        szoveg = naplo_szovege(
            idovonal_jelentes="(idővonal)", fejlec=FEJLEC, meret=MERET,
            vedett_gyokerek=21,
        )
        for tiltott in ("/home/", "C:\\", "\\\\", ".jpg", "Képek"):
            assert tiltott not in szoveg, f"útvonalszerű tartalom: {tiltott!r}"
