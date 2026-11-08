"""#6712: a natív szemcse a köteg export-szálának CRT-folyamát követi.

A `data/grain_stream_6712/` képpárjai a 433/434-es eredeti Picasa-exportokból
származó kivágások. A forrásfoltot a valódi képméretű fekete vászonra tesszük,
majd az export JPEG-et a mért Picasa DQT-kkel és 4:2:0 mintavételezéssel
kódoljuk újra. A hétsoros ellenőrzés így az eredeti exporttal azonos ablakot
hasonlítja össze, nem egy helyben rögzített renderreferenciát.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from picasapy.export import ExportItem, export_photos
from picasapy.export import exporter

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "tools" / "golden"))
from compare_render import Thresholds, _read_rgb, compare_images  # noqa: E402
from jpeg_reference import jpeg_encode_like  # noqa: E402

_ADATOK = Path(__file__).parent / "data" / "grain_stream_6712"
_BEILLESZTES = (304, 224)
_ABLAK = (320, 240, 480, 368)
_MERETEK = {
    "k03": (1280, 853),
    "k05": (1280, 807),
    "k07": (1280, 853),
    "k09": (1280, 851),
    "k10": (1280, 853),
}
_ESETEK = (
    ("001_k03", "PicnikGrain=1,9.856920,1;"),
    ("001_k05", "grain2=1;"),
    ("001_k07", "grain2=1;"),
    ("001_k09", "grain=1;"),
    ("001_k10", "grain2=1;"),
    ("002_k03", "grain2=1;"),
    ("002_k10", "grain=1;"),
)

# A 433/434-es Picasa-exportok mindegyikében azonos DQT-k és 4:2:0 minta van.
_JPEG = {
    "subsampling": 2,
    "qtables": {
        0: [
            4, 3, 3, 4, 6, 10, 13, 16, 3, 3, 4, 5, 7, 15, 16, 14,
            4, 3, 4, 6, 10, 15, 18, 15, 4, 4, 6, 8, 13, 23, 21, 16,
            5, 6, 10, 15, 18, 28, 27, 20, 6, 9, 14, 17, 21, 27, 29, 24,
            13, 17, 20, 23, 27, 31, 31, 26, 19, 24, 25, 25, 29, 26, 27, 26,
        ],
        1: [
            4, 5, 6, 12, 26, 26, 26, 26, 5, 5, 7, 17, 26, 26, 26, 26,
            6, 7, 15, 26, 26, 26, 26, 26, 12, 17, 26, 26, 26, 26, 26, 26,
            26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26,
            26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26,
        ],
    },
}


def _forrasvaszon(kepnev: str, cel: Path) -> Path:
    width, height = _MERETEK[kepnev]
    folt = _read_rgb(_ADATOK / f"{kepnev}_source.png")
    x, y = _BEILLESZTES
    vaszon = np.zeros((height, width, 3), dtype=np.uint8)
    vaszon[y : y + folt.shape[0], x : x + folt.shape[1]] = folt
    cel.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(vaszon).save(cel)
    return cel


@pytest.fixture(scope="module")
def exportalt_kepek(tmp_path_factory: pytest.TempPathFactory):
    """Két exportköteget renderel, a Picasa JPEG-paramétereivel kódolva."""
    temp = tmp_path_factory.mktemp("grain-stream-6712")
    kimenetek: dict[str, np.ndarray] = {}

    def picasa_jpeg(image: np.ndarray, _settings, _source: Path | None) -> bytes:
        # Az exporter BGR-t ad a kódolónak, a mérőharness RGB-t használ.
        rgb = image[..., ::-1].copy()
        return jpeg_encode_like(rgb, _JPEG)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(exporter, "_encode_jpeg", picasa_jpeg)
        for batch in ("001", "002"):
            items = []
            for case_id, filters in _ESETEK:
                prefix, stem = case_id.split("_", 1)
                if prefix != batch:
                    continue
                source = _forrasvaszon(stem, temp / batch / f"{stem}.png")
                items.append(ExportItem(source=source, filters=filters))

            report = export_photos(items, temp / f"out-{batch}")
            assert report.failed == (), report.reasons
            assert len(report.exported) == len(items)
            for target in report.exported:
                key = f"{batch}_{target.stem}"
                with Image.open(target) as encoded:
                    decoded = np.asarray(encoded.convert("RGB"))
                x0, y0, x1, y1 = _ABLAK
                kimenetek[key] = decoded[y0:y1, x0:x1].copy()

    return kimenetek


@pytest.mark.parametrize(
    "case_id", [row[0] for row in _ESETEK], ids=[row[0] for row in _ESETEK]
)
def test_kotegelt_szemcse_az_eredeti_picasa_kivagassal_egyezik(
    exportalt_kepek: dict[str, np.ndarray],
    case_id: str,
) -> None:
    reference = _read_rgb(_ADATOK / f"{case_id}_export.png")
    verdict, metrics, note = compare_images(
        exportalt_kepek[case_id], reference, Thresholds()
    )
    assert verdict == "pixelhű", (
        f"{case_id}: {verdict}; SSIM={metrics.get('ssim')}, "
        f"ΔE={metrics.get('delta_e_mean')}, max_diff={metrics.get('max_diff')}; {note}"
    )
