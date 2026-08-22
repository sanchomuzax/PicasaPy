"""Az eltávolított mappa „sírköve" — ne jöjjön vissza újraolvasáskor (#1249).

## Az eredeti — bizonyíték

`docs/specs/picasa-mappakezelo.md` 15.: az „Eltávolítás a Picasából"
(`0x005ce590`, mód≠0) nem csak kiveszi a mappát — **sírkövet** hagy
(`0x004b9200` → `]album:removed` token), és a beolvasó ettől nem veszi fel
újra. Nálunk a `remove_root` csak prune-olt, ezért a mappa a következő
`rescan()`-nél visszajött (a jegy gépi mérése).
"""

from pathlib import Path

from picasapy.index import open_index, sync_tree
from picasapy.index.sync import (
    add_removed_folder,
    clear_removed_folders_under,
    remove_root,
    removed_folder_paths,
)
from support.jpeg_factory import make_jpeg


def _konyvtar(tmp_path):
    gyoker = tmp_path / "gyoker"
    (gyoker / "alma").mkdir(parents=True)
    make_jpeg(gyoker / "alma" / "a.jpg", size=(32, 24))
    make_jpeg(gyoker / "b.jpg", size=(32, 24))
    return gyoker


def _mappak(conn):
    return {row["path"] for row in conn.execute("SELECT path FROM folders")}


def _alma_bent_van(conn, gyoker) -> bool:
    """Pontos útvonal-illesztés — a részstring-keresés a teszt SAJÁT
    nevén (…almappakra…) is találna „alma"-t a tmp_path-ban."""
    alma = Path(str(gyoker)) / "alma"
    return any(
        Path(p) == alma or Path(p).is_relative_to(alma) for p in _mappak(conn)
    )


class TestSirko:
    def test_a_sirko_utan_a_rescan_nem_hozza_vissza(self, tmp_path):
        """⚠️ A jegy magja: ma ez a lépés bukik."""
        gyoker = _konyvtar(tmp_path)
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, gyoker)
            alma = str(gyoker / "alma")
            remove_root(conn, alma)
            add_removed_folder(conn, alma)
            assert not _alma_bent_van(conn, gyoker)

            sync_tree(conn, gyoker)  # a rescan

            assert not _alma_bent_van(conn, gyoker), (
                "az eltávolított mappa visszajött a rescan után"
            )

    def test_a_sirko_az_almappakra_is_vonatkozik(self, tmp_path):
        gyoker = _konyvtar(tmp_path)
        (gyoker / "alma" / "mely").mkdir()
        make_jpeg(gyoker / "alma" / "mely" / "m.jpg", size=(32, 24))
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, gyoker)
            alma = str(gyoker / "alma")
            remove_root(conn, alma)
            add_removed_folder(conn, alma)

            sync_tree(conn, gyoker)

            assert not _alma_bent_van(conn, gyoker)

    def test_a_torles_utan_ujra_felveheto(self, tmp_path):
        """A sírkő nem örök: az újra-hozzáadás (Mappakezelő) feloldja."""
        gyoker = _konyvtar(tmp_path)
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, gyoker)
            alma = str(gyoker / "alma")
            remove_root(conn, alma)
            add_removed_folder(conn, alma)
            sync_tree(conn, gyoker)

            clear_removed_folders_under(conn, alma)
            sync_tree(conn, gyoker)

            assert _alma_bent_van(conn, gyoker), (
                "az újra felvett mappa nem jött vissza"
            )

    def test_a_szulo_ujrafelvetele_is_felold(self, tmp_path):
        """Ha a felhasználó a SZÜLŐT veszi fel újra figyelt mappának, az
        alatta lévő sírkövek is oldódnak — különben némán hiányozna egy
        almappa, és senki nem tudná, miért."""
        gyoker = _konyvtar(tmp_path)
        with open_index(tmp_path / "i.db") as conn:
            add_removed_folder(conn, str(gyoker / "alma"))

            clear_removed_folders_under(conn, str(gyoker))

            assert removed_folder_paths(conn) == ()

    def test_a_lista_lekerdezheto(self, tmp_path):
        with open_index(tmp_path / "i.db") as conn:
            add_removed_folder(conn, "/x/egy")
            add_removed_folder(conn, "/x/ketto")
            assert set(removed_folder_paths(conn)) == {"/x/egy", "/x/ketto"}
