"""A CI változás-elemzésének próbasora (#3298).

A döntés — lefut-e a tesztmátrix — eddig a munkafolyamat YAML-jében élt,
beágyazott shellként, próba nélkül. Ez a fájl a kiemelt
``scripts/ci_valtozas.py``-t méri VALÓDI git-tárolókon: a merge-base-es
alapválasztást is, nem csak a fájlnév-szűrést.

Amit ez a próbasor NEM mér: a GitHub Actions kifejezés-nyelvét (a
``needs.valtozas.outputs.kod == 'true'`` feltételeket), és azt, hogy a
munkafolyamat tényleg ezt a szkriptet hívja-e — az utóbbira külön állítás
van a fájl végén, forrás-szinten.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[1]
SZKRIPT = GYOKER / "scripts" / "ci_valtozas.py"


def _modul():
    spec = importlib.util.spec_from_file_location("ci_valtozas", SZKRIPT)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    sys.modules["ci_valtozas"] = modul   # a dataclass a modul-bejegyzést nézi
    spec.loader.exec_module(modul)
    return modul


ci_valtozas = _modul()


def _git(tar: Path, *argumentumok: str) -> str:
    return subprocess.run(
        ["git", "-C", str(tar), *argumentumok],
        check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.strip()


@pytest.fixture()
def tarolo(tmp_path: Path) -> Path:
    """Üres git-tároló egy `main` ággal és egy induló committal."""
    tar = tmp_path / "repo"
    tar.mkdir()
    _git(tar, "init", "-q", "-b", "main")
    _git(tar, "config", "user.email", "t@t")
    _git(tar, "config", "user.name", "T")
    (tar / "README.md").write_text("alap\n", encoding="utf-8")
    (tar / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    (tar / "src").mkdir()
    (tar / "src" / "picasapy").mkdir()
    (tar / "src" / "picasapy" / "__init__.py").write_text(
        '__version__ = "0.1.0"\n', encoding="utf-8")
    (tar / "docs").mkdir()
    (tar / "docs" / "lap.md").write_text("lap\n", encoding="utf-8")
    _git(tar, "add", "-A")
    _git(tar, "commit", "-q", "-m", "alap")
    return tar


def _agat_nyit(tar: Path, nev: str) -> None:
    _git(tar, "checkout", "-q", "-b", nev)


def _commit(tar: Path, uzenet: str) -> str:
    _git(tar, "add", "-A")
    _git(tar, "commit", "-q", "-m", uzenet)
    return _git(tar, "rev-parse", "HEAD")


def _dontes(tar: Path, alap: str, fej: str) -> ci_valtozas.Dontes:
    return ci_valtozas.elemezd(str(tar), alap, fej)


# --- az öt mérendő eset (a jegy törzse) -------------------------------------

def test_csak_docs_es_md_eseten_kimarad_a_matrix(tarolo: Path) -> None:
    alap = _git(tarolo, "rev-parse", "HEAD")
    _agat_nyit(tarolo, "ag")
    (tarolo / "docs" / "uj.md").write_text("uj\n", encoding="utf-8")
    (tarolo / "README.md").write_text("alap\nmeg egy sor\n", encoding="utf-8")
    fej = _commit(tarolo, "csak dokumentacio")
    d = _dontes(tarolo, alap, fej)
    assert d.kod is False
    assert d.docs is True


def test_csak_a_verziosor_valtozott_kimarad(tarolo: Path) -> None:
    alap = _git(tarolo, "rev-parse", "HEAD")
    _agat_nyit(tarolo, "ag")
    (tarolo / "pyproject.toml").write_text('version = "0.1.1"\n', encoding="utf-8")
    (tarolo / "src" / "picasapy" / "__init__.py").write_text(
        '__version__ = "0.1.1"\n', encoding="utf-8")
    fej = _commit(tarolo, "verzioemeles")
    d = _dontes(tarolo, alap, fej)
    assert d.kod is False, "a puszta verziósor nem kód"
    assert d.docs is False


def test_egyetlen_src_fajl_a_dokumentacio_mellett_futtat(tarolo: Path) -> None:
    alap = _git(tarolo, "rev-parse", "HEAD")
    _agat_nyit(tarolo, "ag")
    (tarolo / "docs" / "uj.md").write_text("uj\n", encoding="utf-8")
    (tarolo / "src" / "picasapy" / "modul.py").write_text("x = 1\n", encoding="utf-8")
    fej = _commit(tarolo, "kod + dokumentacio")
    d = _dontes(tarolo, alap, fej)
    assert d.kod is True
    assert d.docs is True


def test_verziofajlban_erdemi_valtozas_is_futtat(tarolo: Path) -> None:
    """A verzió-kivétel nem csempészhet be kódot."""
    alap = _git(tarolo, "rev-parse", "HEAD")
    _agat_nyit(tarolo, "ag")
    (tarolo / "pyproject.toml").write_text(
        'version = "0.1.1"\n[tool.ruff]\nline-length = 100\n', encoding="utf-8")
    fej = _commit(tarolo, "verzio + beallitas")
    d = _dontes(tarolo, alap, fej)
    assert d.kod is True


def test_nincs_kozos_elod_eseten_teljes_kor(tarolo: Path, tmp_path: Path) -> None:
    """Sekély klón / átírt történet: fail-safe, fut a mátrix."""
    _agat_nyit(tarolo, "ag")
    (tarolo / "docs" / "uj.md").write_text("uj\n", encoding="utf-8")
    fej = _commit(tarolo, "csak dokumentacio")
    # Gyökértelen ág: nincs közös előd a `fej`-jel.
    _git(tarolo, "checkout", "-q", "--orphan", "idegen")
    _git(tarolo, "rm", "-rq", "--cached", ".")
    (tarolo / "mas.txt").write_text("mas\n", encoding="utf-8")
    idegen = _commit(tarolo, "idegen gyoker")
    d = _dontes(tarolo, idegen, fej)
    assert d.kod is True
    assert "közös előd" in d.indoklas


def test_base_ag_elorement_de_az_ag_csak_dokumentacio(tarolo: Path) -> None:
    """A #3288 valódi esete: az elágazás helyéhez mérünk, nem a main tipjéhez."""
    elagazas = _git(tarolo, "rev-parse", "HEAD")
    _agat_nyit(tarolo, "ag")
    (tarolo / "docs" / "uj.md").write_text("uj\n", encoding="utf-8")
    fej = _commit(tarolo, "csak dokumentacio")
    # Közben a main előremegy egy KÓD-commit-tal.
    _git(tarolo, "checkout", "-q", "main")
    (tarolo / "src" / "picasapy" / "idegen.py").write_text("y = 2\n", encoding="utf-8")
    main_tipp = _commit(tarolo, "idegen kod a main-en")
    assert main_tipp != elagazas
    d = _dontes(tarolo, main_tipp, fej)
    assert d.kod is False, "az idegen commit fájljai nem a PR változásai"


