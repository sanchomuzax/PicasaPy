"""#4233: a két 3229-es részleges Vignette-export zajszinten egyezzen."""

from __future__ import annotations

import tarfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.export.exporter import ExportItem, ExportSettings, export_photos
from picasapy.ini import load_document


_ARCHIVE = Path.home() / ".local/share/picasapy-meroadat/meroadat.tar"
_KONYVTAR = "3229-lanc-sorrend"
# Mért javított MAE: 03 belső 2.278, teljes 2.154; 04 1.566.
# Az 5-ös plafon JPEG-kódoló eltérést enged, a régi 23–28-as hibát nem.
_MAE_ZAJKORLAT = 5.0

pytestmark = pytest.mark.skipif(
    not _ARCHIVE.is_file(),
    reason="a 3229-es mérőadat-archívum nincs ezen a gépen",
)


@pytest.mark.parametrize(
    "name",
    (
        "03-keret-utan-vignetta.jpg",
        "04-vagas-utan-vignetta.jpg",
    ),
)
def test_export_a_picasa_kimenettel_zajszinten_egyezik(name, tmp_path):
    relpaths = (
        f"{_KONYVTAR}/.picasa.ini",
        f"{_KONYVTAR}/{name}",
        f"{_KONYVTAR}/export/{name}",
    )
    with tarfile.open(_ARCHIVE, mode="r:") as archive:
        for relpath in relpaths:
            member = archive.extractfile(relpath)
            assert member is not None, f"hiányzik az archívumból: {relpath}"
            target = tmp_path / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            with member:
                target.write_bytes(member.read())

    base = tmp_path / _KONYVTAR
    source = base / name
    picasa_export = base / "export" / name
    ini = load_document(base / ".picasa.ini")
    section = ini.section(name)
    assert section is not None
    filters = section.get("filters")
    assert filters is not None

    output_dir = tmp_path / "picasapy-export"
    report = export_photos(
        (ExportItem(source=source, filters=filters),),
        output_dir,
        ExportSettings(jpeg_quality=100),
    )
    assert not report.failed, report.reasons

    expected = cv2.imread(str(picasa_export), cv2.IMREAD_COLOR)
    actual = cv2.imread(str(report.exported[0]), cv2.IMREAD_COLOR)
    assert expected is not None and actual is not None
    assert actual.shape == expected.shape
    mae = float(np.abs(actual.astype(np.int16) - expected.astype(np.int16)).mean())
    assert mae <= _MAE_ZAJKORLAT, f"MAE={mae:.4f} > {_MAE_ZAJKORLAT:.1f}"
