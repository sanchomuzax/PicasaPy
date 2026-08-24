"""A teszt-maradék takarítása ne a koron múljon (#1358).

## A lelet

Párhuzamos munkamenetek megszakadt teszt-körei **~1,5 GB**-ot hagytak a
`/tmp`-en, és senki nem vitte el őket — a tulajdonosnak kellett szólnia. A
takarító MEGVOLT (#677), csak két résen szökött át a szemét:

1. **csak a kor számított** (3 óra), a mai maradékok fiatalabbak voltak,
   pedig a hozzájuk tartozó folyamat rég halott volt;
2. **csak tesztfuttatáskor futott** — aki fejleszt vagy kutat, sosem takarít.

A megoldás: a futás hagyjon ÉLETJELET a saját könyvtárában, és a halott
futás maradéka azonnal mehet. A kor marad végső háló.

⚠️ Az élő futás könyvtárához továbbra sem nyúlhat senki: ez a párhuzamos
munkamenetek miatt kritikus — egy futó teszt basetempjét elvinni rosszabb,
mint helyet pazarolni.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402


def _maradek(gyoker: Path, nev: str, *, pid: int | None, kor_s: float = 0.0) -> Path:
    """Teszt-maradék könyvtár gyártása adott életjellel és korral."""
    konyvtar = gyoker / f"{run_tests._TEMP_ELOTAG}{nev}"
    konyvtar.mkdir()
    (konyvtar / "valami.tmp").write_text("x", encoding="utf-8")
    if pid is not None:
        (konyvtar / run_tests._PID_FAJL).write_text(str(pid), encoding="utf-8")
    if kor_s:
        regen = time.time() - kor_s
        os.utime(konyvtar, (regen, regen))
    return konyvtar


#: Egy biztosan nem létező folyamat azonosítója.
def _halott_pid() -> int:
    pid = 999_999
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return pid
        except OSError:
            return pid
        pid -= 1


class TestEletjel:
    def test_halott_futas_maradeka_AZONNAL_torlodik(self, monkeypatch, tmp_path):
        """Ez a #1358 lényege: a mai maradékok fiatalok voltak, mégis halottak."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "halott", pid=_halott_pid())

        run_tests._takarits_regi_maradekot()

        assert not konyvtar.exists()

    def test_ELO_futas_maradekahoz_nem_nyul(self, monkeypatch, tmp_path):
        """Egy futó teszt basetempjét elvinni rosszabb, mint helyet pazarolni."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "elo", pid=os.getpid())

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists()

    def test_eletjel_nelkuli_FRISS_maradek_marad(self, monkeypatch, tmp_path):
        """Nem tudjuk, él-e — a régi, kor-alapú óvatosság marad."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "ismeretlen", pid=None)

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists()

    def test_eletjel_nelkuli_REGI_maradek_torlodik(self, monkeypatch, tmp_path):
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(
            tmp_path, "regi", pid=None, kor_s=run_tests._MARADEK_KOR_S + 60
        )

        run_tests._takarits_regi_maradekot()

        assert not konyvtar.exists()

    def test_a_kor_a_VEGSO_hatar_elo_pid_mellett_is(self, monkeypatch, tmp_path):
        """PID-újrahasznosítás ellen: a saját PID-ünk is „élőnek" látszik, de
        egy háromórás teszt-basetemp nem valódi futás."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(
            tmp_path, "regi-elo", pid=os.getpid(), kor_s=run_tests._MARADEK_KOR_S + 60
        )

        run_tests._takarits_regi_maradekot()

        assert not konyvtar.exists()

    def test_serult_eletjel_nem_dontheti_el(self, monkeypatch, tmp_path):
        """Olvashatatlan PID-fájl = nem tudjuk; ilyenkor nem törlünk."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "serult", pid=None)
        (konyvtar / run_tests._PID_FAJL).write_text("nem szám", encoding="utf-8")

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists()


class TestEletjelKiirasa:
    def test_a_futas_kiirja_a_sajat_azonositojat(self, tmp_path):
        run_tests._jelold_a_futast(tmp_path)
        assert (tmp_path / run_tests._PID_FAJL).read_text(encoding="utf-8") == str(
            os.getpid()
        )

    def test_a_kiiras_bukasa_nem_allitja_meg_a_futast(self, tmp_path):
        """A takarítás kényelme sosem foghatja meg magát a tesztfutást."""
        run_tests._jelold_a_futast(tmp_path / "nincs-ilyen-konyvtar")


class TestWindowsVedelem:
    def test_windowson_NEM_kerdezunk_pidet(self, monkeypatch, tmp_path):
        """⚠️ A CPython `os.kill(pid, 0)` Windowson MEGÖLI a folyamatot —
        ott csak a kor-szabály futhat."""
        # ⚠️ a halott PID-et MÉG az os.kill kicserélése előtt kérdezzük meg,
        # különben a teszt saját segédfüggvénye bukna el rajta
        pid = _halott_pid()
        konyvtar = _maradek(tmp_path, "win", pid=pid)
        monkeypatch.setattr(run_tests.os, "name", "nt")
        monkeypatch.setattr(
            run_tests.os, "kill", lambda *a: pytest.fail("Windowson tilos os.kill")
        )
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists(), "Windowson a friss maradék marad"


class TestCsakTakaritas:
    def test_a_kapcsolo_takarit_es_kilep(self, monkeypatch, tmp_path):
        """A munkamenet-indító ezt hívja: takarítás tesztfuttatás nélkül."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        monkeypatch.setattr(
            run_tests, "_futtat", lambda *a, **k: pytest.fail("nem futhat teszt")
        )
        konyvtar = _maradek(tmp_path, "halott", pid=_halott_pid())

        assert run_tests.main(["--csak-takaritas"]) == 0
        assert not konyvtar.exists()
