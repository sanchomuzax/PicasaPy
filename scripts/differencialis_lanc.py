#!/usr/bin/env python3
"""Véletlen Picasa-szűrőláncok generálása és összevetése (#6585).

Használat:
  python3 scripts/differencialis_lanc.py futtatas --mag 6585 --db 200 \
    --nevjegyzek /adat/kepmappa__lista.json --kepek /adat/tesztkepek \
    --mintakeszlet kombinalt --ki /adat/6585
  python3 scripts/differencialis_lanc.py general --mag 6585 --db 200 \
    --nevjegyzek /adat/kepmappa__lista.json --kepek /adat/tesztkepek \
    --mintakeszlet kombinalt --ki /adat/6585
  python3 scripts/differencialis_lanc.py sajat --be /adat/6585 \
    --nevjegyzek /adat/kepmappa__lista.json --kepek /adat/tesztkepek
  python3 scripts/differencialis_lanc.py osszevet --be /adat/6585 --eredeti /adat/colab
  python3 scripts/differencialis_lanc.py minimalizal --be /adat/6585 --lanc lanc-0001

A névjegyzék és a képmappa tartalmát fájlnév és bájt-méret szerint párosítja.
Az eredeti exportok elvárt helye:
  <eredeti>/<köteg>/export__<eredeti fájlnév tője>.jpg (a végrehajtó az export/ utat így lapítja)
"""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import re
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from differencialis_lanc_osszevet import (
    _read_rgb,
    _write_results,
    _write_rgb,
    compare_all,
    compare_record,
)

from picasapy.app.effect_params import (
    format_param_values,
    resolve_effect_params,
)
from picasapy.cvimage import read_image_bytes
from picasapy.ini import FilterOp, parse_filters, serialize_filters
from picasapy.ini.filter_registry import canonical_filter_name
from picasapy.lazy_cv2 import cv2
from picasapy.render.chain import apply_filters, can_render_filter
from picasapy.render.registry import FILTER_REGISTRY, one_click_keys

_INI_MAX_BAJT = 20_000
_INI_MAX_SOR = 400
_INI_SZEKCIO_RE = re.compile(
    r"\[(Contacts2|Picasa|[A-Za-z0-9_][A-Za-z0-9_. \-]{0,99})\]"
)
_INI_KULCS_RE = re.compile(r"[A-Za-z0-9_]{1,64}")
_INI_ERTEK_MAX = 2_000
_AZONOSITO_RE = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
_JOB_STEPS = [
    {"var": 10},
    {"var": 10},
    {"var": 10},
    {"var": 10},
    {"kattint": [825, 272]},
    {"var": 3},
    {"billentyu": "ctrl+a"},
    {"var": 3},
    {"billentyu": "ctrl+shift+s"},
    {"var": 5},
    {"kattint": [548, 435]},
    {"var": 1},
    {"kattint": [744, 672]},
    # A végrehajtó egy várakozást legfeljebb 10 mp-re enged, egy feladatban
    # legfeljebb 40 lépés lehet; az export kivárása így 20 × 10 mp.
    *({"var": 10} for _ in range(20)),
]
_RENDERELHETO = tuple(
    name
    for key in FILTER_REGISTRY
    if (name := canonical_filter_name(key)) is not None
    and can_render_filter(name)
)
_EGY_KATTINTASOS = frozenset(one_click_keys())
_GENERALHATO = tuple(
    name
    for name in _RENDERELHETO
    if resolve_effect_params(name, width=800.0, height=800.0)
    or name.casefold() in _EGY_KATTINTASOS
)


