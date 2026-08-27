"""#1601: a bal hasáb két ini-alapú gyűjteménye EGYETLEN lemez-söpréssel.

MÉRVE (RPi5, tmpfs, szintetikus index): 5000 mappánál a `people_in_index`
3765 ms, a `project_folders` 1527 ms — együtt az induláskori szinkron munka
**94%-a**. Mindkettő UGYANAZT a `.picasa.ini`-halmazt olvasta végig,
egymástól függetlenül, tehát minden fájlt KÉTSZER.

Ez a teszt a söprések SZÁMÁT rögzíti: az ini-nkénti olvasás determinista,
nem időfüggő — így a szabály nem flaky, mégis megfogja a visszaesést.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index import folder_ini
from picasapy.index.folder_ini import sweep_folder_inis
from picasapy.index.people import people_in_index
from picasapy.index.project_folders import project_folders
from picasapy.index.side_pane import load_side_pane_collections
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_RECT = "3f840000c3509f84"
_PROJECTS = "[Picasa]\nP2category=Projects (internal)\n"


@pytest.fixture
def library(tmp_path):
    """Három ini-vel bíró mappa: arcos, projekt, és egy semleges."""
    root = tmp_path / "kepek"
    for name in ("nyaralas", "Kollázsok", "varos"):
        (root / name).mkdir(parents=True)
        make_jpeg(root / name / "a.jpg")
    (root / "nyaralas" / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n",
        encoding="utf-8",
    )
    (root / "Kollázsok" / ".picasa.ini").write_text(_PROJECTS, encoding="utf-8")
    (root / "varos" / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Folders on Disk\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


@pytest.fixture
def olvasas_szamlalo(monkeypatch):
    """Megszámolja, hányszor olvassuk be egy `.picasa.ini` tartalmát.

    A söprés EGYETLEN helyen nyúl a lemezhez (`folder_ini.load_document`) —
    a számláló ezért itt ül, és minden fogyasztóra érvényes."""
    eredeti = folder_ini.load_document
    olvasasok: list[str] = []

    def szamlalo(path):
        olvasasok.append(str(path))
        return eredeti(path)

    monkeypatch.setattr(folder_ini, "load_document", szamlalo)
    return olvasasok


class TestSweepFolderInis:
    def test_minden_ini_mappat_egyszer_ad_at_minden_fogyasztonak(
        self, conn, olvasas_szamlalo
    ):
        elso: list[str] = []
        masodik: list[str] = []
        sweep_folder_inis(
            conn,
            (
                lambda path, _doc: elso.append(path),
                lambda path, _doc: masodik.append(path),
            ),
        )
        assert len(elso) == 3
        assert sorted(elso) == sorted(masodik)
        # KÉT fogyasztó, mégis mappánként EGY lemez-olvasás
        assert len(olvasas_szamlalo) == 3

    def test_olvashatatlan_ini_csendben_kimarad(self, conn, library, monkeypatch):
        """A könyvtár másik folyamat általi éppen-írása nem omlaszthatja
        össze a hasábot — a hibás mappa kimarad, a többi megmarad."""

        eredeti = folder_ini.load_document

        def hibas(path):
            if "varos" in str(path):
                raise OSError("nem olvasható")
            return eredeti(path)

        monkeypatch.setattr(folder_ini, "load_document", hibas)
        latott: list[str] = []
        sweep_folder_inis(conn, (lambda path, _doc: latott.append(path),))
        assert len(latott) == 2

    def test_fogyaszto_nelkul_sem_olvas(self, conn, olvasas_szamlalo):
        """Üres fogyasztólistával nincs mit gyűjteni — ne is olvassunk."""
        sweep_folder_inis(conn, ())
        assert olvasas_szamlalo == []


class TestLoadSidePaneCollections:
    def test_ugyanazt_adja_mint_a_ket_kulon_hivas(self, conn, library):
        """A gyorsítás nem változtathat az EREDMÉNYEN."""
        egyben = load_side_pane_collections(conn)
        assert egyben.people == people_in_index(conn)
        assert egyben.project_folders == project_folders(conn)

    def test_mappankent_egy_lemez_olvasas(self, conn, olvasas_szamlalo):
        """A #1601 lényege: három ini-s mappa → három olvasás, nem hat."""
        load_side_pane_collections(conn)
        assert len(olvasas_szamlalo) == 3

    def test_a_ket_kulon_hivas_egyutt_ketszer_annyit_olvas(
        self, conn, olvasas_szamlalo
    ):
        """A régi út mérése — ez a kontroll, amihez a nyereség viszonyul."""
        people_in_index(conn)
        project_folders(conn)
        assert len(olvasas_szamlalo) == 6

    def test_a_projekt_mappa_darabszama_az_indexbol_jon(self, conn, library):
        gyujtemenyek = load_side_pane_collections(conn)
        assert [
            (folder.name, folder.photo_count)
            for folder in gyujtemenyek.project_folders
        ] == [("Kollázsok", 1)]

    def test_az_emberek_lista_megvan(self, conn):
        gyujtemenyek = load_side_pane_collections(conn)
        assert [(p.name, p.photo_count) for p in gyujtemenyek.people] == [
            ("Roy Avery", 1)
        ]
