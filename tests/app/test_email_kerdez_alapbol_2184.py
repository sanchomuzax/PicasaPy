"""#2184 — friss profilon az első küldés MEGKÉRDEZI, mivel küldjön.

Az eredetiben a `DoNotPromptForEmailPref` alapértéke **0**, vagyis az
első küldéskor a választó párbeszéd megjelenik (`0x00742154`: `ebp = 0`,
majd `0x00742168 je` → MUTASD). A felhasználó ott dönt, és ott van a
„Ne jelenítse meg többé" jelölőnégyzet is, ami ezt az alapértéket
felülírja.

Nálunk fordítva volt: alapból nem kérdeztünk, ezért a párbeszéd
gyakorlatilag elérhetetlen maradt annak, aki sosem nyitja meg az
Opciókat.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.email_controller import EmailController


@pytest.fixture
def ures_profil(tmp_path, qt_app):
    """Friss telepítés: a beállítás-fájlban NINCS e-mail kulcs."""
    return QSettings(str(tmp_path / "friss.ini"), QSettings.Format.IniFormat)


class TestAFrissProfilKERDEZ:
    def test_a_valaszto_alapbol_BE_van_kapcsolva(self, ures_profil):
        ctl = EmailController(photo_source=lambda: [], settings=ures_profil)
        assert ctl.useDefaultClient is False, (
            "friss profilon az alapértelmezett kliens van beállítva — "
            "a választó párbeszéd sosem jelenne meg"
        )

    def test_a_TAROLT_ertek_erosebb_az_alapertelmezesnel(self, ures_profil):
        """Aki egyszer bepipálta a »ne kérdezz«-t, ne kapja vissza."""
        elso = EmailController(photo_source=lambda: [], settings=ures_profil)
        elso.setUseDefaultClient(True)
        masodik = EmailController(photo_source=lambda: [], settings=ures_profil)
        assert masodik.useDefaultClient is True

    def test_a_visszakapcsolas_is_megmarad(self, ures_profil):
        elso = EmailController(photo_source=lambda: [], settings=ures_profil)
        elso.setUseDefaultClient(True)
        elso.setUseDefaultClient(False)
        masodik = EmailController(photo_source=lambda: [], settings=ures_profil)
        assert masodik.useDefaultClient is False
