"""#1029: a mappa gyűjtemény-hovatartozása a `.picasa.ini` `[Picasa]`
`P2category` kulcsán — ebből él a bal hasáb **Projektek** gyűjteménye.

A kulcs valódi értékei a 859 fájlos korpuszból: `Folders on Disk` (456),
egyéni gyűjtemény-nevek (130), `Projects (internal)` (8), `Other Stuff` (3),
`Exported Pictures` (3). A Projektek gyűjteménybe KIZÁRÓLAG a
`Projects (internal)` értékű mappák tartoznak — a többi marad ott, ahol volt.
"""

from __future__ import annotations

from picasapy.ini import (
    PROJECTS_CATEGORY,
    is_projects_category,
    parse_document,
    read_folder_category,
)


class TestReadFolderCategory:
    def test_missing_picasa_section_yields_none(self):
        document = parse_document("[IMG_0001.jpg]\nstar=yes\n")
        assert read_folder_category(document) is None

    def test_missing_key_yields_none(self):
        document = parse_document("[Picasa]\nname=Nyaralás\n")
        assert read_folder_category(document) is None

    def test_projects_value_is_returned_verbatim(self):
        document = parse_document("[Picasa]\nP2category=Projects (internal)\n")
        assert read_folder_category(document) == "Projects (internal)"

    def test_folders_on_disk_is_returned_too(self):
        """A kulcs ÁLTALÁNOS gyűjtemény-hovatartozás — az olvasó nem szűr,
        a besorolást a hívó dönti el."""
        document = parse_document("[Picasa]\nP2category=Folders on Disk\n")
        assert read_folder_category(document) == "Folders on Disk"

    def test_surrounding_whitespace_is_trimmed(self):
        document = parse_document("[Picasa]\nP2category=  Other Stuff \n")
        assert read_folder_category(document) == "Other Stuff"

    def test_empty_value_yields_none(self):
        document = parse_document("[Picasa]\nP2category=\n")
        assert read_folder_category(document) is None

    def test_key_is_case_insensitive_like_the_ini_itself(self):
        document = parse_document("[Picasa]\np2category=Projects (internal)\n")
        assert read_folder_category(document) == "Projects (internal)"


class TestIsProjectsCategory:
    def test_the_picasa_written_value(self):
        assert is_projects_category(PROJECTS_CATEGORY) is True
        assert PROJECTS_CATEGORY == "Projects (internal)"

    def test_case_and_whitespace_tolerant(self):
        assert is_projects_category("  projects (INTERNAL) ") is True

    def test_folders_on_disk_is_not_a_project(self):
        """⚠️ A korpusz 456 `Folders on Disk` bejegyzése a MAPPÁK alá
        tartozik — ha ide esne, a Mappák nézet romlana el."""
        assert is_projects_category("Folders on Disk") is False

    def test_other_known_values_are_not_projects(self):
        for value in ("Other Stuff", "Exported Pictures", "tech", "Csilla"):
            assert is_projects_category(value) is False, value

    def test_downloaded_albums_prefix_is_not_a_project(self):
        assert is_projects_category("Downloaded Albums~otheruserid") is False

    def test_missing_value_is_not_a_project(self):
        assert is_projects_category(None) is False
        assert is_projects_category("") is False
