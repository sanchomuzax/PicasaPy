"""A kiadás-kapu hook próbasora.

Két vaklárma-osztály élesben derült ki (2026-08-19), mindkettőt őrzi teszt:
  * listázó `git tag` alak (pl. --sort) blokkolódott;
  * a parancs SZÖVEGÉBEN előforduló említés (fájlírás, grep) blokkolódott.
"""

import importlib.util
import io
import json
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


def test_cd_utan_a_celmappat_hasznalja(tmp_path):
    """A parancs `cd`-je dönti el, hol nézzük a verziót — nem a session mappája.

    Éles próbán bukott meg (2026-08-19): a hook a főmappát kapta, ott nincs
    eltérés, és a verzióemelő push némán átment.
    """
    cel = tmp_path / "munkamasolat"
    cel.mkdir()
    cmd = f"cd {cel} && git push origin main"
    assert kapu._munkakonyvtar(cmd, str(tmp_path)) == str(cel)


def test_cd_nelkul_a_session_mappaja(tmp_path):
    assert kapu._munkakonyvtar("git push origin main", str(tmp_path)) == str(tmp_path)


def test_nemletezo_cd_cel_eseten_a_session_mappaja(tmp_path):
    cmd = "cd /nincs/ilyen/mappa && git push origin main"
    assert kapu._munkakonyvtar(cmd, str(tmp_path)) == str(tmp_path)


def test_tobb_cd_eseten_az_utolso_szamit(tmp_path):
    elso, masodik = tmp_path / "a", tmp_path / "b"
    elso.mkdir()
    masodik.mkdir()
    cmd = f"cd {elso}; echo x; cd {masodik} && git push"
    assert kapu._munkakonyvtar(cmd, str(tmp_path)) == str(masodik)


def test_relativ_cd_a_session_mappajahoz_kepest(tmp_path):
    (tmp_path / "alkonyvtar").mkdir()
    cmd = "cd alkonyvtar && git push origin main"
    assert kapu._munkakonyvtar(cmd, str(tmp_path)) == str(tmp_path / "alkonyvtar")


def test_verzio_sor_felismerese():
    """A pyproject-diff verziósorát ismerje fel, a függőség-változást ne."""
    verzio_diff = '--- a/pyproject.toml\n+++ b/pyproject.toml\n-version = "0.8.0"\n+version = "0.8.1"\n'
    fuggoseg_diff = '--- a/pyproject.toml\n+++ b/pyproject.toml\n+  "numpy>=2.0",\n'
    assert kapu._VERZIO_SOR.search(verzio_diff)
    assert not kapu._VERZIO_SOR.search(fuggoseg_diff)


