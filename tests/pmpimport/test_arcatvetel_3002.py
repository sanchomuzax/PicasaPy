"""A db3 arcadatának átvétele a `.picasa.ini`-be — a #3002 őre.

## A döntés, amit ez a lap rögzít

A jegy három szabályt kínált arra az esetre, ha a db3-ban van arc, a fotó
ini-jében viszont nincs (vagy más van). Az **A** maradt (a jegy javaslata):

> **csak a HIÁNYZÓT pótoljuk**: ahol az ini-ben nincs `faces=`, oda beírjuk
> a db3-ból származót; ahol van, hozzá sem nyúlunk.

Indok: az `A` **soha nem ír felül meglévő adatot**, tehát nem ronthat el
semmit. A `.picasa.ini` az igazságforrás; ha ott már áll arc, azt vagy a
felhasználó, vagy az eredeti Picasa írta — az import nem tudja, melyik a
frissebb, tehát nem is dönthet helyette.

## A mintakészlet: GENERÁLT, de VALÓDI formátumú db3

A jegy a tulajdonos saját db3-mentéjét nevezi meg őrforrásnak
(`research/testdata/Picasa2-arcok/`) — az viszont **gitignore-olt**, mert
valódi családtagok nevét tartalmazza. A CI-n tehát nem futhat.

Ezért a próbák a `pmpimport` saját írójával **állítanak elő** db3-at: a
`.pmp` oszlopfejléc és a `thumbindex` szerkezete megfejtett és
dokumentált, tehát a generált készlet **ugyanazon a beolvasón** megy át,
mint az éles adat. Ami ezzel nem mérhető (valódi nevek, duplikált
kontaktok, a készlet mérete), azt a jegy nevesíti.
"""

from __future__ import annotations

import struct

import pytest

from picasapy.ini.contacts import contacts_of, find_contact_id
from picasapy.ini.document import parse_document
from picasapy.ini.faces import parse_faces
from picasapy.pmpimport.arcatvetel import (
    FRVERSION,
    ISMERETLEN_SZEMELY,
    atveendo_arcok,
    arcokat_atvesz,
)
from picasapy.pmpimport.deferredregion import DeferredFace
from picasapy.ini.rect64 import Rect64

MAGIC = 0x3FCCCCCD
CONST_1332 = 0x1332
CONST_2 = 0x00000002
#: a `deferredregion` oszlop típusa (`pmp_column.OSZLOP_TIPUSOK`)
SZOVEG = 0x00


def _pmp_szoveg(ut, ertekek: list[str]) -> None:
    """Egy szöveges `.pmp` oszlop kiírása — a `test_pmp_oszlop_tipus_2521`
    `_pmp` segédjének alakja, listányi értékkel."""
    fej = struct.pack(
        "<IHHIHHI", MAGIC, SZOVEG, CONST_1332, CONST_2,
        SZOVEG, CONST_1332, len(ertekek),
    )
    test = b"".join(ertek.encode("utf-8") + b"\x00" for ertek in ertekek)
    ut.write_bytes(fej + test)


def _ertek(dokumentum, szakasz_nev: str, kulcs: str) -> str | None:
    szakasz = dokumentum.section(szakasz_nev)
    return None if szakasz is None else szakasz.get(kulcs)


def _rect(x: float = 0.1) -> Rect64:
    """A `Rect64` koordinatai RELATIVAK ([0..1]), nem kepontok."""
    return Rect64(left=x, top=x, right=x + 0.2, bottom=x + 0.2)


class TestAzAtveendoArcokSzurese:
    """Mi számít átveendő arcnak (a spec 10. táblája)."""

    def test_a_nevesitett_arc_atveendo(self) -> None:
        arcok = (DeferredFace(rect=_rect(), name="Kiss Anna"),)
        assert atveendo_arcok(arcok) == arcok

    def test_az_ISMERETLEN_szentinel_NEM_szemely(self) -> None:
        """A spec 10. táblájának 6. sora: a csupa `f` azonosító az
        „ismeretlen" szentinel — nem személyként importáljuk."""
        arcok = (DeferredFace(rect=_rect(), name=ISMERETLEN_SZEMELY),)
        assert atveendo_arcok(arcok) == ()

    def test_az_ures_nevu_arc_kimarad(self) -> None:
        assert atveendo_arcok((DeferredFace(rect=_rect(), name=""),)) == ()
        assert atveendo_arcok((DeferredFace(rect=_rect(), name="   "),)) == ()

    def test_a_szentinel_a_tobbit_nem_viszi_magaval(self) -> None:
        jo = DeferredFace(rect=_rect(0.5), name="Nagy Béla")
        arcok = (DeferredFace(rect=_rect(), name=ISMERETLEN_SZEMELY), jo)
        assert atveendo_arcok(arcok) == (jo,)


