"""Az export minden JPEG-jébe Interop IFD kerül (#3989).

Spec: `picasa-metaadat-tulajdonsagok.md` 16. G): `InteropVersion` = `0100`
(csak ha hiányzik), `0x1001`/`0x1002` = a FORRÁS pixelmérete (nem a kimenetié),
az `InteropIndex` (`0x0001`) NEM kerül be, és a meglévő Interop-mező marad.

A forrást kézzel építjük (piexif nélkül), az olvasó a termékkódtól független.
A mért eset (forrás 1600×1200, kimenet 1650×1250) szintetikus képen."""

from __future__ import annotations

import io
import struct
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from picasapy.metadata import export_metadata as em
from picasapy.metadata import tiff_helyben as th

_EXIF_ID = b"Exif\x00\x00"
_MERET = {1: 1, 2: 1, 3: 2, 4: 4, 7: 1}
_MOST = datetime(2026, 9, 29, 12, 0, 0)


def _ifd(bejegyzesek, kezdet, kovetkezo=0, e="<"):
    n = len(bejegyzesek)
    adat_kezdet = kezdet + 2 + 12 * n + 4
    fej, adat = struct.pack(e + "H", n), b""
    for tag, tipus, darab, ertek in sorted(bejegyzesek):
        if len(ertek) <= 4:
            mezo = ertek.ljust(4, b"\x00")
        else:
            if (adat_kezdet + len(adat)) % 2:
                adat += b"\x00"
            mezo = struct.pack(e + "I", adat_kezdet + len(adat))
            adat += ertek
        fej += struct.pack(e + "HHI", tag, tipus, darab) + mezo
    blokk = fej + struct.pack(e + "I", kovetkezo) + adat
    return blokk + (b"\x00" if len(blokk) % 2 else b"")


def _tiff(*, exif=True, interop=None, tajolas=None, e="<"):
    """IFD0 [→ ExifIFD [→ InteropIFD]]; `interop`: az Interop-bejegyzések
    (None = nincs mutató); `exif=False`: csak IFD0."""
    u32 = lambda v: struct.pack(e + "I", v)  # noqa: E731
    fejlec = (b"II" if e == "<" else b"MM") + struct.pack(e + "HI", 42, 8)

    def epit(exif_off, interop_off):
        ifd0_b = [(0x010F, 2, 6, b"Test\x00")]
        if tajolas is not None:
            ifd0_b.append((0x0112, 3, 1, struct.pack(e + "H", tajolas)))
        if exif:
            ifd0_b.append((0x8769, 4, 1, u32(exif_off)))
        exif_b = [(0x9000, 7, 4, b"0230")]
        if interop is not None:
            exif_b.append((0xA005, 4, 1, u32(interop_off)))
        return (
            _ifd(ifd0_b, 8, 0, e),
            _ifd(exif_b, exif_off, 0, e) if exif else b"",
            _ifd(interop, interop_off, 0, e) if interop is not None else b"",
        )

    ifd0, _, _ = epit(0, 0)
    exif_off = 8 + len(ifd0)
    _, exif_blokk, _ = epit(exif_off, 0)
    interop_off = exif_off + len(exif_blokk)
    ifd0, exif_blokk, interop_blokk = epit(exif_off, interop_off)
    return fejlec + ifd0 + exif_blokk + interop_blokk


def _olvas(tiff):
    """{ifd: {tag: (típus, darab, érték-bájtok)}}."""
    e = "<" if tiff[:2] == b"II" else ">"

    def ifd(off):
        (n,) = struct.unpack_from(e + "H", tiff, off)
        out = {}
        for i in range(n):
            tag, tipus, darab = struct.unpack_from(e + "HHI", tiff, off + 2 + 12 * i)
            meret = _MERET.get(tipus, 1) * darab
            mezo = off + 2 + 12 * i + 8
            hely = mezo if meret <= 4 else struct.unpack_from(e + "I", tiff, mezo)[0]
            out.setdefault(tag, []).append((tipus, darab, tiff[hely : hely + meret]))
        return out

    def mutato(d, tag):
        return struct.unpack(e + "I", d[tag][0][2])[0]

    ifd0 = ifd(struct.unpack_from(e + "I", tiff, 4)[0])
    out = {"0th": ifd0, "Exif": {}, "Interop": {}}
    if 0x8769 in ifd0:
        out["Exif"] = ifd(mutato(ifd0, 0x8769))
        if 0xA005 in out["Exif"]:
            out["Interop"] = ifd(mutato(out["Exif"], 0xA005))
    return out


