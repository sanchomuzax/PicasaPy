"""JPEG-, TIFF- és videó-metaadat-olvasók fuzz-próbái."""
# ruff: noqa: E402

from __future__ import annotations

from io import BytesIO
import math
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import example, given, settings, strategies as st
from PIL import Image

from picasapy.metadata.jpeg_quality import jpeg_quality_text
from picasapy.metadata.makernote import (
    canon_camera_settings,
    nikon_objektiv_mezok,
    tiff_blokk,
)
from picasapy.metadata.reader import read_exif_details, read_file_metadata
from picasapy.metadata.tiff_blokk import TiffHiba
from picasapy.metadata.tiff_helyben import frissitett_tiff, tajolas_1_helyben
from picasapy.metadata.video import read_video_metadata
from picasapy.metadata.xmp_people import xmp_person_names


def _jpeg_mag() -> bytes:
    kep = Image.new("RGB", (8, 6), (30, 90, 150))
    exif = kep.getexif()
    exif[274] = 1
    kimenet = BytesIO()
    kep.save(kimenet, format="JPEG", exif=exif)
    return kimenet.getvalue()


def _tiff_mag() -> bytes:
    kimenet = BytesIO()
    Image.new("RGB", (3, 2), (20, 40, 60)).save(kimenet, format="TIFF")
    return kimenet.getvalue()


_JPEG_MAG = _jpeg_mag()
_TIFF_MAG = _tiff_mag()
_XMP_MAG = (
    b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
    b'xmlns:mwg-rs="http://www.metadataworkinggroup.com/schemas/regions/" '
    b'xmlns:stArea="http://ns.adobe.com/xap/1.0/sType/Area#">'
    b'<rdf:Description><mwg-rs:RegionList><rdf:li rdf:parseType="Resource">'
    b'<mwg-rs:Name>Fuzz</mwg-rs:Name><mwg-rs:Area stArea:w="0.2" '
    b'stArea:h="0.3"/></rdf:li></mwg-rs:RegionList></rdf:Description></rdf:RDF>'
)
_TIFF_KORPUSZ = bytes.fromhex(
    (Path(__file__).parent / "korpusz" / "metadata" / "tiff.hex")
    .read_text(encoding="ascii")
    .strip()
)
_VIDEO_VEGES_SEBESSEG = st.floats(
    min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False
)
_VIDEO_VEGES_KOCKASZAM = st.floats(
    min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False
)
_VIDEO_SEBESSEG = st.one_of(
    _VIDEO_VEGES_SEBESSEG, st.sampled_from((0.0, -1.0, math.nan, math.inf, -math.inf))
)
_VIDEO_KOCKASZAM = st.one_of(
    _VIDEO_VEGES_KOCKASZAM, st.sampled_from((-1.0, math.nan, math.inf, -math.inf))
)


@st.composite
def _mutalt_kepbajtok(draw, seed: bytes):
    mod = draw(st.sampled_from(("valtozatlan", "csonkit", "csere", "ifd")))
    if mod == "valtozatlan":
        return seed + draw(st.binary(max_size=32))
    if mod == "csonkit":
        return seed[: draw(st.integers(min_value=0, max_value=len(seed)))]
    adat = bytearray(seed)
    if mod == "ifd":
        tiff = adat.find(b"Exif\x00\x00")
        if tiff >= 0:
            tiff += 6
            hely = tiff + 4
            adat[hely : hely + 4] = draw(st.integers(0, 0xFFFFFFFF)).to_bytes(
                4, "little"
            )
            return bytes(adat)
    hely = draw(st.integers(min_value=0, max_value=len(adat) - 1))
    adat[hely] = draw(st.integers(min_value=0, max_value=255))
    return bytes(adat)


