"""A main minden commitja saját CI-t kap, és a csomag a kiadás commitjából
készül (#4825).

Két, 2026-10-10-én mért hiba ellen:

1. A `ci.yml` csoportkulcsa minden main-pushnál azonos volt; egy csoportban
   csak egy várakozó futás maradhat, így a köztes main-commitok futása
   lecserélődött (38044749969, 38044767026 — `cancelled`).
2. A `package.yml` minden sikeres Release-futás után a LEGUTÓBBI kiadás
   tagjét építette újra a mai lépésekkel; a `v0.9.47` tagben a mai
   `scripts/build_qm.py` még nincs (Package 38044870718).
"""

from __future__ import annotations

from pathlib import Path

import yaml

_GYOKER = Path(__file__).resolve().parents[1]
_CI = _GYOKER / ".github" / "workflows" / "ci.yml"
_PACKAGE = _GYOKER / ".github" / "workflows" / "package.yml"


def _yaml(ut: Path) -> dict:
    return yaml.safe_load(ut.read_text(encoding="utf-8"))


def test_a_main_csoportkulcsa_a_commit():
    csoport = str(_yaml(_CI)["concurrency"]["group"])
    assert "github.sha" in csoport, (
        "a main-futások csoportkulcsában nincs benne a commit — gyors "
        "beolvadáskor a köztes commitok várakozó CI-je lecserélődik"
    )
    assert "github.event_name == 'pull_request' && github.ref" in csoport, (
        "PR-en a ref maradjon a kulcs, különben az új commit nem állítja le a régi futást (#1127)"
    )


def _job_szoveg(job: dict) -> str:
    return "\n".join(
        str(lepes.get("run", "")) + str(lepes.get("if", "")) for lepes in job.get("steps") or []
    )


def _csomagolo_jobok() -> dict:
    jobok = _yaml(_PACKAGE)["jobs"]
    return {nev: jobok[nev] for nev in ("build-and-upload", "windows-telepito")}


def test_a_csomag_csak_a_futas_commitjan_keszult_kiadasbol_epul():
    for nev, job in _csomagolo_jobok().items():
        szoveg = _job_szoveg(job)
        assert "github.event.workflow_run.head_sha" in szoveg, (
            f"{nev}: a kiadás tagjét nem veti össze a Release-futás "
            "commitjával — minden main-push a régi kiadást építené újra"
        )
        assert 'echo "skip=true"' in szoveg


def test_a_windows_job_minden_lepese_tiszteli_a_kihagyast():
    job = _csomagolo_jobok()["windows-telepito"]
    lepesek = job["steps"]
    tag_index = next(i for i, lp in enumerate(lepesek) if lp.get("id") == "tag")
    hianyzo = [
        lp.get("name") or lp.get("uses")
        for lp in lepesek[tag_index + 1 :]
        if "github.event_name == 'pull_request'" != str(lp.get("if", "")).strip()
        and "steps.tag.outputs.skip != 'true'" not in str(lp.get("if", ""))
    ]
    assert not hianyzo, f"kihagyáskor is lefutna: {hianyzo}"


def test_regi_tagnel_a_qm_epites_a_tag_allapotahoz_igazodik():
    for nev, job in _csomagolo_jobok().items():
        sorok = [s for s in _job_szoveg(job).splitlines() if "python scripts/build_qm.py" in s]
        assert sorok, f"{nev}: nincs .qm-építés"
        for sor in sorok:
            assert "[ -f scripts/build_qm.py ]" in sor, (
                f"{nev}: a régi kiadási tagben nincs build_qm.py — a hívás "
                f"feltétel nélkül elbukik: {sor.strip()}"
            )
