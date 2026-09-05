"""#2264 — a bukás mellé oda kell írni, MILYEN környezetben történt.

A CI és a fejlesztői gép ma **nagyverzióban** eltér (OpenCV 4 ↔ 5,
PySide6 6.8 ↔ 6.11). Emiatt egy CI-bukás elemzése vaktában indul: nincs
olyan helyi környezet, amiben elő lehetne hozni — és a „helyben nem
reprodukálható ⇒ flaky" következtetés **hamis lehet** (a #2262-nél épp
az derült ki, hogy a futón determinisztikus).

Ez a modul a LÁTHATÓSÁGOT őrzi: a futtató jelentse a fő verziókat.
"""

from __future__ import annotations

import importlib
import re


def _modul():
    return importlib.import_module("scripts.run_tests")


class TestAKornyezetJelentes:
    def test_letezik_a_jelento_fuggveny(self):
        modul = _modul()
        assert hasattr(modul, "kornyezet_sorai"), (
            "nincs `kornyezet_sorai()` — a bukás mellől hiányozna a környezet"
        )

    def test_a_python_verziot_jelenti(self):
        sorok = "\n".join(_modul().kornyezet_sorai())
        assert re.search(r"Python\s+\d+\.\d+", sorok), sorok

    def test_a_PySide_es_az_OpenCV_verziot_is_jelenti(self):
        """Ez a kettő tér el nagyverzióban a CI és a gép között."""
        sorok = "\n".join(_modul().kornyezet_sorai())
        assert "PySide6" in sorok, sorok
        assert "OpenCV" in sorok or "cv2" in sorok, sorok

    def test_a_HIANYZO_csomag_nem_dont_le_semmit(self, monkeypatch):
        """A jelentés sosem lehet drágább, mint a hiba, amit kísér.

        ⚠️ A MODUL fogantyúját cseréljük (`_import_module`), nem a globális
        `importlib.import_module`-t: az minden más modulra átszivárogna,
        amíg a próba fut (#1217/#1375)."""
        modul = _modul()
        eredeti = modul._import_module

        def robban(nev, *a, **k):
            if nev in ("PySide6", "cv2"):
                raise ImportError("szándékos teszt-hiba")
            return eredeti(nev, *a, **k)

        monkeypatch.setattr(modul, "_import_module", robban)
        sorok = modul.kornyezet_sorai()
        assert sorok, "hiányzó csomagnál üres lett a jelentés"
        assert any("ismeretlen" in s.lower() or "?" in s for s in sorok), sorok

    def test_a_gepi_architekturat_is_jelenti(self):
        """A CI x86-64, a fejlesztői gép aarch64 — ez is része a képnek."""
        sorok = "\n".join(_modul().kornyezet_sorai())
        import platform

        assert platform.machine() in sorok, sorok


class TestABukasJelentesUtja:
    """A jelentés a VALÓDI bukás-úton is megjelenik.

    A `main()` a teljes készletet futtatja, ezért a jelentés-írás külön
    függvénybe került — így percek helyett ezredmásodpercek alatt mérhető,
    hogy a környezet tényleg a bukás mellé kerül.
    """

    def test_a_bukas_melle_odakerul_a_kornyezet(self, capsys):
        modul = _modul()
        modul.jelentsd_a_bukasokat([("tests/app/valami.py", 1)])
        kimenet = capsys.readouterr().out
        assert "HIBÁS RÉSZFUTÁSOK" in kimenet
        assert "tests/app/valami.py: exit 1" in kimenet
        assert "A FUTÁS KÖRNYEZETE" in kimenet
        assert "PySide6" in kimenet and "OpenCV" in kimenet

    def test_a_bukott_reszfutasok_MIND_szerepelnek(self, capsys):
        modul = _modul()
        modul.jelentsd_a_bukasokat([("a.py", 1), ("b.py", -6), ("c.py", 124)])
        kimenet = capsys.readouterr().out
        for nev, kod in [("a.py", 1), ("b.py", -6), ("c.py", 124)]:
            assert f"{nev}: exit {kod}" in kimenet, kimenet
