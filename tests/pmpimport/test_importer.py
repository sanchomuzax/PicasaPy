"""iter_photo_records + parse_deferred_region: a db3-only adatok
kinyerése helyi útvonalakkal (#1)."""

import pytest

from picasapy.pmpimport import (
    PathRemapper,
    iter_photo_records,
    parse_deferred_region,
)
from support.pmp_factory import build_pmp_column, build_thumb_index


class TestParseDeferredRegion:
    def test_parses_named_regions(self):
        faces = parse_deferred_region(
            "rect64(1234567890abcdef),Kiss Anna;rect64(fedcba09),Nagy Béla;"
        )
        assert [face.name for face in faces] == ["Kiss Anna", "Nagy Béla"]
        assert 0 <= faces[0].rect.left <= 1

    def test_short_hex_padded(self):
        # élesben 15 karakteres érték is előfordul → zfill(16) kötelező
        (face,) = parse_deferred_region("rect64(123456789abcdef),Név;")
        assert face.rect.left < 0.1

    def test_empty_and_none(self):
        assert parse_deferred_region("") == ()
        assert parse_deferred_region(None) == ()

    def test_invalid_entry_raises(self):
        with pytest.raises(ValueError):
            parse_deferred_region("nem-rect,Név;")


def _write_db3(tmp_path, *, index_name="thumbindex.db"):
    """Kis szintetikus db3: 1 könyvtár + 3 fájl (1 remap nélküli) + 1 arc-
    és 1 törölt bejegyzés."""
    (tmp_path / index_name).write_bytes(
        build_thumb_index(
            [
                ("C:\\Users\\anna\\Pictures", None),  # 0: könyvtár
                ("IMG_0001.jpg", 0),                  # 1: fájl
                ("IMG_0002.jpg", 0),                  # 2: fájl
                ("", 1),                              # 3: arc-rekord
                ("", None),                           # 4: törölt fájl
                ("D:\\mashol\\kulso.jpg", None),      # 5: könyvtárként) másik gyökér
            ]
        )
    )
    count = 6
    (tmp_path / "imagedata_caption.pmp").write_bytes(
        build_pmp_column(0x6, ["", "Tópart", "", "", "", ""])
    )
    (tmp_path / "imagedata_rotate.pmp").write_bytes(
        build_pmp_column(0x1, [0, 1, 0, 0, 0, 0])
    )
    (tmp_path / "imagedata_star.pmp").write_bytes(
        build_pmp_column(0x3, [0, 1, 0, 0, 0, 0])
    )
    (tmp_path / "imagedata_filters.pmp").write_bytes(
        build_pmp_column(0x6, ["", "enhance=1;", "", "", "", ""])
    )
    # sparse: csak az első 2 sorig ér
    (tmp_path / "imagedata_crop64.pmp").write_bytes(
        build_pmp_column(0x4, [0, 0x1999333366668000])
    )
    (tmp_path / "imagedata_deferredregion.pmp").write_bytes(
        build_pmp_column(
            0x6, ["", "rect64(1234567890abcdef),Kiss Anna;", "", "", "", ""]
        )
    )
    return count


@pytest.fixture
def remapper():
    return PathRemapper.from_dict({"C:\\Users\\anna\\Pictures": "/mnt/nas/fotok"})


class TestIterPhotoRecords:
    def test_yields_only_mapped_files(self, tmp_path, remapper):
        _write_db3(tmp_path)
        records = iter_photo_records(tmp_path, remapper)
        assert [record.local_path for record in records] == [
            "/mnt/nas/fotok/IMG_0001.jpg",
            "/mnt/nas/fotok/IMG_0002.jpg",
        ]

    def test_record_fields_join_imagedata_by_row(self, tmp_path, remapper):
        _write_db3(tmp_path)
        first, second = iter_photo_records(tmp_path, remapper)
        assert first.row == 1
        assert first.caption == "Tópart"
        assert first.rotate == 1
        assert first.star is True
        assert first.filters == "enhance=1;"
        assert first.crop64 == 0x1999333366668000
        assert first.faces[0].name == "Kiss Anna"
        assert second.caption is None
        assert second.star is False
        assert second.crop64 is None  # sparse oszlop vége

    def test_repeatable_same_result(self, tmp_path, remapper):
        # 7. rögzített döntés: az import bármikor újrafuttatható —
        # ugyanarra a bemenetre determinisztikusan ugyanazt adja
        _write_db3(tmp_path)
        assert iter_photo_records(tmp_path, remapper) == iter_photo_records(
            tmp_path, remapper
        )

    def test_case_insensitive_index_filename(self, tmp_path, remapper):
        # MEMORY.md: élesben kisbetűs fájlnevek is előfordulnak
        _write_db3(tmp_path, index_name="Thumbs_Index.db")
        assert len(iter_photo_records(tmp_path, remapper)) == 2

    def test_missing_index_raises(self, tmp_path, remapper):
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x6, ["a"])
        )
        with pytest.raises(FileNotFoundError):
            iter_photo_records(tmp_path, remapper)

    def test_broken_deferredregion_does_not_break_import(self, tmp_path, remapper):
        _write_db3(tmp_path)
        (tmp_path / "imagedata_deferredregion.pmp").write_bytes(
            build_pmp_column(0x6, ["", "hibás-bejegyzés,Név;", "", "", "", ""])
        )
        first, _second = iter_photo_records(tmp_path, remapper)
        assert first.faces == ()
        assert first.caption == "Tópart"  # a többi adat megmarad
