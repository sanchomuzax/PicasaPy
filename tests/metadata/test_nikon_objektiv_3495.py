"""A Nikon objektívnév: a helyes tábla és a bekötött Nikon-ág (#3495).

## A mérés

`docs/specs/picasa-metaadat-tulajdonsagok.md` 9.13:

* **A)** a tábla rekordja `{8 bájtos kulcs, név-mutató}`, a `0x00c7b228`-tól,
  **417** sor — a korábbi (9.2) olvasat a kulcs ELŐTTI mutatót vette névnek,
  ezért minden név a szomszéd sor kulcsához került; a kereső az **első**
  találatnál áll meg (5 kulcs ismétlődik);
* **B)** a kulcs a `LensData` (`0x0098`) verziója szerinti eltolásról vett
  7 bájt + a `LensType` (`0x0083`): `0100` → 6; `0101` → 0x0b;
  `0201`–`0203` → 0x0b + visszafejtés; `0204` → 0x0c + visszafejtés; más →
  üres; a hossz legyen nagyobb, mint `eltolás + 7`; a `LensType` 1…0xFFFE,
  különben tartalék;
* **C)** a visszafejtés (a 4. bájttól) az exiftool Nikon-`Decrypt`
  szerkezete — ⚠️ valódi mintán nem mérve, ezért itt exiftool-lal
  (12.76) ellenőrzött SZINTETIKUS esetek őrzik;
* **D)** a tartalék: `"%d-%dmm f/%.2g-%.2g"` a `p[2…5]`-ből,
  `g(b) = 2^(b/24)`, a gyújtó `5·g`, csonkolva.
"""

from __future__ import annotations

import json
import struct

import pytest
from PIL import Image

from picasapy.metadata.makernote import nikon_objektiv_mezok, tiff_blokk
from picasapy.metadata.objektiv import (
    TABLA_UT,
    nikon_leiras,
    nikon_objektiv,
    nikon_talalat,
    nikon_visszafejt,
)
from picasapy.metadata.reader import read_exif_details

#: A D100-as kontrollminta (`/mnt/photo/2003/2003-01-more/DSC_0001.JPG`)
#: `LensData`-jának a spec 9.13 B-ben rögzített eleje: verzió, két bájt, és
#: a 7 bájtos `p`. A minta itt nincs meg; a hossz-feltétel (> 6 + 7) miatt
#: egy záró bájttal kiegészítve.
D100_LENS_DATA = bytes.fromhex("30313030 1156 563C5C8E303C1C 00".replace(" ", ""))
D100_LENS_TYPE = 2
SIGMA = "Sigma 70-300mm F4-5.6 APO Macro Super II"

#: Szintetikus titkosított `LensData`-k — a nyílt kulcs mindháromban
#: `7A 3C 1F 37 30 30 7E` + `LensType 6`, zárszámláló 12345. Mindhármat az
#: exiftool 12.76 (`-LensID#`) `7A 3C 1F 37 30 30 7E 06`-ra fejtette vissza
#: (a sorozatszám a 0x001d mezőben: `1234567`, ill. a nem számjegyes
#: `No= 30A`, amelynél a kulcs D50-en 0x22, máshol 0x60).
TITKOS_0201_D200 = bytes.fromhex("3032303198cb116ad655e7f67810daeed2872360")
TITKOS_0204_D50 = bytes.fromhex("3032303418a72592ee39739cce87aea15a1da180")
TITKOS_0204_D90 = bytes.fromhex("3032303458556fa6fa6bf9a4166d4c459e370310")
ZARSZAMLALO = 12345
DX_12_24 = "AF-S DX Zoom-Nikkor 12-24mm f/4G IF-ED"


@pytest.fixture(scope="module")
def nikon_tabla() -> list[dict]:
    return json.loads(TABLA_UT.read_text(encoding="utf-8"))["nikon"]


# -- A) a tábla ---------------------------------------------------------------


