"""#6585: determinisztikus Colab-kötegek és helyi összevetés."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import random
import re
import shutil
import sys
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TOOL_PATH = _ROOT / "scripts" / "differencialis_lanc.py"
_SPEC = importlib.util.spec_from_file_location("differencialis_lanc", _TOOL_PATH)
_TOOL = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault("differencialis_lanc", _TOOL)
_SPEC.loader.exec_module(_TOOL)


# figyelo_cella.py Colab nélkül nem importálható (google.colab.userdata), ezért
# ezek a sémaszabályok a végrehajtó _alap(), v3 validate() és ini_ellenoriz()
# függvényeinek releváns, szintetikus feladatokra szűkített másolatai.
_INI_MAX_BAJT = 20_000
_INI_MAX_SOR = 400
_INI_SZEKCIO_RE = re.compile(
    r"\[(Contacts2|Picasa|[A-Za-z0-9_][A-Za-z0-9_. \-]{0,99})\]"
)
_INI_KULCS_RE = re.compile(r"[A-Za-z0-9_]{1,64}")
_INI_ERTEK_MAX = 2_000
_JOB_FIELDS = {
    "v",
    "tipus",
    "cel",
    "indulas",
    "lepesek",
    "kimenet",
    "keret",
    "picasa_ini_be",
    "mintakeszlet",
}
_MINTAKESZLETEK = {"arcos", "kombinalt", "idorend"}
_LEPES_KULCSOK = {"kattint", "billentyu", "var"}
_LEPES_MAX = 40


def _colab_lepesek_ellenoriz(lepesek: object) -> None:
    """A végrehajtó (figyelo_cella.py) lépésszabályainak a #6585 által használt része."""
    if not isinstance(lepesek, list) or not 1 <= len(lepesek) <= _LEPES_MAX:
        raise ValueError("lepesek: 1-40 lépés kell")
    for lepes in lepesek:
        if not isinstance(lepes, dict) or len(lepes) != 1 or set(lepes) - _LEPES_KULCSOK:
            raise ValueError("lepesek: lépésenként egy ismert kulcs kell")
        kulcs, ertek = next(iter(lepes.items()))
        if kulcs == "var" and (
            isinstance(ertek, bool) or not isinstance(ertek, (int, float)) or not 0 < ertek <= 10
        ):
            raise ValueError("var: 0 < mp <= 10")
        if kulcs == "kattint" and (
            not isinstance(ertek, list) or len(ertek) != 2
            or not all(isinstance(v, int) and not isinstance(v, bool) for v in ertek)
        ):
            raise ValueError("kattint: [x, y] egész kell")
        if kulcs == "billentyu" and (not isinstance(ertek, str) or not ertek):
            raise ValueError("billentyu: nem üres szöveg kell")


