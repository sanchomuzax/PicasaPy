"""#6095: a `qml_betoltes_bontas.py` a `Main.qml` betöltését méri.

Nem angol rendszeren, üres beállításokkal az első induláskor a rendszer-nyelv
felajánló ablak (#4325) töltődik be először; a mérő akkor az ő `load`-ját
mérte (és a #6097 hibája miatt el is szállt). A gyermek ezért rögzített nyelvvel
indul.
"""

from __future__ import annotations

import importlib.util
import pathlib

_REPO = pathlib.Path(__file__).resolve().parents[1]
_SZKRIPT = _REPO / "scripts" / "qml_betoltes_bontas.py"

_spec = importlib.util.spec_from_file_location("qml_betoltes_bontas", _SZKRIPT)
mero = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mero)


def test_a_gyermek_rogzitett_nyelvvel_indul(tmp_path):
    kornyezet = mero._gyermek_kornyezet(tmp_path, tmp_path / "gyorstar")

    assert kornyezet["PICASAPY_LANG"] == "en"
    assert kornyezet["XDG_CONFIG_HOME"] == str(tmp_path / "config")


def test_a_gyermek_a_foablakot_meri(tmp_path, monkeypatch):
    """A valódi gyermekfolyamat, magyar rendszer-nyelvvel is a `Main.qml`-t tölti."""
    monkeypatch.setenv("LANG", "hu_HU.UTF-8")
    monkeypatch.setenv("LANGUAGE", "hu")
    adat = mero._futas(tmp_path, tmp_path / "gyorstar", "bontas", "teszt")

    assert adat["letrejott"] is True
    assert adat["url"].endswith("/Main.qml"), adat["url"]
