"""A run_tests csak a kapott listát futtassa, fájlonként darabolva (#4922)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import run_tests  # noqa: E402


def test_a_fajllista_jsonbol_olvassa_a_fajlokat_es_a_teljes_jelzot(tmp_path: Path) -> None:
    teszt = tmp_path / "tests/test_pelda.py"
    teszt.parent.mkdir()
    teszt.write_text("def test_pelda(): pass\n", encoding="utf-8")
    lista = tmp_path / "lista.json"
    lista.write_text(
        json.dumps({"fajlok": ["tests/test_pelda.py"], "teljes": False,
                    "indok": "próba"}),
        encoding="utf-8",
    )

    fajlok, teljes, indok = run_tests._olvas_fajllista(lista, root=tmp_path)

    assert fajlok == ["tests/test_pelda.py"]
    assert teljes is False
    assert indok == "próba"


def test_teljes_futas_a_nem_app_fajlokat_is_kulon_egysegre_oszt() -> None:
    fajlok = ["tests/test_alpha.py", "tests/app/test_beta.py"]

    assert run_tests._fajlokbol_egysegek(fajlok) == sorted(fajlok)


def test_reszleges_futas_minden_kivalasztott_fajlt_kulon_egysegre_oszt() -> None:
    fajlok = ["tests/test_alpha.py", "tests/app/test_beta.py"]

    assert run_tests._fajlokbol_egysegek(fajlok) == sorted(fajlok)


def test_a_teljes_futas_a_nem_app_fajlokat_kulon_inditja(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    inditasok: list[list[str]] = []

    def fake_run(args, _timeout_s, **_kwargs):
        inditasok.append(args)
        return 0

    monkeypatch.setattr(run_tests, "_run_pytest", fake_run)
    monkeypatch.setattr(run_tests, "_PARHUZAM", 1)

    run_tests._futtat(
        False,
        tmp_path,
        fajlok=["tests/test_alpha.py", "tests/test_beta.py"],
        teljes=True,
    )

    assert inditasok == [["tests/test_alpha.py"], ["tests/test_beta.py"]]


def test_a_fajllista_nem_engedi_a_tests_konyvtaron_kivuli_utvonalat(
    tmp_path: Path,
) -> None:
    lista = tmp_path / "lista.json"
    lista.write_text(
        json.dumps({"fajlok": ["../titok.py"], "teljes": False}),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="tests/"):
        run_tests._olvas_fajllista(lista, root=tmp_path)
