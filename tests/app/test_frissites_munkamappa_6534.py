"""A frissítősegéd és gyermekei nem fogják a telepítési mappát munkamappaként (#6534).

A tulajdonos 2026-11-04-én 1.0.41-ről frissített: a „Fájlok cseréje” 100 mp
után `[WinError 32]`-vel bukott. Windowson egy mappa nem nevezhető át, amíg
bármely folyamat munkamappája benne van (Microsoft KB Q60028). A programot az
Intéző a telepítési mappából indítja, a segéd pedig ezt örökölte.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

from picasapy.app import update_folyamatok, update_helper, update_swap_helper


def test_a_seged_munkamappaja_nem_windowson_a_seged_sajat_mappaja(monkeypatch, tmp_path):
    hivasok = []
    monkeypatch.setattr(update_helper, "_popen", lambda args, **kw: hivasok.append(kw))
    seged = tmp_path / "PicasaPy-update" / "PicasaPyUpdateHelper-1.exe"
    assert update_helper.inditsd_a_segedet([str(seged), "--pid", "1"], emelt=False, platform="linux")
    assert Path(hivasok[0]["cwd"]) == seged.parent


def test_windowson_a_shellexecute_megkapja_a_seged_mappajat(monkeypatch, tmp_path):
    hivasok = []
    # #6557: a modul saját fogantyúját foltozzuk, nem a globális ctypes.windll-t (#1375)
    monkeypatch.setattr(update_helper, "_shell_execute", lambda *a: hivasok.append(a) or 42)
    seged = tmp_path / "PicasaPy-update" / "PicasaPyUpdateHelper-1.exe"
    assert update_helper.inditsd_a_segedet([str(seged), "--pid", "1"], emelt=True, platform="win32")
    _hwnd, ige, fajl, _param, munkamappa, _mutat = hivasok[0]
    assert ige == "runas"
    assert Path(fajl) == seged
    assert Path(munkamappa) == seged.parent


def test_a_csomagolt_seged_legelso_lepese_a_munkamappa_athelyezese(monkeypatch, tmp_path):
    lepesek = []
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(update_swap_helper, "biztonsagos_munkamappa", lambda: tmp_path)
    monkeypatch.setattr(update_swap_helper, "_chdir", lambda ut: lepesek.append(("chdir", ut)))
    monkeypatch.setattr(
        update_swap_helper.update_ablak, "ablak_foprogram",
        lambda kod, _status=None: lepesek.append(("ablak", kod)) or 0,
    )
    assert update_swap_helper.main([update_swap_helper.update_ablak.ABLAK_KAPCSOLO, "hu"]) == 0
    assert lepesek == [("chdir", tmp_path), ("ablak", "hu")]


def test_fejlesztoi_futasban_nem_valt_munkamappat(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(update_swap_helper, "_chdir", lambda _ut: (_ for _ in ()).throw(AssertionError))
    update_swap_helper._munkamappa_a_telepitesen_kivulre()


def test_az_onellenorzes_ablak_es_indulokep_nelkul_fut_a_telepitesen_kivul(monkeypatch, tmp_path):
    hivas = {}
    monkeypatch.setattr(update_swap_helper, "biztonsagos_munkamappa", lambda: tmp_path)
    monkeypatch.setattr(
        update_swap_helper, "_run",
        lambda parancs, **kw: hivas.update(kw, parancs=parancs) or SimpleNamespace(returncode=0),
    )
    exe = tmp_path / "PicasaPy" / "PicasaPy.exe"
    assert update_swap_helper._onellenorzes(exe)
    assert Path(hivas["cwd"]) == tmp_path
    assert hivas["env"]["PYINSTALLER_SUPPRESS_SPLASH_SCREEN"] == "1"
    assert hivas["env"]["QT_QPA_PLATFORM"] == "offscreen"


def test_a_qml_elomelegitesek_is_indulokep_nelkul_futnak(monkeypatch):
    from picasapy.app import qml_cache_warmup

    kornyezetek = []
    monkeypatch.setattr(qml_cache_warmup, "melegitsd_qml_cache",
                        lambda _p, env, **_k: kornyezetek.append(env) or "")
    monkeypatch.setattr(qml_cache_warmup, "melegitsd_qml_grafikat",
                        lambda _p, env, **_k: kornyezetek.append(env) or "")
    update_swap_helper._qml_elofordit(Path("PicasaPy.exe"))
    update_swap_helper._qml_grafika_melegites(Path("PicasaPy.exe"))
    assert [env["PYINSTALLER_SUPPRESS_SPLASH_SCREEN"] for env in kornyezetek] == ["1", "1"]


def test_az_uj_program_ugy_indul_mint_az_intezobol(monkeypatch, tmp_path):
    hivas = {}
    monkeypatch.setattr(update_swap_helper, "_popen", lambda args, **kw: hivas.update(kw, args=args))
    exe = tmp_path / "PicasaPy" / "PicasaPy.exe"
    update_swap_helper.inditsd_a_felhasznalonak(exe)
    assert Path(hivas["cwd"]) == exe.parent
    assert "PYINSTALLER_SUPPRESS_SPLASH_SCREEN" not in hivas.get("env", os.environ)


def test_foglalt_mappanal_elobb_leallitja_a_fogo_folyamatokat_es_gyorsan_ujraprobal(tmp_path):
    ora = [0.0]
    esemenyek = []

    def rename(_forras, _cel):
        esemenyek.append("rename")
        if esemenyek.count("rename") < 3:
            hiba = PermissionError(13, "foglalt")
            hiba.winerror = 32
            raise hiba

    update_folyamatok.atnevez_ujraprobalva(
        tmp_path / "a", tmp_path / "b",
        rename=rename,
        alszik=lambda mp: ora.__setitem__(0, ora[0] + mp),
        ora=lambda: ora[0],
        foglaltnal=lambda: esemenyek.append("leallitas"),
    )
    assert esemenyek == ["rename", "leallitas", "rename", "rename"]
    assert ora[0] < 2.0


def test_a_hataridok_rovidek():
    assert update_folyamatok.ATNEVEZESI_HATARIDO_MP <= 10.0
    assert update_folyamatok.FOLYAMAT_HATARIDO_MP <= 5.0
