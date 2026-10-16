"""A helyi és a CI Qt-verziója azonos lehessen (#4834).

A verzió EGY helyen él (`packaging/ci-constraints.txt`); ezt olvassa a CI, a
`scripts/ci_venv.py` és a `scripts/run_tests.py`. A munkafolyamat-őr
szövegből olvas, nem `yaml`-lal (a CI-környezetben nincs PyYAML, és az
`importorskip` ott némán kihagyná az őrt).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_GYOKER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_GYOKER / "scripts"))

import ci_kornyezet  # noqa: E402
import ci_venv  # noqa: E402
import run_tests  # noqa: E402

_CONSTRAINT = _GYOKER / "packaging" / "ci-constraints.txt"
_MUNKAFOLYAMATOK = _GYOKER / ".github" / "workflows"


# --- a fájl formátuma ------------------------------------------------------


def test_a_constraint_fajl_csak_pontos_rogzitest_tartalmaz():
    rogzites = ci_kornyezet.olvasd_a_rogzitest(_CONSTRAINT.read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d+\.\d+\.\d+", rogzites["pyside6"])
    # a Qt-csomagok és a shiboken együtt járnak
    assert {rogzites[n] for n in ("pyside6", "pyside6-essentials", "pyside6-addons", "shiboken6")} == {
        rogzites["pyside6"]
    }


def test_a_rogzites_megfer_a_pyproject_tartomanyaval():
    import tomllib

    adat = tomllib.loads((_GYOKER / "pyproject.toml").read_text(encoding="utf-8"))
    assert any(d.startswith("PySide6<") for d in adat["project"]["dependencies"])
    ci_fo = int(ci_kornyezet.ci_verzio().split(".")[1])
    felso = next(
        int(m.group(1))
        for d in adat["project"]["dependencies"]
        if (m := re.match(r"PySide6<6\.(\d+)", d))
    )
    assert ci_fo < felso, "a rögzített verzió a pyproject tartományán kívül van"


def test_rossz_sor_hangosan_elbukik():
    with pytest.raises(ValueError):
        ci_kornyezet.olvasd_a_rogzitest("PySide6>=6.8\n")
    assert ci_kornyezet.olvasd_a_rogzitest("# komment\n\nPySide6_Addons==6.1.0 # x\n") == {
        "pyside6-addons": "6.1.0"
    }


def test_hianyzo_fajl_nem_dob(tmp_path):
    assert ci_kornyezet.ci_verzio(fajl=tmp_path / "nincs.txt") is None


# --- az összevetés ---------------------------------------------------------


def test_hasonlit_harom_allapot():
    assert ci_kornyezet.hasonlit("6.11.2", "6.11.2") == ci_kornyezet.EGYEZIK
    assert ci_kornyezet.hasonlit("6.8.2", "6.11.2") == ci_kornyezet.ELTER
    assert ci_kornyezet.hasonlit(None, "6.11.2") == ci_kornyezet.HIANYZIK


def test_egyezesnel_nincs_figyelmeztetes():
    assert ci_kornyezet.figyelmeztetes_sorai("6.11.2", "6.11.2") == []


def test_elteresnel_latható_a_figyelmeztetes_es_a_parancs():
    szoveg = "\n".join(ci_kornyezet.figyelmeztetes_sorai("6.8.2", "6.11.2"))
    assert "6.8.2" in szoveg and "6.11.2" in szoveg
    assert "scripts/ci_venv.py" in szoveg and "run_tests.py" in szoveg


def test_nincs_pyside6_is_figyelmeztet():
    szoveg = "\n".join(ci_kornyezet.figyelmeztetes_sorai(None, "6.11.2"))
    assert "nincs PySide6" in szoveg


def test_a_futtato_elejen_es_vegen_is_jelez_de_nem_all_meg(monkeypatch, capsys):
    monkeypatch.setattr(ci_kornyezet, "futo_verzio", lambda csomag="PySide6": "1.0.0")
    monkeypatch.setattr(ci_kornyezet, "ci_verzio", lambda csomag="PySide6", fajl=None: "2.0.0")
    run_tests._ird_ki_a_qt_eltérést()
    assert "NEM CI-AZONOS" in capsys.readouterr().out


def test_a_futtato_egyezesnel_nem_zajong(monkeypatch, capsys):
    monkeypatch.setattr(ci_kornyezet, "futo_verzio", lambda csomag="PySide6": "2.0.0")
    monkeypatch.setattr(ci_kornyezet, "ci_verzio", lambda csomag="PySide6", fajl=None: "2.0.0")
    run_tests._ird_ki_a_qt_eltérést()
    assert capsys.readouterr().out == ""


def test_a_main_a_vegen_is_kiirja_es_a_kodot_megtartja():
    forras = (_GYOKER / "scripts" / "run_tests.py").read_text(encoding="utf-8")
    main = forras[forras.index("def main("):forras.index("_NEM_APP =")]
    assert main.count("_ird_ki_a_qt_eltérést()") == 2, "a futás elején ÉS végén is kell"
    assert "return visszater" in main


# --- a ci_venv döntése (valódi pip nélkül) ---------------------------------


@pytest.mark.parametrize(
    "van,venv,ci,ujra,vart",
    [
        (False, None, "6.11.2", False, True),   # nincs venv
        (True, "6.11.2", "6.11.2", False, False),  # egyezik -> marad
        (True, "6.8.2", "6.11.2", False, True),  # eltér
        (True, None, "6.11.2", False, True),     # sérült (nincs PySide6)
        (True, "6.11.2", "6.11.2", True, True),  # --ujra
    ],
)
def test_kell_ujraepiteni(van, venv, ci, ujra, vart):
    assert ci_venv.kell_ujraepiteni(van, venv, ci, ujra) is vart


def test_keszits_csak_szukseg_eseten_telepit(tmp_path):
    hivasok = []
    python = ci_venv.venv_python(tmp_path / "v")

    def telepito(hely, py):
        hivasok.append(hely)
        python.parent.mkdir(parents=True, exist_ok=True)
        python.write_text("")

    ci = ci_kornyezet.ci_verzio()
    p, epult = ci_venv.keszits(tmp_path / "v", telepito=telepito, venv_verzio_olvaso=lambda _: ci)
    assert epult and len(hivasok) == 1
    p, epult = ci_venv.keszits(tmp_path / "v", telepito=telepito, venv_verzio_olvaso=lambda _: ci)
    assert not epult and len(hivasok) == 1
    _, epult = ci_venv.keszits(tmp_path / "v", telepito=telepito, venv_verzio_olvaso=lambda _: "0.0.1")
    assert epult and len(hivasok) == 2


# --- a CI a constraintet használja ----------------------------------------

@pytest.mark.parametrize("nev", ["ci.yml", "teszt-darabok.yml", "indulas-meres.yml"])
def test_a_tesztet_futtato_munkafolyamat_constraintet_hasznal(nev):
    szoveg = (_MUNKAFOLYAMATOK / nev).read_text(encoding="utf-8")
    sorok = [
        s.split("#", 1)[0]
        for s in szoveg.splitlines()
        if "pip install" in s.split("#", 1)[0]
        and "print_dependencies.py" in s
        and "--dev" not in s
        and "--apt" not in s
    ]
    assert sorok, f"{nev}: nincs futásidejű pip install sor"
    for sor in sorok:
        assert "-c packaging/ci-constraints.txt" in sor, f"{nev}: constraint nélkül: {sor.strip()}"


def test_a_ci_venv_helye_gitignore_ban():
    assert ".venv-ci" in (_GYOKER / ".gitignore").read_text(encoding="utf-8")
