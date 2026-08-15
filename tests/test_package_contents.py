"""A csomagtartalom-ellenőrző MAGA is tesztelt — #646, #651/2.

A tényleges ellenőrzés a CI-ben fut, a FELÉPÍTETT wheelen
(`scripts/check_package_contents.py`), mert csak ott mérhető a kimenet.
Ezek a tesztek azt őrzik, hogy maga az ellenőrző működik: egy hiányzó
fájlt észrevesz, a szándékos kivételt viszont nem jelenti hibának.

Egy néma ellenőrző rosszabb a semminél — azt hinnénk, védve vagyunk.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_package_contents import (  # noqa: E402
    INTENTIONALLY_EXCLUDED,
    is_intentionally_excluded,
    main,
    missing_from_wheel,
    source_data_files,
    stale_build_artifacts,
)


def _wheel(path: Path, names) -> Path:
    """Szintetikus wheel a megadott bejegyzésekkel."""
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, b"x")
        archive.writestr("picasapy-9.9.9.dist-info/METADATA", b"Name: picasapy")
    return path


class TestTheSourceInventory:
    def test_it_finds_the_icon_set(self):
        """A #646 egyik áldozata: a `qml/PicasaPy/icons/` ikonkészlet."""
        icons = [f for f in source_data_files() if "/icons/" in f]

        assert len(icons) >= 20, "az ikonkészletet nem találja a leltár"
        assert all(f.endswith(".svg") for f in icons)

    def test_it_finds_the_webexport_templates(self):
        """A másik áldozat: a webexport sablonjai."""
        templates = [f for f in source_data_files() if "webexport/templates" in f]

        assert len(templates) >= 10

    def test_it_ignores_python_sources_and_caches(self):
        files = source_data_files()

        assert not [f for f in files if f.endswith(".py")]
        assert not [f for f in files if "__pycache__" in f]


class TestItCatchesAMissingFile:
    def test_a_complete_wheel_passes(self, tmp_path):
        wheel = _wheel(tmp_path / "full.whl", source_data_files())

        assert missing_from_wheel(wheel) == []

    def test_a_dropped_icon_directory_is_reported(self, tmp_path):
        """Pontosan a #646 hibája, szintetikusan előállítva."""
        without_icons = {f for f in source_data_files() if "/icons/" not in f}
        wheel = _wheel(tmp_path / "partial.whl", without_icons)

        missing = missing_from_wheel(wheel)

        assert missing, "a hiányzó ikonkészletet nem vette észre"
        assert all("/icons/" in name for name in missing)

    def test_the_exit_code_is_nonzero_when_something_is_missing(self, tmp_path):
        """A CI erre a kilépési kódra épül — enélkül némán zöld maradna."""
        without_icons = {f for f in source_data_files() if "/icons/" not in f}
        wheel = _wheel(tmp_path / "partial.whl", without_icons)

        assert main([str(wheel)]) == 1

    def test_a_missing_wheel_file_is_an_error_not_a_pass(self, tmp_path):
        assert main([str(tmp_path / "nincs-ilyen.whl")]) == 1


class TestStaleBuildArtifacts:
    """#655: a korábbi `build/` vagy `*.egg-info` hamis zöldet adhat."""

    def test_a_clean_tree_reports_nothing(self, tmp_path):
        assert stale_build_artifacts(tmp_path) == []

    def test_a_leftover_build_directory_is_reported(self, tmp_path):
        (tmp_path / "build").mkdir()

        assert stale_build_artifacts(tmp_path) == ["build/"]

    def test_a_leftover_egg_info_under_src_is_reported(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "picasapy.egg-info").mkdir()

        found = stale_build_artifacts(tmp_path)

        assert found == ["src/picasapy.egg-info/"]

    def test_a_leftover_egg_info_at_the_root_is_reported(self, tmp_path):
        (tmp_path / "picasapy.egg-info").mkdir()

        assert stale_build_artifacts(tmp_path) == ["picasapy.egg-info/"]

    def test_both_kinds_are_reported_together(self, tmp_path):
        (tmp_path / "build").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "picasapy.egg-info").mkdir()

        found = stale_build_artifacts(tmp_path)

        assert found == ["build/", "src/picasapy.egg-info/"]

    def test_main_still_passes_with_a_complete_wheel_despite_the_warning(
        self, tmp_path, capsys
    ):
        """A figyelmeztetés nem hazug bukás — a valós repón fut, nem törli.

        Ez a teszt a MEGLÉVŐ (jelen esetben tiszta) munkafán fut: azt
        őrzi, hogy egy teljes wheel mellett a kilépési kód 0 marad, akkor
        is, ha a `main()` időközben belefut a `stale_build_artifacts()`
        hívásba.
        """
        wheel = _wheel(tmp_path / "full.whl", source_data_files())

        assert main([str(wheel)]) == 0


