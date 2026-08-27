"""#1654: a tesztüzem naplózása az ELSŐ szakasztól fut.

Ez a fájl a jegy legfontosabb állítását méri: bekapcsolt tesztüzem mellett
a **következő indítás az első ezredmásodperctől** naplóz. A #211
Teljesítmény-monitorja pont ezt nem tudja (csak menetközben kapcsolható),
a #1601 idővonala pedig csak környezeti változóból indul.

A mérés az `application._indulasi_idovonal()`-t hívja: ez az a KÉT sor,
ami a `run()` legelején eldönti, mérünk-e, és ez zárja le a
Python-/PySide6-importok szakaszát az `entry_at` időbélyeg alapján.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app.application as app_module
from picasapy.perf.tesztuzem import TESZTUZEM_BEALLITAS_KULCS

#: Az indulás LEGELSŐ szakaszának címkéje (#1601). Ha ez nem a nulladik
#: elem, akkor a naplózás nem az első ezredmásodperctől fut.
ELSO_SZAKASZ = "Python- és PySide6-modulok betöltése"


class _Beallitasok:
    """Minimális `QSettings`-utánzat — a valós tárolót nem szennyezzük."""

    def __init__(self, tarolo: dict | None = None) -> None:
        self._tarolo = dict(tarolo or {})

    def value(self, kulcs, alap=None):
        return self._tarolo.get(kulcs, alap)


class TestABekapcsolasUtjai:
    def test_alapbol_KI_van_kapcsolva(self):
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy"], settings=_Beallitasok(), environ={}
        )
        assert idovonal.enabled is False

    def test_a_TARTOS_beallitas_bekapcsolja(self):
        """A #1654/1: a kapcsoló túléli a kilépést, tehát a KÖVETKEZŐ
        indulás magától mér — a felhasználónak semmit nem kell tennie."""
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy"],
            settings=_Beallitasok({TESZTUZEM_BEALLITAS_KULCS: "true"}),
            environ={},
        )
        assert idovonal.enabled is True

    def test_a_parancssori_kapcsolo_bekapcsolja(self):
        """A #1654/2: `--tesztuzem` — env nélkül, fejlesztői és CI-oldalon."""
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy", "--tesztuzem"], settings=_Beallitasok(), environ={}
        )
        assert idovonal.enabled is True

    def test_a_regi_kornyezeti_valtozo_TOVABBRA_is_mukodik(self):
        """A #1601 útja nem törhet el — a CI arra épül (#1653)."""
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy"],
            settings=_Beallitasok(),
            environ={"PICASAPY_STARTUP_TIMELINE": "1"},
        )
        assert idovonal.enabled is True


class TestAzElsoSzakasztolNaploz:
    """⚠️ A jegy DoD-ja: „a következő indulás A LEGELSŐ SZAKASZTÓL naplóz
    — teszttel igazolva, nem docstringgel"."""

    def test_az_elso_bejelentett_szakasz_az_IMPORTOKE(self):
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy", "--tesztuzem"],
            settings=_Beallitasok(),
            environ={},
            entry_at=0.0,
            clock=lambda: 3.0,
        )
        assert idovonal.phases, "egyetlen szakaszt sem jelentett be"
        assert idovonal.phases[0][0] == ELSO_SZAKASZ

    def test_a_processz_INDULASATOL_szamol_nem_a_meres_kezdetetol(self):
        """A Python- és PySide6-import már lefutott, mire idáig eljutunk —
        az `entry_at` (a belépési pont legelső saját órája) hozza be. A
        #1653 windowsos 33 mp-éből épp ez a rész gyanús."""
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy", "--tesztuzem"],
            settings=_Beallitasok(),
            environ={},
            entry_at=0.0,
            clock=lambda: 2.5,
        )
        assert idovonal.phases[0][1] == 2500.0
        assert idovonal.total_ms == 2500.0

    def test_kikapcsolva_egyetlen_szakasz_sincs(self):
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy"], settings=_Beallitasok(), environ={}, entry_at=0.0
        )
        assert idovonal.phases == ()


class TestAKapcsoloNemLeszFigyeltGyoker:
    """⚠️ Az `_resolve_roots` MINDEN `argv[1:]` elemet gyökérnek vesz."""

    def test_a_kapcsolo_kikerul_az_argumentumokbol(self):
        _idovonal, argv = app_module._indulasi_idovonal(
            ["picasapy", "--tesztuzem", "/kepek"],
            settings=_Beallitasok(),
            environ={},
        )
        assert argv == ["picasapy", "/kepek"]

    def test_a_megtisztitott_argv_bol_a_gyokerek_helyesek(self):
        _idovonal, argv = app_module._indulasi_idovonal(
            ["picasapy", "--tesztuzem", "/kepek"],
            settings=_Beallitasok(),
            environ={},
        )
        assert app_module._resolve_roots(argv) == ("/kepek",)


