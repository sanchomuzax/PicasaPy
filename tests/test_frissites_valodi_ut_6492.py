"""A valódi önfrissítési próba csak feltöltött Setup után induljon (#6492)."""

from __future__ import annotations

import re
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_FRISSITES = _GYOKER / ".github/workflows/frissites-valodi-ut.yml"
_PACKAGE = _GYOKER / ".github/workflows/package.yml"
_FRISSITES_MERES = _GYOKER / "packaging/windows/csomag_meres_frissites.py"


def _job(fajl: Path, nev: str) -> str:
    szoveg = fajl.read_text(encoding="utf-8")
    eleje = re.search(rf"^  {re.escape(nev)}:\n", szoveg, re.M)
    assert eleje, f"nincs {nev} job a {fajl.name} fájlban"
    vege = re.search(r"^  [A-Za-z0-9_-]+:\n", szoveg[eleje.end() :], re.M)
    return szoveg[eleje.end() : eleje.end() + vege.start()] if vege else szoveg[eleje.end() :]


def test_a_dontes_a_package_futashoz_kotott_setup_jelolot_es_assetet_nezi():
    workflow = _FRISSITES.read_text(encoding="utf-8")
    dontes = _job(_FRISSITES, "dontes")

    assert "workflow_run.head_commit.message" not in workflow
    assert "workflow_run.conclusion" in dontes
    assert "actions/runs/" in dontes and "/artifacts" in dontes
    assert "setup-release-marker" in dontes
    assert "gh release view" in dontes and "PicasaPy-Setup-" in dontes
    assert 'grep -Fxq "$setup_nev"' in dontes
    assert "else" in dontes and "Hiányzó Setup" in dontes


def test_kezikezi_es_pull_request_inditasnal_a_dontes_atenged():
    workflow = _FRISSITES.read_text(encoding="utf-8")
    dontes = _job(_FRISSITES, "dontes")
    frissites = _job(_FRISSITES, "frissites")

    assert "EVENT_NAME: ${{ github.event_name }}" in dontes
    assert '[ "$EVENT_NAME" != "workflow_run" ]' in dontes
    assert "futtat=true" in dontes
    assert "needs: dontes" in frissites
    assert "needs.dontes.outputs.futtat == 'true'" in frissites
    assert "pull_request:" in workflow and "workflow_dispatch:" in workflow


def test_a_package_csak_a_feltoltott_setup_utani_sikeres_futashoz_ad_jelolot():
    package = _PACKAGE.read_text(encoding="utf-8")
    windows = _job(_PACKAGE, "windows-telepito")
    feltoltes = windows.index("- name: A telepítő feltöltése a kiadásra")
    nyilvanos = windows.index("- name: A kiadás nyilvánossá tétele")
    jelolo = windows.index("- name: A csomagolt Setup jelölése a próba számára")
    csatolas = windows.index("- name: A Package-futás jelölőjének csatolása")

    assert feltoltes < nyilvanos < jelolo < csatolas
    assert "steps.tag.outputs.tag" in windows[jelolo:csatolas]
    assert "steps.tag.outputs.verzio" in windows[jelolo:csatolas]
    assert "actions/upload-artifact@v4" in windows[csatolas:]
    assert "setup-release-marker" in windows[csatolas:]
    assert "steps.tag.outputs.skip != 'true'" in windows[jelolo:]
    assert "github.event_name != 'pull_request'" in windows[jelolo:]
    assert "PicasaPy-Setup-${{ steps.tag.outputs.verzio }}.exe" in package


def test_a_valodi_proba_kepe_a_jelzoablakot_menti_es_a_kiadasba_kerul():
    workflow_job = _job(_FRISSITES, "frissites")
    release_job = _job(_FRISSITES, "kep-a-kiadasba")
    meres = _FRISSITES_MERES.read_text(encoding="utf-8")

    assert "_varjon_frissitesi_ablakra(timeout=30.0)" in meres
    assert "05b-frissites-folyamatban-ablak.png" in meres
    assert "actions/upload-artifact@v4" in workflow_job
    assert "needs: frissites" in release_job
    assert "github.event_name == 'workflow_run'" in release_job
    assert "contents: write" in release_job
    assert "actions/download-artifact@v4" in release_job
    assert "05b-frissites-folyamatban-ablak.png" in release_job
    assert "gh release upload" in release_job
    assert "PicasaPy-frissitesi-folyamat.png" in release_job
