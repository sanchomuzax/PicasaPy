"""A main minden commitja saját CI-t kap, és a csomag a kiadás commitjából
készül (#4825).

Két, 2026-10-10-én mért hiba ellen:

1. A `ci.yml` csoportkulcsa minden main-pushnál azonos volt; egy csoportban
   csak egy várakozó futás maradhat, így a köztes main-commitok futása
   lecserélődött (38044749969, 38044767026 — `cancelled`).
2. A `package.yml` minden sikeres Release-futás után a LEGUTÓBBI kiadás
   tagjét építette újra a mai lépésekkel; a `v0.9.47` tagben a mai
   `scripts/build_qm.py` még nincs (Package 38044870718).

⚠️ Szövegből olvas, nem `yaml`-lal: a CI-környezetben nincs PyYAML, és a
`importorskip` ott némán kihagyná az őrt.
"""

from __future__ import annotations

import re
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_CI = _GYOKER / ".github" / "workflows" / "ci.yml"
_PACKAGE = _GYOKER / ".github" / "workflows" / "package.yml"


def _job(nev: str) -> str:
    """A `package.yml` egy jobjának szövege (a következő jobig)."""
    szoveg = _PACKAGE.read_text(encoding="utf-8")
    eleje = re.search(rf"^  {re.escape(nev)}:\n", szoveg, re.M)
    assert eleje, f"nincs {nev} job a package.yml-ben"
    vege = re.search(r"^  [A-Za-z0-9_-]+:\n", szoveg[eleje.end() :], re.M)
    return szoveg[eleje.end() : eleje.end() + vege.start()] if vege else szoveg[eleje.end() :]


def _lepesek(job: str) -> list[str]:
    return re.split(r"^      - ", job, flags=re.M)[1:]


def test_a_main_csoportkulcsa_a_commit():
    sor = next(
        s for s in _CI.read_text(encoding="utf-8").splitlines() if s.strip().startswith("group:")
    )
    assert "github.sha" in sor, (
        "a main-futások csoportkulcsában nincs benne a commit — gyors "
        "beolvadáskor a köztes commitok várakozó CI-je lecserélődik"
    )
    assert "github.event_name == 'pull_request' && github.ref" in sor, (
        "PR-en a ref maradjon a kulcs, különben az új commit nem állítja le a régi futást (#1127)"
    )


def test_a_csomag_csak_a_futas_commitjan_keszult_kiadasbol_epul():
    for nev in ("build-and-upload", "windows-telepito"):
        job = _job(nev)
        assert "github.event.workflow_run.head_sha" in job, (
            f"{nev}: a kiadás tagjét nem veti össze a Release-futás "
            "commitjával — minden main-push a régi kiadást építené újra"
        )
        assert 'echo "skip=true"' in job


def test_a_windows_job_minden_lepese_tiszteli_a_kihagyast():
    lepesek = _lepesek(_job("windows-telepito"))
    tag = next(i for i, lp in enumerate(lepesek) if "id: tag" in lp)
    hianyzo = [
        lp.splitlines()[0]
        for lp in lepesek[tag + 1 :]
        if "steps.tag.outputs.skip != 'true'" not in lp
        and "if: github.event_name == 'pull_request'" not in lp
    ]
    assert not hianyzo, f"kihagyáskor is lefutna: {hianyzo}"


def test_regi_tagnel_a_qm_epites_a_tag_allapotahoz_igazodik():
    for nev in ("build-and-upload", "windows-telepito"):
        sorok = [s for s in _job(nev).splitlines() if "python scripts/build_qm.py" in s]
        assert sorok, f"{nev}: nincs .qm-építés"
        for sor in sorok:
            assert "[ -f scripts/build_qm.py ]" in sor, (
                f"{nev}: a régi kiadási tagben nincs build_qm.py — a hívás "
                f"feltétel nélkül elbukik: {sor.strip()}"
            )
