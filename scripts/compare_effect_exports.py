#!/usr/bin/env python3
"""Két teljes Picasa-export kép-a-képhez összevetése (#1143).

A szkript a Picasa és a PicasaPy azonos forrásokból készült exportját méri.
Minden közös, relatív útvonalú képnél az átlagos abszolút csatornaeltérést
adja vissza; a méret- és fájlhiány eltérést jelent. A kimenet effekt és
változat szerint determinisztikusan rendezett, ezért új mérési körök
összevetésére is alkalmas.

Példa (a NAS csak olvasott bemenet):
  python3 scripts/compare_effect_exports.py \
    '/mnt/nas/My Pictures/PicasaPy meroszett/export-202608151229' \
    '/mnt/nas/My Pictures/PicasaPy meroszett/export-202608202231' \
    --json /tmp/picasapy-1143-meres.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np


_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png"})


def _validate_directory(path: Path, description: str) -> None:
    """A kötelező bemeneti könyvtár létét és típusát ellenőrzi."""
    if not path.exists():
        raise ValueError(f"A {description} könyvtár nem létezik: {path}")
    if not path.is_dir():
        raise ValueError(f"A {description} útvonal nem könyvtár: {path}")


def _image_paths(root: Path) -> dict[str, Path]:
    """A támogatott képeket relatív, rendezhető útvonalukkal adja vissza."""
    paths = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() in _IMAGE_SUFFIXES
    ]
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix())
    }


def _read_image(path: Path) -> np.ndarray:
    """Képet olvas RGB/RGBA uint8 tömbként, Windows-kompatibilis bájtúton."""
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"A kép nem olvasható: {path}") from exc
    image = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"A kép nem olvasható: {path}")
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
    raise ValueError(f"A kép nem támogatott csatornaszámú: {path}")


def _effect_and_variant(relative_path: str) -> tuple[str, str]:
    """A ``effekt__változat.jpg`` névből kulcsokat készít a riporthoz."""
    stem = Path(relative_path).stem
    effect, separator, variant = stem.partition("__")
    return effect, variant if separator and variant else "alap"


def _missing_row(relative_path: str, message: str) -> dict[str, Any]:
    """A két export valamelyikéből hiányzó képsor egységes alakja."""
    effect, variant = _effect_and_variant(relative_path)
    return {
        "effekt": effect,
        "valtozat": variant,
        "fajl": relative_path,
        "verdikt": "HIÁNYZIK",
        "atlagos_abszolut_csatornaelteres": None,
        "megjegyzes": message,
    }


def _compare_pair(relative_path: str, original: Path, rendered: Path, threshold: float) -> dict[str, Any]:
    """Egy azonos nevű Picasa/PicasaPy exportot vet össze."""
    effect, variant = _effect_and_variant(relative_path)
    original_image = _read_image(original)
    rendered_image = _read_image(rendered)
    row: dict[str, Any] = {
        "effekt": effect,
        "valtozat": variant,
        "fajl": relative_path,
    }
    if original_image.shape != rendered_image.shape:
        original_height, original_width = original_image.shape[:2]
        rendered_height, rendered_width = rendered_image.shape[:2]
        row.update(
            {
                "verdikt": "ELTÉR",
                "atlagos_abszolut_csatornaelteres": None,
                "megjegyzes": (
                    f"MÉRET {original_width}x{original_height} vs "
                    f"{rendered_width}x{rendered_height}"
                ),
            }
        )
        return row

    # A PNG lehet 16 bites: az int16 a 0..65535 tartomány különbségénél
    # túlcsordulna, és akár teljes fekete/fehér eltérést is egyezésnek mérne.
    difference = np.abs(original_image.astype(np.int32) - rendered_image.astype(np.int32))
    mean_difference = float(difference.mean())
    row.update(
        {
            "verdikt": "ELTÉR" if mean_difference > threshold else "EGYEZIK",
            "atlagos_abszolut_csatornaelteres": round(mean_difference, 3),
            "megjegyzes": "",
        }
    )
    return row


def compare_exports(
    original_dir: Path | str, rendered_dir: Path | str, threshold: float = 3.0
) -> dict[str, Any]:
    """Teljes exportpárt hasonlít össze, csak olvasható bemenetet használva."""
    if (
        not isinstance(threshold, (int, float))
        or isinstance(threshold, bool)
        or not math.isfinite(threshold)
        or threshold < 0
    ):
        raise ValueError("A küszöb nemnegatív szám legyen.")
    original_root = Path(original_dir)
    rendered_root = Path(rendered_dir)
    _validate_directory(original_root, "eredeti Picasa-export")
    _validate_directory(rendered_root, "PicasaPy-export")
    original_paths = _image_paths(original_root)
    rendered_paths = _image_paths(rendered_root)
    rows: list[dict[str, Any]] = []

    for relative_path in sorted(original_paths.keys() | rendered_paths.keys()):
        original = original_paths.get(relative_path)
        rendered = rendered_paths.get(relative_path)
        if original is None:
            rows.append(_missing_row(relative_path, "Az eredeti Picasa-exportból hiányzik"))
        elif rendered is None:
            rows.append(_missing_row(relative_path, "A PicasaPy-exportból hiányzik"))
        else:
            rows.append(_compare_pair(relative_path, original, rendered, float(threshold)))

    rows.sort(key=lambda row: (row["effekt"], row["valtozat"], row["fajl"]))
    effects = []
    for effect in sorted({row["effekt"] for row in rows}):
        effects.append(
            {
                "effekt": effect,
                "valtozatok": [row for row in rows if row["effekt"] == effect],
            }
        )
    summary = {
        "eredeti_fajlok": len(original_paths),
        "picasapy_fajlok": len(rendered_paths),
        "parok": sum(row["verdikt"] != "HIÁNYZIK" for row in rows),
        "egyezik": sum(row["verdikt"] == "EGYEZIK" for row in rows),
        "elter": sum(row["verdikt"] == "ELTÉR" for row in rows),
        "hianyzik": sum(row["verdikt"] == "HIÁNYZIK" for row in rows),
    }
    return {"kuszob": float(threshold), "osszegzes": summary, "effektenkent": effects}


def format_report(report: dict[str, Any]) -> str:
    """A JSON-riport tömör, másolható terminálváltozata."""
    lines = ["Teljes effekt-export összevetés", ""]
    lines.append(f"Eltérési küszöb: {report['kuszob']:.3f}")
    for effect in report["effektenkent"]:
        variants = []
        for row in effect["valtozatok"]:
            if row["atlagos_abszolut_csatornaelteres"] is None:
                value = row["megjegyzes"]
            else:
                value = f"{row['atlagos_abszolut_csatornaelteres']:.3f}"
            variants.append(f"{row['valtozat']}: {value}")
        worst = "ELTÉR" if any(
            row["verdikt"] != "EGYEZIK" for row in effect["valtozatok"]
        ) else "EGYEZIK"
        lines.append(f"{effect['effekt']}: {' · '.join(variants)} — {worst}")
    summary = report["osszegzes"]
    lines.extend(
        [
            "",
            "Összesen: "
            f"{summary['parok']} pár · {summary['egyezik']} egyezik · "
            f"{summary['elter']} eltér · {summary['hianyzik']} hiányzik",
        ]
    )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_dir", type=Path, help="az eredeti Picasa-export")
    parser.add_argument("rendered_dir", type=Path, help="a PicasaPy-export")
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="ennél nagyobb átlagos abszolút csatornaeltérés eltérő (alap: 3)",
    )
    parser.add_argument("--json", type=Path, help="opcionális JSON-riport útvonala")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parancssori belépési pont; a lelet nem hiba, ezért 0-val tér vissza."""
    args = _build_parser().parse_args(argv)
    try:
        report = compare_exports(args.original_dir, args.rendered_dir, args.threshold)
    except ValueError as exc:
        raise SystemExit(f"Hiba: {exc}") from exc
    if args.json is not None:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
