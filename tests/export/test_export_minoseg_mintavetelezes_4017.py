"""A kiválasztott exportminőség a tényleges JPEG DQT-jében és SOF-jában látszik (#4017)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from picasapy.export import (
    ExportItem,
    ExportSettings,
    export_photos,
    is_automatic_quality,
    resolve_export_quality,
    resolve_export_subsampling,
)


def _forras_jpeg(hely: Path, *, quality: int = 97, subsampling: int = 0) -> Path:
    zaj = (np.random.RandomState(4017).rand(160, 120, 3) * 255).astype("uint8")
    Image.fromarray(zaj).save(
        hely, format="JPEG", quality=quality, subsampling=subsampling
    )
    return hely


def _mintavetelezes(kep: Image.Image) -> tuple[tuple[int, int], ...]:
    return tuple((h, v) for _azonosito, h, v, _tabla in kep.layer)


@pytest.mark.parametrize(
    (
        "fokozat",
        "preset",
        "custom_quality",
        "expected_quality",
        "subsampling",
        "elso_dqt",
    ),
    [
        (
            "Normal",
            "normal",
            50,
            85,
            2,
            ((5, 3, 3, 5, 7, 12), (5, 5, 7, 14, 30, 30)),
        ),
        (
            "Maximum",
            "maximum",
            50,
            93,
            0,
            ((2, 2, 1, 2, 3, 6), (2, 3, 3, 7, 14, 14)),
        ),
        (
            "Minimum",
            "minimum",
            50,
            65,
            2,
            ((11, 8, 7, 11, 17, 28), (12, 13, 17, 33, 69, 69)),
        ),
        (
            "Custom (85)",
            "custom",
            85,
            85,
            2,
            ((5, 3, 3, 5, 7, 12), (5, 5, 7, 14, 30, 30)),
        ),
        (
            "Custom (95)",
            "custom",
            95,
            95,
            2,
            ((2, 1, 1, 2, 2, 4), (2, 2, 2, 5, 10, 10)),
        ),
    ],
)
def test_a_kimeneti_jpeg_a_valasztott_fokozat_dqt_jet_es_mintavetelezeset_irja(
    tmp_path,
    fokozat,
    preset,
    custom_quality,
    expected_quality,
    subsampling,
    elso_dqt,
):
    forras = _forras_jpeg(tmp_path / "forras.jpg")
    jpeg_quality = resolve_export_quality(preset, custom_quality)
    jpeg_subsampling = resolve_export_subsampling(preset)
    assert jpeg_quality == expected_quality
    assert jpeg_subsampling == subsampling
    jelentes = export_photos(
        [ExportItem(source=forras)],
        tmp_path / fokozat,
        ExportSettings(
            max_dimension=80,
            jpeg_quality=jpeg_quality,
            quality_automatic=is_automatic_quality(preset),
            jpeg_subsampling=jpeg_subsampling,
        ),
    )

    assert jelentes.failed == (), jelentes.reasons
    with Image.open(jelentes.exported[0]) as kimenet:
        y_minta = (1, 1) if subsampling == 0 else (2, 2)
        assert _mintavetelezes(kimenet) == (y_minta, (1, 1), (1, 1)), (
            f"{fokozat}: hibás JPEG mintavételezés"
        )
        assert tuple(tuple(kimenet.quantization[i][:6]) for i in (0, 1)) == elso_dqt


@pytest.mark.parametrize("source_subsampling", (0, 2), ids=("444", "420"))
def test_automatic_a_forras_jpeg_mintavetelezeset_is_megtartja(
    tmp_path, source_subsampling
):
    forras = _forras_jpeg(
        tmp_path / "forras.jpg", subsampling=source_subsampling
    )
    with Image.open(forras) as kep:
        forras_dqt = {index: tuple(tabla) for index, tabla in kep.quantization.items()}
        forras_minta = _mintavetelezes(kep)

    jelentes = export_photos(
        [ExportItem(source=forras)],
        tmp_path / "automatic",
        ExportSettings(
            max_dimension=80,
            jpeg_quality=resolve_export_quality("automatic", 85),
            quality_automatic=is_automatic_quality("automatic"),
            jpeg_subsampling=resolve_export_subsampling("automatic"),
        ),
    )

    assert jelentes.failed == (), jelentes.reasons
    with Image.open(jelentes.exported[0]) as kimenet:
        assert _mintavetelezes(kimenet) == forras_minta
        assert {index: tuple(tabla) for index, tabla in kimenet.quantization.items()} == forras_dqt


# rontás-kontroll: a q=93 preset visszaállítva 100-ra, illetve az automatikus
# újrakódolás a forrás mintájának átvétele nélkül hagyva → Maximum és Automatic piros.
