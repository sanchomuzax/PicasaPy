"""#422 4. lépcső: az Emberek-album kép-szintű kötegelt parancsai.

„Eltávolítás az Emberek albumból" — az adott személy arc-címkéje (a
régióval együtt) lekerül a kijelölt képekről; „Áthelyezés új személyhez…"
— ugyanaz a régió MÁSIK névhez kerül.
"""

from __future__ import annotations

import pytest

from picasapy.ini import contacts_of, load_document, parse_faces
from support.jpeg_factory import make_jpeg

_ANNA = "1111111111111111"
_BELA = "2222222222222222"
# két arc: az elsőé Anna, a másodiké Béla (rect64 alakok a meglévő tesztekből)
_INI = (
    "[Contacts2]\n"
    f"{_ANNA}=Anna;;\n"
    f"{_BELA}=Béla;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA};rect64(5000280078006e00),{_BELA}\n"
    "[b.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA}\n"
)


@pytest.fixture
def controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "lib"
    library.mkdir()
    make_jpeg(library / "a.jpg")
    make_jpeg(library / "b.jpg")
    (library / ".picasa.ini").write_text(_INI, encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    yield ctl, library
    assert ctl.waitForBackgroundWorkers(30.0), "a háttérszál nem állt le"


def _faces(library, photo):
    document = load_document(library / ".picasa.ini")
    names = {c.person_id.casefold(): c.name for c in contacts_of(document)}
    section = document.section(photo)
    # az utolsó arc levétele után a szekció üresen maradhat (vagy ki is
    # eshet) — mindkettő „nincs arc", nem hiba
    raw = (section.get("faces") if section is not None else "") or ""
    return sorted(
        names.get(face.contact_id.casefold(), "") for face in parse_faces(raw)
    )


class TestRemovePersonFromRows:
    def test_removes_only_that_persons_face(self, controller):
        ctl, library = controller
        assert ctl.removePersonFromRows(list(range(2)), "Anna") is True
        assert _faces(library, "a.jpg") == ["Béla"]
        assert _faces(library, "b.jpg") == []

    def test_unknown_person_is_a_noop(self, controller):
        ctl, library = controller
        assert ctl.removePersonFromRows(list(range(2)), "Nincs Ilyen") is True
        assert _faces(library, "a.jpg") == ["Anna", "Béla"]

    def test_empty_person_is_rejected(self, controller):
        ctl, _library = controller
        assert ctl.removePersonFromRows([0], "") is False


class TestMovePersonOnRows:
    def test_face_moves_to_the_new_name(self, controller):
        ctl, library = controller
        assert ctl.movePersonOnRows(list(range(2)), "Anna", "Anna Kovács") is True
        assert _faces(library, "a.jpg") == ["Anna Kovács", "Béla"]
        assert _faces(library, "b.jpg") == ["Anna Kovács"]

    def test_moving_to_an_existing_person_reuses_the_contact(self, controller):
        """Meglévő névre mozgatva NEM keletkezik második kontakt-bejegyzés."""
        ctl, library = controller
        assert ctl.movePersonOnRows([0, 1], "Anna", "Béla") is True
        document = load_document(library / ".picasa.ini")
        assert [c.name for c in contacts_of(document)].count("Béla") == 1
        assert _faces(library, "b.jpg") == ["Béla"]

    def test_empty_new_name_is_rejected(self, controller):
        ctl, library = controller
        assert ctl.movePersonOnRows([0], "Anna", "   ") is False
        assert _faces(library, "a.jpg") == ["Anna", "Béla"]