class TestATabla:
    def test_417_sor(self, nikon_tabla) -> None:
        assert len(nikon_tabla) == 417

    @pytest.mark.parametrize(("sor", "kulcs", "nev"), [
        (0, "0000000000000001", "Manual Lens No CPU"),
        (275, "563C5C8E303C1C02", SIGMA),
        (416, "FE535C8024248406",
         "Tamron SP AF 70-200mm f/2.8 Di LD (IF) Macro (A001)"),
    ])
    def test_a_binarisbol_kiolvasott_sorok(self, nikon_tabla, sor, kulcs, nev) -> None:
        """A spec 9.13 A: a 0. sor, a D100-as kontroll (`0x00c7bf0c`) és az
        utolsó sor, ahogy a `0x00c7b228 + 12·i` rácson állnak."""
        assert nikon_tabla[sor] == {"lens_id": kulcs, "nev": nev}

    def test_a_tabla_az_elso_bajt_szerint_RENDEZETT(self, nikon_tabla) -> None:
        """A kereső kilép, ha a táblabeli első bájt nagyobb (`0x00a362b1`)."""
        elsok = [int(r["lens_id"][:2], 16) for r in nikon_tabla]
        assert elsok == sorted(elsok)

    def test_pontosan_ot_kulcs_ismetlodik(self, nikon_tabla) -> None:
        kulcsok = [r["lens_id"] for r in nikon_tabla]
        assert len(kulcsok) - len(set(kulcsok)) == 5


class TestAzElsoNyer:
    def test_a_kesz_ha_pelda(self) -> None:
        assert nikon_objektiv("32546A6A24243502") == "AF Micro-Nikkor 105mm f/2.8D"

    @pytest.mark.parametrize(("kulcs", "nev"), [
        ("25483C5C24241B02", "Tokina AT-X 270 AF PRO II (AF 28-70mm f/2.6-2.8)"),
        ("2F4030442C342902", "Tokina AF 235 II (AF 20-35mm f/3.5-4.5)"),
        ("2F48304424242902", "AF Zoom-Nikkor 20-35mm f/2.8D IF"),
        ("7A3C1F3730307E06", DX_12_24),
    ])
    def test_a_tobbi_ismetlodo_kulcs(self, kulcs, nev) -> None:
        assert nikon_objektiv(kulcs) == nev


# -- B) a kulcs összerakása és D) a tartalék ----------------------------------


class TestAKulcs:
    def test_a_d100_kontroll(self) -> None:
        assert nikon_talalat(D100_LENS_DATA, D100_LENS_TYPE) == (SIGMA, True)

    def test_0101_eltolasa_0x0b_visszafejtes_nelkul(self) -> None:
        adat = bytearray(20)
        adat[:4] = b"0101"
        adat[0x0B:0x12] = bytes.fromhex("563C5C8E303C1C")
        assert nikon_leiras(bytes(adat), 2) == SIGMA

    @pytest.mark.parametrize("verzio", [b"0300", b"0400", b"0205", b"abcd"])
    def test_ismeretlen_verzio_URES(self, verzio) -> None:
        adat = verzio + D100_LENS_DATA[4:] + bytes(10)
        assert nikon_talalat(adat, D100_LENS_TYPE) is None

    def test_a_hossz_NAGYOBB_kell_legyen_mint_eltolas_plusz_7(self) -> None:
        """`0100`: 6 + 7 = 13 bájt még kevés, 14 már elég."""
        assert nikon_talalat(D100_LENS_DATA[:13], D100_LENS_TYPE) is None
        assert nikon_talalat(D100_LENS_DATA[:14], D100_LENS_TYPE) == (SIGMA, True)

    def test_hianyzo_lensdata_None(self) -> None:
        assert nikon_talalat(None, D100_LENS_TYPE) is None


class TestATartalek:
    def test_a_d100_p_bol_tabla_nelkul(self) -> None:
        """Érvénytelen `LensType` (0) ⇒ a táblát kihagyja (`0x00a3627a`)."""
        assert nikon_talalat(D100_LENS_DATA, 0) == ("71-302mm f/4-5.7", False)

    def test_hianyzo_lens_type_is_tartalek(self) -> None:
        assert nikon_leiras(D100_LENS_DATA, None) == "71-302mm f/4-5.7"

    def test_nincs_talalat_a_tablaban(self) -> None:
        """Ugyanez a `p` más `LensType`-pal nincs a táblában."""
        assert nikon_talalat(D100_LENS_DATA, 0x7F) == ("71-302mm f/4-5.7", False)

    def test_azonos_rekesznel_is_ket_szam(self) -> None:
        """A „≈ 0" próba kiszámolt értékre sosem igaz: `f/2.8-2.8`."""
        adat = b"0100" + bytes(2) + bytes([0x00, 0x00, 0x50, 0x50, 0x24, 0x24, 0x00, 0])
        assert nikon_leiras(adat, 0) == "50-50mm f/2.8-2.8"


