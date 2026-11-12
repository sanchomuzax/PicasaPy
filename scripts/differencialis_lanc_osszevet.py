#!/usr/bin/env python3
"""Differenciális szűrőláncok képi összevetése és kiértékelése (#6585)."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from picasapy.cvimage import read_image_bytes  # noqa: E402
from picasapy.ini import parse_filters  # noqa: E402
from picasapy.lazy_cv2 import cv2  # noqa: E402

# A CRT-vetést és a globális állapotot a differenciális láncok specifikációja
# (#6822) dokumentálja; a PicnikGrain rögzített maggal dolgozik.
_VELETLENFUGGO_SZUROK = frozenset({"grain", "grain2", "triple3"})


def _load_golden_comparator():
    """Betölti a meglévő SSIM/ΔE- és küszöbmegvalósítást."""
    path = _REPO_ROOT / "tools" / "golden" / "compare_render.py"
    spec = importlib.util.spec_from_file_location("picasapy_golden_compare", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nem tölthető be a golden-összevető: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


_GOLDEN = _load_golden_comparator()


def _read_rgb(path: Path) -> np.ndarray:
    payload = read_image_bytes(path)
    image = None if payload is None else cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"A kép nem olvasható: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _write_rgb(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    extension = path.suffix.casefold()
    if extension not in {".jpg", ".jpeg", ".png"}:
        raise ValueError(f"Nem támogatott kimeneti képformátum: {path.suffix}")
    params = [cv2.IMWRITE_JPEG_QUALITY, 95] if extension in {".jpg", ".jpeg"} else []
    success, encoded = cv2.imencode(
        extension, cv2.cvtColor(image, cv2.COLOR_RGB2BGR), params
    )
    if not success:
        raise ValueError(f"A renderelt kép nem kódolható: {path}")
    path.write_bytes(encoded.tobytes())


def _original_image_path(record: dict[str, Any], root: Path) -> Path:
    filename = f"export__{Path(record['kep']).stem}.jpg"
    batch_dir = root / record["koteg"]
    direct = batch_dir / filename
    if direct.is_file():
        return direct
    nested = sorted(batch_dir.rglob(filename)) if batch_dir.is_dir() else []
    return nested[0] if len(nested) == 1 else direct


def _get_skipped_filters(record: dict[str, Any], own_root: Path | str) -> list[str]:
    """Kiolvassa a kihagyott szűrők listáját a rekordból vagy a futtatas.json-ból."""
    if "kihagyott" in record and isinstance(record["kihagyott"], list):
        return [str(item) for item in record["kihagyott"]]
    futtatas_path = Path(own_root) / "futtatas.json"
    if futtatas_path.is_file():
        try:
            data = json.loads(futtatas_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if (
                        isinstance(item, dict)
                        and item.get("azonosito") == record.get("azonosito")
                        and isinstance(item.get("kihagyott"), list)
                    ):
                        return [str(s) for s in item["kihagyott"]]
        except (OSError, json.JSONDecodeError):
            pass
    return []


def compare_record(
    record: dict[str, Any], own_root: Path | str, original_root: Path | str
) -> dict[str, Any]:
    """Egy PicasaPy/Picasa exportpárt a golden küszöbeivel mér össze."""
    own_path = Path(own_root)
    local_path = own_path / f"{record['azonosito']}.png"
    if not local_path.is_file() and (own_path / f"{record['azonosito']}.jpg").is_file():
        local_path = own_path / f"{record['azonosito']}.jpg"
    original_path = _original_image_path(record, Path(original_root))
    row: dict[str, Any] = {
        "azonosito": record["azonosito"],
        "koteg": record["koteg"],
        "kep": record["kep"],
        "filters": record["filters"],
        "veletlenfuggo": "igen" if any(
            op.name.casefold() in _VELETLENFUGGO_SZUROK
            for op in parse_filters(record["filters"])
        ) else "nem",
        "ssim": None,
        "delta_e": None,
        "egyezes": "hiányzik",
        "golden_itelet": "hiányzik",
        "megjegyzes": "",
    }

    skipped = _get_skipped_filters(record, own_root)
    if skipped:
        skipped_str = ", ".join(skipped)
        row["egyezes"] = "helyi hiba"
        row["golden_itelet"] = f"helyi hiba ({skipped_str})"
        row["megjegyzes"] = f"Kihagyott szűrő: {skipped_str}"
        return row

    missing = [str(path) for path in (local_path, original_path) if not path.is_file()]
    if missing:
        row["megjegyzes"] = "Hiányzó kimenet: " + ", ".join(missing)
        return row

    try:
        own_image = _read_rgb(local_path)
        original_image = _read_rgb(original_path)
    except Exception as exc:
        row["egyezes"] = "hibás export"
        row["golden_itelet"] = "hibás export"
        row["megjegyzes"] = f"Sérült vagy olvashatatlan kép: {exc}"
        return row

    # #6585: a saját képet a Picasa-export JPEG-beállításaival (mintavételezés,
    # kvantálótáblák) kódoljuk újra; a 4:2:0 színfelbontás különben kb. 1 ΔE-s
    # hamis eltérést adott (mérve, lanc-0006: 4,459 helyett 0,672)
    own_image = _GOLDEN.encode_like_reference(own_image, original_path)
    thresholds = _GOLDEN.Thresholds()
    verdict, metrics, note = _GOLDEN.compare_images(
        own_image, original_image, thresholds
    )
    row.update(
        {
            "ssim": metrics.get("ssim"),
            "delta_e": metrics.get("delta_e_mean"),
            "egyezes": "egyezik" if verdict in {"pixelhű", "közelítés"} else "eltér",
            "golden_itelet": verdict,
            "megjegyzes": note,
        }
    )
    return row


def _write_results(output_dir: Path, rows: list[dict[str, Any]]) -> None:
    csv_path = output_dir / "eredmeny.csv"
    fields = (
        "azonosito",
        "koteg",
        "kep",
        "filters",
        "veletlenfuggo",
        "ssim",
        "delta_e",
        "egyezes",
        "golden_itelet",
        "megjegyzes",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    matched = sum(row["egyezes"] == "egyezik" for row in rows)
    different = sum(row["egyezes"] == "eltér" for row in rows)
    local_error = sum(row["egyezes"] == "helyi hiba" for row in rows)
    corrupt = sum(row["egyezes"] == "hibás export" for row in rows)
    missing = sum(row["egyezes"] == "hiányzik" for row in rows)
    random_rows = [row for row in rows if row["veletlenfuggo"] == "igen"]
    random_matched = sum(row["egyezes"] == "egyezik" for row in random_rows)
    random_different = sum(row["egyezes"] == "eltér" for row in random_rows)
    stable_rows = [row for row in rows if row["veletlenfuggo"] == "nem"]
    stable_matched = sum(row["egyezes"] == "egyezik" for row in stable_rows)
    stable_measured = sum(row["egyezes"] in {"egyezik", "eltér"} for row in stable_rows)
    stable_rate = (
        f"{stable_matched}/{stable_measured} "
        f"({100 * stable_matched / stable_measured:.1f}%)".replace(".", ",")
        if stable_measured else "nincs értékelhető mérés"
    )

    lines = [
        "# Differenciális szűrőlánc-összevetés",
        "",
        "Mérce: `tools/golden/compare_render.py`, `Thresholds()` és `compare_images()`.",
        "Az `egyezik` a meglévő `pixelhű` vagy `közelítés` ítéletet jelenti.",
        "",
        f"Összesen: {len(rows)} | Egyezik: {matched} | Eltér: {different} | "
        f"Helyi hiba: {local_error} | Hibás export: {corrupt} | Hiányzik: {missing}",
        f"Véletlenállapot-függő: {len(random_rows)} | Egyezik: {random_matched} | "
        f"Eltér: {random_different}",
        f"Véletlenállapot-függők nélkül: {stable_rate}",
        "Az egyezési arány csak az értékelhető, egyező vagy eltérő méréseket számolja.",
        "",
        "| Lánc | Köteg | Kép | filters= | Véletlenállapot-függő | SSIM | ΔE átlag | Eredmény |",
        "|---|---|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        ssim = "—" if row["ssim"] is None else f"{row['ssim']:.5f}"
        delta_e = "—" if row["delta_e"] is None else f"{row['delta_e']:.3f}"
        lines.append(
            f"| {row['azonosito']} | {row['koteg']} | {row['kep']} | "
            f"`{row['filters']}` | {row['veletlenfuggo']} | {ssim} | {delta_e} | {row['egyezes']} |"
        )
    (output_dir / "eredmeny.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_all(batch_dir: Path | str, original_dir: Path | str) -> list[dict[str, Any]]:
    """Minden kezdeti és minimalizáló jelöltet riportba hasonlít."""
    root = Path(batch_dir)
    manifest = root / "lancok.json"
    if not manifest.is_file():
        raise ValueError(f"Nem található a láncjegyzék: {manifest}")
    content = json.loads(manifest.read_text(encoding="utf-8"))
    records = content.get("lancok", []) if isinstance(content, dict) else content
    if not isinstance(records, list):
        raise ValueError("A lancok.json érvénytelen formátumú")
    records = list(records)
    for candidates_path in sorted(root.glob("minimal-*.json")):
        try:
            candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
            if isinstance(candidates, list):
                records.extend(candidates)
        except (OSError, json.JSONDecodeError):
            continue
    rows = [compare_record(record, root / "sajat", original_dir) for record in records]
    _write_results(root, rows)
    return rows
