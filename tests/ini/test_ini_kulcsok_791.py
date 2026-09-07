"""#791 — az öt „nem kezelt" valós ini-kulcs BÁJTRA megőrzése.

## A lelet

A valós korpusz teljes kulcs-leltára (859 fájl, 46 893 kulcs-sor) öt olyan
kulcsot mutat, amit a kódunk nem NEVESÍT, mégis sűrűn előfordul:

| kulcs | db a korpuszban |
|---|---:|
| `IIDLIST_<fiók>_lh` | 6 045 |
| `originhash` | 1 787 |
| `P2category` | 615 |
| `category` | 179 |
| `geotag` | 84 |

## Amit ez a lap ÁLLÍT

A parszerünk **kulcs-agnosztikus**: amit nem ismer, azt bájtra megőrzi.
Ez ma IGAZ — mérve mind a 859 valós fájlon: a `parse_document` →
`serialize` kör 0 eltérést adott, és egy közbeiktatott írás után is
mind a 8 710 célkulcs-példány változatlan maradt (0 elveszett,
0 elváltozott).

Ez a teszt tehát nem hibát javít, hanem **őrt állít**: ha egy jövőbeli
kör kulcs-fehérlistát vezetne be, vagy a szerializálás normalizálni
kezdene, itt bukik el — nem a felhasználó fájljában.

⚠️ A minta **kitalált**: a valós korpusz családi adatot tartalmaz (nevek,
e-mail címek, fiókazonosítók), abból ide egyetlen érték sem kerül.
"""

from __future__ import annotations

from picasapy.ini.document import parse_document
from picasapy.ini.io import load_document, save_document, update_document

#: A #791 öt kulcsa, kitalált értékekkel. Az `originhash` alakja a mérést
#: követi: **32 kisbetűs hexa karakter** (a korpusz 1787/1787 értéke ilyen).
OT_KULCS = {
    "originhash": "033f1132c8741a2b3c4d5e6f708192a3",
    "P2category": "Folders on Disk",
    "category": "Folders on Disk",
    "geotag": "47.497912,19.040235",
    "IIDLIST_teszfiok_lh": "4dfe636c9cf4c302",
}

#: Valósághű minta: az eredeti Picasa **kizárólag CRLF-fel ír** (#2491), és
#: a mappaszintű kulcsok a `[Picasa]`, a képszintűek a fájl-szekcióban
#: állnak — a korpusz szerkezetét követve.
MINTA = (
    "[Picasa]\r\n"
    "name=Nyaralas\r\n"
    "category=Folders on Disk\r\n"
    "P2category=Folders on Disk\r\n"
    "\r\n"
    "[kep.jpg]\r\n"
    "star=yes\r\n"
    "originhash=033f1132c8741a2b3c4d5e6f708192a3\r\n"
    "IIDLIST_teszfiok_lh=4dfe636c9cf4c302\r\n"
    "geotag=47.497912,19.040235\r\n"
    "backuphash=36003\r\n"
)


def _celsorok(szoveg: str) -> list[str]:
    """A minta öt célkulcsának sorai, ahogy a szövegben állnak."""
    nevek = tuple(OT_KULCS)
    return [
        sor
        for sor in szoveg.split("\r\n")
        if sor.split("=", 1)[0] in nevek
    ]


class TestParszerKorbenMegmarad:
    """`parse_document` → `serialize`: bájtra ugyanaz."""

    def test_a_kor_bajtazonos(self):
        assert parse_document(MINTA).serialize() == MINTA

    def test_mind_az_ot_kulcs_olvashato(self):
        """Nem elég megőrizni: a kulcs LÁTSZIK is a modellben."""
        doc = parse_document(MINTA)
        picasa = doc.section("Picasa")
        kep = doc.section("kep.jpg")
        assert picasa is not None and kep is not None
        assert picasa.get("category") == OT_KULCS["category"]
        assert picasa.get("P2category") == OT_KULCS["P2category"]
        assert kep.get("originhash") == OT_KULCS["originhash"]
        assert kep.get("geotag") == OT_KULCS["geotag"]
        assert kep.get("IIDLIST_teszfiok_lh") == OT_KULCS["IIDLIST_teszfiok_lh"]