def _u32(e, v):
    return struct.pack(e + "I", v)


def _jpeg(size):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, "JPEG")
    return buf.getvalue()


def _app1(azonosito, torzs):
    return b"\xff\xe1" + (len(azonosito) + len(torzs) + 2).to_bytes(2, "big") + (
        azonosito + torzs
    )


def _forras(tmp_path, tiff, size=(1600, 1200)):
    raw = _jpeg(size)
    path = tmp_path / "forras.jpg"
    szeg = _app1(_EXIF_ID, tiff) if tiff is not None else b""
    path.write_bytes(raw[:2] + szeg + raw[2:])
    return path


def _kimenet_exif(source, kimenet_meret):
    """A `frissitett_metaadat` kimenetének EXIF-blokkja, olvasva."""
    ki = em.frissitett_metaadat(
        source, _jpeg(kimenet_meret), size=kimenet_meret, now=_MOST
    )
    for marker, seg in em._szegmensek(ki):
        if marker == 0xE1 and seg[4:].startswith(_EXIF_ID):
            return _olvas(seg[4 + len(_EXIF_ID) :])
    raise AssertionError("nincs EXIF a kimenetben")


_INTEROP = [
    th.Valtozas("Interop", 0x0002, th.Ertek(th.UNDEFINED, b"0100"), csak_ha_hianyzik=True),
    th.Valtozas("Interop", 0x1001, th.Ertek(th.LONG, 1600), csak_ha_hianyzik=True),
]
_EXIF_VALTOZAS = th.Valtozas("Exif", 0xA002, th.Ertek(th.SHORT, 5))


def _ifd_helyek(tiff):
    """Az IFD0 és az Exif IFD (kezdet) offsetje: (0th, Exif)."""
    e = "<" if tiff[:2] == b"II" else ">"
    ifd0 = struct.unpack_from(e + "I", tiff, 4)[0]
    n = struct.unpack_from(e + "H", tiff, ifd0)[0]
    exif = 0
    for i in range(n):
        tag = struct.unpack_from(e + "H", tiff, ifd0 + 2 + 12 * i)[0]
        if tag == 0x8769:
            exif = struct.unpack_from(e + "I", tiff, ifd0 + 2 + 12 * i + 8)[0]
    return ifd0, exif


def _bejegyzes_helye(tiff, tag):
    """A `tag` (IFD0 vagy Exif) első bejegyzésének eltolása."""
    e = "<" if tiff[:2] == b"II" else ">"
    for kezdet in _ifd_helyek(tiff):
        n = struct.unpack_from(e + "H", tiff, kezdet)[0]
        for i in range(n):
            hely = kezdet + 2 + 12 * i
            if struct.unpack_from(e + "H", tiff, hely)[0] == tag:
                return hely
    raise AssertionError(hex(tag))


def _bejegyzes_tag_darab(tiff, tag):
    e = "<" if tiff[:2] == b"II" else ">"
    kezdet = _ifd_helyek(tiff)[1]
    n = struct.unpack_from(e + "H", tiff, kezdet)[0]
    return sum(
        struct.unpack_from(e + "H", tiff, kezdet + 2 + 12 * i)[0] == tag for i in range(n)
    )