# --- keret: a döntés tényleg a szkriptből jön -------------------------------

def test_a_munkafolyamat_a_szkriptet_hivja() -> None:
    yml = (GYOKER / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "scripts/ci_valtozas.py" in yml
    # A beágyazott shell-döntés maradékai nem élhetnek tovább mellette.
    assert "van_erdemi_valtozas()" not in yml


def test_a_szkript_kimondja_mit_nem_mer() -> None:
    forras = SZKRIPT.read_text(encoding="utf-8")
    assert "NEM MÉRI" in forras
    for tema in ("bináris", "átnevez", "almodul"):
        assert tema in ci_valtozas.NEM_MERT, f"hiányzik a kimondott korlát: {tema}"


def test_a_cli_a_github_output_ba_ir(tarolo: Path, tmp_path: Path) -> None:
    alap = _git(tarolo, "rev-parse", "HEAD")
    _agat_nyit(tarolo, "ag")
    (tarolo / "docs" / "uj.md").write_text("uj\n", encoding="utf-8")
    fej = _commit(tarolo, "csak dokumentacio")
    kimenet = tmp_path / "out.txt"
    kornyezet = {
        **os.environ,
        "BASE": alap, "HEAD": fej, "ELOZO": "", "MOSTANI": fej,
        "GITHUB_OUTPUT": str(kimenet),
    }
    futas = subprocess.run(
        [sys.executable, str(SZKRIPT), "--tarolo", str(tarolo)],
        check=True, capture_output=True, text=True, env=kornyezet,
        encoding="utf-8", errors="replace",
    )
    sorok = kimenet.read_text(encoding="utf-8").splitlines()
    assert "kod=false" in sorok
    assert "docs=true" in sorok
    assert "Változott fájlok" in futas.stdout


def test_push_esemeny_az_elozo_allapothoz_mer(tarolo: Path, tmp_path: Path) -> None:
    """`main`-re érkező pushnál nincs `base.sha`, de van `event.before`."""
    elozo = _git(tarolo, "rev-parse", "HEAD")
    (tarolo / "docs" / "uj.md").write_text("uj\n", encoding="utf-8")
    mostani = _commit(tarolo, "docs a main-en")
    kimenet = tmp_path / "out.txt"
    kornyezet = {
        **os.environ,
        "BASE": "", "HEAD": "", "ELOZO": elozo, "MOSTANI": mostani,
        "GITHUB_OUTPUT": str(kimenet),
    }
    subprocess.run(
        [sys.executable, str(SZKRIPT), "--tarolo", str(tarolo)],
        check=True, capture_output=True, text=True, env=kornyezet,
        encoding="utf-8", errors="replace",
    )
    assert "kod=false" in kimenet.read_text(encoding="utf-8").splitlines()


def test_elozmeny_nelkuli_push_eseten_teljes_kor(tarolo: Path, tmp_path: Path) -> None:
    mostani = _git(tarolo, "rev-parse", "HEAD")
    kimenet = tmp_path / "out.txt"
    kornyezet = {
        **os.environ,
        "BASE": "", "HEAD": "", "MOSTANI": mostani,
        "ELOZO": "0" * 40,
        "GITHUB_OUTPUT": str(kimenet),
    }
    subprocess.run(
        [sys.executable, str(SZKRIPT), "--tarolo", str(tarolo)],
        check=True, capture_output=True, text=True, env=kornyezet,
        encoding="utf-8", errors="replace",
    )
    assert "kod=true" in kimenet.read_text(encoding="utf-8").splitlines()


def test_a_cli_CP1252_kimeneten_sem_bukik_el(tarolo: Path, tmp_path: Path) -> None:
    """#2077 hibaosztály: a magyar üzenetben van `ő`, ami a Windows
    alapértelmezett `cp1252`-jében nem ábrázolható — a szkript ilyenkor a
    SAJÁT kiírásán hasalna el, és a CI valódi leletnek látná.
    """
    alap = _git(tarolo, "rev-parse", "HEAD")
    _agat_nyit(tarolo, "ag")
    (tarolo / "docs" / "uj.md").write_text("uj\n", encoding="utf-8")
    fej = _commit(tarolo, "csak dokumentacio")
    kimenet = tmp_path / "out.txt"
    kornyezet = {
        **os.environ,
        "BASE": alap, "HEAD": fej, "ELOZO": "", "MOSTANI": fej,
        "GITHUB_OUTPUT": str(kimenet),
        "PYTHONIOENCODING": "cp1252",
    }
    futas = subprocess.run(
        [sys.executable, str(SZKRIPT), "--tarolo", str(tarolo)],
        capture_output=True, text=True, env=kornyezet,
        encoding="utf-8", errors="replace",
    )
    assert futas.returncode == 0, futas.stderr
    assert "kod=false" in kimenet.read_text(encoding="utf-8").splitlines()
