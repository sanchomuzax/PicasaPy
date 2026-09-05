"""#1637: a jelszó KAPUJA a vezérlőben — a rejtettek nem jönnek elő nélküle.

A #1637 magja (`picasapy.hidden_password`) csak a lenyomatot kezeli. Ez az őr
azt méri, hogy a kapu tényleg zár: ha van beállított jelszó, a `showHidden`
kapcsoló **magától nem nyílik ki**, csak sikeres feloldás után.

⚠️ Amit ez NEM véd: a rejtett mappák a lemezen változatlanul ott vannak. A
kapu a PicasaPy felületén belüli megjelenítést zárja, nem a fájlokat.
"""

from __future__ import annotations

import pytest

from picasapy.hidden_password import modern_lenyomat, picasa_lenyomat


@pytest.fixture
def vezerlo(qml_app):
    return qml_app[1]


class TestNincsJelszo:
    def test_jelszo_nelkul_a_kapcsolo_szabadon_all(self, vezerlo):
        """Alaphelyzet: jelszó nélkül a #17 óta megszokott viselkedés marad."""
        assert vezerlo.hiddenPasswordSet is False
        vezerlo.setShowHidden(True)
        assert vezerlo.showHidden is True
        vezerlo.setShowHidden(False)
        assert vezerlo.showHidden is False


class TestJelszoval:
    @pytest.mark.parametrize("keszit", [picasa_lenyomat, modern_lenyomat])
    def test_a_kapcsolo_NEM_nyilik_feloldas_nelkul(self, vezerlo, keszit):
        vezerlo.setHiddenPasswordHash(keszit("titok"))
        assert vezerlo.hiddenPasswordSet is True

        vezerlo.setShowHidden(True)
        assert vezerlo.showHidden is False, (
            "a rejtettek jelszó megadása nélkül előjöttek — a kapu nem zár"
        )

    @pytest.mark.parametrize("keszit", [picasa_lenyomat, modern_lenyomat])
    def test_helyes_jelszoval_kinyilik(self, vezerlo, keszit):
        vezerlo.setHiddenPasswordHash(keszit("titok"))
        assert vezerlo.unlockHidden("titok") is True
        vezerlo.setShowHidden(True)
        assert vezerlo.showHidden is True

    def test_rossz_jelszo_nem_old_fel(self, vezerlo):
        vezerlo.setHiddenPasswordHash(picasa_lenyomat("titok"))
        assert vezerlo.unlockHidden("Titok") is False
        vezerlo.setShowHidden(True)
        assert vezerlo.showHidden is False

    def test_a_PICASABAN_beallitott_jelszo_is_nyit(self, vezerlo):
        """A kompatibilitás lényege: a windowsos Picasa hex-MD5 alakja."""
        vezerlo.setHiddenPasswordHash("201016e8206a5f42aa527090511504d5")
        assert vezerlo.unlockHidden("titok") is True

    def test_a_feloldas_a_jelszo_TORLESEVEL_visszaall(self, vezerlo):
        vezerlo.setHiddenPasswordHash(picasa_lenyomat("titok"))
        vezerlo.unlockHidden("titok")
        vezerlo.setShowHidden(True)
        assert vezerlo.showHidden is True

        vezerlo.lockHidden()
        assert vezerlo.showHidden is False, "a zárás nem kapcsolta vissza"
        vezerlo.setShowHidden(True)
        assert vezerlo.showHidden is False, "zárás után újra kérnie kell"

    def test_a_TAROLT_ertek_soha_nem_a_nyilt_jelszo(self, vezerlo):
        """A kapu akkor is jó, ha a tárolás rossz — ezért külön mérjük."""
        vezerlo.setHiddenPassword("titok", modern=False)
        tarolt = vezerlo.hiddenPasswordHash
        assert "titok" not in tarolt
        assert tarolt == picasa_lenyomat("titok")

        vezerlo.setHiddenPassword("titok", modern=True)
        tarolt = vezerlo.hiddenPasswordHash
        assert "titok" not in tarolt
        assert tarolt.startswith("picasapy-pbkdf2-sha256$")
