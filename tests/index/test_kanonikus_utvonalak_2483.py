"""#2483 ŐR: a KIHAGYOTT útvonal-feloldások mögötti invariánsok.

A #2483 teljesítmény-javítása a `sync_folder`-ben két feloldást hagy ki, és
mindkét kihagyás egy-egy **kimondatlan invariánsra** támaszkodik. Ha az
invariáns elromlik, a kár NÉMA: nem hibaüzenet lesz belőle, hanem rossz
indextartalom.

1. **A gyökér és a mappa azonossága.** Az indulási önjavító ág
   `sync_folder(conn, mappa, mappa)`-t hív; a javítás ilyenkor a `folder`
   feloldását kihagyja, és a `root` már feloldott alakját veszi át.
   Invariáns: a mappa az indexbe akkor is KANONIKUS útvonallal kerül be,
   ha a hívó nem kanonikus szöveget adott át (`..`, symlink). Enélkül
   ugyanaz a mappa két néven létezne az indexben, és a `prune_foreign_
   folders` (#58) egyiket rendre kitakarítaná.

2. **A sírkövek kanonikussága.** A `sync_folder` a `removed_folders`
   (#1249) sorait mostantól ÚJRAFELOLDÁS NÉLKÜL használja kizáró-
   készletként, arra hivatkozva, hogy az `add_removed_folder`
   `normalize_path`-szal ír. Ha ez az író elromlik (vagy egy új író
   kanonizálás nélkül ír be sort), a sírkő némán ELVESZTI a hatását: az
   „Eltávolítás a Picasából"-val kivett mappa a következő indulásnál
   visszajön — pontosan az a hiba, amit a #1249 megszüntetett.

Ezek az őrök a VISELKEDÉST rögzítik. A `tests/perf/`-beli hívásszám-őr
akkor is zöld maradna, ha a fentiek elromlanának.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from picasapy.index import open_index, sync_folder
from picasapy.index.sync import add_removed_folder, removed_folder_paths
from picasapy.paths import normalize_path
from support.jpeg_factory import make_jpeg


def _kepes_mappa(mappa: Path) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    for i in range(2):
        make_jpeg(mappa / f"IMG_{i:04d}.jpg", size=(32, 24))
    return mappa


def _mappak(conn) -> set[str]:
    return {row["path"] for row in conn.execute("SELECT path FROM folders")}


class TestKanonikusIndexUtvonal:
    """A `folder`-feloldás kihagyása nem hozhat be nem kanonikus sort."""

    def test_a_pontpont_os_alak_kanonikusan_kerul_be(self, tmp_path):
        cel = _kepes_mappa(tmp_path / "kimenet" / "Exports")
        # ugyanaz a mappa, `..`-on át megcímezve — a hívó szövege NEM
        # kanonikus, de a `root` és a `folder` szövege AZONOS, tehát a
        # #2483 rövidzárja épp ezen az ágon fut
        nyers = str(tmp_path / "kimenet" / "masik" / ".." / "Exports")
        (tmp_path / "kimenet" / "masik").mkdir()

        with open_index(tmp_path / "i.db") as conn:
            sync_folder(conn, nyers, nyers)

            assert _mappak(conn) == {str(cel)}, (
                "a nem kanonikus hívószöveg nem kanonikus indexsort adott "
                "— ugyanaz a mappa két néven létezhetne az indexben"
            )
            assert nyers not in _mappak(conn)

    @pytest.mark.skipif(
        os.name == "nt", reason="a symlink Windowson külön jogosultságot kér"
    )
    def test_a_symlinken_at_cimzett_mappa_a_valodi_utvonalra_kerul(
        self, tmp_path
    ):
        cel = _kepes_mappa(tmp_path / "valodi")
        link = tmp_path / "link"
        link.symlink_to(cel, target_is_directory=True)

        with open_index(tmp_path / "i.db") as conn:
            sync_folder(conn, str(link), str(link))

            assert _mappak(conn) == {str(cel)}, (
                "a symlinken át címzett mappa a LINK útvonalával került az "
                "indexbe — a #2483 rövidzárja feloldatlan utat engedett át"
            )

    def test_a_kulonbozo_gyoker_es_mappa_agon_is_kanonikus(self, tmp_path):
        """Kontroll: a rövidzár csak azonos szövegnél lép be, a másik ág
        (gyökér ≠ mappa) viselkedése változatlan."""
        gyoker = tmp_path / "gyoker"
        cel = _kepes_mappa(gyoker / "alma")
        nyers = str(gyoker / "alma" / "." / "")

        with open_index(tmp_path / "i.db") as conn:
            sync_folder(conn, str(gyoker), nyers)

            assert _mappak(conn) == {str(cel)}


class TestSirkoKanonikussag:
    """A sírkő-invariáns: amit a `sync_folder` feloldás nélkül használ, azt
    az író kanonikusan tette be."""

    def test_az_iro_kanonizal_nem_kanonikus_bemenetre_is(self, tmp_path):
        """Ez az az állítás, amire a #2483 kihagyása ÉPÜL."""
        cel = tmp_path / "kimenet" / "Exports"
        cel.mkdir(parents=True)
        (tmp_path / "kimenet" / "masik").mkdir()
        nyers = str(tmp_path / "kimenet" / "masik" / ".." / "Exports")

        with open_index(tmp_path / "i.db") as conn:
            add_removed_folder(conn, nyers)

            assert removed_folder_paths(conn) == (normalize_path(str(cel)),), (
                "a sírkő NEM kanonikus alakban került a `removed_folders`-be "
                "— a `sync_folder` (#2483) feloldás nélkül használja, tehát "
                "ez a sírkő némán elvesztené a hatását"
            )

    def test_a_nem_kanonikus_szovegre_tett_sirko_is_kizar(self, tmp_path):
        """Végponttól végpontig: a felhasználó „Eltávolítás a Picasából"
        döntése akkor is él, ha a hívó nem kanonikus szöveget adott át."""
        cel = _kepes_mappa(tmp_path / "kimenet" / "Exports")
        (tmp_path / "kimenet" / "masik").mkdir()
        nyers = str(tmp_path / "kimenet" / "masik" / ".." / "Exports")

        with open_index(tmp_path / "i.db") as conn:
            sync_folder(conn, str(cel), str(cel))
            assert _mappak(conn) == {str(cel)}  # pozitív kontroll

            add_removed_folder(conn, nyers)
            sync_folder(conn, str(cel), str(cel))

            assert _mappak(conn) == set(), (
                "a sírkő nem zárta ki a mappát az újraolvasáskor — az "
                "eltávolított mappa visszajött (#1249)"
            )

    def test_a_sirko_a_reszfat_is_kizarja(self, tmp_path):
        """A kizárás előtag-alapú: a sírkő alatti mappa sem jöhet vissza."""
        szulo = tmp_path / "kimenet"
        cel = _kepes_mappa(szulo / "Exports")

        with open_index(tmp_path / "i.db") as conn:
            add_removed_folder(conn, str(szulo))
            sync_folder(conn, str(cel), str(cel))

            assert _mappak(conn) == set()