# -- C) a visszafejtés --------------------------------------------------------


class TestAVisszafejtes:
    def test_0201_szamjegyes_sorozatszammal(self) -> None:
        assert nikon_talalat(
            TITKOS_0201_D200, 6, sorozatszam="1234567",
            zarszamlalo=ZARSZAMLALO, modell="NIKON D200",
        ) == (DX_12_24, True)

    def test_0204_d50_kulcs_0x22(self) -> None:
        assert nikon_leiras(
            TITKOS_0204_D50, 6, sorozatszam="No= 30A",
            zarszamlalo=ZARSZAMLALO, modell="NIKON D50") == DX_12_24

    def test_0204_mas_gepen_kulcs_0x60(self) -> None:
        assert nikon_leiras(
            TITKOS_0204_D90, 6, sorozatszam="No= 30A",
            zarszamlalo=ZARSZAMLALO, modell="NIKON D90") == DX_12_24

    def test_sorozatszam_nelkul_is_a_modell_dont(self) -> None:
        """Ha a sorozatszám hiányzik: `"D50"` → 0x22, egyébként 0x60."""
        assert nikon_leiras(
            TITKOS_0204_D90, 6, zarszamlalo=ZARSZAMLALO,
            modell="NIKON D90") == DX_12_24

    def test_a_4_bajtos_verzio_nyilt_marad(self) -> None:
        nyilt = nikon_visszafejt(TITKOS_0201_D200, 1234567, ZARSZAMLALO)
        assert nyilt[:4] == b"0201"
        assert nyilt[0x0B:0x12] == bytes.fromhex("7A3C1F3730307E")

    def test_zarszamlalo_nelkul_nincs_tippeles(self) -> None:
        """⚠️ Nem mért: a kulcs fele hiányzik — a szemét név helyett semmi."""
        assert nikon_talalat(TITKOS_0201_D200, 6, sorozatszam="1234567") is None


# -- a MakerNote kiolvasása és a panel sora -----------------------------------


def _ifd(bejegyzesek, kezdet: int, e: str) -> bytes:
    """IFD a `kezdet` eltoláson, utána az adatokkal; az eltolások a TIFF-
    fejléchez viszonyulnak (a hívó ennek a kezdetét adja meg)."""
    n = len(bejegyzesek)
    adat_hely = kezdet + 2 + 12 * n + 4
    ki, adat = struct.pack(e + "H", n), b""
    for tag, tipus, db, ertek in sorted(bejegyzesek):
        if len(ertek) <= 4:
            ki += struct.pack(e + "HHI", tag, tipus, db) + ertek.ljust(4, b"\0")
        else:
            ki += struct.pack(e + "HHII", tag, tipus, db, adat_hely + len(adat))
            adat += ertek + b"\0" * (len(ertek) % 2)
    return ki + b"\0\0\0\0" + adat


def _nikon_makernote(*, lens_data=None, lens_type=None, sorozatszam=None,
                     zarszamlalo=None, e: str = "<") -> bytes:
    """Nikon 3-as MakerNote: `Nikon\\0` fejléc + saját TIFF-fejléc."""
    bejegyzesek = []
    if sorozatszam is not None:
        s = sorozatszam.encode() + b"\0"
        bejegyzesek.append((0x001D, 2, len(s), s))
    if lens_type is not None:
        bejegyzesek.append((0x0083, 1, 1, bytes([lens_type])))
    if lens_data is not None:
        bejegyzesek.append((0x0098, 7, len(lens_data), lens_data))
    if zarszamlalo is not None:
        bejegyzesek.append((0x00A7, 4, 1, struct.pack(e + "I", zarszamlalo)))
    fej = (b"II*\x00" if e == "<" else b"MM\x00*") + struct.pack(e + "I", 8)
    return b"Nikon\x00\x02\x10\x00\x00" + fej + _ifd(bejegyzesek, 8, e)


