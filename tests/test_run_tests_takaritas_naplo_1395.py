"""A takarító ne adja fel NÉMÁN zárolt könyvtárnál (#1395).

## A lelet

A `_takarits_regi_maradekot` két réteg mögött takarít: `shutil.rmtree(...,
ignore_errors=True)` ÉS egy külső `except OSError: continue`. Kimérve (a
javítás ELŐTTI kódon, `shutil.rmtree`-t `PermissionError`-ra kényszerítve):
egyetlen kiírt sor sem születik, és a zárolt könyvtár némán, nyom nélkül
bent marad. Ha ez éles zárolásba futna (a windowsos alak, #998 osztálya), a
futtató nem tudná megmondani, hogy nem takarított.

## A megoldás

`_rmtree` modulszintű fogantyú (ugyanaz a minta, mint a
`tools/golden/make_golden_kit_effects.py`-ban), és `_takarits_egy_konyvtarat`
korlátos újrapróbálkozással: néhány kísérlet rövid várakozással, majd ha
mindegyik elbukik, EGY naplósor a könyvtár nevével és az utolsó hibával.
Végtelen ciklus nincs — egy tartósan zárolt könyvtár csak a saját sorára
korlátozza a kárt.

A sikeres (nem zárolt) úton nincs extra várakozás és nincs felesleges
naplózás — ezt külön teszt bizonyítja.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402

_TETSZOLEGES_PID = 999_999


def _regi_maradek(gyoker: Path, nev: str) -> Path:
    """Kor-alapú ágat kiváltó, életjel nélküli, régi maradék könyvtár."""
    konyvtar = gyoker / f"{run_tests._TEMP_ELOTAG}{nev}"
    konyvtar.mkdir()
    (konyvtar / "valami.tmp").write_text("x", encoding="utf-8")
    regen = time.time() - run_tests._MARADEK_KOR_S - 60
    import os

    os.utime(konyvtar, (regen, regen))
    return konyvtar


class TestZaroltKonyvtarNaplozva:
    def test_tartosan_zarolt_konyvtar_naplozva_marad(
        self, monkeypatch, tmp_path, capsys
    ):
        """A tartósan zárolt könyvtár bent marad, DE a feladás LÁTHATÓ."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        monkeypatch.setattr(run_tests, "_kill", lambda *a: None)
        varasok: list[float] = []
        monkeypatch.setattr(run_tests, "_platform", lambda: "linux")

        def _zarolt_rmtree(*_args, **_kwargs):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(run_tests, "_rmtree", _zarolt_rmtree)
        konyvtar = _regi_maradek(tmp_path, "zarolt")

        run_tests._takarits_regi_maradekot(alvo=varasok.append)

        assert konyvtar.exists(), "zárolt könyvtárhoz nem szabad hozzányúlni"
        kimenet = capsys.readouterr().out
        assert str(konyvtar) in kimenet
        assert "Access is denied" in kimenet or "13" in kimenet
        # korlátos újrapróbálkozás: véges számú várakozás, nem végtelen ciklus
        assert 0 < len(varasok) < 20

    def test_atmenetileg_zarolt_konyvtar_ujraprobalkozasra_torlodik(
        self, monkeypatch, tmp_path, capsys
    ):
        """Ha a MÁSODIK próbálkozásra már sikerül, nincs feladás, nincs napló."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        monkeypatch.setattr(run_tests, "_kill", lambda *a: None)
        monkeypatch.setattr(run_tests, "_platform", lambda: "linux")
        konyvtar = _regi_maradek(tmp_path, "atmenetileg-zarolt")
        eredeti_rmtree = run_tests._rmtree
        allapot = {"hivasok": 0}

        def _elsore_zarolt(*args, **kwargs):
            allapot["hivasok"] += 1
            if allapot["hivasok"] == 1:
                raise PermissionError(13, "Access is denied")
            return eredeti_rmtree(*args, **kwargs)

        monkeypatch.setattr(run_tests, "_rmtree", _elsore_zarolt)
        varasok: list[float] = []

        run_tests._takarits_regi_maradekot(alvo=varasok.append)

        assert not konyvtar.exists()
        assert len(varasok) == 1, "pontosan egy várakozás a sikeres újrapróba előtt"
        kimenet = capsys.readouterr().out
        assert "SIKERTELEN" not in kimenet.upper()


class TestSikeresUtNemLassulNemNaplozFolosleg:
    def test_sikeres_torles_nem_var_es_nem_naplozza_a_sikert(
        self, monkeypatch, tmp_path, capsys
    ):
        """A normál (nem zárolt) úton nincs extra várakozás és nincs napló."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        monkeypatch.setattr(run_tests, "_kill", lambda *a: None)
        monkeypatch.setattr(run_tests, "_platform", lambda: "linux")
        konyvtar = _regi_maradek(tmp_path, "rendben")

        def _sose_hivhato(*_a, **_k):
            raise AssertionError("a sikeres úton nem szabad várakozni")

        run_tests._takarits_regi_maradekot(alvo=_sose_hivhato)

        assert not konyvtar.exists()
        assert capsys.readouterr().out == ""
