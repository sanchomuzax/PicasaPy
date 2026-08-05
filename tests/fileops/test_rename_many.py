"""rename_photos_many / preview_name: tömeges átnevezés a `rename.fen`
szerint (#366) — alapnév + opcionális dátum-/felbontás-utótag, Picasa-
mintájú sorszámozás (`név`, `név-1`, `név-2`…), ütközés-kezelés, és az
egyfájlos `rename_photo` (ini-átvitel!) újrafelhasználása fájlonként."""

import pytest

from picasapy.fileops.rename import RenameItem, preview_name, rename_photos_many
from picasapy.ini import load_document


class TestPreviewName:
    def test_base_name_only(self):
        item = RenameItem(path=None, date="2025-05-01", width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=False, include_size=False,
                sequence=0, ext=".jpg",
            )
            == "nyaralas.jpg"
        )

    def test_with_date_suffix(self):
        item = RenameItem(path=None, date="2025-05-01T07:00:00", width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=True, include_size=False,
                sequence=0, ext=".jpg",
            )
            == "nyaralas 2025-05-01.jpg"
        )

    def test_with_size_suffix(self):
        item = RenameItem(path=None, date=None, width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=False, include_size=True,
                sequence=0, ext=".jpg",
            )
            == "nyaralas 800x600.jpg"
        )

    def test_with_both_suffixes(self):
        item = RenameItem(path=None, date="2025-05-01", width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=True, include_size=True,
                sequence=0, ext=".jpg",
            )
            == "nyaralas 2025-05-01 800x600.jpg"
        )

    def test_missing_metadata_is_silently_skipped(self):
        # ha a kép nem ismert dátumot/felbontást, a hiányzó utótag kimarad
        # (nem "None" vagy hibás szöveg kerül a névbe)
        item = RenameItem(path=None, date=None, width=None, height=None)
        assert (
            preview_name(
                "nev", item, include_date=True, include_size=True,
                sequence=0, ext=".png",
            )
            == "nev.png"
        )

    def test_sequence_zero_has_no_suffix_further_ones_do(self):
        item = RenameItem(path=None)
        assert preview_name("nev", item, sequence=0, ext=".jpg") == "nev.jpg"
        assert preview_name("nev", item, sequence=1, ext=".jpg") == "nev-1.jpg"
        assert preview_name("nev", item, sequence=2, ext=".jpg") == "nev-2.jpg"


class TestRenamePhotosMany:
    def test_renames_with_picasa_sequence_pattern(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        c = tmp_path / "c.jpg"
        for f in (a, b, c):
            f.write_bytes(b"kep")
        items = [RenameItem(path=a), RenameItem(path=b), RenameItem(path=c)]
        results = rename_photos_many(items, "nyaralas")
        assert results == [
            tmp_path / "nyaralas.jpg",
            tmp_path / "nyaralas-1.jpg",
            tmp_path / "nyaralas-2.jpg",
        ]
        for path in results:
            assert path.exists()
        assert not a.exists()
        assert not b.exists()
        assert not c.exists()

    def test_date_and_size_suffix_applied_per_file(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"kep")
        b.write_bytes(b"kep")
        items = [
            RenameItem(path=a, date="2025-05-01", width=800, height=600),
            RenameItem(path=b, date="2025-06-02", width=1024, height=768),
        ]
        results = rename_photos_many(
            items, "nyar", include_date=True, include_size=True
        )
        assert results == [
            tmp_path / "nyar 2025-05-01 800x600.jpg",
            tmp_path / "nyar 2025-06-02 1024x768-1.jpg",
        ]

    def test_ini_sections_follow_each_renamed_file(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"kep")
        b.write_bytes(b"kep")
        ini = tmp_path / ".picasa.ini"
        ini.write_text(
            "[a.jpg]\nstar=yes\n[b.jpg]\ncaption=nyar\n", encoding="utf-8"
        )
        items = [RenameItem(path=a), RenameItem(path=b)]
        rename_photos_many(items, "nyaralas")
        document = load_document(ini)
        assert document.section("a.jpg") is None
        assert document.section("b.jpg") is None
        assert document.section("nyaralas.jpg").get("star") == "yes"
        assert document.section("nyaralas-1.jpg").get("caption") == "nyar"

    def test_no_op_when_new_name_equals_current_name(self, tmp_path):
        # egyetlen fájlnál, ha az utótagok nélküli alapnév megegyezik a
        # jelenlegi (kiterjesztés nélküli) névvel, nincs tényleges átnevezés
        photo = tmp_path / "nyaralas.jpg"
        photo.write_bytes(b"kep")
        results = rename_photos_many([RenameItem(path=photo)], "nyaralas")
        assert results == [photo]
        assert photo.exists()

    def test_empty_batch_returns_empty_list(self):
        assert rename_photos_many([], "nev") == []

    def test_invalid_base_name_raises(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        with pytest.raises(ValueError):
            rename_photos_many([RenameItem(path=photo)], "al/nev")

    def test_duplicate_target_names_raise_without_renaming(self, tmp_path):
        # két azonos kiterjesztésű fájl, de a dátum/felbontás-utótag
        # kikapcsolva és mindkettőnek UGYANAZ lenne az 1. tagja → csak akkor
        # ütközik igazán, ha a hívó szándékosan ugyanazt a sorszámot adná;
        # itt közvetlenül a belső ütközés-ellenőrzést provokáljuk ugyanolyan
        # kiterjesztésű, de eltérő mappájú útvonalak összekeverésével — a
        # normál (egy mappás) híváson a sorszámozás miatt ez nem fordulhat
        # elő, ezért itt a meglévő fájllal ütköztetünk.
        a = tmp_path / "a.jpg"
        existing = tmp_path / "nyaralas.jpg"
        a.write_bytes(b"kep")
        existing.write_bytes(b"mar-van")
        with pytest.raises(FileExistsError):
            rename_photos_many([RenameItem(path=a)], "nyaralas")
        assert a.exists()  # semmi sem történt

    def test_target_collides_with_another_batch_members_current_name(
        self, tmp_path
    ):
        # az 1. fájl célneve ("nyaralas.jpg") megegyezik egy MÁSIK, a
        # kötegben szereplő fájl JELENLEGI nevével (ami maga máshová
        # nevezendő át, "nyaralas-1.jpg"-re) — a sorrend-függő, félig
        # végrehajtott átnevezés elkerülése végett ezt is ütközésként
        # kezeljük, semmi sem nevezhető át
        a = tmp_path / "a.jpg"
        other = tmp_path / "nyaralas.jpg"
        a.write_bytes(b"kep")
        other.write_bytes(b"mar-van")
        items = [RenameItem(path=a), RenameItem(path=other)]
        with pytest.raises(FileExistsError):
            rename_photos_many(items, "nyaralas")
        assert a.exists()
        assert other.exists()

    def test_extension_preserved_per_file(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.mov"
        a.write_bytes(b"kep")
        b.write_bytes(b"video")
        items = [RenameItem(path=a), RenameItem(path=b)]
        results = rename_photos_many(items, "nyaralas")
        assert results == [
            tmp_path / "nyaralas.jpg",
            tmp_path / "nyaralas-1.mov",
        ]
