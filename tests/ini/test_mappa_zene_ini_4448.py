"""#4448: a mappa zene-beállítása a `.picasa.ini`-ben round-tripel."""

from picasapy.ini import parse_document, read_folder_music, with_folder_music


def test_mappa_zene_irasa_es_olvasasa_megoriz_minden_mas_ini_adatot():
    eredeti = parse_document("[Picasa]\ndescription=Nyári képek\n\n[kep.jpg]\ncaption=Naplemente\n")

    zenevel = with_folder_music(eredeti, True, "/zenek/tavasz.mp3")

    assert read_folder_music(zenevel) == (True, "/zenek/tavasz.mp3")
    assert "usemusic=1" in zenevel.serialize()
    assert "music=/zenek/tavasz.mp3" in zenevel.serialize()
    assert "description=Nyári képek" in zenevel.serialize()
    assert "caption=Naplemente" in zenevel.serialize()


def test_kikapcsolaskor_a_kivalasztott_fajl_megmarad_de_nem_jatszodik():
    eredeti = with_folder_music(parse_document(""), True, "/zenek/tavasz.mp3")

    kikapcsolva = with_folder_music(eredeti, False, "/zenek/tavasz.mp3")

    assert read_folder_music(kikapcsolva) == (False, "/zenek/tavasz.mp3")
    assert "usemusic=1" not in kikapcsolva.serialize()


def test_ures_fajlnev_torli_a_regi_zenefajlt():
    eredeti = with_folder_music(parse_document(""), True, "/zenek/tavasz.mp3")

    torolve = with_folder_music(eredeti, True, "  ")

    assert read_folder_music(torolve) == (True, "")
    assert "music=" not in {
        line.split("=", 1)[0]
        for line in torolve.serialize().splitlines()
        if "=" in line
    }
