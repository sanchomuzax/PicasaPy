"""A kattintásos telepítőpróba folyamatfüggetlen diagnosztikája (#6472)."""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

_GYOKER = Path(__file__).resolve().parents[2]
_PROBA = _GYOKER / "packaging/windows/telepito_proba_6472.ps1"
_WORKFLOW = _GYOKER / ".github/workflows/package.yml"


def test_a_varazslot_minden_felso_szintu_ablak_kozul_keresi():
    """Az Inno ideiglenes exe-je másik PID-ben nyitja meg a TWizardFormot."""
    forras = _PROBA.read_text(encoding="utf-8")

    assert "AllWindows()" in forras
    assert "[PicasaPyNative]::AllWindows()" in forras
    assert "ForProcess($setup.Id)" not in forras
    assert "HasExited" not in forras.split("$setupDeadline", 1)[1].split(
        "$appDeadline", 1
    )[0]


def test_az_ablak_es_gomb_allapotvaltozasait_idorendben_naplizza():
    forras = _PROBA.read_text(encoding="utf-8")

    assert "Write-WindowSnapshotIfChanged" in forras
    assert "ClassName" in forras
    assert "buttons=" in forras
    assert "_utolsoDiagnosztika" in forras
    assert "TotalSeconds -ge 1" in forras


def test_a_varazslo_legfeljebb_negy_percig_futhat():
    forras = _PROBA.read_text(encoding="utf-8")

    assert "AddMinutes(4)" in forras
    assert "AddMinutes(12)" not in forras


def test_hiba_eseten_a_windows_update_screenshots_artefaktumba_kepernyokepet_ment():
    forras = _PROBA.read_text(encoding="utf-8")
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    lepesek = workflow["jobs"]["windows-telepito"]["steps"]
    artefakt = next(
        lepes
        for lepes in lepesek
        if lepes.get("name") == "A frissítési képernyőképek csatolása"
    )

    assert "PicasaPy-update-screenshots" in forras
    assert "Save-FailureScreenshot" in forras
    assert "catch {" in forras
    assert "windows-update-screenshots" == artefakt["with"]["name"]
    assert "PicasaPy-update-screenshots" in artefakt["with"]["path"]
    assert "always()" in artefakt["if"]


def test_a_varazslo_minden_oldalat_valodi_kattintassal_lepteti():
    forras = _PROBA.read_text(encoding="utf-8")

    assert "ClickPhysical($yes.Handle)" in forras
    assert "ClickPhysical($next.Handle)" in forras
    assert "^(Install|Telepítés)$" in forras
    assert "ClickPhysical($finish.Handle)" in forras
    assert "$lastActionSignature" in forras
    assert "$promptSignature" in forras
    assert "LastClickError" in forras
