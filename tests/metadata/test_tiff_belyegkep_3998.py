"""Az EXIF-blokk IFD1-je az export bélyegképéből újraépül (#3998).

Spec 16. H) 1. és 5.: a forrás IFD1-e és bélyegképe SOSEM kerül át; új
bélyegképnél az IFD1 tagjai `0x103`=6, `0x11a`/`0x11b`=72/1, `0x128`=2,
`0x201`, `0x202`, a bélyegkép a blokk VÉGÉN áll, páratlan hossznál 1 nullbájt
követi. A forrást piexif-fel építjük (csak a teszt; a termék nem használja).
"""

from __future__ import annotations

import io
import struct

import piexif
import pytest
from PIL import Image

from picasapy.metadata import tiff_helyben as th


def _jpeg(szin, meret=(32, 24), extra=0):
    b = io.BytesIO()
    Image.new("RGB", meret, szin).save(b, "JPEG", quality=70)
    return b.getvalue() + b"\x00" * extra


def _forras(*, elonezet=None, gps=True, interop=True, tajolas=6):
    d = {
        "0th": {
            piexif.ImageIFD.Make: b"Kamera",
            piexif.ImageIFD.Orientation: tajolas,
            piexif.ImageIFD.DateTime: b"2020:01:02 03:04:05",
        },
        "Exif": {piexif.ExifIFD.ExifVersion: b"0230", piexif.ExifIFD.PixelXDimension: 100},
        "GPS": {piexif.GPSIFD.GPSLatitudeRef: b"N"} if gps else {},
        "Interop": {piexif.InteropIFD.InteroperabilityIndex: b"R98"} if interop else {},
        "1st": {},
    }
    if elonezet is not None:
        d["1st"] = {piexif.ImageIFD.Orientation: 6, piexif.ImageIFD.XResolution: (300, 1)}
        d["thumbnail"] = elonezet
    return piexif.dump(d)[6:]


def _ifd_sorok(tiff, off):
    e = "<" if tiff[:2] == b"II" else ">"
    n = struct.unpack_from(e + "H", tiff, off)[0]
    sorok = [struct.unpack_from(e + "HHI4s", tiff, off + 2 + 12 * i) for i in range(n)]
    return e, sorok, struct.unpack_from(e + "I", tiff, off + 2 + 12 * n)[0]


def _ifd1(tiff):
    e, _, kov = _ifd_sorok(tiff, struct.unpack_from(("<" if tiff[:2] == b"II" else ">") + "I", tiff, 4)[0])
    if not kov:
        return e, None
    return e, _ifd_sorok(tiff, kov)[1]


def _ki(tiff, jpeg, valtozasok=()):
    return th.frissitett_tiff(tiff, list(valtozasok), uj_ifd1=lambda: jpeg)


