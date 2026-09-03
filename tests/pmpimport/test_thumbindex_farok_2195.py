"""#2195: a `thumbindex.db` farkának hét mezője és a `*_index.db` olvasója.

## Amit a jegy MÉRÉSE pontosított

A jegy azt írta, hogy nincs olvasónk (`grep -rl "thumbindex" src/` → 0).
**Ez elavult volt:** a `read_thumb_index` régóta megvan, csak a név utáni
30 bájtból mindössze az utolsó négyet olvasta ki (szülőindex), a többi
26-ot átugrotta.

⚠️ **A spec „kiegészítő" mezője AZONOS a szülőindexszel.** Mérve a
tulajdonos katalógusán (3338 rekord): az érték **95,5%-a** a
rekordszámnál kisebb, és **150 darab** pontosan `0xFFFFFFFF` — a meglévő
olvasó „nincs szülő" jelzője. A két olvasat tehát nem mond ellent; a
spec csak nem ismerte fel, mi ez a mező.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from picasapy.pmpimport.thumbindex import (
    ThumbIndexFormatError,
    read_slot_index,
    read_thumb_index,
)

#: A tulajdonos valódi katalógusa — gitignore-olt. A próba KIHAGYJA
#: magát, ha nincs ott; nem bukik. (És útvonalat SOSEM ír a kimenetbe:
#: a katalógus magánadat.)
_VALODI = Path(
    "/home/sancho/Documents/PicasaPy/research/testdata/Picasa2-arcok/Picasa2/db3"
)


def _thumbindex(tmp_path: Path, bejegyzesek) -> Path:
    """Kis, szintetikus `thumbindex.db`."""
    darabok = [struct.pack("<II", 0x40466666, len(bejegyzesek))]
    for nev, farok in bejegyzesek:
        darabok.append(nev.encode("utf-8") + b"\x00")
        darabok.append(struct.pack("<QQIIBBI", *farok))
    ut = tmp_path / "thumbindex.db"
    ut.write_bytes(b"".join(darabok))
    return ut


def _slotindex(tmp_path, ellenorzo, eltolasok, meretek, *, verzio: float = 1.6):
    """Szintetikus `*_index.db`: verzió + NÉGY tömb, mindegyik előtt a
    saját darabszámával (#2202)."""
    darabok = [struct.pack("<f", verzio), struct.pack("<I", 0)]  # az 1. tömb ÜRES
    for tomb in (ellenorzo, eltolasok, meretek):
        darabok.append(struct.pack("<I", len(tomb)))
        darabok.append(struct.pack(f"<{len(tomb)}I", *tomb))
    ut = tmp_path / "thumbs_index.db"
    ut.write_bytes(b"".join(darabok))
    return ut


class TestAFarokHetMezeje:
    def test_mind_a_hetet_kiolvassa(self, tmp_path):
        farok = (130000000000000000, 130000000000000001, 4096, 2, 1, 1, 7)
        bejegyzesek = read_thumb_index(_thumbindex(tmp_path, [("kep.jpg", farok)]))
        b = bejegyzesek[0]
        assert b.name == "kep.jpg"
        assert b.creation_filetime == farok[0]
        assert b.access_filetime == farok[1]
        assert b.size == 4096
        assert b.kind == 2
        assert b.dirty == 1
        assert b.valid == 1
        assert b.parent_index == 7

    def test_a_szulo_index_VALTOZATLANUL_a_farok_utolso_mezeje(self, tmp_path):
        """Visszalépés-őr: a régi olvasó szemantikája megmarad."""
        nincs_szulo = (0, 0, 0, 1, 0, 1, 0xFFFFFFFF)
        b = read_thumb_index(_thumbindex(tmp_path, [("mappa", nincs_szulo)]))[0]
        assert b.parent_index == 0xFFFFFFFF
        assert b.is_directory is True

    def test_rossz_magicre_BESZEDES_hiba(self, tmp_path):
        ut = tmp_path / "rossz.db"
        ut.write_bytes(struct.pack("<II", 0xDEADBEEF, 0))
        with pytest.raises(ThumbIndexFormatError, match="magic"):
            read_thumb_index(ut)

    def test_csonka_bejegyzesre_hiba_nem_nema_nulla(self, tmp_path):
        ut = tmp_path / "csonka.db"
        ut.write_bytes(struct.pack("<II", 0x40466666, 1) + b"kep.jpg\x00" + b"\x00" * 10)
        with pytest.raises(ThumbIndexFormatError, match="Csonka"):
            read_thumb_index(ut)


class TestASlotIndex:
    """#2202: NÉGY párhuzamos tömb, nem 12 bájtos rekordok.

    ⚠️ A #2195 első változata `20 bájt fejléc + N × 12` alakban olvasta,
    és ez **némán** volt rossz: a téves és a helyes modell **bitre
    ugyanazt a fájlméretet** adja, ezért a méret-ellenőrzés átment, a
    verzió is stimmelt — csak az ÉRTÉKEK voltak szemét. Az azonos
    összméret tehát NEM igazol mezőfelosztást.
    """

    def test_a_harom_tombot_slotokka_fuzi(self, tmp_path):
        ut = _slotindex(tmp_path, [0xAA, 0xBB], [0, 100], [100, 50])
        slotok = read_slot_index(ut)
        assert [(s.slot, s.checksum, s.offset, s.size) for s in slotok] == [
            (0, 0xAA, 0, 100),
            (1, 0xBB, 100, 50),
        ]

    def test_a_MERET_also_24_bitje_szamit(self, tmp_path):
        """`0x006b5eea`: `and edx, 0xFFFFFF` — a felső bájt nem méret."""
        ut = _slotindex(tmp_path, [1], [0], [0xAB000064])
        assert read_slot_index(ut)[0].size == 0x64

    def test_a_nulla_meret_URES_slot(self, tmp_path):
        ut = _slotindex(tmp_path, [1, 2], [0, 0], [10, 0])
        slotok = read_slot_index(ut)
        assert slotok[0].ures is False
        assert slotok[1].ures is True

    def test_rossz_verziora_hiba(self, tmp_path):
        ut = _slotindex(tmp_path, [1], [0], [1], verzio=2.0)
        with pytest.raises(ThumbIndexFormatError, match="verzió"):
            read_slot_index(ut)

    def test_CSONKA_tombre_hiba(self, tmp_path):
        ut = _slotindex(tmp_path, [1, 2], [0, 1], [1, 1])
        ut.write_bytes(ut.read_bytes()[:-4])
        with pytest.raises(ThumbIndexFormatError, match="Csonka"):
            read_slot_index(ut)

    def test_MARADEKRA_hiba_nem_nema_reszleges_olvasas(self, tmp_path):
        ut = _slotindex(tmp_path, [1], [0], [1])
        ut.write_bytes(ut.read_bytes() + b"\x00\x00\x00\x00")
        with pytest.raises(ThumbIndexFormatError, match="maradék"):
            read_slot_index(ut)

    def test_ures_tabla_is_ervenyes(self, tmp_path):
        assert read_slot_index(_slotindex(tmp_path, [], [], [])) == ()


@pytest.mark.skipif(
    not (_VALODI / "thumbindex.db").is_file(),
    reason="a valódi katalógus gitignore-olt — a próba kihagyja magát",
)
class TestAValodiKatalogus:
    """A gitignore-olt, valódi adaton. Útvonalat SOSEM ír a kimenetbe."""

    def test_a_fejlec_darabszama_es_a_kiolvasott_EGYEZIK(self):
        adat = (_VALODI / "thumbindex.db").read_bytes()
        _magic, fejlec_szerint = struct.unpack_from("<II", adat, 0)
        assert len(read_thumb_index(_VALODI / "thumbindex.db")) == fejlec_szerint

    def test_a_szulo_index_ertelmes_tartomanyban_van(self):
        """A „kiegészítő" mező VALÓBAN szülőindex: az értékek túlnyomó
        része a rekordszámnál kisebb, a többi a `0xFFFFFFFF` jelző."""
        bejegyzesek = read_thumb_index(_VALODI / "thumbindex.db")
        n = len(bejegyzesek)
        ervenyes = sum(
            1 for b in bejegyzesek if b.parent_index < n or b.is_directory
        )
        assert ervenyes == n, f"{n - ervenyes} rekord szülőindexe értelmezhetetlen"

    def test_minden_TIPUS_konyvtar_szulo_NELKULI(self):
        """Mérve: a 1/5 típusú (könyvtár) rekordok MIND szülőtlenek, és
        további, 0 típusú rekordok is azok."""
        bejegyzesek = read_thumb_index(_VALODI / "thumbindex.db")
        konyvtarak = [b for b in bejegyzesek if b.kind in (1, 5)]
        assert konyvtarak, "nincs könyvtár-típusú rekord — a mérés eltört?"
        assert all(b.is_directory for b in konyvtarak)

    def test_az_utolso_blob_VEGE_az_adatfajl_merete(self):
        """#2202: a legerősebb ellenőrzés — ha a mezőfelosztás téves, ez
        azonnal elromlik. A #2195 rossz modellje ezen bukott volna el."""
        vizsgalt = 0
        for nev in ("thumbs", "albums", "previews", "bigthumbs"):
            ix = _VALODI / f"{nev}_index.db"
            adat = _VALODI / f"{nev}_0.db"
            if not (ix.is_file() and adat.is_file()):
                continue
            slotok = read_slot_index(ix)
            nem_ures = [s for s in slotok if not s.ures]
            if not nem_ures:
                continue
            vizsgalt += 1
            veg = max(s.offset + s.size for s in nem_ures)
            assert veg == adat.stat().st_size, (
                f"{nev}: a legutolsó blob vége {veg}, az adatfájl "
                f"{adat.stat().st_size} — a mezőfelosztás téves"
            )
        assert vizsgalt >= 2, f"csak {vizsgalt} tárat lehetett ellenőrizni"
