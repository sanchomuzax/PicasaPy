"""A bélyegkép-gyorstár TARTALMÁNAK olvasója (#1446).

Az indexet (`20 + 12n`) a `thumbindex.read_slot_index` olvassa (#1444/#2195);
ez a fájl a párját őrzi: a slotból a BÁJTOKAT.

## Amit őriz

1. **A „használt-e a slot" próba a HOSSZ, nem a kulcs.** Mérve (#1444): az
   `albums_index.db` 9 slotjának (109–117) érvényes tartománya van nulla
   kulccsal. Kulcsra szűrve ezek a blobok elérhetetlenek lennének.
2. **`i < n` ellenőrzés.** A spec kimondja, hogy a `previews`/`bigthumbs`
   vektor hosszabb lehet a katalógusnál, a `thumbs_index` pedig rövidebb is —
   a slot-index tehát sosem feltételezhető érvényesnek.
3. **A tartományon kívüli slot DOB**, nem ad rövidebb blobot: a néma féladat
   rosszabb, mint a hangos hiba.
4. **Valódi fájlon**: a tulajdonos katalógusán a JPEG-aláírás, az arcsablonok
   állandó hossza, és a spec két mért egyezése (nincs átfedés; a legnagyobb
   vég = az adatfájl mérete).

⚠️ A 4. csoport a gitignore-olt `research/testdata` meglétén múlik, tehát a
CI-n KIMARAD. Ezért az 1–3. csoport szintetikus fájlokkal dolgozik: azok
mindenhol futnak.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from picasapy.pmpimport.cacheblob import (
    CACHE_NEVEK,
    FACETEMPLATE_HOSSZ,
    open_cache_store,
)
from picasapy.pmpimport.thumbindex import ThumbIndexFormatError

#: A tulajdonos valódi katalógusa — gitignore-olt. A próba KIHAGYJA magát, ha
#: nincs ott; útvonalat sosem ír a kimenetbe (magánadat).
_VALODI = Path(
    "/home/sancho/Documents/PicasaPy/research/testdata/Picasa2-arcok/Picasa2/db3"
)


def _index_fajl(ut: Path, kulcsok, eltolasok, meretek) -> None:
    """Szintetikus `*_index.db` a mért `20 + 12n` elrendezéssel."""
    darabok = [struct.pack("<f", 1.6), struct.pack("<I", 0)]
    for tomb in (kulcsok, eltolasok, meretek):
        darabok.append(struct.pack("<I", len(tomb)))
        darabok.append(struct.pack(f"<{len(tomb)}I", *tomb))
    ut.write_bytes(b"".join(darabok))


@pytest.fixture
def tar(tmp_path: Path):
    """Három slot: nulla kulcsú DE használt · üres · sima."""
    adat = b"AAA" + b"BBBB"
    (tmp_path / "thumbs_0.db").write_bytes(adat)
    _index_fajl(
        tmp_path / "thumbs_index.db",
        kulcsok=(0, 0x1234, 0x5678),
        eltolasok=(0, 0, 3),
        meretek=(3, 0, 4),
    )
    return open_cache_store(tmp_path, "thumbs")


class TestAHasznaltsagAHosszbolJon:
    def test_a_nulla_kulcsu_slot_IS_hasznalt(self, tar) -> None:
        assert tar.hasznalt() == (0, 2), (
            "#1446: a nulla kulcsú, de érvényes tartományú slot kimaradt — "
            "az `albums_index.db` 9 slotja pontosan ilyen (#1444)"
        )

    def test_a_nulla_kulcsu_slot_blobja_megjon(self, tar) -> None:
        assert tar.blob(0) == b"AAA"

    def test_az_ures_slot_None(self, tar) -> None:
        assert tar.blob(1) is None

    def test_a_masodik_blob_a_helyes_tartomanybol_jon(self, tar) -> None:
        assert tar.blob(2) == b"BBBB"


class TestATartomanyEllenorzes:
    def test_a_vektoron_KIVULI_slot_None(self, tar) -> None:
        assert tar.slot(3) is None
        assert tar.blob(3) is None, (
            "a spec szerint a vektor hosszabb ÉS rövidebb is lehet a "
            "katalógusnál — az `i < n` ellenőrzés nem hagyható el"
        )
        assert tar.blob(-1) is None

    def test_az_adatfajlon_TULMUTATO_slot_DOB(self, tmp_path: Path) -> None:
        (tmp_path / "thumbs_0.db").write_bytes(b"rovid")
        _index_fajl(
            tmp_path / "thumbs_index.db",
            kulcsok=(1,),
            eltolasok=(0,),
            meretek=(999,),
        )
        tar = open_cache_store(tmp_path, "thumbs")
        with pytest.raises(ThumbIndexFormatError, match="kívülre mutat"):
            tar.blob(0)


class TestAMegnyitas:
    def test_hianyzo_par_None(self, tmp_path: Path) -> None:
        assert open_cache_store(tmp_path, "previews") is None, (
            "a telepítésenként változó gyorstár-készlet nem hiba"
        )

    def test_csak_az_index_van_meg_akkor_is_None(self, tmp_path: Path) -> None:
        _index_fajl(tmp_path / "previews_index.db", (1,), (0,), (1,))
        assert open_cache_store(tmp_path, "previews") is None

    def test_ismeretlen_tar_nevre_ValueError(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Ismeretlen gyorstár"):
            open_cache_store(tmp_path, "nincs-ilyen")

    def test_a_romlott_index_HIBAT_ad_nem_None_t(self, tmp_path: Path) -> None:
        (tmp_path / "thumbs_0.db").write_bytes(b"x")
        (tmp_path / "thumbs_index.db").write_bytes(b"\x00\x00\x00\x00" * 3)
        with pytest.raises(ThumbIndexFormatError):
            open_cache_store(tmp_path, "thumbs")


@pytest.mark.skipif(not _VALODI.is_dir(), reason="a valódi katalógus nincs itt")
class TestAValodiKatalogus:
    """A négy bélyegkép-szint és az arcsablonok — a jegy célja."""

    def test_mind_az_ot_tar_megnyilik(self) -> None:
        nyitva = {
            nev: open_cache_store(_VALODI, nev)
            for nev in CACHE_NEVEK
            if open_cache_store(_VALODI, nev) is not None
        }
        assert set(nyitva) == set(CACHE_NEVEK), (
            f"nem nyílt meg mind: {sorted(set(CACHE_NEVEK) - set(nyitva))}"
        )

    @pytest.mark.parametrize("nev", ["thumbs", "thumbs2", "previews", "bigthumbs"])
    def test_a_belyegkep_JPEG(self, nev: str) -> None:
        tar = open_cache_store(_VALODI, nev)
        elso = tar.hasznalt()[0]
        blob = tar.blob(elso)
        assert blob[:2] == b"\xff\xd8", (
            f"a {nev} első használt slotja nem JPEG-aláírással kezdődik: "
            f"{blob[:4].hex()}"
        )
        assert blob[-2:] == b"\xff\xd9", "és nem JPEG-záróval végződik"

    def test_az_arcsablon_hossza_allando(self) -> None:
        tar = open_cache_store(_VALODI, "facetemplatesV2")
        hosszak = {tar.slot(i).size for i in tar.hasznalt()}
        assert hosszak == {FACETEMPLATE_HOSSZ}, (
            f"a mért állandó 1 044 bájt helyett: {sorted(hosszak)[:5]}"
        )

    @pytest.mark.parametrize("nev", CACHE_NEVEK)
    def test_a_tartomanyok_nem_fednek_at(self, nev: str) -> None:
        """A spec mérése (#1444): 11/11 fájlon egyetlen átfedés sincs."""
        tar = open_cache_store(_VALODI, nev)
        tartomanyok = sorted(
            (tar.slot(i).offset, tar.slot(i).offset + tar.slot(i).size)
            for i in tar.hasznalt()
        )
        for (kezd, veg), (kovetkezo, _) in zip(tartomanyok, tartomanyok[1:], strict=False):
            assert veg <= kovetkezo, f"{nev}: átfedő tartomány {kezd}..{veg}"

    @pytest.mark.parametrize("nev", CACHE_NEVEK)
    def test_a_legnagyobb_veg_az_adatfajl_merete(self, nev: str) -> None:
        """A spec másik mérése: a legnagyobb vég BÁJTRA a `_0.db` mérete."""
        tar = open_cache_store(_VALODI, nev)
        legnagyobb = max(
            tar.slot(i).offset + tar.slot(i).size for i in tar.hasznalt()
        )
        assert legnagyobb == tar.data_path.stat().st_size

    def test_minden_hasznalt_slot_blobja_kiolvashato(self) -> None:
        """Nem csak az első: a teljes tár végigolvasva (a legkisebb táron)."""
        tar = open_cache_store(_VALODI, "thumbs2")
        hasznalt = tar.hasznalt()
        assert len(hasznalt) > 100, "túl kevés használt slot a próbához"
        for i in hasznalt:
            assert len(tar.blob(i)) == tar.slot(i).size
