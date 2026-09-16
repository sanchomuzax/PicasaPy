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
from picasapy.pmpimport.importer import PhotoRecord
from picasapy.pmpimport.db3_atvetel import (
    AtvetelJelentes,
    atveendo_kulcsszavak,
    helyet_atvesz,
    kulcsszavakat_atvesz,
    rekordokat_atvesz,
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


# --- a futtató: a rekordoktól a kiírt `.picasa.ini`-ig -----------------


def _rekord(ut: str, *, tags=(), lat=None, lon=None) -> PhotoRecord:
    """Egy `PhotoRecord` a futtató próbáihoz — a többi mező semleges."""
    return PhotoRecord(
        local_path=ut,
        windows_path="C:\\\\nincs",
        row=0,
        caption=None,
        rotate=None,
        star=False,
        filters=None,
        crop64=None,
        tags=tags,
        latitude=lat,
        longitude=lon,
        faces=(),
    )


def _ini(mappa) -> str:
    ut = mappa / ".picasa.ini"
    return ut.read_text(encoding="utf-8") if ut.exists() else ""


def test_futtato_kiirja_a_kulcsszot_es_a_helyet(tmp_path):
    (tmp_path / "kep.jpg").write_bytes(b"")
    jelentes = rekordokat_atvesz(
        [_rekord(str(tmp_path / "kep.jpg"), tags=("nyar",), lat=47.5, lon=19.05)]
    )
    szoveg = _ini(tmp_path)
    assert "keywords=nyar" in szoveg
    assert "geotag=47.500000,19.050000" in szoveg
    assert jelentes == AtvetelJelentes(mappak=1, kulcsszo=1, hely=1, kihagyott=0)


def test_futtato_nem_hoz_letre_ini_t_ha_nincs_mit_irni(tmp_path):
    """Üres db3-adat: a fájlhoz hozzá sem nyúlunk."""
    (tmp_path / "kep.jpg").write_bytes(b"")
    jelentes = rekordokat_atvesz([_rekord(str(tmp_path / "kep.jpg"))])
    assert not (tmp_path / ".picasa.ini").exists()
    assert jelentes == AtvetelJelentes()


def test_futtato_meglevo_erteket_nem_bant(tmp_path):
    (tmp_path / "kep.jpg").write_bytes(b"")
    (tmp_path / ".picasa.ini").write_text(
        "[kep.jpg]\nkeywords=sajat\n", encoding="utf-8"
    )
    jelentes = rekordokat_atvesz(
        [_rekord(str(tmp_path / "kep.jpg"), tags=("db3",))]
    )
    assert "keywords=sajat" in _ini(tmp_path)
    assert "db3" not in _ini(tmp_path)
    assert jelentes == AtvetelJelentes(mappak=0, kulcsszo=0, hely=0, kihagyott=1)


def test_futtato_meglevo_kulcsszo_mellett_a_helyet_beirja(tmp_path):
    (tmp_path / "kep.jpg").write_bytes(b"")
    (tmp_path / ".picasa.ini").write_text(
        "[kep.jpg]\nkeywords=sajat\n", encoding="utf-8"
    )
    jelentes = rekordokat_atvesz(
        [_rekord(str(tmp_path / "kep.jpg"), tags=("db3",), lat=1.0, lon=2.0)]
    )
    szoveg = _ini(tmp_path)
    assert "keywords=sajat" in szoveg
    assert "geotag=1.000000,2.000000" in szoveg
    assert jelentes == AtvetelJelentes(mappak=1, kulcsszo=0, hely=1, kihagyott=1)


def test_futtato_tobb_mappat_kulon_ini_be_ir(tmp_path):
    for nev in ("a", "b"):
        (tmp_path / nev).mkdir()
        (tmp_path / nev / "kep.jpg").write_bytes(b"")
    jelentes = rekordokat_atvesz(
        [
            _rekord(str(tmp_path / "a" / "kep.jpg"), tags=("egy",)),
            _rekord(str(tmp_path / "b" / "kep.jpg"), tags=("ketto",)),
        ]
    )
    assert "keywords=egy" in _ini(tmp_path / "a")
    assert "keywords=ketto" in _ini(tmp_path / "b")
    assert jelentes.mappak == 2 and jelentes.kulcsszo == 2


def test_futtato_atugorja_a_nem_letezo_mappat(tmp_path):
    """Remap nélküli útvonal: mappát NEM hozunk létre."""
    hianyzo = tmp_path / "nincs" / "kep.jpg"
    jelentes = rekordokat_atvesz([_rekord(str(hianyzo), tags=("x",))])
    assert not (tmp_path / "nincs").exists()
    assert jelentes == AtvetelJelentes()


def test_futtato_egy_ini_ben_tobb_fotot_kezel(tmp_path):
    for nev in ("a.jpg", "b.jpg"):
        (tmp_path / nev).write_bytes(b"")
    jelentes = rekordokat_atvesz(
        [
            _rekord(str(tmp_path / "a.jpg"), tags=("egy",)),
            _rekord(str(tmp_path / "b.jpg"), lat=10.0, lon=20.0),
        ]
    )
    szoveg = _ini(tmp_path)
    assert "[a.jpg]" in szoveg and "[b.jpg]" in szoveg
    assert jelentes == AtvetelJelentes(mappak=1, kulcsszo=1, hely=1, kihagyott=0)
