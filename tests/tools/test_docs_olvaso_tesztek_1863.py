"""#1863 — a `docs/`-ot olvasó tesztek alapállapota nem rohadhat el.

## Miért kell ez az őr

A `scripts/docs_olvaso_tesztek.py` listáját a CI futtatja le, ha egy PR
CSAK dokumentációt módosít (a teljes mátrix helyett). Ha a listában
elgépelés vagy elavult útvonal van, a CI **semmit nem futtat**, és a
kihagyás pontosan úgy néz ki, mint a siker — ez a #1858 hibája volt,
egy szinttel feljebb.

⚠️ Ez az őr azt fogja meg, ha egy felsorolt fájl **eltűnik vagy
átnevezik**. Azt NEM tudja megmondani, hogy a lista TELJES-e — ahhoz a
mérőt kell futtatni (`--mer`), ami a teszteket futtatja audit-horoggal.
A teljesség tehát mérés kérdése, nem őrzésé; a lista mellett ott áll,
mikor mértük és mi volt a mérés határa.
"""

from __future__ import annotations

import pathlib

import pytest

from scripts.docs_olvaso_tesztek import DOCS_OLVASO_TESZTEK, REPO


class TestAzAlapallapot:
    def test_nem_ures(self):
        """Üres listánál a CI-lépés némán semmit nem futtatna."""
        assert DOCS_OLVASO_TESZTEK

    @pytest.mark.parametrize("ut", DOCS_OLVASO_TESZTEK)
    def test_a_felsorolt_fajl_letezik(self, ut: str):
        assert (REPO / ut).is_file(), (
            f"elavult hivatkozás a docs_olvaso_tesztek listájában: {ut}"
        )

    def test_mind_tesztfajl(self):
        rosszak = [
            ut
            for ut in DOCS_OLVASO_TESZTEK
            if not (ut.startswith("tests/") and pathlib.Path(ut).name.startswith("test_"))
        ]
        assert not rosszak, f"nem tesztfájl a listában: {rosszak}"

    def test_nincs_ismetlodes(self):
        assert len(set(DOCS_OLVASO_TESZTEK)) == len(DOCS_OLVASO_TESZTEK)

    def test_rendezett(self):
        """Rendezve tartva a lista bővítése nem ad álkonfliktust."""
        assert list(DOCS_OLVASO_TESZTEK) == sorted(DOCS_OLVASO_TESZTEK)


class TestAKiiras:
    def test_soronkent_egy_utvonal(self, capsys):
        """A CI `while read`-del olvassa — soronként egy útvonal kell."""
        from scripts.docs_olvaso_tesztek import main

        assert main([]) == 0
        sorok = capsys.readouterr().out.strip().splitlines()
        assert sorok == list(DOCS_OLVASO_TESZTEK)


class TestAMeresNemHazudhat1968:
    """A meghiúsult mérés NE látsszon érvényes eredménynek (#1968).

    A `--mer` korábban nem nézte a `pytest.main()` kilépőkódját: egy
    megszakadt gyűjtés (kód 2) után derűsen kiírta a `JSON: []`-t. Aki
    ezt bemásolja, **kiüríti** a `DOCS_OLVASO_TESZTEK` listát, és a
    docs-only PR-eken onnantól semmi nem fut le.

    Ez ugyanaz a hibaosztály, mint a „hibaüzenet ≠ üres eredmény".
    """

    def _modul(self):
        import importlib.util
        import sys
        from pathlib import Path

        ut = Path(__file__).resolve().parents[2] / "scripts" / "docs_olvaso_tesztek.py"
        spec = importlib.util.spec_from_file_location("dot_1968", ut)
        modul = importlib.util.module_from_spec(spec)
        sys.modules["dot_1968"] = modul
        spec.loader.exec_module(modul)
        return modul

    def test_hasznalati_hiba_eseten_NEM_nulla(self, capsys):
        """Nem létező útvonal → pytest 4 → a mérés meghiúsult."""
        modul = self._modul()
        kod = modul.main(["--mer", "tests/biztosan_nincs_ilyen_konyvtar", "-q"])
        kimenet = capsys.readouterr()
        assert kod != 0, "a meghiúsult mérés 0-val tért vissza"
        assert "MEGHIÚSULT" in (kimenet.err + kimenet.out)

    def test_hibas_meres_NEM_ir_ki_JSON_listat(self, capsys):
        """A `JSON: [...]` sor az, amit bemásolnak — annak nem szabad
        megjelennie, ha a mérés nem futott le rendesen."""
        modul = self._modul()
        modul.main(["--mer", "tests/biztosan_nincs_ilyen_konyvtar", "-q"])
        kimenet = capsys.readouterr()
        assert "JSON:" not in (kimenet.out + kimenet.err), (
            "a meghiúsult mérés is kiírta a bemásolható JSON-listát"
        )