class TestMertEset:
    """Forrás 1600×1200, kimenet 1650×1250 (a 3229-es mappa)."""

    def test_interop_a_forras_meretevel_a_kimenet_pixelmerete_a_kimeneti(self, tmp_path):
        ki = _kimenet_exif(_forras(tmp_path, None), (1650, 1250))
        interop = ki["Interop"]
        assert interop[0x0002] == [(7, 4, b"0100")]
        # metaadat nélküli forrás: az üres blokk nagy végű
        assert interop[0x1001] == [(4, 1, struct.pack(">I", 1600))]
        assert interop[0x1002] == [(4, 1, struct.pack(">I", 1200))]
        assert 0x0001 not in interop  # InteropIndex nincs
        assert ki["Exif"][0xA002][0][2] == struct.pack(">H", 1650)
        assert ki["Exif"][0xA003][0][2] == struct.pack(">H", 1250)

    def test_exif_nelkuli_forras_is_kap_interopot(self, tmp_path):
        ki = _kimenet_exif(_forras(tmp_path, None), (800, 600))
        assert set(ki["Interop"]) == {0x0002, 0x1001, 0x1002}

    def test_atmeretezes_kicsinyitesnel_is_a_forras_merete(self, tmp_path):
        ki = _kimenet_exif(_forras(tmp_path, _tiff()), (400, 300))
        assert ki["Interop"][0x1001][0][2] == struct.pack("<I", 1600)
        assert ki["Interop"][0x1002][0][2] == struct.pack("<I", 1200)

    def test_exif_forras_interop_nelkul_uj_ifd(self, tmp_path):
        forras = _tiff()
        ki = _kimenet_exif(_forras(tmp_path, forras), (1650, 1250))
        assert ki["Interop"][0x0002] == [(7, 4, b"0100")]
        assert ki["Exif"][0x9000] == [(7, 4, b"0230")]  # a forrásé marad


class TestMeglevoMarad:
    def test_meglevo_interop_mezo_marad_csak_a_hianyzo_potlodik(self, tmp_path):
        forras = _tiff(interop=[(0x0002, 7, 4, b"0110"), (0x1001, 4, 1, _u32("<", 77))])
        ki = _kimenet_exif(_forras(tmp_path, forras), (1650, 1250))
        assert ki["Interop"][0x0002] == [(7, 4, b"0110")]
        assert ki["Interop"][0x1001] == [(4, 1, struct.pack("<I", 77))]
        assert ki["Interop"][0x1002] == [(4, 1, struct.pack("<I", 1200))]

    def test_meglevo_interop_index_marad_de_ujat_nem_irunk(self, tmp_path):
        forras = _tiff(interop=[(0x0001, 2, 4, b"R98\x00")])
        ki = _kimenet_exif(_forras(tmp_path, forras), (1650, 1250))
        assert ki["Interop"][0x0001] == [(2, 4, b"R98\x00")]
        assert ki["Interop"][0x0002] == [(7, 4, b"0100")]

    def test_teljes_interop_valtozatlan(self, tmp_path):
        forras = _tiff(
            interop=[
                (0x0002, 7, 4, b"0100"),
                (0x1001, 4, 1, _u32("<", 1600)),
                (0x1002, 4, 1, _u32("<", 1200)),
            ]
        )
        ki = _kimenet_exif(_forras(tmp_path, forras), (1650, 1250))
        assert {t: v for t, v in ki["Interop"].items()} == {
            0x0002: [(7, 4, b"0100")],
            0x1001: [(4, 1, struct.pack("<I", 1600))],
            0x1002: [(4, 1, struct.pack("<I", 1200))],
        }

    def test_nagy_vegu_forras(self, tmp_path):
        forras = _tiff(e=">", interop=[(0x0001, 2, 4, b"R98\x00")])
        ki = _kimenet_exif(_forras(tmp_path, forras), (1650, 1250))
        assert ki["Interop"][0x1001][0][2] == struct.pack(">I", 1600)
        assert ki["Interop"][0x0001] == [(2, 4, b"R98\x00")]


