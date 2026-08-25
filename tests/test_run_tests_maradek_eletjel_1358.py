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

## A platform kimondása (#1381)

Ez a fájl a beolvadása után **két teszttel pirosan állt a windows-lábon**,
minden PR-en (`assert not True` — a maradék nem törlődött). Kimérve: nem a
termék hibája, hanem a TESZTÉ. A `_el_e_a_futas` Windowson szándékosan
`None`-t ad (ott az `os.kill(pid, 0)` nem kérdés, hanem `TerminateProcess`),
tehát a friss maradék ott MARAD — a két teszt viszont a POSIX-választ várta.

A mérés két hipotézist választott szét: a windowsos FÁJLZÁROLÁS (#998
hibaosztálya) mind a HÁROM maradékot bent hagyta volna, a CI-n viszont a
kor-alapú törlések zöldek voltak, és csak az életjel-alapúak buktak — a
`shutil.rmtree` tehát dolgozott. A platform-ág szimulációja pontosan a CI
képét adta vissza.

Ezért itt minden állítás, ami az ÉLETJELEN múlik, kimondja a platformját
(`_posix_eletjel`), és a windowsos viselkedésnek saját, kimondott tesztje
van. A `skipif` nem lett volna megoldás: a kihagyott teszt a másik lábon
nem mér semmit (#1217).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402

#: A maradékba írt életjel PID-je. Az ÉRTÉKE nem hordoz jelentést: hogy a
#: folyamat él-e, azt a `_posix_eletjel` rögzített válasza mondja meg, nem
#: ez a szám. Csak érvényes egésznek kell lennie, hogy a beolvasás sikerüljön.
_TETSZOLEGES_PID = 999_999


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


def _posix_eletjel(monkeypatch, *, el: bool) -> None:
    """A POSIX életjel-kérdés rögzítése — mindkét CI-láb ugyanazt mérje (#1381).

    KÉT fogantyút kell rögzíteni, mert a döntés kettőn múlik:

    1. **`_platform()`** (#1217) — a windowsos ág `None`-t ad, tehát ott a
       friss maradék MARAD. E nélkül a „halott futás maradéka azonnal
       törlődik" állítás a windows-lábon elbukott, pedig a TERMÉK volt jó.
    2. **`os.kill`** — a valódi PID-kérdés lábfüggő, tehát önmagában a
       platform rögzítése nem elég: Windowson a nem létező PID nem
       `ProcessLookupError`-t ad, a létező PID-re pedig a CPython
       `os.kill(pid, 0)` `TerminateProcess`, ami MEGÖLNÉ a tesztfutást.
       Itt ezért a POSIX-alakot írjuk elő: kivétel = halott, csend = él.

    Amit így mérünk, az továbbra is a termék valódi döntése: a
    `_el_e_a_futas` leképezése (kivétel → halott) és a takarító kor ×
    életjel logikája. Csak a valódi oprendszer megkérdezése marad ki — azt
    külön, POSIX-on futó teszt fedi (`test_a_VALODI_os_kill_...`).

    ⚠️ Az `os.kill` cseréje a standard modult érinti, ezért szűkre szabott:
    a `run_tests` ezt az egy hívást használja életjelre. A #1217 tiltása a
    platform-VÁLASZ globális átírására szól (`sys.platform`, `os.name`) —
    az itt szabályosan a modul fogantyúján megy.
    """
    monkeypatch.setattr(run_tests, "_platform", lambda: "linux")

    def _kill(pid: int, jel: int) -> None:
        if not el:
            raise ProcessLookupError(pid)

    monkeypatch.setattr(run_tests.os, "kill", _kill)


def _halott_pid() -> int:
    """Egy biztosan nem élő PID kikeresése — CSAK POSIX-on hívható.

    ⚠️ Az `os.kill` itt a VALÓDI: Windowson ez a keresés folyamatokat
    ölne, ezért az egyetlen hívója `skipif`-fel védett."""
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
        _posix_eletjel(monkeypatch, el=False)
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "halott", pid=_TETSZOLEGES_PID)

        run_tests._takarits_regi_maradekot()

        assert not konyvtar.exists()

    def test_ELO_futas_maradekahoz_nem_nyul(self, monkeypatch, tmp_path):
        """Egy futó teszt basetempjét elvinni rosszabb, mint helyet pazarolni."""
        _posix_eletjel(monkeypatch, el=True)
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "elo", pid=_TETSZOLEGES_PID)

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists()

    def test_eletjel_nelkuli_FRISS_maradek_marad(self, monkeypatch, tmp_path):
        """Nem tudjuk, él-e — a régi, kor-alapú óvatosság marad.

        Az életjel-választ szándékosan „halott"-ra rögzítjük: így az
        állítás tényleg a HIÁNYZÓ életjelen múlik, nem azon, hogy a
        folyamat véletlenül élőnek látszott."""
        _posix_eletjel(monkeypatch, el=False)
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "ismeretlen", pid=None)

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists()

    def test_eletjel_nelkuli_REGI_maradek_torlodik(self, monkeypatch, tmp_path):
        """Tisztán kor-alapú ág: életjelet nem kérdez, platformot sem — ezért
        ez az egy teszt szándékosan NEM rögzít platformot."""
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(
            tmp_path, "regi", pid=None, kor_s=run_tests._MARADEK_KOR_S + 60
        )

        run_tests._takarits_regi_maradekot()

        assert not konyvtar.exists()

    def test_a_kor_a_VEGSO_hatar_elo_pid_mellett_is(self, monkeypatch, tmp_path):
        """PID-újrahasznosítás ellen: a saját PID-ünk is „élőnek" látszik, de
        egy háromórás teszt-basetemp nem valódi futás.

        ⚠️ Az életjel rögzítése itt BIZTONSÁGI kérdés is: a maradékba a
        SAJÁT PID-ünk kerül, és ha ezt a valódi `os.kill` kapná meg a
        windows-lábon, a tesztfutás önmagát ölné meg. Ma a kor-ág rövidre
        zár és el sem jut odáig — de erre nem szabad támaszkodni."""
        _posix_eletjel(monkeypatch, el=True)
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(
            tmp_path, "regi-elo", pid=os.getpid(), kor_s=run_tests._MARADEK_KOR_S + 60
        )

        run_tests._takarits_regi_maradekot()

        assert not konyvtar.exists()

    def test_serult_eletjel_nem_dontheti_el(self, monkeypatch, tmp_path):
        """Olvashatatlan PID-fájl = nem tudjuk; ilyenkor nem törlünk."""
        _posix_eletjel(monkeypatch, el=False)
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "serult", pid=None)
        (konyvtar / run_tests._PID_FAJL).write_text("nem szám", encoding="utf-8")

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists()

    @pytest.mark.skipif(
        sys.platform.startswith("win"),
        reason="az `os.kill(pid, 0)` csak POSIX-on életjel-kérdés; Windowson "
        "`TerminateProcess`, tehát ott meg sem kérdezhető",
    )
    def test_a_VALODI_os_kill_halott_pidre_halottat_mond(self, monkeypatch, tmp_path):
        """A rögzített válasz mellett is kell EGY valódi integrációs mérés.

        A többi teszt az `os.kill` POSIX-ALAKJÁT írja elő; ez az egy pedig
        megkérdezi az igazi oprendszert, hogy az alak stimmel-e. Csak
        POSIX-on futhat, és a `reason` kimondja, miért — ez a CONTRIBUTING
        szerint a `skipif` szabályos esete (valódi oprendszer-képesség)."""
        monkeypatch.setattr(run_tests, "_platform", lambda: "linux")
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        konyvtar = _maradek(tmp_path, "valodi-halott", pid=_halott_pid())

        assert run_tests._el_e_a_futas(konyvtar) is False


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
        konyvtar = _maradek(tmp_path, "win", pid=_TETSZOLEGES_PID)
        # ⚠️ #1217: a fogantyút cseréljük, nem a globális `os.name`-et — az
        # `os` itt MAGA a standard modul, az átírása mindenre hatott volna.
        monkeypatch.setattr(run_tests, "_platform", lambda: "win32")
        monkeypatch.setattr(
            run_tests.os, "kill", lambda *a: pytest.fail("Windowson tilos os.kill")
        )
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)

        run_tests._takarits_regi_maradekot()

        assert konyvtar.exists(), "Windowson a friss maradék marad"

    def test_windowson_a_KOR_viszi_el_a_maradekot(self, monkeypatch, tmp_path):
        """A windows-láb nem marad takarítás nélkül: a kor a végső háló,
        és az ott is dolgozik (a `shutil.rmtree` nem akad el)."""
        konyvtar = _maradek(
            tmp_path, "win-regi", pid=_TETSZOLEGES_PID,
            kor_s=run_tests._MARADEK_KOR_S + 60,
        )
        monkeypatch.setattr(run_tests, "_platform", lambda: "win32")
        monkeypatch.setattr(
            run_tests.os, "kill", lambda *a: pytest.fail("Windowson tilos os.kill")
        )
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)

        run_tests._takarits_regi_maradekot()

        assert not konyvtar.exists()