def _validate_ini(text: str) -> str:
    """A Colab figyelo_cella.py ini_ellenoriz() szabályának másolata."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("picasa_ini_be: nem üres szöveg kell")
    if len(text.encode("utf-8")) > _INI_MAX_BAJT:
        raise ValueError(f"picasa_ini_be: legfeljebb {_INI_MAX_BAJT} bájt")
    lines = text.replace("\r\n", "\n").split("\n")
    if len(lines) > _INI_MAX_SOR:
        raise ValueError(f"picasa_ini_be: legfeljebb {_INI_MAX_SOR} sor")
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if not line.isprintable() or line != line.strip():
            raise ValueError(f"picasa_ini_be.{number}. sor: tiltott karakter")
        if line.startswith("["):
            if not _INI_SZEKCIO_RE.fullmatch(line) or ".." in line:
                raise ValueError(f"picasa_ini_be.{number}. sor: érvénytelen szakasz")
            continue
        key, equals, value = line.partition("=")
        if (
            not equals
            or not _INI_KULCS_RE.fullmatch(key)
            or len(value) > _INI_ERTEK_MAX
        ):
            raise ValueError(f"picasa_ini_be.{number}. sor: kulcs=érték kell")
    return text.replace("\r\n", "\n").rstrip("\n") + "\n"


def _available_images(
    image_manifest: Path | str, image_dir: Path | str
) -> dict[str, tuple[int, int, int]]:
    """A tulajdonosi névjegyzékből csak a helyben, méretazonosan lévő képeket adja."""
    manifest_path = Path(image_manifest)
    directory = Path(image_dir)
    if not directory.is_dir():
        raise ValueError(f"A képmappa nem található: {directory}")
    try:
        catalog = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"A névjegyzék nem olvasható: {manifest_path}") from exc
    rows = catalog.get("fajlok") if isinstance(catalog, dict) else None
    if not isinstance(rows, list):
        raise ValueError("A névjegyzék fajlok mezője nem lista")

    available: dict[str, tuple[int, int, int]] = {}
    seen_stems: set[str] = set()
    skipped: dict[str, int] = {}

    for row in rows:
        if not isinstance(row, dict):
            skipped["nem szótár rekord"] = skipped.get("nem szótár rekord", 0) + 1
            continue
        name = row.get("nev")
        size = row.get("meret")
        if not isinstance(name, str) or not name:
            skipped["hiányzó vagy nem szöveges név"] = (
                skipped.get("hiányzó vagy nem szöveges név", 0) + 1
            )
            continue
        if (
            Path(name).name != name
            or "/" in name
            or "\\" in name
            or ".." in name
            or not _INI_SZEKCIO_RE.fullmatch(f"[{name}]")
        ):
            skipped["érvénytelen fájlnév"] = skipped.get("érvénytelen fájlnév", 0) + 1
            continue
        if Path(name).suffix.casefold() not in _IMAGE_EXTENSIONS:
            skipped["nem támogatott kiterjesztés"] = (
                skipped.get("nem támogatott kiterjesztés", 0) + 1
            )
            continue
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            skipped["érvénytelen méret mező"] = (
                skipped.get("érvénytelen méret mező", 0) + 1
            )
            continue

        stem = Path(name).stem.casefold()
        if stem in seen_stems or name in available:
            skipped["ismétlődő vagy ütköző fájlnévtörzs"] = (
                skipped.get("ismétlődő vagy ütköző fájlnévtörzs", 0) + 1
            )
            continue

        image_path = directory / name
        try:
            if not image_path.is_file():
                skipped["hiányzó fájl a lemezen"] = (
                    skipped.get("hiányzó fájl a lemezen", 0) + 1
                )
                continue
            if image_path.stat().st_size != size:
                skipped["méreteltérés a lemezen"] = (
                    skipped.get("méreteltérés a lemezen", 0) + 1
                )
                continue
            payload = read_image_bytes(image_path)
            image = None if payload is None else cv2.imdecode(
                payload, cv2.IMREAD_COLOR
            )
            if image is not None and image.ndim >= 2:
                available[name] = (size, int(image.shape[1]), int(image.shape[0]))
                seen_stems.add(stem)
            else:
                skipped["nem dekódolható kép"] = (
                    skipped.get("nem dekódolható kép", 0) + 1
                )
        except OSError:
            skipped["olvasási hiba a lemezen"] = (
                skipped.get("olvasási hiba a lemezen", 0) + 1
            )
            continue

    if skipped:
        total = sum(skipped.values())
        sys.stderr.write(f"Kihagyott névjegyzék-tételek ({total} db):\n")
        for reason, count in sorted(skipped.items()):
            sys.stderr.write(f"  - {reason}: {count} db\n")

    return available


def _random_control_value(rng: random.Random, param) -> Any:
    """Egy effektvezérlő engedélyezett tartományából mintáz értéket."""
    if param.kind == "color":
        return f"#{rng.randrange(0x1000000):06x}"
    if param.kind == "checkbox":
        return rng.choice((False, True))
    return rng.uniform(param.minimum, param.maximum)


def _random_filter(rng: random.Random, width: int, height: int) -> str:
    name = rng.choice(_GENERALHATO)
    params = resolve_effect_params(name, width=float(width), height=float(height))
    values = tuple(_random_control_value(rng, param) for param in params)
    serialized = format_param_values(values, params, effect=name)
    return serialize_filters((FilterOp(name, ("1", *serialized)),))


def generate_chains(
    seed: int,
    count: int = 200,
    image_names: tuple[str, ...] = (),
    image_dimensions: dict[str, tuple[int, int]] | None = None,
) -> list[dict[str, Any]]:
    """Determinista, 2–6 renderelhető effektből láncokat készít.

    Egy köteg minden ismert bemeneti képhez legfeljebb egy láncot rendel.
    A hívó a névjegyzék és a helyi képmappa metszetét adja meg bemenetként.
    """
    if count < 1:
        raise ValueError("A láncszám legalább 1 legyen")
    if not image_names or len(set(image_names)) != len(image_names):
        raise ValueError("Legalább egy, ismétlés nélküli tesztképnév kell")
    if any(
        Path(name).name != name
        or "/" in name
        or "\\" in name
        or ".." in name
        or Path(name).suffix.casefold() not in _IMAGE_EXTENSIONS
        or not _INI_SZEKCIO_RE.fullmatch(f"[{name}]")
        for name in image_names
    ):
        raise ValueError("Csak egyszerű képnevek adhatók meg útvonal nélkül")
    if not _RENDERELHETO:
        raise RuntimeError("Nincs renderelhető szűrő a #6582 regiszterben")

    rng = random.Random(seed)
    dimensions = image_dimensions or {}
    records: list[dict[str, Any]] = []
    for index in range(count):
        batch_number, image_index = divmod(index, len(image_names))
        image_name = image_names[image_index]
        width, height = dimensions.get(image_name, (800, 800))
        operation_count = rng.randint(2, 6)
        filters_value = "".join(
            _random_filter(rng, width, height) for _ in range(operation_count)
        )
        records.append(
            {
                "azonosito": f"lanc-{index + 1:04d}",
                "koteg": f"koteg-{batch_number + 1:03d}",
                "kep": image_name,
                "filters": filters_value,
            }
        )
    return records


def _ini_for_records(records: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    seen_stems: set[str] = set()
    for record in records:
        image_name = record["kep"]
        stem = Path(image_name).stem.casefold()
        if stem in seen_stems:
            raise ValueError(f"A kötegben ismétlődik a kép-névtörzs: {image_name}")
        seen_stems.add(stem)
        lines.extend((f"[{image_name}]", f"filters={record['filters']}", ""))
    if not lines:
        raise ValueError("Üres köteg nem írható ki")
    return _validate_ini("\n".join(lines))


def _ini_fits(records: list[dict[str, Any]]) -> bool:
    lines: list[str] = []
    for record in records:
        lines.extend((f"[{record['kep']}]", f"filters={record['filters']}", ""))
    text = "\n".join(lines)
    return (
        len(text.encode("utf-8")) <= _INI_MAX_BAJT
        and len(text.replace("\r\n", "\n").split("\n")) <= _INI_MAX_SOR
    )


MINTAKESZLETEK = ("arcos", "kombinalt", "idorend")


def _capture_job(
    batch_name: str, ini_text: str, mintakeszlet: str | None = None
) -> dict[str, Any]:
    job = {
        "v": 3,
        "tipus": "ui_capture",
        "cel": f"PicasaPy #6585: véletlen szűrőláncok exportja ({batch_name})",
        "indulas": "alapallapot",
        "picasa_ini_be": ini_text,
        "kimenet": ["allapot", "export"],
        "keret": {"perc": 30},
        "lepesek": json.loads(json.dumps(_JOB_STEPS)),
    }
    if mintakeszlet is not None:
        if mintakeszlet not in MINTAKESZLETEK:
            raise ValueError(f"Ismeretlen mintakészlet: {mintakeszlet!r}")
        job["mintakeszlet"] = mintakeszlet
    return job


def _write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def generalize(
    output_dir: Path | str,
    seed: int,
    count: int = 200,
    *,
    image_manifest: Path | str,
    image_dir: Path | str,
    mintakeszlet: str,
) -> list[dict[str, Any]]:
    """A képmappához illesztett, korlátos INI-ket és v3 Colab-jobokat ír."""
    if mintakeszlet not in MINTAKESZLETEK:
        raise ValueError(f"Ismeretlen mintakészlet: {mintakeszlet!r}")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    for pattern in ("koteg-*.ini", "koteg-*.job.json", "minimal-*", "lancok.json"):
        for path in output.glob(pattern):
            if path.is_file():
                path.unlink()

    available = _available_images(image_manifest, image_dir)
    if not available:
        raise ValueError("A névjegyzékben nincs helyben meglévő, méretazonos támogatott kép")
    records = generate_chains(
        seed=seed,
        count=count,
        image_names=tuple(available),
        image_dimensions={
            name: (metadata[1], metadata[2])
            for name, metadata in available.items()
        },
    )
    packed_batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_stems: set[str] = set()
    for record in records:
        stem = Path(record["kep"]).stem.casefold()
        would_repeat = stem in current_stems
        would_overflow = bool(current) and not _ini_fits([*current, record])
        if would_repeat or would_overflow:
            packed_batches.append(current)
            current = []
            current_stems = set()
        if not _ini_fits([*current, record]):
            raise ValueError("Egy szűrőlánc önmagában túllépi a Colab INI-korlátját")
        current.append(record)
        current_stems.add(stem)
    if current:
        packed_batches.append(current)

    for index, batch_records in enumerate(packed_batches, 1):
        batch_name = f"koteg-{index:03d}"
        for record in batch_records:
            record["koteg"] = batch_name
            if mintakeszlet is not None:
                record["mintakeszlet"] = mintakeszlet
        text = _ini_for_records(batch_records)
        (output / f"{batch_name}.ini").write_text(text, encoding="utf-8", newline="\n")
        _write_json(output / f"{batch_name}.job.json", _capture_job(batch_name, text, mintakeszlet))
    _write_json(
        output / "lancok.json",
        {
            "kepek": sorted(available.keys()),
            "lancok": records,
        },
    )
    return records


def _load_records(batch_dir: Path | str) -> list[dict[str, Any]]:
    root = Path(batch_dir)
    manifest = root / "lancok.json"
    if not manifest.is_file():
        raise ValueError(f"Nem található a láncjegyzék: {manifest}")
    content = json.loads(manifest.read_text(encoding="utf-8"))
    if isinstance(content, dict):
        records = list(content.get("lancok", []))
    elif isinstance(content, list):
        records = list(content)
    else:
        raise ValueError("A lancok.json gyökere nem lista vagy szótár")
    for candidates_path in sorted(root.glob("minimal-*.json")):
        try:
            candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
            if isinstance(candidates, list):
                records.extend(candidates)
        except (OSError, json.JSONDecodeError):
            continue
    return records


def run_local(
    batch_dir: Path | str,
    *,
    image_manifest: Path | str,
    image_dir: Path | str,
) -> list[dict[str, Any]]:
    """A helyi képpéldányokon meghívja az apply_filters renderláncot."""
    root = Path(batch_dir)
    records = _load_records(root)
    available = _available_images(image_manifest, image_dir)
    input_dir = Path(image_dir)
    output_dir = root / "sajat"
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for record in records:
        result = {**record, "allapot": "kész", "kimenet": None, "kihagyott": []}
        source_path = input_dir / record["kep"] if record["kep"] in available else None
        if source_path is None:
            result["allapot"] = "hiányzik vagy eltér a katalógusbeli kép"
            for ext in (".png", ".jpg"):
                old_file = output_dir / f"{record['azonosito']}{ext}"
                if old_file.is_file():
                    old_file.unlink()
            results.append(result)
            continue
        image = _read_rgb(source_path)
        report = apply_filters(image, parse_filters(record["filters"]))
        output_path = output_dir / f"{record['azonosito']}.png"
        _write_rgb(output_path, report.image)
        result["kimenet"] = output_path.relative_to(root).as_posix()
        result["kihagyott"] = list(report.skipped)
        if report.skipped:
            result["allapot"] = "szűrő kihagyva"
        results.append(result)
    _write_json(output_dir / "futtatas.json", results)
    return results


def run_campaign(
    output_dir: Path | str,
    seed: int,
    count: int = 200,
    *,
    image_manifest: Path | str,
    image_dir: Path | str,
    mintakeszlet: str,
    original_dir: Path | str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]] | None]:
    """Egy hívásból előkészíti a Colab-kötegeket, renderel helyben, és ha van eredeti export, összevet."""
    root = Path(output_dir)
    records = generalize(
        root,
        seed=seed,
        count=count,
        image_manifest=image_manifest,
        image_dir=image_dir,
        mintakeszlet=mintakeszlet,
    )
    local_results = run_local(
        root, image_manifest=image_manifest, image_dir=image_dir
    )
    comparisons = None
    if original_dir is not None:
        comparisons = [
            compare_record(record, root / "sajat", original_dir)
            for record in records
        ]
        _write_results(root, comparisons)
    return records, local_results, comparisons


def _control_values_from_operation(op: FilterOp, params) -> list[Any] | None:
    values = list(op.params[1:])
    if len(values) != len(params):
        return None
    restored: list[Any] = []
    try:
        for raw, param in zip(values, params, strict=True):
            if param.kind == "color":
                restored.append("#" + raw[-6:])
            elif param.kind == "checkbox":
                restored.append(raw == "1")
            elif param.max_formula is not None:
                normalized = float(raw) / 100.0
                restored.append(
                    param.minimum + normalized * (param.maximum - param.minimum)
                )
            else:
                restored.append(float(raw))
    except (TypeError, ValueError):
        return None
    return restored


def _replace_operation_parameter(
    op: FilterOp, params, changed_index: int, value: Any
) -> FilterOp | None:
    values = _control_values_from_operation(op, params)
    if values is None:
        return None
    values[changed_index] = value
    serialized = format_param_values(values, params, effect=op.name)
    return FilterOp(op.name, ("1", *serialized))


def minimal_candidates(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Egy réteggel rövidebb láncokat, majd paraméterérték-jelölteket ad."""
    operations = parse_filters(record["filters"])
    candidates: list[tuple[FilterOp, ...]] = []
    if len(operations) > 1:
        for index in range(len(operations)):
            candidates.append(operations[:index] + operations[index + 1 :])
    elif operations:
        op = operations[0]
        params = resolve_effect_params(op.name, width=800.0, height=800.0)
        current_values = _control_values_from_operation(op, params)
        if current_values is not None:
            for param_index, param in enumerate(params):
                if param.kind == "color":
                    values = ("#000000", "#808080", "#ffffff")
                elif param.kind == "checkbox":
                    values = (False, True)
                else:
                    midpoint = (param.minimum + param.maximum) / 2.0
                    values = (param.minimum, midpoint, param.maximum)
                for value in values:
                    replacement = _replace_operation_parameter(
                        op, params, param_index, value
                    )
                    if replacement is not None and replacement != op:
                        candidates.append((replacement,))

    distinct: dict[str, tuple[FilterOp, ...]] = {}
    for candidate in candidates:
        filters_value = serialize_filters(candidate)
        distinct.setdefault(filters_value, candidate)
    records = []
    for index, filters_value in enumerate(distinct, 1):
        candidate_id = f"minimal-{record['azonosito']}-{index:03d}"
        records.append(
            {
                "azonosito": candidate_id,
                "koteg": candidate_id,
                "kep": record["kep"],
                "filters": filters_value,
                "elozo_lanc": record["azonosito"],
                **({"mintakeszlet": record["mintakeszlet"]} if "mintakeszlet" in record else {}),
            }
        )
    return records


