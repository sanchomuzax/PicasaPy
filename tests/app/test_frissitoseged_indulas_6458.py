"""#6458: a frissítősegéd több helyről is indítható, és a hiba okát kiírja.

A tulajdonos gépén az „Újraindítás most” gomb „A frissítősegéd nem indítható
el.” hibát adott, miközben a CI-próba zöld volt. A segédet a program a
%TEMP%-be másolta és onnan indította; a céges gépeken az onnan induló
programok gyakran tiltottak. Most előbb a program mellől (a telepítési mappa
testvérmappájából) próbál, utána a %TEMP%-ből, és ha egyik sem megy, a
hibaüzenet okot is mond.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from picasapy.app import update_manager
from picasapy.app.update_manager import UpdateController
from tests.app.test_update_manager_6340 import _InlinePool, _MemorySettings, _ReleaseClient


def _vezerlo(monkeypatch, tmp_path):
    telepites = tmp_path / "Programs" / "PicasaPy"
    telepites.mkdir(parents=True)
    (telepites / "PicasaPyUpdateHelper.exe").write_bytes(b"seged")
    monkeypatch.setattr(
        update_manager, "_futtato", SimpleNamespace(executable=str(telepites / "PicasaPy.exe"))
    )
    monkeypatch.setattr(update_manager, "mappa_irhato", lambda _m: True)
    monkeypatch.setattr(update_manager.tempfile, "gettempdir", lambda: str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    vezerlo = UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=_ReleaseClient(),
        pool=_InlinePool(),
        schedule=False,
        install_kind="windows",
    )
    vezerlo._download_path = tmp_path / "csomag.zip"
    return vezerlo, telepites


def test_eloszor_a_program_melletti_mappabol_indit(monkeypatch, tmp_path):
    vezerlo, telepites = _vezerlo(monkeypatch, tmp_path)
    inditasok: list[Path] = []
    monkeypatch.setattr(
        update_manager, "_inditsd_a_segedet",
        lambda args, *, emelt: inditasok.append(Path(args[0])) or True,
    )
    assert vezerlo.installWhenExiting(False) is True
    assert inditasok[0].parent == telepites.parent / "PicasaPy-update"
    assert inditasok[0].is_file()


def test_ha_az_elso_hely_tiltott_a_tempbol_probal(monkeypatch, tmp_path):
    vezerlo, telepites = _vezerlo(monkeypatch, tmp_path)
    inditasok: list[Path] = []

    def indit(args, *, emelt):
        inditasok.append(Path(args[0]))
        return len(inditasok) == 2

    monkeypatch.setattr(update_manager, "_inditsd_a_segedet", indit)
    assert vezerlo.installWhenExiting(False) is True
    assert [p.parent for p in inditasok] == [telepites.parent / "PicasaPy-update", tmp_path / "tmp"]


def test_ha_semmi_nem_indul_a_hiba_okat_mond(monkeypatch, tmp_path):
    vezerlo, _telepites = _vezerlo(monkeypatch, tmp_path)
    monkeypatch.setattr(update_manager, "_inditsd_a_segedet", lambda args, *, emelt: False)
    assert vezerlo.installWhenExiting(False) is False
    assert vezerlo.helperErrorDetail != ""


def test_hianyzo_segednel_is_okot_mond(monkeypatch, tmp_path):
    vezerlo, telepites = _vezerlo(monkeypatch, tmp_path)
    (telepites / "PicasaPyUpdateHelper.exe").unlink()
    assert vezerlo.installWhenExiting(False) is False
    assert "PicasaPyUpdateHelper.exe" in vezerlo.helperErrorDetail


def test_masolasi_hiba_nem_dob_kivetelt(monkeypatch, tmp_path):
    vezerlo, _telepites = _vezerlo(monkeypatch, tmp_path)

    def hibas_masolas(_forras, _cel):
        raise PermissionError("hozzáférés megtagadva")

    monkeypatch.setattr(update_manager, "_masold_a_segedet", hibas_masolas)
    monkeypatch.setattr(update_manager, "_inditsd_a_segedet", lambda args, *, emelt: True)
    assert vezerlo.installWhenExiting(False) is False
    assert "hozzáférés megtagadva" in vezerlo.helperErrorDetail


def test_telepitett_programban_nincs_dev_felirat(monkeypatch):
    from picasapy import __version__, version

    monkeypatch.setattr(version, "_futtato", SimpleNamespace(frozen=True))
    assert version.version_string() == f"v{__version__}"
