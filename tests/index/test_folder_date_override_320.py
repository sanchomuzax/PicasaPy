"""#320: a mappa-dátum kézi felülírása (`.picasa.ini` `[Picasa]` `date=`)
elsőbbséget élvez a szinkronban a legrégebbi kép ideje felett."""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "balaton").mkdir(parents=True)
    (root / "balaton" / "IMG_0001.jpg").write_bytes(b"x" * 10)
    return root


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as connection:
        yield connection


def _folder_date(conn, path):
    row = conn.execute(
        "SELECT date FROM folders WHERE path = ?", (str(path),)
    ).fetchone()
    return row["date"] if row else None


class TestFolderDateOverride:
    def test_no_override_falls_back_to_computed_date(self, conn, library):
        """EXIF nélküli teszt-JPEG-nél a számított dátum None marad — a
        lényeg, hogy felülírás hiányában NEM a fix override-ág fut le."""
        sync_tree(conn, library / "balaton")
        assert _folder_date(conn, library / "balaton") is not None
        # #2304: felülírás nélkül a SZÁMÍTOTT dátum jön — EXIF-felvételi
        # idő híján a fájlidő tartalékából. Korábban itt None állt; az a
        # kód akkori viselkedését rögzítette, nem az eredetiét.

    def test_override_wins_over_computed_date(self, conn, library):
        (library / "balaton" / ".picasa.ini").write_text(
            "[Picasa]\ndate=2015-08-20\n", encoding="utf-8"
        )
        sync_tree(conn, library / "balaton")
        assert _folder_date(conn, library / "balaton") == "2015-08-20"

    def test_removing_override_reverts_to_computed_date(self, conn, library):
        ini_path = library / "balaton" / ".picasa.ini"
        ini_path.write_text("[Picasa]\ndate=2015-08-20\n", encoding="utf-8")
        sync_tree(conn, library / "balaton")
        assert _folder_date(conn, library / "balaton") == "2015-08-20"

        ini_path.write_text("[Picasa]\nname=x\n", encoding="utf-8")
        sync_tree(conn, library / "balaton", incremental=False)
        assert _folder_date(conn, library / "balaton") is not None
        # #2304: felülírás nélkül a SZÁMÍTOTT dátum jön — EXIF-felvételi
        # idő híján a fájlidő tartalékából. Korábban itt None állt; az a
        # kód akkori viselkedését rögzítette, nem az eredetiét.

    def test_invalid_override_format_is_ignored(self, conn, library):
        (library / "balaton" / ".picasa.ini").write_text(
            "[Picasa]\ndate=nem-datum\n", encoding="utf-8"
        )
        sync_tree(conn, library / "balaton")
        assert _folder_date(conn, library / "balaton") is not None
        # #2304: felülírás nélkül a SZÁMÍTOTT dátum jön — EXIF-felvételi
        # idő híján a fájlidő tartalékából. Korábban itt None állt; az a
        # kód akkori viselkedését rögzítette, nem az eredetiét.