def _colab_ini_ellenoriz(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("üres szöveg")
    if len(text.encode("utf-8")) > _INI_MAX_BAJT:
        raise ValueError("bájtkorlát")
    lines = text.replace("\r\n", "\n").split("\n")
    if len(lines) > _INI_MAX_SOR:
        raise ValueError("sorkorlát")
    for line in lines:
        if not line.strip():
            continue
        if not line.isprintable() or line != line.strip():
            raise ValueError("tiltott karakter")
        if line.startswith("["):
            if not _INI_SZEKCIO_RE.fullmatch(line) or ".." in line:
                raise ValueError("hibás szakasz")
            continue
        key, equals, value = line.partition("=")
        if not equals or not _INI_KULCS_RE.fullmatch(key) or len(value) > _INI_ERTEK_MAX:
            raise ValueError("hibás kulcs=érték sor")
    return text.replace("\r\n", "\n").rstrip("\n") + "\n"


def _colab_validate_job(job: dict) -> None:
    """A #6585 által használt v3 ui_capture séma ellenőrzése."""
    if not isinstance(job, dict) or set(job) - _JOB_FIELDS:
        raise ValueError("ismeretlen vagy hibás job mező")
    if job.get("v") != 3 or isinstance(job.get("v"), bool):
        raise ValueError("v: 3 kell")
    if job.get("tipus") != "ui_capture":
        raise ValueError("tipus: ui_capture kell")
    if not isinstance(job.get("cel"), str) or not 1 <= len(job["cel"]) <= 500:
        raise ValueError("cel: 1-500 karakteres szöveg kell")
    if job.get("indulas") != "alapallapot":
        raise ValueError("indulas: érvénytelen lépéssor")
    _colab_lepesek_ellenoriz(job.get("lepesek"))
    if job.get("kimenet") != ["allapot", "export"]:
        raise ValueError("kimenet: érvénytelen lista")
    if job.get("keret") != {"perc": 30}:
        raise ValueError("keret: érvénytelen időkorlát")
    if "mintakeszlet" in job and job["mintakeszlet"] not in _MINTAKESZLETEK:
        raise ValueError("mintakeszlet: ismeretlen készlet")
    _colab_ini_ellenoriz(job.get("picasa_ini_be"))


def _synthetic_catalog(tmp_path: Path, names: tuple[str, ...]) -> tuple[Path, Path]:
    image_dir = tmp_path / "external-images"
    image_dir.mkdir()
    entries = []
    for index, name in enumerate(names):
        image = np.full((24 + index, 32 + index, 3), 50 + index, dtype=np.uint8)
        _write_rgb(image_dir / name, image)
        entries.append(
            {"nev": name, "meret": (image_dir / name).stat().st_size, "mod": 0}
        )
    manifest = tmp_path / "catalog.json"
    manifest.write_text(
        json.dumps({"fajlok": entries}, ensure_ascii=False), encoding="utf-8"
    )
    return manifest, image_dir


def _write_rgb(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    assert cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def test_a_mag_azonos_lancokat_general() -> None:
    assert _TOOL.generate_chains(
        seed=6585,
        count=12,
        image_names=("minta-1.png", "minta-2.jpg"),
        image_dimensions={"minta-1.png": (32, 24), "minta-2.jpg": (32, 24)},
    ) == _TOOL.generate_chains(
        seed=6585,
        count=12,
        image_names=("minta-1.png", "minta-2.jpg"),
        image_dimensions={"minta-1.png": (32, 24), "minta-2.jpg": (32, 24)},
    )


def test_a_numerikus_mintavetel_a_tartomany_belsejebol_is_valaszt() -> None:
    param = SimpleNamespace(
        kind="number", minimum=-2.0, maximum=3.0, max_formula=None
    )
    rng = random.Random(6585)

    values = [_TOOL._random_control_value(rng, param) for _ in range(32)]

    assert all(param.minimum <= value <= param.maximum for value in values)
    assert any(value not in {param.minimum, 0.5, param.maximum} for value in values)


def test_egy_paranccsal_ujrafuttathato_a_generálas_helyi_render_es_osszevetes(
    tmp_path: Path, capsys
) -> None:
    manifest, image_dir = _synthetic_catalog(tmp_path, ("k01.jpg", "k02.jpg"))
    output = tmp_path / "campaign"
    original_dir = tmp_path / "picasa"
    args = [
        "futtatas",
        "--mag",
        "6585",
        "--db",
        "2",
        "--nevjegyzek",
        str(manifest),
        "--kepek",
        str(image_dir),
        "--mintakeszlet",
        "kombinalt",
        "--ki",
        str(output),
    ]

    assert _TOOL.main(args) == 0
    capsys.readouterr()
    records = json.loads((output / "lancok.json").read_text(encoding="utf-8"))
    assert len(records) == 2
    local_rows = json.loads(
        (output / "sajat" / "futtatas.json").read_text(encoding="utf-8")
    )
    assert all(row["allapot"] == "kész" for row in local_rows)

    for record in records:
        source = output / "sajat" / f"{record['azonosito']}.jpg"
        target = (
            original_dir
            / record["koteg"]
            / f"export__{Path(record['kep']).stem}.jpg"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    assert _TOOL.main([*args, "--eredeti", str(original_dir)]) == 0

    with (output / "eredmeny.csv").open(encoding="utf-8", newline="") as stream:
        result_rows = list(csv.DictReader(stream))
    assert len(result_rows) == 2
    assert all(row["egyezes"] == "egyezik" for row in result_rows)
    assert "Összevetés: 2/2" in capsys.readouterr().out


def test_a_lancok_renderelheto_szuroket_es_tartomanybeli_parametereket_hasznal() -> None:
    records = _TOOL.generate_chains(
        seed=6585,
        count=40,
        image_names=("minta-1.png", "minta-2.jpg", "minta-3.tif"),
        image_dimensions={
            "minta-1.png": (800, 800),
            "minta-2.jpg": (800, 800),
            "minta-3.tif": (800, 800),
        },
    )

    for record in records:
        for operation in _TOOL.parse_filters(record["filters"]):
            assert _TOOL.can_render_filter(operation.name)
            params = _TOOL.resolve_effect_params(
                operation.name, width=800.0, height=800.0
            )
            serialized = operation.params[1:]
            assert len(serialized) == len(params)
            for value, param in zip(serialized, params, strict=True):
                if param.kind == "color":
                    assert re.fullmatch(r"(?:00|ff)[0-9a-f]{6}", value)
                elif param.kind == "checkbox":
                    assert value in {"0", "1"}
                elif param.max_formula is not None:
                    assert 0.0 <= float(value) <= 100.0
                else:
                    assert param.minimum <= float(value) <= param.maximum
        report = _TOOL.apply_filters(
            np.full((800, 800, 3), 127, dtype=np.uint8),
            _TOOL.parse_filters(record["filters"]),
        )
        assert report.skipped == ()


def test_general_a_katalogusbol_csak_meglevo_azonos_meretu_kepeket_valaszt(
    tmp_path: Path,
) -> None:
    manifest, image_dir = _synthetic_catalog(
        tmp_path, ("k01.jpg", "k02.jpg", "invalid,name.png")
    )
    catalog = json.loads(manifest.read_text(encoding="utf-8"))
    catalog["fajlok"].extend(
        [
            {"nev": "missing.png", "meret": 10},
            {"nev": "k01.jpg", "meret": 999},
            {"nev": "ignored.webp", "meret": 20},
        ]
    )
    manifest.write_text(json.dumps(catalog), encoding="utf-8")
    (image_dir / "ignored.webp").write_bytes(b"x" * 20)

    records = _TOOL.generalize(
        tmp_path / "batch",
        seed=6585,
        count=5,
        image_manifest=manifest,
        image_dir=image_dir,
        mintakeszlet="kombinalt",
    )

    assert len(records) == 5
    assert {row["kep"] for row in records} == {"k01.jpg", "k02.jpg"}
    batches = {}
    for row in records:
        batches.setdefault(row["koteg"], []).append(row["kep"])
    assert all(len(images) == len(set(images)) for images in batches.values())


def test_general_200_lancot_korlatozott_ini_es_colab_job_fajlokba_ir(
    tmp_path: Path,
) -> None:
    names = tuple(f"k{index:02d}.jpg" for index in range(1, 8))
    manifest, image_dir = _synthetic_catalog(tmp_path, names)

    records = _TOOL.generalize(
        tmp_path / "batches",
        seed=6585,
        count=200,
        image_manifest=manifest,
        image_dir=image_dir,
        mintakeszlet="kombinalt",
    )
    output = tmp_path / "batches"
    ini_files = sorted(output.glob("koteg-*.ini"))
    job_files = sorted(output.glob("koteg-*.job.json"))

    assert len(records) == 200
    assert len(ini_files) == len(job_files) == 29
    batches = {}
    for row in records:
        batches.setdefault(row["koteg"], []).append(row["kep"])
        assert 2 <= len(_TOOL.parse_filters(row["filters"])) <= 6
    assert all(len(images) == len(set(images)) for images in batches.values())
    for ini_path, job_path in zip(ini_files, job_files, strict=True):
        ini_text = ini_path.read_text(encoding="utf-8")
        assert _colab_ini_ellenoriz(ini_text) == ini_text
        job = json.loads(job_path.read_text(encoding="utf-8"))
        _colab_validate_job(job)
        assert job["picasa_ini_be"] == ini_text
        assert job["mintakeszlet"] == "kombinalt"
        assert len(re.findall(r"^\[[^]]+\]$", ini_text, re.MULTILINE)) <= 7


def test_osszevet_a_picasa_jpg_export_nevet_es_a_meglevo_golden_kuszobot_hasznalja(
    tmp_path: Path,
) -> None:
    image = np.tile(np.arange(64, dtype=np.uint8), (48, 1))
    image = np.repeat(image[:, :, None], 3, axis=2)
    own_path = tmp_path / "sajat" / "lanc-0001.jpg"
    original_path = tmp_path / "eredeti" / "koteg-001" / "export__color_patches.jpg"
    _write_rgb(own_path, image)
    _write_rgb(original_path, image)
    record = {
        "azonosito": "lanc-0001",
        "koteg": "koteg-001",
        "kep": "color_patches.png",
        "filters": "bw=1;sat=1,0.500000;",
    }

    result = _TOOL.compare_record(record, own_path.parent, original_path.parent.parent)

    assert result["egyezes"] == "egyezik"
    assert result["ssim"] == pytest.approx(1.0)
    assert result["delta_e"] == pytest.approx(0.0)


def test_sajat_a_katalogusbol_azonos_meretu_kepeket_jpg_be_renderel(
    tmp_path: Path,
) -> None:
    record = {
        "azonosito": "lanc-0001",
        "koteg": "koteg-001",
        "kep": "color_patches.png",
        "filters": "bw=1;sat=1,0.500000;",
    }
    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    _TOOL._write_json(batch_dir / "lancok.json", [record])
    image = np.zeros((48, 64, 3), dtype=np.uint8)
    image[..., 0] = np.arange(64, dtype=np.uint8)
    image_dir = tmp_path / "images"
    source = image_dir / record["kep"]
    _write_rgb(source, image)
    manifest = tmp_path / "catalog.json"
    manifest.write_text(
        json.dumps({"fajlok": [{"nev": source.name, "meret": source.stat().st_size}]}),
        encoding="utf-8",
    )

    results = _TOOL.run_local(batch_dir, image_manifest=manifest, image_dir=image_dir)

    output = batch_dir / "sajat" / "lanc-0001.jpg"
    assert results[0]["allapot"] == "kész"
    assert output.is_file()
    assert output.read_bytes().startswith(b"\xff\xd8")
    assert _TOOL._read_rgb(output).shape == image.shape


def test_sajat_kihagyja_a_hianyzot_vagy_meretben_eltet_kepeket(tmp_path: Path) -> None:
    record = {
        "azonosito": "lanc-0002",
        "koteg": "koteg-001",
        "kep": "gray_ramp.png",
        "filters": "bw=1;sat=1,0.500000;",
    }
    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    _TOOL._write_json(batch_dir / "lancok.json", [record])
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / record["kep"]).write_bytes(b"wrong size")
    manifest = tmp_path / "catalog.json"
    manifest.write_text(
        json.dumps({"fajlok": [{"nev": record["kep"], "meret": 10_000}]}),
        encoding="utf-8",
    )

    results = _TOOL.run_local(batch_dir, image_manifest=manifest, image_dir=image_dir)

    assert results[0]["allapot"] == "hiányzik vagy eltér a katalógusbeli kép" 
    assert not (batch_dir / "sajat" / "lanc-0002.jpg").exists()
    assert (batch_dir / "sajat" / "futtatas.json").is_file()


def test_minimalizalo_szurotorlesi_jeloltjei_rovidulnek() -> None:
    record = {
        "azonosito": "lanc-0099",
        "koteg": "koteg-050",
        "kep": "gray_ramp.png",
        "filters": "bw=1;sat=1,0.500000;warm=1;",
    }

    candidates = _TOOL.minimal_candidates(record)

    assert candidates
    assert all(
        1 <= len(_TOOL.parse_filters(candidate["filters"])) < 3
        for candidate in candidates
    )
    assert all(candidate["kep"] == record["kep"] for candidate in candidates)
    assert len({candidate["azonosito"] for candidate in candidates}) == len(candidates)


def test_minimalizalo_minden_jelolthoz_kulon_ini_es_futtathato_job_fajlt_ir(
    tmp_path: Path,
) -> None:
    record = {
        "azonosito": "lanc-0099",
        "koteg": "koteg-050",
        "kep": "gray_ramp.png",
        "filters": "bw=1;sat=1,0.500000;warm=1;",
    }
    _TOOL._write_json(tmp_path / "lancok.json", [record])

    candidates = _TOOL.minimize(tmp_path, "lanc-0099")

    ini_files = sorted(tmp_path.glob("minimal-lanc-0099*.ini"))
    job_files = sorted(tmp_path.glob("minimal-lanc-0099*.job.json"))
    assert len(candidates) == len(ini_files) == len(job_files) == 3
    for ini_path, job_path in zip(ini_files, job_files, strict=True):
        text = ini_path.read_text(encoding="utf-8")
        assert _colab_ini_ellenoriz(text) == text
        job = json.loads(job_path.read_text(encoding="utf-8"))
        _colab_validate_job(job)
        assert job["picasa_ini_be"] == text


def test_egy_effekt_parameterjavaslatai_tartomanyon_beluliek() -> None:
    record = {
        "azonosito": "lanc-0100",
        "koteg": "koteg-050",
        "kep": "gray_ramp.png",
        "filters": "sat=1,0.500000;",
    }

    candidates = _TOOL.minimal_candidates(record)

    assert len(candidates) == 3
    values = {
        _TOOL.parse_filters(candidate["filters"])[0].params[1]
        for candidate in candidates
    }
    assert values == {"-1.000000", "0.000000", "1.000000"}


def test_a_colab_lepesellenor_elutasitja_a_tiz_masodpercnel_hosszabb_varakozast() -> None:
    with pytest.raises(ValueError, match="var"):
        _colab_lepesek_ellenoriz([{"var": 60}])
    with pytest.raises(ValueError, match="1-40"):
        _colab_lepesek_ellenoriz([{"var": 1}] * 41)


def test_a_job_lepesei_kivarjak_az_exportot_a_vegrehajto_korlatai_kozott() -> None:
    lepesek = _TOOL._JOB_STEPS
    _colab_lepesek_ellenoriz(lepesek)
    export = next(i for i, lepes in enumerate(lepesek) if lepes == {"kattint": [744, 672]})
    assert sum(lepes.get("var", 0) for lepes in lepesek[export + 1:]) >= 180


def test_az_eredeti_export_neve_a_vegrehajto_lapitasat_koveti(tmp_path: Path) -> None:
    # A végrehajtó a kiadásban az `export/<fájl>` utat `export__<fájl>`-ra lapítja
    # (job-378: `export__color_patches.jpg`, `export___026e89d3-....jpg` a `_026e89d3-....jpg`-ből).
    koteg = tmp_path / "koteg-001"
    koteg.mkdir()
    for nev in ("export__color_patches.jpg", "export___026e.jpg"):
        (koteg / nev).write_bytes(b"x")
    for kep, varhato in (("color_patches.jpg", "export__color_patches.jpg"),
                         ("_026e.jpg", "export___026e.jpg"),
                         ("_026e.png", "export___026e.jpg")):
        ut = _TOOL._original_image_path({"kep": kep, "koteg": "koteg-001"}, tmp_path)
        assert ut == koteg / varhato


def test_a_mintakeszlet_a_jobba_es_a_lancrekordba_kerul(tmp_path: Path) -> None:
    # A mestermásolat képeire a picasa_ini_be nem hat (job-379), a mintakészletéire igen (job-230).
    manifest, image_dir = _synthetic_catalog(tmp_path, ("k01.jpg", "k02.jpg"))
    records = _TOOL.generalize(
        tmp_path / "ki", seed=1, count=4, image_manifest=manifest,
        image_dir=image_dir, mintakeszlet="kombinalt",
    )
    assert {record["mintakeszlet"] for record in records} == {"kombinalt"}
    for job_path in sorted((tmp_path / "ki").glob("koteg-*.job.json")):
        job = json.loads(job_path.read_text(encoding="utf-8"))
        assert job["mintakeszlet"] == "kombinalt"
        _colab_validate_job(job)
    with pytest.raises(ValueError, match="mintakészlet"):
        _TOOL._capture_job("koteg-001", "[a.jpg]\nfilters=sepia=1;\n", "nincs")


def test_az_egyetlen_menet_a_mintakeszletet_minden_colab_kotegbe_atadja(
    tmp_path: Path,
) -> None:
    manifest, image_dir = _synthetic_catalog(tmp_path, ("k01.jpg", "k02.jpg"))
    output = tmp_path / "kampany"

    records, _, _ = _TOOL.run_campaign(
        output,
        seed=6585,
        count=2,
        image_manifest=manifest,
        image_dir=image_dir,
        mintakeszlet="kombinalt",
    )

    assert {record["mintakeszlet"] for record in records} == {"kombinalt"}
    for job_path in sorted(output.glob("koteg-*.job.json")):
        assert json.loads(job_path.read_text(encoding="utf-8"))["mintakeszlet"] == "kombinalt"
