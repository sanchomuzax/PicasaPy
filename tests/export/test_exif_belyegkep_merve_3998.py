"""A #3998 EXIF-bélyegképe a valódi, MÉRT Picasa-exporttal összevetve
(`3229-lanc-sorrend` négy és `3084-poszterizalas` két esete).

FIGYELEM: a mérőkészlet a `~/.local/share/picasapy-meroadat/meroadat.tar`-ban
van, ami a CI-n NINCS meg — ott ez a teszt kihagyódik (`skipif`). Helyben fut.

A tarból csak a két mérőmappa tagjai bomlanak ki (`tmp_path` alá). Az olvasás a
projekt saját `tiff_helyben._szerkezet`-ével történik (piexif nélkül). Esetenként
a projekt exportját és a Picasa exportját vetjük össze:

* a bélyegkép mérete, kvantálótáblái (luma, chroma), 4:2:0, baseline (SOF0);
* JFIF 1.01, sűrűségegység 0, 1:1;
* az IFD1 hat tagja (típus, darab, érték), a `0x201`/`0x202` kivételével (az
  eltolás és a hossz eltérhet); a bélyegkép a blokk végén áll;
* a kicsinyítő lánc: a Picasa exportjának FŐKÉPÉBŐL a mi `exif_belyegkep`
  függvényeinkkel készült bélyegkép átlagos eltérése a Picasa bélyegképétől
  < 1,5 (0–255)."""

from __future__ import annotations

import re
import struct
import tarfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.metadata import exif_belyegkep as bk
from picasapy.metadata import tiff_helyben as th
from picasapy.metadata.export_metadata import _szegmensek

_TAR = Path.home() / ".local/share/picasapy-meroadat/meroadat.tar"
_EXIF_ID = b"Exif\x00\x00"
_ELONEZET = 0x10000  # a `_szerkezet` kulcsa az előnézet bájtjainak
_KIVEVE = {0x0201, 0x0202}
_ATLAG_HATAR = 1.5

_LANC = "3229-lanc-sorrend"
_POSZTER = "3084-poszterizalas"
#: a Picasa főképe MÁS méretű, mint a miénk (a Picasa exportja 1600 × 1200, a miénk a
#: vágott kép; #4008), ezért a bélyegkép mérete sem
#: lehet azonos; ott a képletet mindkét oldalon a saját főkép méretére ellenőrizzük.
_MAS_FOKEP_MERET = {"04-vagas-utan-vignetta.jpg"}

_ESETEK = [
    (_LANC, "01-keret-utan-szepia.jpg"),
    (_LANC, "02-szepia-utan-keret.jpg"),
    (_LANC, "03-keret-utan-vignetta.jpg"),
    (_LANC, "04-vagas-utan-vignetta.jpg"),
    (_POSZTER, "quantizepalette__alap.jpg"),  # 960 × 640
    (_POSZTER, "Warm grasses by dcsearle.t21.jpg"),
]

pytestmark = pytest.mark.skipif(not _TAR.is_file(), reason="a mérőadat-tar nincs meg (CI-n nincs)")


@pytest.fixture(scope="module")
def mero(tmp_path_factory) -> Path:
    gyoker = tmp_path_factory.mktemp("meres3998")
    with tarfile.open(_TAR) as tar:
        tagok = [
            t
            for t in tar.getmembers()
            if any(t.name == m or t.name.startswith(m + "/") for m in (_LANC, _POSZTER))
        ]
        tar.extractall(gyoker, members=tagok, filter="data")
    return gyoker


@pytest.fixture(scope="module")
def sajat(mero) -> Path:
    """A projekt exportja mind a hat esetre (a `filters=` sorral az ini-ből)."""
    ki = mero / "sajat"
    for mappa in (_LANC, _POSZTER):
        ini = (mero / mappa / ".picasa.ini").read_text(encoding="utf-8")
        lancok = re.findall(r"\[(.*?\.jpg)\]\r?\nfilters=(.*?)\r?\n", ini)
        report = export_photos(
            [ExportItem(mero / mappa / nev, filters=f) for nev, f in lancok],
            ki / mappa,
            ExportSettings(),
        )
        assert report.failed == ()
    return ki


def _tiff(path: Path) -> bytes:
    for marker, seg in _szegmensek(path.read_bytes()):
        if marker == 0xE1 and seg[4:].startswith(_EXIF_ID):
            return seg[4 + len(_EXIF_ID) :]
    raise AssertionError(f"nincs EXIF: {path}")


def _ertek(tipus: int, darab: int, nyers: bytes, e: str):
    """A bejegyzés értéke egészként/párként, a fájl bájtsorrendje szerint."""
    kod = {3: "H", 4: "I", 5: "I"}.get(tipus)
    if kod is None:
        return nyers
    db = darab * (2 if tipus == 5 else 1)
    meret = struct.calcsize(kod) * db
    return struct.unpack(e + kod * db, nyers[:meret])


def _ifd1(path: Path):
    """(tagok {tag: (típus, darab, érték)}, előnézet JPEG, a TIFF-blokk,
    a `0x201`/`0x202` értéke)."""
    tiff = _tiff(path)
    e = "<" if tiff[:2] == b"II" else ">"
    szerk = th._szerkezet(tiff, len(tiff))
    tagek = {}
    for (ifd, tag), peldanyok in szerk.items():
        if ifd != "1st" or tag == _ELONEZET:
            continue
        assert len(peldanyok) == 1, hex(tag)
        tipus, darab, nyers = peldanyok[0]
        tagek[tag] = (tipus, darab, _ertek(tipus, darab, nyers, e))
    jpeg = szerk[("1st", _ELONEZET)][0][2]
    return tagek, jpeg, tiff, tagek[0x0201][2][0], tagek[0x0202][2][0]


