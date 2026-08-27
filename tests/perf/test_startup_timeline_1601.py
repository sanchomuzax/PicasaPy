"""#1601: kapcsolható indulási idővonal — a mérőeszköz tesztjei.

A jegy első követelménye nem gyorsítás, hanem **mérés**: meg kell tudni,
mi tart meddig az induláskor. Az eszköz alapból KI van kapcsolva, és
kikapcsolva gyakorlatilag nem kerül semmibe.
"""

from __future__ import annotations

import time

import pytest

from picasapy.perf.startup_timeline import (
    STARTUP_TIMELINE_ENV,
    StartupTimeline,
    start_startup_timeline,
    timeline_enabled,
)


class _Ora:
    """Léptethető óra — a mérés determinista teszteléséhez."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def lep(self, seconds: float) -> None:
        self.now += seconds


class TestKapcsolo:
    def test_alapbol_ki_van_kapcsolva(self):
        assert timeline_enabled({}) is False

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "igen", "yes", "on"])
    def test_bekapcsolo_ertekek(self, value):
        assert timeline_enabled({STARTUP_TIMELINE_ENV: value}) is True

    @pytest.mark.parametrize("value", ["", "0", "false", "nem", "off"])
    def test_kikapcsolo_ertekek(self, value):
        assert timeline_enabled({STARTUP_TIMELINE_ENV: value}) is False

    def test_a_gyar_kikapcsolva_ad_peldanyt(self):
        """Kikapcsolva is VAN objektum — a hívóoldalon nincs `if`-ág."""
        timeline = start_startup_timeline(environ={})
        assert timeline.enabled is False
        with timeline.phase("valami"):
            pass
        timeline.mark("más")
        assert timeline.phases == ()


class TestSzakaszok:
    def test_a_szakasz_ideje_ezredmasodpercben_all(self):
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        with timeline.phase("index előkészítése"):
            ora.lep(0.25)
        assert timeline.phases == (("index előkészítése", 250.0),)

    def test_a_szakaszok_sorrendben_allnak(self):
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        with timeline.phase("első"):
            ora.lep(0.01)
        with timeline.phase("második"):
            ora.lep(0.02)
        assert [label for label, _ms in timeline.phases] == ["első", "második"]

    def test_a_hibaval_veget_ero_szakasz_is_bekerul(self):
        """Egy elszálló lépés ideje is látszik — különben pont a bajos
        szakasz tűnne el a jelentésből."""
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        with pytest.raises(ValueError):
            with timeline.phase("hibás"):
                ora.lep(0.05)
                raise ValueError("hiba")
        assert timeline.phases == (("hibás", 50.0),)

    def test_a_mark_az_elozo_mark_ota_eltelt_idot_meri(self):
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        ora.lep(0.1)
        timeline.mark("Qt-alkalmazás")
        ora.lep(0.2)
        timeline.mark("QML betöltése")
        assert [label for label, _ms in timeline.phases] == [
            "Qt-alkalmazás",
            "QML betöltése",
        ]
        assert [ms for _label, ms in timeline.phases] == pytest.approx(
            [100.0, 200.0]
        )

    def test_a_mark_from_a_peldany_elotti_idot_is_beszamolja(self):
        """A Python/PySide6 import már lefutott, mire az idővonal létrejön —
        a `mark_from` ezt is behozza, és a teljes időt is visszahúzza rá."""
        ora = _Ora()
        ora.lep(3.0)  # a példány „születése" a 3. másodpercben
        timeline = StartupTimeline(enabled=True, clock=ora)
        ora.lep(0.05)
        timeline.mark_from(0.0, "importok")
        assert timeline.phases[0][0] == "importok"
        assert timeline.phases[0][1] == pytest.approx(3050.0)
        assert timeline.total_ms == pytest.approx(3050.0)

    def test_a_mark_from_kikapcsolva_nem_gyujt(self):
        timeline = StartupTimeline(enabled=False)
        timeline.mark_from(0.0, "importok")
        assert timeline.phases == ()

    def test_a_teljes_ido_a_kezdettol_szamol(self):
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        ora.lep(0.4)
        timeline.mark("vége")
        assert timeline.total_ms == pytest.approx(400.0)

    def test_a_szakaszok_ideje_es_a_teljes_ido_kulon_all(self):
        """A `mark` és a `phase` keverhető: a nem mért rés a különbségben
        látszik, nem tűnik el."""
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        ora.lep(0.1)  # nem mért rés (pl. a Qt saját indulása)
        with timeline.phase("mért"):
            ora.lep(0.2)
        assert [label for label, _ms in timeline.phases] == ["mért"]
        assert timeline.phases[0][1] == pytest.approx(200.0)
        # a teljes idő NAGYOBB a szakaszok összegénél — a 100 ms-os rés
        # így nem tűnik el, hanem a különbségben látszik
        assert timeline.total_ms == pytest.approx(300.0)


class TestJelentes:
    def test_a_jelentes_minden_szakaszt_es_az_osszeget_tartalmazza(self):
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        with timeline.phase("index előkészítése"):
            ora.lep(1.5)
        with timeline.phase("fotókönyvtár betöltése"):
            ora.lep(0.25)
        report = timeline.render(app_version="v0.8.120 (1.abc)")

        assert "v0.8.120 (1.abc)" in report
        assert "index előkészítése" in report
        assert "1500" in report.replace(" ", "")
        assert "ÖSSZESEN" in report

    def test_a_jelentes_a_leglassabb_szakaszt_kiemeli(self):
        """A felhasználó által átküldhető szöveg magától mondja meg, hol a
        szűk keresztmetszet — ne kelljen táblázatot olvasnia."""
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        with timeline.phase("gyors"):
            ora.lep(0.01)
        with timeline.phase("lassú"):
            ora.lep(2.0)
        report = timeline.render()
        kiemeles = report.split("leglassabb", 1)[1]
        assert kiemeles.index("lassú") < kiemeles.index("gyors")

    def test_a_jelentes_nem_szivarogtat_utvonalat(self):
        """#211 adatvédelmi szabálya: a küldhető diagnosztikában nincs
        fájlnév és nincs teljes útvonal."""
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        with timeline.phase("index előkészítése"):
            ora.lep(0.1)
        report = timeline.render()
        assert "/home/" not in report
        assert "\\Users\\" not in report

    def test_kikapcsolva_ures_jelentest_ad(self):
        timeline = StartupTimeline(enabled=False)
        assert timeline.render() == ""

    def test_a_fajlba_iras_visszaadja_az_utvonalat(self, tmp_path):
        ora = _Ora()
        timeline = StartupTimeline(enabled=True, clock=ora)
        with timeline.phase("valami"):
            ora.lep(0.1)
        target = timeline.write(tmp_path)
        assert target is not None
        assert target.parent == tmp_path
        assert "valami" in target.read_text(encoding="utf-8")

    def test_kikapcsolva_nem_ir_fajlt(self, tmp_path):
        timeline = StartupTimeline(enabled=False)
        assert timeline.write(tmp_path) is None
        assert list(tmp_path.iterdir()) == []


class TestKikapcsolvaNemLassit:
    """A jegy külön kéri: a mérés maga ne lassítson, ha ki van kapcsolva."""

    def test_a_kikapcsolt_szakasz_koltsege_elhanyagolhato(self):
        timeline = StartupTimeline(enabled=False)
        ismetles = 20_000
        started = time.perf_counter()
        for _ in range(ismetles):
            with timeline.phase("szakasz"):
                pass
            timeline.mark("pont")
        per_hivas_us = (time.perf_counter() - started) / (ismetles * 2) * 1_000_000
        # MÉRT (RPi5, 2026-08-27): ~0,2 µs/hívás. A küszöb 20 µs — két
        # nagyságrend tartalék a lassabb gépnek, de a „véletlenül valódi
        # munkát végez kikapcsolva is" hibát elkapja.
        assert per_hivas_us < 20.0

    def test_kikapcsolva_nem_gyujt_adatot(self):
        """A memória sem nőhet: kikapcsolva egyetlen szakasz sem tárolódik."""
        timeline = StartupTimeline(enabled=False)
        for i in range(1000):
            timeline.mark(f"szakasz-{i}")
        assert timeline.phases == ()
