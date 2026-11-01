"""#6385: a frissítősegéd naplója megkülönbözteti a kimeneteleket."""

from __future__ import annotations

import getpass
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


def _elokeszit(monkeypatch, tmp_path):
    from picasapy.app import update_swap_helper as helper

    naplo = tmp_path / "frissites-naplo.txt"
    monkeypatch.setattr(helper, "_update_log_path", lambda: naplo)
    monkeypatch.setattr(helper, "wait_for_process", lambda _pid: None)
    monkeypatch.setattr(helper, "extract_update_archive", lambda _zip, _stage: tmp_path)
    monkeypatch.setattr(helper, "inditsd_a_felhasznalonak", lambda _exe: None)
    monkeypatch.setattr(helper, "tarolo_tipusa", lambda _path: "helyi")
    monkeypatch.setattr(
        helper,
        "swap_update_directory",
        lambda _stage, _install, *, launch: launch(),
    )
    return helper, naplo


def test_a_frisites_naploja_a_windows_localappdata_adatmappaba_kerul(
    monkeypatch, tmp_path
):
    from picasapy.app import update_swap_helper as helper

    monkeypatch.setattr(helper, "_platform", lambda: "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert helper._update_log_path() == tmp_path / "PicasaPy" / "frissites-naplo.txt"


def test_a_kivetelekben_sem_marad_utvonal_vagy_felhasznalonev():
    from picasapy.app import update_swap_helper as helper

    user = getpass.getuser()
    uzenet = f'hiba: "C:\\Users\\{user}\\App Data\\frissites.zip"'

    tisztitott = helper._sanitized_log_message(uzenet)

    assert "C:\\" not in tisztitott
    assert user.casefold() not in tisztitott.casefold()
    assert "[útvonal]" in tisztitott
    assert "../" not in helper._sanitized_log_message("hibás tag: ../../users/name/file.zip")


@pytest.mark.parametrize(
    ("returncode", "timeout", "exception", "expected"),
    (
        (0, False, None, "kilépési kód: 0"),
        (7, False, None, "kilépési kód: 7"),
        (None, True, None, "IDŐTÚLLÉPÉS"),
        (None, False, OSError("példahiba"), "példahiba"),
    ),
)
def test_az_onellenorzes_minden_kimenetelt_naplozza(
    monkeypatch, tmp_path, returncode, timeout, exception, expected
):
    helper, naplo = _elokeszit(monkeypatch, tmp_path)

    def fake_run(*_args, **_kwargs):
        if timeout:
            raise subprocess.TimeoutExpired("picasapy", 10)
        if exception is not None:
            raise exception
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(helper, "_run", fake_run)
    assert helper._onellenorzes(Path("app.exe"), timeout=10) is (
        expected == "kilépési kód: 0"
    )

    tartalom = naplo.read_text(encoding="utf-8")
    assert expected in tartalom
    assert "tároló: helyi" in tartalom
    assert "app.exe" not in tartalom


@pytest.mark.parametrize("sikeres", (True, False))
def test_a_frisites_varakozasat_es_a_visszaallast_is_naplozza(
    monkeypatch, tmp_path, sikeres
):
    helper, naplo = _elokeszit(monkeypatch, tmp_path)
    monkeypatch.setattr(
        helper,
        "_onellenorzes",
        lambda _executable: sikeres,
    )

    assert helper.install_after_exit(
        123, tmp_path / "csomag.zip", tmp_path / "telepites", "PicasaPy.exe"
    ) is sikeres
    tartalom = naplo.read_text(encoding="utf-8")
    assert "várakozás" in tartalom.casefold()
    assert "kicsomagolás" in tartalom.casefold()
    assert "csere" in tartalom.casefold()
    if not sikeres:
        assert "Visszaállás oka" in tartalom
    assert str(tmp_path) not in tartalom


def test_a_frisites_kivetelet_es_annak_szoveget_naplozza(monkeypatch, tmp_path):
    helper, naplo = _elokeszit(monkeypatch, tmp_path)
    monkeypatch.setattr(
        helper,
        "extract_update_archive",
        lambda *_args: (_ for _ in ()).throw(ValueError("hibás csomag")),
    )

    with pytest.raises(ValueError, match="hibás csomag"):
        helper.install_after_exit(
            123, tmp_path / "csomag.zip", tmp_path / "telepites", "PicasaPy.exe"
        )
    assert "hibás csomag" in naplo.read_text(encoding="utf-8")