def _fokep_meret(path: Path) -> tuple[int, int]:
    return _jpeg_jellemzok(path.read_bytes())["meret"]


def _jpeg_jellemzok(jpeg: bytes) -> dict:
    """Méret, kvantálótáblák, al-mintavétel, SOF-típus és JFIF a szegmensekből."""
    ki: dict = {"kvant": {}}
    for marker, seg in _szegmensek(jpeg):
        adat = seg[4:]
        if marker == 0xE0 and adat.startswith(b"JFIF\x00"):
            ki["jfif"] = (adat[5], adat[6], adat[7], struct.unpack(">HH", adat[8:12]))
        elif marker == 0xDB:
            i = 0
            while i < len(adat):
                pq, tid = adat[i] >> 4, adat[i] & 15
                n = 128 if pq else 64
                ki["kvant"][tid] = adat[i + 1 : i + 1 + n]
                i += 1 + n
        elif marker in (0xC0, 0xC1, 0xC2):
            ki["sof"] = marker
            ki["meret"] = (int.from_bytes(adat[3:5], "big"), int.from_bytes(adat[1:3], "big"))
            ki["mintavetel"] = tuple(
                (adat[7 + 3 * c] >> 4, adat[7 + 3 * c] & 15) for c in range(adat[5])
            )
    return ki


def _a_blokk_vegen_all(hely: int, meret: int, tiff: bytes, nev: str) -> None:
    veg = hely + meret
    if veg == len(tiff):
        return
    assert veg % 2 == 1 and len(tiff) == veg + 1 and tiff[-1] == 0, nev


@pytest.mark.parametrize("mappa,nev", _ESETEK)
def test_a_belyegkep_tulajdonsagai_egyeznek(mero, sajat, mappa, nev):
    p_tagek, p_jpeg, p_tiff, p_hely, p_meret = _ifd1(mero / mappa / "export" / nev)
    s_tagek, s_jpeg, s_tiff, s_hely, s_meret = _ifd1(sajat / mappa / nev)
    pj, sj = _jpeg_jellemzok(p_jpeg), _jpeg_jellemzok(s_jpeg)
    # #4009: a TIFF-blokk bájtsorrendje (II/MM) is egyezik a Picasáéval
    assert s_tiff[:2] == p_tiff[:2], nev

    # a méret a saját főkép méretéből jön a spec képletével, mindkét exportban
    assert pj["meret"] == bk.belyegkep_meret(*_fokep_meret(mero / mappa / "export" / nev)), nev
    assert sj["meret"] == bk.belyegkep_meret(*_fokep_meret(sajat / mappa / nev)), nev
    if nev not in _MAS_FOKEP_MERET:
        assert sj["meret"] == pj["meret"], nev
    assert sj["kvant"][0] == pj["kvant"][0], nev  # luma
    assert sj["kvant"][1] == pj["kvant"][1], nev  # chroma
    assert pj["sof"] == sj["sof"] == 0xC0, nev  # baseline
    assert pj["mintavetel"] == sj["mintavetel"] == ((2, 2), (1, 1), (1, 1)), nev  # 4:2:0
    assert sj["jfif"] == pj["jfif"] == (1, 1, 0, (1, 1)), nev

    assert set(p_tagek) == set(s_tagek) and len(p_tagek) == 6, nev
    for tag in sorted(set(p_tagek) - _KIVEVE):
        assert s_tagek[tag] == p_tagek[tag], f"{nev}: {tag:#x}"

    # a bélyegkép a blokk végén áll (spec 16. H) 5.: ha a vége páratlan
    # eltolásra esik, 1 nullbájt követi), mindkét exportban
    _a_blokk_vegen_all(p_hely, p_meret, p_tiff, nev)
    _a_blokk_vegen_all(s_hely, s_meret, s_tiff, nev)
    assert len(s_jpeg) == s_meret and len(p_jpeg) == p_meret, nev


@pytest.mark.parametrize("mappa,nev", _ESETEK)
def test_a_kicsinyito_lanc_a_picasa_fokepebol_egyezik(mero, mappa, nev):
    export = mero / mappa / "export" / nev
    fokep = cv2.imread(str(export), cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
    assert bk.kell_belyegkep((fokep.shape[1], fokep.shape[0]))
    # mindkét oldal q85 JPEG-ből dekódolva: a nyers kicsinyítést a Picasa
    # KÓDOLT bélyegképével összevetve a JPEG-veszteség is beleszámítana
    # (a poszterizált, éles élű képen 2–4,5), ami nem a lánc hibája
    sajat_kicsi = cv2.imdecode(np.frombuffer(bk.belyegkep(fokep), np.uint8), cv2.IMREAD_COLOR)
    picasa_kicsi = cv2.imdecode(
        np.frombuffer(_ifd1(export)[1], np.uint8), cv2.IMREAD_COLOR
    )
    assert sajat_kicsi.shape == picasa_kicsi.shape, nev
    atlag = float(
        np.abs(sajat_kicsi.astype(np.int16) - picasa_kicsi.astype(np.int16)).mean()
    )
    assert atlag < _ATLAG_HATAR, f"{nev}: {atlag:.3f}"