class TestVizsgaltFaKiirasa:
    """A blokkoló üzenet MONDJA MEG, mit vizsgált (#1113).

    ⚠️ A kapu a MUNKAMENET cwd-jében diffel, ami `cd` nélküli parancsnál a
    KÖZÖS főmásolat — nem a pusholó session worktree-je. Ha a főmásolat épp
    verzióemelő ágon áll, a kapu MINDEN session pushát blokkolja, és az
    üzenet olyan ágról szól, amihez a blokkolt félnek semmi köze.

    2026-08-20-án egy munkamenet ezért futott neki négyszer a SAJÁT ágának,
    ami végig üres volt. Ez az őr azt védi, hogy a válasz megnevezze a
    vizsgált fát — enélkül a tünet és az ok külön munkamenetnél marad.
    """

    def test_a_fa_es_az_ag_a_kimenetben(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr(
            kapu.sys, "stdin", io.StringIO(
                json.dumps({
                    "tool_input": {"command": "gh release create v9.9.9"},
                    "cwd": str(tmp_path),
                })
            )
        )
        assert kapu.main() == 2
        hiba = capsys.readouterr().err
        assert "a vizsgált fa:" in hiba
        assert str(tmp_path) in hiba
        assert "ág:" in hiba
        assert "#1113" in hiba, "a jegyszám nélkül nem találja meg a magyarázatot"


class TestUtvonalFeloldas:
    """#1056: a `cd` célját FEL kell oldani, mielőtt a session-mappához
    fűznénk.

    Élesben (2026-08-20) egy MÁSIK repóba szánt feltöltés blokkolódott a
    PicasaPy verzióemelésére hivatkozva — pedig a célrepóban nincs is
    `pyproject.toml`. Az ok: a tildés útvonal nem abszolút, ezért előbb
    hozzáfűztük a munkakönyvtárhoz (`.../PicasaPy/~/Documents/...`), és az
    `expanduser` ezen már nem segített. A hook így a HÍVÓ mappájában
    diffelt.
    """

    def test_tildes_cd_a_home_ala_old_fel(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        cel = tmp_path / "Documents" / "masik-repo"
        cel.mkdir(parents=True)
        cmd = "cd ~/Documents/masik-repo && git push origin main"
        assert kapu._munkakonyvtar(cmd, "/tmp") == str(cel)

    def test_puszta_tilde_is_feloldodik(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        assert kapu._munkakonyvtar("cd ~ && git push", "/tmp") == str(tmp_path)

    def test_idezojeles_tildes_cd(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        cel = tmp_path / "a b"
        cel.mkdir()
        cmd = 'cd "~/a b" && git push origin main'
        assert kapu._munkakonyvtar(cmd, "/tmp") == str(cel)

    def test_ujsor_utani_cd_is_szamit(self, tmp_path):
        """A `_CD` mintában a `^` nem MULTILINE, ezért egy több soros
        parancsban az újsorral kezdődő `cd` nem illeszkedett."""
        cel = tmp_path / "masik"
        cel.mkdir()
        cmd = f"echo elso\ncd {cel} && git push origin main"
        assert kapu._munkakonyvtar(cmd, str(tmp_path)) == str(cel)


def _git(cwd, *argv):
    import subprocess

    subprocess.run(["git", *argv], cwd=cwd, check=True, capture_output=True,
                   text=True, encoding="utf-8", errors="replace")


def _mini_repo(tmp_path):
    """Kis git-repó `origin/main`-nel és `pyproject.toml`-lal."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "a@b.c")
    _git(repo, "config", "user.name", "Teszt")
    (repo / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    _git(repo, "add", "pyproject.toml")
    _git(repo, "commit", "-qm", "alap")
    _git(repo, "branch", "-f", "origin/main")   # helyi álnév a diffhez
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


class TestCommitolatlanVerzioemeles:
    """A kapu a PARANCS ELŐTT fut, ezért `git diff origin/main...HEAD` a
    commit előtti állapotot látja.

    Élesben (2026-09-04) ezért ment ki egy verzióemelés a ceremónia előtt: a
    push egyetlen parancsban addolt, commitolt és tolt fel. Külön commitba
    téve UGYANAZ a kapu azonnal blokkolt — a különbség csak a parancs
    tagolása volt.
    """

    def test_commit_es_push_egy_parancsban_BLOKKOL(self, tmp_path):
        repo = _mini_repo(tmp_path)
        (repo / "pyproject.toml").write_text('version = "0.2.0"\n', encoding="utf-8")
        cmd = (f"cd {repo} && git add pyproject.toml && "
               "git commit -m x && git push origin main")
        fa = kapu._munkakonyvtar(cmd, str(tmp_path))
        indok = kapu._blokkolando(cmd, fa)
        assert indok is not None and "verzióemelést" in indok

    def test_puszta_push_piszkos_munkafaval_ATMEGY(self, tmp_path):
        """A kapu nem büntetheti az őszinteséget: `git commit` NÉLKÜL a
        munkafában heverő verzióemelés nem tud kimenni, tehát nincs mit
        blokkolni. Enélkül az a fejlesztő is elakadna, aki épp a verziót
        szerkeszti, miközben egy MÁS ágat tol fel."""
        repo = _mini_repo(tmp_path)
        (repo / "pyproject.toml").write_text('version = "0.2.0"\n', encoding="utf-8")
        cmd = f"cd {repo} && git push origin main"
        fa = kapu._munkakonyvtar(cmd, str(tmp_path))
        assert kapu._blokkolando(cmd, fa) is None

    def test_commit_es_push_verzioemeles_NELKUL_atmegy(self, tmp_path):
        repo = _mini_repo(tmp_path)
        (repo / "olvasslak.md").write_text("szia\n", encoding="utf-8")
        cmd = (f"cd {repo} && git add -A && git commit -m x && "
               "git push origin main")
        fa = kapu._munkakonyvtar(cmd, str(tmp_path))
        assert kapu._blokkolando(cmd, fa) is None