class TestUjBelyegkep:
    def test_negy_alapcimke_es_a_ketto_mutato(self):
        ki = _ki(_forras(), _jpeg("red"))
        e, sorok = _ifd1(ki)
        assert [s[0] for s in sorok] == [0x103, 0x11A, 0x11B, 0x128, 0x201, 0x202]
        tag = {s[0]: s for s in sorok}
        assert tag[0x103][1:3] == (th.SHORT, 1)
        assert struct.unpack(e + "H", tag[0x103][3][:2])[0] == 6
        assert struct.unpack(e + "H", tag[0x128][3][:2])[0] == 2
        assert tag[0x128][1:3] == (th.SHORT, 1)
        for t in (0x11A, 0x11B):
            assert tag[t][1:3] == (5, 1)
            off = struct.unpack(e + "I", tag[t][3])[0]
            assert struct.unpack(e + "II", ki[off : off + 8]) == (72, 1)
        assert tag[0x201][1:3] == (th.LONG, 1) and tag[0x202][1:3] == (th.LONG, 1)

    @pytest.mark.parametrize("paratlan", [0, 1])
    def test_a_belyegkep_a_blokk_vegen_paratlannal_nullaval(self, paratlan):
        jpeg = _jpeg("blue")
        jpeg += b"\x00" * ((paratlan - len(jpeg)) % 2)
        assert len(jpeg) % 2 == paratlan
        ki = _ki(_forras(), jpeg)
        e, sorok = _ifd1(ki)
        tag = {s[0]: s for s in sorok}
        kezdet = struct.unpack(e + "I", tag[0x201][3])[0]
        hossz = struct.unpack(e + "I", tag[0x202][3])[0]
        assert hossz == len(jpeg) and ki[kezdet : kezdet + hossz] == jpeg
        assert kezdet % 2 == 0
        assert ki[kezdet + hossz :] == (b"\x00" if len(jpeg) % 2 else b"")

    def test_nagy_vegu_blokk(self):
        tiff = piexif.dump({"0th": {piexif.ImageIFD.Make: b"K"}, "1st": {}})[6:]
        ki = _ki(tiff, _jpeg("green"))
        ki2 = th.frissitett_tiff(
            tiff.replace(b"II*\x00", b"II*\x00", 1), [], uj_ifd1=lambda: _jpeg("green")
        )
        assert _ifd1(ki)[1] is not None and _ifd1(ki2)[1] is not None
        # a piexif kis végű; a nagy végűt kézzel építjük
        mm = b"MM\x00*\x00\x00\x00\x08" + b"\x00\x01" + struct.pack(">HHI", 0x010F, 2, 2) + b"K\x00\x00\x00" + b"\x00\x00\x00\x00"
        ki = th.frissitett_tiff(mm, [], uj_ifd1=lambda: _jpeg("green"))
        e, sorok = _ifd1(ki)
        assert e == ">" and [s[0] for s in sorok][-2:] == [0x201, 0x202]

    def test_forras_ifd1_es_belyegkep_nem_kerul_at(self):
        regi = _jpeg("yellow", (64, 48))
        uj = _jpeg("red")
        ki = _ki(_forras(elonezet=regi), uj)
        assert regi not in ki
        e, sorok = _ifd1(ki)
        assert [s[0] for s in sorok] == [0x103, 0x11A, 0x11B, 0x128, 0x201, 0x202]
        tag = {s[0]: s for s in sorok}
        assert struct.unpack(e + "H", tag[0x103][3][:2])[0] == 6  # nem a forrásé (6 volt Orientation)
        assert 0x112 not in tag

    def test_a_tobbi_tag_valtozatlan(self):
        regi = _jpeg("yellow", (64, 48))
        ki = _ki(_forras(elonezet=regi), _jpeg("red"))
        eredeti = piexif.load(b"Exif\x00\x00" + _forras(elonezet=regi))
        uj = piexif.load(b"Exif\x00\x00" + ki)
        for ifd in ("0th", "Exif", "GPS", "Interop"):
            assert uj[ifd] == eredeti[ifd], ifd
        assert uj["thumbnail"] == _jpeg("red")

    def test_valtozassal_egyutt_a_belyegkep_marad_utolso(self):
        jpeg = _jpeg("red")
        ki = _ki(
            _forras(elonezet=_jpeg("yellow")),
            jpeg,
            [
                th.Valtozas("0th", 0x0131, th.ascii_ertek("PicasaPy"), csak_ha_hianyzik=True),
                th.Valtozas("Exif", 0xA003, th.Ertek(th.SHORT, 77)),
                th.Valtozas("Exif", 0xA002, th.Ertek(th.SHORT, 88)),
            ],
        )
        assert ki.rstrip(b"\x00").endswith(jpeg.rstrip(b"\x00"))
        uj = piexif.load(b"Exif\x00\x00" + ki)
        assert uj["thumbnail"] == jpeg
        assert uj["0th"][0x0131] == b"PicasaPy"
        assert uj["Exif"][0xA003] == 77

    def test_metaadat_nelkuli_forras(self):
        jpeg = _jpeg("red")
        ki = th.frissitett_tiff(None, [th.Valtozas("0th", 0x0131, th.ascii_ertek("X"))], uj_ifd1=lambda: jpeg)
        assert piexif.load(b"Exif\x00\x00" + ki)["thumbnail"] == jpeg

    def test_a_kozepen_allo_regi_belyegkep_nulla_es_a_tobbi_ertek_marad(self):
        """A régi előnézet NEM a blokk végén: a bájtjai kinullázva (nem szivárog
        át a kimenetbe), a mögötte álló másik érték érintetlen."""
        regi = _jpeg("yellow", (64, 48))
        veg = b"MAKERNOTE-ERTEK-1234567890"
        e = "<"
        ifd0_hossz = 2 + 12 * 2 + 4
        ifd1_hossz = 2 + 12 * 2 + 4
        ifd1_off = 8 + ifd0_hossz
        elo_off = ifd1_off + ifd1_hossz
        mn_off = elo_off + len(regi) + (len(regi) % 2)
        ifd0 = struct.pack(e + "H", 2)
        ifd0 += struct.pack(e + "HHI", 0x010F, 2, 2) + b"K\x00\x00\x00"
        ifd0 += struct.pack(e + "HHII", 0x927C, 7, len(veg), mn_off)
        ifd0 += struct.pack(e + "I", ifd1_off)
        ifd1 = struct.pack(e + "H", 2)
        ifd1 += struct.pack(e + "HHII", 0x201, 4, 1, elo_off) + struct.pack(e + "HHII", 0x202, 4, 1, len(regi))
        ifd1 += struct.pack(e + "I", 0)
        tiff = b"II*\x00" + struct.pack(e + "I", 8) + ifd0 + ifd1 + regi + b"\x00" * (len(regi) % 2) + veg
        ki = _ki(tiff, _jpeg("red"))
        assert regi not in ki
        assert ki[mn_off : mn_off + len(veg)] == veg
        assert piexif.load(b"Exif\x00\x00" + ki)["thumbnail"] == _jpeg("red")


