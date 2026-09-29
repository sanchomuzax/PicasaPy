"""Az export metaadat-frissítése SEMMIT nem veszíthet el (#3961, a #3964 átnézése).

A régi út (#136) a forrás APP1/APP13 szegmenseit bájtra másolta. Az új,
spec szerinti frissítés (16. szakasz) csak KIEGÉSZÍTÉS lehet: amit a régi
megtartott, az új sem ronthatja el.

A kamerás mintát piexif NÉLKÜL, kézzel rakjuk össze (a piexif épp azt
rontja, amit mérünk): nem nullára végződő ASCII `ExifVersion`, ismeretlen
tagek, InteropIFD, MakerNote és IFD1-előnézet. Az olvasó is saját,
független a termékkódtól."""

from __future__ import annotations

import io
import struct
from pathlib import Path

import pytest
from PIL import Image

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.export import exporter as exporter_mod
from picasapy.metadata import export_metadata as em

_EXIF_ID = b"Exif\x00\x00"
_XMP_ID = b"http://ns.adobe.com/xap/1.0/\x00"
_EXT_ID = b"http://ns.adobe.com/xmp/extension/\x00"
_MERET = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8}
_MAKERNOTE = b"MKNT\x00\x01" + bytes(range(58))  # 64 bájt, eltolásra érzékeny


# --- kézi TIFF-építő és független olvasó ------------------------------------


def _ifd(bejegyzesek, kezdet, kovetkezo, e="<"):
    """Egy IFD a saját adatterületével; `bejegyzesek`: (tag, típus, darab, érték)."""
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


def _kameras_tiff(*, makernote=_MAKERNOTE, elonezet=None, e="<"):
    """Xiaomi-szerű EXIF-blokk: IFD0 → ExifIFD → InteropIFD, IFD1 előnézettel.
    A `PixelX/YDimension` HIÁNYZIK (hozzá kell adni)."""
    elonezet = elonezet if elonezet is not None else _jpeg_bajt((32, 24), "blue")

    def epit(exif_off, interop_off, ifd1_off, thumb_off):
        u32 = lambda v: struct.pack(e + "I", v)  # noqa: E731
        ifd0 = _ifd(
            [
                (0x010F, 2, 7, b"Xiaomi\x00"),
                (0x0110, 2, 11, b"Xiaomi 14T\x00"),
                (0x0112, 3, 1, struct.pack(e + "H", 1)),
                (0x0132, 2, 20, b"2025:05:01 09:31:22\x00"),
                (0x8769, 4, 1, u32(exif_off)),
            ],
            8,
            ifd1_off,
            e,
        )
        exif = _ifd(
            [
                (0x9000, 2, 4, b"0220"),  # ASCII, lezáró nulla NÉLKÜL
                (0x9003, 2, 20, b"2025:05:01 09:31:22\x00"),
                (0x927C, 7, len(makernote), makernote),
                (0x9999, 2, 12, b"ismeretlen!!"),
                (0x9A00, 7, 6, b"\x01\x02\x03\x04\x05\x06"),
                (0xA005, 4, 1, u32(interop_off)),
            ],
            exif_off,
            0,
            e,
        )
        interop = _ifd([(0x0001, 2, 4, b"R98\x00")], interop_off, 0, e)
        ifd1 = _ifd(
            [
                (0x0103, 3, 1, struct.pack(e + "H", 6)),
                (0x0201, 4, 1, u32(thumb_off)),
                (0x0202, 4, 1, u32(len(elonezet))),
            ],
            ifd1_off,
            0,
            e,
        )
        return ifd0, exif, interop, ifd1

    fejlec = (b"II" if e == "<" else b"MM") + struct.pack(e + "HI", 42, 8)
    ifd0, exif, interop, ifd1 = epit(0, 0, 0, 0)
    exif_off = 8 + len(ifd0)
    interop_off = exif_off + len(exif)
    ifd1_off = interop_off + len(interop)
    thumb_off = ifd1_off + len(ifd1)
    ifd0, exif, interop, ifd1 = epit(exif_off, interop_off, ifd1_off, thumb_off)
    return fejlec + ifd0 + exif + interop + ifd1 + elonezet


