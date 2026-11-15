"""#7038: fizikai mappa helyének olvasása és írása az ini API-n át."""

from picasapy.ini import (
    parse_document,
    read_folder_location,
    with_folder_location,
)


def test_hianyzo_hely_ures_szovegkent_olvashato():
    assert read_folder_location(parse_document("")) == ""


def test_helyet_a_picasa_szekcioba_ir_es_olvas():
    document = parse_document("[Picasa]\ndescription=Régi leírás\n")

    updated = with_folder_location(document, "Balaton")

    assert read_folder_location(updated) == "Balaton"
    assert updated.section("Picasa").get("description") == "Régi leírás"


def test_ures_hely_torli_a_kulcsot_es_megtartja_a_tobbi_metaadatot():
    document = parse_document(
        "[Picasa]\nlocation=Balaton\ndescription=Régi leírás\n"
    )

    updated = with_folder_location(document, "  ")

    assert read_folder_location(updated) == ""
    assert updated.section("Picasa").get("location") is None
    assert updated.section("Picasa").get("description") == "Régi leírás"