class TestIntentionalExclusions:
    def test_the_translation_source_is_excluded_with_a_reason(self):
        reason = is_intentionally_excluded("picasapy/app/i18n/picasapy_hu.ts")

        assert reason, "a .ts fordítási forrás kivétele indoklás nélkül maradt"

    def test_every_exclusion_carries_a_reason(self):
        """A kivétel tudatos döntés — indoklás nélkül nem vehető fel."""
        for pattern, reason in INTENTIONALLY_EXCLUDED:
            assert reason.strip(), f"{pattern} kivétele indoklás nélkül van"

    def test_a_runtime_file_is_not_silently_excluded(self):
        assert is_intentionally_excluded("picasapy/app/qml/Main.qml") is None


class TestThePackagingDeclaration:
    """Gyors, korai jelzés — a lassú, mérvadó ellenőrzés a CI-ben fut."""

    def test_the_manifest_grafts_the_package_tree(self):
        manifest = (Path(__file__).resolve().parents[1] / "MANIFEST.in").read_text(
            encoding="utf-8"
        )

        assert "graft src/picasapy" in manifest, (
            "a MANIFEST.in graft-ja adja a 'minden új alkönyvtár magától "
            "bekerül' garanciát (#646)"
        )

    def test_include_package_data_is_on(self):
        import tomllib

        root = Path(__file__).resolve().parents[1]
        with (root / "pyproject.toml").open("rb") as handle:
            config = tomllib.load(handle)

        assert config["tool"]["setuptools"]["include-package-data"] is True, (
            "enélkül a MANIFEST.in csak az sdist-re hat, a wheelre nem"
        )

    def test_no_itemised_package_data_whitelist_returned(self):
        """A MÓDSZERT őrzi: a tételes lista volt a #646 gyökéroka.

        Ha valaki visszateszi, ez azonnal piros — akkor is, ha épp
        történetesen teljes."""
        import tomllib

        root = Path(__file__).resolve().parents[1]
        with (root / "pyproject.toml").open("rb") as handle:
            config = tomllib.load(handle)

        assert "package-data" not in config["tool"]["setuptools"], (
            "a tételes package-data whitelist csendben hagy ki új "
            "alkönyvtárakat — a MANIFEST.in graft-ja váltja ki"
        )

    def test_the_declared_setuptools_minimum_covers_the_pep639_license_string(self):
        """A #652 őre: a deklarált setuptools-minimum ne hazudjon.

        A `[project] license = "GPL-3.0-or-later"` a PEP 639 szerinti
        string-alak — ezt a setuptools csak 77.0.0-tól érti. Alacsonyabb
        deklarált minimum mellett `--no-build-isolation`-nel a build
        `project.license must be valid exactly by one definition` hibával
        elbukik, build-izolációval viszont észrevétlen marad (az mindig a
        legfrissebb setuptoolst húzza be) — ezért ez a teszt a `pyproject
        .toml` SZÁMÁT nézi, nem a build kimenetét.
        """
        import re
        import tomllib

        root = Path(__file__).resolve().parents[1]
        with (root / "pyproject.toml").open("rb") as handle:
            config = tomllib.load(handle)

        requires = config["build-system"]["requires"]
        setuptools_requirement = next(
            (entry for entry in requires if entry.startswith("setuptools")), None
        )
        assert setuptools_requirement is not None, (
            "nincs setuptools a build-system.requires listában"
        )

        match = re.fullmatch(r"setuptools>=(\d+)(?:\.\d+)*", setuptools_requirement)
        assert match, f"váratlan alak: {setuptools_requirement!r}"
        assert int(match.group(1)) >= 77, (
            f"{setuptools_requirement!r} — a PEP 639 license-string csak "
            "setuptools>=77-től működik (#652)"
        )


@pytest.mark.parametrize(
    "expected",
    [
        "picasapy/app/qml/PicasaPy/icons/deritofeny.svg",
        "picasapy/app/qml/PicasaPy/Gpu/PointFilter.frag",
        "picasapy/webexport/templates/feher/index.tpl",
    ],
)
def test_the_previously_dropped_files_are_in_the_inventory(expected):
    """A #646 három reprezentatív áldozata — a leltárnak látnia kell őket."""
    assert expected in source_data_files()
