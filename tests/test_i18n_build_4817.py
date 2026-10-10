"""#4817: a `.qm` helyben készül a `.ts`-ből, a PR-ek nem hordozzák."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from picasapy.app import i18n_build

GYOKER = Path(__file__).resolve().parents[1]
I18N = GYOKER / "src" / "picasapy" / "app" / "i18n"


@pytest.fixture
def ts(tmp_path):
    forras = tmp_path / "picasapy_hu.ts"
    forras.write_bytes((I18N / "picasapy_hu.ts").read_bytes())
    return forras


def test_hianyzo_qm_elkeszul(ts):
    assert i18n_build.forditsd(ts)
    assert ts.with_suffix(".qm").stat().st_size > 0


def test_friss_qm_nem_fordul_ujra(ts, monkeypatch):
    assert i18n_build.forditsd(ts)
    hivas = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: hivas.append(a))
    assert i18n_build.forditsd(ts)
    assert hivas == []


def test_elavult_qm_ujrafordul(ts):
    qm = ts.with_suffix(".qm")
    qm.write_bytes(b"regi")
    regen = ts.stat().st_mtime - 100
    os.utime(qm, (regen, regen))
    assert i18n_build.forditsd(ts)
    assert qm.read_bytes() != b"regi"


def test_lrelease_nelkul_nem_dob(ts, monkeypatch):
    monkeypatch.setattr(i18n_build, "lrelease_parancs", lambda: None)
    assert i18n_build.forditsd(ts) is False
    assert not ts.with_suffix(".qm").exists()


def test_a_qm_nincs_a_repoban():
    """A `.gitignore` kizárja, és egy sincs követve — különben a PR-ek
    újra ütköznének egymással."""
    kovetett = subprocess.run(
        ["git", "ls-files", "src/picasapy/app/i18n/*.qm"],
        cwd=GYOKER, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert kovetett == []