class TestIrasUtanIsMegmarad:
    """Egy KÖZBEIKTATOTT írás sem viheti el őket."""

    def test_uj_kulcs_irasa_utan(self):
        doc = parse_document(MINTA).with_value("kep.jpg", "caption", "Nyar")
        assert _celsorok(doc.serialize()) == _celsorok(MINTA)

    def test_meglevo_kulcs_atirasa_utan(self):
        doc = parse_document(MINTA).with_value("kep.jpg", "star", "no")
        assert _celsorok(doc.serialize()) == _celsorok(MINTA)

    def test_mas_kulcs_torlese_utan(self):
        doc = parse_document(MINTA).with_removed("kep.jpg", "backuphash")
        assert _celsorok(doc.serialize()) == _celsorok(MINTA)

    def test_uj_szekcio_felvetele_utan(self):
        doc = parse_document(MINTA).with_value("masik.jpg", "star", "yes")
        assert _celsorok(doc.serialize()) == _celsorok(MINTA)

    def test_a_sorvegjelek_nem_valtoznak(self):
        """CRLF-ből nem lehet LF — az eredeti Picasa CRLF-et vár (#2491)."""
        doc = parse_document(MINTA).with_value("kep.jpg", "caption", "Nyar")
        assert doc.serialize().count("\r\n") == MINTA.count("\r\n") + 1


class TestLemezreIsVissza:
    """A teljes lemez-kör (`load_document` → `save_document`)."""

    def test_valtozatlan_dokumentum_bajtazonosan_ir_vissza(self, tmp_path):
        ut = tmp_path / ".picasa.ini"
        ut.write_bytes(MINTA.encode("utf-8"))

        save_document(load_document(ut), ut)

        assert ut.read_bytes() == MINTA.encode("utf-8")

    def test_update_document_utan_az_ot_kulcs_sertetlen(self, tmp_path):
        ut = tmp_path / ".picasa.ini"
        ut.write_bytes(MINTA.encode("utf-8"))

        update_document(ut, lambda d: d.with_value("kep.jpg", "caption", "Nyar"))

        szoveg = ut.read_bytes().decode("utf-8")
        assert _celsorok(szoveg) == _celsorok(MINTA)

    def test_regi_latin1_fajl_ekezetei_nem_serulnek(self, tmp_path):
        """Régi, nem UTF-8 ini: a betöltő latin-1-re esik vissza, tehát a
        vissza-írás bájtőrző. Ha valaki `errors="replace"`-szel olvasná, a
        felhasználó feliratából `?` lenne — visszafordíthatatlanul."""
        ut = tmp_path / ".picasa.ini"
        nyers = (MINTA + "caption=Nyari udvozlet\r\n").replace(
            "caption=Nyari udvozlet", "caption=Ny\xe1ri \xfcdv\xf6zlet"
        ).encode("latin-1")
        ut.write_bytes(nyers)

        save_document(load_document(ut), ut)

        assert ut.read_bytes() == nyers

    def test_bom_os_fajl_bomja_megmarad(self, tmp_path):
        ut = tmp_path / ".picasa.ini"
        nyers = b"\xef\xbb\xbf" + MINTA.encode("utf-8")
        ut.write_bytes(nyers)

        save_document(load_document(ut), ut)

        assert ut.read_bytes() == nyers


class TestHelybenIras:
    """`save_document(..., in_place=True)` — a REJTETT ini miatt (#1097).

    A csere-alapú (temp + rename) írás windowson elveszítené a rejtett
    jelzőt, ezért a projekt-megjelölés helyben ír. A bájt-eredmény
    ugyanaz kell legyen, mint az atomikus úton."""

    def test_ugyanazt_a_bajtsort_adja(self, tmp_path):
        atomi = tmp_path / "a.ini"
        helyben = tmp_path / "b.ini"
        for ut in (atomi, helyben):
            ut.write_bytes(MINTA.encode("utf-8"))

        save_document(load_document(atomi), atomi)
        save_document(load_document(helyben), helyben, in_place=True)

        assert helyben.read_bytes() == atomi.read_bytes()

    def test_rovidebb_tartalom_nem_hagy_maradekot(self, tmp_path):
        """Helyben írásnál a csonkolás elmaradása a fájl VÉGÉN hagyná a
        régi bájtokat — az ini onnantól értelmezhetetlen volna."""
        ut = tmp_path / ".picasa.ini"
        ut.write_bytes(MINTA.encode("utf-8"))

        doc = load_document(ut).with_removed("kep.jpg", "backuphash")
        save_document(doc, ut, in_place=True)

        assert ut.read_bytes() == doc.serialize().encode("utf-8")

    def test_nem_letezo_fajlt_letrehoz(self, tmp_path):
        ut = tmp_path / ".picasa.ini"

        save_document(parse_document(MINTA), ut, in_place=True)

        assert ut.read_bytes() == MINTA.encode("utf-8")
