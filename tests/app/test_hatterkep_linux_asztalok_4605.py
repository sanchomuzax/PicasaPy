"""KDE és wlroots asztalon a megfelelő háttérkép-kezelő fut (#4605)."""

# rontás-kontroll: picasapy.app.wallpaper._WLROOTS_ASZTALOK = () → 1 failed

from __future__ import annotations

import subprocess

from picasapy.app import wallpaper


class _FutoFolyamat:
    def __init__(self, returncode: int | None = None) -> None:
        self.returncode = returncode

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        if self.returncode is None:
            raise subprocess.TimeoutExpired("swaybg", timeout)
        return self.returncode

    def terminate(self) -> None:
        self.returncode = 0


def test_kde_a_plasma_sajat_hatterkep_beallitojat_valasztja(tmp_path):
    futtatott = []

    def fut(parancs, **_kw):
        futtatott.append(parancs)
        return subprocess.CompletedProcess(parancs, 0, "", "")

    nev = wallpaper.set_desktop_background(
        tmp_path / "kep.bmp",
        platform="linux",
        desktop="KDE",
        runner=fut,
        which=lambda parancs: f"/usr/bin/{parancs}"
        if parancs == "plasma-apply-wallpaperimage"
        else None,
    )

    assert nev == "plasma-apply-wallpaperimage"
    assert futtatott == [["plasma-apply-wallpaperimage", str(tmp_path / "kep.bmp")]]


def test_wlroots_a_swaybgot_kozepre_illesztve_es_tartosan_inditja(
    tmp_path, monkeypatch
):
    inditasok = []
    folyamat = _FutoFolyamat()
    monkeypatch.setattr(wallpaper, "_swaybg_folyamat", None)

    def indit(parancs, **kw):
        inditasok.append((parancs, kw))
        return folyamat

    nev = wallpaper.set_desktop_background(
        tmp_path / "kep.bmp",
        platform="linux",
        desktop="labwc:wlroots",
        which=lambda parancs: "/usr/bin/swaybg" if parancs == "swaybg" else None,
        launcher=indit,
    )

    assert nev == "swaybg"
    assert len(inditasok) == 1
    parancs, kw = inditasok[0]
    assert parancs == ["swaybg", "-i", str(tmp_path / "kep.bmp"), "-m", "center"]
    assert kw["start_new_session"] is True
    assert kw["stdin"] is subprocess.DEVNULL


def test_wlroots_azonnal_kilepo_swaybgot_nem_veszi_sikernek(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(wallpaper, "_swaybg_folyamat", None)
    nev = wallpaper.set_desktop_background(
        tmp_path / "kep.bmp",
        platform="linux",
        desktop="labwc:wlroots",
        which=lambda parancs: "/usr/bin/swaybg" if parancs == "swaybg" else None,
        launcher=lambda *_args, **_kw: _FutoFolyamat(returncode=0),
    )

    assert nev is None


def test_nem_asztali_modban_a_pcmanfm_nem_jelenthet_sikert(tmp_path):
    futtatott = []

    def fut(parancs, **_kw):
        futtatott.append(parancs)
        return subprocess.CompletedProcess(parancs, 0, "", "")

    nev = wallpaper.set_desktop_background(
        tmp_path / "kep.bmp",
        platform="linux",
        desktop="GNOME",
        runner=fut,
        which=lambda parancs: "/usr/bin/pcmanfm" if parancs == "pcmanfm" else None,
    )

    assert nev is None
    assert futtatott == []