class TestAzIniBeIras:
    def test_ures_iniben_letrejon_a_faces_es_a_kontakt(self) -> None:
        dok = parse_document("")
        uj = arcokat_atvesz(
            dok, "kep.jpg", (DeferredFace(rect=_rect(), name="Kiss Anna"),)
        )
        arcok = parse_faces(_ertek(uj, "kep.jpg", "faces") or "")
        assert len(arcok) == 1
        azonosito = find_contact_id(uj, "Kiss Anna")
        assert azonosito is not None
        assert arcok[0].contact_id == azonosito
        # a rect64 16 bitre kvantal, tehat a kerekites utan nem bitre
        # azonos a bemenettel — a TURESE a kvantalas lepese (1/65535)
        varhato = _rect()
        for mezo in ("left", "top", "right", "bottom"):
            assert getattr(arcok[0].rect, mezo) == pytest.approx(
                getattr(varhato, mezo), abs=2 / 65535
            )

    def test_a_frversion_15_kerul_be(self) -> None:
        """A spec 10/10: aki importál, `1.5`-öt írjon."""
        uj = arcokat_atvesz(
            parse_document(""), "kep.jpg",
            (DeferredFace(rect=_rect(), name="Kiss Anna"),),
        )
        assert FRVERSION == "1.5"
        assert _ertek(uj, "Picasa", "frversion") == FRVERSION

    def test_A_SZABALY_a_meglevo_faces_hez_HOZZA_SEM_NYUL(self) -> None:
        """⛔ Ez a jegy döntése: meglévő adatot nem írunk felül."""
        eredeti = "[kep.jpg]\nfaces=rect64(1111111111111111),abcdef0123456789\n"
        dok = parse_document(eredeti)
        uj = arcokat_atvesz(
            dok, "kep.jpg", (DeferredFace(rect=_rect(), name="Kiss Anna"),)
        )
        assert _ertek(uj, "kep.jpg", "faces") == _ertek(dok, "kep.jpg", "faces")
        assert find_contact_id(uj, "Kiss Anna") is None, (
            "meglévő `faces=` mellett kontaktot sem hozunk létre — az "
            "árva bejegyzés lenne"
        )
        assert _ertek(uj, "Picasa", "frversion") is None

    def test_a_MEGLEVO_kontakt_azonositoja_ujrahasznosul(self) -> None:
        """Ha a név már szerepel a `[Contacts2]`-ben, ne kapjon második
        azonosítót — különben egy személy kétfelé válna a mappában."""
        dok = parse_document("[Contacts2]\naaaabbbbccccdddd=Kiss Anna;;\n")
        uj = arcokat_atvesz(
            dok, "kep.jpg", (DeferredFace(rect=_rect(), name="Kiss Anna"),)
        )
        assert len(contacts_of(uj)) == 1
        assert parse_faces(_ertek(uj, "kep.jpg", "faces"))[0].contact_id == (
            "aaaabbbbccccdddd"
        )

    def test_ket_arc_ket_kontakt(self) -> None:
        uj = arcokat_atvesz(
            parse_document(""), "kep.jpg",
            (
                DeferredFace(rect=_rect(0.1), name="Kiss Anna"),
                DeferredFace(rect=_rect(0.4), name="Nagy Béla"),
            ),
        )
        assert len(parse_faces(_ertek(uj, "kep.jpg", "faces"))) == 2
        assert len(contacts_of(uj)) == 2

    def test_ugyanaz_a_nev_ketszer_EGY_kontaktot_kap(self) -> None:
        """#3002 / a spec 10/7: a duplikált kontakt előfordul — tűrjük."""
        uj = arcokat_atvesz(
            parse_document(""), "kep.jpg",
            (
                DeferredFace(rect=_rect(0.1), name="Kiss Anna"),
                DeferredFace(rect=_rect(0.4), name="Kiss Anna"),
            ),
        )
        assert len(parse_faces(_ertek(uj, "kep.jpg", "faces"))) == 2
        assert len(contacts_of(uj)) == 1

    def test_arc_nelkul_a_dokumentum_VALTOZATLAN(self) -> None:
        dok = parse_document("[kep.jpg]\nstar=yes\n")
        assert arcokat_atvesz(dok, "kep.jpg", ()).serialize() == dok.serialize()


class TestAValodiDb3Olvasoval:
    """A generált db3 ugyanazon a beolvasón megy át, mint az éles adat."""

    def test_a_deferredregion_oszlopbol_atveheto_arc_lesz(self, tmp_path) -> None:
        from picasapy.pmpimport.table import read_table

        db3 = tmp_path / "db3"
        db3.mkdir()
        _pmp_szoveg(
            db3 / "imagedata_deferredregion.pmp",
            ["rect64(199a199a4ccd4ccd),Kiss Anna;", ""],
        )
        tabla = read_table(db3, "imagedata")
        nyers = tabla.value("deferredregion", 0)
        assert nyers and "Kiss Anna" in nyers

        from picasapy.pmpimport.deferredregion import parse_deferred_region

        arcok = atveendo_arcok(parse_deferred_region(nyers))
        assert len(arcok) == 1 and arcok[0].name == "Kiss Anna"

    def test_az_ures_sor_nem_ad_arcot(self, tmp_path) -> None:
        from picasapy.pmpimport.deferredregion import parse_deferred_region
        from picasapy.pmpimport.table import read_table

        db3 = tmp_path / "db3"
        db3.mkdir()
        _pmp_szoveg(db3 / "imagedata_deferredregion.pmp", ["", ""])
        tabla = read_table(db3, "imagedata")
        assert atveendo_arcok(parse_deferred_region(tabla.value("deferredregion", 1))) == ()


@pytest.mark.parametrize("nev", ["", "   ", ISMERETLEN_SZEMELY])
def test_a_kihagyott_nevekre_nem_keletkezik_kontakt(nev: str) -> None:
    uj = arcokat_atvesz(
        parse_document(""), "kep.jpg", (DeferredFace(rect=_rect(), name=nev),)
    )
    assert _ertek(uj, "kep.jpg", "faces") is None
    assert contacts_of(uj) == ()
