#!/usr/bin/env python3
"""Golden-összehasonlító harness — PicasaPy-render vs Picasa-export (#115).

A PicasaPy szűrő-renderjét (`picasapy.render.apply_filters`) méri a valódi
Picasa 3.9-exportok („goldenek") ellen: SSIM, ΔE (CIE76) és toleranciás
pixel-diff alapján soronkénti ítéletet ad (pixelhű / közelítés / eltér),
állítható küszöbökkel, JSON- és ember-olvasható riporttal.

Futtatás a FEJLESZTŐI GÉPEN (ahol a golden-kitek élnek):

  # Teljes kit (a make_golden_kit.py által generált szerkezet:
  #   <kit>/<mappa>/<kép>__<variáns>.jpg + .picasa.ini,
  #   exportok: <kit>/export/<mappa>/<kép>__<variáns>.jpg):
  python3 tools/golden/compare_render.py kit research/golden-kit-result \
      --luts research/golden-analysis --json riport.json

  # Egyetlen pár (eredeti kép + filters-lánc + Picasa-export):
  python3 tools/golden/compare_render.py pair eredeti.jpg golden.jpg \
      --filters "fill=1,0.500000;bw=1;" --json riport.json

Kilépési kód: 0, ha nincs „eltér" sor; egyébként 1 (CI-barát).

Opcionális mért LUT-ok (`--luts <könyvtár>`): ha a fejlesztői gépen jelen van
a `research/golden-analysis/luts3.json` (ld. `analyze_goldens3.py`), a mért
2D fill-LUT és a highlights/shadows/színhő LUT-ok a beépített közelítések
HELYETT futnak (fill, finetune/finetune2). A fájlok hiánya tiszta kihagyás
— sosem hiba. A repóban ezek az adatok NINCSENEK (gitignore).

Küszöbök (CLI-ből állíthatók, ld. --help):
  pixelhű:   max|Δ| ≤ pixel-tol ÉS a tolerancián túli pixelek aránya ≤ frac-tol
  közelítés: SSIM ≥ ssim-min ÉS átlag ΔE ≤ de-mean-max
  eltér:     minden más (és a méret-eltérés / hiányzó export is jelzett)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

# A tools/ nincs a pythonpath-on — a repo src/-ét kézzel vesszük fel, hogy a
# szkript közvetlenül (python3 tools/golden/compare_render.py) is fusson.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from picasapy.ini.filters import FilterOp, parse_filters  # noqa: E402
from picasapy.render import apply_filters  # noqa: E402
from picasapy.render.curves import apply_lut, lut_ramp, validate_image  # noqa: E402
from picasapy.render.tone import apply_neutral_pipette, parse_neutral_argb  # noqa: E402

#: Az ítéletek rögzített sorrendje (súlyosság szerint).
VERDICTS = ("pixelhű", "közelítés", "eltér", "hiányzik")


# --------------------------------------------------------------- metrikák


def _ensure_same_shape(first: np.ndarray, second: np.ndarray) -> None:
    """Két kép alak-egyezésének ellenőrzése — eltérésnél ValueError."""
    validate_image(first)
    validate_image(second)
    if first.shape != second.shape:
        raise ValueError(
            f"A képek mérete eltér: {first.shape} vs {second.shape}"
        )


def _luma(image: np.ndarray) -> np.ndarray:
    """Rec.601 luma float64-ben (az SSIM szürke alapja)."""
    rgb = image.astype(np.float64)
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def ssim(first: np.ndarray, second: np.ndarray) -> float:
    """Átlagos SSIM a két kép lumáján (Wang et al., 11×11 Gauss, σ=1,5).

    Csak numpy+OpenCV (meglévő függőségek) — nincs scikit-image igény.
    """
    _ensure_same_shape(first, second)
    x = _luma(first)
    y = _luma(second)
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    def blur(img: np.ndarray) -> np.ndarray:
        return cv2.GaussianBlur(img, (11, 11), 1.5)

    mu_x = blur(x)
    mu_y = blur(y)
    mu_xx = mu_x * mu_x
    mu_yy = mu_y * mu_y
    mu_xy = mu_x * mu_y
    sigma_xx = blur(x * x) - mu_xx
    sigma_yy = blur(y * y) - mu_yy
    sigma_xy = blur(x * y) - mu_xy
    numerator = (2.0 * mu_xy + c1) * (2.0 * sigma_xy + c2)
    denominator = (mu_xx + mu_yy + c1) * (sigma_xx + sigma_yy + c2)
    return float((numerator / denominator).mean())


def _srgb_to_lab(image: np.ndarray) -> np.ndarray:
    """sRGB (uint8, RGB) → CIE Lab (D65), float64 — a ΔE alapja."""
    rgb = image.astype(np.float64) / 255.0
    # sRGB → lineáris
    linear = np.where(
        rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4
    )
    # lineáris RGB → XYZ (D65)
    matrix = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    xyz = linear @ matrix.T
    # XYZ → Lab (D65 fehérpont)
    white = np.array([0.95047, 1.0, 1.08883])
    ratio = xyz / white
    epsilon = 216.0 / 24389.0
    kappa = 24389.0 / 27.0
    f = np.where(
        ratio > epsilon, np.cbrt(ratio), (kappa * ratio + 16.0) / 116.0
    )
    lab = np.empty_like(f)
    lab[..., 0] = 116.0 * f[..., 1] - 16.0
    lab[..., 1] = 500.0 * (f[..., 0] - f[..., 1])
    lab[..., 2] = 200.0 * (f[..., 1] - f[..., 2])
    return lab


def delta_e_cie76(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """Pixelenkénti ΔE (CIE76) a két RGB uint8 kép között."""
    _ensure_same_shape(first, second)
    diff = _srgb_to_lab(first) - _srgb_to_lab(second)
    return np.sqrt((diff * diff).sum(axis=-1))


def pixel_diff_stats(
    first: np.ndarray, second: np.ndarray, tolerance: int
) -> dict[str, float]:
    """Toleranciás pixel-diff: max/átlag |Δ| és a tűrésen túli pixelek aránya."""
    _ensure_same_shape(first, second)
    if tolerance < 0:
        raise ValueError(f"A tolerancia nem lehet negatív: {tolerance}")
    diff = np.abs(first.astype(np.int16) - second.astype(np.int16))
    per_pixel = diff.max(axis=-1)  # pixelenként a legrosszabb csatorna
    return {
        "max_diff": int(per_pixel.max()),
        "mean_diff": float(diff.mean()),
        "over_tolerance_ratio": float((per_pixel > tolerance).mean()),
    }


# --------------------------------------------------------------- küszöbök


@dataclass(frozen=True)
class Thresholds:
    """Az ítélet-küszöbök (CLI-ből felülírhatók).

    pixel_tol / frac_tol: a „pixelhű" határa (JPEG-újratömörítési alapzajt
    engedve); ssim_min / de_mean_max: a még elfogadható „közelítés" határa.
    """

    pixel_tol: int = 1
    frac_tol: float = 0.002
    ssim_min: float = 0.98
    de_mean_max: float = 2.0

    def as_dict(self) -> dict[str, float]:
        return {
            "pixel_tol": self.pixel_tol,
            "frac_tol": self.frac_tol,
            "ssim_min": self.ssim_min,
            "de_mean_max": self.de_mean_max,
        }


def verdict(metrics: dict[str, float], thresholds: Thresholds) -> str:
    """Egyetlen összehasonlítás ítélete a metrikákból."""
    if (
        metrics["max_diff"] <= thresholds.pixel_tol
        or metrics["over_tolerance_ratio"] <= thresholds.frac_tol
    ):
        return "pixelhű"
    if (
        metrics["ssim"] >= thresholds.ssim_min
        and metrics["delta_e_mean"] <= thresholds.de_mean_max
    ):
        return "közelítés"
    return "eltér"


# --------------------------------------------------------------- LUT-réteg


@dataclass(frozen=True)
class GoldenLuts:
    """A fejlesztői gépen mért LUT-ok (luts3.json) — mind opcionális.

    fill2d: {s: 256 elemű görbe} — fill / finetune2 p1;
    hs: {"h010".."h080", "s010".."s080": 256 elemű görbe} — highlights/shadows;
    temp: {"tm100".."tp100": [ΔB, ΔG, ΔR]} — színhő-csúszka (cv2 BGR mérés).
    """

    fill2d: dict[float, np.ndarray] | None = None
    hs: dict[str, np.ndarray] | None = None
    temp: dict[float, np.ndarray] | None = None
    source: str | None = None

    def has_any(self) -> bool:
        return bool(self.fill2d or self.hs or self.temp)


def _parse_temp_key(key: str) -> float:
    """A "tm100"/"tp025" kulcs előjeles színhő-értékké (−1,0 / +0,25)."""
    sign = -1.0 if key[1] == "m" else 1.0
    return sign * int(key[2:]) / 100.0


def load_luts(directory: Path | str | None) -> GoldenLuts:
    """A `luts3.json` betöltése a megadott könyvtárból, ha jelen van.

    Hiányzó könyvtár/fájl/blokk esetén tiszta kihagyás (üres override),
    sosem hiba — a repóban a mért adatok nincsenek benne.
    """
    if directory is None:
        return GoldenLuts()
    path = Path(directory) / "luts3.json"
    if not path.is_file():
        return GoldenLuts()
    data = json.loads(path.read_text(encoding="utf-8"))

    def curves(block: dict) -> dict:
        return {key: np.asarray(value, np.float64) for key, value in block.items()}

    fill2d = {
        float(key): lut for key, lut in curves(data.get("fill2d", {})).items()
    }
    hs = curves(data.get("hs", {}))
    temp = {
        _parse_temp_key(key): np.asarray(value, np.float64)
        for key, value in data.get("temp", {}).items()
    }
    return GoldenLuts(
        fill2d=fill2d or None,
        hs=hs or None,
        temp=temp or None,
        source=str(path),
    )


def _interpolate_curve_family(
    family: dict[float, np.ndarray], strength: float
) -> np.ndarray:
    """Görbecsalád (erősség → 256-os LUT) lineáris interpolációja.

    0-nál identitást feltételez (mérten: fill s→0 ≈ identitás); a mért
    tartomány fölött a legnagyobb görbét használja (klippelés, dokumentált
    közelítés).
    """
    knots = sorted(family)
    points = [(0.0, lut_ramp())] + [(s, family[s]) for s in knots]
    if strength <= points[0][0]:
        return points[0][1]
    for (s0, lut0), (s1, lut1) in zip(points, points[1:]):
        if strength <= s1:
            weight = (strength - s0) / (s1 - s0)
            return (1.0 - weight) * lut0 + weight * lut1
    return points[-1][1]


def _hs_family(hs: dict[str, np.ndarray], prefix: str) -> dict[float, np.ndarray]:
    """A hs-blokkból az adott előtag (h/s) görbéi erősség-kulccsal."""
    return {
        int(key[1:]) / 100.0: lut
        for key, lut in hs.items()
        if key.startswith(prefix)
    }


def _apply_temp_offsets(image: np.ndarray, temp: dict, value: float) -> np.ndarray:
    """A mért színhő-eltolások ([ΔB, ΔG, ΔR]) interpolált alkalmazása."""
    knots = sorted(temp)
    points = [(t, temp[t]) for t in knots]
    if 0.0 not in temp:
        points.append((0.0, np.zeros(3)))
        points.sort(key=lambda item: item[0])
    ts = np.array([point[0] for point in points])
    deltas = np.stack([point[1] for point in points])
    offsets_bgr = np.array(
        [np.interp(value, ts, deltas[:, channel]) for channel in range(3)]
    )
    # A mérés cv2/BGR sávokon készült; a render-képeink RGB sorrendűek.
    offsets_rgb = offsets_bgr[::-1]
    result = image.astype(np.float64) + offsets_rgb[None, None, :]
    return np.clip(np.rint(result), 0, 255).astype(np.uint8)


def _apply_fill_lut(image: np.ndarray, luts: GoldenLuts, strength: float) -> np.ndarray:
    return apply_lut(image, _interpolate_curve_family(luts.fill2d, strength))


def _apply_finetune_with_luts(
    image: np.ndarray, op: FilterOp, luts: GoldenLuts
) -> tuple[np.ndarray, bool]:
    """finetune/finetune2 a mért LUT-okkal, ahol vannak; visszaadja, hogy
    történt-e LUT-os felülírás. A paraméter-sorrend a spec szerinti:
    p1=fill, p2=highlights, p3=shadows, p4=pipetta, p5=színhő."""

    def param(index: int) -> float:
        return float(op.params[index]) if len(op.params) > index else 0.0

    used_lut = False
    result = image
    fill = param(1)
    if fill > 0 and luts.fill2d:
        result = _apply_fill_lut(result, luts, fill)
        used_lut = True
    elif fill > 0:
        from picasapy.render.tone import apply_fill

        result = apply_fill(result, fill)
    highlights = param(2)
    hs_h = _hs_family(luts.hs, "h") if luts.hs else {}
    if highlights > 0 and hs_h:
        result = apply_lut(result, _interpolate_curve_family(hs_h, highlights))
        used_lut = True
    elif highlights > 0:
        from picasapy.render.tone import apply_highlights

        result = apply_highlights(result, highlights)
    shadows = param(3)
    hs_s = _hs_family(luts.hs, "s") if luts.hs else {}
    if shadows > 0 and hs_s:
        result = apply_lut(result, _interpolate_curve_family(hs_s, shadows))
        used_lut = True
    elif shadows > 0:
        from picasapy.render.tone import apply_shadows

        result = apply_shadows(result, shadows)
    neutral = parse_neutral_argb(op.params[4]) if len(op.params) > 4 else None
    if neutral is not None:
        result = apply_neutral_pipette(result, neutral)
    temperature = param(5)
    if temperature != 0.0 and luts.temp:
        result = _apply_temp_offsets(result, luts.temp, temperature)
        used_lut = True
    elif temperature != 0.0:
        from picasapy.render.tone import apply_color_temperature

        result = apply_color_temperature(result, temperature)
    return result, used_lut


def render_chain(
    image: np.ndarray, ops: tuple[FilterOp, ...], luts: GoldenLuts
) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    """A lánc renderelése; a mért LUT-ok — ha jelen vannak — a beépített
    közelítések HELYETT futnak (fill, finetune/finetune2 tónus-tagjai).

    Visszatérés: (kép, kihagyott szűrők, LUT-tal felülírt szűrők). LUT-adat
    nélkül bitre azonos az `apply_filters`-szel (delegálja neki a műveletet).
    A crop64 az `apply_filters` szabálya szerint a lánc végén, egyszer fut.
    """
    result = image
    skipped: list[str] = []
    lut_ops: list[str] = []
    crop_op: FilterOp | None = None
    for op in ops:
        name = op.name.casefold()
        if name == "crop64":
            crop_op = op  # csak az effektív (utolsó) crop64 számít
            continue
        if name == "fill" and luts.fill2d:
            strength = float(op.params[1]) if len(op.params) > 1 else 0.0
            result = _apply_fill_lut(result, luts, strength)
            lut_ops.append(op.name)
            continue
        if name in ("finetune", "finetune2") and luts.has_any():
            result, used_lut = _apply_finetune_with_luts(result, op, luts)
            if used_lut:
                lut_ops.append(op.name)
            continue
        result, op_skipped = apply_filters(result, (op,))
        skipped.extend(op_skipped)
    if crop_op is not None:
        result, _ = apply_filters(result, (crop_op,))
    return result, tuple(skipped), tuple(lut_ops)


# --------------------------------------------------------------- összevetés


@dataclass(frozen=True)
class ComparisonResult:
    """Egyetlen (eredeti + lánc + golden) összevetés eredménye."""

    name: str
    filters: str
    verdict: str
    metrics: dict[str, float] = field(default_factory=dict)
    skipped: tuple[str, ...] = ()
    lut_ops: tuple[str, ...] = ()
    note: str = ""

    def filter_names(self) -> tuple[str, ...]:
        """A lánc szűrőnevei (sorrendben, flag nélkül)."""
        return tuple(op.name for op in parse_filters(self.filters))


def _read_rgb(path: Path) -> np.ndarray:
    """Kép beolvasása RGB uint8-ként — hibás/hiányzó fájlnál ValueError."""
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"A kép nem olvasható: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def compare_images(
    rendered: np.ndarray, golden: np.ndarray, thresholds: Thresholds
) -> tuple[str, dict[str, float], str]:
    """Renderelt vs golden kép: (ítélet, metrikák, megjegyzés)."""
    if rendered.shape != golden.shape:
        note = (
            f"méret-eltérés: render {rendered.shape[1]}x{rendered.shape[0]}, "
            f"golden {golden.shape[1]}x{golden.shape[0]}"
        )
        return "eltér", {}, note
    delta_e = delta_e_cie76(rendered, golden)
    metrics = {
        "ssim": round(ssim(rendered, golden), 5),
        "delta_e_mean": round(float(delta_e.mean()), 3),
        "delta_e_p99": round(float(np.percentile(delta_e, 99)), 3),
        **pixel_diff_stats(rendered, golden, thresholds.pixel_tol),
    }
    return verdict(metrics, thresholds), metrics, ""


def compare_pair(
    original_path: Path | str,
    filters_value: str,
    golden_path: Path | str,
    thresholds: Thresholds,
    luts: GoldenLuts = GoldenLuts(),
    name: str | None = None,
) -> ComparisonResult:
    """Egyetlen pár: eredeti kép + filters-lánc renderelve vs Picasa-export."""
    original = _read_rgb(Path(original_path))
    golden = _read_rgb(Path(golden_path))
    ops = parse_filters(filters_value)
    rendered, skipped, lut_ops = render_chain(original, ops, luts)
    result_verdict, metrics, note = compare_images(rendered, golden, thresholds)
    return ComparisonResult(
        name=name or Path(original_path).name,
        filters=filters_value,
        verdict=result_verdict,
        metrics=metrics,
        skipped=skipped,
        lut_ops=lut_ops,
        note=note,
    )


# --------------------------------------------------------------- kit-mód


def _kit_ini_sections(ini_path: Path) -> dict[str, str]:
    """A kit `.picasa.ini`-jéből {képnév: filters-érték} — a saját
    round-trip parserrel (picasapy.ini)."""
    from picasapy.ini.io import load_document

    document = load_document(ini_path)
    sections = {}
    for section in document.file_sections():
        filters_value = section.get("filters")
        if filters_value:
            sections[section.name] = filters_value
    return sections


def _find_export(export_dir: Path, image_name: str) -> Path | None:
    """Az exportált golden megkeresése (a kiterjesztés eltérhet)."""
    exact = export_dir / image_name
    if exact.is_file():
        return exact
    stem = Path(image_name).stem
    for candidate in sorted(export_dir.glob(f"{stem}.*")):
        if candidate.is_file():
            return candidate
    return None


def run_kit(
    kit_dir: Path | str, thresholds: Thresholds, luts: GoldenLuts
) -> list[ComparisonResult]:
    """A make_golden_kit.py által generált kit teljes lefuttatása.

    Szerkezet: <kit>/<mappa>/<kép> + .picasa.ini; goldenek:
    <kit>/export/<mappa>/<kép>. Hiányzó exportnál az eredmény „hiányzik"
    (nem hiba — a felhasználó részlegesen is exportálhatott).
    """
    kit = Path(kit_dir)
    if not kit.is_dir():
        raise ValueError(f"A kit-könyvtár nem létezik: {kit}")
    results: list[ComparisonResult] = []
    for ini_path in sorted(kit.glob("*/.picasa.ini")):
        folder = ini_path.parent
        if folder.name.startswith("00-base") or folder.name == "export":
            continue
        export_dir = kit / "export" / folder.name
        for image_name, filters_value in _kit_ini_sections(ini_path).items():
            row_name = f"{folder.name}/{image_name}"
            original = folder / image_name
            golden = _find_export(export_dir, image_name)
            if golden is None or not original.is_file():
                results.append(
                    ComparisonResult(
                        name=row_name,
                        filters=filters_value,
                        verdict="hiányzik",
                        note="nincs exportált golden ehhez a képhez",
                    )
                )
                continue
            results.append(
                compare_pair(
                    original, filters_value, golden, thresholds, luts, name=row_name
                )
            )
    return results


# --------------------------------------------------------------- riportok


_VERDICT_RANK = {name: rank for rank, name in enumerate(VERDICTS)}


def _per_filter_summary(results: list[ComparisonResult]) -> dict[str, str]:
    """Szűrőnkénti összegzés: minden szűrőhöz a LEGROSSZABB ítélet azok
    közül a sorok közül, amelyek láncában szerepel."""
    summary: dict[str, str] = {}
    for result in results:
        for filter_name in result.filter_names():
            current = summary.get(filter_name)
            if (
                current is None
                or _VERDICT_RANK[result.verdict] > _VERDICT_RANK[current]
            ):
                summary[filter_name] = result.verdict
    return dict(sorted(summary.items()))


def build_report(
    results: list[ComparisonResult], thresholds: Thresholds, luts: GoldenLuts
) -> dict:
    """JSON-szerializálható riport: soronkénti eredmények + összegzések."""
    counts = {name: 0 for name in VERDICTS}
    rows = []
    for result in results:
        counts[result.verdict] += 1
        rows.append(
            {
                "nev": result.name,
                "filters": result.filters,
                "szurok": list(result.filter_names()),
                "itelet": result.verdict,
                "metrikak": result.metrics,
                "kihagyott": list(result.skipped),
                "lut_szurok": list(result.lut_ops),
                "megjegyzes": result.note,
            }
        )
    return {
        "kuszobok": thresholds.as_dict(),
        "lut_forras": luts.source,
        "osszegzes": counts,
        "szuronkent": _per_filter_summary(results),
        "eredmenyek": rows,
    }


def format_report(report: dict) -> str:
    """Ember-olvasható (terminál) riport a JSON-riportból."""
    lines = ["Golden-összehasonlítás — PicasaPy render vs Picasa-export", ""]
    if report["lut_forras"]:
        lines.append(f"Mért LUT-ok: {report['lut_forras']}")
    else:
        lines.append("Mért LUT-ok: nincsenek (beépített közelítések futnak)")
    lines.append("")
    header = (
        f"{'ítélet':<10} {'SSIM':>7} {'ΔEátl':>7} {'ΔEp99':>7} "
        f"{'max|Δ|':>7} {'túl%':>6}  név"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for row in report["eredmenyek"]:
        metrics = row["metrikak"]
        if metrics:
            values = (
                f"{metrics['ssim']:>7.4f} {metrics['delta_e_mean']:>7.2f} "
                f"{metrics['delta_e_p99']:>7.2f} {metrics['max_diff']:>7d} "
                f"{metrics['over_tolerance_ratio'] * 100:>5.1f}%"
            )
        else:
            values = f"{'—':>7} {'—':>7} {'—':>7} {'—':>7} {'—':>6}"
        suffix = ""
        if row["lut_szurok"]:
            suffix += f"  [LUT: {','.join(row['lut_szurok'])}]"
        if row["kihagyott"]:
            suffix += f"  [kihagyva: {','.join(row['kihagyott'])}]"
        if row["megjegyzes"]:
            suffix += f"  ({row['megjegyzes']})"
        lines.append(f"{row['itelet']:<10} {values}  {row['nev']}{suffix}")
    lines.append("")
    lines.append("Szűrőnként (legrosszabb ítélet):")
    for filter_name, filter_verdict in report["szuronkent"].items():
        lines.append(f"  {filter_name:<12} {filter_verdict}")
    lines.append("")
    counts = report["osszegzes"]
    lines.append(
        "Összesen: "
        + " · ".join(f"{name}: {counts[name]}" for name in VERDICTS)
    )
    return "\n".join(lines)


# --------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Golden-összehasonlító harness: PicasaPy-render vs Picasa-export "
            "(SSIM/ΔE/pixel-diff)."
        )
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--luts",
            type=Path,
            default=None,
            help=(
                "A mért LUT-ok könyvtára (luts3.json); hiánynál a beépített "
                "közelítések futnak"
            ),
        )
        p.add_argument("--json", type=Path, default=None, help="JSON-riport útvonala")
        p.add_argument("--pixel-tol", type=int, default=Thresholds.pixel_tol)
        p.add_argument("--frac-tol", type=float, default=Thresholds.frac_tol)
        p.add_argument("--ssim-min", type=float, default=Thresholds.ssim_min)
        p.add_argument("--de-mean-max", type=float, default=Thresholds.de_mean_max)

    pair = sub.add_parser("pair", help="egyetlen eredeti+golden pár összevetése")
    pair.add_argument("original", type=Path, help="eredeti (szűretlen) kép")
    pair.add_argument("golden", type=Path, help="a Picasa exportált képe")
    pair.add_argument("--filters", required=True, help="a filters= lánc értéke")
    add_common(pair)

    kit = sub.add_parser("kit", help="teljes golden-kit lefuttatása")
    kit.add_argument("kit_dir", type=Path, help="a golden-kit gyökere")
    add_common(kit)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI belépési pont; kilépési kód 0 = nincs „eltér" sor."""
    args = _build_parser().parse_args(argv)
    thresholds = Thresholds(
        pixel_tol=args.pixel_tol,
        frac_tol=args.frac_tol,
        ssim_min=args.ssim_min,
        de_mean_max=args.de_mean_max,
    )
    luts = load_luts(args.luts)
    if args.mode == "pair":
        results = [
            compare_pair(args.original, args.filters, args.golden, thresholds, luts)
        ]
    else:
        results = run_kit(args.kit_dir, thresholds, luts)
    report = build_report(results, thresholds, luts)
    if args.json is not None:
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(format_report(report))
    return 1 if report["osszegzes"]["eltér"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