def _olvas(tiff):
    """{ifd: {tag: (típus, darab, eltolás, érték-bájtok)}} — független olvasó."""
    e = "<" if tiff[:2] == b"II" else ">"

    def ifd(off):
        (n,) = struct.unpack_from(e + "H", tiff, off)
        out = {}
        for i in range(n):
            tag, tipus, darab = struct.unpack_from(e + "HHI", tiff, off + 2 + 12 * i)
            meret = _MERET.get(tipus, 1) * darab
            mezo = off + 2 + 12 * i + 8
            hely = mezo if meret <= 4 else struct.unpack_from(e + "I", tiff, mezo)[0]
            out[tag] = (tipus, darab, hely, tiff[hely : hely + meret])
        (kov,) = struct.unpack_from(e + "I", tiff, off + 2 + 12 * n)
        return out, kov

    def mutato(ifd_, tag):
        return struct.unpack(e + "I", ifd_[tag][3])[0]

    ifd0, kov = ifd(struct.unpack_from(e + "I", tiff, 4)[0])
    out = {"0th": ifd0, "Exif": {}, "Interop": {}, "1st": {}}
    if 0x8769 in ifd0:
        out["Exif"] = ifd(mutato(ifd0, 0x8769))[0]
        if 0xA005 in out["Exif"]:
            out["Interop"] = ifd(mutato(out["Exif"], 0xA005))[0]
    if kov:
        out["1st"] = ifd(kov)[0]
    return out


# --- JPEG-szegmensek ---------------------------------------------------------


def _jpeg_bajt(size=(80, 60), szin="red"):
    buf = io.BytesIO()
    Image.new("RGB", size, szin).save(buf, "JPEG")
    return buf.getvalue()


def _app1(azonosito, torzs):
    return b"\xff\xe1" + (len(azonosito) + len(torzs) + 2).to_bytes(2, "big") + (
        azonosito + torzs
    )


def _forras(tmp_path, *szegmensek, size=(80, 60), nev="kamera.jpg"):
    raw = _jpeg_bajt(size)
    path = tmp_path / nev
    path.write_bytes(raw[:2] + b"".join(szegmensek) + raw[2:])
    return path


def _szegmensek(data):
    return em._szegmensek(data)


def _app1_torzs(path, azonosito):
    """Az első `azonosito`-jú APP1 törzse (az azonosító után), vagy None."""
    for marker, seg in _szegmensek(Path(path).read_bytes()):
        if marker == 0xE1 and seg[4:].startswith(azonosito):
            return seg[4 + len(azonosito) :]
    return None


def _export(source, tmp_path, **settings):
    report = export_photos(
        [ExportItem(source, filters="bw=1;")],
        tmp_path / "out",
        ExportSettings(**settings),
    )
    assert report.failed == ()
    return report.exported[0]


_XMP_EGYSZERU = (
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
    b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
    b"<dc:title>Cim</dc:title></rdf:Description></rdf:RDF></x:xmpmeta>"
)


# --- B1: a meglévő EXIF nem romolhat -----------------------------------------