def _tiff(makernote: bytes, *, make="NIKON CORPORATION", modell="NIKON D100",
          lens_model=None) -> bytes:
    e = "<"
    m, mo = make.encode() + b"\0", modell.encode() + b"\0"
    ifd0 = [(0x010F, 2, len(m), m), (0x0110, 2, len(mo), mo),
            (0x8769, 4, 1, b"\0\0\0\0")]
    exif_hely = 8 + len(_ifd(ifd0, 8, e))
    ifd0[2] = (0x8769, 4, 1, struct.pack(e + "I", exif_hely))
    exif = [(0x927C, 7, len(makernote), makernote)]
    if lens_model:
        lm = lens_model.encode() + b"\0"
        exif.append((0xA434, 2, len(lm), lm))
    return (b"II*\x00" + struct.pack(e + "I", 8) + _ifd(ifd0, 8, e)
            + _ifd(exif, exif_hely, e))


def _jpeg(path, tiff: bytes):
    Image.new("RGB", (8, 6), "red").save(path, "JPEG", exif=b"Exif\x00\x00" + tiff)
    return path


class TestAKiolvasas:
    @pytest.mark.parametrize("e", ["<", ">"])
    def test_a_negy_mezo(self, e) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=2,
                              sorozatszam="1234567", zarszamlalo=ZARSZAMLALO, e=e)
        mezok = nikon_objektiv_mezok(_tiff(mn))
        assert mezok.lens_data == D100_LENS_DATA
        assert mezok.lens_type == 2
        assert mezok.sorozatszam == "1234567"
        assert mezok.zarszamlalo == ZARSZAMLALO

    def test_jpegbol(self, tmp_path) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=2)
        kep = _jpeg(tmp_path / "d100.jpg", _tiff(mn))
        assert nikon_objektiv_mezok(tiff_blokk(kep)).lens_data == D100_LENS_DATA

    def test_nem_nikon_fejlec_None(self) -> None:
        assert nikon_objektiv_mezok(_tiff(b"Olympus\0" + bytes(40))) is None

    @pytest.mark.parametrize("vagas", [9, 40, 80, 120])
    def test_csonka_blokk_nem_dob(self, vagas) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=2)
        mezok = nikon_objektiv_mezok(_tiff(mn)[:vagas])
        assert mezok is None or mezok.lens_data is None

    def test_szemet_None(self) -> None:
        assert nikon_objektiv_mezok(b"\x00" * 64) is None
        assert nikon_objektiv_mezok(None) is None


class TestAPanelSora:
    def test_a_d100_minta_panelje(self, tmp_path) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=D100_LENS_TYPE)
        kep = _jpeg(tmp_path / "DSC_0001.JPG", _tiff(mn))
        assert read_exif_details(kep).lens == SIGMA

    def test_titkositott_0201_a_panelen(self, tmp_path) -> None:
        mn = _nikon_makernote(lens_data=TITKOS_0201_D200, lens_type=6,
                              sorozatszam="1234567", zarszamlalo=ZARSZAMLALO)
        kep = _jpeg(tmp_path / "d200.jpg", _tiff(mn, modell="NIKON D200"))
        assert read_exif_details(kep).lens == DX_12_24

    def test_a_tablanev_elozi_a_lensmodelt(self, tmp_path) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=D100_LENS_TYPE)
        kep = _jpeg(tmp_path / "d.jpg", _tiff(mn, lens_model="70.0-300.0 mm"))
        assert read_exif_details(kep).lens == SIGMA

    def test_a_tartalek_NEM_irja_felul_a_lensmodelt(self, tmp_path) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=0)
        kep = _jpeg(tmp_path / "d.jpg", _tiff(mn, lens_model="70.0-300.0 mm"))
        assert read_exif_details(kep).lens == "70.0-300.0 mm"

    def test_lensmodel_nelkul_a_tartalek_latszik(self, tmp_path) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=0)
        kep = _jpeg(tmp_path / "d.jpg", _tiff(mn))
        assert read_exif_details(kep).lens == "71-302mm f/4-5.7"

    def test_mas_gyartonal_a_nikon_makernote_nem_szamit(self, tmp_path) -> None:
        mn = _nikon_makernote(lens_data=D100_LENS_DATA, lens_type=D100_LENS_TYPE)
        kep = _jpeg(tmp_path / "d.jpg", _tiff(mn, make="FUJIFILM", lens_model="XF"))
        assert read_exif_details(kep).lens == "XF"
