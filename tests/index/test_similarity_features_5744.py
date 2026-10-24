"""A hasonlósági jellemző-cache sémája és dHash-megőrzése (#5744)."""

from picasapy.index import open_index
from picasapy.index.similarity_features import (
    load_similarity_features,
    save_similarity_features,
)


def test_hasonlosagi_cache_fajlazonossag_alapjan_ment_es_tolt(tmp_path):
    db = tmp_path / "index.db"
    kulcs = (str(tmp_path / "a.jpg"), 123, 456)
    jellemzők = ((1,) * 64, (2,) * 216, (0.5,) * 8)

    with open_index(db) as conn:
        save_similarity_features(conn, [(*kulcs, jellemzők)])
        conn.commit()
        assert load_similarity_features(conn, [kulcs]) == {kulcs: jellemzők}


def test_v25_migracio_megtartja_a_dhash_t_es_letrehozza_az_uj_tablat(tmp_path):
    from picasapy.index.hashes import load_dhashes, save_dhashes

    db = tmp_path / "regi-index.db"
    kulcs = (str(tmp_path / "régi.jpg"), 456, 789)

    with open_index(db) as conn:
        save_dhashes(conn, [(*kulcs, 0xFEDCBA9876543210)])
        conn.commit()
        conn.execute("DROP TABLE photo_similarity")
        conn.execute("PRAGMA user_version=25")

    with open_index(db) as conn:
        assert load_dhashes(conn, [kulcs]) == {kulcs: 0xFEDCBA9876543210}
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name='photo_similarity'"
        ).fetchone()[0] == 1
