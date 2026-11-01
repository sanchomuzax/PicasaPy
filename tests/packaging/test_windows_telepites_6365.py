"""A Windows-telepítő régi példányt kezelő és verzióerőforrása (#6365)."""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

_GYOKER = Path(__file__).resolve().parents[2]
_ISS = _GYOKER / "packaging/windows/picasapy.iss"
_SPEC = _GYOKER / "packaging/windows/picasapy.spec"
_HELPER_SPEC = _GYOKER / "packaging/windows/picasapy_update_helper.spec"
_VERSION_HELPER = _GYOKER / "packaging/windows/_windows_version_resource.py"
_WORKFLOW = _GYOKER / ".github/workflows/package.yml"
_APP_ID = "{9F3C1D28-7C4E-4E2B-9A55-3B1D6A0C77E1}_is1"


def test_iss_a_negy_regisztracios_nezetben_keres_es_csendben_varja_meg_az_eltavolitast():
    iss = _ISS.read_text(encoding="utf-8")
    code = iss.split("[Code]", 1)[1]

    for gyoker in (
        "HKEY_CURRENT_USER_32",
        "HKEY_CURRENT_USER_64",
        "HKEY_LOCAL_MACHINE_32",
        "HKEY_LOCAL_MACHINE_64",
    ):
        assert gyoker in code
    assert _APP_ID in code
    assert "UninstallString" in code
    assert "InstallLocation" in code
    assert "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" in code
    assert "ewWaitUntilTerminated" in code
    assert "PrepareToInstall" in code
    assert "hu.RemoveOtherInstallation" in iss
    assert "en.RemoveOtherInstallation" in iss


def test_a_windows_ci_elobb_felteszi_a_felhasznaloi_regi_peldanyt_aztan_eltavolitja():
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["windows-telepito"]["steps"]
    install = next(
        step
        for step in steps
        if step.get("name") == "Telepítő telepítése és valós indulási füstpróba"
    )
    script = install["run"]

    assert "/CURRENTUSER" in script
    assert "/ALLUSERS" in script
    assert "PicasaPy-legacy-installed" in script
    assert "[Microsoft.Win32.RegistryView]::Registry32" in script
    assert "[Microsoft.Win32.RegistryView]::Registry64" in script
    assert "régi telepítés" in script
    assert "PicasaPy.exe" in script
    assert script.count("Test-PicasaPyUninstallEntry") >= 3
    assert "Test-Path $legacyExe" in script


def test_a_verzioeroforras_segedje_a_pyproject_verziojabol_ir(tmp_path):
    assert _VERSION_HELPER.is_file(), "hiányzik a Windows-verzióerőforrás segédje"
    spec = importlib.util.spec_from_file_location(
        "windows_version_resource", _VERSION_HELPER
    )
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    output = tmp_path / "version_info.txt"
    project = tomllib.loads((_GYOKER / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    resource_version = tuple(int(part) for part in version.split(".")) + (0,)
    resource_version = resource_version[:4]

    assert helper.write_version_info(
        _GYOKER / "pyproject.toml", output, "PicasaPy.exe"
    ) == version
    contents = output.read_text(encoding="utf-8")
    assert f"filevers={resource_version}" in contents
    assert f"prodvers={resource_version}" in contents
    assert f"StringStruct('FileVersion', '{version}')" in contents
    assert f"StringStruct('ProductVersion', '{version}')" in contents
    assert "StringStruct('ProductName', 'PicasaPy')" in contents


@pytest.mark.parametrize("spec_path", [_SPEC, _HELPER_SPEC])
def test_mindket_windows_spec_a_pyprojectbol_epiti_be_a_verzioeroforrast(spec_path):
    spec = spec_path.read_text(encoding="utf-8")
    assert "_windows_version_resource" in spec
    assert "_VERZIO_EROFORRAS" in spec
    assert "version=str(_VERZIO_EROFORRAS)" in spec
