"""#1168: a PMP-oszlopok NEM egyforma hosszúak — élő adat alakjára szabott őr.

Spec: `docs/specs/kollazs-eletciklus.md` **16.4** és
`docs/specs/pmp-database.md` (`albumdata_hascollage`).

A kutatói kör mérése a tulajdonos VALÓDI adatbázisán
(`research/testdata/Picasa2/db3/`):

| fájl | típus | sorok |
|---|---|---:|
| `albumdata_filename.pmp` | `0x0000` (sztring) | **2371** |
| `albumdata_token.pmp` | `0x0000` | **2371** |
| `albumdata_hascollage.pmp` | `0x0003` (bájt) | **2370** |
| `albumdata_inisync.pmp` | `0x0004` | **2371** |

Egy egyenlő hosszt feltételező parszer ezen a táblán elhasal. A
`read_table` ma kipótol (`test_table.py::test_sparse_columns_padded_with_none`
állítja is) — ez a fájl azt köti le, hogy az élő adat KONKRÉT alakja is
átmegy rajta: a rövidebb oszlop egy **logikai** oszlop, egyetlen sorral a
tábla vége előtt véget érve, és a hiányzó vég **alapértelmezett** (nem 1).

⚠️ A rövidülés SZÁZ sor is lehet, nem csak egy — a kipótolásnak nem
szabad a „pont eggyel rövidebb" esetre szabottnak lennie.
"""

from __future__ import annotations

from picasapy.pmpimport.table import read_table
from support.pmp_factory import build_pmp_column

#: A tulajdonos adatbázisának mérete — az arányok itt számítanak, nem a
#: nagyságrend; a 2371/2370 az élő mérés (spec 16.4).
SOROK = 2371
HASCOLLAGE_SOROK = 2370

#: Az `albumdata_hascollage.pmp` PMP-típuskódja (1 bájt/sor).
LOGIKAI = 0x0003
SZTRING = 0x0000


def _albumdata(mappa, hascollage_sorok: int = HASCOLLAGE_SOROK):
    """Az élő `albumdata` tábla alakja: két teljes sztringoszlop és egy
    rövidebb logikai oszlop."""
    (mappa / "albumdata_filename.pmp").write_bytes(
        build_pmp_column(SZTRING, [f"album{i}" for i in range(SOROK)])
    )
    (mappa / "albumdata_token.pmp").write_bytes(
        build_pmp_column(SZTRING, [f"${i:x}" for i in range(SOROK)])
    )
    (mappa / "albumdata_hascollage.pmp").write_bytes(
        build_pmp_column(LOGIKAI, [0] * hascollage_sorok)
    )
    return read_table(mappa, "albumdata")


class TestElesOszlophosszak:
    def test_a_tabla_a_LEGHOSSZABB_oszlopot_koveti(self, tmp_path):
        tabla = _albumdata(tmp_path)

        assert tabla.row_count == SOROK

    def test_a_rovidebb_oszlop_teljes_hosszan_olvashato(self, tmp_path):
        tabla = _albumdata(tmp_path)

        assert len(tabla.column("hascollage")) == SOROK

    def test_a_hianyzo_veg_alapertelmezett_nem_igaz(self, tmp_path):
        """⚠️ A kipótolt vég `None` — semmiképp nem 1. Egy „van kollázsa"
        jelzés a tábla utolsó sorára néma adathiba volna."""
        tabla = _albumdata(tmp_path)

        assert tabla.value("hascollage", SOROK - 1) is None
        assert bool(tabla.value("hascollage", SOROK - 1)) is False

    def test_a_meglevo_ertekek_a_helyukon_maradnak(self, tmp_path):
        tabla = _albumdata(tmp_path)

        assert tabla.value("hascollage", 0) == 0
        assert tabla.value("hascollage", HASCOLLAGE_SOROK - 1) == 0
        assert tabla.value("filename", SOROK - 1) == f"album{SOROK - 1}"

    def test_szaz_sorral_rovidebb_oszlop_sem_dol_be(self, tmp_path):
        """Az élő eltérés EGY sor volt, de a formátum nem ígér semmit —
        aki a kipótolást az egyes különbségre szabja, a következő
        adatbázison bukik."""
        tabla = _albumdata(tmp_path, hascollage_sorok=SOROK - 100)

        assert tabla.row_count == SOROK
        assert tabla.value("hascollage", SOROK - 101) == 0
        assert tabla.value("hascollage", SOROK - 100) is None
