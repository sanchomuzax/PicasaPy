"""Az előfordító nem akadhat el, és elakadáskor megmondja, hol (#6374).

A Package-mérésen a csomagolt exe `--qml-elofordit` hívása 180 s után
időtúllépett. A telepítő (`waituntilterminated`) és az önfrissítés ugyanezt
futtatja, tehát egy elakadás ott is megakasztaná a folyamatot.
"""

from __future__ import annotations

import io
import subprocess
import sys
import types
from pathlib import Path

import pytest

from picasapy.app import qml_cache_warmup, qml_precompile


class _HamisQCoreApplication:
    def __init__(self, _argv):
        pass

    @staticmethod
    def setApplicationName(*_args):  # noqa: N802
        pass

    @staticmethod
    def setOrganizationName(*_args):  # noqa: N802
        pass


def test_a_haladas_naplo_minden_fajlt_a_betoltes_elott_rogzit(tmp_path, monkeypatch):
    naplo = tmp_path / "elofordit.txt"
    monkeypatch.setenv(qml_precompile.NAPLO_ENV, str(naplo))
    betoltott = []

    def _futtat(command, **_kwargs):
        source = command[-1]
        assert source in naplo.read_text(encoding="utf-8")
        cel = Path(command[command.index("-o") + 1])
        cel.parent.mkdir(parents=True, exist_ok=True)
        cel.write_bytes(b"compiled")
        betoltott.append(source)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(qml_precompile, "_qmlcachegen_exe", lambda: tmp_path / "qmlcachegen")
    monkeypatch.setattr(qml_precompile, "_qml_import_path", lambda: str(tmp_path))
    monkeypatch.setattr(qml_precompile, "_run", _futtat)
    fajlok = [tmp_path / "A.qml", tmp_path / "B.qml"]
    assert qml_precompile._forditsd_le(tmp_path / "cache", fajlok) == 0
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
        qml_cache_warmup.melegitsd_qml_cache([sys.executable], {"TEMP": str(tmp_path)}, timeout=10)
    assert "PlacesMap.qml" in str(hiba.value)


def test_az_osszegzes_utan_azonnal_kilep_a_bontas_nelkul(monkeypatch, capsys):
    """A csomagolt exe a fordítás után a Qt-bontásnál akadt el (0,83 s + 180 s)."""
    kilepesek = []
    monkeypatch.setattr(qml_precompile, "_kilepes", kilepesek.append)
    monkeypatch.setattr(qml_precompile, "_inditsd_a_hataridot", lambda: None)
    monkeypatch.setattr(qml_precompile, "QCoreApplication", _HamisQCoreApplication)
    monkeypatch.setattr(qml_precompile, "_qml_cache_konyvtar", lambda: Path("cache"))
    monkeypatch.setattr(qml_precompile, "_forditsd_le", lambda _cache, fajlok: 0)
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

    monkeypatch.setattr(qml_precompile, "_platform", lambda: "win32")
    monkeypatch.setattr(
        qml_precompile,
        "_windll",
        types.SimpleNamespace(kernel32=_K32()),
    )
    monkeypatch.setattr(qml_precompile, "_os_exit", lambda kod: hivasok.append(("os_exit", kod)))
    qml_precompile._azonnali_kilepes(0)
    assert hivasok[0] == ("folyamat", 0)


class _NemKodolhato:
    """A windowsos cp1252-es kimenet: az „ő” betűre UnicodeEncodeError."""

    def __init__(self):
        self.encoding = "cp1252"
        self.buffer = io.BytesIO()

    def write(self, szoveg):
        self.buffer.write(szoveg.encode(self.encoding))
        return len(szoveg)

    def flush(self):
        pass

    def reconfigure(self, *, encoding, errors):
        self.encoding = encoding


def _hamis_qt(monkeypatch, forditas=lambda _e, fajlok: 0):
    monkeypatch.setattr(qml_precompile, "_inditsd_a_hataridot", lambda: None)
    monkeypatch.setattr(qml_precompile, "QCoreApplication", _HamisQCoreApplication)
    monkeypatch.setattr(qml_precompile, "_qml_cache_konyvtar", lambda: Path("cache"))
    monkeypatch.setattr(qml_precompile, "_forditsd_le", forditas)


def test_a_nem_kodolhato_kimenet_sem_akasztja_meg_a_kilepest(monkeypatch, tmp_path):
    """A csomagolt exe cp1252-es kimenetre írt „ő”-je kivételt dobott, és az ablakos
    PyInstaller-csomag hibaablakot nyitott, ami kattintásra várt (Package-mérés, 180 s)."""
    kilepesek = []
    monkeypatch.setattr(qml_precompile, "_kilepes", kilepesek.append)
    kimenet = _NemKodolhato()
    monkeypatch.setattr(sys, "stdout", kimenet)
    monkeypatch.setenv(qml_precompile.NAPLO_ENV, str(tmp_path / "n.txt"))
    _hamis_qt(monkeypatch)
    qml_precompile.main()
    assert kilepesek == [0]
    assert "QML-előfordítás:" in kimenet.buffer.getvalue().decode("utf-8")


def test_hianyzo_kimenetnel_is_kilep(monkeypatch):
    kilepesek = []
    monkeypatch.setattr(qml_precompile, "_kilepes", kilepesek.append)
    monkeypatch.setattr(sys, "stdout", None)
    _hamis_qt(monkeypatch)
    qml_precompile.main()
    assert kilepesek == [0]


def test_barmilyen_kivetelnel_naploz_es_hibakoddal_kilep(monkeypatch, tmp_path):
    naplo = tmp_path / "n.txt"
    monkeypatch.setenv(qml_precompile.NAPLO_ENV, str(naplo))
    kilepesek = []
    monkeypatch.setattr(qml_precompile, "_kilepes", kilepesek.append)

    def _hibas(_e, _f):
        raise RuntimeError("qml")

    _hamis_qt(monkeypatch, _hibas)
    qml_precompile.main()
    assert kilepesek == [qml_precompile.KIVETEL_KOD]
    assert "RuntimeError" in naplo.read_text(encoding="utf-8")


def test_a_cache_kulcs_windowson_is_perjeles_utvonalbol_keszul():
    """A Qt a `QUrl.toLocalFile()` alakot hasheli, ami Windowson is `C:/...`;
    a natív `C:\\...` alakból számolt név egyetlen bejegyzéssel sem egyezne."""
    from hashlib import sha1
    from pathlib import PureWindowsPath

    ut = PureWindowsPath(r"C:\Program Files\PicasaPy\_internal\picasapy\app\qml\PicasaPy\Main.qml")
    vart = sha1(b"C:/Program Files/PicasaPy/_internal/picasapy/app/qml/PicasaPy/Main.qml").hexdigest()
    assert qml_precompile._qml_cache_nev_utbol(ut) == vart + ".qmlc"
