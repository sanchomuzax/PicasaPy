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


def test_a_mutmut_futtatas_a_run_tests_helyet_foglalja(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
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

    def helyfoglalas(**_kwargs):
        esemenyek.append("hely-foglalva")
        return hely

    monkeypatch.setattr(run_tests, "_varj_szabad_helyre", helyfoglalas)
    monkeypatch.setattr(
        run_tests, "_futtat_mutmut", lambda: esemenyek.append("mutmut") or 0
    )

    def engedd_el(_hely):
        esemenyek.append("hely-felszabaditva")

    monkeypatch.setattr(run_tests, "_engedd_el_a_helyet", engedd_el)

    assert run_tests.main(["--mutmut"]) == 0
    assert esemenyek == ["hely-foglalva", "mutmut", "hely-felszabaditva"]