class TestSzerkezetVedelem:
    def test_ervenytelen_interop_mutato_erintetlen_es_nem_kerul_masodik_mutato(self):
        forras = bytearray(_tiff(interop=[(0x0001, 2, 4, b"R98\x00")]))
        hely = _bejegyzes_helye(forras, 0xA005)
        struct.pack_into("<I", forras, hely + 8, 0x7FFFFF)  # a blokkon kívülre
        ki = th.frissitett_tiff(bytes(forras), [*_INTEROP, _EXIF_VALTOZAS])
        assert ki[: len(forras)].count(struct.pack("<H", 0xA005)) == 1
        assert _bejegyzes_tag_darab(ki, 0xA005) == 1
        assert struct.unpack_from("<I", ki, _bejegyzes_helye(ki, 0xA005) + 8)[0] == 0x7FFFFF

    def test_ket_interop_mutato_nem_nyul_az_interophoz(self):
        forras = bytearray(_tiff(interop=[(0x0001, 2, 4, b"R98\x00")]))
        # a mutató IFD-jét kétszer szereplő 0xa005-tel építjük újra
        e = "<"
        exif_off = struct.unpack_from(e + "I", forras, _bejegyzes_helye(forras, 0x8769) + 8)[0]
        interop_off = struct.unpack_from(e + "I", forras, _bejegyzes_helye(forras, 0xA005) + 8)[0]
        uj_exif = _ifd(
            [(0x9000, 7, 4, b"0230"), (0xA005, 4, 1, _u32(e, interop_off)),
             (0xA005, 4, 1, _u32(e, interop_off))],
            len(forras), 0, e,
        )
        struct.pack_into(e + "I", forras, _bejegyzes_helye(forras, 0x8769) + 8, len(forras))
        forras += uj_exif
        assert exif_off < len(forras)
        ki = th.frissitett_tiff(bytes(forras), [*_INTEROP, _EXIF_VALTOZAS])
        assert _bejegyzes_tag_darab(ki, 0xA005) == 2
        assert b"R98\x00" in ki
        assert 0x1001 not in _olvas(ki)["Interop"]

    def test_ket_interop_mutato_es_az_interop_tablara_mutato_datetime_nem_bukik(self):
        """A kétszer szereplő `0xa005` mellett az Interop-tábla akkor is védett
        (a `_cel_szabad` látja), ha egy másik tag értéke oda mutat: a `DateTime`
        áthelyeződik, a kimenet sikeres (nem `TiffHiba`), az Interop-tábla sértetlen."""
        e = "<"
        forras = bytearray(_tiff(interop=[(0x0001, 2, 4, b"R98\x00")]))
        exif_hely = _bejegyzes_helye(forras, 0x8769)
        interop_off = struct.unpack_from(
            e + "I", forras, _bejegyzes_helye(forras, 0xA005) + 8
        )[0]
        forras += b"\x00" * 32  # szabad hely az Interop-tábla után: a DateTime-érték oda is nyúlhat
        uj_exif_off = len(forras)
        uj_exif = _ifd(
            [(0x9000, 7, 4, b"0230"), (0xA005, 4, 1, _u32(e, interop_off)),
             (0xA005, 4, 1, _u32(e, interop_off))],
            uj_exif_off, 0, e,
        )
        uj_ifd0_off = uj_exif_off + len(uj_exif)
        uj_ifd0 = _ifd(
            [(0x010F, 2, 6, b"Test\x00"), (0x0132, 2, 20, b"2020:01:01 00:00:00\x00"),
             (0x8769, 4, 1, _u32(e, uj_exif_off))],
            uj_ifd0_off, 0, e,
        )
        assert exif_hely
        forras += uj_exif + uj_ifd0
        struct.pack_into(e + "I", forras, 4, uj_ifd0_off)
        # a DateTime értékmutatója az Interop-táblára
        dt_hely = _bejegyzes_helye(forras, 0x0132)
        struct.pack_into(e + "I", forras, dt_hely + 8, interop_off)
        ki = th.frissitett_tiff(
            bytes(forras),
            [th.Valtozas("0th", 0x0132, th.ascii_ertek("2026:09:29 12:00:00")), *_INTEROP],
        )
        olv = _olvas(ki)
        assert olv["0th"][0x0132] == [(2, 20, b"2026:09:29 12:00:00\x00")]
        assert olv["Interop"][0x0001] == [(2, 4, b"R98\x00")]
        assert _bejegyzes_tag_darab(ki, 0xA005) == 2
        assert 0x1001 not in olv["Interop"]

    def test_tiff_szinten_interop_valtozas_es_onellenorzes(self):
        forras = _tiff(interop=[(0x0001, 2, 4, b"R98\x00")])
        ki = th.frissitett_tiff(
            forras,
            [
                th.Valtozas(
                    "Interop", 0x0002, th.Ertek(th.UNDEFINED, b"0100"), csak_ha_hianyzik=True
                ),
                th.Valtozas("Interop", 0x1001, th.Ertek(th.LONG, 1600), csak_ha_hianyzik=True),
            ],
        )
        olv = _olvas(ki)
        assert olv["Interop"][0x0001] == [(2, 4, b"R98\x00")]
        assert olv["Interop"][0x0002] == [(7, 4, b"0100")]
        assert olv["Interop"][0x1001][0][2] == struct.pack("<I", 1600)
        assert olv["Exif"][0x9000] == [(7, 4, b"0230")]
        assert ki.startswith(forras[:4])

    def test_kozbenso_interop_mutato_masik_ifd_tagjait_nem_bantja(self):
        forras = _tiff(interop=[(0x0001, 2, 4, b"R98\x00")])
        ki = th.frissitett_tiff(
            forras,
            [
                th.Valtozas("0th", 0x0132, th.ascii_ertek("2026:09:29 12:00:00")),
                th.Valtozas("Exif", 0xA002, th.Ertek(th.SHORT, 5)),
                th.Valtozas("Interop", 0x1001, th.Ertek(th.LONG, 9), csak_ha_hianyzik=True),
            ],
        )
        olv = _olvas(ki)
        assert olv["Exif"][0xA002][0][2] == struct.pack("<H", 5)
        assert olv["Interop"][0x1001][0][2] == struct.pack("<I", 9)
        assert olv["Interop"][0x0001] == [(2, 4, b"R98\x00")]


