"""#677: a darabolt tesztfuttató ne hagyjon gigabájtokat a `/tmp`-ben.

A `scripts/run_tests.py` fájlonként külön processzben futtat (#53/#155), és a
pytest a „tartsd meg az utolsó hármat" takarítást **basetemp-enként** végzi.
Mivel minden részfutás SAJÁT számozott könyvtárat kapott, egyetlen teljes
futás tucatnyi könyvtárat hagyott maga után — mérve **4,2 GB** egy 8 GB-os
tmpfs-en.

A kár nem a futásé: a betelt tmpfs a PÁRHUZAMOSAN futó másik munkamenet
parancsait töri el, némán, félrevezető `ENOSPC`-hibával.

A megoldás: minden részfutás ugyanazt a **futásonként egyedi** basetempet
kapja (így a következő részfutás induláskor felszabadítja az előzőét — a
csúcsigény egyetlen részfutásnyi), a futás végén pedig az egész eltűnik.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402


class TestBasetempAtadasa:
    """Minden részfutás megkapja a közös basetempet."""

    def test_minden_reszfutas_ugyanazt_a_basetempet_kapja(self, monkeypatch, tmp_path):
        hivasok: list[list[str]] = []

        def _rogzit(command, **kwargs):
            hivasok.append(list(command))

            class _Eredmeny:
                returncode = 0

            return _Eredmeny()

        monkeypatch.setattr(run_tests, "_run", _rogzit)
        monkeypatch.setattr(run_tests, "_ROOT", Path(run_tests._ROOT))

        basetemp = tmp_path / "kozos"
        run_tests._run_pytest(["tests"], 10, cov=False, basetemp=basetemp)

        assert hivasok, "nem indult részfutás"
        assert f"--basetemp={basetemp}" in hivasok[0]

    def test_soros_futasban_a_basetemp_egyseges(self, monkeypatch, tmp_path):
        """SOROS módban a `main()` egyetlen basetempet ad minden részfutásnak.

        Ha részfutásonként külön könyvtár lenne, visszatérne a #677: a
        tucatnyi könyvtár egymás mellett gyűlne, nem egymást váltva.
        """
        latott: list[str] = []

        def _rogzit_pytest(args, timeout_s, *, cov, basetemp, **egyeb):
            latott.append(str(basetemp))
            return 0

        monkeypatch.setattr(run_tests, "_PARHUZAM", 1)
        monkeypatch.setattr(run_tests, "_run_pytest", _rogzit_pytest)
        monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)

        assert run_tests.main([]) == 0
        assert latott, "nem indult részfutás"
        assert len(set(latott)) == 1, f"részfutásonként eltérő basetemp: {set(latott)}"

    def test_parhuzamosan_kulon_de_azonnal_takaritott_mappak(self, monkeypatch):
        """PÁRHUZAMOS módban részfutásonként KÜLÖN mappa kell — de nyomtalanul.

        A #677 tilalma tartalmilag az, hogy a futás ne hagyjon maga után
        tucatnyi könyvtárat. Párhuzamosan a közös basetemp nem járható út: a
        pytest induláskor kiüríti, tehát a szálak egymás ideiglenes fájljait
        törölnék (#1030). A szerződés ezért: külön mappa, viszont a részfutás
        végén AZONNAL eltűnik — így a csúcsigény a szálak számával arányos.
        """
        latott: list[Path] = []
        volt_sajat_mappa: list[bool] = []

        def _rogzit_pytest(args, timeout_s, *, cov, basetemp, **egyeb):
            ut = Path(basetemp)
            ut.mkdir(parents=True, exist_ok=True)
            latott.append(ut)
            volt_sajat_mappa.append(ut.exists())
            return 0

        monkeypatch.setattr(run_tests, "_PARHUZAM", 4)
        monkeypatch.setattr(run_tests, "_run_pytest", _rogzit_pytest)
        monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)

        assert run_tests.main([]) == 0
        app_futasok = [ut for ut in latott if ut.name == "pytest"]
        assert len(app_futasok) > 1, "nem indult több app-részfutás"
        assert len(set(app_futasok)) == len(app_futasok), (
            "a párhuzamos részfutások OSZTOZTAK a basetempen — ez törli "
            "egymás ideiglenes fájljait"
        )
        assert all(volt_sajat_mappa), "a részfutás nem kapott saját mappát"
        assert not [ut for ut in app_futasok if ut.exists()], (
            "a részfutás mappája a futás után is megmaradt (#677)"
        )


class TestTakaritas:
    """A futás ne hagyjon maga után semmit — se sikeresen, se bukás után."""

    def test_a_futas_vegen_eltunik_a_basetemp(self, monkeypatch):
        keletkezett: list[Path] = []

        def _rogzit_pytest(args, timeout_s, *, cov, basetemp, **egyeb):
            basetemp.mkdir(parents=True, exist_ok=True)
            (basetemp / "szemet.bin").write_bytes(b"x" * 1024)
            if basetemp not in keletkezett:
                keletkezett.append(basetemp)
            return 0

        monkeypatch.setattr(run_tests, "_run_pytest", _rogzit_pytest)
        monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)

        run_tests.main([])

        assert keletkezett, "nem jött létre basetemp"
        for konyvtar in keletkezett:
            assert not konyvtar.exists(), f"ottmaradt: {konyvtar}"

    def test_bukott_reszfutas_utan_is_takarit(self, monkeypatch):
        """A takarítás nem függhet attól, zöld volt-e a futás."""
        keletkezett: list[Path] = []

        def _bukik(args, timeout_s, *, cov, basetemp, **egyeb):
            basetemp.mkdir(parents=True, exist_ok=True)
            if basetemp not in keletkezett:
                keletkezett.append(basetemp)
            return 1

        monkeypatch.setattr(run_tests, "_run_pytest", _bukik)
        monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)

        assert run_tests.main([]) == 1
        for konyvtar in keletkezett:
            assert not konyvtar.exists(), f"bukás után ottmaradt: {konyvtar}"

    def test_kivetel_eseten_is_takarit(self, monkeypatch):
        """Megszakítás (Ctrl-C) vagy hiba se hagyjon maradékot."""
        keletkezett: list[Path] = []

        def _dobal(args, timeout_s, *, cov, basetemp, **egyeb):
            basetemp.mkdir(parents=True, exist_ok=True)
            keletkezett.append(basetemp)
            raise KeyboardInterrupt

        monkeypatch.setattr(run_tests, "_run_pytest", _dobal)
        monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)

        with pytest.raises(KeyboardInterrupt):
            run_tests.main([])
        for konyvtar in keletkezett:
            assert not konyvtar.exists(), f"megszakítás után ottmaradt: {konyvtar}"


class TestRegiMaradekTakaritasa:
    """A korábbi (megszakadt) futások maradékai kor szerint tűnjenek el.

    Kor szerint — mert egy PÁRHUZAMOS munkamenet friss könyvtárát elvinni
    rosszabb, mint helyet pazarolni.
    """

    def test_csak_a_regi_es_csak_a_sajat_tunik_el(self, monkeypatch, tmp_path):
        import os
        import time

        monkeypatch.setattr(run_tests, "_TEMP_GYOKER", tmp_path)

        regi_sajat = tmp_path / f"{run_tests._TEMP_ELOTAG}regi"
        friss_sajat = tmp_path / f"{run_tests._TEMP_ELOTAG}friss"
        idegen = tmp_path / "masik-projekt-konyvtara"
        for konyvtar in (regi_sajat, friss_sajat, idegen):
            konyvtar.mkdir()

        # a régi és az idegen is „öreg" — az idegennek MÉGIS maradnia kell
        regi = time.time() - 6 * 3600
        os.utime(regi_sajat, (regi, regi))
        os.utime(idegen, (regi, regi))

        run_tests._takarits_regi_maradekot()

        assert not regi_sajat.exists(), "a régi saját maradékot el kellett volna vinni"
        assert friss_sajat.exists(), "a friss saját könyvtárhoz nem szabad nyúlni"
        assert idegen.exists(), "idegen könyvtárhoz SOHA nem nyúlunk"