class TestExifMegorzes:
    @pytest.fixture
    def par(self, tmp_path):
        tiff = _kameras_tiff()
        source = _forras(tmp_path, _app1(_EXIF_ID, tiff))
        return tiff, _app1_torzs(_export(source, tmp_path), _EXIF_ID)

    def test_exif_verzio_bajtra_marad(self, par):
        _, ki = par
        assert _olvas(ki)["Exif"][0x9000][3] == b"0220"

    def test_ismeretlen_tagek_megmaradnak(self, par):
        eredeti, ki = (_olvas(t)["Exif"] for t in par)
        for tag in (0x9999, 0x9A00):
            assert ki[tag][:2] == eredeti[tag][:2]
            assert ki[tag][3] == eredeti[tag][3]

    def test_interop_ifd_megmarad(self, par):
        assert _olvas(par[1])["Interop"][0x0001][3] == b"R98\x00"

    def test_makernote_eltolasa_es_bajtjai_valtozatlanok(self, par):
        eredeti, ki = (_olvas(t)["Exif"][0x927C] for t in par)
        assert ki[2] == eredeti[2]
        assert ki[3] == _MAKERNOTE

    def test_minden_eredeti_tag_bajtra_megvan(self, par):
        eredeti, ki = (_olvas(t) for t in par)
        valtozhat = {
            ("0th", 0x0132),  # DateTime: az export ideje
            ("0th", 0x8769),  # mutató: az IFD áthelyeződhet
            ("1st", 0x0201),  # az újragenerált előnézet helye
            ("1st", 0x0202),  # és hossza
        }
        for ifd, tagek in eredeti.items():
            for tag, (tipus, darab, _hely, ertek) in tagek.items():
                if (ifd, tag) in valtozhat:
                    continue
                assert ki[ifd][tag][0:2] == (tipus, darab), (ifd, hex(tag))
                assert ki[ifd][tag][3] == ertek, (ifd, hex(tag))

    def test_a_forras_bajtjai_nem_mozdulnak(self, par):
        """A blokk az eredeti bájtokkal kezdődik: csak helyben írt értékek és a
        végére fűzött új IFD-k térhetnek el — semmilyen eltolás nem csúszik."""
        eredeti, ki = par
        elter = [i for i in range(8, len(eredeti)) if i >= len(ki) or ki[i] != eredeti[i]]
        # az eltérések: az IFD0-mutató, a DateTime értéke (20 bájt), a helyben
        # írt mutatók, és a régi előnézet (ha a blokk végén volt, cserélődik)
        e = _olvas(eredeti)
        datum = range(e["0th"][0x0132][2], e["0th"][0x0132][2] + 20)
        elonezet_kezdet = struct.unpack("<I", e["1st"][0x0201][3])[0]
        # helyben írt mutató/érték-mezők: az ExifIFD-mutató (az áthelyezett
        # ExifIFD-re) és az IFD1 két előnézet-mezője
        ifd1_ertekek = {
            hely + k
            for hely in (e["0th"][0x8769][2], e["1st"][0x0201][2], e["1st"][0x0202][2])
            for k in range(4)
        }
        assert all(
            i in datum or i in ifd1_ertekek or i >= elonezet_kezdet for i in elter
        )

    def test_datetime_helyben_frissul(self, par):
        eredeti, ki = (_olvas(t)["0th"][0x0132] for t in par)
        assert ki[2] == eredeti[2]
        assert ki[3] != eredeti[3]

    def test_hianyzo_meret_es_szerzo_hozzaadva(self, par):
        ki = _olvas(par[1])
        assert struct.unpack("<H", ki["Exif"][0xA002][3][:2])[0] == 80
        assert ki["0th"][0x0131][3] == b"PicasaPy\x00"
        assert ki["0th"][0x013B][3] == b"PicasaPy\x00"

    def test_nagy_vegu_blokk_is(self, tmp_path):
        tiff = _kameras_tiff(e=">")
        ki = _app1_torzs(_export(_forras(tmp_path, _app1(_EXIF_ID, tiff)), tmp_path), _EXIF_ID)
        assert ki[:2] == b"MM"
        assert _olvas(ki)["Exif"][0x9000][3] == b"0220"
        assert _olvas(ki)["Exif"][0x927C][2] == _olvas(tiff)["Exif"][0x927C][2]


class TestElonezetIfd1:
    """J3: az eredeti az előnézetet újragenerálja; mi a kimenetből, 160×120-ba."""

    def test_elonezet_a_kimenetbol_ujrageneralva(self, tmp_path):
        tiff = _kameras_tiff()
        source = _forras(tmp_path, _app1(_EXIF_ID, tiff), size=(80, 40))
        report = export_photos(
            [ExportItem(source, rotate_steps=1)], tmp_path / "out"
        )
        ki = _app1_torzs(report.exported[0], _EXIF_ID)
        ifd1 = _olvas(ki)["1st"]
        kezdet = struct.unpack("<I", ifd1[0x0201][3])[0]
        hossz = struct.unpack("<I", ifd1[0x0202][3])[0]
        with Image.open(io.BytesIO(ki[kezdet : kezdet + hossz])) as kep:
            # a forgatott (40×80) kimenet előnézete: álló, 160×120-ba fér
            assert kep.size[0] < kep.size[1]
            assert kep.size[0] <= 160 and kep.size[1] <= 120

    def test_ha_nem_generalhato_a_forrase_marad(self, tmp_path, monkeypatch):
        monkeypatch.setattr(em, "_elonezet", lambda *_a: None)
        tiff = _kameras_tiff()
        ki = _app1_torzs(_export(_forras(tmp_path, _app1(_EXIF_ID, tiff)), tmp_path), _EXIF_ID)
        eredeti, uj = _olvas(tiff)["1st"], _olvas(ki)["1st"]
        assert uj[0x0201][3] == eredeti[0x0201][3]
        assert uj[0x0202][3] == eredeti[0x0202][3]


