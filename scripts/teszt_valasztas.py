#!/usr/bin/env python3
"""PR-diff alapján válassza ki a teszteket, majd tervezze meg a darabokat (#4922).

A választás biztonsági elve: amit nem lehet statikusan követni, az teljes
készletet indít. A Python-importoknál az AST a függvények törzsét is bejárja,
így a lusta importok is bekerülnek a visszafelé követett gráfba.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from teszt_valasztas_importok import (
    _dependento_tesztek,
    _module_name,
)


SMOKE_TESTS = (
    "tests/test_teszt_valasztas.py",
    "tests/test_ci_valtozas_3298.py",
    "tests/app/test_startup_smoke_4687.py",
)
HELP_TESTS = (
    "tests/app/test_sugo_tartalom_2054.py",
    "tests/test_help_hivatkozasok_2212.py",
    "tests/test_help_kereses_2214.py",
    "tests/app/qml_functional/test_sugo_kereso_lista_2214.py",
)
I18N_TESTS = (
    "tests/app/test_i18n_completeness.py",
    "tests/app/test_i18n_dictionary_4313.py",
    "tests/app/test_hivatalos_feliratok_3358.py",
    "tests/app/test_hivatalos_feliratok_3573.py",
    "tests/test_i18n_build_4817.py",
    "tests/test_i18n_generator_4866.py",
)
TARGET_SHARD_SECONDS = 180
MAX_SHARDS = 16
MAX_PR_SHARDS = 20
# Mérés nélküli projektnél az ismert készletből választott konzervatív
# fájlszám. A tényleges időt ilyenkor nem becsüljük meg.
FILES_PER_SHARD_WITHOUT_TIMINGS = 30
MAX_SELECTED_FRACTION = 0.6
# A nem-app fájlok korábbi teljes futásának összesített mérési kulcsa.
# Teljes készletnél ez a súlyozást és a darabszámot segíti, nem futtatási egység.
NON_APP_UNIT = "tests --ignore=tests/app"
_FULL_TRIGGER_FILES = frozenset({"pyproject.toml"})
WINDOWS_SENSITIVE_TESTS = frozenset({
    # Tényleges Windows-futtatásban eltérő QML-geometria, útvonal vagy
    # natív fájlművelet.
    "tests/app/qml_functional/test_adjust_timestamp_4332.py",
    "tests/app/qml_functional/test_button_label_fit_992.py",
    "tests/app/qml_functional/test_earth_megtekintes_1589.py",
    "tests/app/qml_functional/test_eredeti_geometria_racs_2494.py",
    "tests/app/qml_functional/test_felulet_betu_3279.py",
    "tests/app/qml_functional/test_gomb_tipografia_815.py",
    "tests/app/qml_functional/test_gombmagassag_platformfuggetlen_2597.py",
    "tests/app/qml_functional/test_maradek_arc_video_4229.py",
    "tests/app/qml_functional/test_orokolt_ful_betumetrika_3263.py",
    "tests/app/qml_functional/test_tiszta_profil_4317.py",
    "tests/app/qml_functional/test_ui_tulcsordulas_656.py",
    "tests/app/qml_functional/test_video_panel_4566.py",
    "tests/app/test_application.py",
    "tests/app/test_eltunt_gyoker_vedelme_1560.py",
    "tests/app/test_fileops_controller.py",
    "tests/app/test_folder_hierarchy.py",
    "tests/app/test_hatterkep_windows_2985.py",
    "tests/app/test_indulasi_fusteszt_699.py",
    "tests/app/test_kepernyovedo_tetlenseg_4613.py",
    "tests/app/test_mappa_borito_ekezetes_ut_3352.py",
    "tests/app/test_nativ_utvonal_kiiras_1629.py",
    "tests/app/test_platform_storage_1076.py",
    "tests/app/test_qml_video.py",
    "tests/app/test_startup_smoke_4687.py",
    "tests/app/test_timestamp_controller_4693.py",
    "tests/app/test_timestamp_video_4885.py",
    "tests/app/test_windows_csapdak_1082.py",
    "tests/app/test_mentes_gyoker_feloldas_3776.py",
    "tests/export/test_export_hibaagak_1617.py",
    "tests/fileops/test_move_folder.py",
    "tests/fileops/test_kuka_windows_1182.py",
    "tests/fileops/test_reveal_platform_1104.py",
    "tests/index/test_sync.py",
    "tests/mailer/test_mapi_windows_4607.py",
    "tests/metadata/test_iptc_writer.py",
    "tests/packaging/test_windows_csomagolas_3021.py",
    "tests/packaging/test_windows_telepito_3021.py",
    "tests/perf/test_exportcel_utvonalfeloldas_2483.py",
    "tests/perf/test_tarolo_tipus_1660.py",
    "tests/scanner/test_korabbi_telepites_windows_1620.py",
    "tests/test_chmod_platform_kapu_1864.py",
    "tests/test_ioutil.py",
    "tests/test_or_kimenet_kodolas_2077.py",
    "tests/test_paths.py",
    "tests/test_platform_seam_1217.py",
    "tests/test_posix_or_2077.py",
    "tests/test_run_tests_maradek_eletjel_1358.py",
    "tests/test_run_tests_osszeomlas_diagnosztika_1457.py",
    "tests/test_subprocess_kodolas_or_2111.py",
    "tests/webexport/test_ekezetes_utvonal_1991.py",
})
_VERSION_LINE = re.compile(
    r"^\s*version\s*=\s*(['\"])(?P<value>[^'\"]+)\1\s*(?:#.*)?$"
)
_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Selection:
    fajlok: tuple[str, ...]
    teljes: bool
    indok: str
    nem_merheto: tuple[str, ...] = ()


@dataclass(frozen=True)
class ShardPlan:
    darabszam: int
    mert_masodperc: float
    ismeretlen_fajlok: tuple[str, ...]
    tul_hosszu_fajlok: tuple[str, ...]


def discover_tests(root: Path) -> list[str]:
    """A pytest által futtatható, név szerint felismert tesztfájlok."""
    tests = root / "tests"
    if not tests.is_dir():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in tests.rglob("test_*.py")
        if path.is_file()
    )


def pyproject_only_version_changed(old: str, new: str) -> bool:
    """Igaz, ha kizárólag a pyproject egy meglévő verziósora változott."""
    regi_sorok = old.splitlines()
    uj_sorok = new.splitlines()
    regi_verziok = [s for s in regi_sorok if _VERSION_LINE.fullmatch(s)]
    uj_verziok = [s for s in uj_sorok if _VERSION_LINE.fullmatch(s)]
    if len(regi_verziok) != 1 or len(uj_verziok) != 1:
        return False
    regi_maras = [s for s in regi_sorok if not _VERSION_LINE.fullmatch(s)]
    uj_maras = [s for s in uj_sorok if not _VERSION_LINE.fullmatch(s)]
    regi_ertek = _VERSION_LINE.fullmatch(regi_verziok[0]).group("value")
    uj_ertek = _VERSION_LINE.fullmatch(uj_verziok[0]).group("value")
    return regi_maras == uj_maras and regi_ertek != uj_ertek



def _test_files_referencing(root: Path, tests: Iterable[str], path: str) -> set[str]:
    """A fájlt név vagy útvonal szerint olvasó tesztek."""
    normalized = path.replace("\\", "/")
    needles = {normalized, Path(normalized).name}
    if normalized.endswith(".py"):
        needles.add(Path(normalized).stem)
    return {
        test
        for test in tests
        if any(
            needle and needle in (root / test).read_text(
                encoding="utf-8", errors="replace"
            ).replace("\\", "/")
            for needle in needles
        )
    }


def windows_only_tests(
    root: Path, selection: Selection, *, force_full: bool
) -> Selection:
    """PR-en a kiválasztott Windows-érzékeny fájlokat, mainen a teljes listát adja."""
    if force_full:
        return Selection(tuple(discover_tests(root)), True, "main: teljes Windows-tesztkészlet")
    windows = tuple(
        path for path in selection.fajlok if path in WINDOWS_SENSITIVE_TESTS
    )
    return Selection(windows, False, "PR: kiválasztott Windows-érzékeny tesztek")



def select_tests(
    root: Path,
    changed: Sequence[str] | None,
    *,
    pyproject_version_only: bool = False,
    force_full: bool = False,
) -> Selection:
    """Válassza ki a diff által érintett teszteket; bizonytalanságnál mindet."""
    all_tests = discover_tests(root)
    all_set = set(all_tests)
    smoke = sorted(path for path in SMOKE_TESTS if path in all_set)
    if force_full:
        return Selection(tuple(all_tests), True, "teljes futás kérése")
    if not changed:
        return Selection(tuple(all_tests), True, "üres vagy nem megállapítható diff")

    selected: set[str] = set(smoke)
    modules: set[str] = set()
    direct_consumers: dict[str, set[str]] = {}
    qml_paths: list[str] = []
    source_files = 0
    uncertainty: list[str] = []
    actionable = False

    for raw in changed:
        path = raw.replace("\\", "/").removeprefix("./")
        if path in _FULL_TRIGGER_FILES:
            if path == "pyproject.toml" and pyproject_version_only:
                continue
            return Selection(tuple(all_tests), True, f"teljes készletet kiváltó fájl: {path}")
        if path.endswith("/conftest.py") or path == "conftest.py":
            return Selection(tuple(all_tests), True, f"közös pytest-beállítás változott: {path}")
        if path.startswith("tests/support/"):
            return Selection(tuple(all_tests), True, "a tests/support közös segédei változtak")
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
            readers = _test_files_referencing(root, all_tests, path)
            if readers:
                selected.update(readers)
                actionable = True
                continue
            return Selection(
                tuple(all_tests), True,
                f"CI-fájlhoz nem található közvetlen tesztőr: {path}",
            )
        if path.startswith((".github/", "packaging/")):
            return Selection(tuple(all_tests), True, f"közös CI/csomagolási fájl változott: {path}")
        if path == "CHANGELOG.md" or path.startswith("changelog.d/"):
            continue
        if path == "pyproject.toml" and pyproject_version_only:
            continue
        if path.startswith("docs/"):
            fajlnev = Path(path).name
            for test in all_tests:
                try:
                    content = (root / test).read_text(
                        encoding="utf-8", errors="replace"
                    ).replace("\\", "/")
                except OSError:
                    continue
                if path in content or fajlnev in content:
                    selected.add(test)
                    actionable = True
            continue
        if path in {"README.md", "LICENSE", "CONTRIBUTING.md"}:
            continue
        if path in all_set:
            selected.add(path)
            actionable = True
            continue
        if path.startswith("tests/") and path.endswith(".py"):
            module = _module_name(path, root_kind="tests")
            if module:
                modules.add(module)
                modules.add(Path(path).stem)
                actionable = True
                continue
            uncertainty.append(path)
            continue
        if path.startswith("src/picasapy/"):
            if path.endswith(".qml"):
                qml_paths.append(path)
                source_files += 1
                actionable = True
                continue
            if path.startswith("src/picasapy/app/i18n/") and path.endswith((".ts", ".qm")):
                selected.update(test for test in I18N_TESTS if test in all_set)
                # Az egyedi katalógust közvetlenül olvasó tesztek is fussanak.
                for test in all_tests:
                    try:
                        content = (root / test).read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if Path(path).name in content:
                        selected.add(test)
                actionable = True
                continue
            if path.startswith("src/picasapy/help/") and path.endswith(".md"):
                help_tests = {test for test in HELP_TESTS if test in all_set}
                if not help_tests:
                    return Selection(tuple(all_tests), True, "a súgó tartalmához nem található őrteszt")
                selected.update(help_tests)
                actionable = True
                continue
            if path.startswith("src/picasapy/help/") and Path(path).name in {
                ".last_documented_commit", ".update.log"
            }:
                helper_test = "tests/scripts/test_kiadas_szukseges_1319.py"
                if helper_test in all_set:
                    selected.add(helper_test)
                    actionable = True
                    continue
            if path.endswith(".py"):
                module = _module_name(path, root_kind="source")
                if module:
                    modules.add(module)
                    direct_consumers[module] = _test_files_referencing(
                        root, all_tests, path
                    )
                    source_files += 1
                    actionable = True
                    continue
            uncertainty.append(path)
            continue
        if path.startswith("scripts/") and path.endswith(".py"):
            module = _module_name(path, root_kind="scripts")
            if module:
                modules.add(module)
                direct_consumers[module] = _test_files_referencing(
                    root, all_tests, path
                )
                source_files += 1
                actionable = True
                continue
        if path.startswith("scripts/"):
            readers = _test_files_referencing(root, all_tests, path)
            if readers:
                selected.update(readers)
                actionable = True
                continue
        # A fentieken kívüli adat, beállítás vagy új forrásfajta hatását nem
        # lehet megbízhatóan az importgráfból követni.
        uncertainty.append(path)

    if uncertainty:
        return Selection(
            tuple(all_tests), True,
            "nem követhető fájltípus vagy útvonal: " + ", ".join(uncertainty[:4]),
            tuple(uncertainty),
        )
    if source_files >= 20:
        return Selection(tuple(all_tests), True, "nagy, legalább 20 forrásfájlos átalakítás")

    if modules:
        try:
            for module, consumers in _dependento_tesztek(root, modules).items():
                consumers.update(direct_consumers.get(module, ()))
                if not consumers:
                    return Selection(
                        tuple(all_tests), True,
                        f"a forrás importgráfjában nincs biztos tesztfogyasztó: {module}",
                    )
                selected.update(consumers & all_set)
        except ValueError as exc:
            return Selection(tuple(all_tests), True, f"az AST-importgráf bizonytalan: {exc}")
    if qml_paths:
        qml_tests: set[str] = set()
        for qml_path in qml_paths:
            file_name = Path(qml_path).name
            pattern = re.compile(
                rf"\b{re.escape(Path(qml_path).stem)}(?:\.qml)?\b"
            )
            for test in all_tests:
                try:
                    content = (root / test).read_text(
                        encoding="utf-8", errors="replace"
                    ).replace("\\", "/")
                except OSError:
                    continue
                if qml_path in content or file_name in content or pattern.search(content):
                    qml_tests.add(test)
                elif file_name == "Main.qml" and test.startswith(
                    "tests/app/qml_functional/"
                ):
                    # A közös QML-funkcionális conftest minden ilyen tesztnek
                    # Main.qml-t tölt be a `qml_app` fixture-ben.
                    qml_tests.add(test)
                elif file_name == "Main.qml" and test.startswith("tests/app/"):
                    if "qml_app" in content:
                        qml_tests.add(test)
        if not qml_tests:
            return Selection(
                tuple(all_tests), True,
                "QML-változáshoz nem található közvetlen fogyasztóteszt",
            )
        selected.update(qml_tests)
        actionable = True

    if not actionable:
        # Ismert dokumentáció-/változásnapló-diffnél csak a rövid füstkészlet
        # marad. Minden más útvonal fent már teljes készletre esett vissza.
        return Selection(tuple(smoke), False, "csak dokumentáció/verzió/változásnapló")
    if len(selected) > MAX_SELECTED_FRACTION * len(all_tests):
        return Selection(tuple(all_tests), True, "a kiválasztás a készlet több mint 60%-át érinti")
    return Selection(tuple(sorted(selected)), False, "érintett tesztek + füstkészlet")


def meresi_idok(root: Path, path: Path | None = None) -> dict[str, float]:
    """A commitolt tesztfutás-idők; hibás vagy hiányzó táblánál üres."""
    file = path or (root / "scripts" / "teszt_idok.json")
    try:
        adat = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(adat, dict):
            return {}
        return {
            str(name).replace("\\", "/"): float(seconds)
            for name, seconds in adat.items()
            if isinstance(seconds, (int, float)) and seconds >= 0
        }
    except (OSError, ValueError, TypeError):
        return {}


def tervezz_darabokat(
    files: Sequence[str],
    timings: Mapping[str, float],
    *,
    teljes: bool,
    cel_masodperc: int = TARGET_SHARD_SECONDS,
    max_darab: int = MAX_SHARDS,
) -> ShardPlan:
    """A futásidők összege vagy mérés híján a fájlszám alapján tervez."""
    all_files = tuple(sorted(set(files)))
    non_app = tuple(path for path in all_files if not path.startswith("tests/app/"))
    has_non_app_total = teljes and bool(non_app) and NON_APP_UNIT in timings
    ismert_nem_app = sum(
        float(timings[path]) for path in non_app if path in timings
    )
    known = sum(float(timings[path]) for path in all_files if path in timings)
    if has_non_app_total:
        # A teljes készlet mért ideje továbbra is beleszámít a darabszámba,
        # de az egyedi nem-app fájlok idejét nem mérte külön.
        known += max(0.0, float(timings[NON_APP_UNIT]) - ismert_nem_app)
    unknown = tuple(path for path in all_files if path not in timings)
    becslendo = tuple(
        path for path in unknown
        if not (has_non_app_total and path in non_app)
    )
    measured_file_times = sorted(
        float(value)
        for name, value in timings.items()
        if name in all_files and value > 0
    )
    if measured_file_times:
        # A futtató is a mért idők 90. percentilisével tervez a hiányzó
        # fájloknak (#4825); ezt a darabszámnál is beszámítjuk, különben egy
        # néhány mért + sok új fájlos PR túl kevés darabra oszlana.
        ismeretlen_becsles = measured_file_times[
            min(len(measured_file_times) - 1, int(len(measured_file_times) * 0.9))
        ]
        becsult_osszeg = known + len(becslendo) * ismeretlen_becsles
        count = math.ceil(becsult_osszeg / cel_masodperc)
    elif known > 0:
        count = math.ceil((known + len(becslendo)) / cel_masodperc)
    else:
        # A teljesen mérés nélküli repónál nincs miből időt becsülni.
        count = math.ceil(len(all_files) / FILES_PER_SHARD_WITHOUT_TIMINGS)
    count = max(1, min(max_darab, count))
    too_long = tuple(
        path for path in all_files
        if path in timings and float(timings[path]) > cel_masodperc
    )
    return ShardPlan(count, known, unknown, too_long)


def ci_shard_plan(
    files: Sequence[str],
    timings: Mapping[str, float],
    *,
    teljes: bool,
    main_run: bool,
) -> ShardPlan:
    """PR-en legfeljebb 20, mainen a meglévő 16 futtatóval tervez."""
    return tervezz_darabokat(
        files,
        timings,
        teljes=teljes,
        max_darab=MAX_SHARDS if main_run else MAX_PR_SHARDS,
    )


def _shard_units(
    files: Sequence[str], timings: Mapping[str, float], *, teljes: bool
) -> tuple[list[str], dict[str, float]]:
    all_files = tuple(sorted(set(files)))
    non_app = tuple(path for path in all_files if not path.startswith("tests/app/"))
    missing_non_app = tuple(path for path in non_app if path not in timings)
    has_non_app_total = (
        teljes and bool(non_app) and NON_APP_UNIT in timings
    )
    measured = [
        float(timings[name])
        for name in all_files
        if name in timings and float(timings[name]) > 0
    ]
    measured.sort()
    fallback = (
        measured[min(len(measured) - 1, int(len(measured) * 0.9))]
        if measured else 1.0
    )
    non_app_known = sum(
        float(timings[name]) for name in non_app if name in timings
    )
    non_app_fajl_atlag = (
        max(0.0, float(timings[NON_APP_UNIT]) - non_app_known)
        / len(missing_non_app)
        if has_non_app_total and missing_non_app else 0.0
    )
    weights: dict[str, float] = {}
    for unit in all_files:
        if unit in timings:
            weights[unit] = float(timings[unit])
        elif has_non_app_total and unit in missing_non_app:
            # A fájlokat külön futtatjuk, ezért az összesített mérést az
            # egyedi, még nem mért fájlok között osztjuk szét a kiosztáshoz.
            weights[unit] = non_app_fajl_atlag
        else:
            weights[unit] = fallback
    return list(all_files), weights


def darab_fajljai(
    files: Sequence[str],
    timings: Mapping[str, float],
    shard: int,
    count: int,
    *,
    teljes: bool = False,
) -> tuple[str, ...]:
    """Mohó, leghosszabb-először kiosztás; az egységek pontosan egyszer futnak."""
    if count < 1 or not 1 <= shard <= count:
        raise ValueError("a darabszám és a darab sorszáma érvénytelen")
    units, weights = _shard_units(files, timings, teljes=teljes)
    loads = [0.0] * count
    assigned: list[list[str]] = [[] for _ in range(count)]
    for unit in sorted(units, key=lambda name: (-weights[name], name)):
        target = min(range(count), key=lambda idx: (loads[idx], idx))
        assigned[target].append(unit)
        loads[target] += weights[unit]
    return tuple(sorted(assigned[shard - 1]))


def _changed_files(root: Path, base: str, head: str) -> list[str] | None:
    if not base or not head:
        return None
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            cwd=root, check=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _version_only_for_refs(root: Path, base: str, head: str) -> bool:
    if not base or not head:
        return False
    try:
        old = subprocess.run(
            ["git", "show", f"{base}:pyproject.toml"], cwd=root,
            check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
        ).stdout
        new = subprocess.run(
            ["git", "show", f"{head}:pyproject.toml"], cwd=root,
            check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return False
    return pyproject_only_version_changed(old, new)


def _selection_for_cli(root: Path, *, base: str, head: str, force_full: bool) -> Selection:
    changed = None if force_full else _changed_files(root, base, head)
    return select_tests(
        root, changed,
        pyproject_version_only=_version_only_for_refs(root, base, head),
        force_full=force_full,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_ROOT)
    parser.add_argument("--darabszam", action="store_true", help="GitHub Actions matrix-kimenet")
    parser.add_argument("--lista", type=Path, help="a kiválasztott tesztek JSON-listájának kiírása")
    parser.add_argument(
        "--windows", action="store_true",
        help="PR-en csak a Windows-érzékeny, már kiválasztott tesztek",
    )
    parser.add_argument("--alap", default=os.environ.get("PICASAPY_ERINTETT_ALAP", ""))
    parser.add_argument("--fej", default=os.environ.get("GITHUB_SHA", "HEAD"))
    parser.add_argument(
        "--teljes", action="store_true",
        default=os.environ.get("PICASAPY_TESZT_TELJES") == "1",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    selection = _selection_for_cli(
        root, base=args.alap, head=args.fej, force_full=args.teljes
    )
    if args.windows:
        selection = windows_only_tests(root, selection, force_full=args.teljes)
    timings = meresi_idok(root)
    plan = (
        ci_shard_plan(
            selection.fajlok,
            timings,
            teljes=selection.teljes,
            main_run=args.teljes,
        )
        if selection.fajlok else ShardPlan(0, 0.0, (), ())
    )

    if args.darabszam:
        output = os.environ.get("GITHUB_OUTPUT")
        values = (
            f"darabok={[*range(1, plan.darabszam + 1)]}\n"
            f"darabszam={plan.darabszam}\n"
        )
        if output:
            with open(output, "a", encoding="utf-8") as stream:
                stream.write(values)
        else:
            print(values, end="")
        print(
            f"Tesztek: {len(selection.fajlok)} fájl; teljes={selection.teljes}; "
            f"ok={selection.indok}; ismert idő={plan.mert_masodperc:.1f}s; "
            f"mérés nélküli={len(plan.ismeretlen_fajlok)}; "
            f"darab={plan.darabszam}.",
            file=sys.stderr,
        )
        return 0

    if args.lista:
        args.lista.write_text(
            json.dumps(
                {"fajlok": selection.fajlok, "teljes": selection.teljes,
                 "indok": selection.indok},
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        print(
            f"{len(selection.fajlok)} tesztfájl; teljes={selection.teljes}; "
            f"{selection.indok}",
            file=sys.stderr,
        )
        return 0
    parser.error("add meg a --darabszam vagy --lista kapcsolót")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
