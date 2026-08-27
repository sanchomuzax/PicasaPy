"""A döntés ↔ kód őr FOGA — #1623.

A `CONTRIBUTING.md` és a `PROTOKOLL.md` szabálya: *az őrnek legyen foga* —
új ellenőrzést a javítás nélkül is le kell futtatni, és látni kell, hogy
elbukik. Ez a teszt mind a négy irányra magvetett hibát ültet be.

A tiszta ág szándékosan tartalmazza azt a két hamis-pozitív alakzatot, ami
egy naiv változatot használhatatlanná tenne:

1. **a `tests/` fában lévő kitalált fájlnév** — a
   `tests/scripts/test_kiadas_szukseges_1319.py` egy nem létező
   `docs/decisions/0012-valami.md`-t ad át mintaadatként egy
   paraméterlistában. A 3. irány ezért nem nézi a `tests/` fát;
2. **a konvencióról beszélő fájl** — maga az őr és ez a teszt példaként
   említ döntés-útvonalakat; ezek a `_KIVETT` listán vannak.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_decision_links.py"


def _betolt():
    spec = importlib.util.spec_from_file_location("check_decision_links", SCRIPT_PATH)
    assert spec and spec.loader, f"nem tölthető be: {SCRIPT_PATH}"
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _kotes(statusz: str, megv: str, orzi: str) -> str:
    return (f"\n## Kötés\n\n- **Státusz:** {statusz}\n"
            f"- **Megvalósítja:** {megv}\n- **Őrzi:** {orzi}\n")


def _tiszta_fa(gyoker: Path) -> None:
    """Hibátlan minifa — a két ismert hamis-pozitív alakzattal együtt."""
    (gyoker / "docs" / "decisions").mkdir(parents=True)
    (gyoker / "src").mkdir()
    (gyoker / "tests" / "scripts").mkdir(parents=True)

    (gyoker / "src" / "modul.py").write_text(
        "# a döntés: docs/decisions/elso.md\n", encoding="utf-8"
    )
    (gyoker / "tests" / "teszt_modul.py").write_text("assert True\n", encoding="utf-8")
    (gyoker / "docs" / "decisions" / "elso.md").write_text(
        "# Első döntés\n" + _kotes("ELFOGADVA", "`src/modul.py`", "`tests/teszt_modul.py`"),
        encoding="utf-8",
    )
    # döntés megvalósítás nélkül — ÉRVÉNYES állapot, nem hiba
    (gyoker / "docs" / "decisions" / "masodik.md").write_text(
        "# Második döntés\n" + _kotes("ELFOGADVA", "nincs megvalósítva", "nincs őr"),
        encoding="utf-8",
    )
    # hamis-pozitív 1: kitalált döntés-útvonal egy teszt paraméterlistájában
    (gyoker / "tests" / "scripts" / "test_kiadas.py").write_text(
        'MINTA = ["docs/decisions/0012-valami.md"]\n', encoding="utf-8"
    )


class DontesKotesTeszt(unittest.TestCase):
    def setUp(self) -> None:
        self.modul = _betolt()

    def test_tiszta_fan_nincs_eltérés(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gyoker = Path(td)
            _tiszta_fa(gyoker)
            self.assertEqual(self.modul.ellenoriz(gyoker), [])

    def test_hianyzo_kotes_szakaszt_elkap(self) -> None:
        """1. irány — a lapnak muszáj kötést adnia."""
        with tempfile.TemporaryDirectory() as td:
            gyoker = Path(td)
            _tiszta_fa(gyoker)
            (gyoker / "docs" / "decisions" / "kotes-nelkul.md").write_text(
                "# Kötés nélküli döntés\n", encoding="utf-8"
            )
            hibak = self.modul.ellenoriz(gyoker)
            self.assertTrue(any("hiányzik a `## Kötés`" in h for h in hibak), hibak)

    def test_elarvult_megvalositast_elkap(self) -> None:
        """2. irány — jegyzék → valóság."""
        with tempfile.TemporaryDirectory() as td:
            gyoker = Path(td)
            _tiszta_fa(gyoker)
            (gyoker / "docs" / "decisions" / "elso.md").write_text(
                "# Első döntés\n"
                + _kotes("ELFOGADVA", "`src/nincs_ilyen.py`", "`tests/teszt_modul.py`"),
                encoding="utf-8",
            )
            hibak = self.modul.ellenoriz(gyoker)
            self.assertTrue(any("nincs_ilyen.py" in h for h in hibak), hibak)

    def test_nem_letezo_dontesre_hivatkozast_elkap(self) -> None:
        """3. irány — valóság → jegyzék, a `src/` fából."""
        with tempfile.TemporaryDirectory() as td:
            gyoker = Path(td)
            _tiszta_fa(gyoker)
            (gyoker / "src" / "masik.py").write_text(
                "# lásd docs/decisions/soha-nem-volt.md\n", encoding="utf-8"
            )
            hibak = self.modul.ellenoriz(gyoker)
            self.assertTrue(any("soha-nem-volt.md" in h for h in hibak), hibak)

    def test_visszavont_dontes_elo_megvalositassal_elkap(self) -> None:
        """4. irány — a #616-osztály: elvetett döntés tér vissza a kódba."""
        with tempfile.TemporaryDirectory() as td:
            gyoker = Path(td)
            _tiszta_fa(gyoker)
            (gyoker / "docs" / "decisions" / "elso.md").write_text(
                "# Első döntés\n"
                + _kotes("VISSZAVONVA", "`src/modul.py`", "nincs őr"),
                encoding="utf-8",
            )
            hibak = self.modul.ellenoriz(gyoker)
            self.assertTrue(any("#616-osztály" in h for h in hibak), hibak)

    def test_visszavont_dontes_megvalositas_nelkul_rendben(self) -> None:
        """A visszavonás önmagában NEM hiba — csak az élő megvalósítás az."""
        with tempfile.TemporaryDirectory() as td:
            gyoker = Path(td)
            _tiszta_fa(gyoker)
            (gyoker / "docs" / "decisions" / "elso.md").write_text(
                "# Első döntés\n"
                + _kotes("VISSZAVONVA", "nincs megvalósítva", "nincs őr"),
                encoding="utf-8",
            )
            self.assertEqual(self.modul.ellenoriz(gyoker), [])

    def test_ismeretlen_statuszt_elkap(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gyoker = Path(td)
            _tiszta_fa(gyoker)
            (gyoker / "docs" / "decisions" / "elso.md").write_text(
                "# Első döntés\n" + _kotes("TALÁN", "nincs megvalósítva", "nincs őr"),
                encoding="utf-8",
            )
            hibak = self.modul.ellenoriz(gyoker)
            self.assertTrue(any("ismeretlen státusz" in h for h in hibak), hibak)

    def test_ures_mappa_hibat_jelez(self) -> None:
        """Bemeneti hiba != »nincs eltérés« — a néma siker tiltott."""
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "docs" / "decisions").mkdir(parents=True)
            with self.assertRaises(ValueError):
                self.modul.ellenoriz(Path(td))

    def test_eles_repo_zold(self) -> None:
        """A valódi fán is fusson le — ez a CI-job lényege."""
        self.assertEqual(self.modul.ellenoriz(ROOT), [])


if __name__ == "__main__":
    unittest.main()
