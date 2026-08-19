"""A kiadás-kapu hook próbasora.

Két vaklárma-osztály élesben derült ki (2026-08-19), mindkettőt őrzi teszt:
  * listázó `git tag` alak (pl. --sort) blokkolódott;
  * a parancs SZÖVEGÉBEN előforduló említés (fájlírás, grep) blokkolódott.
"""

import importlib.util
import pathlib

import pytest

_UT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "hooks" / "release_kapu.py"
_spec = importlib.util.spec_from_file_location("release_kapu", _UT)
kapu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapu)


BLOKKOLANDO = [
    "gh release create v0.7.77 --title x --notes y",
    "gh release edit v0.7.76 --notes z",
    "git tag -a v0.7.77 -m 'kiadás'",
    "git tag v0.7.77",
    "cd /x && git tag -s v1 -m a",
    "git push origin v0.7.77",
    "git push --tags",
    "git push origin main --follow-tags",
    "git push origin refs/tags/v0.7.77",
]

ATENGEDENDO = [
    # listázó/olvasó alakok — ezek buktak el élesben
    "git tag --sort=-creatordate | head -5",
    "git tag -n --format='%(refname)'",
    "git tag --list",
    "git tag -l 'v*'",
    "git tag",
    "git tag -d proba",
    "git tag --contains abc123",
    # normál munka
    "git push origin main",
    "git push -u origin fix/123-valami",
    "gh release list",
    "gh release view v0.7.76",
    "ls -la",
    # feloldóval
    "PICASA_KIADAS=engedelyezve git tag -a v0.7.77 -m kiadás",
    "PICASA_KIADAS=engedelyezve gh release create v0.7.77",
]

# Említés != futtatás: ezek a parancsok csak SZÖVEGKÉNT tartalmazzák a mintát.
EMLITES = [
    "grep -rn 'git tag' scripts/",
    "echo 'a git tag létrehozása kiadás' >> jegyzet.md",
    "python3 -c \"print('gh release create a kiadás lépése')\"",
    "rg --files-with-matches 'gh release create'",
]


@pytest.mark.parametrize("cmd", BLOKKOLANDO)
def test_kiadasi_lepes_blokkolodik(cmd, tmp_path):
    assert kapu._blokkolando(cmd, str(tmp_path)) is not None


@pytest.mark.parametrize("cmd", ATENGEDENDO)
def test_artalmatlan_parancs_atmegy(cmd, tmp_path):
    assert kapu._blokkolando(cmd, str(tmp_path)) is None


@pytest.mark.parametrize("cmd", EMLITES)
def test_puszta_emlites_nem_blokkol(cmd, tmp_path):
    assert kapu._blokkolando(cmd, str(tmp_path)) is None


@pytest.mark.parametrize("bemenet", ["nem json", "", '{"tool_input": null}'])
def test_fail_open_rossz_bemenetre(bemenet, monkeypatch, capsys):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(bemenet))
    assert kapu.main() == 0


def test_verzioemelo_push_blokkolodik(monkeypatch, tmp_path):
    """A valódi kiadási út: verzióemelés + push -> a CI kiadást csinál belőle."""
    monkeypatch.setattr(kapu, "_verziot_emel", lambda cwd: True)
    indok = kapu._blokkolando("git push origin main", str(tmp_path))
    assert indok is not None and "verzióemelést" in indok


def test_verzioemeles_nelkuli_push_atmegy(monkeypatch, tmp_path):
    monkeypatch.setattr(kapu, "_verziot_emel", lambda cwd: False)
    assert kapu._blokkolando("git push origin main", str(tmp_path)) is None


def test_verzioemelo_pr_merge_blokkolodik(monkeypatch, tmp_path):
    monkeypatch.setattr(kapu, "_pr_verziot_emel", lambda cmd, cwd: True)
    indok = kapu._blokkolando("gh pr merge 974 --squash", str(tmp_path))
    assert indok is not None and "PR beolvasztása" in indok


def test_verzio_sor_felismerese():
    """A pyproject-diff verziósorát ismerje fel, a függőség-változást ne."""
    verzio_diff = '--- a/pyproject.toml\n+++ b/pyproject.toml\n-version = "0.8.0"\n+version = "0.8.1"\n'
    fuggoseg_diff = '--- a/pyproject.toml\n+++ b/pyproject.toml\n+  "numpy>=2.0",\n'
    assert kapu._VERZIO_SOR.search(verzio_diff)
    assert not kapu._VERZIO_SOR.search(fuggoseg_diff)
