"""A Canon objektívnév a MakerNote-ból a tulajdonságok panelig (#3121).

## A mérés

`docs/specs/picasa-metaadat-tulajdonsagok.md` 9.9 és 9.12: a Canon-ág
(`FUN_00a35a60`) a `MakerNote 0x0001` (CameraSettings) tömbből dolgozik:

* **méret-kapu**: legalább 28 elem (`(elemszám·2 & ~1) > 0x36`);
* `A = e24/e25`, `B = e23/e25` — de `B` csak ha `e23 ≠ e24` (a fix
  objektív `B`-je `0.0`), és semmi, ha `e25 = 0`;
* `D = 2^(e26/64)`, `C = 2^(e27/64)` — de `C` csak ha `e27 ≠ e26`;
* a tábla-keresés `(A, B, D, C)` ↔ `(gyujto_min, gyujto_max, rekesz_min,
  rekesz_max)`, 8 ULP tűréssel, és csak `1 ≤ LensType ≤ 0xfffe` esetén;
* ha nincs név: **tartalék-leírás** (`0x00a36650`): `%d-%dmm` / `%dmm`
  (csonkolva), szóköz, `f/%.2g-%.2g` / `f/%.2g`.

A panel „Lens" sora az eredetiben a Picasa-belső **255-ös** kulcs
(`0x00634a0d`: `"Lens"` → `0xff`), tehát épp ez a feloldott név.
"""

from __future__ import annotations

import struct

import pytest
from PIL import Image

from picasapy.metadata.makernote import canon_camera_settings, tiff_blokk
from picasapy.metadata.objektiv import canon_leiras
from picasapy.metadata.reader import read_exif_details


def _beallitasok(**elemek: int) -> tuple[int, ...]:
    """48 elemes CameraSettings-tömb; a nevesített elemek `e22=…` alakban."""
    tomb = [0] * 48
    for nev, ertek in elemek.items():
        tomb[int(nev[1:])] = ertek
    return tuple(tomb)


# -- a Canon-ág számítása és keresése ---------------------------------------


class TestATablaTalalat:
    def test_fix_objektiv_pontos_ertekekkel(self) -> None:
        """35 mm f/2: e23 = e24 ⇒ B = 0.0, és 2^(64/64) = 2.0 pontosan."""
        tomb = _beallitasok(e22=11, e23=35, e24=35, e25=1, e26=64)
        assert canon_leiras(tomb) == "Canon EF 35mm f/2"

    def test_zoom_allando_rekesszel(self) -> None:
        tomb = _beallitasok(e22=9, e23=210, e24=70, e25=1, e26=128)
        assert canon_leiras(tomb) == "Canon EF 70-210mm f/4"

    def test_a_gyujto_egyseg_oszto(self) -> None:
        """e25 az osztó: 350/10 = 35.0."""
        tomb = _beallitasok(e22=11, e23=350, e24=350, e25=10, e26=64)
        assert canon_leiras(tomb) == "Canon EF 35mm f/2"

    def test_e27_egyezese_e26_tal_nullat_ad(self) -> None:
        """`cmp eax, esi / je` — az azonos rekesz-pár C-je 0.0."""
        tomb = _beallitasok(e22=11, e23=35, e24=35, e25=1, e26=64, e27=64)
        assert canon_leiras(tomb) == "Canon EF 35mm f/2"


