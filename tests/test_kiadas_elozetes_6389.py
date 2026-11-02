"""A kiadás előzetesként születik, és csak a teljes csomag után nyilvános (#6389).

Az 1.0.12 már jelezte az 1.0.13-at, de a „Frissítés most" után a letöltés
elbukott: a Release-munkafolyamat a kiadást azonnal nyilvánosként hozta
létre, a windowsos csomagot és a `SHA256SUMS`-t a Package csak percekkel
később töltötte fel. A régi programok a `releases/latest` végpontot nézik,
ami az előzetes (prerelease) kiadást nem adja vissza; így a kiadás addig
rejtve marad, amíg a Package a végén nyilvánossá és legújabbá nem teszi.

Szövegből olvas, nem `yaml`-lal: a CI-környezetben nincs PyYAML.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_PACKAGE = _GYOKER / ".github" / "workflows" / "package.yml"

sys.path.insert(0, str(_GYOKER / "scripts"))

from ensure_release import ensure_release  # noqa: E402


def _job(nev: str) -> str:
    szoveg = _PACKAGE.read_text(encoding="utf-8")
    eleje = re.search(rf"^  {re.escape(nev)}:\n", szoveg, re.M)
    assert eleje, f"nincs {nev} job a package.yml-ben"
    vege = re.search(r"^  [A-Za-z0-9_-]+:\n", szoveg[eleje.end() :], re.M)
    return szoveg[eleje.end() : eleje.end() + vege.start()] if vege else szoveg[eleje.end() :]


def _lepesek(job: str) -> list[str]:
    return re.split(r"^      - ", job, flags=re.M)[1:]


def test_a_kiadas_elozeteskent_jon_letre():
    hivasok: list[list[str]] = []

    def gh(args: list[str]) -> subprocess.CompletedProcess[str]:
        hivasok.append(list(args))
        kod = 1 if "view" in args else 0
        return subprocess.CompletedProcess(args, kod, stdout="", stderr="release not found")

    assert (
        ensure_release(
            version="1.0.15",
            target="abc1234",
            repo="sanchomuzax/PicasaPy",
            runner=gh,
            sleeper=lambda _s: None,
            attempts=1,
        )
        == 0
    )
    create = next(h for h in hivasok if "create" in h)
    assert "--prerelease" in create, (
        "a kiadás azonnal nyilvános: a régi programok a csomag feltöltése "
        "előtt felajánlják, és a letöltés elbukik"
    )


def test_a_package_az_elozetes_kiadast_is_megtalalja():
    for nev in ("build-and-upload", "windows-telepito"):
        job = _job(nev)
        assert "gh release list" in job and "--exclude-drafts" in job, (
            f"{nev}: a tagot a `gh release view` legújabb kiadásából veszi, "
            "ami az előzetes kiadást nem látja, így a régit csomagolná"
        )
        assert not re.search(r"gh release view --repo \"\$GITHUB_REPOSITORY\" --json tagName", job), (
            f"{nev}: maradt tag nélküli `gh release view` a tag feloldásában"
        )


def test_a_kiadas_a_feltoltes_utan_lesz_nyilvanos_es_legujabb():
    lepesek = _lepesek(_job("windows-telepito"))
    feltoltes = next(
        i for i, s in enumerate(lepesek) if s.startswith("name: A telepítő feltöltése a kiadásra")
    )
    nyilvanos = [
        i for i, s in enumerate(lepesek) if "gh release edit" in s and "--prerelease=false" in s
    ]
    assert nyilvanos, "nincs lépés, ami a kiadást nyilvánossá teszi"
    i = nyilvanos[0]
    assert i > feltoltes, "a kiadás a windowsos csomag feltöltése előtt lenne nyilvános"
    lepes = lepesek[i]
    assert "--latest" in lepes, "a nyilvánossá tett kiadás nem lesz a legújabb"
    assert "steps.tag.outputs.skip != 'true'" in lepes
    assert "github.event_name != 'pull_request'" in lepes
