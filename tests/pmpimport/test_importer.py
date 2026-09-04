"""iter_photo_records + parse_deferred_region: a db3-only adatok
kinyerése helyi útvonalakkal (#1)."""

import struct

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
        # (a fájl neve maga "thumbindex.db" — a "thumbs_index.db" NEM
        # ugyanaz a fájl, ld. #1489)
        _write_db3(tmp_path, index_name="ThumbIndex.DB")
        assert len(iter_photo_records(tmp_path, remapper)) == 2

    def test_missing_index_raises(self, tmp_path, remapper):
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x6, ["a"])
        )
        with pytest.raises(FileNotFoundError):
            iter_photo_records(tmp_path, remapper)

    def test_only_thumbs_cache_present_gives_helpful_message(
        self, tmp_path, remapper
    ):
        # #1489: a `thumbs_index.db` a bélyegkép-gyorstár indexe (magic
        # 0x3FCCCCCD), NEM a névindex alternatív neve. Ha csak ez van
        # jelen, a hiba nevezze meg a hiányzó fájlt, és ne "érvénytelen
        # magic"-ként bukjon (azt a felhasználó nem tudja értelmezni).
        (tmp_path / "thumbs_index.db").write_bytes(
            struct.pack("<III", 0x3FCCCCCD, 0, 0)
        )
        with pytest.raises(FileNotFoundError) as exc_info:
            iter_photo_records(tmp_path, remapper)
        message = str(exc_info.value)
        assert "thumbindex.db" in message
        assert "magic" not in message.lower()

    def test_thumbindex_found_even_when_cache_sorts_first(
        self, tmp_path, remapper
    ):
        # A sima sorted() véletlenül "thumbindex.db" < "thumbs_index.db"
        # sorrendet ad — ez a teszt ezt a szerencsét zárja ki: a
        # gyorstár-fájl nagybetűs kezdéssel ASCII szerint MEGELŐZI a
        # kisbetűs névindexet a bejárási sorrendben, mégis a névindexnek
        # kell visszajönnie.
        _write_db3(tmp_path)
        (tmp_path / "Thumbs_Index.DB").write_bytes(
            struct.pack("<III", 0x3FCCCCCD, 0, 0)
        )
        records = iter_photo_records(tmp_path, remapper)
        assert len(records) == 2

    def test_broken_deferredregion_does_not_break_import(self, tmp_path, remapper):
        _write_db3(tmp_path)
        (tmp_path / "imagedata_deferredregion.pmp").write_bytes(
            build_pmp_column(0x6, ["", "hibás-bejegyzés,Név;", "", "", "", ""])
        )
        first, _second = iter_photo_records(tmp_path, remapper)
        assert first.faces == ()
        assert first.caption == "Tópart"  # a többi adat megmarad


class TestStarlist2335:
    """#2335: a csillagozás a `db3/starlist.txt`-ben él, NEM `.pmp`-ben.

    A tulajdonos 2026-08-22-i valódi adatmappájában **65** `.pmp` oszlop
    van, és **nincs köztük `imagedata_star.pmp`** — a `starlist.txt`
    viszont **50** csillagozott képet sorol fel. Az importunk ebből nullát
    hozott át: a hiányzó oszlopra a tábla `None`-t ad, a `bool(None)` pedig
    `False`.

    ⚠️ **Ezért nem fogta meg a régi próbasor:** a `_db3` segéd MAGA hozza
    létre az `imagedata_star.pmp`-t, tehát olyan adatbázist ír le,
    amilyen a valóságban nincs. Ez az osztály a VALÓDI alakot próbálja:
    `starlist.txt`, `star.pmp` nélkül.
    """

    def _valodi_alak(self, tmp_path) -> int:
        """A `_write_db3` készlete, de a `star.pmp` TÖRÖLVE, helyette lista."""
        count = _write_db3(tmp_path)
        (tmp_path / "imagedata_star.pmp").unlink()
        # CRLF sorvégek és windowsos abszolút út — ahogy a valódi fájlban
        (tmp_path / "starlist.txt").write_bytes(
            b"C:\\Users\\anna\\Pictures\\IMG_0002.jpg\r\n"
        )
        return count

    def test_a_starlist_adja_a_csillagot(self, tmp_path, remapper):
        self._valodi_alak(tmp_path)
        elso, masodik = iter_photo_records(tmp_path, remapper)
        assert elso.local_path.endswith("IMG_0001.jpg")
        assert masodik.local_path.endswith("IMG_0002.jpg")
        assert masodik.star is True, "a starlist.txt-ben szereplő kép nem csillagos"
        assert elso.star is False, "a listában NEM szereplő kép csillagot kapott"

    def test_starlist_nelkul_sem_dol_be(self, tmp_path, remapper):
        """Hiányzó lista és hiányzó oszlop: minden csillagozatlan, hiba
        nélkül — a részleges import elve."""
        _write_db3(tmp_path)
        (tmp_path / "imagedata_star.pmp").unlink()
        assert all(r.star is False for r in iter_photo_records(tmp_path, remapper))

    def test_a_regi_star_oszlop_TOVABBRA_IS_szamit(self, tmp_path, remapper):
        """VAGY kapcsolat, nem helyettesítés — a régebbi adatbázisok sem
        sérülhetnek."""
        _write_db3(tmp_path)  # a star.pmp-ben az IMG_0001 csillagos
        elso, masodik = iter_photo_records(tmp_path, remapper)
        assert elso.star is True
        assert masodik.star is False

    def test_a_ketto_EGYUTT_is_mukodik(self, tmp_path, remapper):
        """Ha mindkettő van, a két forrás uniója számít."""
        _write_db3(tmp_path)
        (tmp_path / "starlist.txt").write_bytes(
            b"C:\\Users\\anna\\Pictures\\IMG_0002.jpg\r\n"
        )
        elso, masodik = iter_photo_records(tmp_path, remapper)
        assert elso.star is True, "a .pmp-ből jövő csillag elveszett"
        assert masodik.star is True, "a listából jövő csillag elveszett"