@pytest.mark.skipif(
    not any(
        p.is_file()
        for p in (
            Path(__file__).parents[2] / "research/testdata/2025-05-xx/IMG_20250501_093121.jpg",
            Path.home() / "Documents/PicasaPy/research/testdata/2025-05-xx/IMG_20250501_093121.jpg",
        )
    ),
    reason="a Xiaomi 14T minta (research/, gitignore-olt) nem elérhető",
)
def test_valodi_xiaomi_jpeg_exif_bajtra_megmarad(tmp_path):
    jeloltek = (
        Path(__file__).parents[2] / "research/testdata/2025-05-xx/IMG_20250501_093121.jpg",
        Path.home() / "Documents/PicasaPy/research/testdata/2025-05-xx/IMG_20250501_093121.jpg",
    )
    source = next(p for p in jeloltek if p.is_file())
    kimenet = _export(source, tmp_path, max_dimension=400)
    eredeti, ki = (_olvas(_app1_torzs(p, _EXIF_ID)) for p in (source, kimenet))
    valtozhat = {("0th", 0x0132), ("0th", 0x8769), ("1st", 0x0201), ("1st", 0x0202),
                 ("Exif", 0xA002), ("Exif", 0xA003)}
    for ifd, tagek in eredeti.items():
        for tag, (tipus, darab, _hely, ertek) in tagek.items():
            if (ifd, tag) not in valtozhat:
                assert ki[ifd][tag][:2] == (tipus, darab), (ifd, hex(tag))
                assert ki[ifd][tag][3] == ertek, (ifd, hex(tag))
    assert ki["Exif"][0x927C][2] == eredeti["Exif"][0x927C][2]
    with Image.open(kimenet) as kep:
        meret = kep.size
    x, y = (ki["Exif"][t] for t in (0xA002, 0xA003))
    e = "<" if _app1_torzs(kimenet, _EXIF_ID)[:2] == b"II" else ">"

    def ertek(m):
        return struct.unpack(e + ("I" if m[0] == 4 else "H"), m[3])[0]

    assert (ertek(x), ertek(y)) == meret


# --- B2: hibánál a régi bájtmásolás -------------------------------------------


class TestVisszaeses:
    def test_serult_exif_bajtra_atmegy(self, tmp_path):
        serult = _app1(_EXIF_ID, b"II*\x00\xff\xff\xff\x7fszemet")
        kimenet = _export(_forras(tmp_path, serult), tmp_path)
        assert serult in kimenet.read_bytes()

    def test_exif_iro_kivetele_utan_a_forras_exifje_megy(self, tmp_path, monkeypatch):
        def hibas(*_a, **_k):
            raise RuntimeError("író-hiba")

        monkeypatch.setattr(em, "frissitett_tiff", hibas)
        exif = _app1(_EXIF_ID, _kameras_tiff())
        xmp = _app1(_XMP_ID, _XMP_EGYSZERU)
        kimenet = _export(_forras(tmp_path, exif, xmp), tmp_path)
        assert exif in kimenet.read_bytes()
        # mezőnként: az XMP frissítése ettől még megtörtént
        assert b"ModifyDate" in _app1_torzs(kimenet, _XMP_ID)

    def test_xmp_hiba_nem_viszi_el_az_exif_frissitest(self, tmp_path, monkeypatch):
        def hibas(*_a, **_k):
            raise RuntimeError("xmp-hiba")

        monkeypatch.setattr(em, "_xmp_frissitve", hibas)
        exif = _app1(_EXIF_ID, _kameras_tiff())
        xmp = _app1(_XMP_ID, _XMP_EGYSZERU)
        kimenet = _export(_forras(tmp_path, exif, xmp), tmp_path)
        assert xmp in kimenet.read_bytes()
        assert 0xA002 in _olvas(_app1_torzs(kimenet, _EXIF_ID))["Exif"]

    def test_teljes_frissites_kivetele_utan_bajtmasolas(self, tmp_path, monkeypatch):
        def hibas(*_a, **_k):
            raise RuntimeError("váratlan")

        monkeypatch.setattr(exporter_mod, "frissitett_metaadat", hibas)
        exif = _app1(_EXIF_ID, _kameras_tiff())
        xmp = _app1(_XMP_ID, _XMP_EGYSZERU)
        kimenet = _export(_forras(tmp_path, exif, xmp), tmp_path)
        assert exif + xmp in kimenet.read_bytes()

    def test_65535_folotti_app1_eseten_nem_bukik_a_kep(self, tmp_path):
        """A forrás EXIF-je épp a határ alatt: a hozzáadott mezőkkel túllépne."""
        tiff = _kameras_tiff(makernote=b"M" * 60000)
        tiff += b"\x00" * (65535 - 2 - len(_EXIF_ID) - len(tiff))
        exif = _app1(_EXIF_ID, tiff)
        assert len(exif) == 65537
        kimenet = _export(_forras(tmp_path, exif), tmp_path)
        assert exif in kimenet.read_bytes()


