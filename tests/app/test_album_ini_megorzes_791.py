"""#791 — a projekt-megjelölés NEM írhatja át a felhasználó ini-jét.

## A mért adatvesztés (2026-09-07)

A `write_album_ini` a kollázs/film kimeneti mappájának `.picasa.ini`-jébe
írja a `P2category=Projects (internal)` sort. A #1088 óta ez a VALÓDI
Picasa-mappa, tehát a fájlban ott lehet a felhasználó teljes
Picasa-adata — a korpuszban ugyanezekben a fájlokban `originhash`
(1 787 db), `IIDLIST_<fiók>_lh` (6 045), `geotag` (84), `backuphash`,
feliratok.

A régi megvalósítás `splitlines()`-szal olvasott és `"\\n"`-nel fűzött
vissza, `errors="replace"` dekódolással. Három mért kár egyetlen ilyen
íráson (kitalált mintán, a valós szerkezetet követve):

| kár | mérés |
|---|---|
| **CRLF → LF** | 11 sorvégjelből 11 átíródott — az eredeti Picasa CRLF-fel ír (#2491), tehát a fájl MINDEN sora megváltozott |
| **kódolás-rontás** | latin-1 fájlban `caption=Nyári üdvözlet` → `Ny<?>ri <?>dv<?>zlet` (U+FFFD) — **visszafordíthatatlan** |
| **BOM-os fájl** | a `\\ufeff[Picasa]` első sorra nem illeszkedett a szekció-kereső → MÁSODIK `[Picasa]` szekció került a fájl végére |

Az `.picasa.ini` írásának egyetlen kapuja az `ini/` csomag API-ja
(sáv-invariáns, `CLAUDE.md`); ez a hívó megkerülte. A javítás oda vezeti
vissza, a helyben-írást (#1097, rejtett fájl) megtartva.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.app.collage_output import PROJECTS_CATEGORY, write_album_ini

#: Valósághű minta: CRLF sorvégek, a #791 öt kulcsa, kitalált értékekkel.
MINTA = (
    "[Picasa]\r\n"
    "name=Nyaralas\r\n"
    "category=Folders on Disk\r\n"
    "\r\n"
    "[kep.jpg]\r\n"
    "star=yes\r\n"
    "originhash=033f1132c8741a2b3c4d5e6f708192a3\r\n"
    "IIDLIST_teszfiok_lh=4dfe636c9cf4c302\r\n"
    "geotag=47.497912,19.040235\r\n"
    "backuphash=36003\r\n"
)


def _ini(mappa: Path, tartalom: bytes) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    ut = mappa / ".picasa.ini"
    ut.write_bytes(tartalom)
    return ut


class TestAMeglevoTartalom:
    def test_a_sorvegjelek_nem_valtoznak(self, tmp_path):
        """A CRLF→LF átírás a fájl MINDEN sorát megváltoztatja."""
        ut = _ini(tmp_path / "Kollázsok", MINTA.encode("utf-8"))

        write_album_ini(ut.parent, "Kollázsok")

        nyers = ut.read_bytes()
        assert nyers.count(b"\r\n") >= MINTA.count("\r\n")
        assert b"\n" not in nyers.replace(b"\r\n", b"")

    def test_az_ot_kulcs_sora_bajtra_megmarad(self, tmp_path):
        ut = _ini(tmp_path / "Kollázsok", MINTA.encode("utf-8"))

        write_album_ini(ut.parent, "Kollázsok")

        szoveg = ut.read_bytes().decode("utf-8")
        for sor in (
            "category=Folders on Disk",
            "originhash=033f1132c8741a2b3c4d5e6f708192a3",
            "IIDLIST_teszfiok_lh=4dfe636c9cf4c302",
            "geotag=47.497912,19.040235",
        ):
            assert f"{sor}\r\n" in szoveg, sor

    def test_a_regi_latin1_felirat_nem_lesz_kerdojel(self, tmp_path):
        """⚠️ Ez a legsúlyosabb ág: a felhasználó felirata ELVESZIK."""
        nyers = MINTA.replace(
            "star=yes", "caption=Ny\xe1ri \xfcdv\xf6zlet"
        ).encode("latin-1")
        ut = _ini(tmp_path / "Kollázsok", nyers)

        write_album_ini(ut.parent, "Kollázsok")

        adat = ut.read_bytes()
        assert b"\xef\xbf\xbd" not in adat, "U+FFFD: a felirat elveszett"
        # A betöltő latin-1-re esik vissza, tehát a vissza-írás bájtőrző:
        # az eredeti bájtsor a fájlban marad, csak a megjelölés kerül bele.
        assert b"caption=Ny\xe1ri \xfcdv\xf6zlet\r\n" in adat
        assert f"P2category={PROJECTS_CATEGORY}".encode("latin-1") in adat

    def test_bom_os_fajl_nem_kap_masodik_picasa_szekciot(self, tmp_path):
        ut = _ini(
            tmp_path / "Kollázsok", b"\xef\xbb\xbf" + MINTA.encode("utf-8")
        )

        write_album_ini(ut.parent, "Kollázsok")

        szoveg = ut.read_bytes().decode("utf-8-sig")
        assert szoveg.count("[Picasa]") == 1


class TestAMegjeloles:
    """Amit a megjelölésnek TENNIE kell — ez eddig is működött."""

    def test_uj_mappaba_a_MERT_alakot_irja(self, tmp_path):
        mappa = tmp_path / "Kollázsok"
        mappa.mkdir()

        ut = write_album_ini(mappa, "Kollázsok")

        szoveg = Path(ut).read_bytes().decode("utf-8")
        assert "[Picasa]" in szoveg
        assert f"P2category={PROJECTS_CATEGORY}" in szoveg
        assert "[encoding]" not in szoveg
        assert "name=" not in szoveg

    def test_meglevo_P2category_ertekét_nem_irja_felul(self, tmp_path):
        ut = _ini(
            tmp_path / "Kollázsok",
            b"[Picasa]\r\nP2category=Folders on Disk\r\n",
        )

        write_album_ini(ut.parent, "Kollázsok")

        assert ut.read_bytes() == b"[Picasa]\r\nP2category=Folders on Disk\r\n"

    def test_kisbetus_picasa_szekcioba_ir(self, tmp_path):
        """⚠️ A korpuszban a szekció **733 fájlban `[picasa]`**, kisbetűvel —
        ez a TÖBBSÉGI alak. Második szekciót nyitni rá adatkettőzés volna."""
        ut = _ini(tmp_path / "Kollázsok", b"[picasa]\r\nname=Nyaralas\r\n")

        write_album_ini(ut.parent, "Kollázsok")

        szoveg = ut.read_bytes().decode("utf-8")
        assert szoveg.lower().count("[picasa]") == 1
        assert f"P2category={PROJECTS_CATEGORY}\r\n" in szoveg

    def test_picasa_szekcio_nelkuli_fajlhoz_hozzafuzi(self, tmp_path):
        ut = _ini(tmp_path / "Kollázsok", b"[kep.jpg]\r\nstar=yes\r\n")

        write_album_ini(ut.parent, "Kollázsok")

        szoveg = ut.read_bytes().decode("utf-8")
        assert "star=yes\r\n" in szoveg
        assert f"P2category={PROJECTS_CATEGORY}" in szoveg
