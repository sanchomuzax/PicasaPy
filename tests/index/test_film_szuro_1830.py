"""#1830 — „csak filmek” szűrő a keresősávra.

Az eredeti keresősávján hat szűrőgomb ül; nálunk kettő volt (csillag,
geocímke). A `moviesearch` („Show movies only”) vegyes könyvtárban a
leggyorsabb út a videókhoz — ma végig kell görgetni értük.

A szűrő a MÁR MEGLÉVŐ `kind` indexmezőre épül (`kind = 'video'`), tehát
nem igényel sem sémaváltozást, sem újraindexelést. A valódi
`sync_tree`-vel mérünk, nem kézzel írt SQL-lel: így az is bizonyított,
hogy a `kind` a bejárás során tényleg `video`-ra áll a videófájlokon.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree, video_photos


@pytest.fixture
def conn(tmp_path):
    gyoker = tmp_path / "kepek"
    (gyoker / "a").mkdir(parents=True)
    (gyoker / "b").mkdir()
    (gyoker / "a" / "alpha.jpg").write_bytes(b"1")
    (gyoker / "a" / "nyaralas.mp4").write_bytes(b"2")
    (gyoker / "b" / "gamma.jpg").write_bytes(b"3")
    (gyoker / "b" / "buli.avi").write_bytes(b"4")
    with open_index(tmp_path / "index.db") as kapcsolat:
        sync_tree(kapcsolat, gyoker)
        yield kapcsolat


class TestAFilmSzuro:
    def test_csak_a_videokat_adja(self, conn):
        assert [p.name for p in video_photos(conn)] == [
            "nyaralas.mp4",
            "buli.avi",
        ]

    def test_a_fenykepek_kimaradnak(self, conn):
        nevek = [p.name for p in video_photos(conn)]
        assert "alpha.jpg" not in nevek
        assert "gamma.jpg" not in nevek

    def test_a_sorrend_a_tobbi_szuroet_koveti(self, conn):
        """Mappa, majd név szerint — mint a csillag-szűrőnél."""
        mappak = [p.folder_path for p in video_photos(conn)]
        assert mappak == sorted(mappak)

    def test_video_nelkuli_konyvtarra_URES(self, tmp_path):
        gyoker = tmp_path / "csak-kep"
        gyoker.mkdir()
        (gyoker / "a.jpg").write_bytes(b"1")
        with open_index(tmp_path / "i.db") as kapcsolat:
            sync_tree(kapcsolat, gyoker)
            assert video_photos(kapcsolat) == ()
