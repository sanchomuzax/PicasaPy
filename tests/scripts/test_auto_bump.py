"""A merge-kori verzióemelés (#1127, 4. lépés)."""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

_UT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "auto_bump.py"
_spec = importlib.util.spec_from_file_location("auto_bump", _UT)
auto_bump = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(auto_bump)


@pytest.mark.parametrize(
    ("bemenet", "vart"),
    [("0.8.28", "0.8.29"), ("1.0.0", "1.0.1"), ("0.9.99", "0.9.100")],
)
def test_a_patch_szam_emelkedik(bemenet, vart):
    assert auto_bump.kovetkezo_verzio(bemenet) == vart


@pytest.mark.parametrize("rossz", ["0.8", "v0.8.28", "0.8.x", ""])
def test_nem_semver_alakra_hibat_dob(rossz):
    """⚠️ Némán rossz verziót írni rosszabb, mint megállni."""
    with pytest.raises(ValueError):
        auto_bump.kovetkezo_verzio(rossz)


def test_a_pyproject_verzioja_emelkedik(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "x"\nversion = "0.8.28"\n', encoding="utf-8")

    regi, uj = auto_bump.emeld_a_pyprojectet(p)

    assert (regi, uj) == ("0.8.28", "0.8.29")
    assert 'version = "0.8.29"' in p.read_text(encoding="utf-8")


def test_a_changelog_cime_lezarodik(tmp_path):
    c = tmp_path / "CHANGELOG.md"
    c.write_text(
        "# Változásnapló\n\n## [Nem kiadott]\n\n- valami\n\n## [0.8.28] – 2026-08-20\n",
        encoding="utf-8",
    )

    assert auto_bump.zard_le_a_changelogot(c, "0.8.29", "2026-08-21") is True
    szoveg = c.read_text(encoding="utf-8")
    assert "## [0.8.29] – 2026-08-21" in szoveg
    assert "Nem kiadott" not in szoveg
    assert "## [0.8.28] – 2026-08-20" in szoveg, "a régi szakasz nem sérülhet"


def test_kiadatlan_szakasz_nelkul_sem_hibazik(tmp_path):
    """Tisztán belső változáshoz nem muszáj felhasználói mondatot írni."""
    c = tmp_path / "CHANGELOG.md"
    c.write_text("# Változásnapló\n\n## [0.8.28] – 2026-08-20\n", encoding="utf-8")

    assert auto_bump.zard_le_a_changelogot(c, "0.8.29", "2026-08-21") is False
    assert "0.8.29" not in c.read_text(encoding="utf-8")


class TestWorkflowBekotes:
    """A workflow-fájlt semmilyen teszt nem futtatja — ez az őr szól, ha
    a bekötés némán kikerül (#1127)."""

    @staticmethod
    def _release_yaml():
        yaml = pytest.importorskip("yaml")
        ut = _UT.parents[1] / ".github" / "workflows" / "release.yml"
        return yaml.safe_load(ut.read_text(encoding="utf-8")), ut.read_text(
            encoding="utf-8"
        )

    def test_a_verzioemeles_a_kiadas_ELOTT_fut(self):
        """Fordított sorrendben a friss verzióhoz nem születne kiadás."""
        adat, _ = self._release_yaml()
        nevek = [
            str(lepes.get("name", ""))
            for lepes in adat["jobs"]["release"]["steps"]
        ]
        emeles = next(i for i, n in enumerate(nevek) if "Verzióemelés" in n)
        kiadas = next(i for i, n in enumerate(nevek) if "Release létrehozása" in n)
        assert emeles < kiadas

    def test_csak_MAR_KIADOTT_verziora_emel(self):
        """⚠️ A rekurzió-korlát: enélkül minden push emelne, örökre."""
        _, szoveg = self._release_yaml()
        assert "gh release view" in szoveg, (
            "nincs ellenőrzés, hogy a jelenlegi verzió ki van-e adva — "
            "az emelés önmagát hívná újra, végtelenül"
        )


class TestNemAkaszthatjaMegAKiadast:
    """A verzióemelés bukása NEM viheti el a kiadást (#1165).

    ⚠️ Az első változat közvetlenül a `main`-re pusholt, és a védett ág
    elutasította („Required status check is expected"). Ettől a LÉPÉS
    elbukott, és a rákövetkező kiadási lépés `skipped` lett — vagyis a
    verzióemelés hibája MEGAKADÁLYOZTA a kiadást. Rosszabb volt, mint
    amit javítani akart.
    """

    @staticmethod
    def _release():
        yaml = pytest.importorskip("yaml")
        ut = _UT.parents[1] / ".github" / "workflows" / "release.yml"
        return yaml.safe_load(ut.read_text(encoding="utf-8")), ut.read_text(
            encoding="utf-8"
        )

    def test_a_bump_lepes_nem_fatalis(self):
        adat, _ = self._release()
        bump = [
            lepes
            for lepes in adat["jobs"]["release"]["steps"]
            if lepes.get("id") == "bump"
        ]
        assert bump, "nincs `bump` azonosítójú lépés"
        assert bump[0].get("continue-on-error") is True, (
            "a verzióemelés bukása elviszi a kiadást — pontosan ez történt"
        )

    def test_nem_pusholunk_kozvetlenul_a_mainre(self):
        """A védett ág ezt elutasítja; ágra + PR-re megy."""
        _, szoveg = self._release()
        assert "HEAD:main" not in szoveg, (
            "közvetlen push a védett `main`-re — a hook elutasítja"
        )


def test_a_workflow_nyithat_PR_t():
    """A `gh pr create` külön jogosultságot kér (#1166).

    ⚠️ A `contents: write` NEM elég: a PR-nyitás `Resource not accessible by
    integration`-nel bukott, és a verzióemelés csak a naplóban látszott —
    a felhasználó számára úgy tűnt, nem történt semmi."""
    yaml = pytest.importorskip("yaml")
    ut = _UT.parents[1] / ".github" / "workflows" / "release.yml"
    adat = yaml.safe_load(ut.read_text(encoding="utf-8"))
    assert adat.get("permissions", {}).get("pull-requests") == "write"
