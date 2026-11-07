"""A nightly tesztsorrend-mérés diagnosztikája (#6590)."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import run_tests  # noqa: E402
import pytest_random_order  # noqa: E402


def test_a_rendes_futtatas_kikapcsolja_a_pytest_randomlyt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    parancsok: list[list[str]] = []

    class Eredmeny:
        returncode = 0

    def rogzit(parancs, **_kwargs):
        parancsok.append(list(parancs))
        return Eredmeny()

    monkeypatch.setattr(run_tests, "_run", rogzit)
    monkeypatch.setattr(run_tests, "_memoria_burok", lambda: [])

    assert run_tests._run_pytest(
        ["tests/test_pelda.py"], 30, cov=False, basetemp=tmp_path
    ) == 0

    pytest_args = parancsok[0]
    assert "no:randomly" in pytest_args
    assert "--randomly-seed" not in pytest_args


def test_az_ejszakai_futas_a_maggal_es_a_sorrendjelentovel_inditja_a_pluginet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    parancsok: list[list[str]] = []

    class Eredmeny:
        returncode = 0

    def rogzit(parancs, **_kwargs):
        parancsok.append(list(parancs))
        return Eredmeny()

    monkeypatch.setattr(run_tests, "_run", rogzit)
    monkeypatch.setattr(run_tests, "_memoria_burok", lambda: [])

    assert run_tests._run_pytest(
        ["tests/test_pelda.py"],
        30,
        cov=False,
        basetemp=tmp_path,
        randomly_seed=6590,
    ) == 0

    pytest_args = parancsok[0]
    assert "no:randomly" not in pytest_args
    assert pytest_args[pytest_args.index("randomly") - 1] == "-p"
    assert pytest_args[pytest_args.index("--randomly-seed") + 1] == "6590"
    assert "scripts.pytest_random_order" in pytest_args
    assert run_tests._random_mag_argumentum(
        ["--nightly-random-seed", "6590"]
    ) == 6590
    with pytest.raises(SystemExit, match="egész szám"):
        run_tests._random_mag_argumentum(["--nightly-random-seed", "x"])


@pytest.mark.parametrize(
    ("kwargs", "kell"),
    [
        ({}, False),
        ({"randomly_seed": 6590}, True),
        ({"randomly_seed": 6590, "fixed_order": True,
          "order_targets": {"tests/test_pelda.py::test_bukik"}}, True),
    ],
)
def test_a_diagnosztikai_futas_kiirja_a_bukott_tesztek_nevet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kwargs: dict, kell: bool
) -> None:
    # A besorolás a `FAILED <nodeid>` összegzősorból olvas; a `-rs` csak a
    # kihagyást írja ki, így az első éjszakai futás minden sorrendfüggést
    # „nem azonosítható" tesztnévvel jelentett (#6590).
    parancsok: list[list[str]] = []

    class Eredmeny:
        returncode = 0

    def rogzit(parancs, **_kwargs):
        parancsok.append(list(parancs))
        return Eredmeny()

    monkeypatch.setattr(run_tests, "_run", rogzit)
    monkeypatch.setattr(run_tests, "_memoria_burok", lambda: [])

    run_tests._run_pytest(
        ["tests/test_pelda.py"], 30, cov=False, basetemp=tmp_path, **kwargs
    )

    assert ("-rfE" in parancsok[0]) is kell


def test_a_visszatero_bukas_sorrendfugges_ingadozas_vagy_valodi_hiba_lehet() -> None:
    sorrendfuggo = {"tests/test_x.py::test_bukik"}
    ingadozo = {"tests/test_y.py::test_ingadozik"}
    valodi = {"tests/test_z.py::test_hibas"}

    besorolas = run_tests._random_besorolas(
        sorrendfuggo | ingadozo | valodi,
        sorrendfuggo | valodi,
        valodi,
        fix_sorrend_zold=True,
    )

    assert besorolas == {
        "tests/test_x.py::test_bukik": "sorrendfüggés",
        "tests/test_y.py::test_ingadozik": "ingadozás (#999/#3265)",
        "tests/test_z.py::test_hibas": "valódi hiba",
    }


def test_a_sorrendriport_kulon_sorba_irhato_es_feldolgozhato(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parok = [("test_file.py::test_bukik", "test_file.py::test_elod")]

    pytest_random_order._write_order_pairs(parok)

    kimenet = capsys.readouterr().out
    assert kimenet.startswith("\nPICASAPY_RANDOM_ORDER\t")
    assert run_tests._random_sorrend_parok(kimenet) == {
        "test_file.py::test_bukik": "test_file.py::test_elod"
    }


def test_az_ejszakai_bukas_azonos_magon_ujra_es_fix_sorrendben_is_fut(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hivasok: list[tuple[int | None, bool]] = []
    kimenetek = iter(
        [
            (
                "FAILED tests/test_pelda.py::test_bukik - AssertionError\n"
                "PICASAPY_RANDOM_ORDER\ttests/test_pelda.py::test_bukik\t"
                "tests/test_pelda.py::test_allapotot_hagy",
                1,
            ),
            (
                "FAILED tests/test_pelda.py::test_bukik - AssertionError\n"
                "PICASAPY_RANDOM_ORDER\ttests/test_pelda.py::test_bukik\t"
                "tests/test_pelda.py::test_allapotot_hagy",
                1,
            ),
            ("", 0),
        ]
    )

    def rogzit_pytest(
        args,
        _timeout_s,
        *,
        randomly_seed=None,
        fixed_order=False,
        **_kwargs,
    ):
        hivasok.append((randomly_seed, fixed_order))
        kimenet, kod = next(kimenetek)
        run_tests._KIMENET[" ".join(args)] = kimenet
        return kod

    monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
    monkeypatch.setattr(run_tests, "_run_pytest", rogzit_pytest)
    monkeypatch.setattr(run_tests, "_APP_FILE_TIMEOUT_S", 30)
    run_tests._KIMENET.clear()
    teszt = tmp_path / "tests" / "test_pelda.py"

    bukasok = run_tests._tesztfajlok_sorosan(
        [teszt], cov=False, basetemp=tmp_path / ".bt", randomly_seed=6590
    )

    # windowson a futtató a platform elválasztójával adja vissza az utat
    assert [(nev.replace("\\", "/"), kod) for nev, kod in bukasok] == [
        ("tests/test_pelda.py", 1)
    ]
    assert hivasok == [(6590, False), (6590, False), (None, True)]
    kimenet = capsys.readouterr().out
    assert "Sorrendfüggés" in kimenet
    assert (
        "tests/test_pelda.py::test_allapotot_hagy -> "
        "tests/test_pelda.py::test_bukik"
    ) in kimenet


def test_a_pytest_randomly_a_dev_extraban_es_a_schedule_magbekotesevel_szerepel() -> None:
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev = pyproject["project"]["optional-dependencies"]["dev"]
    assert any(dependency.startswith("pytest-randomly") for dependency in dev)

    ci = (_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    reusable = (
        _ROOT / ".github" / "workflows" / "teszt-darabok.yml"
    ).read_text(encoding="utf-8")
    assert "random_seed:" in ci
    assert "secrets.randbelow" in ci
    assert "random_seed:" in reusable
    assert "--nightly-random-seed" in reusable


def test_a_csupasz_pytest_hivas_nem_kever() -> None:
    """A pytest-randomly csak a futtató kifejezett `-p randomly`-jával fut."""
    import tomllib
    from pathlib import Path

    adat = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )
    addopts = adat["tool"]["pytest"]["ini_options"]["addopts"]
    assert addopts[addopts.index("no:randomly") - 1] == "-p"