class TestXmpVisszaeses:
    def test_serult_xmp_bajtra_atmegy(self, tmp_path):
        xmp = _app1(_XMP_ID, b"<x:xmpmeta xmlns:x='adobe:ns:meta/'><rdf:RDF><nincs-lezarva")
        kimenet = _export(_forras(tmp_path, xmp), tmp_path)
        assert xmp in kimenet.read_bytes()
        assert kimenet.read_bytes().count(_XMP_ID) == 1

    def test_burok_nelkuli_rdf_nem_cserelodik_le(self, tmp_path):
        csupasz = _XMP_EGYSZERU.split(b">", 1)[1].rsplit(b"</x:xmpmeta>", 1)[0]
        assert csupasz.startswith(b"<rdf:RDF")
        xmp = _app1(_XMP_ID, csupasz)
        kimenet = _export(_forras(tmp_path, xmp), tmp_path)
        assert xmp in kimenet.read_bytes()
        assert b"PicasaPy" not in _app1_torzs(kimenet, _XMP_ID)

    def test_hatarra_novo_xmp_a_forrase_marad(self, tmp_path):
        """A frissített csomag túllépné a 64 KiB-os APP1-et: a forrásé megy,
        nem hagyjuk el."""
        hely = 65535 - 2 - len(_XMP_ID) - len(_XMP_EGYSZERU)
        nagy = _XMP_EGYSZERU.replace(b"Cim", b"C" * (hely + 3))
        xmp = _app1(_XMP_ID, nagy)
        assert len(xmp) == 65537
        kimenet = _export(_forras(tmp_path, xmp), tmp_path)
        assert xmp in kimenet.read_bytes()

    def test_app1_hatar(self):
        torzs_max = 65535 - 2 - len(_XMP_ID)
        assert em._app1_ha_elfer(_XMP_ID, b"a" * torzs_max) is not None
        assert em._app1_ha_elfer(_XMP_ID, b"a" * (torzs_max + 1)) is None

    def test_kiterjesztett_xmp_valtozatlanul_atmegy(self, tmp_path):
        """J1: a `xmp/extension` szegmensek bájtra mennek."""
        ext = [
            _app1(_EXT_ID, b"0123456789ABCDEF0123456789ABCDEF" + struct.pack(">II", 20, i * 10)
                  + (b"<a>" + bytes([65 + i]) * 7))
            for i in range(2)
        ]
        xmp = _app1(_XMP_ID, _XMP_EGYSZERU)
        kimenet = _export(_forras(tmp_path, xmp, *ext), tmp_path).read_bytes()
        for szegmens in ext:
            assert szegmens in kimenet


class TestXmpExifSzures:
    def test_attributum_alaku_exif_mezok_is_torlodnek(self, tmp_path):
        """J4: `exif:FNumber="…"` attribútumként is kikerül, a dátum marad."""
        csomag = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
            b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about="" xmlns:exif="http://ns.adobe.com/exif/1.0/" '
            b'exif:FNumber="32/10" exif:ISOSpeedRatings="200" '
            b'exif:DateTimeOriginal="2014-06-21T15:03:38"/></rdf:RDF></x:xmpmeta>'
        )
        kimenet = _export(_forras(tmp_path, _app1(_XMP_ID, csomag)), tmp_path)
        xmp = _app1_torzs(kimenet, _XMP_ID).decode()
        assert "FNumber" not in xmp and "ISOSpeedRatings" not in xmp
        assert 'DateTimeOriginal="2014-06-21T15:03:38"' in xmp


class TestKamerasXmpNelkul:
    """J2: kamerás (EXIF-es), XMP nélküli forrás: csak `xmp:ModifyDate`."""

    def test_nincs_picasapy_szerzo_az_xmp_ben(self, tmp_path):
        source = _forras(tmp_path, _app1(_EXIF_ID, _kameras_tiff()))
        xmp = _app1_torzs(_export(source, tmp_path), _XMP_ID).decode()
        assert "ModifyDate" in xmp
        assert "creator" not in xmp and "PicasaPy" not in xmp
        assert "exif:" not in xmp


# --- a helyben író TIFF-szerkesztő közvetlenül ---------------------------------


