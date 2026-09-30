"""Export crop64-előzményének és a külön aktuális crop mezőnek a regressziói."""

from __future__ import annotations

import logging
import tarfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

import picasapy.export.exporter as exporter_module
from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.ini import load_document, parse_document, save_document
from picasapy.ini.filters import parse_filters
from picasapy.render import apply_filters

_TAR = Path.home() / ".local/share/picasapy-meroadat/meroadat.tar"
_MAPPA = "3229-lanc-sorrend"
_VAGOTT = "04-vagas-utan-vignetta.jpg"
_CROP = "rect64(3c3c8c8c)"


def _forras(mappa: Path, nev: str = "pelda.png") -> tuple[Path, np.ndarray]:
    """Kiszámítható, tömörítetlen tesztkép, szín- és helyfüggő tartalommal."""
    y, x = np.indices((300, 400))
    rgb = np.stack(((x * 3 + y) % 256, (y * 5 + x) % 256, (x + y * 2) % 256), axis=2)
    source = mappa / nev
    Image.fromarray(rgb.astype(np.uint8), "RGB").save(source)
    return source, rgb.astype(np.uint8)


def _crop_mentese(source: Path, value: str) -> None:
    ini_path = source.parent / ".picasa.ini"
    document = load_document(ini_path) if ini_path.exists() else parse_document("")
    save_document(document.with_value(source.name, "crop", value), ini_path)


def _export(source: Path, filters: str, target: Path):
    return export_photos(
        [ExportItem(source, filters=filters)],
        target,
        ExportSettings(jpeg_quality=100),
    )


def _export_rgb(path: Path) -> np.ndarray:
    payload = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    assert image is not None
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _jpeg_q100_rgb(image_rgb: np.ndarray) -> np.ndarray:
    """A nézőképet az exporttal azonos OpenCV JPEG q100 úton kódolja."""
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    ok, payload = cv2.imencode(
        ".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 100]
    )
    assert ok
    decoded = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    assert decoded is not None
    return cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)


def _assert_export_matches_viewer(source: Path, filters: str, exported: Path) -> None:
    source_rgb = _export_rgb(source)
    viewer_rgb, _ = apply_filters(source_rgb, parse_filters(filters))
    export_rgb = _export_rgb(exported)
    viewer_jpeg_rgb = _jpeg_q100_rgb(viewer_rgb)
    assert export_rgb.shape == viewer_jpeg_rgb.shape
    mae = float(
        np.abs(export_rgb.astype(np.int16) - viewer_jpeg_rgb.astype(np.int16)).mean()
    )
    assert mae == 0.0


@pytest.mark.parametrize(
    "effect",
    [
        "Border=1,20.000000,5.000000,0.000000,00000000,00ffffff,0.000000;",
        "tilt=1,0.450000,0.000000;",
        "Vignette=1,35.000000,1.400000,0.000000,00000000;",
    ],
    ids=("Border", "tilt", "Vignette"),
)
def test_ervenyes_crop_a_lancbeli_helyen_marad_es_egyezik_a_nezovel(tmp_path, effect):
    source, _ = _forras(tmp_path)
    filters = f"crop64=1,3c3c8c8c;{effect}"
    _crop_mentese(source, _CROP)

    report = _export(source, filters, tmp_path / "export")

    assert report.failed == ()
    _assert_export_matches_viewer(source, filters, report.exported[0])


def test_crop_kulcs_a_lanc_utolso_crop64_elemet_helyben_csereli(tmp_path):
    source, _ = _forras(tmp_path)
    filters = (
        "crop64=1,10101010;"
        "Border=1,20.000000,5.000000,0.000000,00000000,00ffffff,0.000000;"
        "crop64=1,3c3c8c8c;"
        "Vignette=1,35.000000,1.400000,0.000000,00000000;"
    )
    crop = "rect64(20002000a000a000)"
    _crop_mentese(source, crop)
    viewer_filters = filters.replace("crop64=1,3c3c8c8c", f"crop64=1,{crop}")

    report = _export(source, filters, tmp_path / "export")

    assert report.failed == ()
    _assert_export_matches_viewer(source, viewer_filters, report.exported[0])


def test_olvashatatlan_ini_eseten_a_lanc_valtozatlanul_fut_tovabb(
    tmp_path, monkeypatch, caplog
):
    source, _ = _forras(tmp_path)
    filters = "crop64=1,3c3c8c8c;Border=1,20,5,0,00000000,00ffffff,0;"
    monkeypatch.setattr(
        exporter_module,
        "load_or_empty",
        lambda _path: (_ for _ in ()).throw(PermissionError("Permission denied")),
    )

    with caplog.at_level(logging.WARNING, logger=exporter_module.__name__):
        report = _export(source, filters, tmp_path / "export")

    assert report.failed == ()
    assert any(
        ".picasa.ini" in record.message.casefold()
        and "permission denied" in record.message.casefold()
        for record in caplog.records
    )
    _assert_export_matches_viewer(source, filters, report.exported[0])


def test_hibas_crop_kulcsnal_a_lanc_utolso_crop64_tagja_a_tartalek(
    tmp_path, caplog
):
    source, _ = _forras(tmp_path)
    filters = "crop64=1,3c3c8c8c;Vignette=1,35,1.4,0,00000000;"
    _crop_mentese(source, "1,2,3,4,5;")

    with caplog.at_level(logging.WARNING, logger=exporter_module.__name__):
        report = _export(source, filters, tmp_path / "export")

    assert report.failed == ()
    assert any(
        "crop" in record.message.casefold() and "érvénytelen" in record.message.casefold()
        for record in caplog.records
    )
    _assert_export_matches_viewer(source, filters, report.exported[0])


def _kibont(tmp_path: Path) -> Path:
    """A 04-es esethez szükséges tar-tagokat bontja ki a közös basetemp alá."""
    szukseges = {
        _MAPPA,
        f"{_MAPPA}/.picasa.ini",
        f"{_MAPPA}/{_VAGOTT}",
        f"{_MAPPA}/export",
        f"{_MAPPA}/export/{_VAGOTT}",
    }
    with tarfile.open(_TAR) as tar:
        tagok = [tag for tag in tar.getmembers() if tag.name.rstrip("/") in szukseges]
        tar.extractall(tmp_path, members=tagok, filter="data")
    return tmp_path / _MAPPA


def _meret(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


@pytest.mark.skipif(not _TAR.is_file(), reason="a mérőadat-tar nincs meg (CI-n nincs)")
def test_a_3229_04_crop64_előzmeny_crop_kulcs_nelkul_nem_vagja_az_exportot(tmp_path):
    mappa = _kibont(tmp_path)
    source = mappa / _VAGOTT
    szekcio = load_document(mappa / ".picasa.ini").section(_VAGOTT)
    assert szekcio is not None
    assert szekcio.get("crop") is None
    filters = szekcio.get("filters")
    assert filters == "crop64=1,3c3c8c8c;Vignette=1,35.000000,1.400000,0.000000;"

    eredeti_meret = _meret(source)
    picasa_meret = _meret(mappa / "export" / _VAGOTT)
    report = _export(source, filters, tmp_path / "export")

    assert report.failed == ()
    assert (eredeti_meret, picasa_meret, _meret(report.exported[0])) == (
        (1600, 1200),
        (1600, 1200),
        (1600, 1200),
    )
