"""#1168: a `hascollage` MEGFELELŐJE — album-szintű, származtatott jelző.

Spec: `docs/specs/pmp-database.md` („Az `albumdata_hascollage` oszlop") és
`docs/specs/kollazs-eletciklus.md` 16.4.

⚠️ **A jegy kérdése hamis alternatívát kínált** („a forrásképekre vagy a
kimeneti képre?"): egyikre sem. A K6-os visszafejtés szerint a
`hascollage` **nem képoszlop, hanem ALBUM-oszlop**
(`albumdata_hascollage.pmp`, egy bájt albumonként), és a jelentése:

> „ehhez az albumhoz tartozik egy mentett `PicasaCollage.cxf` fájl".

Az eredeti sem a kollázs mentésekor írja: az album mentése/betöltése
(`0x005608f0`) megnézi, LÉTEZIK-e a `<az album mappája>\\PicasaCollage.cxf`
(`0x0047c3f0` építi az útvonalat), és abból lesz a bájt 1.

**Ezért nálunk sincs szükség séma-oszlopra.** A jelző fájl-létezésből
számolható — a `project_folders.py` bevált mintája (ott is direkt
lemez-olvasás áll a séma-bővítés helyett, mert a `schema.py` az
integrátoré, és egy új oszlopot csak teljes újraindexelés töltene fel).
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree

_ALBUM = "[.album:$abc123]\nname=Nyaralás\n"
_MASIK = "[.album:$def456]\nname=Karácsony\n"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    for name in ("nyaralas", "karacsony", "ini_nelkul"):
        (root / name).mkdir(parents=True)
        (root / name / "IMG_0001.jpg").write_bytes(b"x" * 10)
    (root / "nyaralas" / ".picasa.ini").write_text(_ALBUM, encoding="utf-8")
    (root / "karacsony" / ".picasa.ini").write_text(_MASIK, encoding="utf-8")
    # CSAK a nyaralásnak van kollázs-projektje
    (root / "nyaralas" / "PicasaCollage.cxf").write_text("<xml/>", encoding="utf-8")
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


class TestMappaSzintuJelzo:
    def test_a_PicasaCollage_cxf_jelenti_a_kollazst(self, tmp_path, library):
        from picasapy.index.album_collage import folder_has_collage

        assert folder_has_collage(library / "nyaralas") is True

    def test_nelkule_nincs(self, tmp_path, library):
        from picasapy.index.album_collage import folder_has_collage

        assert folder_has_collage(library / "karacsony") is False

    def test_nem_letezo_mappara_hamis_nem_kivetel(self, tmp_path):
        from picasapy.index.album_collage import folder_has_collage

        assert folder_has_collage(tmp_path / "nincs-ilyen") is False

    def test_a_kollazs_kepe_MAGABAN_nem_eleg(self, tmp_path, library):
        """A `.jpg` bárhonnan odakerülhet; az eredeti a `.cxf`-et nézi."""
        from picasapy.index.album_collage import folder_has_collage

        (library / "karacsony" / "Karácsony.jpg").write_bytes(b"x" * 10)

        assert folder_has_collage(library / "karacsony") is False

    def test_a_nev_kis_nagybetu_fuggetlen(self, tmp_path, library):
        """A tulajdonos könyvtárában kisbetűs fájlnevek is előfordulnak
        (MEMORY: a `thumbindex.db`/`thumbs_index.db` esete)."""
        from picasapy.index.album_collage import folder_has_collage

        (library / "karacsony" / "picasacollage.cxf").write_text("", encoding="utf-8")

        assert folder_has_collage(library / "karacsony") is True


class TestAlbumSzintuJelzo:
    def test_csak_a_kollazsos_album_tokenje_jon_vissza(self, conn):
        from picasapy.index.album_collage import albums_with_collage

        assert albums_with_collage(conn) == frozenset({"$abc123"})

    def test_kollazs_nelkul_ures(self, tmp_path, library):
        from picasapy.index.album_collage import albums_with_collage

        (library / "nyaralas" / "PicasaCollage.cxf").unlink()
        with open_index(tmp_path / "masik.db") as connection:
            sync_tree(connection, library)

            assert albums_with_collage(connection) == frozenset()

    def test_ugyanaz_a_token_tobb_mappaban_EGYSZER_szamit(self, tmp_path):
        """A Picasa minden érintett mappába kiírja az album-definíciót —
        elég, ha az EGYIKBEN ott a kollázs (a `.cxf` egy albumhoz tartozik,
        nem mappánként külön)."""
        from picasapy.index.album_collage import albums_with_collage

        root = tmp_path / "kepek"
        for name in ("egy", "ketto"):
            (root / name).mkdir(parents=True)
            (root / name / "IMG_0001.jpg").write_bytes(b"x" * 10)
            (root / name / ".picasa.ini").write_text(_ALBUM, encoding="utf-8")
        (root / "ketto" / "PicasaCollage.cxf").write_text("", encoding="utf-8")

        with open_index(tmp_path / "index.db") as connection:
            sync_tree(connection, root)

            assert albums_with_collage(connection) == frozenset({"$abc123"})

    def test_a_lekerdezes_nem_ir_a_semaba(self, conn):
        """⚠️ A `schema.py` az integrátoré — ez a jelző SZÁRMAZTATOTT,
        nem tárolt. Ha valaha oszlop lesz belőle, az külön döntés."""
        from picasapy.index.album_collage import albums_with_collage

        albums_with_collage(conn)
        oszlopok = {
            sor["name"] for sor in conn.execute("PRAGMA table_info(albums)")
        }

        assert "has_collage" not in oszlopok and "hascollage" not in oszlopok