class TestATartalekLeiras:
    def test_nem_egzakt_rekesz_nem_talalat_hanem_leiras(self) -> None:
        """2^(116/64) = 3,51…, 2^(139/64) = 4,51… — a 8 ULP-n kívül esik,
        tehát a 4-es LensType két sora közül egyik sem, jön a leírás."""
        tomb = _beallitasok(e22=4, e23=105, e24=35, e25=1, e26=116, e27=139)
        assert canon_leiras(tomb) == "35-105mm f/3.5-4.5"

    def test_fix_gyujto_egy_rekesz(self) -> None:
        tomb = _beallitasok(e22=9999, e23=50, e24=50, e25=1, e26=54)
        assert canon_leiras(tomb) == "50mm f/1.8"

    def test_a_gyujto_CSONKOLVA(self) -> None:
        """`cvttsd2si` — 17,9 → 17, nem kerekítve 18."""
        tomb = _beallitasok(e22=9999, e23=179, e24=179, e25=10)
        assert canon_leiras(tomb) == "17mm"

    def test_egyseg_nelkul_csak_a_rekesz(self) -> None:
        tomb = _beallitasok(e22=9999, e23=50, e24=50, e25=0, e26=128)
        assert canon_leiras(tomb) == "f/4"

    @pytest.mark.parametrize("lens_type", [0, 0xFFFF])
    def test_ervenytelen_lens_type_mellett_nincs_kereses(self, lens_type) -> None:
        """`lea ecx,[edi-1] / cmp ecx,0xfffd / ja` — a 11-es sor egzakt
        négyese sem ad nevet, ha az azonosító érvénytelen."""
        tomb = _beallitasok(e22=lens_type, e23=35, e24=35, e25=1, e26=64)
        assert canon_leiras(tomb) == "35mm f/2"

    def test_minden_nulla_nincs_leiras(self) -> None:
        assert canon_leiras(_beallitasok()) is None


class TestAMeretKapu:
    def test_28_elem_eleg(self) -> None:
        tomb = _beallitasok(e22=11, e23=35, e24=35, e25=1, e26=64)[:28]
        assert canon_leiras(tomb) == "Canon EF 35mm f/2"

    def test_27_elem_keves(self) -> None:
        tomb = _beallitasok(e22=11, e23=35, e24=35, e25=1, e26=64)[:27]
        assert canon_leiras(tomb) is None


# -- a MakerNote kiolvasása -------------------------------------------------


def _tiff_canon(beallitasok, *, make="Canon", bajtrend="<", lens_model=None) -> bytes:
    """Minimális TIFF: IFD0 (Make, ExifIFD) → Exif IFD (MakerNote
    [+ LensModel]) → Canon MakerNote IFD (0x0001 SHORT-tömb)."""
    e = bajtrend
    fej = (b"II*\x00" if e == "<" else b"MM\x00*") + struct.pack(e + "I", 8)
    make_b = make.encode() + b"\x00"
    lens_b = (lens_model.encode() + b"\x00") if lens_model else b""
    # elrendezés: fej(8) | IFD0 (2+2·12+4=30) | Exif IFD | MakerNote | adatok
    ifd0_off = 8
    exif_n = 2 if lens_model else 1
    exif_off = ifd0_off + 30
    mn_off = exif_off + 2 + exif_n * 12 + 4
    mn_len = 2 + 12 + 4
    tomb_off = mn_off + mn_len
    tomb_b = struct.pack(e + f"{len(beallitasok)}H", *beallitasok)
    make_off = tomb_off + len(tomb_b)
    lens_off = make_off + len(make_b)

    def bejegyzes(tag, tipus, db, ertek):
        return struct.pack(e + "HHI", tag, tipus, db) + ertek

    def ofs(x):
        return struct.pack(e + "I", x)

    ifd0 = struct.pack(e + "H", 2) + bejegyzes(
        0x010F, 2, len(make_b), ofs(make_off)) + bejegyzes(
        0x8769, 4, 1, ofs(exif_off)) + ofs(0)
    mn_teljes = mn_len + len(tomb_b)
    exif = struct.pack(e + "H", exif_n) + bejegyzes(
        0x927C, 7, mn_teljes, ofs(mn_off))
    if lens_model:
        exif += bejegyzes(0xA434, 2, len(lens_b), ofs(lens_off))
    exif += ofs(0)
    mn = struct.pack(e + "H", 1) + bejegyzes(
        0x0001, 3, len(beallitasok), ofs(tomb_off)) + ofs(0)
    return fej + ifd0 + exif + mn + tomb_b + make_b + lens_b


def _jpeg(path, tiff: bytes):
    Image.new("RGB", (8, 6), "red").save(path, "JPEG", exif=b"Exif\x00\x00" + tiff)
    return path


@pytest.fixture
def canon_35mm() -> tuple[int, ...]:
    return _beallitasok(e22=11, e23=35, e24=35, e25=1, e26=64)


