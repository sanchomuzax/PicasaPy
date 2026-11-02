"""Az előfordító nem akadhat el, és elakadáskor megmondja, hol (#6374).

A Package-mérésen a csomagolt exe `--qml-elofordit` hívása 180 s után
időtúllépett. A telepítő (`waituntilterminated`) és az önfrissítés ugyanezt
futtatja, tehát egy elakadás ott is megakasztaná a folyamatot.
"""

from __future__ import annotations

import subprocess
import sys

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

    monkeypatch.setattr(qml_precompile.threading, "Timer", _Idozito)
    monkeypatch.setenv(qml_precompile.HATARIDO_ENV, "7")
    qml_precompile._inditsd_a_hataridot()
    assert idozitok == [(7.0, qml_precompile._hatarido_lejart), True]


def test_idotullepeskor_a_meres_kiirja_a_naplo_veget(monkeypatch, tmp_path):
    def _lassu(parancs, *, env, **_kw):
        with open(env[qml_precompile.NAPLO_ENV], "a", encoding="utf-8") as f:
            f.write("fordítás: C:/x/PlacesMap.qml\n")
        raise subprocess.TimeoutExpired(parancs, 1)

    monkeypatch.setattr(qml_cache_warmup.subprocess, "run", _lassu)
    with pytest.raises(qml_cache_warmup.QmlWarmupError) as hiba:
        qml_cache_warmup.melegitsd_qml_cache([sys.executable], {"TEMP": str(tmp_path)}, timeout=1)
    assert "PlacesMap.qml" in str(hiba.value)
