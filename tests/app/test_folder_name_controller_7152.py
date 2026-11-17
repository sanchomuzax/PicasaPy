"""#7152: a mappanév mentése a controller INI-író slotján át."""

from __future__ import annotations

import os

import pytest
from PySide6.QtCore import QObject

from picasapy.ini import IniSaveError


def _host():
    from picasapy.app.controller_folder_description_mixin import (
        AppControllerFolderDescriptionMixin,
    )

    class Host(AppControllerFolderDescriptionMixin, QObject):
        def __init__(self):
            super().__init__()
            self.write_errors = []

        def jelentsdAzIrasiHibat(self, error):
            self.write_errors.append(error)

    return Host()


def test_nevet_ment_es_a_tobbi_picasa_adatot_es_kepszekciot_megorzi(tmp_path):
    host = _host()
    folder = tmp_path / "Balaton"
    folder.mkdir()
    ini = folder / ".picasa.ini"
    ini.write_text(
        "[Picasa]\nname=Régi név\nlocation=Vízpart\ndescription=Leírás\n"
        "[photo.jpg]\ncaption=Fotófelirat\n",
        encoding="utf-8",
    )

    assert host.setFolderNameOf(str(folder)) is True

    saved = ini.read_text(encoding="utf-8")
    assert "name=Balaton" in saved
    assert "location=Vízpart" in saved
    assert "description=Leírás" in saved
    assert "[photo.jpg]\ncaption=Fotófelirat" in saved
    assert host.write_errors == []


def test_hianyzo_ini_eseten_letrehozza_a_nev_sort(tmp_path):
    host = _host()
    folder = tmp_path / "Új mappa"
    folder.mkdir()

    assert host.setFolderNameOf(str(folder)) is True

    assert (folder / ".picasa.ini").is_file()
    assert "[Picasa]" in (folder / ".picasa.ini").read_text(encoding="utf-8")
    assert "name=Új mappa" in (folder / ".picasa.ini").read_text(encoding="utf-8")


@pytest.mark.skipif(os.name != "posix", reason="a chmod-os írásvédelem csak POSIX-on érvényes (#1864)")
def test_mar_egyezo_nevnel_nincs_iras_es_irasvedett_fajlon_sincs_hiba(
    tmp_path, monkeypatch
):
    host = _host()
    folder = tmp_path / "Balaton"
    folder.mkdir()
    ini = folder / ".picasa.ini"
    before = b"[Picasa]\r\nname=Balaton\r\nlocation=V\xC3\xADzpart\r\n"
    ini.write_bytes(before)
    ini.chmod(0o444)

    import picasapy.app.controller as controller_module

    def fail_if_written(*_args, **_kwargs):
        raise IniSaveError("az azonos névhez nem szabad írni")

    monkeypatch.setattr(controller_module, "update_document", fail_if_written)

    assert host.setFolderNameOf(str(folder)) is True

    assert ini.read_bytes() == before
    assert host.write_errors == []


def test_iras_hibat_jelent_es_nem_jelzi_sikeresnek(tmp_path, monkeypatch):
    host = _host()
    folder = tmp_path / "Balaton"
    folder.mkdir()
    ini = folder / ".picasa.ini"
    ini.write_text("[Picasa]\nname=Régi név\n", encoding="utf-8")
    before = ini.read_bytes()

    import picasapy.app.controller as controller_module

    def fail(*_args, **_kwargs):
        raise IniSaveError("teszt írási hiba")

    monkeypatch.setattr(controller_module, "update_document", fail)

    assert host.setFolderNameOf(str(folder)) is False

    assert ini.read_bytes() == before
    assert len(host.write_errors) == 1
    assert "teszt írási hiba" in str(host.write_errors[0])