class TestAKiolvasas:
    def test_little_endian(self, canon_35mm) -> None:
        assert canon_camera_settings(_tiff_canon(canon_35mm)) == canon_35mm

    def test_big_endian(self, canon_35mm) -> None:
        tiff = _tiff_canon(canon_35mm, bajtrend=">")
        assert canon_camera_settings(tiff) == canon_35mm

    def test_jpegbol(self, tmp_path, canon_35mm) -> None:
        kep = _jpeg(tmp_path / "canon.jpg", _tiff_canon(canon_35mm))
        assert canon_camera_settings(tiff_blokk(kep)) == canon_35mm

    def test_nyers_tiff_alapu_fajlbol(self, tmp_path, canon_35mm) -> None:
        """A CR2 maga TIFF — a fájl eleje a blokk."""
        nyers = tmp_path / "kep.cr2"
        nyers.write_bytes(_tiff_canon(canon_35mm))
        assert canon_camera_settings(tiff_blokk(nyers)) == canon_35mm

    @pytest.mark.parametrize("vagas", [9, 40, 60, 80])
    def test_csonka_blokkra_None_es_nem_dob(self, canon_35mm, vagas) -> None:
        assert canon_camera_settings(_tiff_canon(canon_35mm)[:vagas]) is None

    def test_szemet_None(self) -> None:
        assert canon_camera_settings(b"\x00" * 64) is None
        assert tiff_blokk("/nincs/ilyen/fajl.jpg") is None


class TestAPanelSora:
    def test_a_canon_nev_a_lens_mezobe_kerul(self, tmp_path, canon_35mm) -> None:
        kep = _jpeg(tmp_path / "canon.jpg", _tiff_canon(canon_35mm))
        assert read_exif_details(kep).lens == "Canon EF 35mm f/2"

    def test_a_makernote_nev_elozi_a_lensmodelt(self, tmp_path, canon_35mm) -> None:
        """Az eredeti a 255-ös kulcsot mutatja; a LensModel (0xA434) nincs a
        3.7 tulajdonságtáblájában (6.1), tehát nem versenyez vele."""
        tiff = _tiff_canon(canon_35mm, lens_model="EF35mm f/2")
        kep = _jpeg(tmp_path / "canon.jpg", tiff)
        assert read_exif_details(kep).lens == "Canon EF 35mm f/2"

    def test_mas_gyartonal_a_makernote_nem_szamit(self, tmp_path, canon_35mm) -> None:
        tiff = _tiff_canon(canon_35mm, make="FUJIFILM", lens_model="XF35mmF2")
        kep = _jpeg(tmp_path / "fuji.jpg", tiff)
        assert read_exif_details(kep).lens == "XF35mmF2"

    def test_a_tartalek_leiras_NEM_irja_felul_a_lensmodelt(self, tmp_path) -> None:
        """A „50mm f/1.8" általánosabb, mint a gép saját neve — a ma is
        látszó pontos név marad (kimondott eltérés, spec 9.12)."""
        tomb = _beallitasok(e22=9999, e23=50, e24=50, e25=1, e26=54)
        tiff = _tiff_canon(tomb, lens_model="EF50mm f/1.8 STM")
        kep = _jpeg(tmp_path / "canon.jpg", tiff)
        assert read_exif_details(kep).lens == "EF50mm f/1.8 STM"

    def test_lensmodel_nelkul_a_tartalek_leiras_latszik(self, tmp_path) -> None:
        tomb = _beallitasok(e22=9999, e23=50, e24=50, e25=1, e26=54)
        kep = _jpeg(tmp_path / "canon.jpg", _tiff_canon(tomb))
        assert read_exif_details(kep).lens == "50mm f/1.8"

    @pytest.mark.parametrize("rekesz", [8192, 0xFFFF])
    def test_tulcsordulo_rekesz_nem_dob(self, tmp_path, rekesz) -> None:
        """`2^(e/64)` ≥ 2^128 nem fér a float32-be — sérült fájl ne
        döntse le a panelt (és a mentés szűrését)."""
        tomb = _beallitasok(e22=11, e23=35, e24=35, e25=1, e26=rekesz, e27=rekesz - 1)
        kep = _jpeg(tmp_path / "canon.jpg", _tiff_canon(tomb))
        assert read_exif_details(kep).lens == "35mm"


class TestTulcsordulas:
    def test_a_vegtelen_rekesz_kimarad_a_leirasbol(self) -> None:
        tomb = _beallitasok(e22=9999, e23=50, e24=50, e25=1, e26=0xFFFF)
        assert canon_leiras(tomb) == "50mm"
