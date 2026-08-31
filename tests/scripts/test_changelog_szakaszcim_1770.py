"""#1770 ŐR: a „Nem kiadott" szakasz nem tűnhet el a CHANGELOG-ból.

## A hiba, amit ez az őr kizár

A kiadási automatika (`auto_bump.zard_le_a_changelogot`) átnevezi a
`## [Nem kiadott]` címet `## [verzió] – dátum` alakra — és **nem tesz a
helyére újat**. A következő kör tehát olyan fájlt kap, amiben nincs hova
írni; aki ilyenkor kézzel vesz fel szakaszt, könnyen MÁS néven teszi.

Pontosan ez történt: a `629a0872` óta a fájl `## [Kiadatlan]`-t használt,
az eszközök viszont `## [Nem kiadott]`-at kerestek. Hat napig, némán:
**19 bejegyzés gyűlt fel** egyetlen dátumozatlan halomban, a v0.8.133-tól
a v0.8.154-ig, és a napló elvesztette a verzió-hozzárendelést.

## A javítás szerkezete

A lezárás után az automatika **azonnal visszateszi** az üres
`## [Nem kiadott]` szakaszt. Így a szakasz MINDIG létezik, tehát nincs
alkalom rossz néven újra felvenni.
"""

from __future__ import annotations

from pathlib import Path

from scripts import auto_bump

_FEJ = "# Változásnapló\n\nBevezető mondat.\n\n"


def test_a_lezaras_utan_van_ures_kiadatlan_szakasz(tmp_path: Path) -> None:
    """Ez a #1770 javításának foga."""
    c = tmp_path / "CHANGELOG.md"
    c.write_text(
        _FEJ + "## [Nem kiadott]\n\n### Javítva\n- **Valami (#1).**\n\n"
        "## [0.8.28] – 2026-08-20\n",
        encoding="utf-8",
    )

    assert auto_bump.zard_le_a_changelogot(c, "0.8.29", "2026-08-21") is True
    szoveg = c.read_text(encoding="utf-8")

    assert "## [0.8.29] – 2026-08-21" in szoveg, "a lezárás nem történt meg"
    assert auto_bump.KIADATLAN_CIM in szoveg, (
        "a lezárás után NINCS üres „Nem kiadott\" szakasz — a következő kör "
        "megint más néven venné fel (#1770)"
    )
    # a friss szakasz a lezárt FÖLÖTT áll
    assert szoveg.index(auto_bump.KIADATLAN_CIM) < szoveg.index(
        "## [0.8.29]"
    ), "az üres szakasz a lezárt alá került"
    # a bejegyzés a LEZÁRT szakaszban maradt, nem vándorolt fel
    assert szoveg.index("- **Valami (#1).**") > szoveg.index("## [0.8.29]"), (
        "a bejegyzés átkerült az új üres szakaszba"
    )


def test_a_regi_szakaszok_nem_serulnek(tmp_path: Path) -> None:
    c = tmp_path / "CHANGELOG.md"
    c.write_text(
        _FEJ + "## [Nem kiadott]\n\n- **Új (#2).**\n\n"
        "## [0.8.28] – 2026-08-20\n\n- **Régi (#1).**\n",
        encoding="utf-8",
    )
    auto_bump.zard_le_a_changelogot(c, "0.8.29", "2026-08-21")
    szoveg = c.read_text(encoding="utf-8")
    assert "## [0.8.28] – 2026-08-20" in szoveg
    assert "- **Régi (#1).**" in szoveg


def test_szakasz_nelkuli_fajlba_sem_ir_uresen(tmp_path: Path) -> None:
    """Ha nem volt mit lezárni, ne keletkezzen szakasz a semmiből: az
    üres szakasz a LEZÁRÁS kísérője, nem önálló művelet."""
    c = tmp_path / "CHANGELOG.md"
    c.write_text(_FEJ + "## [0.8.28] – 2026-08-20\n", encoding="utf-8")

    assert auto_bump.zard_le_a_changelogot(c, "0.8.29", "2026-08-21") is False
    assert auto_bump.KIADATLAN_CIM not in c.read_text(encoding="utf-8")


class TestAValodiChangelog:
    """A repó SAJÁT fájlja — ez fogta volna meg a hat napos csúszást."""

    def test_a_valodi_changelogban_a_szerzodes_szerinti_cim_all(self) -> None:
        ut = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
        szoveg = ut.read_text(encoding="utf-8")
        assert auto_bump.KIADATLAN_CIM in szoveg, (
            f"a CHANGELOG.md-ben nincs `{auto_bump.KIADATLAN_CIM}` szakasz. "
            "Ha más néven van (pl. „Kiadatlan\"), az eszközök NEM találják "
            "meg: a kiadás nem nevezi át, és a bejegyzések dátumozatlanul "
            "gyűlnek (#1770)."
        )
