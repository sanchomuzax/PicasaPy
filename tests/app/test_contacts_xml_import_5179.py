"""#5179: a Picasa profil contacts.xml-je a központi névtárba kerül."""

from pathlib import Path

from picasapy.app.picasa_import_controller import PicasaImportController
from picasapy.pmpimport.db3_atvetel import AtvetelJelentes
from picasapy.ini import ContactXmlEntry, load_contacts_xml, save_contacts_xml
from picasapy.scanner.discovery import PicasaInstallation


def test_picasa_import_beemeli_a_teljes_profil_nevjegylistat(
    qt_app, tmp_path: Path
):
    profil = tmp_path / "Google" / "Picasa2"
    forras = profil / "contacts" / "contacts.xml"
    forras.parent.mkdir(parents=True)
    forras.write_text(
        "<?xml version='1.0'?>\n"
        "<contacts>\n"
        ' <contact id="00000000000000a1" name="Forrás Név" '
        'modified_time="2026-10-17T10:00:00+02:00" local_contact="1"/>\n'
        ' <contact id="00000000000000a2" name="Másik Név" '
        'modified_time="2026-10-17T10:01:00+02:00" local_contact="1"/>\n'
        "</contacts>\n",
        encoding="utf-8",
    )
    index_path = tmp_path / "PicasaPy" / "index.db"
    central = index_path.parent / "contacts" / "contacts.xml"
    save_contacts_xml(
        central,
        (
            ContactXmlEntry(
                person_id="00000000000000a1",
                name="Elavult név",
                modified_time="2026-10-16T10:00:00+02:00",
                local_contact="1",
            ),
            ContactXmlEntry(
                person_id="00000000000000b1",
                name="Saját névjegy",
                modified_time="2026-10-16T10:01:00+02:00",
                local_contact="1",
            ),
        ),
    )
    installation = PicasaInstallation(
        label="próba",
        picasa2_dir=profil,
        picasa2albums_dir=None,
        watched_folders_file=None,
    )
    controller = PicasaImportController(
        felderito=lambda: (installation,),
        olvaso=lambda _directory, _remapper: (),
        atvevo=lambda _records: AtvetelJelentes(),
        index_path=index_path,
    )

    controller.startImport()
    assert controller.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()

    imported = {entry.person_id: entry.name for entry in load_contacts_xml(central)}
    assert imported == {
        "00000000000000a1": "Forrás Név",
        "00000000000000a2": "Másik Név",
        "00000000000000b1": "Saját névjegy",
    }


def test_hibas_contacts_xml_nem_allitja_meg_a_kepek_atvetelet(qt_app, tmp_path: Path):
    """A contacts.xml opcionális (pmp-database.md): a romlott fájl mellett is fut az átvétel."""
    profil = tmp_path / "Google" / "Picasa2"
    forras = profil / "contacts" / "contacts.xml"
    forras.parent.mkdir(parents=True)
    forras.write_text("nem xml <<<", encoding="utf-8")
    atvett = []
    controller = PicasaImportController(
        felderito=lambda: (
            PicasaInstallation(
                label="próba",
                picasa2_dir=profil,
                picasa2albums_dir=None,
                watched_folders_file=None,
            ),
        ),
        olvaso=lambda _directory, _remapper: (),
        atvevo=lambda records: atvett.append(records) or AtvetelJelentes(),
        index_path=tmp_path / "PicasaPy" / "index.db",
    )

    controller.startImport()
    assert controller.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()

    assert atvett, "a hibás contacts.xml miatt elmaradt a képek átvétele"
