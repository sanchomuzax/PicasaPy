"""#7152: a Folder Properties mentse a fizikai mappanevet az ini-be."""

from picasapy.ini import parse_document, with_folder_name


def test_mappanev_felulirasa_megoriz_minden_mas_szekciot_es_kulcsot():
    document = parse_document(
        "[Picasa]\nname=Régi név\nlocation=Balaton\ndescription=Leírás\n"
        "[photo.jpg]\ncaption=Fotófelirat\n"
    )

    updated = with_folder_name(document, "Új név")

    assert updated.section("Picasa").get("name") == "Új név"
    assert updated.section("Picasa").get("location") == "Balaton"
    assert updated.section("Picasa").get("description") == "Leírás"
    assert updated.section("photo.jpg").get("caption") == "Fotófelirat"


def test_hianyzo_picasa_szakasz_es_name_kulcs_letrejon():
    updated = with_folder_name(parse_document("[photo.jpg]\ncaption=Fotó\n"), "Nyaralás")

    assert updated.section("Picasa").get("name") == "Nyaralás"
    assert updated.section("photo.jpg").get("caption") == "Fotó"


def test_valtozatlan_nevnel_a_dokumentum_sorositasa_valtozatlan():
    original = "[Picasa]\r\nname=Balaton\r\nlocation=Vízpart\r\n"
    document = parse_document(original)

    updated = with_folder_name(document, "Balaton")

    assert updated.serialize() == original