class TestCsakTakaritas:
    def test_a_kapcsolo_takarit_es_kilep(self, monkeypatch, tmp_path):
        """A munkamenet-indító ezt hívja: takarítás tesztfuttatás nélkül."""
        _posix_eletjel(monkeypatch, el=False)
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        monkeypatch.setattr(
            run_tests, "_futtat", lambda *a, **k: pytest.fail("nem futhat teszt")
        )
        konyvtar = _maradek(tmp_path, "halott", pid=_TETSZOLEGES_PID)

        assert run_tests.main(["--csak-takaritas"]) == 0
        assert not konyvtar.exists()

    def test_windowson_is_takarit_es_kilep(self, monkeypatch, tmp_path):
        """Ugyanaz a kapcsoló a windows-lábon: teszt nem fut, és a kor
        szerinti maradék elmegy — az életjel-kérdés viszont kimarad."""
        monkeypatch.setattr(run_tests, "_platform", lambda: "win32")
        monkeypatch.setattr(
            run_tests.os, "kill", lambda *a: pytest.fail("Windowson tilos os.kill")
        )
        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)
        monkeypatch.setattr(
            run_tests, "_futtat", lambda *a, **k: pytest.fail("nem futhat teszt")
        )
        friss = _maradek(tmp_path, "win-friss", pid=_TETSZOLEGES_PID)
        regi = _maradek(
            tmp_path, "win-regi", pid=_TETSZOLEGES_PID,
            kor_s=run_tests._MARADEK_KOR_S + 60,
        )

        assert run_tests.main(["--csak-takaritas"]) == 0
        assert friss.exists(), "életjel-kérdés nélkül a friss maradék marad"
        assert not regi.exists()
