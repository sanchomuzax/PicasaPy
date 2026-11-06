"""JPEG-, TIFF- és videó-metaadat-olvasók fuzz-próbái."""
# ruff: noqa: E402

from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import example, given, strategies as st
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
    jpeg_path = tmp_path / "mutalt.jpg"
    tiff_path = tmp_path / "mutalt.tif"
    video_path = tmp_path / "mutalt.mp4"
    with fuzz_keret():
        jpeg_path.write_bytes(jpeg)
        tiff_path.write_bytes(tiff)
        video_path.write_bytes(jpeg[:4096])

        read_file_metadata(jpeg_path)
        read_exif_details(jpeg_path)
        jpeg_quality_text(jpeg_path)
        xmp_person_names(xmp)
        videoadat = read_video_metadata(video_path)
        assert videoadat.movie_format == "MP4"

        exif = tiff_blokk(jpeg_path)
        canon_camera_settings(exif)
        nikon_objektiv_mezok(exif)
        canon_camera_settings(_TIFF_KORPUSZ)
        nikon_objektiv_mezok(_TIFF_KORPUSZ)

        for muvelet in (tajolas_1_helyben,):
            try:
                kimenet = muvelet(tiff)
            except TiffHiba:
                continue
            with Image.open(BytesIO(kimenet)) as visszaolvasott:
                visszaolvasott.load()

        try:
            friss = frissitett_tiff(tiff, [])
        except TiffHiba:
            pass
        else:
            with Image.open(BytesIO(friss)) as visszaolvasott:
                visszaolvasott.load()


def test_libraw_futas_kulon_idokorlatozott_folyamatban(
    tmp_path, fuzz_keret
):
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
        with fuzz_keret():
            futas = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from picasapy.rawdecode import dekodol_nyerset; "
                    "import sys; dekodol_nyerset(sys.argv[1])",
                    str(raw_path),
                ],
                capture_output=True,
                check=False,
                env=env,
                timeout=2,
            )
        assert futas.returncode == 0, futas.stderr.decode("utf-8", "replace")
