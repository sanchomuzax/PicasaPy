"""#1512 — a `00-index.md` prózájában ne rothadjon kézzel írt leltár-szám.

A `docs/specs/lanc-szakadasok-leltar.md` sorában korábban két, kézzel
karbantartott szám állt („**52 tag**… ebből **39-et csak a teszt hív**"),
miközben a mért érték rég 49 volt. Nem generált, nem őrizte semmi, tehát
némán elavult minden alkalommal, amikor a leltár változott.

A #1508 ugyanezt a hibaosztályt szüntette meg a generált blokkban: a
terjedelmi számok az őr futásának kimenetébe (CI-napló) költöztek. Ez a
teszt azt őrzi, hogy a szám ne kússzon vissza a mutató lapra sem.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

INDEX = Path(__file__).resolve().parents[1] / "docs" / "specs" / "00-index.md"

# Kézzel írt darabszám a leltárról: „**52 tag**", „**39-et** csak a teszt hív".
SZAM_MINTA = re.compile(r"\*\*\d+\s*(?:tag|-et|-et\s+csak)\b|\*\*\d+\*\*\s*tag")


def _leltar_sor() -> str:
    """A `lanc-szakadasok-leltar.md`-re mutató táblasor a mutató lapról."""
    for sor in INDEX.read_text(encoding="utf-8").splitlines():
        if "lanc-szakadasok-leltar.md" in sor and sor.lstrip().startswith("|"):
            return sor
    pytest.fail("a 00-index.md-ben nincs sor a lanc-szakadasok-leltar.md-re")


def test_a_leltar_sora_letezik() -> None:
    assert "Ahol a háttér kész" in _leltar_sor()


def test_a_leltar_soraban_nincs_kezzel_irt_tagszam() -> None:
    """A visszacsúszás őre: darabszám nem kerülhet vissza a prózába."""
    talalat = SZAM_MINTA.findall(_leltar_sor())
    assert not talalat, (
        "kézzel írt leltár-szám került vissza a 00-index.md prózájába: "
        f"{talalat}. A szám a generált blokkban és az őr kimenetében él "
        "(#1508, #1512) — a prózai másolat némán elavul."
    )


def test_a_sor_a_generalt_forrasra_mutat() -> None:
    """Szám helyett a friss forrás megnevezése áll a sorban."""
    sor = _leltar_sor()
    assert "kepesseg_or.py" in sor, "nincs megnevezve, hol áll a friss szám"


def test_az_or_foga_megvan() -> None:
    """Pozitív kontroll: a mintának a RÉGI szövegre illeszkednie KELL.

    Enélkül a fenti tiltó teszt üresen is zöld lenne, tehát semmit nem őrizne.
    """
    regi = (
        "| [lanc-szakadasok-leltar.md](lanc-szakadasok-leltar.md) | mért "
        "leltár: 19 regisztrált vezérlőből egy sem holt, de **52 tag** "
        "elérhetetlen a QML-ből, ebből **39-et csak a teszt hív**. |"
    )
    assert SZAM_MINTA.findall(regi), "a minta a régi, hibás szövegre sem illeszkedik"
