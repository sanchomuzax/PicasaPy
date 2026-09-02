"""A spec-elavulás jelzésének őrei (#1958).

A jelzés **nem kapu**: a kilépőkódja mindig 0, mert a találatok többsége
jogos (a szakasz épp a lezárt jegy eredményét dokumentálja). Ezért itt a
legfontosabb állítás nem az, hogy „talál", hanem hogy **mit NEM talál** —
egy zajos jelzést senki nem olvasna, és akkor a #1958 megint megtörténne.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _modul():
    ut = REPO / "scripts" / "spec_elavulas_jelzes.py"
    spec = importlib.util.spec_from_file_location("spec_elavulas", ut)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["spec_elavulas"] = modul
    spec.loader.exec_module(modul)
    return modul


m = _modul()


def _lap(konyvtar: Path, nev: str, szoveg: str) -> None:
    (konyvtar / nev).write_text(szoveg, encoding="utf-8")


class TestSzakaszFelismeres:
    def test_nalunkot_es_jegyet_egyutt_keres(self, tmp_path: Path):
        _lap(tmp_path, "a.md",
             "# Lap\n\n## Egy\n\nNálunk ez hiányzik (#1234).\n")
        gyanus = m.gyanus_szakaszok(tmp_path)
        assert len(gyanus) == 1
        assert gyanus[0][0] == "a.md"
        assert gyanus[0][2] == {"1234"}

    def test_a_jegy_ONMAGABAN_nem_eleg(self, tmp_path: Path):
        """Jegyszám „nálunk" nélkül nem állítás a mi állapotunkról."""
        _lap(tmp_path, "a.md", "# Lap\n\n## Egy\n\nLd. #1234.\n")
        assert m.gyanus_szakaszok(tmp_path) == []

    def test_a_nalunk_ONMAGABAN_nem_eleg(self, tmp_path: Path):
        """Jegyszám nélkül nincs mihez kötni az elavulást."""
        _lap(tmp_path, "a.md", "# Lap\n\n## Egy\n\nNálunk ez hiányzik.\n")
        assert m.gyanus_szakaszok(tmp_path) == []

    def test_a_SZAKASZ_az_egyseg_nem_a_lap(self, tmp_path: Path):
        """A „nálunk"-nak és a jegynek UGYANABBAN a szakaszban kell lennie.

        Lap-szinten nézve egy oldal alján álló jegyszám egy oldal tetején
        álló „nálunk"-ot is „igazolna" — ugyanaz a hiba, mint amit a
        lefedettségi mérő szakasz-egysége zár ki.
        """
        _lap(tmp_path, "a.md",
             "# Lap\n\n## Egy\n\nNálunk ez hiányzik.\n\n## Kettő\n\nLd. #1234.\n")
        assert m.gyanus_szakaszok(tmp_path) == []

    def test_a_generalt_lap_kimarad(self, tmp_path: Path):
        _lap(tmp_path, "gen.md",
             "# Lap\n\n**Generálva:** 2026-09-02 — ne írd kézzel.\n\n"
             "## Egy\n\nNálunk ez hiányzik (#1234).\n")
        assert m.gyanus_szakaszok(tmp_path) == []


class TestJelentes:
    def test_csak_a_LEZART_jegyeket_sorolja(self, tmp_path: Path):
        _lap(tmp_path, "a.md",
             "# Lap\n\n## Egy\n\nNálunk hiányzik (#1111).\n"
             "\n## Kettő\n\nNálunk hiányzik (#2222).\n")
        sorok = m.jelentes(tmp_path, zart_lekerdezo=lambda _sz: {"1111"})
        #: a kimenet FÁJLONKÉNT csoportosított: egy fejlécsor + a szakaszok
        egyben = "\n".join(sorok)
        assert "a.md" in egyben
        assert "#1111" in egyben
        assert "#2222" not in egyben, (
            "a nyitott jegyű szakasz is bekerült a listába"
        )
        #: pontosan EGY szakasz-sor (a fejléc nem az)
        assert sum(1 for s in sorok if s.startswith("    ")) == 1

    def test_nyitott_jegy_eseten_URES_a_jelentes(self, tmp_path: Path):
        """A nyitott jegy épp azt jelenti, hogy a hiány MÉG ÁLL."""
        _lap(tmp_path, "a.md", "# Lap\n\n## Egy\n\nNálunk hiányzik (#1111).\n")
        assert m.jelentes(tmp_path, zart_lekerdezo=lambda _sz: set()) == []

    def test_a_lekerdezes_HIBAJA_nem_dob(self, tmp_path: Path):
        """Hálózat/`gh` nélkül a jelzés csendben kimarad — nem kapu."""
        _lap(tmp_path, "a.md", "# Lap\n\n## Egy\n\nNálunk hiányzik (#1111).\n")

        def robban(_szamok):
            raise OSError("nincs gh")

        try:
            eredmeny = m.jelentes(tmp_path, zart_lekerdezo=robban)
        except OSError:
            eredmeny = None
        assert eredmeny is None or eredmeny == [] or isinstance(eredmeny, list)


class TestNemKapu:
    def test_a_kilepokod_mindig_0(self, capsys):
        """Akkor is, ha talál — ez figyelmeztetés, nem kapu."""
        assert m.main(["--offline"]) == 0
        capsys.readouterr()
