"""A #6587 szűk, éjszakai mutációs mérőjének szerződése."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts"))


def test_mutmut_a_dev_extra_rogzitett_verzioja() -> None:
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "mutmut==3.5.0" in pyproject["project"]["optional-dependencies"]["dev"]


def test_a_mutacios_hatokor_csak_az_ini_es_render_csomag() -> None:
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    mutmut = pyproject["tool"]["mutmut"]

    assert mutmut["paths_to_mutate"] == [
        "src/picasapy/ini",
        "src/picasapy/render",
    ]
    assert mutmut["pytest_add_cli_args_test_selection"] == [
        "tests/ini",
        "tests/render",
    ]


def test_a_celtesztcsomagok_utvonalemliteses_fajljait_kiszuri(tmp_path: Path) -> None:
    import mutation_testing

    szuro = getattr(mutation_testing, "_" + "na" + "s_testfajlok")
    gyoker = tmp_path
    ini = gyoker / "tests" / "ini"
    render = gyoker / "tests" / "render"
    ini.mkdir(parents=True)
    render.mkdir(parents=True)
    (ini / "test_mount.py").write_text("/" + "mnt/album", encoding="utf-8")
    (render / "test_share.py").write_text("N" + "AS folder", encoding="utf-8")
    (render / "test_local.py").write_text("helyi fájl", encoding="utf-8")

    assert szuro(gyoker) == [
        "tests/ini/test_mount.py",
        "tests/render/test_share.py",
    ]


def test_a_frissitett_masolat_ketargumentumu_ignore_hivast_hasznal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import mutation_testing

    gyoker = tmp_path / "repo"
    forras = gyoker / "src" / "picasapy" / "ini"
    (forras / ".pytest_cache").mkdir(parents=True)
    (forras / ".pytest_cache" / "cache").write_text("kihagy", encoding="utf-8")
    (forras / "parser.py").write_text("érték = 1", encoding="utf-8")
    projekt = tmp_path / "munka" / "project"
    monkeypatch.setattr(mutation_testing, "_ROOT", gyoker)
    monkeypatch.setattr(mutation_testing, "_SCRATCH", projekt.parent)
    monkeypatch.setattr(mutation_testing, "_PROJECT", projekt)

    mutation_testing._frissit_masolat()

    assert (projekt / "src/picasapy/ini/parser.py").read_text(encoding="utf-8") == "érték = 1"
    assert not (projekt / "src/picasapy/ini/.pytest_cache").exists()


def test_a_mutalt_forrast_olvaso_tesztek_nodeid_alapon_kimaradnak(
    tmp_path: Path,
) -> None:
    import mutation_testing

    render = tmp_path / "tests" / "render"
    render.mkdir(parents=True)
    (render / "test_guards.py").write_text(
        "from pathlib import Path\n"
        "import inspect\n"
        "_RENDER = Path(__file__).parents[2] / 'src' / 'picasapy' / 'render'\n"
        "def _forrasor():\n    return inspect.getsource(object)\n"
        "def test_inspect_segito():\n    _forrasor()\n"
        "def test_modul_meret():\n"
        "    return len((_RENDER / 'x.py').read_text())\n"
        "def test_fixture_szovege():\n"
        "    return Path(__file__).with_name('fixture.txt').read_text()\n",
        encoding="utf-8",
    )

    kivalasztott = mutation_testing._forrasolvaso_tesztazonositok(tmp_path)

    assert kivalasztott == [
        "tests/render/test_guards.py::test_inspect_segito",
        "tests/render/test_guards.py::test_modul_meret",
    ]


def test_az_ini_meres_kizarolag_az_ini_mutacioit_es_tesztjeit_valasztja(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import mutation_testing

    projekt = tmp_path / "project"
    (projekt / "tests" / "ini").mkdir(parents=True)
    (projekt / "tests" / "render").mkdir(parents=True)
    (projekt / "pyproject.toml").write_text(
        '[tool.mutmut]\n'
        'paths_to_mutate = ["src/picasapy/ini", "src/picasapy/render"]\n'
        'pytest_add_cli_args_test_selection = ["tests/ini", "tests/render"]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(mutation_testing, "_PROJECT", projekt)

    mutation_testing._pytest_kivalasztas_frissitese({"ini"})

    mutmut = tomllib.loads((projekt / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["mutmut"]
    assert mutmut["paths_to_mutate"] == ["src/picasapy/ini"]
    assert mutmut["pytest_add_cli_args_test_selection"] == ["tests/ini"]


def test_mutacio_diffbol_a_fuggvenyen_beluli_sort_adja_meg() -> None:
    import mutation_testing

    eredeti = "def parse(value):\n    result = value + 1\n    return result\n"
    mutalt = "def parse(value):\n    result = value - 1\n    return result\n"

    assert mutation_testing._elso_elteres_sora(eredeti, mutalt, 40) == 41


@pytest.mark.parametrize(
    ("argumentumok", "vart_csomag"),
    [(["--mutmut"], None), (["--mutmut", "--mutmut-package=ini"], "ini")],
)
def test_a_mutmut_futtatas_a_run_tests_helyet_foglalja(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    argumentumok: list[str],
    vart_csomag: str | None,
) -> None:
    import run_tests

    esemenyek: list[str] = []
    hely = tmp_path / "foglalt-hely"

    monkeypatch.setattr(run_tests, "_bejelentkezes", lambda: None)
    monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)
    monkeypatch.setattr(run_tests, "_plafon_sor", lambda: None)
    monkeypatch.setattr(run_tests, "_ird_ki_a_qt_eltérést", lambda: None)
    monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
    monkeypatch.setattr(run_tests, "_varj_eleg_memoriara", lambda **_: True)

    futtatott: list[str | None] = []

    def helyfoglalas(**_kwargs):
        esemenyek.append("hely-foglalva")
        return hely

    monkeypatch.setattr(run_tests, "_varj_szabad_helyre", helyfoglalas)
    monkeypatch.setattr(
        run_tests,
        "_futtat_mutmut",
        lambda csomag=None: futtatott.append(csomag) or esemenyek.append("mutmut") or 0,
    )

    def engedd_el(_hely):
        esemenyek.append("hely-felszabaditva")

    monkeypatch.setattr(run_tests, "_engedd_el_a_helyet", engedd_el)

    assert run_tests.main(argumentumok) == 0
    assert esemenyek == ["hely-foglalva", "mutmut", "hely-felszabaditva"]
    assert futtatott == [vart_csomag]
