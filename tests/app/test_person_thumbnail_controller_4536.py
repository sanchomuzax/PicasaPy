"""#4536: a PeopleMixin az index API-n át kezeli a személy-borítóképet."""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings

from picasapy.index import open_index, sync_tree
from picasapy.index.queries import photos_in_folder
from picasapy.ini import parse_document, update_document
from tests.support.jpeg_factory import make_jpeg

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_RECT = "1e00280045006e00"


def _library(root):
    root.mkdir()
    make_jpeg(root / "a.jpg")
    make_jpeg(root / "b.jpg")
    update_document(
        root / ".picasa.ini",
        lambda _old: parse_document(
            "[Contacts2]\n"
            f"{_PERSON_ID}=Anna;;\n"
            "[a.jpg]\n"
            f"faces=rect64({_RECT}),{_PERSON_ID}\n"
            "[b.jpg]\n"
        ),
        backup=False,
    )


def test_controller_checks_and_saves_the_named_face(tmp_path, qt_app):
    from picasapy.app.people_controller import PeopleMixin

    library = tmp_path / "kepek"
    _library(library)
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, library)

    class Host(PeopleMixin, QObject):
        def __init__(self):
            super().__init__()
            self._db_path = db
            self._view_mode = ("person", "Anna")
            self._init_people()
            with open_index(db) as conn:
                self._load_people(conn)

        def _show(self, _records):
            pass

        def _rows_to_photos(self, rows):
            with open_index(db) as conn:
                indexed = photos_in_folder(conn, library)
            return [indexed[int(row)] for row in rows]

        def _get_settings(self):
            return QSettings(
                str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
            )

    host = Host()
    with open_index(db) as conn:
        photos = photos_in_folder(conn, library)
    photo_a = next(p for p in photos if p.name == "a.jpg")
    photo_b = next(p for p in photos if p.name == "b.jpg")

    assert host.canSetPersonThumbnail(photo_a.id, "Anna") is True
    assert host.canSetPersonThumbnail(photo_b.id, "Anna") is False
    assert host.setPersonThumbnail(photo_a.id, "Anna") is True
    assert host.setPersonThumbnail(photo_b.id, "Anna") is False

    person = next(item for item in host.people if item["name"] == "Anna")
    assert person["thumbUrl"].startswith(f"image://thumbs/{photo_a.id}?")
    assert "&fz=" in person["thumbUrl"]
    panel_person = host.peopleOfRows([0])[0]
    assert panel_person["thumbUrl"] == person["thumbUrl"]
    manager_person = next(
        row for row in host.peopleManagerContacts() if row["name"] == "Anna"
    )
    assert manager_person["thumbUrl"] == person["thumbUrl"]

    fresh_host = Host()
    reloaded = next(item for item in fresh_host.people if item["name"] == "Anna")
    assert reloaded["thumbUrl"] == person["thumbUrl"]