class TestForrasMeret:
    def test_tajolt_forras_a_tarolt_meretet_kapja(self, tmp_path):
        """A tájolt (5-8) forrásnál a SOF TÁROLT mérete kerül az Interopba:
        a felcserélésre nincs sem mérés, sem bináris olvasat (spec 16. E: a forrás
        `0x4d`/`0x4e`-je). A tájolt eset NINCS mérve, nyitott kérdés: #3996."""
        forras = _forras(tmp_path, _tiff(tajolas=6))
        ki = _kimenet_exif(forras, (1250, 1650))
        assert ki["Interop"][0x1001][0][2] == struct.pack("<I", 1600)
        assert ki["Interop"][0x1002][0][2] == struct.pack("<I", 1200)

    def test_sof_olvasas(self, tmp_path):
        assert em._forras_meret(_jpeg((123, 45))) == (123, 45)

    def test_nem_jpeg_forras_nem_ad_meretet(self):
        assert em._forras_meret(b"\xff\xd8\xff\xd9") is None

    def test_meret_hiaban_nincs_interop_de_az_exif_frissul(self, tmp_path, monkeypatch):
        monkeypatch.setattr(em, "_forras_meret", lambda _b: None)
        ki = _kimenet_exif(_forras(tmp_path, _tiff()), (1650, 1250))
        assert ki["Interop"] == {}
        assert ki["Exif"][0xA002][0][2] == struct.pack("<H", 1650)


def test_export_vegponttol_vegpontig(tmp_path):
    """A valódi export-úton is: a kimenet EXIF-jében ott az Interop."""
    from picasapy.export import ExportItem, ExportSettings, export_photos

    forras = _forras(tmp_path, None, size=(160, 120))
    report = export_photos(
        [ExportItem(forras, filters="bw=1;")], tmp_path / "out", ExportSettings()
    )
    assert report.failed == ()
    data = Path(report.exported[0]).read_bytes()
    for marker, seg in em._szegmensek(data):
        if marker == 0xE1 and seg[4:].startswith(_EXIF_ID):
            interop = _olvas(seg[4 + len(_EXIF_ID) :])["Interop"]
            assert interop[0x0002] == [(7, 4, b"0100")]
            assert interop[0x1001][0][2] == struct.pack(">I", 160)
            return
    pytest.fail("nincs EXIF")