def minimize(batch_dir: Path | str, chain_id: str) -> list[dict[str, Any]]:
    """Futtatható ini-jelölteket ír, hogy a hívó Colabban újramérhesse."""
    if not _AZONOSITO_RE.fullmatch(chain_id):
        raise ValueError(f"Érvénytelen láncazonosító: {chain_id!r}")
    root = Path(batch_dir)
    matching = [record for record in _load_records(root) if record["azonosito"] == chain_id]
    if not matching:
        raise ValueError(f"Nem található lánc: {chain_id}")
    candidates = minimal_candidates(matching[0])
    for candidate in candidates:
        ini_text = _ini_for_records([candidate])
        (root / f"{candidate['azonosito']}.ini").write_text(
            ini_text, encoding="utf-8", newline="\n"
        )
        _write_json(
            root / f"{candidate['azonosito']}.job.json",
            _capture_job(candidate["koteg"], ini_text, candidate.get("mintakeszlet")),
        )
    _write_json(root / f"minimal-{chain_id}.json", candidates)
    return candidates


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("general", help="véletlen chains és ini-kötegek")
    generate.add_argument("--mag", type=int, required=True)
    generate.add_argument("--db", type=int, default=200)
    generate.add_argument("--nevjegyzek", type=Path, required=True)
    generate.add_argument("--kepek", type=Path, required=True)
    generate.add_argument("--ki", type=Path, required=True)
    generate.add_argument(
        "--mintakeszlet",
        choices=MINTAKESZLETEK,
        required=True,
        help="a végrehajtó mintakészlete, amelynek képeire a láncok vonatkoznak",
    )

    campaign = subparsers.add_parser(
        "futtatas",
        help="Colab-kötegek generálása, helyi render és opcionális összevetés egy menetben",
    )
    campaign.add_argument("--mag", type=int, required=True)
    campaign.add_argument("--db", type=int, default=200)
    campaign.add_argument("--nevjegyzek", type=Path, required=True)
    campaign.add_argument("--kepek", type=Path, required=True)
    campaign.add_argument("--mintakeszlet", choices=MINTAKESZLETEK, required=True)
    campaign.add_argument("--ki", type=Path, required=True)
    campaign.add_argument("--eredeti", type=Path)

    local = subparsers.add_parser("sajat", help="helyi renderelés apply_filters-szel")
    local.add_argument("--be", type=Path, required=True)
    local.add_argument("--nevjegyzek", type=Path, required=True)
    local.add_argument("--kepek", type=Path, required=True)

    compare = subparsers.add_parser("osszevet", help="Picasa-exportok összevetése")
    compare.add_argument("--be", type=Path, required=True)
    compare.add_argument("--eredeti", type=Path, required=True)

    minimize_parser = subparsers.add_parser(
        "minimalizal", help="rövidítő és paraméterjelöltek előállítása"
    )
    minimize_parser.add_argument("--be", type=Path, required=True)
    minimize_parser.add_argument("--lanc", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "general":
            records = generalize(
                args.ki,
                seed=args.mag,
                count=args.db,
                image_manifest=args.nevjegyzek,
                image_dir=args.kepek,
                mintakeszlet=args.mintakeszlet,
            )
            batch_count = len({record["koteg"] for record in records})
            print(
                f"{len(records)} lánc, {batch_count} köteg; "
                f"mag={args.mag}; fájlok: {args.ki}"
            )
        elif args.command == "futtatas":
            records, local_results, comparisons = run_campaign(
                args.ki,
                seed=args.mag,
                count=args.db,
                image_manifest=args.nevjegyzek,
                image_dir=args.kepek,
                mintakeszlet=args.mintakeszlet,
                original_dir=args.eredeti,
            )
            initial_ids = {record["azonosito"] for record in records}
            ready = sum(
                row["azonosito"] in initial_ids and row["allapot"] == "kész"
                for row in local_results
            )
            batch_count = len({record["koteg"] for record in records})
            print(
                f"{len(records)} lánc, {batch_count} Colab-köteg; mag={args.mag}; "
                f"helyben kész: {ready}/{len(records)}; fájlok: {args.ki}"
            )
            if comparisons is None:
                print(
                    "Az eredeti Picasa-exportok után ismételd meg --eredeti <mappa> "
                    "megadásával az összevetési táblához."
                )
            else:
                matched = sum(row["egyezes"] == "egyezik" for row in comparisons)
                different = sum(row["egyezes"] == "eltér" for row in comparisons)
                local_error = sum(row["egyezes"] == "helyi hiba" for row in comparisons)
                corrupt = sum(row["egyezes"] == "hibás export" for row in comparisons)
                missing = sum(row["egyezes"] == "hiányzik" for row in comparisons)
                print(
                    f"Összevetés: {matched}/{len(comparisons)} egyezik, "
                    f"{different} eltér, {local_error} helyi hiba, {corrupt} hibás export, "
                    f"{missing} hiányzik; eredmeny.md és eredmeny.csv: {args.ki}"
                )
        elif args.command == "sajat":
            results = run_local(
                args.be,
                image_manifest=args.nevjegyzek,
                image_dir=args.kepek,
            )
            ready = sum(row["allapot"] == "kész" for row in results)
            missing = len(results) - ready
            print(f"Helyben renderelt: {ready}; kihagyott/hiányzó: {missing}")
            for row in results:
                if row["allapot"] != "kész":
                    print(f"{row['azonosito']}: {row['kep']} — {row['allapot']}")
        elif args.command == "osszevet":
            rows = compare_all(args.be, args.eredeti)
            matched = sum(row["egyezes"] == "egyezik" for row in rows)
            different = sum(row["egyezes"] == "eltér" for row in rows)
            local_error = sum(row["egyezes"] == "helyi hiba" for row in rows)
            corrupt = sum(row["egyezes"] == "hibás export" for row in rows)
            missing = sum(row["egyezes"] == "hiányzik" for row in rows)
            print(
                f"{len(rows)} sor: egyezik={matched}, eltér={different}, "
                f"helyi hiba={local_error}, hibás export={corrupt}, "
                f"hiányzik={missing}; eredmeny.md és eredmeny.csv: {args.be}"
            )
        else:
            candidates = minimize(args.be, args.lanc)
            print(
                f"{len(candidates)} jelölt; külön ini/köteg mindegyikhez: "
                f"{args.be}/minimal-{args.lanc}*.ini"
            )
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