class TestASorrendAForrasban:
    """Az idővonal létrehozása a `run()` LEGELSŐ érdemi lépése.

    Egy szakasz-bejelentés (`timeline.mark`/`timeline.phase`) az idővonal
    létrehozása ELŐTT csendben elveszne — ezt a forrás sorrendje dönti el,
    és semmilyen viselkedési teszt nem fogja meg."""

    def test_a_run_eloszor_az_idovonalat_hozza_letre(self):
        forras = Path(app_module.__file__).read_text(encoding="utf-8")
        run_torzs = forras.split("\ndef run(", 1)[1]
        letrehozas = run_torzs.find("_indulasi_idovonal(")
        assert letrehozas >= 0, "a run() nem az _indulasi_idovonal-t hívja"
        elso_bejelentes = min(
            (
                hely
                for hely in (
                    run_torzs.find("timeline.mark("),
                    run_torzs.find("timeline.phase("),
                )
                if hely >= 0
            ),
            default=len(run_torzs),
        )
        assert letrehozas < elso_bejelentes, (
            "a run() előbb jelent be szakaszt, mint hogy az idővonal "
            "létrejönne — az első szakaszok elvesznének"
        )

    def test_a_run_a_MEGTISZTITOTT_argv_t_hasznalja(self):
        """A `--tesztuzem` sehol nem juthat el a gyökér-feloldásig.

        A `run()` ugyanazt az `argv` nevet köti újra a megtisztított
        listára — az invariáns tehát az, hogy az ÚJRAKÖTÉS megelőzi a
        gyökér-feloldást. A nyers listával hívott `_resolve_roots` egy
        `--tesztuzem` nevű mappát venne fel a könyvtárba."""
        forras = Path(app_module.__file__).read_text(encoding="utf-8")
        run_torzs = forras.split("\ndef run(", 1)[1]
        ujrakotes = re.search(
            r"timeline,\s*argv\s*=\s*_indulasi_idovonal\(", run_torzs
        )
        assert ujrakotes is not None, (
            "a run() nem köti újra az argv-t a megtisztított listára"
        )
        feloldas = run_torzs.find("_resolve_roots(argv)")
        assert feloldas >= 0, "a run() nem oldja fel a gyökereket"
        assert ujrakotes.start() < feloldas, (
            "a gyökér-feloldás megelőzi az argv megtisztítását"
        )


class TestKikapcsolvaKoltsegmentes:
    """⚠️ A jegy DoD-ja: „Kikapcsolva a mérés KÖLTSÉGMENTES".

    A #1601 mérése (0,2 µs/hívás) a szakasz-bejelentésekre vonatkozik; ez
    az őr a #1654 ÚJ költségét méri: a napló összeállítása a könyvtár
    méretét is megkérdezi az indextől, és az egy SQLite-nyitás minden
    induláskor. Kikapcsolt tesztüzemben ennek meg sem szabad történnie."""

    def test_kikapcsolva_a_konyvtarmeret_lekerdezese_EL_SEM_INDUL(self, tmp_path):
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy"], settings=_Beallitasok(), environ={}
        )
        hivasok = []

        def _kepszamok():
            hivasok.append(True)
            return (1, 2, 3)

        app_module._jelentsd_az_idovonalat(idovonal, _kepszamok)

        assert hivasok == [], (
            "kikapcsolt tesztüzemben is megnyitottuk az indexet a "
            "könyvtárméretért — ez minden induláskor fizetendő költség"
        )

    def test_kikapcsolva_nem_ir_naplot(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_module, "default_log_dir", lambda: tmp_path)
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy"], settings=_Beallitasok(), environ={}
        )
        app_module._jelentsd_az_idovonalat(idovonal, lambda: (1,))
        assert list(tmp_path.iterdir()) == []

    def test_bekapcsolva_VISZONT_ir_es_a_meret_is_benne_van(
        self, tmp_path, monkeypatch, qt_app
    ):
        """A kikapcsolt ág üressége csak akkor bizonyít, ha a bekapcsolt
        ág tényleg dolgozik — különben egy soha nem működő funkció is
        „költségmentes"."""
        monkeypatch.setattr(app_module, "default_log_dir", lambda: tmp_path)
        idovonal, _argv = app_module._indulasi_idovonal(
            ["picasapy", "--tesztuzem"], settings=_Beallitasok(), environ={}
        )
        idovonal.mark("próbaszakasz")

        app_module._jelentsd_az_idovonalat(idovonal, lambda: (10, 20, 12))

        naplok = list(tmp_path.glob("indulas-*.txt"))
        assert len(naplok) == 1
        szoveg = naplok[0].read_text(encoding="utf-8")
        assert "próbaszakasz" in szoveg
        assert "42" in szoveg, "a képek darabszáma nem került a naplóba"
        assert "3" in szoveg, "a mappák darabszáma nem került a naplóba"