class TestNincsBelyegkep:
    def test_nincs_ifd1_es_a_regi_belyegkep_sem_marad(self):
        regi = _jpeg("yellow", (64, 48))
        ki = th.frissitett_tiff(_forras(elonezet=regi), [], uj_ifd1=lambda: None)
        assert regi not in ki
        assert _ifd1(ki)[1] is None
        uj = piexif.load(b"Exif\x00\x00" + ki)
        assert uj["1st"] == {} and uj["thumbnail"] is None
        assert uj["0th"][0x010F] == b"Kamera"

    def test_forras_ifd1_nelkul_valtozatlan_blokk(self):
        tiff = _forras()
        assert th.frissitett_tiff(tiff, [], uj_ifd1=lambda: None) == tiff

    def test_a_forras_tobbi_bajtja_a_helyen(self):
        tiff = _forras(elonezet=_jpeg("yellow"))
        ki = th.frissitett_tiff(tiff, [], uj_ifd1=lambda: None)
        assert ki[8:20] == tiff[8:20]


def test_elonezet_es_uj_ifd1_egyutt_nem_adhato():
    with pytest.raises(th.TiffHiba):
        th.frissitett_tiff(_forras(), [], elonezet=lambda: b"x", uj_ifd1=lambda: b"y")


def test_a_regi_mod_valtozatlan():
    ki = th.frissitett_tiff(_forras(elonezet=_jpeg("yellow")), [], elonezet=lambda: _jpeg("red"))
    assert piexif.load(b"Exif\x00\x00" + ki)["thumbnail"] == _jpeg("red")


def test_serult_blokk_csak_tiffhibat_dobhat():
    """Véletlenszerűen rontott forrásnál a kimenet vagy önellenőrzött, vagy
    `TiffHiba` (a hívó ilyenkor a forrás bájtjait adja tovább) — más kivétel nem."""
    import random

    alap = _forras(elonezet=_jpeg("yellow", (64, 48)))
    uj = _jpeg("red")
    rng = random.Random(3998)
    for _ in range(400):
        rontott = bytearray(alap)
        for _ in range(rng.randint(1, 4)):
            rontott[rng.randrange(len(rontott))] = rng.randrange(256)
        for jpeg in (uj, None):
            try:
                th.frissitett_tiff(
                    bytes(rontott),
                    [th.Valtozas("0th", 0x0131, th.ascii_ertek("PicasaPy"), csak_ha_hianyzik=True)],
                    uj_ifd1=lambda jpeg=jpeg: jpeg,
                )
            except th.TiffHiba:
                pass