def _kis_tiff(exif_bejegyzesek, ifd0_extra=()):
    """IFD0 (ExifIFD-mutatóval) + ExifIFD, kis végű."""
    ifd0_hossz = len(_ifd([(0x8769, 4, 1, b"\x00" * 4), *ifd0_extra], 8, 0))
    exif_off = 8 + ifd0_hossz
    ifd0 = _ifd([(0x8769, 4, 1, struct.pack("<I", exif_off)), *ifd0_extra], 8, 0)
    return b"II*\x00\x08\x00\x00\x00" + ifd0 + _ifd(exif_bejegyzesek, exif_off, 0)


def _meret(tiff, tag):
    tipus, _d, _h, ertek = _olvas(tiff)["Exif"][tag]
    e = "<" if tiff[:2] == b"II" else ">"
    return struct.unpack(e + ("I" if tipus == 4 else "H"), ertek)[0]


class TestTiffHelyben:
    def _valtozasok(self, x, y, datum="2026:09:29 10:00:00"):
        from picasapy.metadata import tiff_helyben as th

        return [
            th.Valtozas("0th", 0x0132, th.ascii_ertek(datum)),
            th.Valtozas("Exif", 0x9000, th.Ertek(th.UNDEFINED, b"0220"), csak_ha_hianyzik=True),
            th.Valtozas("Exif", 0xA002, th.Ertek(th.SHORT, x)),
            th.Valtozas("Exif", 0xA003, th.Ertek(th.SHORT, y)),
        ]

    def test_helyben_irt_ertek_az_athelyezett_ifd_be_is_atkerul(self):
        """A meglévő méret helyben íródik, az ExifIFD pedig (a hiányzó
        `ExifVersion` miatt) áthelyeződik: az új érték a másolatba is kell."""
        tiff = _kis_tiff([(0xA002, 3, 1, struct.pack("<H", 10)), (0xA003, 3, 1, struct.pack("<H", 20))])
        ki = em.frissitett_tiff(tiff, self._valtozasok(300, 200))
        assert (_meret(ki, 0xA002), _meret(ki, 0xA003)) == (300, 200)
        assert _olvas(ki)["Exif"][0x9000][3] == b"0220"

    def test_short_mezobe_nem_fero_meret_long_lesz(self):
        tiff = _kis_tiff([(0x9000, 7, 4, b"0230"), (0xA002, 3, 1, struct.pack("<H", 10)), (0xA003, 3, 1, struct.pack("<H", 20))])
        ki = em.frissitett_tiff(tiff, self._valtozasok(70000, 20))
        assert _meret(ki, 0xA002) == 70000 and _olvas(ki)["Exif"][0xA002][0] == 4
        assert _olvas(ki)["Exif"][0x9000][3] == b"0230"

    def test_rovid_datetime_nem_irodik_tul_a_szomszedra(self):
        """A 10 bájtos `DateTime`-ba a 20 bájtos nem fér: új értékhelyre kerül,
        a régi bájtjai és a szomszédja érintetlen."""
        tiff = _kis_tiff([(0x9000, 7, 4, b"0230")], ifd0_extra=[(0x0132, 2, 10, b"2020:01:0\x00"), (0x010F, 2, 6, b"Canon\x00")])
        ki = em.frissitett_tiff(tiff, self._valtozasok(1, 1))
        assert _olvas(ki)["0th"][0x0132][3] == b"2026:09:29 10:00:00\x00"
        assert _olvas(ki)["0th"][0x010F][3] == b"Canon\x00"
        # a forrás bájtjai: csak a fejléc IFD0-mutatója és az ExifIFD-mutató
        # (a PixelX/Y miatt áthelyezett ExifIFD-re) más
        mutato = _olvas(tiff)["0th"][0x8769][2]
        maszk = lambda b: b[8:mutato] + b[mutato + 4 :]  # noqa: E731
        assert maszk(ki[: len(tiff)]) == maszk(tiff)

    def test_blokkon_kivuli_eltolas_tiffhiba(self):
        from picasapy.metadata.tiff_helyben import TiffHiba

        tiff = b"II*\x00\x08\x00\x00\x00" + struct.pack("<H", 1) + struct.pack("<HHII", 0x0132, 2, 20, 9999) + b"\x00" * 4
        with pytest.raises(TiffHiba):
            em.frissitett_tiff(tiff, self._valtozasok(1, 1))

    def test_ures_forrasbol_uj_blokk(self):
        ki = em.frissitett_tiff(None, self._valtozasok(64, 48))
        assert (_meret(ki, 0xA002), _meret(ki, 0xA003)) == (64, 48)
        assert _olvas(ki)["0th"][0x0132][3] == b"2026:09:29 10:00:00\x00"
