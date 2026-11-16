"""#7038: a mappa helye a controller ini API-ján keresztül szerkeszthető."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from picasapy.ini import IniSaveError


@pytest.fixture
def host():
    from picasapy.app.controller_folder_description_mixin import (
        AppControllerFolderDescriptionMixin,
    )

    class _Host(AppControllerFolderDescriptionMixin, QObject):
        def __init__(self):
            super().__init__()
            self.write_errors = []

        def jelentsdAzIrasiHibat(self, error):
            self.write_errors.append(error)

    return _Host()


@pytest.fixture
def folder(tmp_path):
    path = tmp_path / "balaton"
    path.mkdir()
    return path


def test_meglevo_mappa_helyet_elore_tolt(host, folder):
    (folder / ".picasa.ini").write_text(
        "[Picasa]\nlocation=Balaton\n", encoding="utf-8"
    )

    assert host.folderLocationOf(str(folder)) == "Balaton"


def test_helyet_uresre_allitva_torli_a_kulcsot(host, folder):
    (folder / ".picasa.ini").write_text(
        "[Picasa]\nlocation=Balaton\ndescription=Leírás\n", encoding="utf-8"
    )

    assert host.setFolderLocationOf(str(folder), "  ") is True

    saved = (folder / ".picasa.ini").read_text(encoding="utf-8")
    assert "location=" not in saved
    assert "description=Leírás" in saved
    assert host.folderLocationOf(str(folder)) == ""


def test_iras_hibanal_a_regi_ertek_megmarad_es_a_hiba_jelzett(
    host, folder, monkeypatch
):
    ini = folder / ".picasa.ini"
    ini.write_text("[Picasa]\nlocation=Régi hely\n", encoding="utf-8")
    before = ini.read_bytes()

    import picasapy.app.controller as controller_module

    def fail(*_args, **_kwargs):
        raise IniSaveError("teszt írási hiba")

    monkeypatch.setattr(controller_module, "update_document", fail)

    assert host.setFolderLocationOf(str(folder), "Új hely") is False

    assert ini.read_bytes() == before
    assert host.folderLocationOf(str(folder)) == "Régi hely"
    assert len(host.write_errors) == 1