@given(
    jpeg=_mutalt_kepbajtok(_JPEG_MAG),
    tiff=_mutalt_kepbajtok(_TIFF_MAG),
    xmp=st.one_of(st.just(_XMP_MAG), st.binary(max_size=4096)),
)
@example(jpeg=_JPEG_MAG, tiff=_TIFF_MAG, xmp=_XMP_MAG)
def test_mutalt_jpeg_es_tiff_metaadat_olvasok_nem_dobnak_varatlan_kivetelt(
    jpeg, tiff, xmp, tmp_path, fuzz_keret
):
    with TemporaryDirectory(prefix="metadata-", dir=tmp_path) as temp_dir:
        mappa = Path(temp_dir)
        jpeg_path = mappa / "mutalt.jpg"
        tiff_path = mappa / "mutalt.tif"
        with fuzz_keret():
            jpeg_path.write_bytes(jpeg)
            tiff_path.write_bytes(tiff)

            read_file_metadata(jpeg_path)
            read_exif_details(jpeg_path)
            jpeg_quality_text(jpeg_path)
            xmp_person_names(xmp)

            exif = tiff_blokk(jpeg_path)
            canon_camera_settings(exif)
            nikon_objektiv_mezok(exif)
            canon_camera_settings(_TIFF_KORPUSZ)
            nikon_objektiv_mezok(_TIFF_KORPUSZ)

            # A helyben író csak olvasható bemenetből köteles olvasható
            # kimenetet adni: az eleve sérült TIFF-et nem javítja meg, de nem
            # is ront rajta (a hívó egybájtos rontással mérte: mind a 721
            # olvasható bemenet olvasható maradt, olvashatatlan kimenet csak
            # olvashatatlan bemenetből lett).
            bemenet_olvashato = _pillow_olvassa(tiff)
            for muvelet in (tajolas_1_helyben, lambda adat: frissitett_tiff(adat, [])):
                try:
                    kimenet = muvelet(tiff)
                except TiffHiba:
                    continue
                if bemenet_olvashato:
                    assert _pillow_olvassa(kimenet), "olvasható TIFF-ből olvashatatlan lett"


def _pillow_olvassa(adat: bytes) -> bool:
    try:
        with Image.open(BytesIO(adat)) as kep:
            kep.load()
    except Exception:  # noqa: BLE001 - bármilyen olvasási hiba „olvashatatlan"
        return False
    return True


class _FakeVideoCapture:
    def __init__(self, cv2, sebesseg, kockaszam, megnyilt: bool) -> None:
        self._cv2 = cv2
        self._sebesseg = sebesseg
        self._kockaszam = kockaszam
        self._megnyilt = megnyilt

    def isOpened(self) -> bool:
        return self._megnyilt

    def get(self, tulajdonsag: int) -> float:
        if tulajdonsag == self._cv2.CAP_PROP_FPS:
            return self._sebesseg
        return self._kockaszam

    def release(self) -> None:
        return None


@given(
    sebesseg=_VIDEO_SEBESSEG,
    kockaszam=_VIDEO_KOCKASZAM,
    megnyilt=st.booleans(),
)
# Az első példa a videómodul lusta betöltése miatt másodpercekig tart; a
# dekóder itt álfelvétel, így a határidő nem mér semmit.
@settings(deadline=None)
def test_video_metadata_a_vegyes_dekoderadatokat_vegyes_eredmenyre_kepezi(
    sebesseg, kockaszam, megnyilt, fuzz_keret, monkeypatch
):
    import cv2

    capture = _FakeVideoCapture(cv2, sebesseg, kockaszam, megnyilt)
    monkeypatch.setattr(cv2, "VideoCapture", lambda _ut: capture)
    with fuzz_keret():
        eredmeny = read_video_metadata("fuzz.avi")

    assert eredmeny.movie_format == "AVI"
    ervenyes = (
        megnyilt
        and math.isfinite(sebesseg)
        and sebesseg > 0
        and math.isfinite(kockaszam)
        and kockaszam >= 0
    )
    if not ervenyes:
        assert eredmeny.frame_rate is None
        assert eredmeny.duration_seconds is None
    else:
        assert eredmeny.frame_rate == sebesseg
        assert eredmeny.duration_seconds == kockaszam / sebesseg


_LIBRAW_CIMTER = 2 * 1024**3


@pytest.mark.skipif(sys.platform == "win32", reason="RLIMIT_AS csak POSIX-on van")
def test_libraw_futas_kulon_idokorlatozott_folyamatban(tmp_path):
    pytest.importorskip("rawpy")
    for sorszam, payload in enumerate(
        (b"", b"\xff\xd8" + bytes(64), b"II*\x00" + bytes(128))
    ):
        raw_path = tmp_path / f"hibas-{sorszam}.raw"
        raw_path.write_bytes(payload)
        gyoker = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, (str(gyoker / "src"), env.get("PYTHONPATH", "")))
        )
        # A memóriakorlát a GYEREKFOLYAMATRA kerül: a szülőben beállított
        # RLIMIT_AS-sel már az új Python indítása is ENOMEM-mel bukna.
        futas = subprocess.run(
            [
                sys.executable,
                "-c",
                "import resource, sys; "
                f"resource.setrlimit(resource.RLIMIT_AS, ({_LIBRAW_CIMTER}, {_LIBRAW_CIMTER})); "
                "from picasapy.rawdecode import dekodol_nyerset; "
                "dekodol_nyerset(sys.argv[1])",
                str(raw_path),
            ],
            capture_output=True,
            check=False,
            env=env,
            timeout=10,
        )
        assert futas.returncode == 0, futas.stderr.decode("utf-8", "replace")
