"""Ismételhető db3-import path-remappel — issue #1 DoD."""

import os

import pytest

from picasapy.pmpimport import (
    ImageRecord,
    PathRemapper,
    PmpImport,
    load_db3,
    merge_imports,
    parse_deferredregion,
)
from support.pmp_factory import build_pmp, build_thumbindex


@pytest.fixture()
def db3_dir(tmp_path):
    """Szintetikus db3-készlet: 1 mappa, 2 kép, 1 törölt, 1 arc-rekord."""
    entries = [
        ("C:\\Users\\anna\\Képek\\", None),
        ("nyaralás.jpg", 0),
        ("tél.jpg", 0),
        ("", None),
        ("", 1),
    ]
    (tmp_path / "thumbindex.db").write_bytes(build_thumbindex(entries))
    (tmp_path / "imagedata_caption.pmp").write_bytes(
        build_pmp(0x0, ["", "Nyaralás", "Tél"])
    )
    (tmp_path / "imagedata_rotate.pmp").write_bytes(build_pmp(0x1, [0, 1, 3]))
    (tmp_path / "imagedata_deferredregion.pmp").write_bytes(
        build_pmp(0x0, ["", "rect64(3f845bcb59418507),Kovács Anna;"])
    )
    return tmp_path


REMAP = {"C:\\Users\\anna\\Képek": "/mnt/kepek"}


class TestLoadDb3:
    def test_only_file_entries_become_images(self, db3_dir):
        result = load_db3(db3_dir, PathRemapper(REMAP))
        assert [img.path for img in result.images] == [
            "/mnt/kepek/nyaralás.jpg",
            "/mnt/kepek/tél.jpg",
        ]

    def test_image_data_comes_from_sparse_row(self, db3_dir):
        result = load_db3(db3_dir, PathRemapper(REMAP))
        first, second = result.images
        assert first.data["caption"] == "Nyaralás"
        assert first.data["rotate"] == 1
        assert second.data == {"caption": "Tél", "rotate": 3}

    def test_faces_parsed_from_deferredregion(self, db3_dir):
        result = load_db3(db3_dir, PathRemapper(REMAP))
        first, second = result.images
        assert [face.name for face in first.faces] == ["Kovács Anna"]
        assert second.faces == ()

    def test_folder_order_follows_thumbindex_order(self, db3_dir):
        # Csak a db-ben élő adat: a képek mappán belüli sorrendje.
        result = load_db3(db3_dir, PathRemapper(REMAP))
        assert result.folder_orders == {
            "/mnt/kepek": ("/mnt/kepek/nyaralás.jpg", "/mnt/kepek/tél.jpg")
        }

    def test_unmapped_paths_are_reported(self, db3_dir):
        result = load_db3(db3_dir, PathRemapper({"D:\\Más": "/mnt/mas"}))
        assert result.images == ()
        assert "C:\\Users\\anna\\Képek\\nyaralás.jpg" in result.unmapped

    def test_import_is_repeatable(self, db3_dir):
        # 7. rögzített döntés: az import bármikor újrafuttatható.
        remapper = PathRemapper(REMAP)
        assert load_db3(db3_dir, remapper) == load_db3(db3_dir, remapper)

    def test_source_mtime_is_newest_input_file(self, db3_dir):
        os.utime(db3_dir / "imagedata_rotate.pmp", (2_000_000_000, 2_000_000_000))
        result = load_db3(db3_dir, PathRemapper(REMAP))
        assert result.source_mtime == 2_000_000_000


class TestMerge:
    def _import(self, mtime, caption):
        image = ImageRecord(
            path="/mnt/kepek/a.jpg",
            source_path="C:\\Képek\\a.jpg",
            entry_index=1,
            data={"caption": caption},
            faces=(),
        )
        return PmpImport(
            images=(image,),
            folder_orders={"/mnt/kepek": ("/mnt/kepek/a.jpg",)},
            unmapped=(),
            source_mtime=mtime,
        )

    def test_newer_import_wins_on_conflict(self):
        old = self._import(100.0, "régi")
        new = self._import(200.0, "új")
        merged = merge_imports(old, new)
        assert merged.images[0].data["caption"] == "új"
        assert merged.source_mtime == 200.0

    def test_order_of_arguments_does_not_matter(self):
        old = self._import(100.0, "régi")
        new = self._import(200.0, "új")
        assert merge_imports(new, old) == merge_imports(old, new)

    def test_previous_none_returns_new(self):
        new = self._import(200.0, "új")
        assert merge_imports(None, new) == new

    def test_union_of_distinct_images(self):
        old = self._import(100.0, "régi")
        other_image = ImageRecord(
            path="/mnt/kepek/b.jpg",
            source_path="C:\\Képek\\b.jpg",
            entry_index=2,
            data={},
            faces=(),
        )
        new = PmpImport(
            images=(other_image,),
            folder_orders={"/mnt/masik": ("/mnt/masik/b.jpg",)},
            unmapped=(),
            source_mtime=200.0,
        )
        merged = merge_imports(old, new)
        assert {img.path for img in merged.images} == {
            "/mnt/kepek/a.jpg",
            "/mnt/kepek/b.jpg",
        }
        assert set(merged.folder_orders) == {"/mnt/kepek", "/mnt/masik"}


class TestDeferredRegion:
    def test_parses_named_regions(self):
        faces = parse_deferredregion(
            "rect64(3f845bcb59418507),Kovács Anna;rect64(1234),Nagy Béla;"
        )
        assert [face.name for face in faces] == ["Kovács Anna", "Nagy Béla"]
        assert faces[0].rect.left == pytest.approx(0.248108, abs=1e-6)

    def test_short_hex_is_padded(self):
        # 15 karakteres érték élesben megfigyelve → zfill(16) kötelező.
        (face,) = parse_deferredregion("rect64(f845bcb59418507),X;")
        assert face.rect.left == pytest.approx(0x0F84 / 65536, abs=1e-6)

    def test_empty_value_yields_no_faces(self):
        assert parse_deferredregion("") == ()

    def test_malformed_chunk_raises(self):
        with pytest.raises(ValueError):
            parse_deferredregion("nemrect,Valaki;")
