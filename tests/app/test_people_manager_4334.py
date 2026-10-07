"""#4334: a központi névjegytár és az érintett mappa-ini-k kezelése."""

# rontás-kontroll: központi tár/mappairány: 3 failed; e-mail/formátum: 2 failed

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from picasapy.index import open_index, sync_tree
from picasapy.ini import ContactXmlEntry, load_contacts_xml, save_contacts_xml

_RECT = "1e00280045006e00"
_ANNA_A = "aaaaaaaaaaaaaaaa"
_ANNA_B = "bbbbbbbbbbbbbbbb"
_ZOLI = "cccccccccccccccc"
_CENTRAL_ANNA = "1111111111111111"
_CENTRAL_ZOLI = "2222222222222222"
_MODIFIED = "2026-08-15T18:42:17+02:00"


def _host(db_path):
    """A PeopleMixin minimális tárolóteszt-gazdája."""
    from picasapy.app.people_controller import PeopleMixin

    class Host(PeopleMixin, QObject):
        syncFailed = Signal(str)

        def __init__(self, index_path):
            super().__init__()
            self._db_path = index_path
            self.reload_count = 0

        def _reload_after_sync(self):
            self.reload_count += 1

    return Host(db_path)


def _library(root: Path, contact_id: str, name: str, photo: str = "a.jpg") -> Path:
    from support.jpeg_factory import make_jpeg

    root.mkdir(parents=True)
    make_jpeg(root / photo)
    (root / ".picasa.ini").write_text(
        f"[Contacts2]\n{contact_id}={name};;\n"
        f"[{photo}]\nfaces=rect64({_RECT}),{contact_id}\n",
        encoding="utf-8",
    )
    return root


def _setup_host(tmp_path, *libraries):
    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        for library in libraries:
            sync_tree(conn, library)
    return _host(db_path)


def _central_path(host):
    return Path(host._db_path).parent / "contacts" / "contacts.xml"


def test_people_manager_unites_central_and_folder_contacts(tmp_path):
    from support.jpeg_factory import make_jpeg

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    make_jpeg(first / "a.jpg")
    make_jpeg(second / "b.jpg")
    (first / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ANNA_A}=Anna;anna@example.test;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ANNA_A}\n",
        encoding="utf-8",
    )
    (second / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ANNA_B}=Anna;;\n{_ZOLI}=Zoli;;\n"
        f"[b.jpg]\nfaces=rect64({_RECT}),{_ANNA_B}\n",
        encoding="utf-8",
    )
    host = _setup_host(tmp_path, first, second)
    save_contacts_xml(
        _central_path(host),
        (
            ContactXmlEntry(
                _CENTRAL_ANNA,
                "Anna",
                modified_time=_MODIFIED,
                local_contact="1",
            ),
            ContactXmlEntry(
                _CENTRAL_ZOLI,
                "Central Only",
                modified_time=_MODIFIED,
                local_contact="1",
            ),
        ),
    )

    rows = {row["name"]: row for row in host.peopleManagerContacts()}

    assert set(rows) == {"Anna", "Central Only", "Zoli"}
    assert rows["Anna"]["photoCount"] == 2
    assert rows["Anna"]["email"] == "anna@example.test"
    assert set(rows["Anna"]["localContactIds"]) == {_ANNA_A, _ANNA_B}
    assert set(rows["Anna"]["contactIds"]) == {
        _ANNA_A,
        _ANNA_B,
        _CENTRAL_ANNA,
    }
    assert rows["Central Only"]["photoCount"] == 0
    assert rows["Central Only"]["localContactIds"] == []


def test_create_refuses_email_not_supported_by_the_measured_central_shape(tmp_path):
    host = _setup_host(tmp_path)

    assert not host.savePeopleManagerChanges(
        [{"action": "create", "name": "Béla", "email": "bela@example.test"}]
    )

    assert not _central_path(host).exists()


def test_new_contact_goes_to_central_store_without_changing_folder_ini(
    tmp_path,
):
    library = _library(tmp_path / "library", _ANNA_A, "Anna")
    host = _setup_host(tmp_path, library)
    ini_path = library / ".picasa.ini"
    before = ini_path.read_bytes()

    assert host.savePeopleManagerChanges(
        [{"action": "create", "name": "Béla", "email": ""}]
    )

    assert ini_path.read_bytes() == before
    assert not ini_path.with_name(".picasa.ini.bak").exists()
    contacts = load_contacts_xml(_central_path(host))
    bela = next(contact for contact in contacts if contact.name == "Béla")
    assert len(bela.person_id) == 16
    assert bela.local_contact == "1"
    assert datetime.fromisoformat(bela.modified_time).utcoffset() is not None


def test_rename_and_delete_touch_only_folders_with_the_person(tmp_path):
    affected = _library(tmp_path / "affected", _ANNA_A, "Anna")
    unrelated = _library(tmp_path / "unrelated", _ZOLI, "Zoli")
    host = _setup_host(tmp_path, affected, unrelated)
    save_contacts_xml(
        _central_path(host),
        (
            ContactXmlEntry(
                _CENTRAL_ANNA, "Anna", modified_time=_MODIFIED, local_contact="1"
            ),
            ContactXmlEntry(
                _CENTRAL_ZOLI, "Zoli", modified_time=_MODIFIED, local_contact="1"
            ),
        ),
    )
    affected_ini = affected / ".picasa.ini"
    unrelated_ini = unrelated / ".picasa.ini"
    unrelated_before = unrelated_ini.read_bytes()

    assert host.savePeopleManagerChanges(
        [{"action": "update", "oldName": "Anna", "name": "Anita", "email": ""}]
    )

    assert unrelated_ini.read_bytes() == unrelated_before
    assert not unrelated_ini.with_name(".picasa.ini.bak").exists()
    assert f"{_ANNA_A}=Anita;;" in affected_ini.read_text(encoding="utf-8")
    central = load_contacts_xml(_central_path(host))
    assert any(contact.name == "Anita" for contact in central)
    assert any(contact.name == "Zoli" for contact in central)

    assert host.savePeopleManagerChanges([{"action": "delete", "oldName": "Anita"}])

    affected_text = affected_ini.read_text(encoding="utf-8")
    assert f"{_ANNA_A}=Anita;;" not in affected_text
    assert f"faces=rect64({_RECT}),{_ANNA_A}" not in affected_text
    assert unrelated_ini.read_bytes() == unrelated_before
    assert not unrelated_ini.with_name(".picasa.ini.bak").exists()
    central = load_contacts_xml(_central_path(host))
    assert all(contact.name != "Anita" for contact in central)
    assert any(contact.name == "Zoli" for contact in central)
