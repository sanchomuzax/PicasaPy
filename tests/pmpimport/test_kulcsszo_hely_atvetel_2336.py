"""A db3 kulcsszavainak és helyadatának átvétele a `.picasa.ini`-be (#2336).

## Mit rögzít ez a lap

Az OLVASÓ oldal a #2342 óta kész: az `importer.iter_photo_records` behozza a
`tags`, `lat`, `long` oszlopokat (a geotag tényleges jelzője a `geoview`
üressége). A tulajdonos szava a jegyen: *„Az adat ma nem az importon vész
el, hanem azon, hogy nincs fogyasztója."* Ez a modul a fogyasztó.

## A szabály: csak a HIÁNYZÓT pótoljuk

Ugyanaz az „A" szabály, ami a #3002 arcátvételét vezeti: ahol a fotónak már
van `keywords=` / `geotag=` kulcsa, ahhoz **hozzá sem nyúlunk**. A
`.picasa.ini` az igazságforrás; ha ott már áll érték, azt vagy a
felhasználó, vagy az eredeti Picasa írta — az import nem tudja, melyik a
frissebb, tehát nem is dönthet helyette.

A két adatfajta **külön** dől el: a meglévő `keywords=` nem akadálya annak,
hogy a hiányzó `geotag=` bekerüljön.
"""

from __future__ import annotations

import pytest

from picasapy.ini.document import parse_document
from picasapy.metadata.gps import parse_geotag
from picasapy.pmpimport.kulcsszo_hely_atvetel import (
    atveendo_kulcsszavak,
    helyet_atvesz,
    kulcsszavakat_atvesz,
)

URES = parse_document("")
EGY_FOTO = parse_document("[kep.jpg]\nstar=yes\n")


def _kulcsszo(dokumentum, nev: str) -> str | None:
    szakasz = dokumentum.section(nev)
    return None if szakasz is None else szakasz.get("keywords")


def _geotag(dokumentum, nev: str) -> str | None:
    szakasz = dokumentum.section(nev)
    return None if szakasz is None else szakasz.get("geotag")


# --- kulcsszavak ------------------------------------------------------


def test_kulcsszo_beirodik_ha_nincs():
    eredmeny = kulcsszavakat_atvesz(URES, "kep.jpg", ("nyaralas", "tenger"))
    assert _kulcsszo(eredmeny, "kep.jpg") == "nyaralas,tenger"


def test_meglevo_kulcsszot_nem_irja_felul():
    alap = parse_document("[kep.jpg]\nkeywords=sajat\n")
    eredmeny = kulcsszavakat_atvesz(alap, "kep.jpg", ("db3",))
    assert _kulcsszo(eredmeny, "kep.jpg") == "sajat"


def test_ures_kulcsszolista_nem_hoz_letre_kulcsot():
    eredmeny = kulcsszavakat_atvesz(EGY_FOTO, "kep.jpg", ())
    assert _kulcsszo(eredmeny, "kep.jpg") is None


def test_ures_meglevo_ertek_potolhato():
    """A `keywords=` üres értéke nem „meglévő adat" — pótolható."""
    alap = parse_document("[kep.jpg]\nkeywords=\n")
    eredmeny = kulcsszavakat_atvesz(alap, "kep.jpg", ("db3",))
    assert _kulcsszo(eredmeny, "kep.jpg") == "db3"


@pytest.mark.parametrize(
    "bemenet, vart",
    [
        ((" nyaralas ", "tenger"), "nyaralas,tenger"),
        (("nyaralas", "", "tenger"), "nyaralas,tenger"),
        (("nyaralas", "nyaralas", "tenger"), "nyaralas,tenger"),
        (("nyaralas", "  ", "tenger"), "nyaralas,tenger"),
    ],
)
def test_kulcsszavak_normalizalasa(bemenet, vart):
    assert ",".join(atveendo_kulcsszavak(bemenet)) == vart


def test_csak_ures_kulcsszo_nem_ir():
    eredmeny = kulcsszavakat_atvesz(EGY_FOTO, "kep.jpg", ("", "   "))
    assert _kulcsszo(eredmeny, "kep.jpg") is None


def test_kulcsszo_sorrendje_megmarad():
    """A duplikátum az ELSŐ előfordulás helyén marad."""
    assert atveendo_kulcsszavak(("b", "a", "b")) == ("b", "a")


# --- helyadat ---------------------------------------------------------


def test_geotag_beirodik_ha_nincs():
    eredmeny = helyet_atvesz(URES, "kep.jpg", 47.5, 19.05)
    assert _geotag(eredmeny, "kep.jpg") == "47.500000,19.050000"


def test_meglevo_geotagot_nem_irja_felul():
    alap = parse_document("[kep.jpg]\ngeotag=1.0,2.0\n")
    eredmeny = helyet_atvesz(alap, "kep.jpg", 47.5, 19.05)
    assert _geotag(eredmeny, "kep.jpg") == "1.0,2.0"


def test_hianyzo_koordinata_nem_ir():
    assert _geotag(helyet_atvesz(EGY_FOTO, "kep.jpg", None, 19.05), "kep.jpg") is None
    assert _geotag(helyet_atvesz(EGY_FOTO, "kep.jpg", 47.5, None), "kep.jpg") is None
    assert _geotag(helyet_atvesz(EGY_FOTO, "kep.jpg", None, None), "kep.jpg") is None


def test_valodi_nulla_koordinata_kimegy():
    """A `geoview` már kiszűrte a hamis nullákat — a maradék VALÓDI hely."""
    eredmeny = helyet_atvesz(URES, "kep.jpg", 0.0, 0.0)
    assert _geotag(eredmeny, "kep.jpg") == "0.000000,0.000000"


def test_ertelmetlen_koordinata_kihagyva():
    """Sérült adat `None`-t ér, nem kivételt (#301 elve)."""
    eredmeny = helyet_atvesz(URES, "kep.jpg", 999.0, 19.05)
    assert _geotag(eredmeny, "kep.jpg") is None


def test_a_beirt_geotag_visszaolvashato():
    eredmeny = helyet_atvesz(URES, "kep.jpg", -33.868820, 151.209290)
    pont = parse_geotag(_geotag(eredmeny, "kep.jpg"))
    assert pont is not None
    assert abs(pont.latitude - (-33.868820)) < 1e-6
    assert abs(pont.longitude - 151.209290) < 1e-6


# --- a kettő egymástól függetlensége ----------------------------------


def test_a_ket_adatfajta_kulon_dol_el():
    """Meglévő `keywords=` mellé a hiányzó `geotag=` beírható."""
    alap = parse_document("[kep.jpg]\nkeywords=sajat\n")
    kozben = kulcsszavakat_atvesz(alap, "kep.jpg", ("db3",))
    eredmeny = helyet_atvesz(kozben, "kep.jpg", 47.5, 19.05)
    assert _kulcsszo(eredmeny, "kep.jpg") == "sajat"
    assert _geotag(eredmeny, "kep.jpg") == "47.500000,19.050000"


def test_masik_foto_szakasza_erintetlen():
    alap = parse_document("[a.jpg]\nkeywords=eredeti\n")
    eredmeny = kulcsszavakat_atvesz(alap, "b.jpg", ("uj",))
    assert _kulcsszo(eredmeny, "a.jpg") == "eredeti"
    assert _kulcsszo(eredmeny, "b.jpg") == "uj"
