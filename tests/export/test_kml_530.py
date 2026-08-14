"""A Google Earth-export KML-építője (#530).

A szerkezet az eredeti Picasa `runtime/geotag.kml` sablonjából való; a
tesztek azt rögzítik, hogy a kimenet **érvényes XML**, a Google Earth által
elvárt csomópontokat tartalmazza, és hogy a felhasználói szövegek (felirat,
fájlnév) nem tudják kiszakítani a dokumentumot.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from picasapy.export.kml import KmlPlacemark, build_kml

KML_NS = "{http://earth.google.com/kml/2.0}"


def _pm(**kwargs) -> KmlPlacemark:
    alap = {
        "uid": "1",
        "latitude": 47.4979,
        "longitude": 19.0402,
        "name": "Budapest",
    }
    alap.update(kwargs)
    return KmlPlacemark(**alap)


def _elemzes(xml_text: str) -> ET.Element:
    """A kimenet elemzése — ez önmagában is állítás: érvénytelen XML-nél
    az `ET.fromstring` kivételt dob."""
    return ET.fromstring(xml_text)


class TestDokumentumVaz:
    def test_ervenyes_xml_es_kml_gyoker(self) -> None:
        gyoker = _elemzes(build_kml((_pm(),), folder_name="Nyaralás"))

        assert gyoker.tag == f"{KML_NS}kml"

    def test_ures_listanal_is_ervenyes(self) -> None:
        """A hívó dönthet úgy, hogy üres exportot is kiír — ne dőljön el."""
        gyoker = _elemzes(build_kml((), folder_name="Üres"))

        mappa = gyoker.find(f"{KML_NS}Document/{KML_NS}Folder")
        assert mappa is not None
        assert mappa.findall(f"{KML_NS}Placemark") == []

    def test_a_mappa_neve_es_nyitottsaga(self) -> None:
        gyoker = _elemzes(build_kml((_pm(),), folder_name="Nyaralás 2019"))

        mappa = gyoker.find(f"{KML_NS}Document/{KML_NS}Folder")
        assert mappa.find(f"{KML_NS}name").text == "Nyaralás 2019"
        assert mappa.find(f"{KML_NS}open").text == "1"

    def test_a_keltezes_elhagyhato(self) -> None:
        """A modul nem olvas órát — a keltezést a hívó adja, üresnél kimarad
        (így a teszt determinisztikus)."""
        gyoker = _elemzes(build_kml((_pm(),), folder_name="M"))

        mappa = gyoker.find(f"{KML_NS}Document/{KML_NS}Folder")
        assert mappa.find(f"{KML_NS}description") is None


class TestStilusok:
    """Az eredeti képenként KÉT stílust és egy StyleMap-et ad."""

    def test_ket_stilus_es_egy_stylemap_kepenkent(self) -> None:
        gyoker = _elemzes(
            build_kml((_pm(uid="a"), _pm(uid="b")), folder_name="M")
        )
        dok = gyoker.find(f"{KML_NS}Document")

        assert len(dok.findall(f"{KML_NS}Style")) == 4
        assert len(dok.findall(f"{KML_NS}StyleMap")) == 2

    def test_a_kiemelt_ikon_ketszeres(self) -> None:
        gyoker = _elemzes(build_kml((_pm(uid="a"),), folder_name="M"))
        dok = gyoker.find(f"{KML_NS}Document")

        kiemelt = [
            s
            for s in dok.findall(f"{KML_NS}Style")
            if s.get("id") == "picasaDisplayHighlight_a"
        ]
        assert len(kiemelt) == 1
        scale = kiemelt[0].find(f"{KML_NS}IconStyle/{KML_NS}scale")
        assert scale is not None and scale.text == "2"

    def test_a_felirat_alapbol_rejtett(self) -> None:
        """`LabelStyle/scale = 0` — sok képnél a kiírt nevek olvashatatlanná
        tennék a térképet; a felirat a buborékban jelenik meg."""
        gyoker = _elemzes(build_kml((_pm(uid="a"),), folder_name="M"))
        dok = gyoker.find(f"{KML_NS}Document")

        normal = [
            s
            for s in dok.findall(f"{KML_NS}Style")
            if s.get("id") == "picasaDisplayNormal_a"
        ][0]
        assert normal.find(f"{KML_NS}LabelStyle/{KML_NS}scale").text == "0"

    def test_a_stylemap_a_ket_stilusra_mutat(self) -> None:
        gyoker = _elemzes(build_kml((_pm(uid="x"),), folder_name="M"))
        dok = gyoker.find(f"{KML_NS}Document")

        parok = dok.find(f"{KML_NS}StyleMap").findall(f"{KML_NS}Pair")
        hivatkozasok = {
            p.find(f"{KML_NS}key").text: p.find(f"{KML_NS}styleUrl").text
            for p in parok
        }
        assert hivatkozasok == {
            "normal": "#picasaDisplayNormal_x",
            "highlight": "#picasaDisplayHighlight_x",
        }


class TestHelyjelzo:
    def test_a_koordinata_hosszusag_szelesseg_sorrendben(self) -> None:
        """A KML sorrendje: hosszúság, szélesség, magasság — a felcserélés
        a képeket a Föld túloldalára tenné."""
        gyoker = _elemzes(
            build_kml(
                (_pm(latitude=47.5, longitude=19.0),), folder_name="M"
            )
        )

        pont = gyoker.find(
            f"{KML_NS}Document/{KML_NS}Folder/{KML_NS}Placemark/"
            f"{KML_NS}Point/{KML_NS}coordinates"
        )
        assert pont.text == "19.000000,47.500000,0"

    def test_a_nezopont_a_kep_helyere_nez(self) -> None:
        gyoker = _elemzes(
            build_kml(
                (_pm(latitude=47.5, longitude=19.0),),
                folder_name="M",
                look_at_range_m=500.0,
            )
        )

        nezopont = gyoker.find(
            f"{KML_NS}Document/{KML_NS}Folder/{KML_NS}Placemark/{KML_NS}LookAt"
        )
        assert nezopont.find(f"{KML_NS}latitude").text == "47.500000"
        assert nezopont.find(f"{KML_NS}longitude").text == "19.000000"
        assert nezopont.find(f"{KML_NS}range").text == "500.0"

    def test_a_nev_a_helyjelzoben(self) -> None:
        gyoker = _elemzes(build_kml((_pm(name="Halászbástya"),), folder_name="M"))

        helyjelzo = gyoker.find(
            f"{KML_NS}Document/{KML_NS}Folder/{KML_NS}Placemark"
        )
        assert helyjelzo.find(f"{KML_NS}name").text == "Halászbástya"

    def test_a_belyegkep_es_a_felirat_a_buborekban(self) -> None:
        gyoker = _elemzes(
            build_kml(
                (
                    _pm(
                        thumb_href="thumbs/a.jpg",
                        thumb_width=160,
                        thumb_height=120,
                        caption="Naplemente",
                        file_date="2019-07-14",
                    ),
                ),
                folder_name="M",
            )
        )

        leiras = gyoker.find(
            f"{KML_NS}Document/{KML_NS}Folder/{KML_NS}Placemark/{KML_NS}description"
        ).text
        assert 'src="thumbs/a.jpg"' in leiras
        assert 'width="160"' in leiras and 'height="120"' in leiras
        assert "Naplemente" in leiras
        assert "2019-07-14" in leiras

    def test_nincs_halott_google_hivatkozas(self) -> None:
        """Az eredeti buborék alján egy megszűnt szolgáltatásra mutató logó
        állt — halott hivatkozást nem exportálunk."""
        szoveg = build_kml((_pm(thumb_href="t.jpg"),), folder_name="M")

        assert "picasa.google.com" not in szoveg


class TestBeviteliVedelem:
    """A felirat és a fájlnév a FELHASZNÁLÓTÓL jön — nem szakíthatja ki a
    dokumentumot."""

    @pytest.mark.parametrize(
        "rosszindulatu",
        [
            "</name></Placemark>",
            "idézőjel \" és & jel",
            "<script>alert(1)</script>",
        ],
    )
    def test_a_nev_nem_torheti_el_az_xml_t(self, rosszindulatu: str) -> None:
        gyoker = _elemzes(
            build_kml((_pm(name=rosszindulatu),), folder_name="M")
        )

        helyjelzo = gyoker.find(
            f"{KML_NS}Document/{KML_NS}Folder/{KML_NS}Placemark"
        )
        assert helyjelzo.find(f"{KML_NS}name").text == rosszindulatu

    def test_a_cdata_lezarasa_nem_szakithato_ki(self) -> None:
        """Egy `]]>` a feliratban kiszakítaná a CDATA-blokkot, és
        érvénytelen KML-t adna."""
        gyoker = _elemzes(
            build_kml((_pm(caption="vége ]]> utána"),), folder_name="M")
        )

        leiras = gyoker.find(
            f"{KML_NS}Document/{KML_NS}Folder/{KML_NS}Placemark/{KML_NS}description"
        ).text
        assert "]]>" not in leiras.replace("]]&gt;", "")

    def test_a_mappanev_is_vedve_van(self) -> None:
        gyoker = _elemzes(build_kml((_pm(),), folder_name="A & B </name>"))

        mappa = gyoker.find(f"{KML_NS}Document/{KML_NS}Folder")
        assert mappa.find(f"{KML_NS}name").text == "A & B </name>"
