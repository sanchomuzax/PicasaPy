"""#1770 (2. réteg) ŐR: a kiadási jegyzet ne essen gépi tartalékra.

## A mért kár

2026-08-31 este **tizenöt kiadás** ment ki egymás után, MINDEGYIK ezzel a
fejléccel:

> ⚠️ Ehhez a kiadáshoz **nem készült emberi összefoglaló** …

Pedig mind a tizenöthöz készült: gondos magyar bekezdés a CHANGELOG
`## [Nem kiadott]` szakaszában. A tulajdonos a Releases hasábból követi a
fejlődést — tehát épp az nem jutott el hozzá, amit neki írtunk.

## Az ok — három réteg, ez a harmadik

1. a szakasz neve elcsúszott (`[Kiadatlan]` vs `[Nem kiadott]`) — javítva;
2. a szakaszt lezáró `auto_bump` **csak akkor fut, ha a verzió MÁR ki van
   adva**; mi viszont minden PR-ben kézzel emelünk, tehát a lezárás a
   gyakorlatban SOHA nem fut le;
3. ⇒ a `changelog_notes(verzió)` nem talál `## [verzió]` szakaszt, és a
   hívó a gépi tartalékra vált.

## A javítás

Ha nincs `## [verzió]` szakasz, de van EMBERI tartalom a `[Nem kiadott]`
alatt, a jegyzet AZ lesz — hiszen épp azokat a változásokat adjuk ki.
"""

from __future__ import annotations

from pathlib import Path

from scripts import ensure_release

_FEJ = "# Változásnapló\n\nBevezető.\n\n"
_EMBERI = "### Javítva\n- **Valami elromlott, és megjavult (#1).**"


def test_a_verzio_szakasz_nyer_ha_van(tmp_path: Path) -> None:
    c = tmp_path / "CHANGELOG.md"
    c.write_text(
        f"{_FEJ}## [Nem kiadott]\n\n- **Későbbi (#2).**\n\n"
        f"## [0.8.29] – 2026-08-21\n\n{_EMBERI}\n",
        encoding="utf-8",
    )
    jegyzet = ensure_release.changelog_notes("0.8.29", c)
    assert "Valami elromlott" in jegyzet
    assert "Későbbi" not in jegyzet, (
        "a kiadatlan szakasz beszivárgott a lezárt verzió jegyzetébe"
    )


def test_verzio_szakasz_hianyaban_a_kiadatlan_jon(tmp_path: Path) -> None:
    """Ez a #1770 második rétegének foga."""
    c = tmp_path / "CHANGELOG.md"
    c.write_text(
        f"{_FEJ}## [Nem kiadott]\n\n{_EMBERI}\n\n## [0.8.28] – 2026-08-20\n",
        encoding="utf-8",
    )
    jegyzet = ensure_release.changelog_notes("0.8.29", c)
    assert "Valami elromlott" in jegyzet, (
        "a kiadás gépi tartalékra esett, pedig a „Nem kiadott\" szakaszban "
        "ott állt az emberi mondat (#1770)"
    )


def test_ures_kiadatlan_szakaszbol_nem_lesz_jegyzet(tmp_path: Path) -> None:
    """Üres szakaszból ne csináljunk látszat-jegyzetet: a hívó ilyenkor
    joggal vált a tartalékra, ami KIMONDJA, hogy nincs emberi mondat."""
    c = tmp_path / "CHANGELOG.md"
    c.write_text(
        f"{_FEJ}## [Nem kiadott]\n\n## [0.8.28] – 2026-08-20\n",
        encoding="utf-8",
    )
    assert ensure_release.changelog_notes("0.8.29", c) == ""


def test_helykitolto_kommentbol_sem(tmp_path: Path) -> None:
    c = tmp_path / "CHANGELOG.md"
    c.write_text(
        f"{_FEJ}## [Nem kiadott]\n\n*(ide jön a következő kör)*\n\n"
        "## [0.8.28] – 2026-08-20\n",
        encoding="utf-8",
    )
    assert ensure_release.changelog_notes("0.8.29", c) == ""
