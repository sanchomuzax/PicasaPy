"""Az előfordító nem akadhat el, és elakadáskor megmondja, hol (#6374).

A Package-mérésen a csomagolt exe `--qml-elofordit` hívása 180 s után
időtúllépett. A telepítő (`waituntilterminated`) és az önfrissítés ugyanezt
futtatja, tehát egy elakadás ott is megakasztaná a folyamatot.
"""

from __future__ import annotations

import subprocess
import sys
import types

import pytest

from picasapy.app import qml_cache_warmup, qml_precompile


def test_a_haladas_naplo_minden_fajlt_a_betoltes_elott_rogzit(tmp_path, monkeypatch):
    naplo = tmp_path / "elofordit.txt"
    monkeypatch.setenv(qml_precompile.NAPLO_ENV, str(naplo))
    betoltott = []

    class _Komponens:
        def __init__(self, _engine):
            pass

        def loadUrl(self, url, _mode):  # noqa: N802
            betoltott.append(url.toLocalFile())
            assert url.toLocalFile() in naplo.read_text(encoding="utf-8")

        def status(self):
            return qml_precompile.QQmlComponent.Status.Ready

    valodi = qml_precompile.QQmlComponent
    monkeypatch.setattr(qml_precompile, "QQmlComponent", _Komponens)
    _Komponens.Status = valodi.Status
    _Komponens.CompilationMode = valodi.CompilationMode
    fajlok = [tmp_path / "A.qml", tmp_path / "B.qml"]
    assert qml_precompile._forditsd_le(object(), fajlok) == 0
    assert len(betoltott) == 2


def test_a_belso_hatarido_kilep_es_naploz(tmp_path, monkeypatch):
    naplo = tmp_path / "elofordit.txt"
    monkeypatch.setenv(qml_precompile.NAPLO_ENV, str(naplo))
    kilepesek = []
    monkeypatch.setattr(qml_precompile, "_kilepes", kilepesek.append)
    qml_precompile._hatarido_lejart()
    assert kilepesek == [qml_precompile.HATARIDO_KOD]
    assert "időtúllépés" in naplo.read_text(encoding="utf-8")


def test_a_hatarido_kornyezetbol_allithato_es_hatter_szalon_fut(monkeypatch):
    idozitok = []

    class _Idozito:
        def __init__(self, mp, fv):
            idozitok.append((mp, fv))
            self.daemon = False

        def start(self):
            idozitok.append(self.daemon)

    monkeypatch.setattr(qml_precompile, "_Timer", _Idozito)
    monkeypatch.setenv(qml_precompile.HATARIDO_ENV, "7")
    qml_precompile._inditsd_a_hataridot()
    assert idozitok == [(7.0, qml_precompile._hatarido_lejart), True]


def test_idotullepeskor_a_meres_kiirja_a_naplo_veget(monkeypatch, tmp_path):
    def _lassu(parancs, *, env, **_kw):
        with open(env[qml_precompile.NAPLO_ENV], "a", encoding="utf-8") as f:
            f.write("fordítás: C:/x/PlacesMap.qml\n")
        raise subprocess.TimeoutExpired(parancs, 1)

    monkeypatch.setattr(qml_cache_warmup, "_run", _lassu)
    with pytest.raises(qml_cache_warmup.QmlWarmupError) as hiba:
        qml_cache_warmup.melegitsd_qml_cache([sys.executable], {"TEMP": str(tmp_path)}, timeout=1)
    assert "PlacesMap.qml" in str(hiba.value)


def test_az_osszegzes_utan_azonnal_kilep_a_bontas_nelkul(monkeypatch, capsys):
    """A csomagolt exe a fordítás után a Qt-bontásnál akadt el (0,83 s + 180 s)."""
    kilepesek = []
    monkeypatch.setattr(qml_precompile, "_kilepes", kilepesek.append)
    monkeypatch.setattr(qml_precompile, "_inditsd_a_hataridot", lambda: None)
    monkeypatch.setattr(qml_precompile, "QGuiApplication", lambda _argv: type("A", (), {
        "setApplicationName": lambda *_: None, "setOrganizationName": lambda *_: None})())
    monkeypatch.setattr(qml_precompile, "QQmlEngine", lambda: type("E", (), {
        "addImportPath": lambda *_: None})())
    monkeypatch.setattr(qml_precompile, "_forditsd_le", lambda _e, fajlok: 0)
    assert qml_precompile.main() == 0
    assert kilepesek == [0]
    assert "QML-előfordítás:" in capsys.readouterr().out


def test_a_meres_nem_csovon_var_es_a_naplobol_osszegez(monkeypatch, tmp_path):
    """A csomagolt exe kilépés után is nyitva hagyott csővégeket örökített (Package-mérés)."""
    hivasok = []

    def _fut(parancs, *, env, **kw):
        hivasok.append(kw)
        with open(env[qml_precompile.NAPLO_ENV], "a", encoding="utf-8") as f:
            f.write("fordítás: x.qml\nQML-előfordítás: 3 fájl, 0 hibás, 0.10 s\n")
        return subprocess.CompletedProcess(parancs, 0)

    monkeypatch.setattr(qml_cache_warmup, "_run", _fut)
    ki = qml_cache_warmup.melegitsd_qml_cache([sys.executable], {"TEMP": str(tmp_path)})
    assert ki == "QML-előfordítás: 3 fájl, 0 hibás, 0.10 s"
    assert hivasok[0]["stdout"] is subprocess.DEVNULL and hivasok[0]["stderr"] is subprocess.DEVNULL
    assert "capture_output" not in hivasok[0]


def test_windowson_a_kilepes_kihagyja_a_dll_levalasztast(monkeypatch):
    """Az `os._exit` a csomagolt windowsos exe-ben is elakadt (ExitProcess)."""
    hivasok = []

    class _K32:
        def GetCurrentProcess(self):  # noqa: N802
            return "folyamat"

        def TerminateProcess(self, h, kod):  # noqa: N802
            hivasok.append((h, kod))

    import ctypes

    monkeypatch.setattr(qml_precompile, "_platform", lambda: "win32")
    monkeypatch.setattr(ctypes, "windll", types.SimpleNamespace(kernel32=_K32()), raising=False)
    monkeypatch.setattr(qml_precompile, "_os_exit", lambda kod: hivasok.append(("os_exit", kod)))
    qml_precompile._azonnali_kilepes(0)
    assert hivasok[0] == ("folyamat", 0)
