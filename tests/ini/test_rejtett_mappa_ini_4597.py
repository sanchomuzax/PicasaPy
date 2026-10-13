"""#4597 — a mappa elrejtése a `.picasa.ini` `[Picasa] P2category` sora.

Spec: `docs/specs/picasa-menu-parancsok-viselkedes.md` 32.3.1. A `Hidden
Folders` beépített kategória (nem saját gyűjtemény), az olvasó üres
`P2category` mellett a régi `category` kulcsra esik vissza, és az író a
`Hidden Folders` / `Folders on Disk` értéket az ini API-n át írja.
"""

from __future__ import annotations

from picasapy.ini import (
    is_custom_collection_category,
    is_hidden_folders_category,
    load_document,
    parse_document,
    read_folder_category,
    set_folder_hidden_in_ini,
)


class TestBeepitettKategoria:
    def test_a_hidden_folders_nem_sajat_gyujtemeny(self):
        assert is_custom_collection_category("Hidden Folders") is False

    def test_kis_nagybetu_fuggetlenul_is_beepitett(self):
        assert is_custom_collection_category("hidden folders") is False

    def test_egyeni_nev_tovabbra_is_gyujtemeny(self):
        assert is_custom_collection_category("Hidden Folders 2") is True

    def test_felismeres_ascii_kis_nagybetu_fuggetlen(self):
        assert is_hidden_folders_category(" HIDDEN folders ") is True
        assert is_hidden_folders_category("Folders on Disk") is False
        assert is_hidden_folders_category(None) is False


class TestKategoriaVisszaeses:
    def test_ures_p2category_mellett_a_category_ervenyes(self):
        document = parse_document("[Picasa]\nP2category=\ncategory=Hidden Folders\n")
        assert read_folder_category(document) == "Hidden Folders"

    def test_hianyzo_p2category_mellett_a_category_ervenyes(self):
        document = parse_document("[Picasa]\ncategory=Folders on Disk\n")
        assert read_folder_category(document) == "Folders on Disk"

    def test_a_p2category_elsobbseget_elvez(self):
        document = parse_document(
            "[Picasa]\nP2category=Other Stuff\ncategory=Hidden Folders\n"
        )
        assert read_folder_category(document) == "Other Stuff"

    def test_egyik_sincs_none(self):
        assert read_folder_category(parse_document("[Picasa]\nname=x\n")) is None


class TestElrejtesAzIniben:
    def test_ini_nelkuli_mappanal_letrejon(self, tmp_path):
        set_folder_hidden_in_ini(tmp_path, True)
        document = load_document(tmp_path / ".picasa.ini")
        assert read_folder_category(document) == "Hidden Folders"

    def test_a_tobbi_kulcs_valtozatlan(self, tmp_path):
        ini = tmp_path / ".picasa.ini"
        ini.write_text(
            "[Picasa]\nname=Nyaralás\nP2category=Other Stuff\n\n"
            "[a.jpg]\nstar=yes\n",
            encoding="utf-8",
        )
        set_folder_hidden_in_ini(tmp_path, True)
        document = load_document(ini)
        assert read_folder_category(document) == "Hidden Folders"
        assert document.section("Picasa").get("name") == "Nyaralás"
        assert document.section("a.jpg").get("star") == "yes"

    def test_megjelenites_folders_on_disk_ot_ir_nem_a_regi_gyujtemenyt(
        self, tmp_path
    ):
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[Picasa]\nP2category=Other Stuff\n", encoding="utf-8")
        set_folder_hidden_in_ini(tmp_path, True)
        set_folder_hidden_in_ini(tmp_path, False)
        assert read_folder_category(load_document(ini)) == "Folders on Disk"
